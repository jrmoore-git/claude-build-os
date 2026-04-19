#!/usr/bin/env python3.11
"""
Arm-comparison study scorer.

Reads arm outputs from stores/arm-study/<run_id>/arm-x/ and arm-y/
(neutral filenames on disk; labels obfuscated until after aggregation).
Invokes `debate.py review --models <j1>,<j2> --prompt-file <comparison-prompt>`
with two non-Claude judges per arm, parses per-dimension structured extractions,
aggregates (count + quality distribution + convergence), unblinds arm labels
from labels.json AFTER aggregation, then emits per-dimension scored JSON +
markdown summary.

For Dimensions 4/5 additionally invokes `debate.py judge --verify-claims`
to classify each finding as valid / hallucinated / partial / unverifiable.

See tasks/arm-comparison-methodology-validation-plan.md (Phase 1 Track B-min)
for the authoritative spec.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STORE = REPO_ROOT / "stores" / "arm-study"
DEFAULT_PROMPT = REPO_ROOT / "config" / "study" / "comparison-prompt.md"

DIMENSIONS = [
    "direction_improvement",
    "nuance_caught",
    "net_new_ideas",
    "catch_rate",
    "miss_rate",
    "plan_quality_delta",
    "code_review_quality_delta",
]
GROUND_TRUTH_DIMENSIONS = {"catch_rate", "miss_rate"}
QUALITY_CATEGORIES = ("substantive", "marginal", "superficial", "harmful")

DEFAULT_JUDGES = ("gpt-5.4", "gemini-3.1-pro")
COUNT_CONVERGENCE_TOLERANCE = 1
QUALITY_CONVERGENCE_THRESHOLD = 0.60
UNANIMOUS_QUALITY_THRESHOLD = 0.80

# REDESIGN A — second-pass mechanism classifier (tasks/arm-study-redesigns-refined.md)
A3_PROMPT_PATH = REPO_ROOT / "config" / "study" / "a3-mechanism-prompt.md"
A3_DEFAULT_MODEL = "claude-sonnet-4-6"
A3_MECHANISM_LABELS = (
    "PROPOSAL_ERROR_CAUGHT",
    "CHALLENGER_FABRICATION",
    "AMBIGUOUS",
    "INFERENCE_NOT_GROUNDED",
)
A3_AMBIGUOUS_FALLBACK_THRESHOLD = 0.50  # >50% AMBIGUOUS → regex fallback
A3_PARSE_FAIL_FALLBACK_THRESHOLD = 0.20  # >20% parse failures → regex fallback
A3_MECHANISM_CACHE_PATH = DEFAULT_STORE / "mechanism-cache.jsonl"
A3_ADJUDICATION_LOG_PATH = DEFAULT_STORE / "adjudication-log.jsonl"
A3_EXCERPT_WINDOW = 600  # chars of context around claim text in proposal/challenger


# ── Family exclusion ────────────────────────────────────────────────────────


def enforce_non_claude(judges: Iterable[str]) -> list[str]:
    """Reject any judge whose model id starts with 'claude-'. Returns the
    list unchanged if clean; raises ValueError otherwise."""
    bad = [j for j in judges if j.startswith("claude-")]
    if bad:
        raise ValueError(
            f"judge family-exclusion: Claude-family judges not permitted for "
            f"comparative scoring. Rejected: {bad}"
        )
    return list(judges)


# ── Judge invocation ────────────────────────────────────────────────────────


def invoke_review(
    input_path: Path,
    prompt_path: Path,
    models: list[str],
    timeout: int = 600,
) -> tuple[int, str, str]:
    """Invoke `debate.py review --models ... --prompt-file ...`.
    Returns (exit_code, stdout, stderr). Not called in --dry-run."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "debate.py"),
        "review",
        "--models", ",".join(models),
        "--prompt-file", str(prompt_path),
        "--input", str(input_path),
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=str(REPO_ROOT),
        )
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def run_claim_verifier_inprocess(
    challenge_text: str,
    proposal_text: str,
) -> dict[str, Any]:
    """Run the claim verifier in-process via `debate._run_claim_verifier`.

    `debate.py judge` is a full judgment pipeline with no standalone
    verify-only subcommand, and modifying production debate.py is out of
    scope per the study plan. Calling the helper function directly yields
    the raw verification_text the plan's Phase 1 intent calls for, at the
    cost of one LLM call rather than two.

    Returns {status, verification_text, stats, error}.
    """
    try:
        import debate
        import debate_common
    except ImportError as e:
        return {"status": "failed", "error": f"import failed: {e}",
                "verification_text": None, "stats": None}

    try:
        api_key, litellm_url, _ = debate_common._load_credentials()
    except Exception as e:
        return {"status": "failed", "error": f"credential load failed: {e}",
                "verification_text": None, "stats": None}

    try:
        verification_text, stats = debate._run_claim_verifier(
            challenge_text, proposal_text, litellm_url, api_key,
        )
    except Exception as e:
        return {"status": "failed", "error": f"verifier raised: {e}",
                "verification_text": None, "stats": None}

    if verification_text is None:
        return {"status": "failed",
                "error": "verifier returned None (see debate.py stderr)",
                "verification_text": None, "stats": None}

    return {"status": "verified", "error": None,
            "verification_text": verification_text, "stats": stats}


# ── FALSIFIED source classification (item 2 of metric-fix plan) ────────────
#
# The verifier emits per-claim blocks like:
#   **Claim**: ...
#   **Source**: Proposal (1A), Challenger A (Challenge 1)
#   **Status**: FALSIFIED
#   **Evidence**: ...
#
# A FALSIFIED claim conflates two very different failure modes:
#   - "hallucination": the challenger ASSERTED X as fact, and X is false.
#   - "caught_misquote": the challenger quoted the proposal ("proposal says
#     X") in order to flag that X is false.
#
# The Source field attributes the claim's origin. Classification rule:
#   - Source mentions Challenger and NOT Proposal -> hallucination
#   - Source mentions Proposal and NOT Challenger -> caught_misquote
#   - Source mentions BOTH -> caught_misquote (challenger picked up the
#     proposal's claim in the context of critique; the verifier agrees the
#     claim is false; the challenger didn't independently hallucinate it)
#   - Source unparseable -> unclear
#
# This is a conservative heuristic. The "mixed" case is the ambiguous one
# but empirically on n=3 the majority of mixed claims are challengers
# quoting the proposal to flag the error. The assumption is flagged in the
# markdown output so a reader can spot-check.


import re as _re  # module-level import for the parser below


_CLAIM_BLOCK_RE = _re.compile(
    r"\*\*Claim\*\*.*?(?=\*\*Claim\*\*|\Z)",
    _re.DOTALL,
)
_SOURCE_RE = _re.compile(r"\*\*Source\*\*:\s*(.+?)$", _re.MULTILINE)
_STATUS_RE = _re.compile(r"\*\*Status\*\*:\s*(.+?)$", _re.MULTILINE)


def classify_falsified_claims(verification_text: str | None) -> dict[str, int]:
    """Parse verifier's per-claim blocks. Return classification counts.

    Returns {
        "hallucination": int,       # challenger asserted, verifier falsified
        "caught_misquote": int,     # challenger quoted proposal, proposal wrong
        "unclear": int,             # source field unparseable
        "total_falsified": int,     # sum for sanity
        "total_verified": int,
        "total_unresolvable": int,
    }
    All zero on empty/missing input.
    """
    out = {"hallucination": 0, "caught_misquote": 0, "unclear": 0,
           "total_falsified": 0, "total_verified": 0, "total_unresolvable": 0}
    if not verification_text:
        return out

    for block in _CLAIM_BLOCK_RE.findall(verification_text):
        status_m = _STATUS_RE.search(block)
        if not status_m:
            continue
        status = status_m.group(1).upper()
        if "VERIFIED" in status and "FALSIFIED" not in status:
            out["total_verified"] += 1
            continue
        if "UNRESOLVABLE" in status:
            out["total_unresolvable"] += 1
            continue
        if "FALSIFIED" not in status:
            continue
        out["total_falsified"] += 1

        source_m = _SOURCE_RE.search(block)
        source = (source_m.group(1) if source_m else "").lower()
        has_prop = "proposal" in source
        has_chal = "challenger" in source
        if has_chal and not has_prop:
            out["hallucination"] += 1
        elif has_prop:
            # Proposal-only OR mixed: treat as caught_misquote.
            out["caught_misquote"] += 1
        else:
            out["unclear"] += 1
    return out


# ── REDESIGN A — second-pass mechanism classifier ──────────────────────────
#
# Per cross-model challenge (tasks/arm-study-redesigns-judgment.md Challenge 1),
# the regex above conflates 4 mechanisms into 2 labels. The dedicated
# second-pass classifier asks a separate LLM (no tools, schema-constrained
# JSON output, temperature=0, content-hashed cache) to attribute each
# FALSIFIED claim to one of A3_MECHANISM_LABELS.
#
# Failure detection (>50% AMBIGUOUS or >20% parse failures) falls back to
# the regex above and flags the run as `classifier_source: regex-fallback`
# so the verdict aggregator can apply legacy formulas.
#
# Production debate.py is NOT modified — the classifier lives entirely in
# this module and uses llm_client.llm_call_json directly.


import hashlib as _hashlib  # module-level for deterministic cache keys


_A3_PROMPT_CACHE: tuple[str, str] | None = None  # (system, user_template)


def _load_a3_prompt() -> tuple[str, str]:
    """Load and split the A3 mechanism prompt into (system, user_template).
    Cached at module level. Splits on the '## SYSTEM' / '## USER' headings.
    """
    global _A3_PROMPT_CACHE
    if _A3_PROMPT_CACHE is not None:
        return _A3_PROMPT_CACHE
    text = A3_PROMPT_PATH.read_text()
    sys_marker = "\n## SYSTEM\n"
    usr_marker = "\n## USER\n"
    if sys_marker not in text or usr_marker not in text:
        raise ValueError(
            f"a3-mechanism-prompt.md missing required '## SYSTEM' / '## USER' "
            f"sections at {A3_PROMPT_PATH}"
        )
    sys_idx = text.index(sys_marker) + len(sys_marker)
    usr_idx = text.index(usr_marker)
    system = text[sys_idx:usr_idx].strip()
    user_template = text[usr_idx + len(usr_marker):].strip()
    _A3_PROMPT_CACHE = (system, user_template)
    return _A3_PROMPT_CACHE


def _hash_claim(
    claim_text: str, verifier_evidence: str, model_version: str,
) -> str:
    """Stable cache key for one (claim, verifier_evidence, model, prompt) tuple.

    Includes a hash of the loaded a3-mechanism-prompt.md so a prompt edit
    invalidates cached labels (post-build review Finding 1A — the prompt
    file's own claim that "edits invalidate the cache" was previously
    untrue).
    """
    h = _hashlib.sha256()
    h.update(model_version.encode("utf-8"))
    h.update(b"\x1e")
    h.update(claim_text.encode("utf-8"))
    h.update(b"\x1e")
    h.update(verifier_evidence.encode("utf-8"))
    h.update(b"\x1e")
    try:
        system, user_template = _load_a3_prompt()
        h.update(system.encode("utf-8"))
        h.update(b"\x1d")
        h.update(user_template.encode("utf-8"))
    except Exception:
        # Prompt unreadable → use a stable placeholder so cache stays
        # consistent across runs in degraded environments.
        h.update(b"prompt-unavailable")
    return h.hexdigest()


def _load_mechanism_cache(
    cache_path: Path = A3_MECHANISM_CACHE_PATH,
) -> dict[str, dict[str, Any]]:
    """Load the JSONL cache as a dict keyed by claim hash. Last-write-wins
    on duplicates (file is append-only; later entries override earlier)."""
    out: dict[str, dict[str, Any]] = {}
    if not cache_path.is_file():
        return out
    with cache_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = entry.get("claim_hash")
            if isinstance(key, str):
                out[key] = entry
    return out


def _persist_mechanism_cache_entry(
    entry: dict[str, Any],
    cache_path: Path = A3_MECHANISM_CACHE_PATH,
) -> None:
    """Append one entry to the JSONL cache. Creates parent dir if missing."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def _log_adjudication(
    log_path: Path, payload: dict[str, Any],
) -> None:
    """Append one classifier I/O record to the adjudication log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")


def _excerpt_around(text: str, needle: str, window: int = A3_EXCERPT_WINDOW) -> str:
    """Return up to `window` chars centered on the first case-insensitive
    occurrence of `needle` in `text`. If not found, return the first
    `window` chars. Empty inputs → empty string."""
    if not text or not needle:
        return (text or "")[:window]
    idx = text.lower().find(needle.lower()[:80])  # match first 80 chars
    if idx < 0:
        return text[:window]
    half = window // 2
    start = max(0, idx - half)
    end = min(len(text), idx + half)
    return text[start:end]


def _utc_now_iso() -> str:
    """Stable ISO-8601 UTC timestamp for log entries."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def classify_mechanism_for_claim(
    claim_text: str,
    source_field: str,
    verifier_evidence: str,
    proposal_text: str,
    challenger_text: str,
    model: str = A3_DEFAULT_MODEL,
    cache: dict[str, dict[str, Any]] | None = None,
    run_id: str | None = None,
    log_path: Path = A3_ADJUDICATION_LOG_PATH,
    cache_path: Path = A3_MECHANISM_CACHE_PATH,
    _llm_call_json=None,  # injectable for tests
) -> dict[str, Any]:
    """Classify one FALSIFIED claim into one of A3_MECHANISM_LABELS.

    Returns {label, rationale, parse_ok, raw_response, cache_hit, error}.
    On any LLM error: returns label=AMBIGUOUS + parse_ok=False + error=msg.
    Never raises — all failures recorded inline so the caller can compute
    parse-fail rates and fall back to regex.
    """
    cache_key = _hash_claim(claim_text, verifier_evidence, model)
    if cache is not None and cache_key in cache:
        cached = cache[cache_key]
        return {
            "label": cached.get("label", "AMBIGUOUS"),
            "rationale": cached.get("rationale", ""),
            "parse_ok": cached.get("parse_ok", True),
            "raw_response": cached.get("raw_response", ""),
            "cache_hit": True,
            "error": None,
        }

    if _llm_call_json is None:
        try:
            from llm_client import llm_call_json as _llm_call_json
        except ImportError as e:
            return {
                "label": "AMBIGUOUS", "rationale": "", "parse_ok": False,
                "raw_response": "", "cache_hit": False,
                "error": f"llm_client import failed: {e}",
            }

    system, user_template = _load_a3_prompt()
    proposal_excerpt = _excerpt_around(proposal_text, claim_text)
    challenger_excerpt = _excerpt_around(challenger_text, claim_text)
    user_filled = (
        user_template
        .replace("{claim_text}", claim_text)
        .replace("{source_field}", source_field)
        .replace("{verifier_evidence}", verifier_evidence)
        .replace("{proposal_excerpt}", proposal_excerpt)
        .replace("{challenger_excerpt}", challenger_excerpt)
    )

    raw_response = ""
    parse_ok = False
    label = "AMBIGUOUS"
    rationale = ""
    error: str | None = None
    try:
        result = _llm_call_json(
            system=system, user=user_filled, model=model,
            temperature=0.0, max_tokens=200, timeout=60,
        )
        raw_response = json.dumps(result) if isinstance(result, dict) else str(result)
        if isinstance(result, dict):
            candidate = result.get("label")
            if isinstance(candidate, str) and candidate in A3_MECHANISM_LABELS:
                label = candidate
                parse_ok = True
            else:
                error = f"label not in allowed set: {candidate!r}"
            r = result.get("rationale")
            if isinstance(r, str):
                rationale = r[:160]
        else:
            error = "JSON top-level not an object"
    except Exception as e:
        error = f"llm_call_json raised: {e!s}"

    entry = {
        "claim_hash": cache_key,
        "label": label,
        "rationale": rationale,
        "parse_ok": parse_ok,
        "raw_response": raw_response,
        "model": model,
        "error": error,
    }
    _persist_mechanism_cache_entry(entry, cache_path=cache_path)
    if cache is not None:
        cache[cache_key] = entry

    _log_adjudication(log_path, {
        "ts": _utc_now_iso(),
        "run_id": run_id,
        "claim_hash": cache_key,
        "model": model,
        "label": label,
        "parse_ok": parse_ok,
        "error": error,
        "claim_excerpt": claim_text[:200],
    })

    return {
        "label": label, "rationale": rationale, "parse_ok": parse_ok,
        "raw_response": raw_response, "cache_hit": False, "error": error,
    }


def iter_falsified_blocks(verification_text: str | None):
    """Yield (claim_text, source_field, evidence_text) per FALSIFIED claim.
    Used by classify_mechanisms_llm and arm_study_a3_calibration."""
    if not verification_text:
        return
    _EVIDENCE_RE = _re.compile(r"\*\*Evidence\*\*:\s*(.+?)$", _re.MULTILINE)
    for block in _CLAIM_BLOCK_RE.findall(verification_text):
        status_m = _STATUS_RE.search(block)
        if not status_m:
            continue
        status = status_m.group(1).upper()
        if "FALSIFIED" not in status or "VERIFIED" in status:
            continue
        # Extract claim text — content between **Claim**: marker and the
        # next **Field** marker. The verifier indents subsequent fields
        # with whitespace (e.g. "   **Source**:"), so the lookahead allows
        # optional leading whitespace before the next bold marker.
        claim_m = _re.search(
            r"\*\*Claim\*\*:?\s*(.+?)(?=\n\s*\*\*[A-Z]|\Z)",
            block, _re.DOTALL,
        )
        claim_text = (claim_m.group(1).strip() if claim_m else "").strip()
        source_m = _SOURCE_RE.search(block)
        source = source_m.group(1).strip() if source_m else ""
        ev_m = _EVIDENCE_RE.search(block)
        evidence = ev_m.group(1).strip() if ev_m else ""
        yield claim_text, source, evidence


def classify_mechanisms_llm(
    verification_text: str | None,
    proposal_text: str,
    challenger_text: str,
    model: str = A3_DEFAULT_MODEL,
    run_id: str | None = None,
    cache: dict[str, dict[str, Any]] | None = None,
    log_path: Path = A3_ADJUDICATION_LOG_PATH,
    cache_path: Path = A3_MECHANISM_CACHE_PATH,
    _llm_call_json=None,
    _regex_fallback=None,
) -> dict[str, Any]:
    """Run the second-pass classifier across every FALSIFIED claim.

    Returns aggregate + per-claim labels + classifier_source. If degraded
    (high AMBIGUOUS rate or parse failures), falls back to the regex
    classifier and sets classifier_source = "regex-fallback".
    """
    if cache is None:
        cache = _load_mechanism_cache(cache_path=cache_path)
    if _regex_fallback is None:
        _regex_fallback = classify_falsified_claims

    regex_counts = _regex_fallback(verification_text)
    base = {
        "labels": {label: 0 for label in A3_MECHANISM_LABELS},
        "per_claim": [],
        "classifier_source": "llm",
        "ambiguous_rate": 0.0,
        "parse_failures": 0,
        "regex_fallback_used": False,
        "fallback_reason": None,
        "total_falsified": regex_counts.get("total_falsified", 0),
        "total_verified": regex_counts.get("total_verified", 0),
        "total_unresolvable": regex_counts.get("total_unresolvable", 0),
    }

    blocks = list(iter_falsified_blocks(verification_text))
    if not blocks:
        # No FALSIFIED claims → trivially degenerate; surface regex-counts
        # for compat (they'll be all-zero too).
        base["hallucination"] = regex_counts.get("hallucination", 0)
        base["caught_misquote"] = regex_counts.get("caught_misquote", 0)
        base["unclear"] = regex_counts.get("unclear", 0)
        return base

    for claim_text, source_field, evidence in blocks:
        result = classify_mechanism_for_claim(
            claim_text=claim_text,
            source_field=source_field,
            verifier_evidence=evidence,
            proposal_text=proposal_text,
            challenger_text=challenger_text,
            model=model, cache=cache, run_id=run_id,
            log_path=log_path, cache_path=cache_path,
            _llm_call_json=_llm_call_json,
        )
        base["per_claim"].append({
            "claim_text": claim_text[:200],
            "source_field": source_field,
            "label": result["label"],
            "rationale": result["rationale"],
            "parse_ok": result["parse_ok"],
            "error": result["error"],
            "cache_hit": result["cache_hit"],
        })
        base["labels"][result["label"]] += 1
        if not result["parse_ok"]:
            base["parse_failures"] += 1

    total = len(base["per_claim"])
    base["ambiguous_rate"] = (
        base["labels"]["AMBIGUOUS"] / total if total > 0 else 0.0
    )
    parse_fail_rate = base["parse_failures"] / total if total > 0 else 0.0

    if base["ambiguous_rate"] > A3_AMBIGUOUS_FALLBACK_THRESHOLD:
        base["regex_fallback_used"] = True
        base["fallback_reason"] = (
            f"ambiguous_rate {base['ambiguous_rate']:.2%} exceeds "
            f"{A3_AMBIGUOUS_FALLBACK_THRESHOLD:.0%} threshold"
        )
    elif parse_fail_rate > A3_PARSE_FAIL_FALLBACK_THRESHOLD:
        base["regex_fallback_used"] = True
        base["fallback_reason"] = (
            f"parse_failure_rate {parse_fail_rate:.2%} exceeds "
            f"{A3_PARSE_FAIL_FALLBACK_THRESHOLD:.0%} threshold"
        )

    if base["regex_fallback_used"]:
        base["classifier_source"] = "regex-fallback"
        base["hallucination"] = regex_counts.get("hallucination", 0)
        base["caught_misquote"] = regex_counts.get("caught_misquote", 0)
        base["unclear"] = regex_counts.get("unclear", 0)
    else:
        # Map explicit labels to legacy field names for verdict-aggregator
        # backward compat. With LLM mode, the verdict aggregator reads
        # `labels` directly and uses CHALLENGER_FABRICATION as the
        # hallucination denominator (orphan #10/#11 fixes per refined doc).
        base["hallucination"] = base["labels"]["CHALLENGER_FABRICATION"]
        base["caught_misquote"] = base["labels"]["PROPOSAL_ERROR_CAUGHT"]
        base["unclear"] = (
            base["labels"]["AMBIGUOUS"] + base["labels"]["INFERENCE_NOT_GROUNDED"]
        )

    return base


# ── Parsing ─────────────────────────────────────────────────────────────────


_DIMENSION_PREFIX_RE = None  # compiled lazily


def _normalize_dimension_keys(obj: dict[str, Any]) -> dict[str, Any]:
    """The prompt emits `dimension_N_<name>` keys for readability; the scorer
    indexes on bare `<name>`. Strip the `dimension_\\d+_` prefix on top-level
    keys so judge output maps onto the DIMENSIONS list. Keys without the
    prefix are preserved unchanged (older fixtures, dry-run)."""
    import re

    global _DIMENSION_PREFIX_RE
    if _DIMENSION_PREFIX_RE is None:
        _DIMENSION_PREFIX_RE = re.compile(r"^dimension_\d+_(.+)$")
    out: dict[str, Any] = {}
    for key, value in obj.items():
        m = _DIMENSION_PREFIX_RE.match(key)
        out[m.group(1) if m else key] = value
    return out


def parse_judge_output(text: str) -> dict[str, Any]:
    """Parse debate.py review stdout. The comparison prompt is documented to
    emit per-dimension JSON blocks. Accept either a fenced JSON code block or
    a raw JSON object at top level. If multiple reviewers wrote separate
    sections (e.g. '## Reviewer A' / '## Reviewer B'), each section is parsed
    independently and returned under a judge label.

    Returns {"<judge-label>": {<dimension>: {items: [...], ...}, ...}}.
    Top-level `dimension_N_` prefixes are stripped so keys align with
    DIMENSIONS. If parsing fails, the value for the judge label is
    {"_parse_error": msg}.
    """
    import re

    sections = _split_reviewer_sections(text)
    parsed: dict[str, Any] = {}
    for label, body in sections.items():
        block = _extract_json(body)
        if block is None:
            parsed[label] = {"_parse_error": "no JSON block found"}
            continue
        try:
            raw = json.loads(block)
        except json.JSONDecodeError as exc:
            parsed[label] = {"_parse_error": f"invalid JSON: {exc}"}
            continue
        if isinstance(raw, dict):
            parsed[label] = _normalize_dimension_keys(raw)
        else:
            parsed[label] = {"_parse_error": "top-level JSON is not an object"}
    return parsed


def _split_reviewer_sections(text: str) -> dict[str, str]:
    """Split `debate.py review` stdout on '## Reviewer ...' headings.
    Falls back to {"Reviewer": <full text>} if no heading is present."""
    import re

    header_re = re.compile(r"^## Reviewer(?:\s+([A-Z0-9]+))?\s*$", re.MULTILINE)
    matches = list(header_re.finditer(text))
    if not matches:
        return {"Reviewer": text}
    sections: dict[str, str] = {}
    for i, match in enumerate(matches):
        label = match.group(1) or f"Reviewer-{i+1}"
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[label] = text[start:end]
    return sections


def _extract_json(text: str) -> str | None:
    """Extract the first JSON object from text. Prefers a ```json fenced
    block; falls back to the first balanced {...} run."""
    import re

    fence_re = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)
    m = fence_re.search(text)
    if m:
        return m.group(1).strip()

    # Fallback: find first balanced brace run.
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                return text[start:i + 1]
    return None


# ── Aggregation ─────────────────────────────────────────────────────────────


def aggregate_dimension(
    judge_extractions: dict[str, Any],
    dimension: str,
    is_ground_truth: bool = False,
) -> dict[str, Any]:
    """Aggregate two judges' extractions for one dimension.

    Returns {
        "dimension": name,
        "status": "scored" | "not_scorable" | "inconclusive-split",
        "item_counts": {judge_label: int, ...},
        "quality_distribution": {judge_label: {substantive: n, ...}, ...},
        "substantive_count": {judge_label: int, ...},
        "convergence": {
            "count_delta": int,
            "count_converged": bool,
            "quality_agreement_rate": float | None,
            "quality_converged": bool,
            "level": "high" | "medium" | "low" | "split",
        },
        "quality_disagreements": [{item_id, judge_ratings: {...}}],
        "verified": {...}   # only present if is_ground_truth
    }

    If a dimension is missing from ALL judges, status = not_scorable.
    If present but judges disagree beyond thresholds, status = inconclusive-split.
    Otherwise status = scored.
    """
    judge_labels = sorted(judge_extractions.keys())
    per_judge: dict[str, list[dict[str, Any]]] = {}
    missing = []
    for label in judge_labels:
        ext = judge_extractions[label]
        if not isinstance(ext, dict) or "_parse_error" in ext:
            missing.append(label)
            continue
        dim_block = ext.get(dimension)
        if dim_block is None or "items" not in dim_block:
            missing.append(label)
            continue
        items = dim_block.get("items") or []
        if not isinstance(items, list):
            missing.append(label)
            continue
        per_judge[label] = items

    if not per_judge:
        return {
            "dimension": dimension,
            "status": "not_scorable",
            "reason": "no judge produced an items list for this dimension",
            "item_counts": {},
            "quality_distribution": {},
            "substantive_count": {},
            "convergence": {"level": "not_scorable"},
            "quality_disagreements": [],
        }

    item_counts = {label: len(items) for label, items in per_judge.items()}
    quality_dist = {
        label: _count_qualities(items) for label, items in per_judge.items()
    }
    substantive_count = {
        label: dist.get("substantive", 0) for label, dist in quality_dist.items()
    }

    # Count-convergence: all pairs within tolerance.
    counts = list(item_counts.values())
    count_delta = max(counts) - min(counts) if counts else 0
    count_converged = count_delta <= COUNT_CONVERGENCE_TOLERANCE

    # Quality-convergence: per-item category agreement when judges match items
    # by a shared item_id/index. If no shared ids, fall back to per-rank pairing.
    quality_rate, disagreements = _quality_agreement(per_judge)
    quality_converged = (
        quality_rate is not None and quality_rate >= QUALITY_CONVERGENCE_THRESHOLD
    )

    if count_converged and quality_rate is not None and quality_rate >= UNANIMOUS_QUALITY_THRESHOLD:
        level = "high"
    elif count_converged and quality_converged:
        level = "medium"
    elif count_converged or quality_converged:
        level = "low"
    else:
        level = "split"

    status = "scored"
    if not count_converged and (quality_rate is None or quality_rate < QUALITY_CONVERGENCE_THRESHOLD):
        status = "inconclusive-split"

    out: dict[str, Any] = {
        "dimension": dimension,
        "status": status,
        "item_counts": item_counts,
        "quality_distribution": quality_dist,
        "substantive_count": substantive_count,
        "convergence": {
            "count_delta": count_delta,
            "count_converged": count_converged,
            "quality_agreement_rate": quality_rate,
            "quality_converged": quality_converged,
            "level": level,
        },
        "quality_disagreements": disagreements,
    }
    if missing:
        out["judges_missing_dimension"] = missing
    return out


def _count_qualities(items: list[dict[str, Any]]) -> dict[str, int]:
    dist = {cat: 0 for cat in QUALITY_CATEGORIES}
    for item in items:
        q = (item.get("quality") or "").lower()
        if q in dist:
            dist[q] += 1
    return dist


def _quality_agreement(
    per_judge: dict[str, list[dict[str, Any]]],
) -> tuple[float | None, list[dict[str, Any]]]:
    """Compute per-item quality-category agreement rate across judges.

    Strategy: if all judges share common `item_id` values for some subset of
    items, pair by item_id. Otherwise pair by list index, truncated to the
    shortest list. Returns (agreement_rate, disagreement_list).

    Agreement_rate is None if there's nothing to compare (e.g. all lists empty).
    """
    labels = list(per_judge.keys())
    if len(labels) < 2:
        return (None, [])
    lists = [per_judge[l] for l in labels]

    id_sets = [{_item_id(it): it for it in items if _item_id(it) is not None}
               for items in lists]
    shared_ids = set.intersection(*[set(d.keys()) for d in id_sets]) if id_sets else set()

    pairs: list[tuple[str, list[str]]] = []
    if shared_ids:
        for iid in sorted(shared_ids):
            qs = [(d[iid].get("quality") or "").lower() for d in id_sets]
            pairs.append((iid, qs))
    else:
        n = min(len(lst) for lst in lists)
        for i in range(n):
            qs = [(lst[i].get("quality") or "").lower() for lst in lists]
            pairs.append((f"idx-{i}", qs))

    if not pairs:
        return (None, [])

    agreed = 0
    disagreements: list[dict[str, Any]] = []
    for iid, qs in pairs:
        if len(set(qs)) == 1:
            agreed += 1
        else:
            disagreements.append({
                "item_id": iid,
                "judge_ratings": dict(zip(labels, qs)),
            })
    return (agreed / len(pairs), disagreements)


def _item_id(item: dict[str, Any]) -> str | None:
    for key in ("item_id", "id", "finding_id"):
        val = item.get(key)
        if isinstance(val, str) and val:
            return val
    return None


def aggregate_proposal(
    arm_extractions: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate all dimensions for one proposal across both arms (blinded).

    arm_extractions: {"arm-x": {<judge_label>: {...}, ...}, "arm-y": {...}}
    Returns {
        "arms": {
            "arm-x": {dimension: <aggregate_dimension output>, ...},
            "arm-y": {...}
        },
        "aggregate_inconclusive": bool,
    }
    """
    out: dict[str, Any] = {"arms": {}}
    inconclusive_flags: list[bool] = []
    for arm_label, judges in arm_extractions.items():
        per_dim: dict[str, Any] = {}
        for dim in DIMENSIONS:
            per_dim[dim] = aggregate_dimension(
                judges, dim, is_ground_truth=(dim in GROUND_TRUTH_DIMENSIONS)
            )
            inconclusive_flags.append(
                per_dim[dim]["status"] in ("inconclusive-split",)
            )
        out["arms"][arm_label] = per_dim

    # Aggregate-level inconclusive: all dimensions across both arms inconclusive.
    scorable = [
        dim_data
        for arm in out["arms"].values()
        for dim_data in arm.values()
        if dim_data["status"] != "not_scorable"
    ]
    if scorable and all(d["status"] == "inconclusive-split" for d in scorable):
        out["aggregate_inconclusive"] = True
    else:
        out["aggregate_inconclusive"] = False
    return out


def check_variance_gap(
    scored: dict[str, Any],
    within_arm_variance: dict[str, dict[str, float]] | None,
) -> dict[str, Any]:
    """Per-plan rule: if within-arm variance on a dimension exceeds half the
    inter-arm gap, that dimension is INCONCLUSIVE for that comparison.

    within_arm_variance: optional {arm_label: {dimension: variance}}. If
    absent, this check is a no-op.
    """
    if not within_arm_variance:
        return scored
    arm_labels = list(scored["arms"].keys())
    if len(arm_labels) != 2:
        return scored
    a, b = arm_labels
    for dim in DIMENSIONS:
        a_sub = sum(scored["arms"][a][dim].get("substantive_count", {}).values())
        b_sub = sum(scored["arms"][b][dim].get("substantive_count", {}).values())
        gap = abs(a_sub - b_sub)
        max_variance = max(
            within_arm_variance.get(a, {}).get(dim, 0.0),
            within_arm_variance.get(b, {}).get(dim, 0.0),
        )
        if gap > 0 and max_variance > 0.5 * gap:
            for arm_label in arm_labels:
                scored["arms"][arm_label][dim]["variance_exceeded_gap"] = True
                if scored["arms"][arm_label][dim]["status"] == "scored":
                    scored["arms"][arm_label][dim]["status"] = "inconclusive-variance"
    return scored


def compute_stratified_counts(
    per_proposal: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    """Track proposal-type distribution separately (governance vs architecture
    vs code-change vs research). Input: list of proposal scorings each with
    `proposal_type` key."""
    counts: dict[str, dict[str, int]] = {}
    for p in per_proposal:
        ptype = p.get("proposal_type") or "unknown"
        counts.setdefault(ptype, {"proposals": 0})
        counts[ptype]["proposals"] += 1
    return counts


# ── Unblinding ──────────────────────────────────────────────────────────────


def unblind(scored: dict[str, Any], labels: dict[str, str]) -> dict[str, Any]:
    """Map arm-x/arm-y (neutral filenames on disk) to arm-a/arm-b (semantic
    arm names) AFTER aggregation is complete. `labels` = {'arm-x': 'arm-a',
    'arm-y': 'arm-b'} or similar."""
    unblinded_arms: dict[str, Any] = {}
    for neutral, data in scored["arms"].items():
        semantic = labels.get(neutral, neutral)
        unblinded_arms[semantic] = data
    scored["arms"] = unblinded_arms
    scored["unblinded"] = True
    scored["label_mapping"] = dict(labels)
    return scored


# ── Fixtures for --dry-run ──────────────────────────────────────────────────


def _fixture_judge_extraction(arm: str, judge: str) -> dict[str, Any]:
    """Synthetic per-dimension extraction for dry-run. Emits the shape the
    real comparison prompt produces: {dimension: {items: [{item_id,
    source_present, quality, rationale}, ...]}}.

    Two arms differ in substantive count to exercise the aggregation path."""
    base_counts = {"arm-x": 3, "arm-y": 4}
    n = base_counts.get(arm, 3)

    def _items(dim: str, count: int, substantive_n: int) -> list[dict[str, Any]]:
        out = []
        for i in range(count):
            q = "substantive" if i < substantive_n else "marginal"
            out.append({
                "item_id": f"{arm}-{dim}-{i+1}",
                "source_present": False,
                "quality": q,
                "rationale": f"fixture rationale for {arm}/{judge}/{dim} #{i+1}",
            })
        return out

    return {
        "direction_improvement": {"items": _items("dir", n, 2)},
        "nuance_caught": {"items": _items("nuance", n, 2)},
        "net_new_ideas": {"items": _items("new", n, 1)},
        "catch_rate": {"items": _items("catch", n, 2)},
        "miss_rate": {"items": _items("miss", max(n - 1, 1), 1)},
        "plan_quality_delta": {"items": _items("plan", n, 1)},
        "code_review_quality_delta": {"items": _items("code", max(n - 2, 0), 0)},
    }


def build_dry_run_scored(judges: list[str]) -> dict[str, Any]:
    """Build a full scored object from fixtures (no subprocess calls)."""
    arm_extractions: dict[str, dict[str, Any]] = {}
    for arm in ("arm-x", "arm-y"):
        arm_extractions[arm] = {
            j: _fixture_judge_extraction(arm, j) for j in judges
        }
    scored = aggregate_proposal(arm_extractions)
    scored = unblind(scored, {"arm-x": "arm-a", "arm-y": "arm-b"})
    scored["metadata"] = {
        "dry_run": True,
        "judges": judges,
        "run_id": "dry-run-fixture",
        "proposal_type": "governance",
    }
    return scored


# ── Markdown emission ───────────────────────────────────────────────────────


def render_markdown(scored: dict[str, Any]) -> str:
    lines = ["# Arm-comparison scored results", ""]
    meta = scored.get("metadata", {})
    if meta:
        lines.append("## Metadata")
        lines.append("")
        for k, v in meta.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")
    lines.append("## Per-arm per-dimension")
    lines.append("")
    for arm_label in sorted(scored.get("arms", {}).keys()):
        lines.append(f"### {arm_label}")
        lines.append("")
        lines.append("| Dimension | Status | Count (per judge) | Substantive (per judge) | Convergence |")
        lines.append("|---|---|---|---|---|")
        for dim in DIMENSIONS:
            d = scored["arms"][arm_label].get(dim, {})
            status = d.get("status", "?")
            counts = d.get("item_counts", {})
            sub = d.get("substantive_count", {})
            conv = d.get("convergence", {}).get("level", "?")
            counts_s = ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "—"
            sub_s = ", ".join(f"{k}={v}" for k, v in sorted(sub.items())) or "—"
            lines.append(f"| {dim} | {status} | {counts_s} | {sub_s} | {conv} |")
        lines.append("")
    lines.append(f"**aggregate_inconclusive**: {scored.get('aggregate_inconclusive', False)}")
    lines.append("")
    return "\n".join(lines) + "\n"


# ── Main ────────────────────────────────────────────────────────────────────


def score_run(
    run_id: str,
    store_root: Path,
    prompt_path: Path,
    judges: list[str],
) -> dict[str, Any]:
    """Score a real run by invoking `debate.py review` on each arm's output.
    NOT called by --dry-run. Requires arm-x/ and arm-y/ directories and a
    labels.json under store_root/<run_id>/.

    For ground-truth dimensions (catch_rate, miss_rate), additionally invokes
    `debate.py judge --verify-claims` so each extracted item carries a
    validity flag (valid / hallucinated / partial / unverifiable)."""
    run_dir = store_root / run_id
    if not run_dir.is_dir():
        raise FileNotFoundError(f"run directory not found: {run_dir}")
    labels_path = run_dir / "labels.json"
    if not labels_path.is_file():
        raise FileNotFoundError(f"labels.json not found: {labels_path}")

    # Resolve the proposal path from the orchestrator's manifest. Needed
    # for the claim verifier, which takes (challenge_text, proposal_text).
    manifest_path = run_dir / "manifest.json"
    proposal_path: Path | None = None
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text())
            rel = manifest.get("proposal_path")
            if rel:
                proposal_path = REPO_ROOT / rel
        except (json.JSONDecodeError, OSError):
            proposal_path = None

    arm_extractions: dict[str, dict[str, Any]] = {}
    arm_verifications: dict[str, dict[str, Any]] = {}
    for arm in ("arm-x", "arm-y"):
        arm_dir = run_dir / arm
        if not arm_dir.is_dir():
            raise FileNotFoundError(f"arm directory not found: {arm_dir}")
        # Orchestrator writes per-proposal subdirs (<arm>/<proposal_stem>/<file>.md).
        # Glob nested + flat, exclude scorer scratch files.
        review_files = sorted(
            p for p in arm_dir.glob("**/*.md")
            if not p.name.startswith("_")
        )
        if not review_files:
            raise FileNotFoundError(f"no review files under {arm_dir}")
        # Concatenate (prompt is per-dimension, so judges see the full review).
        combined = arm_dir / "_combined-for-scoring.md"
        combined.write_text("\n\n---\n\n".join(p.read_text() for p in review_files))
        code, stdout, stderr = invoke_review(combined, prompt_path, judges)
        if code != 0:
            raise RuntimeError(
                f"debate.py review failed for {arm}: exit={code}\n{stderr}"
            )
        arm_extractions[arm] = parse_judge_output(stdout)

        # Dim 4/5 code grounding: run the claim verifier in-process on the
        # concatenated challenge + proposal, then run the REDESIGN A
        # second-pass mechanism classifier. Failures are recorded but do
        # not abort scoring — downstream aggregation reads what's available.
        if proposal_path is not None and proposal_path.is_file():
            arm_verifications[arm] = _verify_ground_truth_dimensions(
                combined, proposal_path,
                run_classifier=True, run_id=run_id,
            )
        else:
            arm_verifications[arm] = {
                "status": "failed",
                "error": f"proposal_path missing from manifest ({manifest_path})",
                "verification_text": None,
                "stats": None,
            }

    scored = aggregate_proposal(arm_extractions)
    _attach_verifications(scored, arm_verifications)

    # miss_rate (Dim 5) coverage pass — reads reference issue list if present.
    # The discoverer is run separately via arm_study_miss_discoverer.py to
    # keep LLM costs transparent. If the reference file doesn't exist, the
    # miss_rate block stays "not-yet-measured" for this run.
    _attach_miss_rate_coverage(scored, run_dir, arm_extractions_dirs={
        arm: run_dir / arm / "_combined-for-scoring.md"
        for arm in ("arm-x", "arm-y")
    })

    labels = json.loads(labels_path.read_text())
    scored = unblind(scored, labels)
    scored["metadata"] = {
        "dry_run": False,
        "judges": judges,
        "run_id": run_id,
        "verify_claims_judge": judges[0],
    }
    return scored


def _attach_miss_rate_coverage(
    scored: dict[str, Any],
    run_dir: Path,
    arm_extractions_dirs: dict[str, Path],
) -> None:
    """Attach miss_rate coverage data to each arm's miss_rate block.

    Reads stores/arm-study/<run_id>/miss_reference_issues.json (produced by
    arm_study_miss_discoverer.py). Matches each issue's key_tokens against
    each arm's combined challenge text. Stores per-arm matched/missed
    counts so the verdict can compute miss_rate per arm.
    """
    ref_path = run_dir / "miss_reference_issues.json"
    if not ref_path.is_file():
        for arm in scored.get("arms", {}).values():
            if "miss_rate" in arm:
                arm["miss_rate"]["reference_coverage"] = {
                    "status": "reference-not-generated",
                    "reason": (
                        f"miss_reference_issues.json not found at "
                        f"{ref_path.relative_to(REPO_ROOT)} — run "
                        f"arm_study_miss_discoverer.py to generate"
                    ),
                }
        return

    try:
        ref = json.loads(ref_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        for arm in scored.get("arms", {}).values():
            if "miss_rate" in arm:
                arm["miss_rate"]["reference_coverage"] = {
                    "status": "reference-load-failed",
                    "error": str(e),
                }
        return

    issues = ref.get("issues") or []
    if not issues:
        for arm in scored.get("arms", {}).values():
            if "miss_rate" in arm:
                arm["miss_rate"]["reference_coverage"] = {
                    "status": "reference-empty",
                    "reason": "discoverer returned zero issues",
                }
        return

    # Lazy import — keeps the scorer importable without the discoverer's
    # dependencies (the matcher itself is pure Python).
    try:
        import arm_study_miss_discoverer as mrd
    except ImportError as e:
        for arm in scored.get("arms", {}).values():
            if "miss_rate" in arm:
                arm["miss_rate"]["reference_coverage"] = {
                    "status": "matcher-import-failed",
                    "error": str(e),
                }
        return

    # REDESIGN B: when discoverer ran in ensemble mode, attach sensitivity
    # data using union/intersection in addition to majority (primary).
    provenance = ref.get("aggregation_provenance") or {}
    use_v2_matcher = bool(provenance)
    sensitivity_buckets = {
        "majority": provenance.get("majority", issues),
        "union": provenance.get("union", issues),
        "intersection": provenance.get("intersection", issues),
    } if use_v2_matcher else None

    for arm_neutral, arm_data in scored.get("arms", {}).items():
        combined_path = arm_extractions_dirs.get(arm_neutral)
        if not combined_path or not combined_path.is_file():
            continue
        challenge_text = combined_path.read_text()
        if use_v2_matcher:
            # Primary = majority. v2 word-boundary tokenization + LLM
            # adjudication for borderline matches. Adjudicator failures
            # default to "missed" so any fault is conservative.
            coverage = mrd.match_reference_issues_v2(
                sensitivity_buckets["majority"], challenge_text,
            )
        else:
            coverage = mrd.match_reference_issues(issues, challenge_text)
        if "miss_rate" not in arm_data:
            arm_data["miss_rate"] = {
                "dimension": "miss_rate", "status": "scored",
                "item_counts": {}, "quality_distribution": {},
                "substantive_count": {}, "convergence": {},
            }
        arm_data["miss_rate"]["reference_coverage"] = {
            "status": "scored",
            "total_reference_issues": coverage["total_reference_issues"],
            "caught_count": coverage["caught_count"],
            "missed_count": coverage["missed_count"],
            "miss_rate": coverage["miss_rate"],
            "caught": coverage["caught"],
            "missed": coverage["missed"],
        }
        # Optional: v2 includes borderline + adjudicator stats.
        for key in ("borderline_count", "adjudicator_calls"):
            if key in coverage:
                arm_data["miss_rate"]["reference_coverage"][key] = coverage[key]
        # Sensitivity attachment for ensemble runs.
        if use_v2_matcher:
            sens_block: dict[str, Any] = {}
            for rule in ("majority", "union", "intersection"):
                rule_issues = sensitivity_buckets[rule]
                if rule == "majority":
                    rule_cov = coverage  # already computed
                else:
                    rule_cov = mrd.match_reference_issues_v2(
                        rule_issues, challenge_text,
                    )
                sens_block[rule] = {
                    "total_reference_issues": rule_cov["total_reference_issues"],
                    "caught_count": rule_cov["caught_count"],
                    "missed_count": rule_cov["missed_count"],
                    "miss_rate": rule_cov["miss_rate"],
                }
            arm_data["miss_rate"]["reference_coverage_sensitivity"] = sens_block


def _verify_ground_truth_dimensions(
    challenge_path: Path,
    proposal_path: Path,
    *,
    run_classifier: bool = True,
    classifier_model: str = A3_DEFAULT_MODEL,
    run_id: str | None = None,
    mechanism_cache: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Read the per-arm concatenated challenge file and the proposal, run
    the claim verifier in-process, then run the REDESIGN A second-pass
    mechanism classifier on FALSIFIED claims.

    Returns dict with verifier output + (when run_classifier) a
    `mechanism_classification` block populated by classify_mechanisms_llm.
    """
    try:
        challenge_text = challenge_path.read_text()
    except OSError as e:
        return {"status": "failed", "error": f"read challenge failed: {e}",
                "verification_text": None, "stats": None,
                "challenge_text": None, "proposal_text": None}
    try:
        proposal_text = proposal_path.read_text()
    except OSError as e:
        return {"status": "failed", "error": f"read proposal failed: {e}",
                "verification_text": None, "stats": None,
                "challenge_text": challenge_text, "proposal_text": None}

    result = run_claim_verifier_inprocess(challenge_text, proposal_text)
    result["challenge_text"] = challenge_text
    result["proposal_text"] = proposal_text

    if run_classifier and result.get("status") == "verified":
        try:
            mech = classify_mechanisms_llm(
                verification_text=result.get("verification_text"),
                proposal_text=proposal_text,
                challenger_text=challenge_text,
                model=classifier_model,
                run_id=run_id,
                cache=mechanism_cache,
            )
            result["mechanism_classification"] = mech
        except Exception as e:
            # Classifier failure is non-fatal — verifier output stays.
            result["mechanism_classification"] = {
                "classifier_source": "regex-fallback",
                "regex_fallback_used": True,
                "fallback_reason": f"classifier raised: {e!s}",
                "labels": {label: 0 for label in A3_MECHANISM_LABELS},
                "per_claim": [],
                "ambiguous_rate": 0.0,
                "parse_failures": 0,
            }
            # Backfill regex counts so verdict aggregator has data.
            regex_counts = classify_falsified_claims(
                result.get("verification_text")
            )
            result["mechanism_classification"].update({
                "hallucination": regex_counts.get("hallucination", 0),
                "caught_misquote": regex_counts.get("caught_misquote", 0),
                "unclear": regex_counts.get("unclear", 0),
                "total_falsified": regex_counts.get("total_falsified", 0),
                "total_verified": regex_counts.get("total_verified", 0),
                "total_unresolvable": regex_counts.get("total_unresolvable", 0),
            })
    return result


def _attach_verifications(
    scored: dict[str, Any],
    verifications: dict[str, dict[str, Any]],
) -> None:
    """Attach verify-claims output to each ground-truth dimension in-place.

    Verifier output is stored alongside the REDESIGN A `mechanism_classification`
    block (per-claim explicit labels via the second-pass LLM classifier, or
    regex-fallback when degraded). The verdict aggregator reads
    `mechanism_classification.classifier_source` to pick formula path.
    """
    for arm_label, arm_data in scored.get("arms", {}).items():
        verif = verifications.get(arm_label, {})
        full_text = verif.get("verification_text") or ""
        mech = verif.get("mechanism_classification")
        if mech is None:
            # Caller skipped the classifier (e.g., legacy code path or test
            # that constructed verifications without it) — fall back to regex.
            # Post-build review Finding 2: removed the dead `__wrapped__`
            # branch that never fired (function was never decorated).
            regex = classify_falsified_claims(full_text)
            mech = {
                "classifier_source": "regex-fallback",
                "regex_fallback_used": True,
                "fallback_reason": "no mechanism_classification in verifier output",
                "labels": {label: 0 for label in A3_MECHANISM_LABELS},
                "per_claim": [],
                "ambiguous_rate": 0.0,
                "parse_failures": 0,
                **regex,
            }
        entry = {
            "status": verif.get("status", "unknown"),
            "stats": verif.get("stats"),
            "verification_text": full_text,
            "falsified_classification": mech,
        }
        if verif.get("error"):
            entry["error"] = verif["error"]
        for dim in GROUND_TRUTH_DIMENSIONS:
            if dim in arm_data:
                arm_data[dim]["verify_claims"] = entry


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--run-id", default=None, help="stores/arm-study/<run-id>/")
    ap.add_argument("--store-root", type=Path, default=DEFAULT_STORE)
    ap.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT,
                    help="Path to config/study/comparison-prompt.md")
    ap.add_argument("--judge-a", default=DEFAULT_JUDGES[0])
    ap.add_argument("--judge-b", default=DEFAULT_JUDGES[1])
    ap.add_argument("--dry-run", action="store_true",
                    help="Use fixture judge outputs; no API calls.")
    ap.add_argument("--output-markdown", type=Path, default=None,
                    help="Override markdown summary path. Default: "
                         "<store_root>/<run_id>/scored.md (real run) "
                         "or skip (dry-run).")
    args = ap.parse_args()

    try:
        judges = enforce_non_claude([args.judge_a, args.judge_b])
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.dry_run:
        scored = build_dry_run_scored(judges)
    else:
        if not args.run_id:
            print("ERROR: --run-id required (or pass --dry-run)", file=sys.stderr)
            return 2
        try:
            scored = score_run(args.run_id, args.store_root, args.prompt_file, judges)
        except (FileNotFoundError, RuntimeError) as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        md_path = args.output_markdown or (args.store_root / args.run_id / "scored.md")
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(scored))
        # Verdict CLI reads scored.json from <store_root>/<run_id>/scored.json.
        json_path = args.store_root / args.run_id / "scored.json"
        json_path.write_text(json.dumps(scored, indent=2, sort_keys=True) + "\n")

    json.dump(scored, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

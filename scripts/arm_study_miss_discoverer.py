#!/usr/bin/env python3.11
"""
Arm-comparison study: independent miss-rate discoverer (item 5 of the
metric-fix plan).

Reads a proposal + code repo and produces a REFERENCE issue list: the set
of concrete issues a rigorous adversarial review should catch. This
reference set is independent of both arms — the scorer can then diff each
arm's challenge output against it to compute miss_rate per arm.

Design rationale:
- The original miss_rate definition in comparison-prompt.md was degenerate
  (extract only items where the review explicitly acknowledges a gap),
  which returned empty on virtually every proposal. The useful miss_rate
  is "issues that exist but weren't caught," which requires a reference.
- The discoverer uses claude-sonnet-4-6 + repo tools (grep, read_file
  snippet) to ground claims, matching the verifier's posture. Sonnet is not
  in either arm (arms use opus-4-6 or a production mix), so the discoverer
  is not structurally aligned with either.
- Prompt targets exhaustive concrete issues with key_tokens for
  matcher-based coverage. Not inflationary — matcher treats unmatched
  tokens as a miss, so over-producing reference issues would unfairly
  favor neither arm.

Usage:
    python3.11 scripts/arm_study_miss_discoverer.py \\
        --proposal tasks/foo-proposal.md \\
        --output stores/arm-study/<run-id>/miss_reference_issues.json
"""

from __future__ import annotations

import argparse
import hashlib as _hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = "claude-sonnet-4-6"

# REDESIGN B (tasks/arm-study-redesigns-refined.md) — multi-model ensemble +
# semantic matcher constants. Module-level for auditability + test override.
B1_ENSEMBLE_MODELS = ("claude-sonnet-4-6", "gpt-5.4", "gemini-3.1-pro")
B1_DEDUP_TOKEN_OVERLAP = 0.50  # jaccard on key_tokens to count as same issue
B1_MIN_VOTES_FOR_MAJORITY = 2  # ≥2 of 3 → majority bucket
B1_MATCHER_CAUGHT_THRESHOLD = 0.60  # token-overlap ratio to call caught
B1_MATCHER_BORDERLINE_THRESHOLD = 0.30  # ≥this and <caught → adjudicator
B1_ADJUDICATOR_MODEL = "gpt-5.4"  # cheap binary classifier; gpt-5.4-mini if
                                  # available in LiteLLM, otherwise this
B1_ADJUDICATOR_MAX_TOKENS = 200
B1_ADJUDICATOR_TIMEOUT = 60
B1_ADJUDICATOR_PROMPT_PATH = REPO_ROOT / "config" / "study" / "b1-adjudicator-prompt.md"
B1_ADJUDICATION_CACHE_PATH = (
    REPO_ROOT / "stores" / "arm-study" / "adjudication-cache.jsonl"
)
B1_ADJUDICATION_LOG_PATH = (
    REPO_ROOT / "stores" / "arm-study" / "adjudication-log.jsonl"
)
B1_EXCERPT_WINDOW = 600

# Pre-egress credential patterns. Reused regex literals from
# scripts/judge_frame_orchestrator.py:CREDENTIAL_PATTERNS — the LLM-call surface
# in this file is small enough that fresh constants are simpler than introducing
# a cross-module import (per .claude/rules/code-quality.md).
_CREDENTIAL_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
]


class CredentialEgressError(RuntimeError):
    """Raised when challenge_text contains a credential-shaped pattern.
    Stops the borderline adjudicator from sending suspect text to the LLM."""


MISS_DISCOVERER_SYSTEM_PROMPT = """\
You are an independent meta-reviewer evaluating a proposal.

Your job is to enumerate every concrete issue a rigorous adversarial review
SHOULD catch in this proposal. These become the reference set for measuring
how well different review processes cover the real issue space. You are NOT
reviewing on behalf of one approach or another — you are producing the
ground truth list.

For each issue, emit:
- id: short unique identifier (issue-1, issue-2, ...)
- category: one of
    {risk, gap, inconsistency, unverified-claim, scope-problem, assumption,
     spec-drift, contradiction}
- description: one-sentence concrete statement of the issue
- key_tokens: 2-5 distinctive lowercase tokens (file paths, function
  names, specific quoted phrases from the proposal) that would appear in
  any review flagging this issue. At least one token must be highly
  specific (a filename, a flag like "--verify-claims", or a function name
  like "compute_verdict"). Generic terms like "security" or "testing" do
  not count as distinctive.
- severity: one of {blocker, material, minor}
- rationale: 1-2 lines on why this matters (what goes wrong if unfixed)

Use the available tools to verify any claim the proposal makes about code
(file paths, function signatures, specific content). If a proposal asserts
X about the codebase, check X, and if X is wrong, add an issue for it.

Be exhaustive but NOT inflationary. Every issue must be concrete and
actionable. Emit no more than 20 issues per proposal. If a proposal is
simple and lacks issues, emit 3-5 and stop. If you emit zero issues, the
proposal is trivially clean — say so explicitly in a final JSON field.

Output format: a single JSON object of shape
  {"issues": [<issue1>, <issue2>, ...], "notes": "<optional>"}
No prose before or after. No code fences.
"""


# ── LLM wiring (imports lazily to keep the script light) ───────────────────


def _run_discoverer(
    proposal_text: str,
    model: str = DEFAULT_MODEL,
    timeout_seconds: int = 900,
) -> tuple[str | None, dict[str, Any] | None]:
    """Invoke the issue-discoverer LLM with tool access.

    Returns (raw_text, stats) where stats is a dict of token/tool usage.
    Returns (None, None) on failure — callers must handle.
    """
    try:
        import debate_common
        import debate_tools
        from llm_client import llm_tool_loop
    except ImportError as e:
        print(f"ERROR: import failed: {e}", file=sys.stderr)
        return None, None

    try:
        api_key, litellm_url, _ = debate_common._load_credentials()
    except Exception as e:
        print(f"ERROR: credential load failed: {e}", file=sys.stderr)
        return None, None

    user_content = (
        "## PROPOSAL UNDER REVIEW\n\n"
        f"{proposal_text}\n\n"
        "---\n\n"
        "Use your tools to verify claims about the codebase and to discover "
        "issues. Emit the JSON object described in the system prompt."
    )

    tool_log: list[dict[str, Any]] = []
    try:
        result = llm_tool_loop(
            system=MISS_DISCOVERER_SYSTEM_PROMPT,
            user=user_content,
            tools=debate_tools.TOOL_DEFINITIONS,
            tool_executor=debate_tools.execute_tool,
            model=model,
            max_turns=20,
            max_tokens=8000,
            timeout=timeout_seconds,
            base_url=litellm_url,
            api_key=api_key,
            on_tool_call=lambda turn, name, targs, res: tool_log.append(
                {"turn": turn, "tool": name}
            ),
        )
    except Exception as e:
        print(f"ERROR: discoverer LLM raised: {e}", file=sys.stderr)
        return None, None

    stats = {
        "model": model,
        "tool_calls": len(tool_log),
    }
    return result.get("content"), stats


# ── Output parsing + sanity check ──────────────────────────────────────────


def parse_discoverer_output(raw: str | None) -> dict[str, Any]:
    """Parse the discoverer's JSON. Returns {"issues": [...], "notes": ...,
    "parse_error": <optional>}."""
    if not raw:
        return {"issues": [], "parse_error": "empty output"}

    # Strip optional code fences.
    s = raw.strip()
    if s.startswith("```json"):
        s = s.split("\n", 1)[-1]
        if s.endswith("```"):
            s = s[:-3]
    elif s.startswith("```"):
        s = s.split("\n", 1)[-1]
        if s.endswith("```"):
            s = s[:-3]
    s = s.strip()

    try:
        obj = json.loads(s)
    except json.JSONDecodeError as e:
        # Try to extract the first balanced { ... } block.
        depth = 0
        start = None
        for i, ch in enumerate(s):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    try:
                        obj = json.loads(s[start:i + 1])
                        break
                    except json.JSONDecodeError:
                        continue
        else:
            return {"issues": [], "parse_error": f"invalid JSON: {e}"}

    if not isinstance(obj, dict):
        return {"issues": [], "parse_error": "top-level not an object"}

    issues = obj.get("issues")
    if not isinstance(issues, list):
        return {"issues": [], "parse_error": "missing or non-list 'issues'"}

    # Normalize each issue — fill in missing fields with defaults.
    clean: list[dict[str, Any]] = []
    for i, issue in enumerate(issues):
        if not isinstance(issue, dict):
            continue
        clean.append({
            "id": str(issue.get("id", f"issue-{i+1}")),
            "category": str(issue.get("category", "uncategorized")),
            "description": str(issue.get("description", "")).strip(),
            "key_tokens": [
                str(t).strip().lower()
                for t in (issue.get("key_tokens") or [])
                if str(t).strip()
            ],
            "severity": str(issue.get("severity", "material")),
            "rationale": str(issue.get("rationale", "")).strip(),
        })

    out: dict[str, Any] = {"issues": clean}
    if obj.get("notes"):
        out["notes"] = str(obj["notes"])
    return out


# ── Matcher (used by the scorer) ───────────────────────────────────────────


TOKEN_MATCH_THRESHOLD = 0.6  # require ≥60% of key_tokens to appear


def match_reference_issues(
    issues: list[dict[str, Any]],
    challenge_text: str,
    threshold: float = TOKEN_MATCH_THRESHOLD,
) -> dict[str, Any]:
    """For each reference issue, check whether the challenger output mentions
    its key tokens. An issue is "caught" when ≥threshold fraction of its
    key_tokens appear in challenge_text (case-insensitive substring).

    V1 strict-AND matching produced 80-100% miss rates on n=3 because
    challenger wording didn't match every token verbatim. Relaxed to a
    majority threshold (0.6) — still token-grounded and deterministic, but
    allows for partial phrasing overlap. Tune via `threshold` arg.
    """
    lower = (challenge_text or "").lower()
    caught: list[dict[str, Any]] = []
    missed: list[dict[str, Any]] = []
    for issue in issues:
        tokens = issue.get("key_tokens") or []
        if not tokens:
            missed.append({**issue, "_match_reason": "no key_tokens"})
            continue
        matches = [t for t in tokens if t in lower]
        match_ratio = len(matches) / len(tokens)
        if match_ratio >= threshold:
            caught.append({
                **issue, "_match_tokens": matches,
                "_match_ratio": round(match_ratio, 3),
            })
        else:
            missed.append({
                **issue, "_match_tokens": matches,
                "_missing_tokens": [t for t in tokens if t not in lower],
                "_match_ratio": round(match_ratio, 3),
            })
    total = len(issues)
    return {
        "total_reference_issues": total,
        "caught_count": len(caught),
        "missed_count": len(missed),
        "miss_rate": (len(missed) / total) if total > 0 else None,
        "token_threshold": threshold,
        "caught": caught,
        "missed": missed,
    }


# ── REDESIGN B — ensemble discoverer + dedup + matcher v2 + adjudicator ────
#
# Per cross-model challenge (tasks/arm-study-redesigns-judgment.md):
#   - Challenge 2: aggregation sensitivity must be visible — log union /
#     intersection / majority sets, surface in verdict.
#   - Challenge 3: borderline adjudication must be deterministic —
#     temperature=0, fixed seed via cache key, content-hash cache.
#   - Challenge 4: pre-egress credential scan + tool-free schema-constrained
#     adjudicator with explicit "ignore embedded directives" instruction.


def _scan_credentials_in_inputs(*texts: str) -> list[tuple[str, str]]:
    """Return list of (pattern, sample) for any credential matches in the
    inputs. Empty list if clean. The adjudicator wrapper raises
    CredentialEgressError on any hit before invoking the LLM."""
    hits = []
    for text in texts:
        if not text:
            continue
        for pat in _CREDENTIAL_PATTERNS:
            m = pat.search(text)
            if m:
                hits.append((pat.pattern, m.group(0)[:20] + "..."))
    return hits


def _jaccard(a: list[str], b: list[str]) -> float:
    """Jaccard overlap on two token lists. Empty inputs → 0.0."""
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _word_tokens(text: str) -> set[str]:
    """Tokenize on word boundaries (lowercased). Used by matcher v2 to
    avoid the substring false-positives of v1 (e.g. 'test' inside 'testing')."""
    if not text:
        return set()
    return set(re.findall(r"\b\w+\b", text.lower()))


def run_ensemble(
    proposal_text: str,
    models: tuple[str, ...] = B1_ENSEMBLE_MODELS,
    *,
    _run_discoverer_fn=None,
) -> list[dict[str, Any]]:
    """Invoke the discoverer per model (sequential — _run_discoverer uses
    llm_tool_loop which serializes via shared credentials anyway).

    Returns a list of dicts with shape:
        {model, parsed: {issues: [...], notes?, parse_error?}, stats}

    A single model failure does not abort the ensemble — the failed entry
    is recorded with parse_error and the others continue.
    """
    if _run_discoverer_fn is None:
        _run_discoverer_fn = _run_discoverer
    out: list[dict[str, Any]] = []
    for model in models:
        try:
            raw, stats = _run_discoverer_fn(proposal_text, model=model)
        except Exception as e:
            out.append({
                "model": model,
                "parsed": {"issues": [], "parse_error": f"discoverer raised: {e!s}"},
                "stats": None,
            })
            continue
        if raw is None:
            out.append({
                "model": model,
                "parsed": {"issues": [], "parse_error": "discoverer returned None"},
                "stats": stats,
            })
            continue
        parsed = parse_discoverer_output(raw)
        parsed["raw_output"] = raw
        out.append({"model": model, "parsed": parsed, "stats": stats})
    return out


def _issues_match(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Two ensemble issues are the same iff (a) categories match and
    (b) jaccard on key_tokens ≥ B1_DEDUP_TOKEN_OVERLAP."""
    if (a.get("category") or "").lower() != (b.get("category") or "").lower():
        return False
    return _jaccard(a.get("key_tokens") or [], b.get("key_tokens") or []) >= B1_DEDUP_TOKEN_OVERLAP


def dedup_ensemble(
    per_model_outputs: list[dict[str, Any]],
    min_votes_for_majority: int = B1_MIN_VOTES_FOR_MAJORITY,
) -> dict[str, Any]:
    """Group issues across models into union / intersection / majority sets.

    Each output issue carries `models_surfaced: [model_name, ...]` so the
    verdict can attribute coverage. The unified "issue" within a group uses
    the first-seen issue's id/description and the union of key_tokens.
    """
    n_models = len(per_model_outputs)
    # Build a flat list of (model, issue) tuples from successful parses.
    flat: list[tuple[str, dict[str, Any]]] = []
    for entry in per_model_outputs:
        model = entry["model"]
        parsed = entry.get("parsed") or {}
        if parsed.get("parse_error"):
            continue
        for issue in parsed.get("issues") or []:
            flat.append((model, issue))

    # Greedy clustering: each new issue either joins an existing cluster
    # (matches the cluster's first issue) or starts a new cluster.
    clusters: list[dict[str, Any]] = []
    for model, issue in flat:
        joined = False
        for cluster in clusters:
            if _issues_match(cluster["representative"], issue):
                if model not in cluster["models"]:
                    cluster["models"].append(model)
                # Union the key_tokens for downstream matching.
                cluster_tokens = set(cluster["representative"].get("key_tokens") or [])
                cluster_tokens.update(issue.get("key_tokens") or [])
                cluster["representative"]["key_tokens"] = sorted(cluster_tokens)
                joined = True
                break
        if not joined:
            clusters.append({
                "representative": dict(issue),
                "models": [model],
            })

    union: list[dict[str, Any]] = []
    intersection: list[dict[str, Any]] = []
    majority: list[dict[str, Any]] = []
    for cluster in clusters:
        rep = dict(cluster["representative"])
        rep["models_surfaced"] = list(cluster["models"])
        union.append(rep)
        if len(cluster["models"]) >= min_votes_for_majority:
            majority.append(rep)
        if len(cluster["models"]) == n_models and n_models > 0:
            intersection.append(rep)
    return {
        "union": union,
        "intersection": intersection,
        "majority": majority,
        "n_models": n_models,
        "n_clusters": len(clusters),
    }


_B1_PROMPT_CACHE: tuple[str, str] | None = None


def _load_b1_prompt() -> tuple[str, str]:
    """Load and split the B1 adjudicator prompt into (system, user_template).
    Cached at module level. Splits on '## SYSTEM' / '## USER' headings."""
    global _B1_PROMPT_CACHE
    if _B1_PROMPT_CACHE is not None:
        return _B1_PROMPT_CACHE
    text = B1_ADJUDICATOR_PROMPT_PATH.read_text()
    sys_marker = "\n## SYSTEM\n"
    usr_marker = "\n## USER\n"
    if sys_marker not in text or usr_marker not in text:
        raise ValueError(
            f"b1-adjudicator-prompt.md missing required '## SYSTEM' / '## USER' "
            f"sections at {B1_ADJUDICATOR_PROMPT_PATH}"
        )
    sys_idx = text.index(sys_marker) + len(sys_marker)
    usr_idx = text.index(usr_marker)
    system = text[sys_idx:usr_idx].strip()
    user_template = text[usr_idx + len(usr_marker):].strip()
    _B1_PROMPT_CACHE = (system, user_template)
    return _B1_PROMPT_CACHE


def _hash_adjudication(
    challenge_text: str, issue: dict[str, Any], model_version: str,
) -> str:
    """Stable cache key for an adjudication call.

    Includes a hash of the b1-adjudicator-prompt.md template so prompt
    edits invalidate cached YES/NO decisions (post-build review Finding 1).
    """
    h = _hashlib.sha256()
    h.update(model_version.encode("utf-8"))
    h.update(b"\x1e")
    h.update(challenge_text.encode("utf-8"))
    h.update(b"\x1e")
    h.update(str(issue.get("id", "")).encode("utf-8"))
    h.update(b"\x1e")
    tokens = "|".join(sorted(issue.get("key_tokens") or []))
    h.update(tokens.encode("utf-8"))
    h.update(b"\x1e")
    h.update(str(issue.get("description", "")).encode("utf-8"))
    h.update(b"\x1e")
    try:
        system, user_template = _load_b1_prompt()
        h.update(system.encode("utf-8"))
        h.update(b"\x1d")
        h.update(user_template.encode("utf-8"))
    except Exception:
        h.update(b"prompt-unavailable")
    return h.hexdigest()


def _load_adjudication_cache(
    cache_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    if cache_path is None:
        cache_path = B1_ADJUDICATION_CACHE_PATH
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
            key = entry.get("adj_hash")
            if isinstance(key, str):
                out[key] = entry
    return out


def _persist_adjudication_entry(
    entry: dict[str, Any], cache_path: Path | None = None,
) -> None:
    if cache_path is None:
        cache_path = B1_ADJUDICATION_CACHE_PATH
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def _log_adjudication_event(
    payload: dict[str, Any], log_path: Path | None = None,
) -> None:
    if log_path is None:
        log_path = B1_ADJUDICATION_LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")


def _excerpt_around_tokens(
    text: str, tokens: list[str], window: int = B1_EXCERPT_WINDOW,
) -> str:  # noqa: E501
    # Known edge case (post-build review v2 Finding 6): for hyphen-bearing
    # tokens like "foo-bar", the (?<!\w)...(?!\w) boundary is satisfied by
    # adjacent hyphens too — so "foo-bar" matches inside "foo-bar-baz".
    # Acceptable for the current discoverer key-token vocabulary (filename
    # + function-name fragments rarely collide this way); revisit only if a
    # real false-positive is observed in the n=10 calibration sweep.
    """Return up to `window` chars around the first whole-word match of
    a key_token in `text`. Falls back to first `window` chars if no token
    matches.

    Post-build review Finding 4: word-boundary lookup matches the matcher-v2
    semantics — a substring search would reintroduce partial-token false
    positives (e.g. matching 'test' inside 'testing') in the adjudicator
    excerpt, biasing the LLM toward YES on token noise.
    """
    if not text:
        return ""
    lower = text.lower()
    for token in tokens:
        t = token.lower()
        # Whole-word match using regex word boundaries.
        m = re.search(rf"(?<!\w){re.escape(t)}(?!\w)", lower)
        if m:
            idx = m.start()
            half = window // 2
            start = max(0, idx - half)
            end = min(len(text), idx + half)
            return text[start:end]
    return text[:window]


def adjudicate_borderline(
    challenge_text: str,
    issue: dict[str, Any],
    model: str = B1_ADJUDICATOR_MODEL,
    cache: dict[str, dict[str, Any]] | None = None,
    cache_path: Path | None = None,
    log_path: Path | None = None,
    _llm_call_json=None,
) -> dict[str, Any]:
    """Tool-free LLM binary adjudication for borderline matches.

    Returns {decision: 'YES'|'NO', rationale, parse_ok, cache_hit, error}.
    Raises CredentialEgressError if challenge_text contains credential
    patterns (pre-egress safety stop).

    Post-build review Finding 3: when called with `cache=None`, loads the
    on-disk JSONL cache so cross-process reruns hit cached decisions
    rather than re-invoking the LLM.
    """
    if cache_path is None:
        cache_path = B1_ADJUDICATION_CACHE_PATH
    if log_path is None:
        log_path = B1_ADJUDICATION_LOG_PATH
    if cache is None:
        cache = _load_adjudication_cache(cache_path=cache_path)

    hits = _scan_credentials_in_inputs(challenge_text, issue.get("description") or "")
    if hits:
        raise CredentialEgressError(
            f"credential pattern in borderline-adjudication input: "
            f"{[h[0] for h in hits]}"
        )

    cache_key = _hash_adjudication(challenge_text, issue, model)
    if cache is not None and cache_key in cache:
        cached = cache[cache_key]
        return {
            "decision": cached.get("decision", "NO"),
            "rationale": cached.get("rationale", ""),
            "parse_ok": cached.get("parse_ok", True),
            "cache_hit": True,
            "error": None,
        }

    if _llm_call_json is None:
        try:
            from llm_client import llm_call_json as _llm_call_json
        except ImportError as e:
            return {
                "decision": "NO", "rationale": "", "parse_ok": False,
                "cache_hit": False,
                "error": f"llm_client import failed: {e}",
            }

    # Post-build review v2 Finding 2: graceful prompt-load failure mirrors
    # the LLM-import-failure path. Conservative on degraded mode (NO + error)
    # so the matcher marks the issue missed rather than crashing the run.
    try:
        system, user_template = _load_b1_prompt()
    except Exception as e:
        return {
            "decision": "NO", "rationale": "", "parse_ok": False,
            "cache_hit": False,
            "error": f"prompt load failed: {e!s}",
        }
    excerpt = _excerpt_around_tokens(
        challenge_text, issue.get("key_tokens") or []
    )
    user_filled = (
        user_template
        .replace("{issue_id}", str(issue.get("id", "")))
        .replace("{issue_category}", str(issue.get("category", "")))
        .replace("{issue_description}", str(issue.get("description", "")))
        .replace("{issue_key_tokens}",
                 ", ".join(issue.get("key_tokens") or []))
        .replace("{issue_severity}", str(issue.get("severity", "")))
        .replace("{challenger_excerpt}", excerpt)
    )

    decision = "NO"
    rationale = ""
    parse_ok = False
    error: str | None = None
    try:
        result = _llm_call_json(
            system=system, user=user_filled, model=model,
            temperature=0.0,
            max_tokens=B1_ADJUDICATOR_MAX_TOKENS,
            timeout=B1_ADJUDICATOR_TIMEOUT,
        )
        if isinstance(result, dict):
            d = result.get("decision")
            if isinstance(d, str) and d.upper() in ("YES", "NO"):
                decision = d.upper()
                parse_ok = True
            else:
                error = f"decision not YES/NO: {d!r}"
            r = result.get("rationale")
            if isinstance(r, str):
                rationale = r[:160]
        else:
            error = "JSON top-level not an object"
    except Exception as e:
        error = f"llm_call_json raised: {e!s}"

    entry = {
        "adj_hash": cache_key,
        "issue_id": issue.get("id"),
        "decision": decision,
        "rationale": rationale,
        "parse_ok": parse_ok,
        "model": model,
        "error": error,
    }
    _persist_adjudication_entry(entry, cache_path=cache_path)
    if cache is not None:
        cache[cache_key] = entry

    _log_adjudication_event({
        "ts": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "kind": "b1-adjudication",
        "issue_id": issue.get("id"),
        "decision": decision,
        "parse_ok": parse_ok,
        "error": error,
        "model": model,
    }, log_path=log_path)

    return {
        "decision": decision, "rationale": rationale,
        "parse_ok": parse_ok, "cache_hit": False, "error": error,
    }


def match_reference_issues_v2(
    issues: list[dict[str, Any]],
    challenge_text: str,
    threshold_caught: float = B1_MATCHER_CAUGHT_THRESHOLD,
    threshold_borderline: float = B1_MATCHER_BORDERLINE_THRESHOLD,
    *,
    _adjudicator_fn=None,
    adjudicator_model: str = B1_ADJUDICATOR_MODEL,
    adjudicator_cache: dict[str, dict[str, Any]] | None = None,
    adjudicator_cache_path: Path | None = None,
    adjudicator_log_path: Path | None = None,
    skip_adjudication: bool = False,
) -> dict[str, Any]:
    """Word-boundary token matcher with LLM adjudication for borderline cases.

    For each reference issue:
      - overlap ratio ≥ threshold_caught          → caught
      - overlap ratio in [borderline, caught)     → adjudicator (YES → caught,
                                                                 NO  → missed)
      - overlap ratio < threshold_borderline      → missed
    Substring false-positives from v1 (e.g. "test" matching inside "testing")
    are eliminated by tokenizing on word boundaries before computing overlap.
    """
    if _adjudicator_fn is None:
        _adjudicator_fn = adjudicate_borderline

    text_tokens = _word_tokens(challenge_text)
    caught: list[dict[str, Any]] = []
    missed: list[dict[str, Any]] = []
    borderline_count = 0
    adjudicator_calls = 0

    for issue in issues:
        tokens = [t.lower() for t in (issue.get("key_tokens") or [])]
        if not tokens:
            missed.append({**issue, "_match_reason": "no key_tokens"})
            continue
        # Word-boundary match: token must appear as a whole word.
        matched_tokens = [t for t in tokens if t in text_tokens]
        # Multi-word tokens (e.g. "verify-claims") fall back to word-boundary
        # search via the full text since they contain hyphens.
        for t in tokens:
            if t in matched_tokens:
                continue
            if re.search(rf"(?<!\w){re.escape(t)}(?!\w)",
                         challenge_text.lower()):
                matched_tokens.append(t)
        ratio = len(matched_tokens) / len(tokens)
        ratio_rounded = round(ratio, 3)

        if ratio >= threshold_caught:
            caught.append({
                **issue, "_match_tokens": matched_tokens,
                "_match_ratio": ratio_rounded,
                "_adjudicated": False,
            })
        elif ratio >= threshold_borderline and not skip_adjudication:
            borderline_count += 1
            adjudicator_calls += 1
            try:
                verdict = _adjudicator_fn(
                    challenge_text=challenge_text, issue=issue,
                    model=adjudicator_model,
                    cache=adjudicator_cache,
                    cache_path=adjudicator_cache_path,
                    log_path=adjudicator_log_path,
                )
            except CredentialEgressError as e:
                # Treat as missed and surface reason — fail-closed on egress.
                missed.append({
                    **issue, "_match_tokens": matched_tokens,
                    "_match_ratio": ratio_rounded,
                    "_adjudicated": False,
                    "_match_reason": f"credential-egress-blocked: {e!s}",
                })
                continue
            if verdict["decision"] == "YES":
                caught.append({
                    **issue, "_match_tokens": matched_tokens,
                    "_match_ratio": ratio_rounded,
                    "_adjudicated": True,
                    "_adjudicator_rationale": verdict["rationale"],
                })
            else:
                missed.append({
                    **issue, "_match_tokens": matched_tokens,
                    "_missing_tokens": [t for t in tokens
                                        if t not in matched_tokens],
                    "_match_ratio": ratio_rounded,
                    "_adjudicated": True,
                    "_adjudicator_rationale": verdict["rationale"],
                })
        else:
            missed.append({
                **issue, "_match_tokens": matched_tokens,
                "_missing_tokens": [t for t in tokens
                                    if t not in matched_tokens],
                "_match_ratio": ratio_rounded,
                "_adjudicated": False,
            })

    total = len(issues)
    return {
        "total_reference_issues": total,
        "caught_count": len(caught),
        "missed_count": len(missed),
        "miss_rate": (len(missed) / total) if total > 0 else None,
        "token_threshold_caught": threshold_caught,
        "token_threshold_borderline": threshold_borderline,
        "borderline_count": borderline_count,
        "adjudicator_calls": adjudicator_calls,
        "caught": caught,
        "missed": missed,
    }


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--proposal", required=True, type=Path,
                    help="Path to proposal markdown")
    ap.add_argument("--output", type=Path, default=None,
                    help="Path to write reference-issues JSON (default: stdout)")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help="Single-model fallback (ignored when --ensemble)")
    ap.add_argument("--ensemble", action="store_true",
                    help="Run multi-model ensemble (REDESIGN B). Issues "
                         "deduped across models; majority-vote becomes "
                         "primary; union/intersection logged for sensitivity.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Emit fixture issues without LLM call")
    args = ap.parse_args()

    if not args.proposal.exists():
        print(f"ERROR: proposal not found: {args.proposal}", file=sys.stderr)
        return 1

    if args.dry_run:
        parsed = {
            "issues": [
                {
                    "id": "issue-1", "category": "gap",
                    "description": "DRY_RUN fixture issue",
                    "key_tokens": ["dry-run"], "severity": "minor",
                    "rationale": "placeholder",
                },
            ],
            "notes": "dry-run fixture",
        }
        stats = {"model": "dry-run", "tool_calls": 0}
        out = {
            "discoverer_stats": stats,
            "proposal_path": str(args.proposal),
            **parsed,
        }
    elif args.ensemble:
        proposal_text = args.proposal.read_text()
        per_model = run_ensemble(proposal_text)
        agg = dedup_ensemble(per_model)
        # Primary issues = majority-vote (used by scorer + verdict).
        out = {
            "proposal_path": str(args.proposal),
            "issues": agg["majority"],
            "ensemble_models": list(B1_ENSEMBLE_MODELS),
            "aggregation_provenance": {
                "union": agg["union"],
                "intersection": agg["intersection"],
                "majority": agg["majority"],
                "n_models": agg["n_models"],
                "n_clusters": agg["n_clusters"],
            },
            "per_model_stats": [
                {"model": e["model"], "stats": e.get("stats"),
                 "parse_error": (e.get("parsed") or {}).get("parse_error")}
                for e in per_model
            ],
        }
        # Mirror v1 shape so existing scorer reads continue to work.
        if not out["issues"]:
            out["parse_error"] = (
                "majority-vote produced 0 issues — see per_model_stats for failures"
            )
    else:
        proposal_text = args.proposal.read_text()
        raw, stats = _run_discoverer(proposal_text, model=args.model)
        if raw is None:
            return 1
        parsed = parse_discoverer_output(raw)
        parsed["raw_output"] = raw
        out = {
            "discoverer_stats": stats or {},
            "proposal_path": str(args.proposal),
            **parsed,
        }

    serialized = json.dumps(out, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized)
    sys.stdout.write(serialized)

    if out.get("parse_error"):
        print(f"WARNING: {out['parse_error']}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

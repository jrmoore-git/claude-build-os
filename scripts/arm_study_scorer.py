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
        # concatenated challenge + proposal. Failures are recorded but do
        # not abort scoring — downstream aggregation reads what's available.
        if proposal_path is not None and proposal_path.is_file():
            arm_verifications[arm] = _verify_ground_truth_dimensions(
                combined, proposal_path
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
    labels = json.loads(labels_path.read_text())
    scored = unblind(scored, labels)
    scored["metadata"] = {
        "dry_run": False,
        "judges": judges,
        "run_id": run_id,
        "verify_claims_judge": judges[0],
    }
    return scored


def _verify_ground_truth_dimensions(
    challenge_path: Path,
    proposal_path: Path,
) -> dict[str, Any]:
    """Read the per-arm concatenated challenge file and the proposal, run
    the claim verifier in-process, and return its result dict. Per-item
    mapping from VERIFIED/FALSIFIED/UNRESOLVABLE to extracted items is
    deferred to Phase 2 per D39 — this stores the raw verifier_text so
    Phase 2 can observe real output before wiring the matcher."""
    try:
        challenge_text = challenge_path.read_text()
    except OSError as e:
        return {"status": "failed", "error": f"read challenge failed: {e}",
                "verification_text": None, "stats": None}
    try:
        proposal_text = proposal_path.read_text()
    except OSError as e:
        return {"status": "failed", "error": f"read proposal failed: {e}",
                "verification_text": None, "stats": None}
    return run_claim_verifier_inprocess(challenge_text, proposal_text)


def _attach_verifications(
    scored: dict[str, Any],
    verifications: dict[str, dict[str, Any]],
) -> None:
    """Attach verify-claims output to each ground-truth dimension in-place.

    `debate.py judge --verify-claims` emits a "## Claim Verification Results"
    section with per-claim VERIFIED / FALSIFIED / UNRESOLVABLE statuses
    (documented at debate.py:1347 in VERIFIER_SYSTEM_PROMPT). Phase 1 stores
    the raw output; Phase 2 dry run will observe real judge responses and
    implement the per-item matching that maps verifier claims to
    judge-extracted items, producing valid / hallucinated / partial /
    unverifiable labels on each item. See plan Files table row for this
    script."""
    for arm_label, arm_data in scored.get("arms", {}).items():
        verif = verifications.get(arm_label, {})
        entry = {
            "status": verif.get("status", "unknown"),
            "stats": verif.get("stats"),
            "verification_text": (verif.get("verification_text") or "")[:4000],
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

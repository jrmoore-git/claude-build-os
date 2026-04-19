#!/usr/bin/env python3.11
"""
Arm-comparison study: retrospective plan/refined-doc quality-delta scorer
(item 6 of metric-fix plan, Dim 6 = plan_quality_delta).

For each arm, asks whether the arm's challenger items actually LANDED in
the downstream plan/refined-doc artifact. Higher landing rate = challenger
was more load-bearing. Comparing arms' landing rates gives Dim 6 signal.

Auto-discovers downstream artifact in priority order:
    tasks/<proposal_stem>-plan.md
    tasks/<proposal_stem>-refined.md
    tasks/<proposal_stem>-judgment.md

If none exists, emits "no-downstream-artifact" and exits 0 (not-scorable).

Dim 7 (code_review_quality_delta) is deferred — would need code-diff
analysis linking to proposal commits; non-trivial to automate.

Usage:
    python3.11 scripts/arm_study_retrospective.py --run-id <run-id>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
STUDY_ROOT = REPO_ROOT / "stores" / "arm-study"
DEFAULT_MODEL = "claude-sonnet-4-6"


RETROSPECTIVE_SYSTEM_PROMPT = """\
You are a retrospective scorer. You are given two documents:

1. A CHALLENGER TRANSCRIPT — the output of a review process on a proposal.
2. A DOWNSTREAM ARTIFACT — the plan, refined spec, or judgment that was
   produced after the review.

Your job is to classify every concrete, load-bearing item in the
challenger transcript as one of:

- LANDED: the item's substance is reflected in the downstream artifact
  (the artifact incorporates or addresses the challenger's point).
- PARTIAL: the item is partially acknowledged or narrowed but not fully
  adopted.
- NOT_LANDED: the item is ignored, rejected, or absent from the artifact.

You are NOT evaluating whether the item was right or wrong — only whether
the downstream work incorporated it. A wrong item that the artifact
explicitly rejects also counts as "LANDED" (the process engaged with it);
a right item the artifact ignored is NOT_LANDED.

For each item, emit:
- item_id: short identifier (you can assign sequential ids like item-1,
  item-2, etc.)
- short_text: 1-line paraphrase of the challenger item
- landed: one of LANDED, PARTIAL, NOT_LANDED
- evidence: 1-sentence pointer to where in the downstream artifact the
  item appears (quote a key phrase or reference a section heading), or
  "not present" for NOT_LANDED.

Ignore items that are purely process comments ("the review format is
good"), style notes, or other non-substantive content. Focus on concrete
items: risks, gaps, redirections, specific objections, proposed changes.

Output format: single JSON object of shape
  {"items": [<item1>, ...], "summary": {"total": N, "landed": X,
     "partial": Y, "not_landed": Z}, "notes": "<optional>"}
No prose before or after. No code fences.
"""


# ── Artifact discovery ──────────────────────────────────────────────────────


def discover_downstream_artifact(proposal_path: Path) -> Path | None:
    """Look for tasks/<stem>-plan.md, then -refined.md, then -judgment.md."""
    # proposal_path is something like tasks/foo-proposal.md; derive the stem.
    stem = proposal_path.stem
    if stem.endswith("-proposal"):
        stem = stem[: -len("-proposal")]
    candidates = [
        proposal_path.parent / f"{stem}-plan.md",
        proposal_path.parent / f"{stem}-refined.md",
        proposal_path.parent / f"{stem}-judgment.md",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


# ── LLM wiring ──────────────────────────────────────────────────────────────


def _run_retrospective(
    challenge_text: str,
    downstream_text: str,
    model: str = DEFAULT_MODEL,
    timeout_seconds: int = 600,
) -> tuple[str | None, dict[str, Any] | None]:
    """Run the retrospective scorer LLM. No tools needed — the reasoning is
    on the two already-provided documents. Returns (raw_text, stats)."""
    try:
        import debate_common
        from llm_client import llm_call
    except ImportError as e:
        print(f"ERROR: import failed: {e}", file=sys.stderr)
        return None, None

    try:
        api_key, litellm_url, _ = debate_common._load_credentials()
    except Exception as e:
        print(f"ERROR: credential load failed: {e}", file=sys.stderr)
        return None, None

    user_content = (
        "## CHALLENGER TRANSCRIPT\n\n"
        f"{challenge_text}\n\n"
        "---\n\n"
        "## DOWNSTREAM ARTIFACT\n\n"
        f"{downstream_text}\n\n"
        "---\n\n"
        "Classify each substantive challenger item per the instructions."
    )

    try:
        content = llm_call(
            system=RETROSPECTIVE_SYSTEM_PROMPT,
            user=user_content,
            model=model,
            max_tokens=8000,
            timeout=timeout_seconds,
            base_url=litellm_url,
            api_key=api_key,
        )
    except Exception as e:
        print(f"ERROR: retrospective LLM raised: {e}", file=sys.stderr)
        return None, None

    stats = {"model": model}
    return content, stats


# ── Parsing ────────────────────────────────────────────────────────────────


def parse_retrospective_output(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {"items": [], "parse_error": "empty output"}

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
        depth = 0
        start = None
        obj = None
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
        if obj is None:
            return {"items": [], "parse_error": f"invalid JSON: {e}"}

    if not isinstance(obj, dict):
        return {"items": [], "parse_error": "top-level not an object"}

    items = obj.get("items")
    if not isinstance(items, list):
        return {"items": [], "parse_error": "missing or non-list 'items'"}

    valid_outcomes = ("LANDED", "PARTIAL", "NOT_LANDED")
    clean: list[dict[str, Any]] = []
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            continue
        landed = str(it.get("landed", "")).upper().strip()
        if landed not in valid_outcomes:
            landed = "NOT_LANDED"
        clean.append({
            "item_id": str(it.get("item_id", f"item-{i+1}")),
            "short_text": str(it.get("short_text", "")).strip(),
            "landed": landed,
            "evidence": str(it.get("evidence", "")).strip(),
        })

    total = len(clean)
    counts = {"LANDED": 0, "PARTIAL": 0, "NOT_LANDED": 0}
    for it in clean:
        counts[it["landed"]] += 1

    summary = {
        "total": total,
        "landed": counts["LANDED"],
        "partial": counts["PARTIAL"],
        "not_landed": counts["NOT_LANDED"],
        "landing_rate_full": (counts["LANDED"] / total) if total > 0 else None,
        "landing_rate_with_partial": (
            (counts["LANDED"] + 0.5 * counts["PARTIAL"]) / total
            if total > 0 else None
        ),
    }

    out: dict[str, Any] = {"items": clean, "summary": summary}
    if obj.get("notes"):
        out["notes"] = str(obj["notes"])
    return out


# ── Main ───────────────────────────────────────────────────────────────────


def score_run(run_id: str, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    """Compute retrospective scoring for one run. Returns dict ready to
    write to stores/arm-study/<run-id>/retrospective.json."""
    run_dir = STUDY_ROOT / run_id
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"manifest.json not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())
    proposal_rel = manifest.get("proposal_path")
    if not proposal_rel:
        raise RuntimeError("manifest missing proposal_path")
    proposal_path = REPO_ROOT / proposal_rel
    downstream = discover_downstream_artifact(proposal_path)

    out: dict[str, Any] = {
        "run_id": run_id,
        "proposal_path": str(proposal_rel),
        "downstream_artifact": str(downstream.relative_to(REPO_ROOT)) if downstream else None,
    }

    if downstream is None:
        out["status"] = "no-downstream-artifact"
        out["reason"] = (
            f"no tasks/<stem>-plan.md, -refined.md, or -judgment.md found "
            f"adjacent to {proposal_rel}"
        )
        return out

    labels = json.loads((run_dir / "labels.json").read_text())
    downstream_text = downstream.read_text()

    per_arm: dict[str, Any] = {}
    for arm_neutral in ("arm-x", "arm-y"):
        combined = run_dir / arm_neutral / "_combined-for-scoring.md"
        if not combined.is_file():
            per_arm[labels[arm_neutral]] = {
                "status": "missing-challenge-file",
                "reason": str(combined.relative_to(REPO_ROOT)),
            }
            continue
        challenge_text = combined.read_text()
        raw, stats = _run_retrospective(challenge_text, downstream_text, model=model)
        if raw is None:
            per_arm[labels[arm_neutral]] = {"status": "llm-failed"}
            continue
        parsed = parse_retrospective_output(raw)
        per_arm[labels[arm_neutral]] = {
            "status": "scored" if not parsed.get("parse_error") else "parse-error",
            "stats": stats,
            **parsed,
        }

    out["status"] = "scored"
    out["per_arm"] = per_arm
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--output", type=Path, default=None,
                    help="Output path (default: stores/arm-study/<run-id>/"
                         "retrospective.json)")
    args = ap.parse_args()

    try:
        out = score_run(args.run_id, model=args.model)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    target = args.output or (STUDY_ROOT / args.run_id / "retrospective.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    sys.stdout.write(json.dumps(out, indent=2, sort_keys=True) + "\n")
    return 0 if out["status"] == "scored" else 2


if __name__ == "__main__":
    sys.exit(main())

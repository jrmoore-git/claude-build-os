#!/usr/bin/env python3.11
"""
Arm-comparison study verdict (SCAFFOLD ONLY — Phase 1).

Reads scorer output (from arm_study_scorer.py) and emits a verdict.
Phase 1 scope: interface, family-exclusion check, and a stub
compute_verdict() that always returns "evidence-gathering-only".

The full decision rule (substantive-count weighting + convergence thresholds
+ no-regression check) is deferred to Phase 3 per the plan — Phase 2
validity dry run must pass first.

See tasks/arm-comparison-methodology-validation-plan.md Phase 3.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STORE = REPO_ROOT / "stores" / "arm-study"


# ── Family exclusion (same rule as scorer) ─────────────────────────────────


def enforce_non_claude_from_scored(scored: dict[str, Any]) -> list[str]:
    """Read judge IDs from scored metadata and verify none are Claude-family.
    Raises ValueError if a Claude-family judge is found or if metadata is
    missing the judges field."""
    meta = scored.get("metadata") or {}
    judges = meta.get("judges")
    if not judges or not isinstance(judges, list):
        raise ValueError(
            "scored input missing metadata.judges; cannot enforce family-exclusion"
        )
    bad = [j for j in judges if isinstance(j, str) and j.startswith("claude-")]
    if bad:
        raise ValueError(
            f"judge family-exclusion: Claude-family judges not permitted. "
            f"Rejected: {bad}"
        )
    return list(judges)


# ── Stub verdict (Phase 3 will implement the full rule) ────────────────────


# TODO(phase-3): implement decision rule with substantive-count weighting +
# convergence thresholds + no-regression check. Primary outcome per the
# refined methodology is Dimension 5 (miss rate) from the prospective arm
# at n>=5. Secondary: Dimensions 1-4, 6, 7. Default hedged to
# "no routing change" unless Arm B beats Arm A on majority of dimensions
# by substantive-count AND no regression on hallucination rate AND
# convergence rate >= 70% AND sample size adequate.
def compute_verdict(scored_data: dict[str, Any]) -> dict[str, Any]:
    """Phase 1 stub. Always returns evidence-gathering-only."""
    return {
        "verdict": "evidence-gathering-only",
        "reason": "Phase 3 decision logic not yet implemented",
    }


# ── Fixture for --dry-run ──────────────────────────────────────────────────


def _dry_run_scored_fixture() -> dict[str, Any]:
    """Minimal scored input that satisfies family-exclusion and shape checks."""
    return {
        "metadata": {
            "dry_run": True,
            "judges": ["gpt-5.4", "gemini-3.1-pro"],
            "run_id": "dry-run-fixture",
        },
        "arms": {
            "arm-a": {},
            "arm-b": {},
        },
        "aggregate_inconclusive": False,
        "unblinded": True,
    }


# ── Output ─────────────────────────────────────────────────────────────────


def render_markdown(verdict: dict[str, Any], scored: dict[str, Any]) -> str:
    meta = scored.get("metadata", {})
    lines = [
        "# Arm-comparison verdict",
        "",
        f"- **verdict**: `{verdict.get('verdict')}`",
        f"- **reason**: {verdict.get('reason', '')}",
        f"- **run_id**: {meta.get('run_id', '—')}",
        f"- **judges**: {', '.join(meta.get('judges', []))}",
        "",
        "_Phase 1 scaffold: full decision logic lands in Phase 3._",
        "",
    ]
    return "\n".join(lines) + "\n"


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--run-id", default=None,
                     help="Read scored input from <store_root>/<run-id>/scored.json")
    src.add_argument("--scored-file", type=Path, default=None,
                     help="Explicit path to scored JSON file")
    ap.add_argument("--store-root", type=Path, default=DEFAULT_STORE)
    ap.add_argument("--dry-run", action="store_true",
                    help="Use fixture scored input; no file I/O")
    ap.add_argument("--output-markdown", type=Path, default=None)
    args = ap.parse_args()

    if args.dry_run:
        scored = _dry_run_scored_fixture()
    elif args.scored_file:
        scored = json.loads(args.scored_file.read_text())
    elif args.run_id:
        scored_path = args.store_root / args.run_id / "scored.json"
        if not scored_path.is_file():
            print(f"ERROR: scored file not found: {scored_path}", file=sys.stderr)
            return 1
        scored = json.loads(scored_path.read_text())
    else:
        print("ERROR: pass --run-id, --scored-file, or --dry-run", file=sys.stderr)
        return 2

    try:
        enforce_non_claude_from_scored(scored)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    verdict = compute_verdict(scored)

    if args.output_markdown:
        args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
        args.output_markdown.write_text(render_markdown(verdict, scored))

    out = {"verdict": verdict, "metadata": scored.get("metadata", {})}
    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    # Also emit a short markdown block to stderr for human-readable trace.
    sys.stderr.write("\n" + render_markdown(verdict, scored))
    return 0


if __name__ == "__main__":
    sys.exit(main())

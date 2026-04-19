#!/usr/bin/env python3.11
"""
Arm-comparison study verdict (Phase 3).

Aggregates scored outputs from arm_study_scorer.py across N proposals and
emits a verdict dict + markdown summary.

Per D40 the primary trust metric is verifier accuracy on catch_rate:
`verified / (verified + falsified)`. The hallucination guardrail is the
falsified rate. Judge-count convergence is advisory only; substantive-count
per arm (mean across non-Claude judges per dimension, summed across
non-ground-truth dimensions) is the secondary signal.

Decision ladder (first matching rule wins):

  - n < MIN_SAMPLE_FOR_DIRECTIONAL (3)           -> insufficient-sample
  - any arm missing verifier data                -> evidence-gathering-only
  - |accuracy(B) - accuracy(A)| < 5pp            -> inconclusive
  - primary winner regresses hallucination > 2pp -> regression-blocked
  - primary + secondary disagree                 -> mixed-directional
  - primary + secondary agree, n < 5             -> directional-favor-<arm>
  - primary + secondary agree, n >= 5            -> confident-favor-<arm>

Any non-default verdict still surfaces every signal value so the reader can
audit the conclusion.

See tasks/decisions.md D40 for the methodology shift that motivates the
accuracy-first framing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STORE = REPO_ROOT / "stores" / "arm-study"

# Thresholds are module-level for auditability + test access.
PRIMARY_ACCURACY_DELTA_PP = 0.05  # 5pp accuracy gap needed to call a winner
HALLUCINATION_GUARDRAIL_PP = 0.02  # primary winner must not regress > 2pp
MIN_SAMPLE_FOR_DIRECTIONAL = 3
MIN_SAMPLE_FOR_CONFIDENT = 5

# Dimensions the verifier grounds directly (catch_rate) + active judge-only
# dims used for the secondary substantive-count signal. Dim 6/7 are
# retrospective-only per the plan and skipped unless scorable. miss_rate
# is ground-truth but produces 0/0 unless the review explicitly names gaps
# — excluded from secondary since it's usually empty.
ACCURACY_DIMENSION = "catch_rate"
SECONDARY_DIMENSIONS = (
    "direction_improvement",
    "nuance_caught",
    "net_new_ideas",
)


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


# ── Aggregation helpers ────────────────────────────────────────────────────


def _arm_verifier_stats(scored: dict[str, Any], arm: str) -> dict[str, int] | None:
    """Return verifier stats for one arm, or None if unavailable."""
    arm_data = scored.get("arms", {}).get(arm) or {}
    dim = arm_data.get(ACCURACY_DIMENSION) or {}
    vc = dim.get("verify_claims") or {}
    if vc.get("status") != "verified":
        return None
    stats = vc.get("stats") or {}
    required = ("verified", "falsified", "unresolvable", "claims_checked")
    if not all(k in stats for k in required):
        return None
    return {k: int(stats[k]) for k in required}


def _aggregate_accuracy(all_scored: list[dict[str, Any]]) -> dict[str, Any]:
    """Pool verifier stats across proposals, per arm. Accuracy excludes
    unresolvable; hallucination is falsified / claims_checked."""
    pooled = {"arm-a": {"verified": 0, "falsified": 0, "unresolvable": 0,
                        "claims_checked": 0, "missing": 0},
              "arm-b": {"verified": 0, "falsified": 0, "unresolvable": 0,
                        "claims_checked": 0, "missing": 0}}
    for scored in all_scored:
        for arm in ("arm-a", "arm-b"):
            stats = _arm_verifier_stats(scored, arm)
            if stats is None:
                pooled[arm]["missing"] += 1
                continue
            for k in ("verified", "falsified", "unresolvable", "claims_checked"):
                pooled[arm][k] += stats[k]

    def _rates(p: dict[str, int]) -> dict[str, float | None]:
        denom_acc = p["verified"] + p["falsified"]
        denom_hall = p["claims_checked"]
        return {
            "accuracy": (p["verified"] / denom_acc) if denom_acc > 0 else None,
            "hallucination_rate": (p["falsified"] / denom_hall) if denom_hall > 0 else None,
            "unresolvable_rate": (p["unresolvable"] / denom_hall) if denom_hall > 0 else None,
        }

    return {
        "arm-a": {**pooled["arm-a"], **_rates(pooled["arm-a"])},
        "arm-b": {**pooled["arm-b"], **_rates(pooled["arm-b"])},
    }


def _dim_mean_substantive(dim_data: dict[str, Any]) -> float | None:
    """Mean substantive-count across judges for one dim. Mean over n=2 is
    the median at n=2 and is stable under judge-label swap. None if the
    dim is not scorable or has no substantive_count."""
    sub = dim_data.get("substantive_count")
    if not isinstance(sub, dict) or not sub:
        return None
    vals = [v for v in sub.values() if isinstance(v, (int, float))]
    if not vals:
        return None
    return sum(vals) / len(vals)


def _aggregate_substantive(all_scored: list[dict[str, Any]]) -> dict[str, Any]:
    """Sum mean-across-judges substantive counts across proposals for each
    secondary dimension. Returns per-dim deltas (B-A) plus an aggregate
    (how many dims Arm B wins)."""
    per_dim: dict[str, dict[str, float]] = {
        dim: {"arm-a": 0.0, "arm-b": 0.0, "n_scored": 0}
        for dim in SECONDARY_DIMENSIONS
    }
    for scored in all_scored:
        for arm in ("arm-a", "arm-b"):
            arm_data = scored.get("arms", {}).get(arm) or {}
            for dim in SECONDARY_DIMENSIONS:
                mean = _dim_mean_substantive(arm_data.get(dim, {}))
                if mean is None:
                    continue
                per_dim[dim][arm] += mean
                if arm == "arm-a":
                    per_dim[dim]["n_scored"] += 1  # count once per proposal

    dim_winners = {}
    for dim, totals in per_dim.items():
        delta = totals["arm-b"] - totals["arm-a"]
        if delta > 0:
            dim_winners[dim] = "arm-b"
        elif delta < 0:
            dim_winners[dim] = "arm-a"
        else:
            dim_winners[dim] = "tie"

    b_wins = sum(1 for w in dim_winners.values() if w == "arm-b")
    a_wins = sum(1 for w in dim_winners.values() if w == "arm-a")
    return {
        "per_dim_totals": per_dim,
        "per_dim_winners": dim_winners,
        "b_dim_wins": b_wins,
        "a_dim_wins": a_wins,
        "majority_winner": (
            "arm-b" if b_wins > a_wins else
            "arm-a" if a_wins > b_wins else "tie"
        ),
    }


def _convergence_note(all_scored: list[dict[str, Any]]) -> dict[str, Any]:
    """D40 demoted convergence to advisory. Summarize it so the markdown
    can surface the noise level without gating on it."""
    count_converged = 0
    count_total = 0
    deltas = []
    for scored in all_scored:
        for arm in ("arm-a", "arm-b"):
            arm_data = scored.get("arms", {}).get(arm) or {}
            for dim in (ACCURACY_DIMENSION,) + SECONDARY_DIMENSIONS:
                conv = (arm_data.get(dim) or {}).get("convergence") or {}
                if "count_converged" in conv:
                    count_total += 1
                    if conv["count_converged"]:
                        count_converged += 1
                    if isinstance(conv.get("count_delta"), (int, float)):
                        deltas.append(abs(conv["count_delta"]))
    return {
        "dims_converged": count_converged,
        "dims_total": count_total,
        "convergence_rate": (
            count_converged / count_total if count_total > 0 else None
        ),
        "mean_abs_count_delta": (sum(deltas) / len(deltas)) if deltas else None,
        "max_abs_count_delta": max(deltas) if deltas else None,
    }


# ── Decision rule ──────────────────────────────────────────────────────────


def compute_verdict(all_scored: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate across N proposals and return a verdict dict.

    Input: list of scored.json contents (one per proposal). Family-exclusion
    should already have been enforced on each input by the caller.

    Output keys:
      verdict: one of the labels in the decision ladder
      reason: short string explaining the selected label
      n_proposals: count
      accuracy: per-arm accuracy/hallucination/unresolvable stats
      secondary: per-dim substantive-count deltas + majority winner
      convergence: advisory convergence note
      decision_thresholds: constants used for auditability
    """
    n = len(all_scored)
    thresholds = {
        "primary_accuracy_delta_pp": PRIMARY_ACCURACY_DELTA_PP,
        "hallucination_guardrail_pp": HALLUCINATION_GUARDRAIL_PP,
        "min_sample_for_directional": MIN_SAMPLE_FOR_DIRECTIONAL,
        "min_sample_for_confident": MIN_SAMPLE_FOR_CONFIDENT,
    }

    base = {
        "n_proposals": n,
        "decision_thresholds": thresholds,
        "accuracy": _aggregate_accuracy(all_scored) if n > 0 else None,
        "secondary": _aggregate_substantive(all_scored) if n > 0 else None,
        "convergence": _convergence_note(all_scored) if n > 0 else None,
    }

    if n < MIN_SAMPLE_FOR_DIRECTIONAL:
        return {**base,
                "verdict": "insufficient-sample",
                "reason": f"n={n} < {MIN_SAMPLE_FOR_DIRECTIONAL}; "
                          f"need more proposals before any directional call"}

    acc = base["accuracy"]
    acc_a = acc["arm-a"]["accuracy"]
    acc_b = acc["arm-b"]["accuracy"]
    if acc_a is None or acc_b is None:
        return {**base,
                "verdict": "evidence-gathering-only",
                "reason": "verifier accuracy missing on one or both arms; "
                          "cannot compute primary signal"}

    delta = acc_b - acc_a
    if abs(delta) < PRIMARY_ACCURACY_DELTA_PP:
        return {**base,
                "verdict": "inconclusive",
                "reason": f"accuracy delta {delta*100:+.1f}pp is within "
                          f"±{PRIMARY_ACCURACY_DELTA_PP*100:.0f}pp noise floor"}

    primary_winner = "arm-b" if delta > 0 else "arm-a"
    primary_loser = "arm-a" if primary_winner == "arm-b" else "arm-b"

    hall_winner = acc[primary_winner]["hallucination_rate"]
    hall_loser = acc[primary_loser]["hallucination_rate"]
    if hall_winner is None or hall_loser is None:
        return {**base,
                "verdict": "evidence-gathering-only",
                "reason": "hallucination guardrail not computable; "
                          "cannot promote primary signal"}

    if hall_winner - hall_loser > HALLUCINATION_GUARDRAIL_PP:
        return {**base,
                "verdict": "regression-blocked",
                "reason": f"primary winner ({primary_winner}) hallucinates "
                          f"{(hall_winner - hall_loser)*100:+.1f}pp more than "
                          f"{primary_loser}; guardrail blocks promotion",
                "primary_winner": primary_winner}

    sec = base["secondary"]
    sec_winner = sec["majority_winner"]

    if sec_winner != primary_winner and sec_winner != "tie":
        return {**base,
                "verdict": "mixed-directional",
                "reason": f"primary signal favors {primary_winner} "
                          f"but secondary (substantive-count majority) "
                          f"favors {sec_winner}; "
                          f"signals disagree — call ambiguous at n={n}",
                "primary_winner": primary_winner,
                "secondary_winner": sec_winner}

    label_suffix = primary_winner.replace("arm-", "arm-")
    if n >= MIN_SAMPLE_FOR_CONFIDENT:
        return {**base,
                "verdict": f"confident-favor-{label_suffix}",
                "reason": f"primary + secondary agree on {primary_winner}, "
                          f"no hallucination regression, n={n} "
                          f">= {MIN_SAMPLE_FOR_CONFIDENT}",
                "primary_winner": primary_winner}
    return {**base,
            "verdict": f"directional-favor-{label_suffix}",
            "reason": f"primary + secondary agree on {primary_winner}, "
                      f"no hallucination regression, but n={n} "
                      f"< {MIN_SAMPLE_FOR_CONFIDENT} — directional only",
            "primary_winner": primary_winner}


# ── Fixtures for --dry-run ─────────────────────────────────────────────────


def _dry_run_scored_fixture() -> dict[str, Any]:
    """Minimal scored input that satisfies family-exclusion and shape checks.
    Used by the --dry-run CLI path; also consumed by tests that need a
    clean baseline."""
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


def _fmt_pct(x: float | None) -> str:
    return "—" if x is None else f"{x*100:.1f}%"


def render_markdown(verdict: dict[str, Any], scored_list: list[dict[str, Any]]) -> str:
    judges = set()
    run_ids = []
    for s in scored_list:
        meta = s.get("metadata", {})
        if isinstance(meta.get("judges"), list):
            judges.update(meta["judges"])
        if meta.get("run_id"):
            run_ids.append(meta["run_id"])

    lines = [
        "# Arm-comparison verdict",
        "",
        f"- **verdict**: `{verdict.get('verdict')}`",
        f"- **reason**: {verdict.get('reason', '')}",
        f"- **n proposals**: {verdict.get('n_proposals', 0)}",
        f"- **judges**: {', '.join(sorted(judges)) if judges else '—'}",
        f"- **run_ids**: {', '.join(run_ids) if run_ids else '—'}",
        "",
    ]

    acc = verdict.get("accuracy")
    if acc:
        lines.extend([
            "## Primary signal — verifier accuracy (catch_rate)",
            "",
            "| Arm | Claims | Verified | Falsified | Unresolvable | Accuracy | Hallucination |",
            "|---|---|---|---|---|---|---|",
        ])
        for arm in ("arm-a", "arm-b"):
            a = acc[arm]
            lines.append(
                f"| {arm} | {a['claims_checked']} | {a['verified']} | "
                f"{a['falsified']} | {a['unresolvable']} | "
                f"{_fmt_pct(a['accuracy'])} | {_fmt_pct(a['hallucination_rate'])} |"
            )
        lines.append("")

    sec = verdict.get("secondary")
    if sec:
        lines.extend([
            "## Secondary signal — substantive-count by dimension (mean across judges)",
            "",
            "| Dimension | Arm A | Arm B | Winner |",
            "|---|---|---|---|",
        ])
        for dim, totals in sec["per_dim_totals"].items():
            winner = sec["per_dim_winners"].get(dim, "—")
            lines.append(
                f"| {dim} | {totals['arm-a']:.1f} | {totals['arm-b']:.1f} | {winner} |"
            )
        lines.append(
            f"\n_Dim majority: Arm B wins {sec['b_dim_wins']}, "
            f"Arm A wins {sec['a_dim_wins']}. Majority winner: {sec['majority_winner']}._"
        )
        lines.append("")

    conv = verdict.get("convergence")
    if conv and conv.get("dims_total"):
        lines.extend([
            "## Advisory — judge count convergence (not a gate per D40)",
            "",
            f"- Dims converged (±{conv.get('dims_total', 0)} total): "
            f"{conv['dims_converged']}/{conv['dims_total']} "
            f"({_fmt_pct(conv['convergence_rate'])})",
            f"- Mean |count_delta|: {conv['mean_abs_count_delta']:.1f}"
            if conv.get("mean_abs_count_delta") is not None else "- Mean |count_delta|: —",
            f"- Max |count_delta|: {conv['max_abs_count_delta']}"
            if conv.get("max_abs_count_delta") is not None else "- Max |count_delta|: —",
            "",
            "_Wide convergence deltas indicate prompt looseness on item counts, "
            "not arm quality — primary signal above is independent._",
            "",
        ])

    thresholds = verdict.get("decision_thresholds") or {}
    if thresholds:
        lines.extend([
            "## Decision thresholds (pre-registered)",
            "",
            f"- Primary accuracy delta to call a winner: "
            f"{thresholds['primary_accuracy_delta_pp']*100:.0f}pp",
            f"- Hallucination guardrail: primary winner may not regress > "
            f"{thresholds['hallucination_guardrail_pp']*100:.0f}pp vs loser",
            f"- Min sample for directional verdict: "
            f"{thresholds['min_sample_for_directional']}",
            f"- Min sample for confident verdict: "
            f"{thresholds['min_sample_for_confident']}",
            "",
        ])

    return "\n".join(lines) + "\n"


# ── Main ───────────────────────────────────────────────────────────────────


def _load_scored(run_ids: list[str], store_root: Path) -> list[dict[str, Any]]:
    out = []
    for rid in run_ids:
        p = store_root / rid / "scored.json"
        if not p.is_file():
            raise FileNotFoundError(f"scored file not found: {p}")
        out.append(json.loads(p.read_text()))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--run-id", nargs="+", default=None,
                     help="One or more run-ids under <store_root>/")
    src.add_argument("--scored-file", type=Path, nargs="+", default=None,
                     help="One or more explicit paths to scored JSON files")
    ap.add_argument("--store-root", type=Path, default=DEFAULT_STORE)
    ap.add_argument("--dry-run", action="store_true",
                    help="Use fixture scored input; no file I/O")
    ap.add_argument("--output-markdown", type=Path, default=None)
    args = ap.parse_args()

    if args.dry_run:
        scored_list = [_dry_run_scored_fixture()]
    elif args.scored_file:
        scored_list = [json.loads(p.read_text()) for p in args.scored_file]
    elif args.run_id:
        try:
            scored_list = _load_scored(args.run_id, args.store_root)
        except FileNotFoundError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
    else:
        print("ERROR: pass --run-id, --scored-file, or --dry-run", file=sys.stderr)
        return 2

    for scored in scored_list:
        try:
            enforce_non_claude_from_scored(scored)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2

    verdict = compute_verdict(scored_list)

    if args.output_markdown:
        args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
        args.output_markdown.write_text(render_markdown(verdict, scored_list))

    out = {"verdict": verdict}
    json.dump(out, sys.stdout, indent=2, sort_keys=True, default=str)
    sys.stdout.write("\n")
    sys.stderr.write("\n" + render_markdown(verdict, scored_list))
    return 0


if __name__ == "__main__":
    sys.exit(main())

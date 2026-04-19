#!/usr/bin/env python3.11
"""
Arm-comparison study verdict (Phase 3, refined per user feedback to surface
all 7 dimensions and granularity-weight the per-dim signals).

Reads scorer output (from arm_study_scorer.py) across N proposals and emits
a verdict that includes a PER-DIMENSION primary verdict for each scorable
dimension, plus an overall verdict that combines them.

Design (supersedes the single-primary accuracy-only framing of the earlier
commit):

- catch_rate (Dim 4) is verifier-grounded. Primary signal per arm is
  quality-weighted accuracy: verifier accuracy × judge-rated quality
  density. Hallucination rate is a guardrail.
- direction_improvement (Dim 1), nuance_caught (Dim 2), net_new_ideas
  (Dim 3) are judge-graded. Primary signal per arm per dim is
  quality-weighted substantive score:
      substantive*3 + marginal*1 + superficial*0.5 + harmful*(-1)
  summed across proposals, mean across non-Claude judges. Convergence
  is advisory, not a gate (D40).
- miss_rate (Dim 5), plan_quality_delta (Dim 6), code_review_quality_delta
  (Dim 7) are not yet fully wired. Dim 5 requires an independent
  issue-discoverer (item 5 in the metric-fix plan); Dim 6/7 require a
  retrospective scorer reading downstream artifacts (item 6). Verdict
  reports "not-yet-measured" for each and the reason.

Overall verdict composes the per-dim verdicts. A scorable dim contributes
only if its own verdict is directional-favor-<arm> or
confident-favor-<arm>. Inconclusive, not-yet-measured, and
regression-blocked dims do not vote.

See tasks/decisions.md D40 for methodology framing, and D41 (this commit)
for the per-dim promotion + quality-weighting shift.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STORE = REPO_ROOT / "stores" / "arm-study"

# ── Thresholds (module-level for auditability + test access) ────────────────

PRIMARY_ACCURACY_DELTA_PP = 0.05
HALLUCINATION_GUARDRAIL_PP = 0.02
# Substantive-score threshold for per-dim winner. Absolute scale: weighted
# score uses substantive*3 + marginal*1 + superficial*0.5 + harmful*(-1).
# At n=3 with typical 3-10 items per dim per arm per proposal, totals land
# around 15-50. A delta of 5 corresponds to ~1 substantive item's worth of
# signal averaged across proposals — tight enough to reject noise, loose
# enough to call a real 2-3 substantive-item gap.
SUBSTANTIVE_DELTA_MIN = 5.0
# Quality-density regression guardrail. If arm X wins substantive score but
# has more harmful items (absolute count), block promotion.
HARMFUL_REGRESSION_ABSOLUTE_MAX = 2
MIN_SAMPLE_FOR_DIRECTIONAL = 3
MIN_SAMPLE_FOR_CONFIDENT = 5

# Quality weights. substantive is the load-bearing class; marginal is
# directionally useful; superficial is filler; harmful actively subtracts.
QUALITY_WEIGHTS = {
    "substantive": 3.0,
    "marginal": 1.0,
    "superficial": 0.5,
    "harmful": -1.0,
}

GROUND_TRUTH_DIM = "catch_rate"
JUDGE_GRADED_DIMS = (
    "direction_improvement",
    "nuance_caught",
    "net_new_ideas",
)
NOT_YET_MEASURED_DIMS = (
    "code_review_quality_delta",
)
MISS_RATE_DIM = "miss_rate"
PLAN_QUALITY_DELTA_DIM = "plan_quality_delta"
ALL_REPORTED_DIMS = (
    (GROUND_TRUTH_DIM,) + JUDGE_GRADED_DIMS
    + (MISS_RATE_DIM, PLAN_QUALITY_DELTA_DIM) + NOT_YET_MEASURED_DIMS
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


# ── Quality-weighted helpers ───────────────────────────────────────────────


def _arm_dim_data(scored: dict[str, Any], arm: str, dim: str) -> dict[str, Any]:
    return (scored.get("arms", {}).get(arm) or {}).get(dim) or {}


def _weighted_dim_score(dim_data: dict[str, Any]) -> float | None:
    """Mean weighted score across judges for one dim. Uses per-judge
    quality_distribution. None if the dim is not_scorable."""
    qd = dim_data.get("quality_distribution")
    if not isinstance(qd, dict) or not qd:
        return None
    per_judge_scores = []
    for _, counts in qd.items():
        if not isinstance(counts, dict):
            continue
        score = sum(
            int(counts.get(cat, 0)) * QUALITY_WEIGHTS[cat]
            for cat in QUALITY_WEIGHTS
        )
        per_judge_scores.append(score)
    if not per_judge_scores:
        return None
    return sum(per_judge_scores) / len(per_judge_scores)


def _dim_harmful_total(dim_data: dict[str, Any]) -> int:
    """Sum of harmful items across judges (max-upper-bound, not mean, to keep
    the guardrail conservative — if any judge saw harmful items, count them)."""
    qd = dim_data.get("quality_distribution")
    if not isinstance(qd, dict) or not qd:
        return 0
    return max(
        (int(counts.get("harmful", 0)) for counts in qd.values()
         if isinstance(counts, dict)),
        default=0,
    )


def _arm_dim_quality_distribution(dim_data: dict[str, Any]) -> dict[str, float]:
    """Mean per-category counts across judges for one dim."""
    qd = dim_data.get("quality_distribution")
    if not isinstance(qd, dict) or not qd:
        return {cat: 0.0 for cat in QUALITY_WEIGHTS}
    out: dict[str, float] = {cat: 0.0 for cat in QUALITY_WEIGHTS}
    n = 0
    for _, counts in qd.items():
        if not isinstance(counts, dict):
            continue
        for cat in QUALITY_WEIGHTS:
            out[cat] += int(counts.get(cat, 0))
        n += 1
    if n > 0:
        out = {cat: v / n for cat, v in out.items()}
    return out


def _sum_dim_distribution(
    all_scored: list[dict[str, Any]], arm: str, dim: str,
) -> dict[str, float]:
    """Sum mean-across-judges quality distribution across proposals for one
    (arm, dim) pair."""
    out = {cat: 0.0 for cat in QUALITY_WEIGHTS}
    for scored in all_scored:
        dim_data = _arm_dim_data(scored, arm, dim)
        dist = _arm_dim_quality_distribution(dim_data)
        for cat in QUALITY_WEIGHTS:
            out[cat] += dist.get(cat, 0.0)
    return out


def _quality_density(dist: dict[str, float]) -> float | None:
    """(substantive + marginal) / total items. None if total is 0."""
    total = sum(dist.values())
    if total <= 0:
        return None
    return (dist.get("substantive", 0.0) + dist.get("marginal", 0.0)) / total


# ── Verifier-grounded dim verdict (catch_rate) ──────────────────────────────


def _arm_verifier_stats(scored: dict[str, Any], arm: str) -> dict[str, int] | None:
    """Return verifier stats for one arm's catch_rate, or None if unavailable.

    REDESIGN A (2026-04-19): when `falsified_classification.classifier_source
    == "llm"`, the explicit per-claim labels resolve the classifier ambiguity
    that the regex collapses; classified_accuracy/hallucination_rate use
    `CHALLENGER_FABRICATION` as the hallucination denominator (orphan #10/#11
    fixes — same denominator across both metrics).

    When classifier_source is "regex-fallback" or absent, legacy formulas
    apply via the regex-counted hallucination/caught_misquote/unclear fields.
    """
    vc = (_arm_dim_data(scored, arm, GROUND_TRUTH_DIM) or {}).get("verify_claims") or {}
    if vc.get("status") != "verified":
        return None
    stats = vc.get("stats") or {}
    required = ("verified", "falsified", "unresolvable", "claims_checked")
    if not all(k in stats for k in required):
        return None
    out = {k: int(stats[k]) for k in required}
    clf = vc.get("falsified_classification") or {}
    if clf:
        source = clf.get("classifier_source", "regex")
        out["classifier_source"] = source
        out["regex_fallback_used"] = bool(clf.get("regex_fallback_used", False))
        if "fallback_reason" in clf:
            out["fallback_reason"] = clf.get("fallback_reason")
        # Surface the labels block when LLM mode (used by markdown render).
        if "labels" in clf and isinstance(clf["labels"], dict):
            out["mechanism_labels"] = {
                k: int(v) for k, v in clf["labels"].items()
            }
        # Legacy fields (always populated by classify_mechanisms_llm)
        # — used by regex-fallback path AND as cross-checks.
        parsed_total = int(clf.get("total_falsified", 0))
        for k in ("hallucination", "caught_misquote", "unclear"):
            out[k] = int(clf.get(k, 0))
        out["classification_parsed_total"] = parsed_total
        out["classification_stats_total"] = int(stats["falsified"])
        # When LLM mode, hallucination = CHALLENGER_FABRICATION exactly
        # (set by classify_mechanisms_llm; preserved here for clarity).
        if source == "llm" and "mechanism_labels" in out:
            out["hallucination"] = out["mechanism_labels"].get(
                "CHALLENGER_FABRICATION", out["hallucination"]
            )
            out["caught_misquote"] = out["mechanism_labels"].get(
                "PROPOSAL_ERROR_CAUGHT", out["caught_misquote"]
            )
    return out


def _aggregate_verifier(all_scored: list[dict[str, Any]]) -> dict[str, Any]:
    """Pool verifier stats across proposals, per arm, plus weighted accuracy
    using the judge-rated quality density on catch_rate items.

    When falsified_classification is present in the source data (item 2 of
    metric-fix plan), computes TWO accuracy/hallucination pairs:
      - raw: verified / (verified + falsified), falsified / claims_checked
      - classified: verified / (verified + hallucination),
                    hallucination / claims_checked (caught_misquote excluded
                    from both denominators because it is not a claim the
                    challenger made; they quoted the proposal's false claim)
    The classified version is the one the per-dim verdict uses when both
    arms have classifications with parsed totals that match (or
    approximately match) the authoritative stats.falsified.
    """
    pooled = {
        arm: {"verified": 0, "falsified": 0, "unresolvable": 0,
              "claims_checked": 0, "missing": 0,
              "hallucination": 0, "caught_misquote": 0, "unclear": 0,
              "classified_parsed_total": 0, "classified_stats_total": 0,
              # REDESIGN A: per-source counts so the markdown can show how
              # many proposals were classified by LLM vs regex-fallback.
              "n_llm_classified": 0, "n_regex_fallback": 0,
              "mechanism_labels": {
                  "PROPOSAL_ERROR_CAUGHT": 0,
                  "CHALLENGER_FABRICATION": 0,
                  "AMBIGUOUS": 0,
                  "INFERENCE_NOT_GROUNDED": 0,
              }}
        for arm in ("arm-a", "arm-b")
    }
    has_classification = {"arm-a": False, "arm-b": False}
    for scored in all_scored:
        for arm in ("arm-a", "arm-b"):
            stats = _arm_verifier_stats(scored, arm)
            if stats is None:
                pooled[arm]["missing"] += 1
                continue
            for k in ("verified", "falsified", "unresolvable", "claims_checked"):
                pooled[arm][k] += stats[k]
            if "hallucination" in stats:
                has_classification[arm] = True
                for k in ("hallucination", "caught_misquote", "unclear"):
                    pooled[arm][k] += stats.get(k, 0)
                pooled[arm]["classified_parsed_total"] += stats.get(
                    "classification_parsed_total", 0)
                pooled[arm]["classified_stats_total"] += stats.get(
                    "classification_stats_total", 0)
                # REDESIGN A: surface classifier provenance.
                source = stats.get("classifier_source", "regex")
                if source == "llm":
                    pooled[arm]["n_llm_classified"] += 1
                else:
                    pooled[arm]["n_regex_fallback"] += 1
                mech = stats.get("mechanism_labels") or {}
                for label, count in mech.items():
                    if label in pooled[arm]["mechanism_labels"]:
                        pooled[arm]["mechanism_labels"][label] += int(count)

    out: dict[str, Any] = {}
    use_classified = has_classification["arm-a"] and has_classification["arm-b"]
    for arm in ("arm-a", "arm-b"):
        p = pooled[arm]
        denom_acc_raw = p["verified"] + p["falsified"]
        denom_hall = p["claims_checked"]
        accuracy_raw = (p["verified"] / denom_acc_raw) if denom_acc_raw > 0 else None
        hallucination_raw = (p["falsified"] / denom_hall) if denom_hall > 0 else None

        # Quality density on catch_rate items (judge-rated).
        catch_rate_dist = _sum_dim_distribution(all_scored, arm, GROUND_TRUTH_DIM)
        density = _quality_density(catch_rate_dist)

        # Classified versions (source-aware) if available.
        accuracy_cls = None
        hallucination_cls = None
        caught_misquote_rate = None
        if use_classified:
            denom_acc_cls = p["verified"] + p["hallucination"]
            accuracy_cls = (p["verified"] / denom_acc_cls) if denom_acc_cls > 0 else None
            hallucination_cls = (
                p["hallucination"] / denom_hall if denom_hall > 0 else None
            )
            caught_misquote_rate = (
                p["caught_misquote"] / denom_hall if denom_hall > 0 else None
            )

        # The primary accuracy the verdict will use: classified when both arms
        # have it, else raw.
        primary_accuracy = accuracy_cls if use_classified else accuracy_raw
        primary_hallucination = hallucination_cls if use_classified else hallucination_raw
        weighted_accuracy = (
            primary_accuracy * density
            if primary_accuracy is not None and density is not None
            else None
        )

        out[arm] = {
            **p,
            "accuracy": primary_accuracy,
            "accuracy_raw": accuracy_raw,
            "accuracy_classified": accuracy_cls,
            "hallucination_rate": primary_hallucination,
            "hallucination_rate_raw": hallucination_raw,
            "hallucination_rate_classified": hallucination_cls,
            "caught_misquote_rate": caught_misquote_rate,
            "unresolvable_rate": (
                p["unresolvable"] / denom_hall if denom_hall > 0 else None
            ),
            "quality_density": density,
            "weighted_accuracy": weighted_accuracy,
            "quality_distribution_sum": catch_rate_dist,
            "signal_source": "classified" if use_classified else "raw",
        }
    return out


def _per_dim_verdict_verifier(
    all_scored: list[dict[str, Any]],
    verifier_agg: dict[str, Any],
    n: int,
) -> dict[str, Any]:
    """Compute the catch_rate verdict using verifier accuracy + hallucination
    guard + quality-weighted accuracy alignment."""
    a = verifier_agg["arm-a"]
    b = verifier_agg["arm-b"]
    surfaced = (
        "verified", "falsified", "unresolvable", "claims_checked",
        "accuracy", "accuracy_raw", "accuracy_classified",
        "hallucination_rate", "hallucination_rate_raw",
        "hallucination_rate_classified", "caught_misquote_rate",
        "hallucination", "caught_misquote", "unclear",
        "quality_density", "weighted_accuracy",
        "quality_distribution_sum", "signal_source",
    )
    out: dict[str, Any] = {
        "dimension": GROUND_TRUTH_DIM,
        "signal_type": "verifier-grounded + source-classified + quality-weighted",
        "arm-a": {k: a.get(k) for k in surfaced},
        "arm-b": {k: b.get(k) for k in surfaced},
    }

    # Fix 3 (must-fix per cross-model review): primary is weighted_accuracy,
    # not raw/classified accuracy. D40 intended weighted as primary; earlier
    # impl left it as a tie-break. If weighted is unavailable (density is
    # None — no judge catch_rate items), fall back to classified/raw so the
    # dim still produces a signal, but note the fallback.
    wa_a = a.get("weighted_accuracy")
    wa_b = b.get("weighted_accuracy")
    if wa_a is not None and wa_b is not None:
        delta = wa_b - wa_a
        primary_basis = "weighted_accuracy"
    elif a.get("accuracy") is not None and b.get("accuracy") is not None:
        delta = b["accuracy"] - a["accuracy"]
        primary_basis = "accuracy (weighted unavailable)"
    else:
        out["verdict"] = "not-yet-measured"
        out["reason"] = "verifier accuracy missing on one or both arms"
        return out
    out["delta_pp"] = delta
    out["primary_basis"] = primary_basis

    if abs(delta) < PRIMARY_ACCURACY_DELTA_PP:
        out["verdict"] = "inconclusive"
        out["reason"] = (
            f"{primary_basis} delta {delta*100:+.1f}pp within "
            f"±{PRIMARY_ACCURACY_DELTA_PP*100:.0f}pp noise floor"
        )
        return out

    winner = "arm-b" if delta > 0 else "arm-a"
    loser = "arm-a" if winner == "arm-b" else "arm-b"
    hall_winner = verifier_agg[winner]["hallucination_rate"]
    hall_loser = verifier_agg[loser]["hallucination_rate"]
    if hall_winner is not None and hall_loser is not None:
        if hall_winner - hall_loser > HALLUCINATION_GUARDRAIL_PP:
            out["verdict"] = "regression-blocked"
            out["reason"] = (
                f"primary winner ({winner}) hallucinates "
                f"{(hall_winner - hall_loser)*100:+.1f}pp more than {loser}; "
                f"guardrail blocks promotion"
            )
            out["primary_winner"] = winner
            return out

    label = f"directional-favor-{winner}" if n < MIN_SAMPLE_FOR_CONFIDENT \
        else f"confident-favor-{winner}"
    out["verdict"] = label
    out["reason"] = (
        f"{primary_basis} delta {delta*100:+.1f}pp, "
        f"hallucination guardrail passes, n={n}"
    )
    out["primary_winner"] = winner
    return out


# ── Judge-graded dim verdict ────────────────────────────────────────────────


def _aggregate_judge_dim(
    all_scored: list[dict[str, Any]], dim: str,
) -> dict[str, Any]:
    """Aggregate a judge-graded dim across proposals + judges.

    Fix 1A (must-fix per cross-model review): paired aggregation. A proposal
    is pooled only when BOTH arms have a scorable weighted_dim_score for
    this dim. Dropping one arm because it failed extraction while counting
    the other was silently biasing verdicts.
    """
    per_arm_state: dict[str, dict[str, Any]] = {
        arm: {"weighted_scores": [], "harmful_totals": [],
              "distribution": {cat: 0.0 for cat in QUALITY_WEIGHTS},
              "n_scored": 0}
        for arm in ("arm-a", "arm-b")
    }
    unpaired_dropped = 0
    for scored in all_scored:
        a_data = _arm_dim_data(scored, "arm-a", dim)
        b_data = _arm_dim_data(scored, "arm-b", dim)
        a_ws = _weighted_dim_score(a_data)
        b_ws = _weighted_dim_score(b_data)
        if a_ws is None or b_ws is None:
            unpaired_dropped += 1
            continue
        for arm, data, ws in (("arm-a", a_data, a_ws),
                              ("arm-b", b_data, b_ws)):
            state = per_arm_state[arm]
            state["weighted_scores"].append(ws)
            state["harmful_totals"].append(_dim_harmful_total(data))
            dist = _arm_dim_quality_distribution(data)
            for cat in QUALITY_WEIGHTS:
                state["distribution"][cat] += dist.get(cat, 0.0)
            state["n_scored"] += 1

    per_arm: dict[str, dict[str, Any]] = {}
    for arm in ("arm-a", "arm-b"):
        s = per_arm_state[arm]
        density = _quality_density(s["distribution"])
        per_arm[arm] = {
            "weighted_score_total": sum(s["weighted_scores"]),
            "weighted_score_mean": (
                sum(s["weighted_scores"]) / len(s["weighted_scores"])
                if s["weighted_scores"] else None
            ),
            "harmful_total": sum(s["harmful_totals"]),
            "quality_distribution_sum": s["distribution"],
            "quality_density": density,
            "n_scored": s["n_scored"],
        }
    per_arm["_unpaired_dropped"] = unpaired_dropped
    return per_arm


def _per_dim_verdict_judge_graded(
    all_scored: list[dict[str, Any]],
    dim: str,
    n: int,
) -> dict[str, Any]:
    agg = _aggregate_judge_dim(all_scored, dim)
    out: dict[str, Any] = {
        "dimension": dim,
        "signal_type": "judge-graded quality-weighted substantive score",
        "arm-a": agg["arm-a"],
        "arm-b": agg["arm-b"],
        "unpaired_dropped": agg.get("_unpaired_dropped", 0),
    }
    a = agg["arm-a"]
    b = agg["arm-b"]
    if a["n_scored"] == 0 or b["n_scored"] == 0:
        out["verdict"] = "not-yet-measured"
        out["reason"] = "no scorable data for this dimension"
        return out

    delta = b["weighted_score_total"] - a["weighted_score_total"]
    out["delta"] = delta

    if abs(delta) < SUBSTANTIVE_DELTA_MIN:
        out["verdict"] = "inconclusive"
        out["reason"] = (
            f"weighted-score delta {delta:+.1f} within "
            f"±{SUBSTANTIVE_DELTA_MIN} noise floor"
        )
        return out

    winner = "arm-b" if delta > 0 else "arm-a"
    winner_agg = agg[winner]
    loser_agg = agg["arm-a" if winner == "arm-b" else "arm-b"]

    # Fix 2 (must-fix per cross-model review): harmful-regression semantics.
    # The rule is "winner may not regress > HARMFUL_REGRESSION_ABSOLUTE_MAX
    # harmful items", i.e. the DELTA between winner and loser exceeds the
    # cap. Earlier impl blocked only when winner's absolute count was ≥ 2.
    harm_delta = winner_agg["harmful_total"] - loser_agg["harmful_total"]
    if harm_delta > HARMFUL_REGRESSION_ABSOLUTE_MAX:
        out["verdict"] = "regression-blocked"
        out["reason"] = (
            f"primary winner ({winner}) has {winner_agg['harmful_total']} "
            f"harmful items vs loser's {loser_agg['harmful_total']} "
            f"(delta {harm_delta:+d} > cap {HARMFUL_REGRESSION_ABSOLUTE_MAX}); "
            f"guardrail blocks promotion"
        )
        out["primary_winner"] = winner
        return out

    label = f"directional-favor-{winner}" if n < MIN_SAMPLE_FOR_CONFIDENT \
        else f"confident-favor-{winner}"
    out["verdict"] = label
    out["reason"] = (
        f"weighted-score delta {delta:+.1f} clears ±{SUBSTANTIVE_DELTA_MIN}, "
        f"no harmful regression, n={n}"
    )
    out["primary_winner"] = winner
    return out


# ── Not-yet-measured dim stubs ──────────────────────────────────────────────


_NOT_YET_MEASURED_REASON = {
    "code_review_quality_delta": (
        "Dim 7 requires retrospective scorer reading downstream code artifact "
        "(deferred — would need code-diff analysis linking to proposal commits; "
        "non-trivial to automate)"
    ),
}

PLAN_QUALITY_DELTA_MIN = 0.15  # landing-rate delta ≥15pp to call a winner

MISS_RATE_DELTA_MIN = 0.15  # miss_rate delta must be ≥15pp for a winner


def _per_dim_verdict_not_yet_measured(dim: str) -> dict[str, Any]:
    return {
        "dimension": dim,
        "signal_type": "not-yet-wired",
        "verdict": "not-yet-measured",
        "reason": _NOT_YET_MEASURED_REASON.get(dim, "dimension not yet implemented"),
    }


def _load_retrospective_for_scored(
    scored: dict[str, Any], store_root: Path,
) -> dict[str, Any] | None:
    """Look for retrospective.json in the scored run's directory."""
    meta = scored.get("metadata") or {}
    rid = meta.get("run_id")
    if not rid:
        return None
    retro_path = store_root / rid / "retrospective.json"
    if not retro_path.is_file():
        return None
    try:
        return json.loads(retro_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _per_dim_verdict_plan_quality(
    all_scored: list[dict[str, Any]],
    store_root: Path,
    n: int,
) -> dict[str, Any]:
    """plan_quality_delta verdict from retrospective.json per run.

    Pools landed/partial/not_landed counts across proposals per arm.
    Landing rate = (landed + 0.5*partial) / total (same as retrospective.py).
    Higher landing rate wins.
    """
    pooled = {arm: {"landed": 0, "partial": 0, "not_landed": 0, "total": 0}
              for arm in ("arm-a", "arm-b")}
    any_scored = False
    no_artifact_count = 0
    unpaired_dropped = 0
    # Fix 1C (must-fix per cross-model review): pair proposals before pooling.
    for scored in all_scored:
        retro = _load_retrospective_for_scored(scored, store_root)
        if retro is None:
            continue
        if retro.get("status") == "no-downstream-artifact":
            no_artifact_count += 1
            continue
        if retro.get("status") != "scored":
            continue
        per_arm_retro = retro.get("per_arm") or {}
        a_retro = per_arm_retro.get("arm-a") or {}
        b_retro = per_arm_retro.get("arm-b") or {}
        if (a_retro.get("status") != "scored"
                or b_retro.get("status") != "scored"):
            if (a_retro.get("status") == "scored"
                    or b_retro.get("status") == "scored"):
                unpaired_dropped += 1
            continue
        any_scored = True
        for arm, arm_retro in (("arm-a", a_retro), ("arm-b", b_retro)):
            summary = arm_retro.get("summary") or {}
            for k in ("landed", "partial", "not_landed", "total"):
                pooled[arm][k] += int(summary.get(k, 0))

    out: dict[str, Any] = {
        "dimension": "plan_quality_delta",
        "signal_type": "retrospective-landing (plan > refined > judgment)",
        "arm-a": pooled["arm-a"],
        "arm-b": pooled["arm-b"],
        "unpaired_dropped": unpaired_dropped,
        "no_artifact_count": no_artifact_count,
    }
    if not any_scored:
        out["verdict"] = "not-yet-measured"
        if no_artifact_count > 0:
            out["reason"] = (
                f"{no_artifact_count} of {n} proposals have no downstream "
                f"artifact adjacent to the proposal; no retrospective data"
            )
        else:
            out["reason"] = (
                "retrospective.json absent for all proposals — run "
                "arm_study_retrospective.py per run-id to generate"
            )
        return out

    for arm in ("arm-a", "arm-b"):
        total = pooled[arm]["total"]
        pooled[arm]["landing_rate"] = (
            (pooled[arm]["landed"] + 0.5 * pooled[arm]["partial"]) / total
            if total > 0 else None
        )
    out["arm-a"] = pooled["arm-a"]
    out["arm-b"] = pooled["arm-b"]

    lr_a = pooled["arm-a"]["landing_rate"]
    lr_b = pooled["arm-b"]["landing_rate"]
    if lr_a is None or lr_b is None:
        out["verdict"] = "not-yet-measured"
        out["reason"] = "insufficient landing data on one or both arms"
        return out

    delta = lr_b - lr_a  # positive = B lands more items
    out["delta"] = delta
    out["retrospective_proposals_with_artifact"] = n - no_artifact_count

    if abs(delta) < PLAN_QUALITY_DELTA_MIN:
        out["verdict"] = "inconclusive"
        out["reason"] = (
            f"landing-rate delta {delta*100:+.1f}pp within "
            f"±{PLAN_QUALITY_DELTA_MIN*100:.0f}pp noise floor"
        )
        return out

    winner = "arm-b" if delta > 0 else "arm-a"
    # Confidence requires n≥5 AND all scored proposals agreed.
    retro_n = n - no_artifact_count
    if retro_n < MIN_SAMPLE_FOR_DIRECTIONAL:
        out["verdict"] = "insufficient-retrospective-sample"
        out["reason"] = (
            f"only {retro_n} of {n} proposals had a downstream artifact — "
            f"below MIN_SAMPLE_FOR_DIRECTIONAL={MIN_SAMPLE_FOR_DIRECTIONAL} "
            f"for this dim"
        )
        return out
    label = (
        f"directional-favor-{winner}"
        if retro_n < MIN_SAMPLE_FOR_CONFIDENT
        else f"confident-favor-{winner}"
    )
    out["verdict"] = label
    out["reason"] = (
        f"landing-rate delta {delta*100:+.1f}pp favors {winner} "
        f"(retro_n={retro_n})"
    )
    out["primary_winner"] = winner
    return out


def _per_dim_verdict_miss_rate(
    all_scored: list[dict[str, Any]], n: int,
) -> dict[str, Any]:
    """miss_rate verdict based on reference-issue coverage (item 5 output).

    Pools reference issues across proposals per arm; miss_rate(arm) =
    total_missed / total_reference_issues. Lower is better.
    """
    pooled = {arm: {"caught": 0, "missed": 0, "total": 0}
              for arm in ("arm-a", "arm-b")}
    any_scored = False
    unpaired_dropped = 0
    # Fix 1B (must-fix per cross-model review): pair proposals before pooling.
    for scored in all_scored:
        a_rc = (
            (_arm_dim_data(scored, "arm-a", "miss_rate") or {})
            .get("reference_coverage") or {}
        )
        b_rc = (
            (_arm_dim_data(scored, "arm-b", "miss_rate") or {})
            .get("reference_coverage") or {}
        )
        if a_rc.get("status") != "scored" or b_rc.get("status") != "scored":
            if a_rc.get("status") == "scored" or b_rc.get("status") == "scored":
                unpaired_dropped += 1
            continue
        any_scored = True
        for arm, rc in (("arm-a", a_rc), ("arm-b", b_rc)):
            pooled[arm]["caught"] += int(rc.get("caught_count", 0))
            pooled[arm]["missed"] += int(rc.get("missed_count", 0))
            pooled[arm]["total"] += int(rc.get("total_reference_issues", 0))

    out: dict[str, Any] = {
        "dimension": "miss_rate",
        "signal_type": "independent-discoverer + token-coverage matcher",
        "arm-a": pooled["arm-a"],
        "arm-b": pooled["arm-b"],
        "unpaired_dropped": unpaired_dropped,
    }
    if not any_scored:
        out["verdict"] = "not-yet-measured"
        out["reason"] = (
            "miss_rate reference_coverage absent on all proposals — run "
            "arm_study_miss_discoverer.py per proposal to generate"
        )
        return out

    for arm in ("arm-a", "arm-b"):
        total = pooled[arm]["total"]
        pooled[arm]["miss_rate"] = (
            pooled[arm]["missed"] / total if total > 0 else None
        )
        pooled[arm]["catch_rate"] = (
            pooled[arm]["caught"] / total if total > 0 else None
        )
    out["arm-a"] = pooled["arm-a"]
    out["arm-b"] = pooled["arm-b"]

    mr_a = pooled["arm-a"]["miss_rate"]
    mr_b = pooled["arm-b"]["miss_rate"]
    if mr_a is None or mr_b is None:
        out["verdict"] = "not-yet-measured"
        out["reason"] = "insufficient coverage data on one or both arms"
        return out

    # Lower miss_rate wins. Compute delta as (loser - winner).
    delta = mr_a - mr_b  # positive = B misses less
    out["delta"] = delta

    if abs(delta) < MISS_RATE_DELTA_MIN:
        out["verdict"] = "inconclusive"
        out["reason"] = (
            f"miss_rate delta {delta*100:+.1f}pp within "
            f"±{MISS_RATE_DELTA_MIN*100:.0f}pp noise floor"
        )
        return out

    winner = "arm-b" if delta > 0 else "arm-a"
    label = (
        f"directional-favor-{winner}"
        if n < MIN_SAMPLE_FOR_CONFIDENT
        else f"confident-favor-{winner}"
    )
    out["verdict"] = label
    out["reason"] = (
        f"miss_rate delta {delta*100:+.1f}pp favors {winner} "
        f"({pooled[winner]['missed']}/{pooled[winner]['total']} missed vs "
        f"{pooled['arm-a' if winner == 'arm-b' else 'arm-b']['missed']}/"
        f"{pooled['arm-a' if winner == 'arm-b' else 'arm-b']['total']}); "
        f"n={n}"
    )
    out["primary_winner"] = winner
    return out


# ── Advisory convergence note ───────────────────────────────────────────────


def _convergence_note(all_scored: list[dict[str, Any]]) -> dict[str, Any]:
    """D40 demoted convergence to advisory. Summarize it so the markdown can
    surface the noise level without gating on it."""
    count_converged = 0
    count_total = 0
    deltas = []
    for scored in all_scored:
        for arm in ("arm-a", "arm-b"):
            for dim in (GROUND_TRUTH_DIM,) + JUDGE_GRADED_DIMS:
                conv = (_arm_dim_data(scored, arm, dim) or {}).get("convergence") or {}
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


# ── Overall verdict composition ─────────────────────────────────────────────


def _compose_overall_verdict(
    per_dim: dict[str, dict[str, Any]],
    n: int,
) -> dict[str, Any]:
    """Compose overall verdict from per-dim verdicts. A dim votes only if its
    verdict is directional-favor-<arm> or confident-favor-<arm>. Everything
    else abstains (inconclusive, regression-blocked, not-yet-measured,
    mixed-on-quality)."""
    a_votes = 0
    b_votes = 0
    abstaining = []
    for dim, v in per_dim.items():
        verdict = v.get("verdict", "")
        if verdict.endswith("arm-a"):
            a_votes += 1
        elif verdict.endswith("arm-b"):
            b_votes += 1
        else:
            abstaining.append((dim, verdict))

    if n < MIN_SAMPLE_FOR_DIRECTIONAL:
        return {
            "verdict": "insufficient-sample",
            "reason": f"n={n} < {MIN_SAMPLE_FOR_DIRECTIONAL}",
            "a_votes": a_votes, "b_votes": b_votes,
            "abstaining_dims": abstaining,
        }
    if a_votes == 0 and b_votes == 0:
        return {
            "verdict": "inconclusive",
            "reason": "no dimension produced a directional-or-stronger signal",
            "a_votes": 0, "b_votes": 0,
            "abstaining_dims": abstaining,
        }
    if a_votes > 0 and b_votes > 0:
        return {
            "verdict": "mixed-directional",
            "reason": (
                f"{b_votes} dim(s) favor arm-b, {a_votes} dim(s) favor arm-a; "
                f"signals split"
            ),
            "a_votes": a_votes, "b_votes": b_votes,
            "abstaining_dims": abstaining,
        }
    winner = "arm-b" if b_votes > a_votes else "arm-a"
    votes = max(a_votes, b_votes)
    strength = "confident" if n >= MIN_SAMPLE_FOR_CONFIDENT else "directional"
    return {
        "verdict": f"{strength}-favor-{winner}",
        "reason": (
            f"{votes} dim(s) favor {winner}, 0 oppose; "
            f"{len(abstaining)} abstain (inconclusive / not-yet-measured / "
            f"regression-blocked)"
        ),
        "a_votes": a_votes, "b_votes": b_votes,
        "abstaining_dims": abstaining,
    }


# ── Entry point ────────────────────────────────────────────────────────────


def compute_verdict(
    all_scored: list[dict[str, Any]],
    store_root: Path = DEFAULT_STORE,
) -> dict[str, Any]:
    """Aggregate across N proposals and return a verdict dict with per-dim
    primary signals + overall composition.

    store_root: where retrospective.json files live for Dim 6 (item 6 of
    metric-fix plan). Defaults to DEFAULT_STORE so tests that don't
    exercise retrospective data work unchanged.
    """
    n = len(all_scored)
    thresholds = {
        "primary_accuracy_delta_pp": PRIMARY_ACCURACY_DELTA_PP,
        "hallucination_guardrail_pp": HALLUCINATION_GUARDRAIL_PP,
        "substantive_delta_min": SUBSTANTIVE_DELTA_MIN,
        "harmful_regression_absolute_max": HARMFUL_REGRESSION_ABSOLUTE_MAX,
        "min_sample_for_directional": MIN_SAMPLE_FOR_DIRECTIONAL,
        "min_sample_for_confident": MIN_SAMPLE_FOR_CONFIDENT,
        "quality_weights": QUALITY_WEIGHTS,
    }

    if n == 0:
        return {
            "verdict": "insufficient-sample",
            "reason": "no scored inputs",
            "n_proposals": 0,
            "per_dimension_verdicts": {},
            "decision_thresholds": thresholds,
        }

    verifier_agg = _aggregate_verifier(all_scored)
    per_dim: dict[str, dict[str, Any]] = {
        GROUND_TRUTH_DIM: _per_dim_verdict_verifier(all_scored, verifier_agg, n),
    }
    for dim in JUDGE_GRADED_DIMS:
        per_dim[dim] = _per_dim_verdict_judge_graded(all_scored, dim, n)
    # miss_rate (Dim 5) — now computed when item 5 discoverer + scorer
    # coverage pass has run (reference-coverage data populated).
    per_dim["miss_rate"] = _per_dim_verdict_miss_rate(all_scored, n)
    # plan_quality_delta (Dim 6) — now computed when item 6 retrospective
    # scorer has run (retrospective.json present for at least some
    # proposals). Requires store_root to locate the sibling file.
    per_dim["plan_quality_delta"] = _per_dim_verdict_plan_quality(
        all_scored, store_root, n,
    )
    for dim in NOT_YET_MEASURED_DIMS:
        per_dim[dim] = _per_dim_verdict_not_yet_measured(dim)

    overall = _compose_overall_verdict(per_dim, n)

    return {
        "verdict": overall["verdict"],
        "reason": overall["reason"],
        "n_proposals": n,
        "per_dimension_verdicts": per_dim,
        "overall": {
            "a_votes": overall["a_votes"],
            "b_votes": overall["b_votes"],
            "abstaining_dims": overall["abstaining_dims"],
            "verifier_aggregate": verifier_agg,
            "convergence_advisory": _convergence_note(all_scored),
        },
        "decision_thresholds": thresholds,
    }


# ── Fixture for --dry-run ──────────────────────────────────────────────────


def _dry_run_scored_fixture() -> dict[str, Any]:
    return {
        "metadata": {
            "dry_run": True,
            "judges": ["gpt-5.4", "gemini-3.1-pro"],
            "run_id": "dry-run-fixture",
        },
        "arms": {"arm-a": {}, "arm-b": {}},
        "aggregate_inconclusive": False,
        "unblinded": True,
    }


# ── Output ─────────────────────────────────────────────────────────────────


def _fmt_pct(x: float | None) -> str:
    return "—" if x is None else f"{x*100:.1f}%"


def _fmt_num(x: float | int | None, dec: int = 1) -> str:
    if x is None:
        return "—"
    return f"{x:.{dec}f}"


def render_markdown(
    verdict: dict[str, Any], scored_list: list[dict[str, Any]]
) -> str:
    judges: set[str] = set()
    run_ids: list[str] = []
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

    per_dim = verdict.get("per_dimension_verdicts", {}) or {}

    # ── Per-dim table (all 7 dims) ─────────────────────────────────────
    lines.extend([
        "## Per-dimension verdicts (all 7 dimensions)",
        "",
        "| Dim | Type | Verdict | Reason |",
        "|---|---|---|---|",
    ])
    for dim in ALL_REPORTED_DIMS:
        v = per_dim.get(dim, {})
        lines.append(
            f"| {dim} | {v.get('signal_type', '—')} | "
            f"`{v.get('verdict', '—')}` | "
            f"{(v.get('reason') or '')[:120]} |"
        )
    lines.append("")

    # ── catch_rate detail ─────────────────────────────────────────────
    cr = per_dim.get(GROUND_TRUTH_DIM)
    if cr and "arm-a" in cr and "arm-b" in cr:
        signal_source = cr["arm-a"].get("signal_source", "raw")
        label = (
            "source-classified (hallucination vs caught-misquote)"
            if signal_source == "classified" else "raw (all falsified pooled)"
        )
        lines.extend([
            f"## catch_rate — verifier accuracy + quality density ({label})",
            "",
            "| Arm | Claims | Verified | Falsified | Unresolvable | Accuracy | Hallucination | Quality density | Weighted accuracy |",
            "|---|---|---|---|---|---|---|---|---|",
        ])
        for arm in ("arm-a", "arm-b"):
            a = cr[arm]
            lines.append(
                f"| {arm} | {a['claims_checked']} | {a['verified']} | "
                f"{a['falsified']} | {a['unresolvable']} | "
                f"{_fmt_pct(a['accuracy'])} | {_fmt_pct(a['hallucination_rate'])} | "
                f"{_fmt_pct(a['quality_density'])} | "
                f"{_fmt_pct(a['weighted_accuracy'])} |"
            )
        lines.append("")

        if signal_source == "classified":
            lines.extend([
                "### FALSIFIED breakdown (item 2 of metric-fix plan)",
                "",
                "| Arm | Hallucination | Caught-misquote | Unclear | Raw accuracy | Classified accuracy |",
                "|---|---|---|---|---|---|",
            ])
            for arm in ("arm-a", "arm-b"):
                a = cr[arm]
                lines.append(
                    f"| {arm} | {a.get('hallucination', 0)} | "
                    f"{a.get('caught_misquote', 0)} | "
                    f"{a.get('unclear', 0)} | "
                    f"{_fmt_pct(a.get('accuracy_raw'))} | "
                    f"{_fmt_pct(a.get('accuracy_classified'))} |"
                )
            lines.extend([
                "",
                "_Hallucination = challenger asserted X, X is false. "
                "Caught-misquote = challenger quoted proposal's false claim; "
                "credit to challenger, not a hallucination. "
                "Classified accuracy excludes caught-misquote from the "
                "denominator (not a claim the challenger made)._",
                "",
            ])

            # REDESIGN A: explicit per-label breakdown + classifier provenance.
            any_llm = any(
                cr[arm].get("n_llm_classified", 0) > 0
                for arm in ("arm-a", "arm-b")
            )
            any_fb = any(
                cr[arm].get("n_regex_fallback", 0) > 0
                for arm in ("arm-a", "arm-b")
            )
            if any_llm or any_fb:
                lines.extend([
                    "### Mechanism classification provenance (REDESIGN A)",
                    "",
                    "| Arm | LLM-classified | Regex-fallback | "
                    "PROPOSAL_ERROR_CAUGHT | CHALLENGER_FABRICATION | "
                    "AMBIGUOUS | INFERENCE_NOT_GROUNDED |",
                    "|---|---|---|---|---|---|---|",
                ])
                for arm in ("arm-a", "arm-b"):
                    a = cr[arm]
                    mech = a.get("mechanism_labels") or {}
                    lines.append(
                        f"| {arm} | {a.get('n_llm_classified', 0)} | "
                        f"{a.get('n_regex_fallback', 0)} | "
                        f"{mech.get('PROPOSAL_ERROR_CAUGHT', 0)} | "
                        f"{mech.get('CHALLENGER_FABRICATION', 0)} | "
                        f"{mech.get('AMBIGUOUS', 0)} | "
                        f"{mech.get('INFERENCE_NOT_GROUNDED', 0)} |"
                    )
                lines.extend([
                    "",
                    "_With LLM classification, hallucination_rate = "
                    "CHALLENGER_FABRICATION / claims_checked and "
                    "classified_accuracy = verified / (verified + "
                    "CHALLENGER_FABRICATION). Same denominator across both "
                    "metrics (orphan #11 fix)._",
                    "",
                ])

    # ── Judge-graded detail ───────────────────────────────────────────
    for dim in JUDGE_GRADED_DIMS:
        d = per_dim.get(dim)
        if not d or "arm-a" not in d:
            continue
        lines.extend([
            f"## {dim} — quality-weighted substantive score",
            "",
            "| Arm | Substantive | Marginal | Superficial | Harmful | Weighted score | Density |",
            "|---|---|---|---|---|---|---|",
        ])
        for arm in ("arm-a", "arm-b"):
            a = d[arm]
            dist = a["quality_distribution_sum"]
            lines.append(
                f"| {arm} | {_fmt_num(dist.get('substantive'))} | "
                f"{_fmt_num(dist.get('marginal'))} | "
                f"{_fmt_num(dist.get('superficial'))} | "
                f"{_fmt_num(dist.get('harmful'))} | "
                f"{_fmt_num(a.get('weighted_score_total'))} | "
                f"{_fmt_pct(a.get('quality_density'))} |"
            )
        lines.append("")

    # ── Convergence advisory ──────────────────────────────────────────
    conv = (verdict.get("overall") or {}).get("convergence_advisory") or {}
    if conv.get("dims_total"):
        lines.extend([
            "## Advisory — judge count convergence (not a gate per D40)",
            "",
            f"- Dims converged: {conv['dims_converged']}/{conv['dims_total']} "
            f"({_fmt_pct(conv.get('convergence_rate'))})",
            f"- Mean |count_delta|: {_fmt_num(conv.get('mean_abs_count_delta'))}",
            f"- Max |count_delta|: {conv.get('max_abs_count_delta', '—')}",
            "",
            "_Wide deltas indicate prompt looseness on extraction counts — "
            "per-dim primary signals above are independent._",
            "",
        ])

    # ── Thresholds ────────────────────────────────────────────────────
    thresholds = verdict.get("decision_thresholds") or {}
    if thresholds:
        lines.extend([
            "## Decision thresholds (pre-registered)",
            "",
            f"- Primary accuracy delta to call a winner: "
            f"{thresholds['primary_accuracy_delta_pp']*100:.0f}pp",
            f"- Hallucination guardrail: primary winner may not regress > "
            f"{thresholds['hallucination_guardrail_pp']*100:.0f}pp",
            f"- Substantive-score delta min: {thresholds['substantive_delta_min']}",
            f"- Harmful regression cap: {thresholds['harmful_regression_absolute_max']}",
            f"- Min sample for directional: {thresholds['min_sample_for_directional']}",
            f"- Min sample for confident: {thresholds['min_sample_for_confident']}",
            f"- Quality weights: {thresholds['quality_weights']}",
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

    verdict = compute_verdict(scored_list, store_root=args.store_root)

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

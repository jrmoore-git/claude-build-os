#!/usr/bin/env python3.11
"""
Arm-comparison study verdict — paired-bootstrap verdicting against a
locked threshold file (REDESIGN C, supersedes the prior fixed-threshold
direct-delta logic).

Reads scorer output (from arm_study_scorer.py) across N proposals and
emits a per-dimension verdict using:

- **Per-proposal aggregation** rather than summed-across-proposals totals
  (eliminates style/verbosity bias on judge-graded dims).
- **Paired bootstrap** (B=10000, fixed seed) on per-proposal deltas to
  produce 95% / 99% CIs. Verdict ladder: inconclusive if CI includes 0
  OR `|mean delta| < floor`; directional if 95% CI excludes 0 AND ≥ floor;
  confident if 99% CI excludes 0 AND ≥ confident-floor.
- **Locked thresholds** loaded from `config/study/arm_study_thresholds.json`
  via `arm_study_thresholds.load_thresholds()`. SHA256 captured in every
  run artifact; `verify_hash` aborts a rerun if the file changed.
- **Rate-based harmful guardrail** — winners with > harmful_rate_per_proposal_max
  fraction of harmful items per proposal are blocked.

This is a redesign of *shipped* verdict logic (commits `52584fc`,
`e2c77ab` wired Dim 5/6 originally). Regression surface relative to
`stores/arm-study/verdict-n3-v7.md` is intentional — direct-delta and
summed-score thresholds didn't scale n=3 → n=10. See D42 (REDESIGN B
sensitivity logging) and D43 (REDESIGN C bootstrap + locked thresholds)
in `tasks/decisions.md`.

If the threshold JSON cannot be read, falls back to legacy module-level
constants in degraded mode and surfaces the fallback in the run artifact.
The overall verdict composition still requires `directional-favor-<arm>`
or `confident-favor-<arm>` for a per-dim vote (D40 framing preserved).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STORE = REPO_ROOT / "stores" / "arm-study"

import sys as _sys  # noqa: E402
_sys.path.insert(0, str(REPO_ROOT / "scripts"))
import arm_study_thresholds as _thresholds  # noqa: E402
import random as _random  # noqa: E402

# ── Thresholds (loaded from locked JSON file with legacy fallback) ─────────
# REDESIGN C: thresholds live in config/study/arm_study_thresholds.json with
# SHA256 captured per-run. Module-level constants below mirror the loaded
# values for backward compat with tests + downstream callers reading them.

_LOADED_THRESHOLDS, _LOADED_THRESHOLDS_HASH = _thresholds.load_thresholds()


def _set_module_thresholds(t: dict) -> None:
    """Hydrate module-level constants from a thresholds dict. Called at
    import time and exposed for test override."""
    global PRIMARY_ACCURACY_DELTA_PP, HALLUCINATION_GUARDRAIL_PP
    global SUBSTANTIVE_DELTA_MIN, SUBSTANTIVE_DELTA_CONFIDENT
    global HARMFUL_RATE_PER_PROPOSAL_MAX
    global MIN_SAMPLE_FOR_DIRECTIONAL, MIN_SAMPLE_FOR_CONFIDENT
    global QUALITY_WEIGHTS
    global BOOTSTRAP_B, BOOTSTRAP_SEED, CI_DIRECTIONAL, CI_CONFIDENT
    global MISS_RATE_DELTA_MIN, MISS_RATE_DELTA_CONFIDENT
    global PLAN_QUALITY_DELTA_MIN, PLAN_QUALITY_DELTA_CONFIDENT
    PRIMARY_ACCURACY_DELTA_PP = t["catch_rate"]["floor_directional_pp"]
    SUBSTANTIVE_DELTA_MIN = t["judge_graded"]["floor_directional"]
    SUBSTANTIVE_DELTA_CONFIDENT = t["judge_graded"]["floor_confident"]
    HALLUCINATION_GUARDRAIL_PP = t["catch_rate"]["hallucination_regression_pp"]
    HARMFUL_RATE_PER_PROPOSAL_MAX = t["judge_graded"]["harmful_rate_per_proposal_max"]
    MIN_SAMPLE_FOR_DIRECTIONAL = t["min_sample_for_directional"]
    MIN_SAMPLE_FOR_CONFIDENT = t["min_sample_for_confident"]
    QUALITY_WEIGHTS = dict(t["quality_weights"])
    BOOTSTRAP_B = t["bootstrap"]["B"]
    BOOTSTRAP_SEED = t["bootstrap"]["seed"]
    CI_DIRECTIONAL = t["bootstrap"]["ci_directional"]
    CI_CONFIDENT = t["bootstrap"]["ci_confident"]
    MISS_RATE_DELTA_MIN = t["miss_rate"]["floor_directional_pp"]
    MISS_RATE_DELTA_CONFIDENT = t["miss_rate"]["floor_confident_pp"]
    PLAN_QUALITY_DELTA_MIN = t["plan_quality_delta"]["floor_directional_pp"]
    PLAN_QUALITY_DELTA_CONFIDENT = t["plan_quality_delta"]["floor_confident_pp"]


_set_module_thresholds(_LOADED_THRESHOLDS)
# Legacy alias kept exported (one downstream test references it).
HARMFUL_REGRESSION_ABSOLUTE_MAX = 2


# ── Paired bootstrap (REDESIGN C) ───────────────────────────────────────────


def _percentile(sorted_vals: list[float], q: float) -> float:
    """Linear-interpolation percentile on a sorted list. q in [0, 1]."""
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def paired_bootstrap_ci(
    deltas: list[float],
    *,
    B: int | None = None,
    seed: int | None = None,
    ci_directional: float | None = None,
    ci_confident: float | None = None,
) -> dict:
    """Pure-Python percentile bootstrap on per-proposal deltas.

    Returns {mean, ci_dir_low, ci_dir_high, ci_conf_low, ci_conf_high, n,
    method}. Tie handling: when all deltas identical, CI collapses to a
    point — return [delta, delta] for both intervals.

    Why percentile and not BCa: at n ≤ 30, BCa's bias-correction
    acceleration estimate is unstable and can produce overly-narrow CIs.
    Percentile is conservative and well-understood.
    """
    if B is None:
        B = BOOTSTRAP_B
    if seed is None:
        seed = BOOTSTRAP_SEED
    if ci_directional is None:
        ci_directional = CI_DIRECTIONAL
    if ci_confident is None:
        ci_confident = CI_CONFIDENT

    n = len(deltas)
    if n == 0:
        return {
            "mean": None, "ci_dir_low": None, "ci_dir_high": None,
            "ci_conf_low": None, "ci_conf_high": None, "n": 0,
            "method": "empty",
        }
    mean_delta = sum(deltas) / n
    if all(d == deltas[0] for d in deltas):
        return {
            "mean": deltas[0],
            "ci_dir_low": deltas[0], "ci_dir_high": deltas[0],
            "ci_conf_low": deltas[0], "ci_conf_high": deltas[0],
            "n": n, "method": "constant-delta",
        }

    rng = _random.Random(seed)
    resample_means = []
    for _ in range(B):
        sample = [rng.choice(deltas) for _ in range(n)]
        resample_means.append(sum(sample) / n)
    resample_means.sort()

    dir_alpha = (1 - ci_directional) / 2  # tail per side
    conf_alpha = (1 - ci_confident) / 2
    ci_dir_low = _percentile(resample_means, dir_alpha)
    ci_dir_high = _percentile(resample_means, 1 - dir_alpha)
    ci_conf_low = _percentile(resample_means, conf_alpha)
    ci_conf_high = _percentile(resample_means, 1 - conf_alpha)
    return {
        "mean": mean_delta,
        "ci_dir_low": ci_dir_low, "ci_dir_high": ci_dir_high,
        "ci_conf_low": ci_conf_low, "ci_conf_high": ci_conf_high,
        "n": n, "method": "percentile",
    }


def _bootstrap_verdict(
    boot: dict, floor_directional: float, floor_confident: float,
) -> tuple[str, str | None]:
    """Map a bootstrap result + floors → verdict label + winner.

    Returns (label, winner) where label is "inconclusive" |
    "directional-favor-arm-a" | "directional-favor-arm-b" |
    "confident-favor-arm-a" | "confident-favor-arm-b" | "not-yet-measured".
    Winner is "arm-a" / "arm-b" / None.

    Confident label additionally requires n ≥ MIN_SAMPLE_FOR_CONFIDENT
    (preserves the n=3 design ceiling — no "confident" claims at n=3 even
    when the bootstrap CI is degenerate-tight).
    """
    mean = boot.get("mean")
    n_paired = boot.get("n", 0)
    if mean is None:
        return "not-yet-measured", None
    abs_mean = abs(mean)
    ci_dir_includes_zero = boot["ci_dir_low"] <= 0 <= boot["ci_dir_high"]
    ci_conf_includes_zero = boot["ci_conf_low"] <= 0 <= boot["ci_conf_high"]
    winner = "arm-b" if mean > 0 else "arm-a"
    if ci_dir_includes_zero or abs_mean < floor_directional:
        return "inconclusive", None
    if (n_paired >= MIN_SAMPLE_FOR_CONFIDENT
            and not ci_conf_includes_zero
            and abs_mean >= floor_confident):
        return f"confident-favor-{winner}", winner
    return f"directional-favor-{winner}", winner

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


def _per_proposal_weighted_accuracy(
    scored: dict[str, Any], arm: str,
) -> tuple[float | None, float | None]:
    """Compute per-proposal (weighted_accuracy, hallucination_rate) for one
    arm. Returns (None, None) if verifier data missing for that arm.

    weighted_accuracy = accuracy × quality_density on catch_rate items.
    accuracy uses CHALLENGER_FABRICATION as the hallucination denominator
    when LLM-mode mechanism labels present (orphan #11), else legacy stats.
    """
    stats = _arm_verifier_stats(scored, arm)
    if stats is None:
        return None, None
    verified = stats["verified"]
    hallucination = stats.get("hallucination", 0)
    falsified = stats["falsified"]
    claims_checked = stats["claims_checked"]
    # Prefer mechanism-classified accuracy when available (REDESIGN A).
    if stats.get("classifier_source") == "llm" and "mechanism_labels" in stats:
        denom_acc = verified + hallucination
        accuracy = (verified / denom_acc) if denom_acc > 0 else None
        hall_rate = (hallucination / claims_checked) if claims_checked > 0 else None
    else:
        denom_acc = verified + falsified
        accuracy = (verified / denom_acc) if denom_acc > 0 else None
        hall_rate = (falsified / claims_checked) if claims_checked > 0 else None
    if accuracy is None:
        return None, hall_rate
    # Quality density on catch_rate items for this proposal.
    dim_data = _arm_dim_data(scored, arm, GROUND_TRUTH_DIM)
    dist = _arm_dim_quality_distribution(dim_data)
    density = _quality_density(dist)
    if density is None:
        density = 1.0  # fallback: no judge items → treat density as 1
    return accuracy * density, hall_rate


def _per_dim_verdict_verifier(
    all_scored: list[dict[str, Any]],
    verifier_agg: dict[str, Any],
    n: int,
) -> dict[str, Any]:
    """REDESIGN C: paired bootstrap on per-proposal weighted_accuracy delta.

    The pooled verifier_agg block is preserved for markdown rendering /
    audit (quality density across all claims, raw vs classified accuracy
    comparison, etc.). The verdict label is computed from per-proposal
    paired bootstrap on weighted_accuracy.
    """
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

    # Build per-proposal weighted_accuracy + hallucination_rate pairs.
    pp_a: list[float] = []
    pp_b: list[float] = []
    pp_hall_a: list[float] = []
    pp_hall_b: list[float] = []
    for scored in all_scored:
        wa_a, hr_a = _per_proposal_weighted_accuracy(scored, "arm-a")
        wa_b, hr_b = _per_proposal_weighted_accuracy(scored, "arm-b")
        if wa_a is None or wa_b is None:
            continue
        pp_a.append(wa_a)
        pp_b.append(wa_b)
        if hr_a is not None and hr_b is not None:
            pp_hall_a.append(hr_a)
            pp_hall_b.append(hr_b)

    if not pp_a:
        # Fallback to pooled comparison when per-proposal data unavailable.
        wa_a_pooled = a.get("weighted_accuracy")
        wa_b_pooled = b.get("weighted_accuracy")
        if wa_a_pooled is None or wa_b_pooled is None:
            out["verdict"] = "not-yet-measured"
            out["reason"] = "verifier accuracy missing on one or both arms"
            return out
        delta = wa_b_pooled - wa_a_pooled
        out["delta_pp"] = delta
        out["primary_basis"] = "pooled_weighted_accuracy (no per-proposal data)"
        if abs(delta) < PRIMARY_ACCURACY_DELTA_PP:
            out["verdict"] = "inconclusive"
            out["reason"] = (
                f"pooled weighted_accuracy delta {delta*100:+.1f}pp < floor "
                f"{PRIMARY_ACCURACY_DELTA_PP*100:.0f}pp"
            )
            return out
        winner = "arm-b" if delta > 0 else "arm-a"
        out["verdict"] = (f"directional-favor-{winner}" if n < MIN_SAMPLE_FOR_CONFIDENT
                          else f"confident-favor-{winner}")
        out["reason"] = (
            f"pooled weighted_accuracy delta {delta*100:+.1f}pp favors "
            f"{winner} (per-proposal bootstrap unavailable)"
        )
        out["primary_winner"] = winner
        return out

    deltas = [b_v - a_v for a_v, b_v in zip(pp_a, pp_b)]
    boot = paired_bootstrap_ci(deltas)
    out["bootstrap"] = boot
    out["per_proposal_mean_a"] = sum(pp_a) / len(pp_a)
    out["per_proposal_mean_b"] = sum(pp_b) / len(pp_b)
    out["delta_pp"] = boot["mean"]
    out["primary_basis"] = "weighted_accuracy paired bootstrap"

    label, winner = _bootstrap_verdict(
        boot,
        floor_directional=PRIMARY_ACCURACY_DELTA_PP,
        floor_confident=PRIMARY_ACCURACY_DELTA_PP * 2,  # 0.10 from JSON
    )

    # Hallucination rate guardrail (per-proposal mean).
    if winner is not None and pp_hall_a and pp_hall_b:
        h_winner = pp_hall_b if winner == "arm-b" else pp_hall_a
        h_loser = pp_hall_a if winner == "arm-b" else pp_hall_b
        h_winner_mean = sum(h_winner) / len(h_winner)
        h_loser_mean = sum(h_loser) / len(h_loser)
        if h_winner_mean - h_loser_mean > HALLUCINATION_GUARDRAIL_PP:
            out["verdict"] = "regression-blocked"
            out["reason"] = (
                f"primary winner ({winner}) hallucinates "
                f"{(h_winner_mean - h_loser_mean)*100:+.1f}pp/proposal more "
                f"than loser; cap {HALLUCINATION_GUARDRAIL_PP*100:.0f}pp"
            )
            out["primary_winner"] = winner
            return out

    out["verdict"] = label
    if label == "inconclusive":
        out["reason"] = (
            f"per-proposal weighted_accuracy delta {boot['mean']*100:+.1f}pp, "
            f"95% CI [{boot['ci_dir_low']*100:+.1f}pp, "
            f"{boot['ci_dir_high']*100:+.1f}pp] includes 0 or |delta| < "
            f"{PRIMARY_ACCURACY_DELTA_PP*100:.0f}pp"
        )
    else:
        out["reason"] = (
            f"per-proposal weighted_accuracy delta {boot['mean']*100:+.1f}pp "
            f"favors {winner}, CI excludes 0; n_paired={boot['n']}"
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
    """REDESIGN C: per-proposal mean weighted score + paired bootstrap CI.

    Per-proposal delta list = `[arm_b_score(p) - arm_a_score(p) for paired p]`.
    Bootstrap on the delta list → 95%/99% CIs. Verdict from
    _bootstrap_verdict against judge_graded floors. Harmful guardrail uses
    per-proposal harmful rate (fraction of harmful items in this dim per
    proposal), winner blocked if mean rate exceeds loser's by more than
    HARMFUL_RATE_PER_PROPOSAL_MAX.
    """
    # Collect per-proposal pairs.
    per_proposal_a: list[float] = []
    per_proposal_b: list[float] = []
    per_proposal_harm_a: list[float] = []
    per_proposal_harm_b: list[float] = []
    unpaired_dropped = 0
    for scored in all_scored:
        a_data = _arm_dim_data(scored, "arm-a", dim)
        b_data = _arm_dim_data(scored, "arm-b", dim)
        a_ws = _weighted_dim_score(a_data)
        b_ws = _weighted_dim_score(b_data)
        if a_ws is None or b_ws is None:
            unpaired_dropped += 1
            continue
        per_proposal_a.append(a_ws)
        per_proposal_b.append(b_ws)
        # Per-proposal harmful rate = harmful_total / total_items_in_dim
        # (denominator is mean across judges).
        a_dist = _arm_dim_quality_distribution(a_data)
        b_dist = _arm_dim_quality_distribution(b_data)
        a_total = sum(a_dist.values()) or 1.0
        b_total = sum(b_dist.values()) or 1.0
        per_proposal_harm_a.append(a_dist.get("harmful", 0) / a_total)
        per_proposal_harm_b.append(b_dist.get("harmful", 0) / b_total)

    # Legacy aggregate fields preserved for backward compat with markdown.
    agg = _aggregate_judge_dim(all_scored, dim)
    out: dict[str, Any] = {
        "dimension": dim,
        "signal_type": "judge-graded per-proposal mean (paired bootstrap)",
        "arm-a": agg["arm-a"],
        "arm-b": agg["arm-b"],
        "unpaired_dropped": unpaired_dropped,
    }

    n_paired = len(per_proposal_a)
    if n_paired == 0:
        out["verdict"] = "not-yet-measured"
        out["reason"] = "no paired-scorable data for this dimension"
        return out

    deltas = [b - a for a, b in zip(per_proposal_a, per_proposal_b)]
    boot = paired_bootstrap_ci(deltas)
    out["bootstrap"] = boot
    out["per_proposal_mean_a"] = sum(per_proposal_a) / n_paired
    out["per_proposal_mean_b"] = sum(per_proposal_b) / n_paired
    out["delta"] = boot["mean"]

    label, winner = _bootstrap_verdict(
        boot, SUBSTANTIVE_DELTA_MIN, SUBSTANTIVE_DELTA_CONFIDENT,
    )

    # Harmful-rate-per-proposal guardrail.
    if winner is not None and per_proposal_harm_a and per_proposal_harm_b:
        winner_harm = per_proposal_harm_b if winner == "arm-b" else per_proposal_harm_a
        loser_harm = per_proposal_harm_a if winner == "arm-b" else per_proposal_harm_b
        winner_harm_mean = sum(winner_harm) / len(winner_harm)
        loser_harm_mean = sum(loser_harm) / len(loser_harm)
        if winner_harm_mean - loser_harm_mean > HARMFUL_RATE_PER_PROPOSAL_MAX:
            out["verdict"] = "regression-blocked"
            out["reason"] = (
                f"primary winner ({winner}) per-proposal harmful rate "
                f"{winner_harm_mean:.2%} vs loser's {loser_harm_mean:.2%}; "
                f"delta exceeds cap {HARMFUL_RATE_PER_PROPOSAL_MAX:.0%}"
            )
            out["primary_winner"] = winner
            out["winner_harm_rate"] = winner_harm_mean
            out["loser_harm_rate"] = loser_harm_mean
            return out

    out["verdict"] = label
    if label == "inconclusive":
        out["reason"] = (
            f"per-proposal mean delta {boot['mean']:+.2f}, 95% CI "
            f"[{boot['ci_dir_low']:+.2f}, {boot['ci_dir_high']:+.2f}] "
            f"includes 0 or |delta| < floor {SUBSTANTIVE_DELTA_MIN}; n_paired={n_paired}"
        )
    else:
        strength = "confident" if label.startswith("confident") else "directional"
        ci_used = (
            f"[{boot['ci_conf_low']:+.2f}, {boot['ci_conf_high']:+.2f}]"
            if strength == "confident"
            else f"[{boot['ci_dir_low']:+.2f}, {boot['ci_dir_high']:+.2f}]"
        )
        out["reason"] = (
            f"per-proposal mean delta {boot['mean']:+.2f} favors {winner}, "
            f"{strength} CI {ci_used} excludes 0; n_paired={n_paired}"
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

    out["retrospective_proposals_with_artifact"] = n - no_artifact_count
    retro_n = n - no_artifact_count

    # REDESIGN C: bootstrap on per-proposal landing-rate delta.
    pp_a_rates: list[float] = []
    pp_b_rates: list[float] = []
    for scored in all_scored:
        retro = _load_retrospective_for_scored(scored, store_root)
        if retro is None or retro.get("status") != "scored":
            continue
        per_arm_retro = retro.get("per_arm") or {}
        a_retro = per_arm_retro.get("arm-a") or {}
        b_retro = per_arm_retro.get("arm-b") or {}
        if (a_retro.get("status") != "scored"
                or b_retro.get("status") != "scored"):
            continue
        a_summary = a_retro.get("summary") or {}
        b_summary = b_retro.get("summary") or {}
        a_total = int(a_summary.get("total", 0))
        b_total = int(b_summary.get("total", 0))
        if a_total <= 0 or b_total <= 0:
            continue
        a_landed = (int(a_summary.get("landed", 0))
                    + 0.5 * int(a_summary.get("partial", 0)))
        b_landed = (int(b_summary.get("landed", 0))
                    + 0.5 * int(b_summary.get("partial", 0)))
        pp_a_rates.append(a_landed / a_total)
        pp_b_rates.append(b_landed / b_total)

    if pp_a_rates:
        # Higher landing rate wins; delta = b - a (positive favors B).
        deltas = [b - a for a, b in zip(pp_a_rates, pp_b_rates)]
        boot = paired_bootstrap_ci(deltas)
        out["bootstrap"] = boot
        out["per_proposal_mean_a"] = sum(pp_a_rates) / len(pp_a_rates)
        out["per_proposal_mean_b"] = sum(pp_b_rates) / len(pp_b_rates)
        out["delta"] = boot["mean"]
        label, winner = _bootstrap_verdict(
            boot, PLAN_QUALITY_DELTA_MIN, PLAN_QUALITY_DELTA_CONFIDENT,
        )
        if retro_n < MIN_SAMPLE_FOR_DIRECTIONAL and label != "inconclusive":
            out["verdict"] = "insufficient-retrospective-sample"
            out["reason"] = (
                f"retro_n={retro_n} < {MIN_SAMPLE_FOR_DIRECTIONAL}"
            )
            return out
        out["verdict"] = label
        if label == "inconclusive":
            out["reason"] = (
                f"per-proposal landing-rate delta {boot['mean']*100:+.1f}pp, "
                f"95% CI [{boot['ci_dir_low']*100:+.1f}pp, "
                f"{boot['ci_dir_high']*100:+.1f}pp] includes 0 or "
                f"|delta| < {PLAN_QUALITY_DELTA_MIN*100:.0f}pp"
            )
        else:
            out["reason"] = (
                f"per-proposal landing-rate delta {boot['mean']*100:+.1f}pp "
                f"favors {winner}; n_paired={boot['n']}"
            )
            out["primary_winner"] = winner
        return out

    # Fallback: pooled comparison.
    delta = lr_b - lr_a
    out["delta"] = delta
    if abs(delta) < PLAN_QUALITY_DELTA_MIN:
        out["verdict"] = "inconclusive"
        out["reason"] = (
            f"pooled landing-rate delta {delta*100:+.1f}pp < "
            f"{PLAN_QUALITY_DELTA_MIN*100:.0f}pp"
        )
        return out
    winner = "arm-b" if delta > 0 else "arm-a"
    if retro_n < MIN_SAMPLE_FOR_DIRECTIONAL:
        out["verdict"] = "insufficient-retrospective-sample"
        out["reason"] = (
            f"only {retro_n} of {n} proposals had a downstream artifact"
        )
        return out
    out["verdict"] = (
        f"directional-favor-{winner}"
        if retro_n < MIN_SAMPLE_FOR_CONFIDENT
        else f"confident-favor-{winner}"
    )
    out["reason"] = f"pooled landing-rate delta {delta*100:+.1f}pp favors {winner}"
    out["primary_winner"] = winner
    return out


def _per_dim_verdict_miss_rate(
    all_scored: list[dict[str, Any]], n: int,
) -> dict[str, Any]:
    """miss_rate verdict based on reference-issue coverage (item 5 output).

    Pools reference issues across proposals per arm; miss_rate(arm) =
    total_missed / total_reference_issues. Lower is better.

    REDESIGN B: when the discoverer ran in ensemble mode, scored.json
    carries reference_coverage_sensitivity with per-rule (majority / union /
    intersection) coverage. The primary verdict still uses majority; the
    sensitivity block is surfaced for the markdown report.
    """
    pooled = {arm: {"caught": 0, "missed": 0, "total": 0}
              for arm in ("arm-a", "arm-b")}
    sensitivity_pooled = {
        rule: {arm: {"caught": 0, "missed": 0, "total": 0}
               for arm in ("arm-a", "arm-b")}
        for rule in ("majority", "union", "intersection")
    }
    sensitivity_present = False
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
        # Pool sensitivity data when both arms have it for this proposal.
        a_sens = (
            (_arm_dim_data(scored, "arm-a", "miss_rate") or {})
            .get("reference_coverage_sensitivity") or {}
        )
        b_sens = (
            (_arm_dim_data(scored, "arm-b", "miss_rate") or {})
            .get("reference_coverage_sensitivity") or {}
        )
        if a_sens and b_sens:
            sensitivity_present = True
            for rule in ("majority", "union", "intersection"):
                a_rule = a_sens.get(rule) or {}
                b_rule = b_sens.get(rule) or {}
                if not a_rule or not b_rule:
                    continue
                for arm, rd in (("arm-a", a_rule), ("arm-b", b_rule)):
                    sensitivity_pooled[rule][arm]["caught"] += int(
                        rd.get("caught_count", 0))
                    sensitivity_pooled[rule][arm]["missed"] += int(
                        rd.get("missed_count", 0))
                    sensitivity_pooled[rule][arm]["total"] += int(
                        rd.get("total_reference_issues", 0))

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

    # REDESIGN C: bootstrap on per-proposal miss_rate delta (lower wins).
    pp_a_rates: list[float] = []
    pp_b_rates: list[float] = []
    for scored in all_scored:
        a_rc = ((_arm_dim_data(scored, "arm-a", "miss_rate") or {})
                .get("reference_coverage") or {})
        b_rc = ((_arm_dim_data(scored, "arm-b", "miss_rate") or {})
                .get("reference_coverage") or {})
        if a_rc.get("status") != "scored" or b_rc.get("status") != "scored":
            continue
        a_total = int(a_rc.get("total_reference_issues", 0))
        b_total = int(b_rc.get("total_reference_issues", 0))
        if a_total <= 0 or b_total <= 0:
            continue
        pp_a_rates.append(int(a_rc.get("missed_count", 0)) / a_total)
        pp_b_rates.append(int(b_rc.get("missed_count", 0)) / b_total)

    if pp_a_rates:
        # Lower miss_rate wins. delta = a - b means positive favors arm-b.
        deltas = [a - b for a, b in zip(pp_a_rates, pp_b_rates)]
        boot = paired_bootstrap_ci(deltas)
        out["bootstrap"] = boot
        out["per_proposal_mean_a"] = sum(pp_a_rates) / len(pp_a_rates)
        out["per_proposal_mean_b"] = sum(pp_b_rates) / len(pp_b_rates)
        out["delta"] = boot["mean"]
        label, winner = _bootstrap_verdict(
            boot, MISS_RATE_DELTA_MIN, MISS_RATE_DELTA_CONFIDENT,
        )
        if label == "inconclusive":
            out["verdict"] = label
            out["reason"] = (
                f"per-proposal miss_rate delta {boot['mean']*100:+.1f}pp, "
                f"95% CI [{boot['ci_dir_low']*100:+.1f}pp, "
                f"{boot['ci_dir_high']*100:+.1f}pp] includes 0 or "
                f"|delta| < {MISS_RATE_DELTA_MIN*100:.0f}pp"
            )
        else:
            out["verdict"] = label
            out["reason"] = (
                f"per-proposal miss_rate delta {boot['mean']*100:+.1f}pp "
                f"favors {winner}, CI excludes 0; n_paired={boot['n']}"
            )
            out["primary_winner"] = winner
    else:
        # Fallback to pooled comparison.
        delta = mr_a - mr_b
        out["delta"] = delta
        if abs(delta) < MISS_RATE_DELTA_MIN:
            out["verdict"] = "inconclusive"
            out["reason"] = (
                f"miss_rate delta {delta*100:+.1f}pp < {MISS_RATE_DELTA_MIN*100:.0f}pp"
            )
        else:
            winner = "arm-b" if delta > 0 else "arm-a"
            out["verdict"] = (
                f"directional-favor-{winner}"
                if n < MIN_SAMPLE_FOR_CONFIDENT
                else f"confident-favor-{winner}"
            )
            out["reason"] = (
                f"pooled miss_rate delta {delta*100:+.1f}pp favors {winner}"
            )
            out["primary_winner"] = winner
    # REDESIGN B sensitivity: append per-rule pooled coverage so render
    # can show how the verdict shifts under union/intersection aggregation.
    if sensitivity_present:
        sens_block: dict[str, Any] = {}
        for rule in ("majority", "union", "intersection"):
            r_pooled = sensitivity_pooled[rule]
            for arm in ("arm-a", "arm-b"):
                t = r_pooled[arm]["total"]
                r_pooled[arm]["miss_rate"] = (
                    r_pooled[arm]["missed"] / t if t > 0 else None
                )
            mr_a = r_pooled["arm-a"]["miss_rate"]
            mr_b = r_pooled["arm-b"]["miss_rate"]
            if mr_a is None or mr_b is None:
                rule_delta = None
                rule_winner = None
            else:
                rule_delta = mr_a - mr_b
                rule_winner = (
                    "arm-b" if rule_delta > 0
                    else ("arm-a" if rule_delta < 0 else None)
                )
            sens_block[rule] = {
                "arm-a": r_pooled["arm-a"],
                "arm-b": r_pooled["arm-b"],
                "delta": rule_delta,
                "winner": rule_winner,
            }
        out["sensitivity"] = sens_block
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
        "substantive_delta_confident": SUBSTANTIVE_DELTA_CONFIDENT,
        "harmful_rate_per_proposal_max": HARMFUL_RATE_PER_PROPOSAL_MAX,
        "min_sample_for_directional": MIN_SAMPLE_FOR_DIRECTIONAL,
        "min_sample_for_confident": MIN_SAMPLE_FOR_CONFIDENT,
        "quality_weights": QUALITY_WEIGHTS,
        "bootstrap_B": BOOTSTRAP_B,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "ci_directional": CI_DIRECTIONAL,
        "ci_confident": CI_CONFIDENT,
        "thresholds_path": str(_thresholds.DEFAULT_THRESHOLDS_PATH),
        "thresholds_sha256": _LOADED_THRESHOLDS_HASH,
        "thresholds_version": _LOADED_THRESHOLDS.get("version", "unknown"),
        "thresholds_source": (
            "locked-json" if _LOADED_THRESHOLDS_HASH != "legacy-fallback"
            else "legacy-fallback"
        ),
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

    # ── miss_rate sensitivity (REDESIGN B) ────────────────────────────
    mr = per_dim.get("miss_rate")
    if mr and mr.get("sensitivity"):
        sens = mr["sensitivity"]
        lines.extend([
            "## miss_rate — sensitivity to ensemble aggregation (REDESIGN B)",
            "",
            "| Rule | arm-a miss-rate | arm-b miss-rate | Delta (a−b) | Rule winner |",
            "|---|---|---|---|---|",
        ])
        for rule in ("majority", "union", "intersection"):
            r = sens.get(rule, {})
            mr_a = (r.get("arm-a") or {}).get("miss_rate")
            mr_b = (r.get("arm-b") or {}).get("miss_rate")
            delta = r.get("delta")
            winner = r.get("winner") or "—"
            lines.append(
                f"| {rule} | {_fmt_pct(mr_a)} | {_fmt_pct(mr_b)} | "
                f"{('—' if delta is None else f'{delta*100:+.1f}pp')} | "
                f"{winner} |"
            )
        lines.extend([
            "",
            "_Majority is the primary scoring rule; union/intersection shown "
            "for sensitivity. If the rule winner flips across rules, the "
            "miss_rate signal is fragile to discoverer aggregation choice._",
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
            f"- Substantive-score delta confident: {thresholds.get('substantive_delta_confident', '—')}",
            f"- Harmful rate per proposal max: {thresholds.get('harmful_rate_per_proposal_max', '—')}",
            f"- Min sample for directional: {thresholds['min_sample_for_directional']}",
            f"- Min sample for confident: {thresholds['min_sample_for_confident']}",
            f"- Quality weights: {thresholds['quality_weights']}",
            f"- Bootstrap B / seed: {thresholds.get('bootstrap_B', '—')} / {thresholds.get('bootstrap_seed', '—')}",
            f"- Thresholds path: {thresholds.get('thresholds_path', '—')}",
            f"- Thresholds SHA256: {(thresholds.get('thresholds_sha256') or '—')[:16]}",
            f"- Thresholds source: {thresholds.get('thresholds_source', '—')}",
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

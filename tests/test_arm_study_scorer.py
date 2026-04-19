"""Unit tests for scripts/arm_study_scorer.py.

Covers 10 edge cases from the Phase 1 Track B-min plan:
  1. Tie on primary → falls through to secondary (secondary stub OK)
  2. Variance > ½ inter-arm gap → INCONCLUSIVE on that dimension
  3. Missing Dim 4/5 data → marked not_scorable (not zero)
  4. All dimensions INCONCLUSIVE → aggregate fallback fires
  5. Split judge (count+category disagreement) → pair INCONCLUSIVE
  6. Unanimous judge (count ±0, category ≥80%) → convergence=high
  7. Substantive-count weighting (10 items 2-sub vs 3 items 3-sub)
  8. Quality-only disagreement → flagged, not silently averaged
  9. Stratified aggregation with unequal type counts
 10. Cost data missing on one arm → graceful handling

Uses pytest conventions, fixtures only, no real API calls.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import arm_study_scorer as scorer  # noqa: E402


# ── Fixture builders ────────────────────────────────────────────────────────


def _item(item_id: str, quality: str) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "source_present": False,
        "quality": quality,
        "rationale": f"test rationale {item_id}",
    }


def _dim_block(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"items": items}


def _full_extraction(
    overrides: dict[str, list[dict[str, Any]]] | None = None,
    default_quality: str = "marginal",
    default_count: int = 2,
) -> dict[str, Any]:
    overrides = overrides or {}
    out: dict[str, Any] = {}
    for dim in scorer.DIMENSIONS:
        if dim in overrides:
            out[dim] = _dim_block(overrides[dim])
        else:
            out[dim] = _dim_block(
                [_item(f"{dim}-{i}", default_quality) for i in range(default_count)]
            )
    return out


# ── 1. Tie on primary → falls through to secondary ──────────────────────────


def test_tie_on_primary_falls_through_to_secondary():
    """Dim 5 (miss_rate) identical across arms → aggregation reports a tie,
    and per-dimension data for secondary dimensions remains intact so a later
    verdict step can pick up the fallthrough. Stub-level check: scorer does
    not collapse secondary data on primary tie."""
    judge_ext_a = _full_extraction({
        "miss_rate": [_item("m1", "substantive"), _item("m2", "marginal")],
        "direction_improvement": [_item("d1", "substantive"), _item("d2", "substantive")],
    })
    judge_ext_b = _full_extraction({
        "miss_rate": [_item("m1", "substantive"), _item("m2", "marginal")],
        "direction_improvement": [_item("d1", "marginal")],
    })

    arm_x_judges = {"A": judge_ext_a, "B": judge_ext_a}
    arm_y_judges = {"A": judge_ext_b, "B": judge_ext_b}

    scored = scorer.aggregate_proposal({"arm-x": arm_x_judges, "arm-y": arm_y_judges})
    # Primary: miss_rate substantive counts equal → tie on primary.
    x_sub = sum(scored["arms"]["arm-x"]["miss_rate"]["substantive_count"].values())
    y_sub = sum(scored["arms"]["arm-y"]["miss_rate"]["substantive_count"].values())
    assert x_sub == y_sub, "primary outcome should tie for this fixture"
    # Secondary (direction_improvement) should differ AND remain scored.
    assert scored["arms"]["arm-x"]["direction_improvement"]["status"] == "scored"
    assert scored["arms"]["arm-y"]["direction_improvement"]["status"] == "scored"
    sec_x = sum(scored["arms"]["arm-x"]["direction_improvement"]["substantive_count"].values())
    sec_y = sum(scored["arms"]["arm-y"]["direction_improvement"]["substantive_count"].values())
    assert sec_x != sec_y, "secondary data must be retained when primary ties"


# ── 2. Variance > ½ inter-arm gap → INCONCLUSIVE on that dimension ──────────


def test_variance_exceeds_half_gap_marks_inconclusive():
    judge_ext_a = _full_extraction({
        "miss_rate": [_item("m1", "substantive"), _item("m2", "substantive")],
    })
    judge_ext_b = _full_extraction({
        "miss_rate": [_item("m1", "substantive"), _item("m2", "substantive"),
                      _item("m3", "substantive")],
    })
    scored = scorer.aggregate_proposal({
        "arm-x": {"A": judge_ext_a, "B": judge_ext_a},
        "arm-y": {"A": judge_ext_b, "B": judge_ext_b},
    })
    # Inter-arm gap on miss_rate substantive_count: 4 vs 6 → gap = 2.
    # Within-arm variance of 1.5 > 0.5 * 2 → triggers variance rule.
    within_arm = {
        "arm-x": {"miss_rate": 1.5},
        "arm-y": {"miss_rate": 1.5},
    }
    scored = scorer.check_variance_gap(scored, within_arm)
    assert scored["arms"]["arm-x"]["miss_rate"]["status"] == "inconclusive-variance"
    assert scored["arms"]["arm-y"]["miss_rate"]["status"] == "inconclusive-variance"
    assert scored["arms"]["arm-x"]["miss_rate"].get("variance_exceeded_gap") is True


# ── 3. Missing Dim 4/5 → not_scorable (not zero) ────────────────────────────


def test_missing_dim4_5_marks_not_scorable():
    """If neither judge emits a catch_rate or miss_rate block for a
    proposal, those dimensions must be not_scorable — NOT silently zero."""
    partial = _full_extraction()
    partial.pop("catch_rate")
    partial.pop("miss_rate")
    scored = scorer.aggregate_proposal({
        "arm-x": {"A": partial, "B": partial},
        "arm-y": {"A": partial, "B": partial},
    })
    assert scored["arms"]["arm-x"]["catch_rate"]["status"] == "not_scorable"
    assert scored["arms"]["arm-x"]["miss_rate"]["status"] == "not_scorable"
    # Crucially: substantive_count should NOT be populated with zeros as if
    # the judges had emitted empty lists — it's just empty / not comparable.
    assert scored["arms"]["arm-x"]["catch_rate"]["substantive_count"] == {}
    assert scored["arms"]["arm-x"]["miss_rate"]["substantive_count"] == {}


# ── 4. All dimensions INCONCLUSIVE → aggregate fallback fires ───────────────


def test_all_dimensions_inconclusive_triggers_aggregate_fallback():
    # Build two judges that disagree on count by >1 AND quality by <60% for
    # every dimension.
    def _disagree(dim: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        judge_a = [_item(f"{dim}-{i}", "substantive") for i in range(5)]
        judge_b = [_item(f"{dim}-{i}", "marginal") for i in range(2)]
        return judge_a, judge_b

    ext_a: dict[str, Any] = {}
    ext_b: dict[str, Any] = {}
    for dim in scorer.DIMENSIONS:
        a_items, b_items = _disagree(dim)
        ext_a[dim] = _dim_block(a_items)
        ext_b[dim] = _dim_block(b_items)

    arm_judges = {"A": ext_a, "B": ext_b}
    scored = scorer.aggregate_proposal({"arm-x": arm_judges, "arm-y": arm_judges})

    statuses = {
        scored["arms"][arm][dim]["status"]
        for arm in ("arm-x", "arm-y") for dim in scorer.DIMENSIONS
    }
    assert statuses == {"inconclusive-split"}, f"unexpected statuses: {statuses}"
    assert scored["aggregate_inconclusive"] is True


# ── 5. Split judge → pair INCONCLUSIVE for that dimension ───────────────────


def test_split_judges_count_and_category_disagreement_is_inconclusive():
    split_a = _full_extraction({
        "nuance_caught": [_item(f"n-{i}", "substantive") for i in range(6)],
    })
    split_b = _full_extraction({
        "nuance_caught": [_item(f"n-{i}", "superficial") for i in range(2)],
    })
    arm_judges = {"A": split_a, "B": split_b}
    agg = scorer.aggregate_dimension(arm_judges, "nuance_caught")
    # count delta 4 > 1 tolerance.
    assert agg["convergence"]["count_converged"] is False
    # quality agreement = 0 (no shared item_ids; paired by idx; different cats).
    assert agg["convergence"]["quality_agreement_rate"] == 0.0
    assert agg["status"] == "inconclusive-split"
    assert agg["convergence"]["level"] == "split"


# ── 6. Unanimous judges → propagation correct (convergence=high) ────────────


def test_unanimous_judges_propagates_high_convergence():
    # Both judges: 3 items, all substantive, identical item_ids.
    items = [_item("u-1", "substantive"), _item("u-2", "substantive"),
             _item("u-3", "substantive")]
    ext_a = _full_extraction({"direction_improvement": items})
    ext_b = _full_extraction({"direction_improvement": items})
    agg = scorer.aggregate_dimension({"A": ext_a, "B": ext_b}, "direction_improvement")
    assert agg["status"] == "scored"
    assert agg["convergence"]["count_converged"] is True
    assert agg["convergence"]["quality_agreement_rate"] == 1.0
    assert agg["convergence"]["level"] == "high"


# ── 7. Substantive-count weighting: 10/2-sub vs 3/3-sub → 3-sub wins ────────


def test_substantive_count_winner_beats_raw_count():
    # Arm X: 10 items, 2 substantive. Arm Y: 3 items, 3 substantive.
    arm_x_items = ([_item(f"x-sub-{i}", "substantive") for i in range(2)]
                   + [_item(f"x-marg-{i}", "marginal") for i in range(8)])
    arm_y_items = [_item(f"y-sub-{i}", "substantive") for i in range(3)]
    ext_x = _full_extraction({"net_new_ideas": arm_x_items})
    ext_y = _full_extraction({"net_new_ideas": arm_y_items})
    scored = scorer.aggregate_proposal({
        "arm-x": {"A": ext_x, "B": ext_x},
        "arm-y": {"A": ext_y, "B": ext_y},
    })
    x_raw = sum(scored["arms"]["arm-x"]["net_new_ideas"]["item_counts"].values())
    y_raw = sum(scored["arms"]["arm-y"]["net_new_ideas"]["item_counts"].values())
    x_sub = sum(scored["arms"]["arm-x"]["net_new_ideas"]["substantive_count"].values())
    y_sub = sum(scored["arms"]["arm-y"]["net_new_ideas"]["substantive_count"].values())
    assert x_raw > y_raw  # arm-x wins raw count (20 vs 6)
    assert y_sub > x_sub  # arm-y wins substantive (6 vs 4)


# ── 8. Quality-only disagreement → flagged, not silently averaged ───────────


def test_quality_only_disagreement_is_flagged():
    # Both judges agree on count AND item_ids, but disagree on quality rating.
    items_a = [_item("q-1", "substantive"), _item("q-2", "substantive"),
               _item("q-3", "substantive")]
    items_b = [_item("q-1", "marginal"), _item("q-2", "marginal"),
               _item("q-3", "marginal")]
    ext_a = _full_extraction({"plan_quality_delta": items_a})
    ext_b = _full_extraction({"plan_quality_delta": items_b})
    agg = scorer.aggregate_dimension({"A": ext_a, "B": ext_b}, "plan_quality_delta")
    assert agg["convergence"]["count_converged"] is True
    # agreement rate = 0: judges pair on shared item_ids, all categories differ.
    assert agg["convergence"]["quality_agreement_rate"] == 0.0
    # Should record per-item disagreements rather than silently averaging.
    assert len(agg["quality_disagreements"]) == 3
    for d in agg["quality_disagreements"]:
        assert set(d["judge_ratings"].keys()) == {"A", "B"}
        assert d["judge_ratings"]["A"] == "substantive"
        assert d["judge_ratings"]["B"] == "marginal"


# ── 9. Stratified aggregation with unequal type counts ──────────────────────


def test_stratified_counts_track_unequal_proposal_types():
    per_proposal = [
        {"proposal_type": "governance"},
        {"proposal_type": "governance"},
        {"proposal_type": "governance"},
        {"proposal_type": "architecture"},
    ]
    strat = scorer.compute_stratified_counts(per_proposal)
    assert strat["governance"]["proposals"] == 3
    assert strat["architecture"]["proposals"] == 1
    assert set(strat.keys()) == {"governance", "architecture"}


# ── 10. Cost data missing on one arm → graceful handling ────────────────────


def test_missing_cost_data_does_not_crash(capsys):
    """Cost data is metadata — not part of per-dimension aggregation. If an
    arm's cost file is absent, dry-run/fixture path must still produce a
    scored object without raising."""
    judges = ["gpt-5.4", "gemini-3.1-pro"]
    scored = scorer.build_dry_run_scored(judges)
    # Simulate missing cost metadata on one arm by NOT populating cost fields.
    # The scorer should not hard-require them.
    assert "arms" in scored
    assert "metadata" in scored
    # No 'cost' key in metadata — and nothing crashes downstream:
    md = scorer.render_markdown(scored)
    assert "Arm-comparison scored results" in md


# ── Family exclusion guard ──────────────────────────────────────────────────


def test_family_exclusion_rejects_claude_judge():
    with pytest.raises(ValueError, match="family-exclusion"):
        scorer.enforce_non_claude(["claude-opus-4-6", "gemini-3.1-pro"])


def test_family_exclusion_accepts_non_claude():
    out = scorer.enforce_non_claude(["gpt-5.4", "gemini-3.1-pro"])
    assert out == ["gpt-5.4", "gemini-3.1-pro"]


# ── Parser smoke test ───────────────────────────────────────────────────────


def test_parse_judge_output_handles_fenced_json():
    fake_stdout = """## Reviewer A

Some preamble.

```json
{"direction_improvement": {"items": [{"item_id": "a-1", "quality": "substantive"}]}}
```

## Reviewer B

```json
{"direction_improvement": {"items": []}}
```
"""
    parsed = scorer.parse_judge_output(fake_stdout)
    assert "A" in parsed and "B" in parsed
    assert parsed["A"]["direction_improvement"]["items"][0]["item_id"] == "a-1"
    assert parsed["B"]["direction_improvement"]["items"] == []


def test_classify_falsified_challenger_only_is_hallucination():
    """Source names Challenger alone → hallucination (independent false claim)."""
    text = """## Claim Verification Results

1. **Claim**: `scripts/batch_dispatch.py` exists
   **Source**: Challenger B
   **Status**: FALSIFIED
   **Evidence**: not present on disk.
"""
    out = scorer.classify_falsified_claims(text)
    assert out["hallucination"] == 1
    assert out["caught_misquote"] == 0
    assert out["unclear"] == 0
    assert out["total_falsified"] == 1


def test_classify_falsified_proposal_only_is_caught_misquote():
    """Source names Proposal alone → challenger was quoting the proposal
    to flag it; proposal is the wrong one."""
    text = """## Claim Verification Results

1. **Claim**: CLAUDE.md says "Update decisions.md"
   **Source**: Proposal (1A)
   **Status**: FALSIFIED
   **Evidence**: phrase not found in CLAUDE.md.
"""
    out = scorer.classify_falsified_claims(text)
    assert out["caught_misquote"] == 1
    assert out["hallucination"] == 0


def test_classify_falsified_mixed_source_is_caught_misquote():
    """Mixed source (Proposal + Challenger) → conservatively caught_misquote;
    the challenger echoed a proposal claim in a critique context."""
    text = """## Claim Verification Results

1. **Claim**: review-protocol.md contains "--skip-challenge"
   **Source**: Proposal (1C), Challenger A
   **Status**: FALSIFIED
   **Evidence**: flag not in rules.
"""
    out = scorer.classify_falsified_claims(text)
    assert out["caught_misquote"] == 1
    assert out["hallucination"] == 0


def test_classify_verified_and_unresolvable_counted_but_not_classified():
    text = """## Claim Verification Results

1. **Claim**: foo
   **Source**: Challenger A
   **Status**: VERIFIED
   **Evidence**: match found.

2. **Claim**: bar
   **Source**: Proposal
   **Status**: UNRESOLVABLE
   **Evidence**: ambiguous.
"""
    out = scorer.classify_falsified_claims(text)
    assert out["total_verified"] == 1
    assert out["total_unresolvable"] == 1
    assert out["total_falsified"] == 0
    assert out["hallucination"] == 0
    assert out["caught_misquote"] == 0


def test_classify_empty_input_returns_zeros():
    assert scorer.classify_falsified_claims("")["total_falsified"] == 0
    assert scorer.classify_falsified_claims(None)["total_falsified"] == 0


def test_classify_unparseable_source_is_unclear():
    text = """## Claim Verification Results

1. **Claim**: something
   **Status**: FALSIFIED
   **Evidence**: checked.
"""
    # No Source line at all — classification falls through to unclear.
    out = scorer.classify_falsified_claims(text)
    assert out["total_falsified"] == 1
    assert out["unclear"] == 1
    assert out["hallucination"] == 0
    assert out["caught_misquote"] == 0


def test_parse_judge_output_strips_dimension_prefix():
    """Comparison prompt emits `dimension_N_<name>` keys; aggregator indexes
    bare `<name>`. parse_judge_output must strip the prefix so real runs
    don't silently produce all-not_scorable results (M-1)."""
    fake_stdout = """## Reviewer A

```json
{
  "dimension_1_direction_improvement": {"items": [{"item_id": "d-1", "quality": "substantive"}]},
  "dimension_6_plan_quality_delta": {"items": []},
  "dimension_7_code_review_quality_delta": {"items": []}
}
```
"""
    parsed = scorer.parse_judge_output(fake_stdout)
    assert "direction_improvement" in parsed["A"]
    assert "dimension_1_direction_improvement" not in parsed["A"]
    assert parsed["A"]["direction_improvement"]["items"][0]["item_id"] == "d-1"
    assert "plan_quality_delta" in parsed["A"]
    assert "code_review_quality_delta" in parsed["A"]

"""Unit tests for scripts/arm_study_verdict.py — per-dimension verdict logic.

Covers family-exclusion, catch_rate verifier dim verdict (accuracy +
hallucination guard + quality-weighted alignment), judge-graded dim verdict
(weighted substantive score + harmful regression guard), not-yet-measured
dim stubs, and overall verdict composition.

Fixtures are constructed with a helper so each test declares only the
values that matter to it.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import arm_study_verdict as verdict  # noqa: E402


# ── Test fixture builder ────────────────────────────────────────────────────


def _qdist(substantive=0, marginal=0, superficial=0, harmful=0):
    return {"substantive": substantive, "marginal": marginal,
            "superficial": superficial, "harmful": harmful}


def _scored(
    catch_rate_verifier: tuple[int, int, int] | None = None,
    catch_rate_quality: dict[str, int] | None = None,
    dim_quality: dict[str, dict[str, dict[str, int]]] | None = None,
    judges: list[str] | None = None,
    run_id: str = "test-run",
    arm_swap: bool = False,
) -> dict[str, Any]:
    """Build a minimal scored dict.

    catch_rate_verifier: (verified, falsified, unresolvable) for arm-a; arm-b
        gets the same tuple unless arm_swap=True.
    catch_rate_quality: per-arm quality dict {"arm-a": {"substantive": N, ...}}.
    dim_quality: per-dim per-arm quality dict, e.g.
        {"direction_improvement": {"arm-a": {"substantive": 3, ...},
                                   "arm-b": {...}}}.
    """
    judges = judges or ["gpt-5.4", "gemini-3.1-pro"]
    ja, jb = judges[0], judges[1]
    catch_rate_quality = catch_rate_quality or {
        "arm-a": _qdist(), "arm-b": _qdist(),
    }

    def _build_arm(arm: str):
        out: dict[str, Any] = {
            "catch_rate": {
                "dimension": "catch_rate",
                "status": "scored",
                "substantive_count": {ja: catch_rate_quality[arm].get("substantive", 0),
                                       jb: catch_rate_quality[arm].get("substantive", 0)},
                "quality_distribution": {
                    ja: catch_rate_quality[arm],
                    jb: catch_rate_quality[arm],
                },
                "convergence": {"count_converged": True, "count_delta": 0,
                                "level": "high"},
            }
        }
        if catch_rate_verifier is not None:
            v, f, u = catch_rate_verifier
            out["catch_rate"]["verify_claims"] = {
                "status": "verified",
                "stats": {
                    "verified": v, "falsified": f, "unresolvable": u,
                    "claims_checked": v + f + u,
                    "model": "claude-sonnet-4-6",
                    "tool_calls": 0,
                },
            }
        else:
            out["catch_rate"]["verify_claims"] = {
                "status": "failed", "stats": None, "error": "test fixture",
            }
        for dim in verdict.JUDGE_GRADED_DIMS:
            q = (dim_quality or {}).get(dim, {}).get(arm) or _qdist()
            out[dim] = {
                "dimension": dim,
                "status": "scored",
                "substantive_count": {ja: q.get("substantive", 0),
                                       jb: q.get("substantive", 0)},
                "quality_distribution": {ja: q, jb: q},
                "convergence": {"count_converged": True, "count_delta": 0,
                                "level": "high"},
            }
        return out

    return {
        "metadata": {"judges": judges, "run_id": run_id},
        "arms": {"arm-a": _build_arm("arm-a"), "arm-b": _build_arm("arm-b")},
        "unblinded": True,
    }


# ── Family exclusion ────────────────────────────────────────────────────────


def test_family_exclusion_rejects_claude_judge():
    scored = {"metadata": {"judges": ["claude-opus-4-6", "gpt-5.4"]}}
    with pytest.raises(ValueError, match="family-exclusion"):
        verdict.enforce_non_claude_from_scored(scored)


def test_family_exclusion_accepts_two_non_claude_judges():
    scored = {"metadata": {"judges": ["gpt-5.4", "gemini-3.1-pro"]}}
    out = verdict.enforce_non_claude_from_scored(scored)
    assert out == ["gpt-5.4", "gemini-3.1-pro"]


def test_family_exclusion_rejects_missing_judges():
    scored = {"metadata": {}}
    with pytest.raises(ValueError, match="judges"):
        verdict.enforce_non_claude_from_scored(scored)


def test_dry_run_fixture_passes_family_exclusion():
    scored = verdict._dry_run_scored_fixture()
    out = verdict.enforce_non_claude_from_scored(scored)
    assert all(not j.startswith("claude-") for j in out)


# ── catch_rate (verifier-grounded) per-dim verdict ──────────────────────────


def test_catch_rate_inconclusive_when_accuracy_delta_below_floor():
    # A: 10/15, B: 10/16 — delta ~4pp, below 5pp floor
    scored = _scored(catch_rate_verifier=(10, 5, 1))
    v = verdict.compute_verdict([scored] * 3)
    cr = v["per_dimension_verdicts"]["catch_rate"]
    assert cr["verdict"] == "inconclusive"


def test_catch_rate_regression_blocked_when_winner_hallucinates_more():
    # B has higher accuracy but higher hallucination rate.
    scores = []
    for _ in range(3):
        s = _scored(catch_rate_verifier=(7, 3, 10))  # arm-a
        # Override arm-b's verifier stats to show higher accuracy + higher hall
        s["arms"]["arm-b"]["catch_rate"]["verify_claims"]["stats"] = {
            "verified": 16, "falsified": 4, "unresolvable": 0,
            "claims_checked": 20, "model": "claude-sonnet-4-6", "tool_calls": 0,
        }
        scores.append(s)
    v = verdict.compute_verdict(scores)
    cr = v["per_dimension_verdicts"]["catch_rate"]
    # Accuracy: A 70% B 80% delta +10pp. Hallucination: A 15% B 20% — B regresses 5pp.
    assert cr["verdict"] == "regression-blocked"
    assert cr["primary_winner"] == "arm-b"


def test_catch_rate_directional_at_n3_when_clean_signal():
    scores = []
    for _ in range(3):
        s = _scored(
            catch_rate_verifier=(8, 6, 2),
            catch_rate_quality={
                "arm-a": _qdist(substantive=4, marginal=3, superficial=7, harmful=0),
                "arm-b": _qdist(substantive=6, marginal=5, superficial=2, harmful=0),
            },
        )
        s["arms"]["arm-b"]["catch_rate"]["verify_claims"]["stats"] = {
            "verified": 14, "falsified": 3, "unresolvable": 2,
            "claims_checked": 19, "model": "claude-sonnet-4-6", "tool_calls": 0,
        }
        scores.append(s)
    v = verdict.compute_verdict(scores)
    cr = v["per_dimension_verdicts"]["catch_rate"]
    assert cr["verdict"] == "directional-favor-arm-b"


def test_catch_rate_confident_at_n5():
    scores = []
    for _ in range(5):
        s = _scored(
            catch_rate_verifier=(8, 6, 2),
            catch_rate_quality={
                "arm-a": _qdist(substantive=4, marginal=3, superficial=7, harmful=0),
                "arm-b": _qdist(substantive=6, marginal=5, superficial=2, harmful=0),
            },
        )
        s["arms"]["arm-b"]["catch_rate"]["verify_claims"]["stats"] = {
            "verified": 14, "falsified": 3, "unresolvable": 2,
            "claims_checked": 19, "model": "claude-sonnet-4-6", "tool_calls": 0,
        }
        scores.append(s)
    v = verdict.compute_verdict(scores)
    cr = v["per_dimension_verdicts"]["catch_rate"]
    assert cr["verdict"] == "confident-favor-arm-b"


def test_catch_rate_uses_weighted_accuracy_as_primary():
    """Fix 3 (must-fix per cross-model review): catch_rate primary metric
    is weighted_accuracy, not raw accuracy. When raw accuracy ties across
    arms but quality density differs, weighted_accuracy picks the winner."""
    scores = []
    for _ in range(3):
        s = _scored(
            catch_rate_verifier=(20, 0, 0),  # Arm A: 100% raw accuracy
            catch_rate_quality={
                # A: 100% superficial → quality_density 0
                "arm-a": _qdist(substantive=0, marginal=0, superficial=20, harmful=0),
                # B: 100% substantive → quality_density 1.0
                "arm-b": _qdist(substantive=10, marginal=0, superficial=0, harmful=0),
            },
        )
        s["arms"]["arm-b"]["catch_rate"]["verify_claims"]["stats"] = {
            "verified": 10, "falsified": 0, "unresolvable": 0,
            "claims_checked": 10, "model": "claude-sonnet-4-6", "tool_calls": 0,
        }
        scores.append(s)
    v = verdict.compute_verdict(scores)
    cr = v["per_dimension_verdicts"]["catch_rate"]
    # Raw accuracy ties (both 100%); weighted favors B → verdict favors B.
    assert cr["verdict"] == "directional-favor-arm-b"
    assert cr["primary_basis"] == "weighted_accuracy"


def test_catch_rate_not_yet_measured_when_verifier_missing():
    scored = _scored(catch_rate_verifier=None)
    v = verdict.compute_verdict([scored] * 3)
    cr = v["per_dimension_verdicts"]["catch_rate"]
    assert cr["verdict"] == "not-yet-measured"


# ── Judge-graded per-dim verdict ────────────────────────────────────────────


def test_judge_graded_dim_directional_at_n3():
    """Arm B wins direction_improvement by substantive margin."""
    scores = []
    for _ in range(3):
        s = _scored(
            dim_quality={
                "direction_improvement": {
                    "arm-a": _qdist(substantive=2, marginal=3, superficial=2, harmful=0),
                    "arm-b": _qdist(substantive=6, marginal=4, superficial=1, harmful=0),
                },
            },
        )
        scores.append(s)
    v = verdict.compute_verdict(scores)
    d = v["per_dimension_verdicts"]["direction_improvement"]
    assert d["verdict"] == "directional-favor-arm-b"


def test_judge_graded_dim_inconclusive_when_below_floor():
    """Tight scores — delta below SUBSTANTIVE_DELTA_MIN."""
    scores = []
    for _ in range(3):
        s = _scored(
            dim_quality={
                "direction_improvement": {
                    "arm-a": _qdist(substantive=2, marginal=2),
                    "arm-b": _qdist(substantive=2, marginal=3),
                },
            },
        )
        scores.append(s)
    v = verdict.compute_verdict(scores)
    d = v["per_dimension_verdicts"]["direction_improvement"]
    assert d["verdict"] == "inconclusive"


def test_judge_graded_dim_regression_blocked_on_harmful_items():
    """Arm B wins substantive but has too many harmful items."""
    scores = []
    for _ in range(3):
        s = _scored(
            dim_quality={
                "direction_improvement": {
                    "arm-a": _qdist(substantive=2, marginal=3, harmful=0),
                    "arm-b": _qdist(substantive=6, marginal=4, harmful=3),
                },
            },
        )
        scores.append(s)
    v = verdict.compute_verdict(scores)
    d = v["per_dimension_verdicts"]["direction_improvement"]
    assert d["verdict"] == "regression-blocked"


# ── Not-yet-measured dims ───────────────────────────────────────────────────


def test_not_yet_measured_dims_report_reason():
    """Dim 7 (code_review_quality_delta) is the only remaining not-yet-wired
    dim after Dim 5 (miss_rate) and Dim 6 (plan_quality_delta) are wired
    in items 5 and 6 of the metric-fix plan. Its reason should surface
    concrete words like "deferred" or "non-trivial" so readers know it's
    an active gap, not a missing value."""
    scored = _scored(catch_rate_verifier=(10, 5, 1))
    v = verdict.compute_verdict([scored] * 3)
    for dim in verdict.NOT_YET_MEASURED_DIMS:
        d = v["per_dimension_verdicts"][dim]
        assert d["verdict"] == "not-yet-measured"
        assert d["reason"]
        assert any(
            kw in d["reason"].lower()
            for kw in ("deferred", "pending", "requires", "non-trivial")
        )


# ── Overall composition ────────────────────────────────────────────────────


def test_overall_insufficient_sample_at_n_lt_3():
    scored = _scored(catch_rate_verifier=(18, 2, 0))
    v = verdict.compute_verdict([scored, scored])
    assert v["verdict"] == "insufficient-sample"


def test_overall_inconclusive_when_no_dim_produces_verdict():
    scored = _scored(catch_rate_verifier=(10, 5, 1))  # within noise
    v = verdict.compute_verdict([scored] * 3)
    assert v["verdict"] == "inconclusive"
    assert v["overall"]["a_votes"] == 0
    assert v["overall"]["b_votes"] == 0


def test_overall_mixed_when_dims_split():
    """B wins catch_rate, A wins a judge-graded dim."""
    scores = []
    for _ in range(3):
        s = _scored(
            catch_rate_verifier=(8, 6, 2),
            catch_rate_quality={
                "arm-a": _qdist(substantive=3, marginal=3, superficial=2),
                "arm-b": _qdist(substantive=6, marginal=5, superficial=1),
            },
            dim_quality={
                "direction_improvement": {
                    "arm-a": _qdist(substantive=6, marginal=4),  # A wins
                    "arm-b": _qdist(substantive=2, marginal=2),
                },
            },
        )
        s["arms"]["arm-b"]["catch_rate"]["verify_claims"]["stats"] = {
            "verified": 14, "falsified": 3, "unresolvable": 2,
            "claims_checked": 19, "model": "claude-sonnet-4-6", "tool_calls": 0,
        }
        scores.append(s)
    v = verdict.compute_verdict(scores)
    assert v["verdict"] == "mixed-directional"
    assert v["overall"]["a_votes"] >= 1
    assert v["overall"]["b_votes"] >= 1


def test_overall_directional_when_all_voting_dims_agree():
    """Arm B wins catch_rate AND direction_improvement; others inconclusive."""
    scores = []
    for _ in range(3):
        s = _scored(
            catch_rate_verifier=(8, 6, 2),
            catch_rate_quality={
                "arm-a": _qdist(substantive=3, marginal=3, superficial=2),
                "arm-b": _qdist(substantive=6, marginal=5, superficial=1),
            },
            dim_quality={
                "direction_improvement": {
                    "arm-a": _qdist(substantive=2, marginal=2),
                    "arm-b": _qdist(substantive=6, marginal=4),
                },
            },
        )
        s["arms"]["arm-b"]["catch_rate"]["verify_claims"]["stats"] = {
            "verified": 14, "falsified": 3, "unresolvable": 2,
            "claims_checked": 19, "model": "claude-sonnet-4-6", "tool_calls": 0,
        }
        scores.append(s)
    v = verdict.compute_verdict(scores)
    assert v["verdict"] == "directional-favor-arm-b"
    assert v["overall"]["b_votes"] >= 2
    assert v["overall"]["a_votes"] == 0


# ── Rendering ──────────────────────────────────────────────────────────────


def test_render_markdown_includes_all_seven_dims():
    scores = [_scored(catch_rate_verifier=(10, 5, 1))] * 3
    v = verdict.compute_verdict(scores)
    md = verdict.render_markdown(v, scores)
    for dim in verdict.ALL_REPORTED_DIMS:
        assert dim in md


def test_render_markdown_renders_with_empty_input():
    v = {"verdict": "insufficient-sample", "reason": "test", "n_proposals": 0,
         "per_dimension_verdicts": {}, "decision_thresholds": {},
         "overall": {}}
    md = verdict.render_markdown(v, [])
    assert "insufficient-sample" in md

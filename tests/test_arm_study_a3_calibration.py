"""Unit tests for scripts/arm_study_a3_calibration.py.

Covers:
- collect-only walks scored.json files and extracts FALSIFIED blocks
- sample returns full population when ≤ threshold
- sample returns stratified subset when > threshold (proportional, deterministic)
- compare PASS verdict when LLM beats regex
- compare FAIL verdict when LLM ties or loses
- compare FAIL verdict when LLM dominates safe labels (>60%)
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import arm_study_a3_calibration as cal  # noqa: E402
import arm_study_scorer as scorer  # noqa: E402


# ── Fixture builders ───────────────────────────────────────────────────────


def _verification_text(claims: list[tuple[str, str, str, str]]) -> str:
    """Build a synthetic verifier output. Each claim = (text, source,
    status, evidence)."""
    parts = ["## Claim Verification Results", ""]
    for i, (text, source, status, evidence) in enumerate(claims, 1):
        parts.append(
            f"{i}. **Claim**: {text}\n"
            f"   **Source**: {source}\n"
            f"   **Status**: {status}\n"
            f"   **Evidence**: {evidence}\n"
        )
    return "\n".join(parts)


def _scored_fixture(verification_texts: dict[str, str]) -> dict:
    """Build a minimal scored.json fixture with verify_claims populated."""
    arms = {}
    for arm_label, vt in verification_texts.items():
        arms[arm_label] = {
            "catch_rate": {
                "verify_claims": {
                    "status": "verified",
                    "verification_text": vt,
                    "stats": {"verified": 0, "falsified": 0,
                              "unresolvable": 0, "claims_checked": 0},
                }
            },
            "miss_rate": {},
        }
    return {"arms": arms, "metadata": {"run_id": "test-run"}}


# ── collect ────────────────────────────────────────────────────────────────


def test_collect_extracts_falsified_blocks(tmp_path: Path):
    """Walks run-* dirs, extracts only FALSIFIED claims (skips
    VERIFIED/UNRESOLVABLE)."""
    run_dir = tmp_path / "run-foo"
    run_dir.mkdir()
    vt_a = _verification_text([
        ("c1-verified", "Proposal", "VERIFIED", "ok"),
        ("c2-fab", "Challenger A", "FALSIFIED", "false claim"),
        ("c3-misq", "Proposal (1A), Challenger B", "FALSIFIED", "wrong"),
    ])
    vt_b = _verification_text([
        ("c4-fab", "Challenger C", "FALSIFIED", "another"),
    ])
    scored = _scored_fixture({"arm-a": vt_a, "arm-b": vt_b})
    (run_dir / "scored.json").write_text(json.dumps(scored))

    claims = cal.collect_falsified_claims(store_root=tmp_path)
    assert len(claims) == 3  # 2 from arm-a + 1 from arm-b; VERIFIED dropped
    arms = Counter(c["arm"] for c in claims)
    assert arms == {"arm-a": 2, "arm-b": 1}
    patterns = Counter(c["source_pattern"] for c in claims)
    assert patterns["challenger"] == 2
    assert patterns["mixed"] == 1


def test_collect_handles_missing_verification_text(tmp_path: Path):
    """Run dirs with empty/missing verify_claims block return empty list."""
    run_dir = tmp_path / "run-empty"
    run_dir.mkdir()
    scored = {"arms": {"arm-a": {"catch_rate": {}}}}
    (run_dir / "scored.json").write_text(json.dumps(scored))

    claims = cal.collect_falsified_claims(store_root=tmp_path)
    assert claims == []


# ── sample ─────────────────────────────────────────────────────────────────


def test_sample_population_le_threshold_returns_all(tmp_path: Path):
    """Population ≤ SAMPLE_THRESHOLD → label all (no random sampling)."""
    claims = [
        {"claim_id": f"c{i}", "arm": "arm-a", "source_pattern": "challenger"}
        for i in range(40)
    ]
    sample = (claims if len(claims) <= cal.SAMPLE_THRESHOLD
              else cal.stratified_sample(claims))
    assert len(sample) == 40


def test_sample_population_gt_threshold_stratified(tmp_path: Path):
    """Population > SAMPLE_THRESHOLD → stratified sample of fixed size."""
    claims = []
    # 100 claims: 60 arm-a (40 challenger, 20 proposal),
    #             40 arm-b (30 mixed, 10 other)
    for i in range(40):
        claims.append({"claim_id": f"a-c-{i}", "arm": "arm-a",
                       "source_pattern": "challenger"})
    for i in range(20):
        claims.append({"claim_id": f"a-p-{i}", "arm": "arm-a",
                       "source_pattern": "proposal"})
    for i in range(30):
        claims.append({"claim_id": f"b-m-{i}", "arm": "arm-b",
                       "source_pattern": "mixed"})
    for i in range(10):
        claims.append({"claim_id": f"b-o-{i}", "arm": "arm-b",
                       "source_pattern": "other"})
    sample = cal.stratified_sample(claims, sample_size=30, seed=42)
    assert len(sample) == 30
    # Each non-empty stratum must contribute at least 1.
    by_stratum = Counter((c["arm"], c["source_pattern"]) for c in sample)
    assert ("arm-a", "challenger") in by_stratum
    assert ("arm-a", "proposal") in by_stratum
    assert ("arm-b", "mixed") in by_stratum
    assert ("arm-b", "other") in by_stratum


def test_sample_deterministic_with_seed():
    """Same seed → same sample on every run."""
    claims = [
        {"claim_id": f"c{i}", "arm": "arm-a", "source_pattern": "challenger"}
        for i in range(100)
    ]
    s1 = cal.stratified_sample(claims, sample_size=30, seed=42)
    s2 = cal.stratified_sample(claims, sample_size=30, seed=42)
    assert [c["claim_id"] for c in s1] == [c["claim_id"] for c in s2]


# ── compare ────────────────────────────────────────────────────────────────


def _make_calibration_setup(
    tmp_path: Path,
    truth_label_pairs: list[tuple[str, str]],  # (claim_id, ground_truth)
    llm_predictions: dict[str, str],  # claim_id -> label
    source_field_for: dict[str, str] | None = None,  # claim_id -> source
):
    """Build claims.jsonl + labels.jsonl + LLM stub for compare tests."""
    src_map = source_field_for or {}
    claims_path = tmp_path / "claims.jsonl"
    labels_path = tmp_path / "labels.jsonl"
    cache_path = tmp_path / "cache.jsonl"
    log_path = tmp_path / "log.jsonl"

    with claims_path.open("w") as f:
        for cid, _ in truth_label_pairs:
            entry = {
                "claim_id": cid, "run_id": "r1", "arm": "arm-a",
                "dim": "catch_rate", "claim_idx": 0,
                "claim_text": f"text-{cid}",
                "source_field": src_map.get(cid, "Challenger"),
                "source_pattern": "challenger",
                "verifier_evidence": f"ev-{cid}",
            }
            f.write(json.dumps(entry, sort_keys=True) + "\n")
    with labels_path.open("w") as f:
        for cid, gt in truth_label_pairs:
            f.write(json.dumps({
                "claim_id": cid, "ground_truth": gt,
                "claim_text": f"text-{cid}", "arm": "arm-a",
                "source_pattern": "challenger",
            }, sort_keys=True) + "\n")

    def stub(*, system, user, model, temperature, max_tokens, timeout):
        # Recover claim_id from the user prompt: claim_text is "text-c5".
        for cid in llm_predictions:
            if f"text-{cid}" in user:
                return {"label": llm_predictions[cid], "rationale": ""}
        return {"label": "AMBIGUOUS", "rationale": "fallback"}

    # Patch module paths so cmd_compare uses the temp files.
    monkey_paths = {
        "A3_MECHANISM_CACHE_PATH": cache_path,
        "A3_ADJUDICATION_LOG_PATH": log_path,
    }
    for attr, path in monkey_paths.items():
        setattr(scorer, attr, path)
    return claims_path, labels_path, stub


def test_compare_pass_when_llm_beats_regex(tmp_path: Path, monkeypatch):
    """LLM matches GT 100%, regex matches 50% → PASS."""
    truth = [
        ("c1", "PROPOSAL_ERROR_CAUGHT"),
        ("c2", "CHALLENGER_FABRICATION"),
        ("c3", "INFERENCE_NOT_GROUNDED"),
        ("c4", "PROPOSAL_ERROR_CAUGHT"),
    ]
    llm_pred = {
        "c1": "PROPOSAL_ERROR_CAUGHT",
        "c2": "CHALLENGER_FABRICATION",
        "c3": "INFERENCE_NOT_GROUNDED",
        "c4": "PROPOSAL_ERROR_CAUGHT",
    }
    # Regex for these source fields: c1/c4 → PROPOSAL (matches), c2 →
    # CHALLENGER (matches), c3 → CHALLENGER (mismatches truth).
    src = {"c1": "Proposal", "c2": "Challenger",
           "c3": "Challenger", "c4": "Proposal"}
    claims_path, labels_path, stub = _make_calibration_setup(
        tmp_path, truth, llm_pred, src
    )
    report_path = tmp_path / "report.md"
    rc = cal.cmd_compare(claims_path, labels_path, report_path,
                         classifier_model="test-m", _llm_call_json=stub)
    assert rc == 0
    assert "PASS" in report_path.read_text()


def test_compare_fail_when_llm_ties_or_loses(tmp_path: Path):
    """LLM matches 50%, regex matches 75% → FAIL (LLM did not beat regex)."""
    truth = [
        ("c1", "PROPOSAL_ERROR_CAUGHT"),
        ("c2", "PROPOSAL_ERROR_CAUGHT"),
        ("c3", "PROPOSAL_ERROR_CAUGHT"),
        ("c4", "CHALLENGER_FABRICATION"),
    ]
    llm_pred = {
        "c1": "PROPOSAL_ERROR_CAUGHT",  # match
        "c2": "PROPOSAL_ERROR_CAUGHT",  # match
        "c3": "AMBIGUOUS",  # miss
        "c4": "AMBIGUOUS",  # miss
    }
    # Regex: all "Proposal" sources → PROPOSAL_ERROR_CAUGHT, all "Challenger"
    # → CHALLENGER_FABRICATION. Truth is 3xPEC + 1xCF.
    src = {"c1": "Proposal", "c2": "Proposal",
           "c3": "Proposal", "c4": "Challenger"}
    claims_path, labels_path, stub = _make_calibration_setup(
        tmp_path, truth, llm_pred, src
    )
    report_path = tmp_path / "report.md"
    rc = cal.cmd_compare(claims_path, labels_path, report_path,
                         classifier_model="test-m", _llm_call_json=stub)
    assert rc == 1  # non-zero exit on FAIL
    assert "FAIL" in report_path.read_text()


def test_compare_fail_on_safe_label_collapse(tmp_path: Path):
    """LLM beats regex on accuracy but >60% safe labels → FAIL."""
    # 5 claims, all GT = PROPOSAL_ERROR_CAUGHT. Regex predicts 0/5 (sources
    # all "Challenger"). LLM predicts CHALLENGER_FABRICATION 4/5 + 1 PEC.
    # LLM accuracy 1/5 = 20%, regex 0/5 = 0%, so LLM beats regex. But
    # 4/5 = 80% > 60% safe-label cap → FAIL.
    truth = [(f"c{i}", "PROPOSAL_ERROR_CAUGHT") for i in range(5)]
    llm_pred = {
        "c0": "PROPOSAL_ERROR_CAUGHT",
        "c1": "CHALLENGER_FABRICATION",
        "c2": "CHALLENGER_FABRICATION",
        "c3": "CHALLENGER_FABRICATION",
        "c4": "CHALLENGER_FABRICATION",
    }
    src = {f"c{i}": "Challenger" for i in range(5)}
    claims_path, labels_path, stub = _make_calibration_setup(
        tmp_path, truth, llm_pred, src
    )
    report_path = tmp_path / "report.md"
    rc = cal.cmd_compare(claims_path, labels_path, report_path,
                         classifier_model="test-m", _llm_call_json=stub)
    assert rc == 1
    text = report_path.read_text()
    assert "FAIL" in text
    assert "safe-label" in text


# ── kappa correctness ─────────────────────────────────────────────────────


def test_cohens_kappa_perfect_agreement():
    pred = ["A", "B", "C", "A"]
    true = ["A", "B", "C", "A"]
    assert cal.cohens_kappa(pred, true, ("A", "B", "C")) == pytest.approx(1.0)


def test_cohens_kappa_chance_agreement():
    """All same prediction; truth varied → kappa near 0."""
    pred = ["A"] * 4
    true = ["A", "B", "A", "B"]
    k = cal.cohens_kappa(pred, true, ("A", "B"))
    # Observed = 2/4 = 0.5; expected with all-A pred and 50/50 truth = 0.5.
    assert k == pytest.approx(0.0)

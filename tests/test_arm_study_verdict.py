"""Minimal unit tests for scripts/arm_study_verdict.py (Phase 1 scaffold).

Full decision-logic test suite lands in Phase 3 per the plan. This file
covers the scaffold's one load-bearing behavior (family-exclusion) plus
the stub compute_verdict() contract, so the verification_commands entry
in the plan's frontmatter has something to run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import arm_study_verdict as verdict  # noqa: E402


# ── Family exclusion guard ──────────────────────────────────────────────────


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


# ── Stub compute_verdict contract ───────────────────────────────────────────


def test_compute_verdict_stub_returns_evidence_gathering_only():
    """Phase 1 stub — always returns 'evidence-gathering-only'. When Phase 3
    replaces compute_verdict with the real decision logic, this test must be
    expanded to cover substantive-count weighting + convergence thresholds +
    no-regression check."""
    scored = verdict._dry_run_scored_fixture()
    v = verdict.compute_verdict(scored)
    assert v["verdict"] == "evidence-gathering-only"
    assert "reason" in v


def test_dry_run_fixture_passes_family_exclusion():
    """Sanity: the dry-run fixture must not trip family-exclusion (otherwise
    --dry-run CLI mode fails for the wrong reason)."""
    scored = verdict._dry_run_scored_fixture()
    out = verdict.enforce_non_claude_from_scored(scored)
    assert all(not j.startswith("claude-") for j in out)


# ── Output shape ────────────────────────────────────────────────────────────


def test_render_markdown_contains_verdict_and_run_id():
    scored = verdict._dry_run_scored_fixture()
    v = verdict.compute_verdict(scored)
    md = verdict.render_markdown(v, scored)
    assert "evidence-gathering-only" in md
    assert "dry-run-fixture" in md
    assert "gpt-5.4" in md

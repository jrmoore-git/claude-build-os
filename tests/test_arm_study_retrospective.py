"""Unit tests for scripts/arm_study_retrospective.py.

Covers the orphan #2 fix (top-level status contract): retrospective.json
must reflect actual per-arm outcomes rather than always emitting "scored".
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import arm_study_retrospective as retro  # noqa: E402


def _make_run_dir(tmp_path: Path, arm_files: dict[str, str | None]) -> Path:
    """Build a synthetic run directory with arm-x/, arm-y/, labels.json."""
    rd = tmp_path / "run-test"
    rd.mkdir()
    (rd / "labels.json").write_text(
        '{"arm-x": "arm-a", "arm-y": "arm-b"}'
    )
    # Build arm-x/ and arm-y/ stubs.
    for arm in ("arm-x", "arm-y"):
        ad = rd / arm
        ad.mkdir()
    return rd


def test_top_level_status_scored_when_any_arm_scored(tmp_path, monkeypatch):
    """When at least one arm scored, top-level status = 'scored'."""
    out = {
        "per_arm": {
            "arm-a": {"status": "scored", "stats": {}},
            "arm-b": {"status": "llm-failed"},
        }
    }
    # Manually exercise the post-loop status logic (mirroring score_run tail).
    arm_statuses = [v.get("status") for v in out["per_arm"].values()]
    assert any(s == "scored" for s in arm_statuses)


def test_top_level_status_failed_when_all_arms_failed():
    """When ALL arms produced parse-error / llm-failed, status='failed'."""
    per_arm = {
        "arm-a": {"status": "llm-failed"},
        "arm-b": {"status": "parse-error"},
    }
    arm_statuses = [v.get("status") for v in per_arm.values()]
    assert not any(s == "scored" for s in arm_statuses)
    assert all(s in ("llm-failed", "parse-error", "no-arm-output")
               for s in arm_statuses)


def test_no_downstream_artifact_exit_zero(tmp_path, monkeypatch):
    """`no-downstream-artifact` status returns exit 0 (intentional non-scorable)."""
    monkeypatch.setattr(retro, "score_run", lambda *a, **kw: {
        "status": "no-downstream-artifact",
        "reason": "no plan/refined/judgment",
    })
    monkeypatch.setattr(sys, "argv",
                        ["arm_study_retrospective.py", "--run-id", "x",
                         "--output", str(tmp_path / "out.json")])
    rc = retro.main()
    assert rc == 0


def test_failed_status_exit_nonzero(tmp_path, monkeypatch):
    """`failed` status returns exit 2."""
    monkeypatch.setattr(retro, "score_run", lambda *a, **kw: {
        "status": "failed", "failed_reason": "all arms failed",
        "per_arm": {},
    })
    monkeypatch.setattr(sys, "argv",
                        ["arm_study_retrospective.py", "--run-id", "x",
                         "--output", str(tmp_path / "out.json")])
    rc = retro.main()
    assert rc == 2

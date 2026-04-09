"""Tests for scripts/artifact_check.py — artifact integrity checker."""
import json
import os
import subprocess
import sys

PYTHON = sys.executable
SCRIPT = "scripts/artifact_check.py"
CWD = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True
).stdout.strip() or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_check(scope, base=None):
    """Run artifact_check.py and return parsed JSON."""
    cmd = [PYTHON, SCRIPT, "--scope", scope]
    if base:
        cmd.extend(["--base", base])
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=CWD)
    assert result.returncode == 0, f"exit {result.returncode}: {result.stderr}"
    return json.loads(result.stdout)


# ── Basic output structure ───────────────────────────────────────────────────

def test_output_structure():
    out = run_check("nonexistent-topic")
    assert "scope" in out
    assert "git_head" in out
    assert "artifacts" in out
    assert "open_material_findings" in out
    assert out["scope"] == "nonexistent-topic"


def test_missing_artifacts():
    out = run_check("nonexistent-topic-xyz")
    for name in ("plan", "challenge", "judgment", "review"):
        assert out["artifacts"][name]["exists"] is False


# ── Existing debate artifacts ────────────────────────────────────────────────

def test_existing_debate_artifacts():
    """Check against actual debate artifacts in tasks/ if any exist."""
    tasks_dir = os.path.join(CWD, "tasks")
    if not os.path.isdir(tasks_dir):
        return  # Skip if no tasks dir
    for f in os.listdir(tasks_dir):
        if f.endswith("-challenge.md"):
            scope = f.replace("-challenge.md", "")
            out = run_check(scope)
            challenge = out["artifacts"]["challenge"]
            assert challenge["exists"] is True
            assert "has_material" in challenge
            assert "valid" in challenge
            break


def test_existing_judgment_artifacts():
    """Check against actual judgment artifacts in tasks/ if any exist."""
    tasks_dir = os.path.join(CWD, "tasks")
    if not os.path.isdir(tasks_dir):
        return
    for f in os.listdir(tasks_dir):
        if f.endswith("-judgment.md"):
            scope = f.replace("-judgment.md", "")
            out = run_check(scope)
            judgment = out["artifacts"]["judgment"]
            assert judgment["exists"] is True
            assert "accepted" in judgment
            assert "dismissed" in judgment
            break


# ── Open material findings ───────────────────────────────────────────────────

def test_no_judgment_returns_none_findings():
    out = run_check("nonexistent-topic-xyz")
    assert out["open_material_findings"] is None

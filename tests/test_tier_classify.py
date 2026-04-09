"""Tests for scripts/tier_classify.py — deterministic tier classification."""
import json
import os
import subprocess
import sys

PYTHON = sys.executable
SCRIPT = "scripts/tier_classify.py"
CWD = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True
).stdout.strip() or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_classify(*files):
    """Run tier_classify.py with given files, return parsed JSON output."""
    result = subprocess.run(
        [PYTHON, SCRIPT, *files],
        capture_output=True, text=True,
        cwd=CWD,
    )
    assert result.returncode == 0, f"exit {result.returncode}: {result.stderr}"
    return json.loads(result.stdout)


def run_classify_stdin(files_text):
    """Run tier_classify.py with --stdin, return parsed JSON output."""
    result = subprocess.run(
        [PYTHON, SCRIPT, "--stdin"],
        input=files_text,
        capture_output=True, text=True,
        cwd=CWD,
    )
    assert result.returncode == 0, f"exit {result.returncode}: {result.stderr}"
    return json.loads(result.stdout)


# ── Tier 1 files ─────────────────────────────────────────────────────────────

def test_prd_is_tier1():
    out = run_classify("docs/PROJECT-PRD-v1.0.md")
    assert out["tier"] == 1
    assert "PRD" in out["reason"]


def test_project_prd_is_tier1():
    out = run_classify("docs/project-prd.md")
    assert out["tier"] == 1


def test_schema_sql_is_tier1():
    out = run_classify("schema_v2.sql")
    assert out["tier"] == 1
    assert "schema" in out["reason"]


def test_migration_sql_is_tier1():
    out = run_classify("migrations/001_add_col.sql")
    assert out["tier"] == 1


def test_security_rules_is_tier1():
    out = run_classify(".claude/rules/security.md")
    assert out["tier"] == 1


def test_db_file_is_tier1():
    out = run_classify("stores/app.db")
    assert out["tier"] == 1


# ── Tier 1.5 files ───────────────────────────────────────────────────────────

def test_toolbelt_script_is_tier15():
    out = run_classify("scripts/briefing_tool.py")
    assert out["tier"] == 1.5
    assert "toolbelt" in out["reason"]


def test_debate_py_is_tier15():
    out = run_classify("scripts/debate.py")
    assert out["tier"] == 1.5


def test_hook_script_is_tier15():
    out = run_classify("scripts/hook-review-gate.sh")
    assert out["tier"] == 1.5


# ── Exempt files ─────────────────────────────────────────────────────────────

def test_tasks_is_exempt():
    out = run_classify("tasks/handoff.md")
    assert out["tier"] == "exempt"


def test_docs_non_prd_is_exempt():
    out = run_classify("docs/current-state.md")
    assert out["tier"] == "exempt"


def test_tests_is_exempt():
    out = run_classify("tests/test_foo.py")
    assert out["tier"] == "exempt"


def test_config_is_exempt():
    out = run_classify("config/settings.json")
    assert out["tier"] == "exempt"


def test_stores_non_db_is_exempt():
    out = run_classify("stores/debate-log.jsonl")
    assert out["tier"] == "exempt"


# ── Tier 2 files ─────────────────────────────────────────────────────────────

def test_claude_rules_non_security_is_tier2():
    out = run_classify(".claude/rules/code-quality.md")
    assert out["tier"] == 2


def test_random_script_is_tier2():
    out = run_classify("scripts/deploy_all.sh")
    assert out["tier"] == 2


def test_non_core_skill_is_tier2():
    out = run_classify("skills/status/SKILL.md")
    assert out["tier"] == 2


# ── Fail-upward rule ─────────────────────────────────────────────────────────

def test_mixed_fails_upward():
    out = run_classify("stores/app.db", "tasks/foo.md")
    assert out["tier"] == 1
    assert out["ambiguous"] is False


def test_mixed_tiers_is_ambiguous():
    out = run_classify("stores/app.db", ".claude/rules/code-quality.md")
    assert out["tier"] == 1
    assert out["ambiguous"] is True


def test_mixed_tier15_and_tier2():
    out = run_classify("scripts/briefing_tool.py", ".claude/rules/code-quality.md")
    assert out["tier"] == 1.5


# ── Stdin mode ───────────────────────────────────────────────────────────────

def test_stdin_mode():
    out = run_classify_stdin("stores/app.db\ntasks/handoff.md\n")
    assert out["tier"] == 1


# ── Edge cases ───────────────────────────────────────────────────────────────

def test_no_files_exits_1():
    result = subprocess.run(
        [PYTHON, SCRIPT],
        capture_output=True, text=True,
        cwd=CWD,
    )
    assert result.returncode == 1


def test_all_exempt_overall_exempt():
    out = run_classify("tasks/foo.md", "tasks/bar.md")
    assert out["tier"] == "exempt"

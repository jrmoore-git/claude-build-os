"""Tests for scripts/read_tier.py"""
import subprocess
import tempfile
import os

PYTHON = "/opt/homebrew/bin/python3.11"
SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "read_tier.py")


def _run_tier(claude_md_content, args=None):
    """Create a temp dir with CLAUDE.md, run read_tier.py against it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_md = os.path.join(tmpdir, "CLAUDE.md")
        with open(claude_md, "w") as f:
            f.write(claude_md_content)

        cmd = [PYTHON, SCRIPT]
        if args:
            cmd.extend(args)

        result = subprocess.run(
            cmd,
            capture_output=True, text=True,
            env={**os.environ, "PLAN_GATE_PROJECT": tmpdir},
        )
        return result


def test_tier_0():
    result = _run_tier("<!-- buildos-tier: 0 -->\n# CLAUDE.md\n")
    assert result.stdout.strip() == "0"


def test_tier_1():
    result = _run_tier("<!-- buildos-tier: 1 -->\n# CLAUDE.md\n")
    assert result.stdout.strip() == "1"


def test_tier_2():
    result = _run_tier("<!-- buildos-tier: 2 -->\n# CLAUDE.md\n")
    assert result.stdout.strip() == "2"


def test_tier_3():
    result = _run_tier("<!-- buildos-tier: 3 -->\n# CLAUDE.md\n")
    assert result.stdout.strip() == "3"


def test_no_declaration_defaults_to_3():
    result = _run_tier("# CLAUDE.md\n\nNo tier here.\n")
    assert result.stdout.strip() == "3"


def test_missing_file_defaults_to_3():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [PYTHON, SCRIPT],
            capture_output=True, text=True,
            env={**os.environ, "PLAN_GATE_PROJECT": tmpdir},
        )
        assert result.stdout.strip() == "3"


def test_check_flag_passes():
    result = _run_tier("<!-- buildos-tier: 2 -->\n# CLAUDE.md\n", ["--check", "2"])
    assert result.returncode == 0


def test_check_flag_fails():
    result = _run_tier("<!-- buildos-tier: 1 -->\n# CLAUDE.md\n", ["--check", "2"])
    assert result.returncode == 1


def test_tier_not_on_first_line():
    """Tier declaration within first 5 lines should still be found."""
    content = "# CLAUDE.md\n\n<!-- buildos-tier: 1 -->\n\nSome content.\n"
    result = _run_tier(content)
    assert result.stdout.strip() == "1"


def test_tier_after_line_5_not_found():
    """Tier declaration after line 5 should not be found (defaults to 3)."""
    content = "line1\nline2\nline3\nline4\nline5\nline6\n<!-- buildos-tier: 0 -->\n"
    result = _run_tier(content)
    assert result.stdout.strip() == "3"

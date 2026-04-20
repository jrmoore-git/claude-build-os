"""Tests for hooks/hook-context-inject.py"""

import json
import os
import subprocess
import tempfile
import uuid

import pytest

HOOK_PATH = os.path.join(
    os.path.dirname(__file__), "..", "hooks", "hook-context-inject.py"
)


def run_hook(tool_input, env_override=None):
    """Run the hook with given tool_input, return (stdout, exit_code).

    Each call gets a unique CLAUDE_SESSION_ID so the hook's session-level dedup
    cache (/tmp/claude-context-inject-<sid>.json) doesn't swallow output for the
    second+ test that targets the same file under one pytest process.
    """
    env = os.environ.copy()
    env["CLAUDE_SESSION_ID"] = f"pytest-{uuid.uuid4()}"
    if env_override:
        env.update(env_override)
    input_json = json.dumps({"tool_input": tool_input})
    result = subprocess.run(
        ["/opt/homebrew/bin/python3.11", HOOK_PATH],
        input=input_json,
        capture_output=True,
        text=True,
        timeout=5,
        env=env,
    )
    return result.stdout.strip(), result.returncode


def parse_output(stdout):
    """Parse hook JSON output, return the hookSpecificOutput dict."""
    if not stdout:
        return None
    data = json.loads(stdout)
    return data.get("hookSpecificOutput", {})


# --- Skip conditions ---


class TestSkipConditions:
    def test_empty_file_path(self):
        stdout, rc = run_hook({"file_path": ""})
        assert rc == 0
        assert stdout == ""

    def test_missing_file_path(self):
        stdout, rc = run_hook({})
        assert rc == 0
        assert stdout == ""

    def test_non_python_file(self):
        stdout, rc = run_hook({"file_path": "/tmp/test.md"})
        assert rc == 0
        assert stdout == ""

    def test_nonexistent_file(self):
        stdout, rc = run_hook({"file_path": "/tmp/nonexistent_xyz_test.py"})
        assert rc == 0
        assert stdout == ""

    def test_shell_script(self):
        stdout, rc = run_hook({"file_path": "/tmp/test.sh"})
        assert rc == 0
        assert stdout == ""

    def test_javascript_file(self):
        stdout, rc = run_hook({"file_path": "/tmp/test.js"})
        assert rc == 0
        assert stdout == ""

    def test_invalid_json_input(self):
        """Hook should exit cleanly on malformed input."""
        result = subprocess.run(
            ["/opt/homebrew/bin/python3.11", HOOK_PATH],
            input="not json",
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""


# --- Output format ---


class TestOutputFormat:
    def test_always_allows(self):
        """Hook must never block — always permissionDecision: allow."""
        # Use a real Python file from the project
        project_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True
        ).stdout.strip()
        target = os.path.join(project_root, "scripts", "tier_classify.py")
        if not os.path.isfile(target):
            pytest.skip("tier_classify.py not found")

        stdout, rc = run_hook({"file_path": target})
        assert rc == 0
        if stdout:
            output = parse_output(stdout)
            assert output["permissionDecision"] == "allow"

    def test_has_additional_context(self):
        """Output must include additionalContext when context is found."""
        project_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True
        ).stdout.strip()
        target = os.path.join(project_root, "scripts", "tier_classify.py")
        if not os.path.isfile(target):
            pytest.skip("tier_classify.py not found")

        stdout, rc = run_hook({"file_path": target})
        assert stdout, "Expected context output for tier_classify.py"
        output = parse_output(stdout)
        assert "additionalContext" in output
        assert "Context for" in output["additionalContext"]

    def test_context_cap(self):
        """Context must not exceed MAX_CONTEXT_CHARS."""
        project_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True
        ).stdout.strip()
        target = os.path.join(project_root, "scripts", "debate.py")
        if not os.path.isfile(target):
            pytest.skip("debate.py not found")

        stdout, rc = run_hook({"file_path": target})
        if stdout:
            output = parse_output(stdout)
            ctx = output.get("additionalContext", "")
            assert len(ctx) <= 3000


# --- Test file discovery ---


class TestTestFileDiscovery:
    def test_finds_test_file(self):
        """Should find tests/test_tier_classify.py for scripts/tier_classify.py."""
        project_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True
        ).stdout.strip()
        target = os.path.join(project_root, "scripts", "tier_classify.py")
        if not os.path.isfile(target):
            pytest.skip("tier_classify.py not found")

        stdout, _ = run_hook({"file_path": target})
        assert stdout
        output = parse_output(stdout)
        ctx = output["additionalContext"]
        assert "Test file" in ctx
        assert "test_tier_classify.py" in ctx

    def test_shows_test_function_names(self):
        """Should list test function names from the test file."""
        project_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True
        ).stdout.strip()
        target = os.path.join(project_root, "scripts", "tier_classify.py")
        if not os.path.isfile(target):
            pytest.skip("tier_classify.py not found")

        stdout, _ = run_hook({"file_path": target})
        output = parse_output(stdout)
        ctx = output["additionalContext"]
        assert "def test_" in ctx


# --- Import signature extraction ---


class TestImportSignatures:
    def test_resolves_local_imports(self):
        """Should resolve local imports and show their signatures."""
        project_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True
        ).stdout.strip()
        target = os.path.join(project_root, "scripts", "debate.py")
        if not os.path.isfile(target):
            pytest.skip("debate.py not found")

        stdout, _ = run_hook({"file_path": target})
        assert stdout
        output = parse_output(stdout)
        ctx = output["additionalContext"]
        assert "Local import signatures" in ctx
        assert "llm_client.py" in ctx

    def test_skips_stdlib_imports(self):
        """Should not try to resolve stdlib imports like json, os, sys."""
        project_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True
        ).stdout.strip()
        target = os.path.join(project_root, "scripts", "debate.py")
        if not os.path.isfile(target):
            pytest.skip("debate.py not found")

        stdout, _ = run_hook({"file_path": target})
        if stdout:
            output = parse_output(stdout)
            ctx = output.get("additionalContext", "")
            # stdlib modules should not appear as resolved local imports
            assert "json.py:" not in ctx
            assert "os.py:" not in ctx


# --- Git history ---


class TestGitHistory:
    def test_shows_recent_commits(self):
        """Should show recent git log entries for the file."""
        project_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True
        ).stdout.strip()
        target = os.path.join(project_root, "scripts", "debate.py")
        if not os.path.isfile(target):
            pytest.skip("debate.py not found")

        git_log = subprocess.run(
            ["git", "log", "--oneline", "-1", "--", target],
            capture_output=True, text=True
        )
        if not git_log.stdout.strip():
            pytest.skip("debate.py has no git history in this repo (symlinked consumer project)")

        stdout, _ = run_hook({"file_path": target})
        assert stdout
        output = parse_output(stdout)
        ctx = output["additionalContext"]
        assert "Recent changes:" in ctx


# --- Performance ---


class TestPerformance:
    def test_completes_within_timeout(self):
        """Hook must complete well within the 2-second timeout."""
        import time

        project_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True
        ).stdout.strip()
        target = os.path.join(project_root, "scripts", "debate.py")
        if not os.path.isfile(target):
            pytest.skip("debate.py not found")

        start = time.time()
        run_hook({"file_path": target})
        elapsed = time.time() - start
        assert elapsed < 2.0, f"Hook took {elapsed:.2f}s, must be < 2s"


# --- Isolated file tests (no project dependency) ---


class TestIsolatedFiles:
    def test_python_file_with_no_context(self):
        """A Python file with no tests, no local imports, no git = silent exit."""
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("x = 1\n")
            f.flush()
            try:
                stdout, rc = run_hook({"file_path": f.name})
                assert rc == 0
                # May or may not have output depending on git context
                # But should not crash
            finally:
                os.unlink(f.name)

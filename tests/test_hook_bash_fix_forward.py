"""Tests for hooks/hook-bash-fix-forward.py — bandaid pattern detection."""
import json
import os
import sys

import pytest

# Add hooks/ to sys.path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))

# Import with hyphens in filename
import importlib

hook_module = importlib.import_module("hook-bash-fix-forward")
check_command = hook_module.check_command

TRACKER_PATH_ATTR = None  # We'll monkeypatch the tracker file path for pattern 5


# ── Pattern 1: rm .git/index.lock ───────────────────────────────────────────


class TestRmGitIndexLock:
    def test_bare_rm(self):
        result = check_command("rm .git/index.lock")
        assert result is not None
        assert "fix-forward" in result
        assert "git locks" in result.lower() or "index.lock" in result.lower() or "git" in result.lower()

    def test_rm_force(self):
        result = check_command("rm -f .git/index.lock")
        assert result is not None
        assert "fix-forward" in result

    def test_rm_rf_absolute_path(self):
        result = check_command("rm -rf /some/path/.git/index.lock")
        assert result is not None
        assert "fix-forward" in result

    def test_rm_other_file_allowed(self):
        assert check_command("rm somefile.txt") is None

    def test_git_status_allowed(self):
        assert check_command("git status") is None

    def test_echo_index_lock_allowed(self):
        """echo mentions the file but doesn't rm it — should be allowed."""
        assert check_command("echo .git/index.lock") is None

    def test_lsof_index_lock_allowed(self):
        """lsof is the investigation step — should be allowed."""
        assert check_command("lsof .git/index.lock") is None


# ── Pattern 2: kill -9 / kill -KILL / kill -SIGKILL ─────────────────────────


class TestKillForce:
    def test_kill_dash_9(self):
        result = check_command("kill -9 1234")
        assert result is not None
        assert "fix-forward" in result
        assert "force-kill" in result.lower() or "kill" in result.lower()

    def test_kill_KILL(self):
        result = check_command("kill -KILL 1234")
        assert result is not None
        assert "fix-forward" in result

    def test_kill_SIGKILL(self):
        result = check_command("kill -SIGKILL 1234")
        assert result is not None
        assert "fix-forward" in result

    def test_graceful_kill_allowed(self):
        """Plain kill (no signal) is graceful — allowed."""
        assert check_command("kill 1234") is None

    def test_kill_15_allowed(self):
        """SIGTERM (15) is graceful — allowed."""
        assert check_command("kill -15 1234") is None

    def test_kill_HUP_allowed(self):
        """SIGHUP is not force-kill — allowed."""
        assert check_command("kill -HUP 1234") is None


# ── Pattern 3: pkill ────────────────────────────────────────────────────────


class TestPkill:
    def test_pkill_simple(self):
        result = check_command("pkill nginx")
        assert result is not None
        assert "fix-forward" in result
        assert "pkill" in result.lower()

    def test_pkill_with_flags(self):
        result = check_command("pkill -f 'some pattern'")
        assert result is not None
        assert "fix-forward" in result

    def test_pgrep_allowed(self):
        """pgrep is the investigation step — should be allowed."""
        assert check_command("pgrep nginx") is None

    def test_pgrep_with_flag_allowed(self):
        assert check_command("pgrep -a nginx") is None


# ── Pattern 4: rm *.lock / rm *.pid ─────────────────────────────────────────


class TestRmGlobLockPid:
    def test_rm_star_lock(self):
        result = check_command("rm *.lock")
        assert result is not None
        assert "fix-forward" in result
        assert "lock" in result.lower() or "pid" in result.lower()

    def test_rm_force_path_star_pid(self):
        result = check_command("rm -f /tmp/*.pid")
        assert result is not None
        assert "fix-forward" in result

    def test_rm_both_globs(self):
        """First match fires — should still block."""
        result = check_command("rm *.lock *.pid")
        assert result is not None

    def test_rm_normal_file_allowed(self):
        assert check_command("rm myfile.txt") is None

    def test_ls_star_lock_allowed(self):
        """ls is not rm — should be allowed."""
        assert check_command("ls *.lock") is None

    def test_rm_specific_lock_file_allowed(self):
        """rm of a specific named .lock file (no glob) — not matched by pattern 4."""
        # Pattern 4 requires a glob (*), so a specific file like "foo.lock" won't match
        assert check_command("rm foo.lock") is None


# ── Pattern 5: Serial debate.py review --persona (D13) ─────────────────────


class TestSerialDebateReview:
    """Test D13 serial review detection using a temp tracker file."""

    @pytest.fixture(autouse=True)
    def _patch_tracker(self, tmp_path, monkeypatch):
        """Redirect the tracker file to a temp directory."""
        self.tracker_path = str(tmp_path / "debate-review-serial-tracker.json")
        # The tracker path is hardcoded in check_command as a local variable.
        # We need to monkeypatch it at the module level. The code reads:
        #   tracker = "/tmp/debate-review-serial-tracker.json"
        # We'll patch via a wrapper that replaces the path in the source.
        # Simpler: just monkeypatch os.path.exists and open for that specific path.

        # Actually, the cleanest approach: patch the function's behavior by
        # rewriting the tracker constant. The code uses a local string, so we
        # need to do something creative. Let's just write a helper that
        # manipulates the temp tracker directly and monkeypatch the path.

        original_open = open
        original_exists = os.path.exists
        hardcoded = "/tmp/debate-review-serial-tracker.json"

        def patched_open(path, *args, **kwargs):
            if path == hardcoded:
                return original_open(self.tracker_path, *args, **kwargs)
            return original_open(path, *args, **kwargs)

        def patched_exists(path):
            if path == hardcoded:
                return original_exists(self.tracker_path)
            return original_exists(path)

        monkeypatch.setattr("builtins.open", patched_open)
        monkeypatch.setattr("os.path.exists", patched_exists)

    def test_first_call_allowed(self):
        """First debate.py review --persona call is allowed (count=1)."""
        cmd = "python3.11 scripts/debate.py review --persona pm --prompt 'Review' --input tasks/foo.md"
        result = check_command(cmd)
        assert result is None

    def test_second_call_blocked(self):
        """Second call with same --input triggers D13 warning."""
        cmd = "python3.11 scripts/debate.py review --persona pm --prompt 'Review' --input tasks/foo.md"
        # First call — allowed
        result1 = check_command(cmd)
        assert result1 is None
        # Second call — blocked
        result2 = check_command(cmd)
        assert result2 is not None
        assert "D13" in result2
        assert "2x" in result2
        assert "tasks/foo.md" in result2

    def test_third_call_shows_count_3(self):
        """Third call shows count=3."""
        cmd = "python3.11 scripts/debate.py review --persona pm --prompt 'Review' --input tasks/foo.md"
        check_command(cmd)  # 1
        check_command(cmd)  # 2
        result = check_command(cmd)  # 3
        assert result is not None
        assert "3x" in result

    def test_different_input_separate_counter(self):
        """Different --input files have independent counters."""
        cmd_a = "python3.11 scripts/debate.py review --persona pm --prompt 'Review' --input tasks/foo.md"
        cmd_b = "python3.11 scripts/debate.py review --persona pm --prompt 'Review' --input tasks/bar.md"
        # First call each — both allowed
        assert check_command(cmd_a) is None
        assert check_command(cmd_b) is None
        # Second call on foo — blocked
        result = check_command(cmd_a)
        assert result is not None
        assert "D13" in result
        assert "tasks/foo.md" in result
        # bar is still at count=1 — second call now triggers
        result_b = check_command(cmd_b)
        assert result_b is not None
        assert "tasks/bar.md" in result_b

    def test_no_input_flag_uses_unknown(self):
        """When --input is missing, tracker key is 'unknown'."""
        cmd = "python3.11 scripts/debate.py review --persona pm --prompt 'Review'"
        assert check_command(cmd) is None  # count=1
        result = check_command(cmd)  # count=2
        assert result is not None
        assert "unknown" in result

    def test_review_with_personas_plural_not_matched(self):
        """--personas (plural) is the correct form — should NOT trigger D13."""
        cmd = "python3.11 scripts/debate.py review --personas pm,security --prompt 'Review' --input tasks/foo.md"
        assert check_command(cmd) is None
        assert check_command(cmd) is None  # Even second call — no D13

    def test_review_with_models_not_matched(self):
        """--models flag should NOT trigger D13."""
        cmd = "python3.11 scripts/debate.py review --models claude-opus-4-7 --prompt 'Review' --input tasks/foo.md"
        assert check_command(cmd) is None
        assert check_command(cmd) is None


# ── Edge cases ──────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_string(self):
        assert check_command("") is None

    def test_no_match(self):
        assert check_command("ls -la /tmp") is None

    def test_harmless_git_command(self):
        assert check_command("git log --oneline -10") is None

    def test_npm_install(self):
        assert check_command("npm install express") is None

    def test_pattern_priority_rm_index_lock_before_glob(self):
        """rm .git/index.lock should match pattern 1, not pattern 4."""
        result = check_command("rm .git/index.lock")
        assert result is not None
        # Pattern 1 message mentions "git locks" / "lsof .git/index.lock"
        assert "lsof .git/index.lock" in result


# ── main() integration ──────────────────────────────────────────────────────


class TestMain:
    def test_main_with_blocked_command(self, capsys, monkeypatch):
        """main() should print ask decision for blocked commands."""
        payload = json.dumps({
            "tool_input": {"command": "kill -9 1234"}
        })
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(payload))
        hook_module.main()
        output = json.loads(capsys.readouterr().out)
        assert output["permissionDecision"] == "ask"
        assert "fix-forward" in output["message"]

    def test_main_with_allowed_command(self, capsys, monkeypatch):
        """main() should print {} for allowed commands."""
        payload = json.dumps({
            "tool_input": {"command": "git status"}
        })
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(payload))
        hook_module.main()
        output = json.loads(capsys.readouterr().out)
        assert output == {}

    def test_main_with_empty_command(self, capsys, monkeypatch):
        """main() should print {} when command is empty."""
        payload = json.dumps({
            "tool_input": {"command": ""}
        })
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(payload))
        hook_module.main()
        output = json.loads(capsys.readouterr().out)
        assert output == {}

    def test_main_with_invalid_json(self, capsys, monkeypatch):
        """main() should print {} for malformed input."""
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO("not json"))
        hook_module.main()
        output = json.loads(capsys.readouterr().out)
        assert output == {}

    def test_main_with_missing_tool_input(self, capsys, monkeypatch):
        """main() should print {} when tool_input is missing."""
        payload = json.dumps({"something_else": True})
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(payload))
        hook_module.main()
        output = json.loads(capsys.readouterr().out)
        assert output == {}

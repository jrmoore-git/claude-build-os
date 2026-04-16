"""Tests for hooks/hook-read-before-edit.py.

Tests both phases:
  Phase 1 (PostToolUse Read): Records which files have been Read.
  Phase 2 (PreToolUse Write|Edit): Warns if editing a protected file not yet Read.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the hook module directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))
import importlib
hook_mod = importlib.import_module("hook-read-before-edit")


# ── Helpers ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def isolated_tracker(tmp_path, monkeypatch):
    """Each test gets a unique tracker file via a unique session ID."""
    session_id = f"test-{id(tmp_path)}"
    monkeypatch.setenv("CLAUDE_SESSION_ID", session_id)
    tracker = tmp_path / f"buildos-read-tracker-{session_id}.txt"
    # Patch get_tracker_path to use tmp_path
    monkeypatch.setattr(hook_mod, "get_tracker_path", lambda: tracker)
    # Reset global PROJECT_ROOT so tests don't leak state
    monkeypatch.setattr(hook_mod, "PROJECT_ROOT", None)
    yield tracker


@pytest.fixture
def project_root(tmp_path, monkeypatch):
    """Set up a fake project root with protected-paths.json."""
    root = tmp_path / "project"
    root.mkdir()
    config_dir = root / "config"
    config_dir.mkdir()
    config = {
        "protected_globs": ["scripts/*.py", "hooks/hook-*", ".claude/rules/*.md"]
    }
    (config_dir / "protected-paths.json").write_text(json.dumps(config))
    monkeypatch.setattr(hook_mod, "get_project_root", lambda: str(root))
    monkeypatch.setattr(hook_mod, "PROJECT_ROOT", str(root))
    return root


# ── get_session_id ───────────────────────────────────────────────────────────


class TestGetSessionId:
    def test_uses_env_var_when_set(self, monkeypatch):
        monkeypatch.setenv("CLAUDE_SESSION_ID", "my-session-123")
        assert hook_mod.get_session_id() == "my-session-123"

    def test_falls_back_to_ppid(self, monkeypatch):
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        result = hook_mod.get_session_id()
        assert result == str(os.getppid())

    def test_sanitizes_dangerous_chars(self, monkeypatch):
        monkeypatch.setenv("CLAUDE_SESSION_ID", "../../etc/passwd")
        result = hook_mod.get_session_id()
        # Path separators removed — no traversal possible
        assert "/" not in result
        assert os.sep not in result


# ── canonicalize ─────────────────────────────────────────────────────────────


class TestCanonicalize:
    def test_resolves_absolute_path(self, tmp_path):
        f = tmp_path / "test.py"
        f.touch()
        result = hook_mod.canonicalize(str(f))
        assert result == str(f.resolve())

    def test_resolves_relative_path(self):
        result = hook_mod.canonicalize("./some/relative/path.py")
        assert os.path.isabs(result)

    def test_handles_symlinks(self, tmp_path):
        real = tmp_path / "real.py"
        real.touch()
        link = tmp_path / "link.py"
        link.symlink_to(real)
        assert hook_mod.canonicalize(str(link)) == hook_mod.canonicalize(str(real))


# ── is_exempt ────────────────────────────────────────────────────────────────


class TestIsExempt:
    def test_tasks_exempt(self):
        assert hook_mod.is_exempt("tasks/my-plan.md") is True

    def test_docs_exempt(self):
        assert hook_mod.is_exempt("docs/current-state.md") is True

    def test_tests_exempt(self):
        assert hook_mod.is_exempt("tests/test_something.py") is True

    def test_config_exempt(self):
        assert hook_mod.is_exempt("config/debate-models.json") is True

    def test_stores_exempt(self):
        assert hook_mod.is_exempt("stores/debate-log.jsonl") is True

    def test_claude_plans_exempt(self):
        assert hook_mod.is_exempt(".claude/plans/my-plan.md") is True

    def test_claude_projects_exempt(self):
        assert hook_mod.is_exempt(".claude/projects/foo/bar.md") is True

    def test_scripts_not_exempt(self):
        assert hook_mod.is_exempt("scripts/debate.py") is False

    def test_hooks_not_exempt(self):
        assert hook_mod.is_exempt("hooks/hook-something.py") is False

    def test_root_file_not_exempt(self):
        assert hook_mod.is_exempt("CLAUDE.md") is False


# ── is_protected ─────────────────────────────────────────────────────────────


class TestIsProtected:
    def test_protected_script(self, project_root):
        assert hook_mod.is_protected("scripts/debate.py") is True

    def test_protected_hook(self, project_root):
        assert hook_mod.is_protected("hooks/hook-something.py") is True

    def test_protected_rule(self, project_root):
        assert hook_mod.is_protected(".claude/rules/workflow.md") is True

    def test_unprotected_file(self, project_root):
        assert hook_mod.is_protected("README.md") is False

    def test_missing_config_returns_false(self, monkeypatch):
        monkeypatch.setattr(hook_mod, "get_project_root", lambda: "/nonexistent")
        monkeypatch.setattr(hook_mod, "PROJECT_ROOT", "/nonexistent")
        assert hook_mod.is_protected("scripts/debate.py") is False


# ── record_read / was_read ───────────────────────────────────────────────────


class TestReadTracking:
    def test_record_and_check(self, tmp_path, isolated_tracker):
        f = tmp_path / "myfile.py"
        f.touch()
        assert hook_mod.was_read(str(f)) is False
        hook_mod.record_read(str(f))
        assert hook_mod.was_read(str(f)) is True

    def test_multiple_files_tracked(self, tmp_path, isolated_tracker):
        f1 = tmp_path / "a.py"
        f2 = tmp_path / "b.py"
        f1.touch()
        f2.touch()
        hook_mod.record_read(str(f1))
        assert hook_mod.was_read(str(f1)) is True
        assert hook_mod.was_read(str(f2)) is False
        hook_mod.record_read(str(f2))
        assert hook_mod.was_read(str(f2)) is True

    def test_unread_file_returns_false(self, tmp_path, isolated_tracker):
        f = tmp_path / "never_read.py"
        f.touch()
        assert hook_mod.was_read(str(f)) is False

    def test_tracker_not_exists_returns_false(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            hook_mod, "get_tracker_path",
            lambda: tmp_path / "nonexistent-tracker.txt"
        )
        assert hook_mod.was_read("/some/file.py") is False

    def test_canonicalization_matches(self, tmp_path, isolated_tracker):
        """Record via one path form, check via another — should match."""
        real = tmp_path / "real.py"
        real.touch()
        link = tmp_path / "link.py"
        link.symlink_to(real)
        hook_mod.record_read(str(link))
        assert hook_mod.was_read(str(real)) is True

    def test_append_only_no_data_loss(self, tmp_path, isolated_tracker):
        """Multiple records don't overwrite each other."""
        files = [tmp_path / f"f{i}.py" for i in range(5)]
        for f in files:
            f.touch()
            hook_mod.record_read(str(f))
        for f in files:
            assert hook_mod.was_read(str(f)) is True


# ── handle_post_read ─────────────────────────────────────────────────────────


class TestHandlePostRead:
    def test_records_file_from_tool_input(self, tmp_path, monkeypatch, isolated_tracker):
        f = tmp_path / "target.py"
        f.touch()
        tool_input = json.dumps({"file_path": str(f)})
        monkeypatch.setenv("TOOL_INPUT", tool_input)
        monkeypatch.setenv("HOOK_EVENT", "PostToolUse")
        hook_mod.handle_post_read()
        assert hook_mod.was_read(str(f)) is True

    def test_empty_tool_input_is_noop(self, monkeypatch, isolated_tracker):
        monkeypatch.setenv("TOOL_INPUT", "")
        hook_mod.handle_post_read()
        # No crash, tracker not created
        assert not isolated_tracker.exists()

    def test_invalid_json_is_noop(self, monkeypatch, isolated_tracker):
        monkeypatch.setenv("TOOL_INPUT", "not json")
        hook_mod.handle_post_read()
        assert not isolated_tracker.exists()

    def test_missing_file_path_is_noop(self, monkeypatch, isolated_tracker):
        monkeypatch.setenv("TOOL_INPUT", json.dumps({"other": "data"}))
        hook_mod.handle_post_read()
        assert not isolated_tracker.exists()


# ── handle_pre_edit ──────────────────────────────────────────────────────────


class TestHandlePreEdit:
    def _run_pre_edit(self, stdin_data, monkeypatch, capsys):
        """Helper: run handle_pre_edit with given stdin JSON."""
        monkeypatch.setenv("HOOK_EVENT", "PreToolUse")
        import io
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(stdin_data)))
        hook_mod.handle_pre_edit()
        return json.loads(capsys.readouterr().out)

    def test_warns_on_protected_unread_file(self, tmp_path, project_root,
                                            monkeypatch, capsys, isolated_tracker):
        # Create a protected file inside project root
        scripts_dir = project_root / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        target = scripts_dir / "debate.py"
        target.touch()

        result = self._run_pre_edit(
            {"tool_input": {"file_path": str(target)}},
            monkeypatch, capsys
        )
        assert "hookSpecificOutput" in result
        output = result["hookSpecificOutput"]
        assert output["permissionDecision"] == "ask"
        assert "READ-BEFORE-EDIT" in output["permissionDecisionReason"]

    def test_passes_after_read(self, tmp_path, project_root,
                               monkeypatch, capsys, isolated_tracker):
        scripts_dir = project_root / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        target = scripts_dir / "debate.py"
        target.touch()

        # Read the file first
        hook_mod.record_read(str(target))

        result = self._run_pre_edit(
            {"tool_input": {"file_path": str(target)}},
            monkeypatch, capsys
        )
        assert result == {}

    def test_passes_for_new_file(self, project_root, monkeypatch, capsys,
                                 isolated_tracker):
        # File doesn't exist on disk
        target = project_root / "scripts" / "brand_new.py"
        result = self._run_pre_edit(
            {"tool_input": {"file_path": str(target)}},
            monkeypatch, capsys
        )
        assert result == {}

    def test_passes_for_exempt_path(self, project_root, monkeypatch, capsys,
                                    isolated_tracker):
        tasks_dir = project_root / "tasks"
        tasks_dir.mkdir(exist_ok=True)
        target = tasks_dir / "plan.md"
        target.touch()

        result = self._run_pre_edit(
            {"tool_input": {"file_path": str(target)}},
            monkeypatch, capsys
        )
        assert result == {}

    def test_passes_for_unprotected_file(self, project_root, monkeypatch, capsys,
                                         isolated_tracker):
        target = project_root / "README.md"
        target.touch()

        result = self._run_pre_edit(
            {"tool_input": {"file_path": str(target)}},
            monkeypatch, capsys
        )
        assert result == {}

    def test_empty_file_path_passes(self, monkeypatch, capsys, isolated_tracker):
        result = self._run_pre_edit(
            {"tool_input": {"file_path": ""}},
            monkeypatch, capsys
        )
        assert result == {}

    def test_empty_stdin_passes(self, monkeypatch, capsys, isolated_tracker):
        monkeypatch.setenv("HOOK_EVENT", "PreToolUse")
        import io
        monkeypatch.setattr("sys.stdin", io.StringIO(""))
        hook_mod.handle_pre_edit()
        result = json.loads(capsys.readouterr().out)
        assert result == {}


# ── main dispatch ────────────────────────────────────────────────────────────


class TestMainDispatch:
    def test_post_tool_use_routes_to_read(self, tmp_path, monkeypatch, isolated_tracker):
        f = tmp_path / "dispatch_test.py"
        f.touch()
        monkeypatch.setenv("HOOK_EVENT", "PostToolUse")
        monkeypatch.setenv("TOOL_INPUT", json.dumps({"file_path": str(f)}))
        hook_mod.main()
        assert hook_mod.was_read(str(f)) is True

    def test_pre_tool_use_routes_to_edit(self, project_root, monkeypatch,
                                         capsys, isolated_tracker):
        scripts_dir = project_root / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        target = scripts_dir / "test.py"
        target.touch()

        monkeypatch.setenv("HOOK_EVENT", "PreToolUse")
        import io
        stdin_data = json.dumps({"tool_input": {"file_path": str(target)}})
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        hook_mod.main()
        result = json.loads(capsys.readouterr().out)
        assert "hookSpecificOutput" in result

    def test_fallback_with_tool_input_env(self, tmp_path, monkeypatch, isolated_tracker):
        """No HOOK_EVENT set, but TOOL_INPUT present → PostToolUse path."""
        f = tmp_path / "fallback_test.py"
        f.touch()
        monkeypatch.delenv("HOOK_EVENT", raising=False)
        monkeypatch.setenv("TOOL_INPUT", json.dumps({"file_path": str(f)}))
        hook_mod.main()
        assert hook_mod.was_read(str(f)) is True

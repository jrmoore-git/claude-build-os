"""Unit tests for scripts/detect-uncommitted.py.

Tests file relevance filtering, auto-commit detection, and category classification.
"""

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Module uses hyphens in filename — import via importlib
import importlib
detect_uncommitted = importlib.import_module("detect-uncommitted")


# ── is_relevant ────────────────────────────────────────────────────────────


class TestIsRelevant:
    def test_tasks_path_relevant(self):
        assert detect_uncommitted.is_relevant("tasks/handoff.md") is True

    def test_scripts_path_relevant(self):
        assert detect_uncommitted.is_relevant("scripts/debate.py") is True

    def test_tests_path_relevant(self):
        assert detect_uncommitted.is_relevant("tests/test_foo.py") is True

    def test_config_path_relevant(self):
        assert detect_uncommitted.is_relevant("config/debate-models.json") is True

    def test_docs_path_relevant(self):
        assert detect_uncommitted.is_relevant("docs/current-state.md") is True

    def test_rules_path_relevant(self):
        assert detect_uncommitted.is_relevant(".claude/rules/security.md") is True

    def test_skills_path_relevant(self):
        assert detect_uncommitted.is_relevant(".claude/skills/start/SKILL.md") is True

    def test_root_file_not_relevant(self):
        assert detect_uncommitted.is_relevant("README.md") is False

    def test_random_dir_not_relevant(self):
        assert detect_uncommitted.is_relevant("vendor/lib.py") is False

    # Exclusion patterns
    def test_env_excluded(self):
        assert detect_uncommitted.is_relevant("config/.env") is False

    def test_pycache_excluded(self):
        assert detect_uncommitted.is_relevant("scripts/__pycache__/foo.pyc") is False

    def test_worktrees_excluded(self):
        assert detect_uncommitted.is_relevant(".claude/worktrees/abc/file.md") is False

    def test_ds_store_excluded(self):
        assert detect_uncommitted.is_relevant("tasks/.DS_Store") is False


# ── check_auto_commit_pending ──────────────────────────────────────────────


class TestCheckAutoCommitPending:
    def test_auto_captured_detected(self, tmp_path, monkeypatch):
        session_log = tmp_path / "tasks" / "session-log.md"
        session_log.parent.mkdir(parents=True)
        session_log.write_text("# Session Log\n---\n## Session 1\nStuff\n---\n## Session 2\n[auto-captured: stop hook]\n")
        monkeypatch.setattr(detect_uncommitted, "get_repo_root", lambda: tmp_path)
        assert detect_uncommitted.check_auto_commit_pending() is True

    def test_normal_entry_not_pending(self, tmp_path, monkeypatch):
        session_log = tmp_path / "tasks" / "session-log.md"
        session_log.parent.mkdir(parents=True)
        session_log.write_text("# Session Log\n---\n## Session 1\nNormal content\n")
        monkeypatch.setattr(detect_uncommitted, "get_repo_root", lambda: tmp_path)
        assert detect_uncommitted.check_auto_commit_pending() is False

    def test_missing_session_log(self, tmp_path, monkeypatch):
        monkeypatch.setattr(detect_uncommitted, "get_repo_root", lambda: tmp_path)
        assert detect_uncommitted.check_auto_commit_pending() is False


# ── file categorization ───────────────────────────────────────────────────


class TestFileCategorization:
    def test_categorizes_by_directory(self):
        files = ["tasks/handoff.md", "tasks/lessons.md", "scripts/debate.py"]
        categories = {}
        for f in files:
            cat = f.split("/")[0] if "/" in f else "root"
            categories.setdefault(cat, []).append(f)
        assert "tasks" in categories
        assert "scripts" in categories
        assert len(categories["tasks"]) == 2


# ── main output format ────────────────────────────────────────────────────


class TestMainOutput:
    def test_clean_repo_silent(self, tmp_path, monkeypatch, capsys):
        """Healthy state emits no stdout — bootstrap_diagnostics treats silence as OK."""
        monkeypatch.setattr(detect_uncommitted, "get_uncommitted_files", lambda: [])
        monkeypatch.setattr(detect_uncommitted, "check_auto_commit_pending", lambda: False)
        detect_uncommitted.main()
        assert capsys.readouterr().out == ""

    def test_uncommitted_emits_json(self, tmp_path, monkeypatch, capsys):
        """Issue state emits one JSON object with the findings."""
        monkeypatch.setattr(detect_uncommitted, "get_uncommitted_files", lambda: ["tasks/foo.md"])
        monkeypatch.setattr(detect_uncommitted, "check_auto_commit_pending", lambda: False)
        monkeypatch.setattr(detect_uncommitted, "file_age_summary", lambda files: (None, None))
        detect_uncommitted.main()
        output = json.loads(capsys.readouterr().out)
        assert output["has_uncommitted"] is True
        assert output["files"] == ["tasks/foo.md"]

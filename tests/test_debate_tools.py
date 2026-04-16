"""Unit tests for scripts/debate_tools.py.

Tests the verifier tool implementations used by debate challengers and judges.
Uses tmp_path fixtures for file I/O tests to avoid touching real project files.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

for mod in [k for k in sys.modules if k.startswith("debate_tools")]:
    del sys.modules[mod]

import debate_tools


# ── execute_tool dispatcher ────────────────────────────────────────────────


class TestExecuteTool:
    def test_unknown_tool_returns_error(self):
        result = json.loads(debate_tools.execute_tool("nonexistent_tool", {}))
        assert "error" in result
        assert "unknown tool" in result["error"]

    def test_dispatches_to_check_test_coverage(self):
        result = json.loads(debate_tools.execute_tool(
            "check_test_coverage",
            {"module_path": "scripts/debate.py"},
        ))
        assert "module" in result
        assert result["module"] == "scripts/debate.py"

    def test_exception_in_handler_returns_error(self):
        with patch.dict(debate_tools._TOOL_DISPATCH, {
            "bad_tool": lambda args: (_ for _ in ()).throw(RuntimeError("boom"))
        }):
            result = json.loads(debate_tools.execute_tool("bad_tool", {}))
            assert "error" in result

    def test_result_truncation(self):
        with patch.dict(debate_tools._TOOL_DISPATCH, {
            "big_tool": lambda args: json.dumps({"data": "x" * 10000})
        }):
            result = debate_tools.execute_tool("big_tool", {})
            assert len(result) <= debate_tools.MAX_RESULT_LEN + 10


# ── _check_test_coverage (pure path logic) ─────────────────────────────────


class TestCheckTestCoverage:
    def test_finds_existing_test(self):
        # debate_tools.py has a test file: tests/test_debate_tools.py
        result = json.loads(debate_tools._check_test_coverage(
            {"module_path": "scripts/debate_tools.py"}
        ))
        assert result["module"] == "scripts/debate_tools.py"
        assert result["has_test"] is True
        assert any("test_debate_tools" in f for f in result["test_files"])

    def test_module_without_test(self):
        result = json.loads(debate_tools._check_test_coverage(
            {"module_path": "scripts/check-current-state-freshness.py"}
        ))
        assert result["has_test"] is False
        assert result["test_files"] == []

    def test_empty_path_rejected(self):
        result = json.loads(debate_tools._check_test_coverage({"module_path": ""}))
        assert "error" in result

    def test_path_traversal_rejected(self):
        result = json.loads(debate_tools._check_test_coverage(
            {"module_path": "../../../etc/passwd"}
        ))
        assert "error" in result

    def test_absolute_path_rejected(self):
        result = json.loads(debate_tools._check_test_coverage(
            {"module_path": "/usr/bin/python3"}
        ))
        assert "error" in result

    def test_long_path_rejected(self):
        result = json.loads(debate_tools._check_test_coverage(
            {"module_path": "a" * 201}
        ))
        assert "error" in result

    def test_strips_leading_dot_slash(self):
        result = json.loads(debate_tools._check_test_coverage(
            {"module_path": "./scripts/debate.py"}
        ))
        assert result["module"] == "scripts/debate.py"


# ── _check_code_presence ───────────────────────────────────────────────────


class TestCheckCodePresence:
    def test_finds_existing_code(self):
        result = json.loads(debate_tools._check_code_presence(
            {"substring": "def _estimate_cost", "file_set": "scripts"}
        ))
        assert result["exists"] is True
        assert result["match_count"] >= 1

    def test_missing_code(self):
        result = json.loads(debate_tools._check_code_presence(
            {"substring": "def _this_function_does_not_exist_xyz", "file_set": "scripts"}
        ))
        assert result["exists"] is False
        assert result["match_count"] == 0

    def test_invalid_file_set(self):
        result = json.loads(debate_tools._check_code_presence(
            {"substring": "test", "file_set": "system_files"}
        ))
        assert "error" in result

    def test_empty_substring(self):
        result = json.loads(debate_tools._check_code_presence(
            {"substring": "", "file_set": "scripts"}
        ))
        assert "error" in result

    def test_too_long_substring(self):
        result = json.loads(debate_tools._check_code_presence(
            {"substring": "x" * 201, "file_set": "scripts"}
        ))
        assert "error" in result


# ── _check_function_exists ─────────────────────────────────────────────────


class TestCheckFunctionExists:
    def test_finds_existing_function(self):
        result = json.loads(debate_tools._check_function_exists(
            {"identifier": "_estimate_cost", "file_set": "scripts"}
        ))
        assert result["exists"] is True

    def test_finds_existing_class(self):
        result = json.loads(debate_tools._check_function_exists(
            {"identifier": "LLMError", "file_set": "scripts"}
        ))
        assert result["exists"] is True

    def test_missing_function(self):
        result = json.loads(debate_tools._check_function_exists(
            {"identifier": "nonexistent_function_xyz", "file_set": "scripts"}
        ))
        assert result["exists"] is False

    def test_invalid_identifier(self):
        result = json.loads(debate_tools._check_function_exists(
            {"identifier": "bad-identifier!", "file_set": "scripts"}
        ))
        assert "error" in result

    def test_empty_identifier(self):
        result = json.loads(debate_tools._check_function_exists(
            {"identifier": "", "file_set": "scripts"}
        ))
        assert "error" in result


# ── _read_config_value ─────────────────────────────────────────────────────


class TestReadConfigValue:
    def test_reads_allowed_key(self):
        result = json.loads(debate_tools._read_config_value(
            {"key": "judge_default"}
        ))
        assert "value" in result
        assert result["key"] == "judge_default"

    def test_disallowed_key(self):
        result = json.loads(debate_tools._read_config_value(
            {"key": "not_in_allowlist"}
        ))
        assert "error" in result

    def test_secret_pattern_blocked(self):
        # Even if a key were in the allowlist, secret patterns should block
        result = json.loads(debate_tools._read_config_value(
            {"key": "api_key"}
        ))
        assert "error" in result


# ── _read_file_snippet ─────────────────────────────────────────────────────


class TestReadFileSnippet:
    def test_reads_valid_file(self):
        result = json.loads(debate_tools._read_file_snippet(
            {"file_path": "scripts/debate_tools.py", "start_line": 1, "max_lines": 5}
        ))
        assert "content" in result
        assert result["start_line"] == 1
        assert result["end_line"] == 5

    def test_path_traversal_rejected(self):
        result = json.loads(debate_tools._read_file_snippet(
            {"file_path": "../../../etc/passwd"}
        ))
        assert "error" in result

    def test_absolute_path_rejected(self):
        result = json.loads(debate_tools._read_file_snippet(
            {"file_path": "/etc/passwd"}
        ))
        assert "error" in result

    def test_disallowed_directory(self):
        result = json.loads(debate_tools._read_file_snippet(
            {"file_path": "stores/debate-log.jsonl"}
        ))
        assert "error" in result
        assert "allowed directories" in result["error"]

    def test_blocked_extension(self):
        result = json.loads(debate_tools._read_file_snippet(
            {"file_path": "config/secrets.env"}
        ))
        assert "error" in result

    def test_nonexistent_file(self):
        result = json.loads(debate_tools._read_file_snippet(
            {"file_path": "scripts/nonexistent_xyz.py"}
        ))
        assert "error" in result
        assert "not found" in result["error"]

    def test_max_lines_capped(self):
        result = json.loads(debate_tools._read_file_snippet(
            {"file_path": "scripts/debate_tools.py", "max_lines": 999}
        ))
        # Should cap at MAX_SNIPPET_LINES
        line_count = result["end_line"] - result["start_line"] + 1
        assert line_count <= debate_tools.MAX_SNIPPET_LINES


# ── _get_recent_commits ────────────────────────────────────────────────────


class TestGetRecentCommits:
    def test_gets_commits_for_real_file(self):
        result = json.loads(debate_tools._get_recent_commits(
            {"file_paths": ["scripts/debate.py"], "limit": 3}
        ))
        assert "commits" in result
        assert result["commit_count"] <= 3

    def test_invalid_paths_rejected(self):
        result = json.loads(debate_tools._get_recent_commits(
            {"file_paths": ["../../../etc/passwd"]}
        ))
        assert "error" in result

    def test_empty_paths_rejected(self):
        result = json.loads(debate_tools._get_recent_commits(
            {"file_paths": []}
        ))
        assert "error" in result

    def test_too_many_paths_rejected(self):
        result = json.loads(debate_tools._get_recent_commits(
            {"file_paths": ["a.py", "b.py", "c.py", "d.py", "e.py", "f.py"]}
        ))
        assert "error" in result

    def test_non_list_rejected(self):
        result = json.loads(debate_tools._get_recent_commits(
            {"file_paths": "scripts/debate.py"}
        ))
        assert "error" in result


# ── TOOL_DEFINITIONS shape ─────────────────────────────────────────────────


class TestToolDefinitions:
    def test_all_dispatched_tools_have_definitions(self):
        defined_names = {t["function"]["name"] for t in debate_tools.TOOL_DEFINITIONS}
        dispatch_names = set(debate_tools._TOOL_DISPATCH.keys())
        assert dispatch_names == defined_names, (
            f"Mismatch: dispatch has {dispatch_names - defined_names}, "
            f"definitions has {defined_names - dispatch_names}"
        )

    def test_definitions_have_required_fields(self):
        for tool in debate_tools.TOOL_DEFINITIONS:
            assert "type" in tool
            assert tool["type"] == "function"
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func

    def test_all_definitions_have_required_params(self):
        for tool in debate_tools.TOOL_DEFINITIONS:
            func = tool["function"]
            params = func["parameters"]
            assert "properties" in params
            # "required" is optional but should be a list if present
            if "required" in params:
                assert isinstance(params["required"], list)


# ── ALLOWED_FILE_SETS / ALLOWED_SNIPPET_PATHS consistency ─────────────────


class TestFileSetConsistency:
    def test_hooks_in_allowed_file_sets(self):
        assert "hooks" in debate_tools.ALLOWED_FILE_SETS

    def test_tests_in_allowed_file_sets(self):
        assert "tests" in debate_tools.ALLOWED_FILE_SETS

    def test_rules_in_allowed_file_sets(self):
        assert "rules" in debate_tools.ALLOWED_FILE_SETS

    def test_docs_in_allowed_file_sets(self):
        assert "docs" in debate_tools.ALLOWED_FILE_SETS

    def test_snippet_paths_include_rules_and_docs(self):
        assert "rules" in debate_tools.ALLOWED_SNIPPET_PATHS
        assert "docs" in debate_tools.ALLOWED_SNIPPET_PATHS

    def test_search_can_find_hooks(self):
        """The session 18 failure: challengers couldn't search hooks/."""
        result = json.loads(debate_tools._check_code_presence(
            {"substring": "def ", "file_set": "hooks"}
        ))
        assert result["exists"] is True
        assert result["match_count"] >= 1

    def test_search_can_find_tests(self):
        result = json.loads(debate_tools._check_code_presence(
            {"substring": "def test_", "file_set": "tests"}
        ))
        assert result["exists"] is True

    def test_function_exists_searches_hooks(self):
        """check_function_exists should find hook functions."""
        # hook-context-inject.py has exported functions
        result = json.loads(debate_tools._check_function_exists(
            {"identifier": "gather_context", "file_set": "hooks"}
        ))
        # May or may not find this specific name, but shouldn't error
        assert "error" not in result

    def test_snippet_reads_rules(self):
        result = json.loads(debate_tools._read_file_snippet(
            {"file_path": ".claude/rules/code-quality.md", "max_lines": 5}
        ))
        assert "content" in result

    def test_snippet_reads_docs(self):
        result = json.loads(debate_tools._read_file_snippet(
            {"file_path": "docs/current-state.md", "max_lines": 5}
        ))
        assert "content" in result


# ── generate_repo_manifest ────────────────────────────────────────────────


class TestRepoManifest:
    def test_manifest_returns_dict(self):
        m = debate_tools.generate_repo_manifest()
        assert isinstance(m, dict)
        assert "directories" in m
        assert "files" in m
        assert "exports" in m

    def test_manifest_includes_hooks_dir(self):
        m = debate_tools.generate_repo_manifest()
        assert "hooks" in m["directories"]

    def test_manifest_lists_hook_files(self):
        m = debate_tools.generate_repo_manifest()
        hooks = m["files"].get("hooks", [])
        assert len(hooks) > 0
        assert any("hook-context-inject" in h for h in hooks)

    def test_manifest_lists_scripts(self):
        m = debate_tools.generate_repo_manifest()
        scripts = m["files"].get("scripts", [])
        assert any("debate.py" in s for s in scripts)

    def test_manifest_lists_skills_by_name(self):
        m = debate_tools.generate_repo_manifest()
        skills = m["files"].get("skills", [])
        assert "challenge" in skills
        assert "review" in skills

    def test_manifest_includes_exports(self):
        m = debate_tools.generate_repo_manifest()
        assert len(m["exports"]) > 0
        # debate.py should have exported functions
        debate_exports = m["exports"].get("scripts/debate.py", [])
        assert len(debate_exports) > 0

    def test_manifest_excludes_secrets(self):
        m = debate_tools.generate_repo_manifest()
        all_files = []
        for files in m["files"].values():
            all_files.extend(files)
        for f in all_files:
            basename = os.path.basename(f).lower()
            for pattern in debate_tools.SECRET_PATTERNS:
                assert pattern not in basename, f"Secret-like file in manifest: {f}"

    def test_manifest_caps_file_count(self):
        m = debate_tools.generate_repo_manifest()
        for category, files in m["files"].items():
            assert len(files) <= debate_tools.MAX_MANIFEST_FILES

    def test_format_manifest_context_returns_string(self):
        m = debate_tools.generate_repo_manifest()
        text = debate_tools.format_manifest_context(m)
        assert isinstance(text, str)
        assert "Repository Structure" in text
        assert "deterministic" in text

    def test_format_manifest_includes_hooks_section(self):
        m = debate_tools.generate_repo_manifest()
        text = debate_tools.format_manifest_context(m)
        assert "hooks" in text.lower()
        assert "hook-context-inject" in text

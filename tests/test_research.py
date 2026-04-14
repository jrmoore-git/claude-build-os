"""Unit tests for scripts/research.py.

Tests pure functions: format_output, load_api_key, request body construction.
Does NOT test actual API calls.
"""

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import research  # noqa: E402


# ── format_output ──────────────────────────────────────────────────────────


class TestFormatOutput:
    def test_async_basic(self):
        result = {
            "response": {
                "choices": [{"message": {"content": "Research findings here."}}],
                "citations": [],
            }
        }
        output = research.format_output(result, async_mode=True)
        assert "Research findings here." in output

    def test_sync_basic(self):
        result = {
            "choices": [{"message": {"content": "Sync findings."}}],
            "citations": [],
        }
        output = research.format_output(result, async_mode=False)
        assert "Sync findings." in output

    def test_dict_citations(self):
        result = {
            "choices": [{"message": {"content": "Content."}}],
            "citations": [
                {"title": "Paper A", "url": "https://example.com/a", "date": "2026-01"},
                {"title": "Paper B", "url": "https://example.com/b"},
            ],
        }
        output = research.format_output(result, async_mode=False)
        assert "Sources" in output
        assert "[Paper A](https://example.com/a)" in output
        assert "(2026-01)" in output
        assert "[Paper B](https://example.com/b)" in output

    def test_string_citations(self):
        result = {
            "choices": [{"message": {"content": "Content."}}],
            "citations": ["https://example.com/1", "https://example.com/2"],
        }
        output = research.format_output(result, async_mode=False)
        assert "1. https://example.com/1" in output
        assert "2. https://example.com/2" in output

    def test_no_choices_returns_error(self):
        result = {"choices": []}
        output = research.format_output(result, async_mode=False)
        assert "ERROR" in output

    def test_empty_content(self):
        result = {"choices": [{"message": {"content": ""}}]}
        output = research.format_output(result, async_mode=False)
        assert isinstance(output, str)

    def test_citation_without_title_uses_url(self):
        result = {
            "choices": [{"message": {"content": "Content."}}],
            "citations": [{"url": "https://example.com/notitle"}],
        }
        output = research.format_output(result, async_mode=False)
        assert "https://example.com/notitle" in output

    def test_async_nested_response(self):
        """Async results nest the response under a 'response' key."""
        result = {
            "response": {
                "choices": [{"message": {"content": "Async content."}}],
                "citations": [{"title": "Source", "url": "https://x.com"}],
            }
        }
        output = research.format_output(result, async_mode=True)
        assert "Async content." in output
        assert "[Source](https://x.com)" in output

    def test_usage_not_in_stdout(self, capsys):
        """Usage stats go to stderr, not stdout."""
        result = {
            "choices": [{"message": {"content": "Content."}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 200},
        }
        output = research.format_output(result, async_mode=False)
        captured = capsys.readouterr()
        # Usage goes to stderr
        assert "300" in captured.err or "Tokens" in captured.err
        # Content is in the return value, not stdout
        assert "Content." in output


# ── load_api_key ───────────────────────────────────────────────────────────


class TestLoadApiKey:
    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key-123")
        assert research.load_api_key() == "test-key-123"

    def test_from_env_file(self, tmp_path, monkeypatch):
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text("OTHER_VAR=foo\nPERPLEXITY_API_KEY=file-key-456\n")
        monkeypatch.setattr(research, "PROJECT_ROOT", tmp_path)
        assert research.load_api_key() == "file-key-456"

    def test_env_takes_precedence(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PERPLEXITY_API_KEY", "env-key")
        env_file = tmp_path / ".env"
        env_file.write_text("PERPLEXITY_API_KEY=file-key\n")
        monkeypatch.setattr(research, "PROJECT_ROOT", tmp_path)
        assert research.load_api_key() == "env-key"

    def test_missing_key_exits(self, tmp_path, monkeypatch):
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        monkeypatch.setattr(research, "PROJECT_ROOT", tmp_path)
        with pytest.raises(SystemExit):
            research.load_api_key()

    def test_strips_quotes(self, tmp_path, monkeypatch):
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text("PERPLEXITY_API_KEY='quoted-key'\n")
        monkeypatch.setattr(research, "PROJECT_ROOT", tmp_path)
        assert research.load_api_key() == "quoted-key"

    def test_skips_comments(self, tmp_path, monkeypatch):
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text("# PERPLEXITY_API_KEY=commented-out\nPERPLEXITY_API_KEY=real-key\n")
        monkeypatch.setattr(research, "PROJECT_ROOT", tmp_path)
        assert research.load_api_key() == "real-key"


# ── Request body construction ──────────────────────────────────────────────


class TestRequestBodyConstruction:
    def test_submit_async_default_body(self, monkeypatch):
        """Verify submit_async builds the correct request body."""
        captured = {}

        def fake_api_request(method, path, key, body=None):
            captured["body"] = body
            return {"id": "test-id"}

        monkeypatch.setattr(research, "api_request", fake_api_request)
        research.submit_async("key", [{"role": "user", "content": "test"}])
        assert captured["body"]["request"]["model"] == "sonar-deep-research"
        assert "reasoning_effort" not in captured["body"]["request"]

    def test_submit_async_with_effort(self, monkeypatch):
        captured = {}

        def fake_api_request(method, path, key, body=None):
            captured["body"] = body
            return {"id": "test-id"}

        monkeypatch.setattr(research, "api_request", fake_api_request)
        research.submit_async("key", [{"role": "user", "content": "test"}], effort="high")
        assert captured["body"]["request"]["reasoning_effort"] == "high"

    def test_submit_async_academic(self, monkeypatch):
        captured = {}

        def fake_api_request(method, path, key, body=None):
            captured["body"] = body
            return {"id": "test-id"}

        monkeypatch.setattr(research, "api_request", fake_api_request)
        research.submit_async("key", [{"role": "user", "content": "test"}], academic=True)
        assert captured["body"]["request"]["search_mode"] == "academic"

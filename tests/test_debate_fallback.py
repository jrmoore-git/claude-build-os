"""Unit tests for debate.py fallback and retry logic.

Tests _call_with_model_fallback behavior under various failure scenarios.
Uses monkeypatch on the module object to avoid import-order issues in full suite.
"""

import sys
import urllib.error
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import debate  # noqa: E402


def _make_call(primary="model-a", fallback="model-b", **kwargs):
    """Call _call_with_model_fallback with test defaults."""
    return debate._call_with_model_fallback(
        primary, fallback,
        system_prompt="test system",
        user_content="test user",
        litellm_url="http://test:4000",
        api_key="test-key",
        **kwargs,
    )


class TestCallWithModelFallback:
    """Tests for _call_with_model_fallback."""

    def test_primary_succeeds(self, monkeypatch):
        calls = []

        def fake_call(model, *a, **kw):
            calls.append(model)
            return "primary response"

        monkeypatch.setattr(debate, "_call_litellm", fake_call)
        text, model_used = _make_call()
        assert text == "primary response"
        assert model_used == "model-a"
        assert len(calls) == 1

    def test_timeout_triggers_fallback(self, monkeypatch):
        calls = []

        def fake_call(model, *a, **kw):
            calls.append(model)
            if len(calls) == 1:
                raise debate.LLMError("timed out", category="timeout")
            return "fallback response"

        monkeypatch.setattr(debate, "_call_litellm", fake_call)
        text, model_used = _make_call()
        assert text == "fallback response"
        assert model_used == "model-b"
        assert len(calls) == 2

    def test_builtin_timeout_triggers_fallback(self, monkeypatch):
        calls = []

        def fake_call(model, *a, **kw):
            calls.append(model)
            if len(calls) == 1:
                raise TimeoutError("conn timeout")
            return "fallback response"

        monkeypatch.setattr(debate, "_call_litellm", fake_call)
        text, model_used = _make_call()
        assert text == "fallback response"
        assert model_used == "model-b"

    def test_non_timeout_error_raises(self, monkeypatch):
        calls = []

        def fake_call(model, *a, **kw):
            calls.append(model)
            raise debate.LLMError("rate limited", category="rate_limit")

        monkeypatch.setattr(debate, "_call_litellm", fake_call)
        with pytest.raises(debate.LLMError, match="rate limited"):
            _make_call()
        assert len(calls) == 1

    def test_both_models_fail(self, monkeypatch):
        calls = []

        def fake_call(model, *a, **kw):
            calls.append(model)
            if len(calls) == 1:
                raise debate.LLMError("primary timeout", category="timeout")
            raise debate.LLMError("fallback timeout", category="timeout")

        monkeypatch.setattr(debate, "_call_litellm", fake_call)
        with pytest.raises(debate.LLMError, match="fallback timeout"):
            _make_call()
        assert len(calls) == 2

    def test_no_fallback_model_raises(self, monkeypatch):
        calls = []

        def fake_call(model, *a, **kw):
            calls.append(model)
            raise debate.LLMError("timed out", category="timeout")

        monkeypatch.setattr(debate, "_call_litellm", fake_call)
        with pytest.raises(debate.LLMError):
            _make_call(fallback=None)
        assert len(calls) == 1

    def test_same_model_fallback_raises(self, monkeypatch):
        calls = []

        def fake_call(model, *a, **kw):
            calls.append(model)
            raise debate.LLMError("timed out", category="timeout")

        monkeypatch.setattr(debate, "_call_litellm", fake_call)
        with pytest.raises(debate.LLMError):
            _make_call(primary="model-a", fallback="model-a")
        assert len(calls) == 1

    def test_fallback_non_timeout_error_raises(self, monkeypatch):
        calls = []

        def fake_call(model, *a, **kw):
            calls.append(model)
            if len(calls) == 1:
                raise debate.LLMError("primary timeout", category="timeout")
            raise debate.LLMError("auth failed", category="auth")

        monkeypatch.setattr(debate, "_call_litellm", fake_call)
        with pytest.raises(debate.LLMError, match="auth failed"):
            _make_call()

    def test_kwargs_passed_through(self, monkeypatch):
        captured_kwargs = {}

        def fake_call(model, system_prompt, user_content, litellm_url, api_key, **kw):
            captured_kwargs.update(kw)
            return "ok"

        monkeypatch.setattr(debate, "_call_litellm", fake_call)
        _make_call(temperature=0.7, max_tokens=1000)
        assert captured_kwargs.get("temperature") == 0.7
        assert captured_kwargs.get("max_tokens") == 1000

    def test_urllib_error_not_timeout_raises(self, monkeypatch):
        calls = []

        def fake_call(model, *a, **kw):
            calls.append(model)
            raise urllib.error.HTTPError(
                "http://test", 500, "Server Error", {}, None
            )

        monkeypatch.setattr(debate, "_call_litellm", fake_call)
        with pytest.raises(urllib.error.HTTPError):
            _make_call()
        assert len(calls) == 1


class TestGetFallbackModel:
    """Tests for _get_fallback_model."""

    def test_returns_different_model(self):
        config = {
            "single_review_default": "gpt-5.4",
            "verifier_default": "claude-sonnet-4-6",
            "judge_default": "gpt-5.4",
        }
        result = debate._get_fallback_model("gemini-3.1-pro", config)
        assert result == "gpt-5.4"
        assert result != "gemini-3.1-pro"

    def test_skips_same_model(self):
        config = {
            "single_review_default": "gpt-5.4",
            "verifier_default": "claude-sonnet-4-6",
            "judge_default": "gpt-5.4",
        }
        result = debate._get_fallback_model("gpt-5.4", config)
        assert result == "claude-sonnet-4-6"

    def test_returns_none_when_all_same(self):
        config = {
            "single_review_default": "model-x",
            "verifier_default": "model-x",
            "judge_default": "model-x",
        }
        result = debate._get_fallback_model("model-x", config)
        assert result is None

    def test_uses_defaults_when_config_empty(self):
        result = debate._get_fallback_model("gemini-3.1-pro", {})
        assert result == "gpt-5.4"

    def test_uses_defaults_when_primary_is_default(self):
        result = debate._get_fallback_model("gpt-5.4", {})
        assert result == "claude-sonnet-4-6"

    def test_returns_first_available_candidate(self):
        config = {
            "single_review_default": "model-a",
            "verifier_default": "model-b",
            "judge_default": "model-c",
        }
        result = debate._get_fallback_model("model-a", config)
        assert result == "model-b"

    def test_none_config_value_skipped(self):
        config = {
            "single_review_default": None,
            "verifier_default": "model-b",
            "judge_default": "model-c",
        }
        result = debate._get_fallback_model("model-a", config)
        assert result == "model-b"

    def test_skips_duplicate_candidates(self):
        config = {
            "single_review_default": "model-a",
            "verifier_default": "model-a",
            "judge_default": "model-b",
        }
        result = debate._get_fallback_model("model-a", config)
        assert result == "model-b"

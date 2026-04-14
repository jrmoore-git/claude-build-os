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

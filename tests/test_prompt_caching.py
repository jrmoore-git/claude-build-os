#!/usr/bin/env python3.11
"""Tests for prompt-caching plumbing in scripts/llm_client.py and
scripts/debate_common.py.

Covers:
- cache_control / cache_ttl validation
- BUILDOS_CACHE_DISABLE rollback flag
- _cache_marker shape for 5m vs 1h TTL
- _extract_cache_usage (dict + object + nested prompt_tokens_details)
- cache_control threads through _sdk_call (OpenAI SDK path)
- cache_control threads through _legacy_call (urllib path)
- cache_control threads through _anthropic_call (direct Anthropic path)
- _log_debate_event captures cache_read / cache_creation tokens
- BUILDOS_CACHE_DISABLE=1 strips markers at the payload boundary

Does NOT cover cost pricing (Component 3b) — those tests are added when 3b lands.

Run with: python3.11 -m pytest tests/test_prompt_caching.py -v
"""

import json
import os
import sys
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts/ to import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import debate_common
import llm_client
from llm_client import (
    LLMError,
    _anthropic_call,
    _cache_enabled,
    _cache_marker,
    _extract_cache_usage,
    _legacy_call,
    _sdk_call,
    _should_cache,
    _validate_cache_args,
)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_cache_control_accepts_valid_scopes():
    _validate_cache_args(None, None)
    _validate_cache_args("system", None)
    _validate_cache_args("system+user", None)


def test_cache_ttl_accepts_valid_values():
    _validate_cache_args("system", None)
    _validate_cache_args("system", "5m")


def test_cache_control_rejects_invalid_scope():
    with pytest.raises(LLMError) as ei:
        _validate_cache_args("bogus", None)
    assert ei.value.category == "parse"


def test_cache_ttl_rejects_invalid_value():
    with pytest.raises(LLMError) as ei:
        _validate_cache_args("system", "3m")
    assert ei.value.category == "parse"


def test_cache_ttl_rejects_1h_in_phase_0():
    """Phase 0 exposes only 5m TTL via the public API.

    The internal _cache_marker helper still supports emitting ttl='1h' for
    a future phase where pricing logic is extended; but the public validator
    rejects '1h' today so no caller can silently misbill through the
    hardcoded 5m write multiplier in debate_common._estimate_cost.
    """
    with pytest.raises(LLMError) as ei:
        _validate_cache_args("system", "1h")
    assert ei.value.category == "parse"
    # Error message must not advertise '1h' in the "Expected one of" list —
    # catches drift when 1h re-enables in a future phase without the validator
    # message being updated. (The rejected value itself is echoed back in the
    # message, so we check the "Expected" clause only.)
    expected_clause = str(ei.value).split("Expected one of:", 1)[1]
    assert "'1h'" not in expected_clause


# ---------------------------------------------------------------------------
# BUILDOS_CACHE_DISABLE flag
# ---------------------------------------------------------------------------

def test_cache_enabled_default_true(monkeypatch):
    monkeypatch.delenv("BUILDOS_CACHE_DISABLE", raising=False)
    assert _cache_enabled() is True


def test_cache_disabled_when_env_set(monkeypatch):
    monkeypatch.setenv("BUILDOS_CACHE_DISABLE", "1")
    assert _cache_enabled() is False


def test_should_cache_respects_disable_flag(monkeypatch):
    monkeypatch.setenv("BUILDOS_CACHE_DISABLE", "1")
    # Even with a valid scope, _should_cache returns False when disabled
    assert _should_cache("system") is False
    assert _should_cache("system+user") is False


def test_should_cache_false_when_scope_none(monkeypatch):
    monkeypatch.delenv("BUILDOS_CACHE_DISABLE", raising=False)
    assert _should_cache(None) is False


# ---------------------------------------------------------------------------
# _cache_marker
# ---------------------------------------------------------------------------

def test_cache_marker_default_omits_ttl():
    # Default (None or '5m') should produce {'type': 'ephemeral'} — no ttl field
    assert _cache_marker(None) == {"type": "ephemeral"}
    assert _cache_marker("5m") == {"type": "ephemeral"}


def test_cache_marker_1h_sets_ttl():
    assert _cache_marker("1h") == {"type": "ephemeral", "ttl": "1h"}


# ---------------------------------------------------------------------------
# _extract_cache_usage
# ---------------------------------------------------------------------------

def test_extract_cache_usage_empty_dict():
    assert _extract_cache_usage({}) == (0, 0)


def test_extract_cache_usage_anthropic_native_fields():
    usage = {"cache_read_input_tokens": 1000, "cache_creation_input_tokens": 500}
    assert _extract_cache_usage(usage) == (1000, 500)


def test_extract_cache_usage_openai_style_nested():
    # LiteLLM may normalize Anthropic cache reads into prompt_tokens_details.cached_tokens
    usage = {"prompt_tokens_details": {"cached_tokens": 200}}
    assert _extract_cache_usage(usage) == (200, 0)


def test_extract_cache_usage_object_with_attrs():
    usage = MagicMock()
    usage.cache_read_input_tokens = 100
    usage.cache_creation_input_tokens = 50
    # ensure prompt_tokens_details doesn't interfere
    usage.prompt_tokens_details = None
    assert _extract_cache_usage(usage) == (100, 50)


def test_extract_cache_usage_handles_missing_fields_on_object():
    # An OpenAI usage object without cache fields should return (0, 0) cleanly
    class FakeUsage:
        prompt_tokens = 100
        completion_tokens = 50
        total_tokens = 150
    assert _extract_cache_usage(FakeUsage()) == (0, 0)


# ---------------------------------------------------------------------------
# cache_control threads through _sdk_call
# ---------------------------------------------------------------------------

def _make_sdk_response(prompt_tokens=100, completion_tokens=50,
                      cache_read=0, cache_creation=0):
    response = MagicMock()
    response.model = "claude-sonnet-4-6"
    response.choices = [MagicMock()]
    response.choices[0].message.content = "test response"
    response.usage.prompt_tokens = prompt_tokens
    response.usage.completion_tokens = completion_tokens
    response.usage.total_tokens = prompt_tokens + completion_tokens
    response.usage.cache_read_input_tokens = cache_read
    response.usage.cache_creation_input_tokens = cache_creation
    response.usage.prompt_tokens_details = None
    return response


def test_sdk_call_without_cache_uses_plain_strings():
    """When cache_control is None, messages stay as plain {'role', 'content': str}."""
    captured = {}
    with patch("openai.OpenAI") as mock_openai_cls:
        client = mock_openai_cls.return_value
        def capture(**kwargs):
            captured.update(kwargs)
            return _make_sdk_response()
        client.chat.completions.create.side_effect = capture

        _sdk_call("sys prompt", "user msg",
                  model="claude-sonnet-4-6", temperature=0.0,
                  max_tokens=512, timeout=30,
                  base_url="http://localhost:4000/v1", api_key="test-key")

    assert captured["messages"][0] == {"role": "system", "content": "sys prompt"}
    assert captured["messages"][1] == {"role": "user", "content": "user msg"}


def test_sdk_call_with_system_cache_rewrites_system_only():
    """cache_control='system' adds cache_control marker to system block only."""
    captured = {}
    with patch("openai.OpenAI") as mock_openai_cls:
        client = mock_openai_cls.return_value
        def capture(**kwargs):
            captured.update(kwargs)
            return _make_sdk_response()
        client.chat.completions.create.side_effect = capture

        _sdk_call("sys prompt", "user msg",
                  model="claude-sonnet-4-6", temperature=0.0,
                  max_tokens=512, timeout=30,
                  base_url="http://localhost:4000/v1", api_key="test-key",
                  cache_control="system")

    sys_msg = captured["messages"][0]
    user_msg = captured["messages"][1]
    assert sys_msg["role"] == "system"
    assert sys_msg["content"] == [
        {"type": "text", "text": "sys prompt", "cache_control": {"type": "ephemeral"}},
    ]
    # user stays plain
    assert user_msg == {"role": "user", "content": "user msg"}


def test_sdk_call_with_system_plus_user_cache_rewrites_both():
    """cache_control='system+user' adds markers to both blocks."""
    captured = {}
    with patch("openai.OpenAI") as mock_openai_cls:
        client = mock_openai_cls.return_value
        def capture(**kwargs):
            captured.update(kwargs)
            return _make_sdk_response()
        client.chat.completions.create.side_effect = capture

        _sdk_call("sys prompt", "user msg",
                  model="claude-sonnet-4-6", temperature=0.0,
                  max_tokens=512, timeout=30,
                  base_url="http://localhost:4000/v1", api_key="test-key",
                  cache_control="system+user")

    sys_msg = captured["messages"][0]
    user_msg = captured["messages"][1]
    assert sys_msg["content"][0]["cache_control"] == {"type": "ephemeral"}
    assert user_msg["content"] == [
        {"type": "text", "text": "user msg", "cache_control": {"type": "ephemeral"}},
    ]


def test_sdk_call_with_1h_ttl_sets_ttl_field(monkeypatch):
    """cache_ttl='1h' adds ttl: '1h' to the marker."""
    captured = {}
    monkeypatch.delenv("BUILDOS_CACHE_DISABLE", raising=False)
    with patch("openai.OpenAI") as mock_openai_cls:
        client = mock_openai_cls.return_value
        def capture(**kwargs):
            captured.update(kwargs)
            return _make_sdk_response()
        client.chat.completions.create.side_effect = capture

        _sdk_call("sys prompt", "user msg",
                  model="claude-sonnet-4-6", temperature=0.0,
                  max_tokens=512, timeout=30,
                  base_url="http://localhost:4000/v1", api_key="test-key",
                  cache_control="system+user", cache_ttl="1h")

    marker = captured["messages"][0]["content"][0]["cache_control"]
    assert marker == {"type": "ephemeral", "ttl": "1h"}


def test_sdk_call_returns_cache_tokens_in_usage():
    """Returned usage dict exposes cache_read / cache_creation token counts."""
    with patch("openai.OpenAI") as mock_openai_cls:
        client = mock_openai_cls.return_value
        client.chat.completions.create.return_value = _make_sdk_response(
            cache_read=250, cache_creation=100,
        )

        _content, _model, usage = _sdk_call(
            "sys prompt", "user msg",
            model="claude-sonnet-4-6", temperature=0.0,
            max_tokens=512, timeout=30,
            base_url="http://localhost:4000/v1", api_key="test-key",
        )
    assert usage["cache_read_input_tokens"] == 250
    assert usage["cache_creation_input_tokens"] == 100


# ---------------------------------------------------------------------------
# cache_control threads through _anthropic_call (direct Anthropic path)
# ---------------------------------------------------------------------------

def _make_anthropic_response_body(input_tokens=100, output_tokens=50,
                                  cache_read=0, cache_creation=0):
    return {
        "content": [{"text": "test response"}],
        "model": "claude-sonnet-4-6-20250805",
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_input_tokens": cache_read,
            "cache_creation_input_tokens": cache_creation,
        },
    }


def _patch_urlopen_with_body(body_dict):
    """Return a context manager patch for urllib.request.urlopen that captures
    the payload and returns a fake response."""
    captured = {"url": None, "payload": None, "headers": None}

    fake_resp = MagicMock()
    fake_resp.read.return_value = json.dumps(body_dict).encode()

    def _urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["payload"] = json.loads(req.data.decode())
        captured["headers"] = dict(req.headers)
        return fake_resp

    return patch.object(urllib.request, "urlopen", _urlopen), captured


def test_anthropic_call_without_cache_sends_plain_system():
    ctx, captured = _patch_urlopen_with_body(_make_anthropic_response_body())
    with ctx:
        _anthropic_call("sys prompt", "user msg",
                        model="claude-sonnet-4-6", temperature=0.0,
                        max_tokens=512, timeout=30, api_key="test-key")
    assert captured["payload"]["system"] == "sys prompt"
    assert captured["payload"]["messages"] == [{"role": "user", "content": "user msg"}]


def test_anthropic_call_with_system_cache_rewrites_system_as_array():
    ctx, captured = _patch_urlopen_with_body(_make_anthropic_response_body())
    with ctx:
        _anthropic_call("sys prompt", "user msg",
                        model="claude-sonnet-4-6", temperature=0.0,
                        max_tokens=512, timeout=30, api_key="test-key",
                        cache_control="system")
    assert captured["payload"]["system"] == [
        {"type": "text", "text": "sys prompt", "cache_control": {"type": "ephemeral"}},
    ]
    # user still plain string
    assert captured["payload"]["messages"] == [{"role": "user", "content": "user msg"}]


def test_anthropic_call_with_system_plus_user_rewrites_both():
    ctx, captured = _patch_urlopen_with_body(_make_anthropic_response_body())
    with ctx:
        _anthropic_call("sys prompt", "user msg",
                        model="claude-sonnet-4-6", temperature=0.0,
                        max_tokens=512, timeout=30, api_key="test-key",
                        cache_control="system+user", cache_ttl="1h")
    assert captured["payload"]["system"][0]["cache_control"] == {
        "type": "ephemeral", "ttl": "1h",
    }
    assert captured["payload"]["messages"][0]["content"] == [
        {"type": "text", "text": "user msg",
         "cache_control": {"type": "ephemeral", "ttl": "1h"}},
    ]


def test_anthropic_call_returns_cache_tokens_in_usage():
    ctx, _captured = _patch_urlopen_with_body(
        _make_anthropic_response_body(cache_read=400, cache_creation=200),
    )
    with ctx:
        _content, _model, usage = _anthropic_call(
            "sys prompt", "user msg",
            model="claude-sonnet-4-6", temperature=0.0,
            max_tokens=512, timeout=30, api_key="test-key",
        )
    assert usage["cache_read_input_tokens"] == 400
    assert usage["cache_creation_input_tokens"] == 200


# ---------------------------------------------------------------------------
# cache_control threads through _legacy_call
# ---------------------------------------------------------------------------

def _make_legacy_response_body(prompt_tokens=100, completion_tokens=50,
                               cache_read=0, cache_creation=0):
    return {
        "choices": [{"message": {"content": "test response"}}],
        "model": "claude-sonnet-4-6",
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cache_read_input_tokens": cache_read,
            "cache_creation_input_tokens": cache_creation,
        },
    }


def test_legacy_call_with_cache_rewrites_messages_with_content_blocks():
    ctx, captured = _patch_urlopen_with_body(_make_legacy_response_body())
    with ctx:
        _legacy_call("sys prompt", "user msg",
                     model="claude-sonnet-4-6", temperature=0.0,
                     max_tokens=512, timeout=30,
                     base_url="http://localhost:4000/v1", api_key="test-key",
                     cache_control="system+user")
    sys_msg = captured["payload"]["messages"][0]
    assert sys_msg["content"][0]["cache_control"] == {"type": "ephemeral"}
    user_msg = captured["payload"]["messages"][1]
    assert user_msg["content"][0]["text"] == "user msg"


def test_legacy_call_returns_cache_tokens_in_usage():
    ctx, _captured = _patch_urlopen_with_body(
        _make_legacy_response_body(cache_read=300, cache_creation=150),
    )
    with ctx:
        _content, _model, usage = _legacy_call(
            "sys prompt", "user msg",
            model="claude-sonnet-4-6", temperature=0.0,
            max_tokens=512, timeout=30,
            base_url="http://localhost:4000/v1", api_key="test-key",
        )
    assert usage["cache_read_input_tokens"] == 300
    assert usage["cache_creation_input_tokens"] == 150


# ---------------------------------------------------------------------------
# BUILDOS_CACHE_DISABLE strips markers at the payload boundary
# ---------------------------------------------------------------------------

def test_disable_flag_strips_markers_from_sdk_call(monkeypatch):
    """With BUILDOS_CACHE_DISABLE=1, _sdk_call sends plain strings even when
    cache_control='system+user' is passed — byte-identical to pre-caching."""
    monkeypatch.setenv("BUILDOS_CACHE_DISABLE", "1")
    captured = {}
    with patch("openai.OpenAI") as mock_openai_cls:
        client = mock_openai_cls.return_value
        def capture(**kwargs):
            captured.update(kwargs)
            return _make_sdk_response()
        client.chat.completions.create.side_effect = capture

        _sdk_call("sys prompt", "user msg",
                  model="claude-sonnet-4-6", temperature=0.0,
                  max_tokens=512, timeout=30,
                  base_url="http://localhost:4000/v1", api_key="test-key",
                  cache_control="system+user", cache_ttl="1h")

    # Plain-string messages, no cache_control markers anywhere
    assert captured["messages"][0] == {"role": "system", "content": "sys prompt"}
    assert captured["messages"][1] == {"role": "user", "content": "user msg"}
    payload_str = json.dumps(captured["messages"])
    assert "cache_control" not in payload_str


def test_disable_flag_strips_markers_from_anthropic_call(monkeypatch):
    monkeypatch.setenv("BUILDOS_CACHE_DISABLE", "1")
    ctx, captured = _patch_urlopen_with_body(_make_anthropic_response_body())
    with ctx:
        _anthropic_call("sys prompt", "user msg",
                        model="claude-sonnet-4-6", temperature=0.0,
                        max_tokens=512, timeout=30, api_key="test-key",
                        cache_control="system+user", cache_ttl="5m")
    # system stays as a plain string, not an array
    assert captured["payload"]["system"] == "sys prompt"
    assert captured["payload"]["messages"] == [{"role": "user", "content": "user msg"}]
    assert "cache_control" not in json.dumps(captured["payload"])


def test_disable_flag_strips_markers_from_legacy_call(monkeypatch):
    """BUILDOS_CACHE_DISABLE=1 must strip markers on the urllib legacy path too."""
    monkeypatch.setenv("BUILDOS_CACHE_DISABLE", "1")
    ctx, captured = _patch_urlopen_with_body(_make_legacy_response_body())
    with ctx:
        _legacy_call("sys prompt", "user msg",
                     model="claude-sonnet-4-6", temperature=0.0,
                     max_tokens=512, timeout=30,
                     base_url="http://localhost:4000/v1", api_key="test-key",
                     cache_control="system+user")

    # Plain-string messages, no cache_control markers anywhere
    assert captured["payload"]["messages"][0] == {"role": "system", "content": "sys prompt"}
    assert captured["payload"]["messages"][1] == {"role": "user", "content": "user msg"}
    assert "cache_control" not in json.dumps(captured["payload"])


def test_disable_flag_strips_markers_from_tool_loop(monkeypatch):
    """BUILDOS_CACHE_DISABLE=1 must strip markers on turn-0 messages in llm_tool_loop.

    llm_tool_loop builds messages[0] (system) and messages[1] (user) once before
    entering the per-turn loop. When the disable flag is set, those initial
    messages must stay as plain-string content blocks — byte-identical to
    pre-caching behavior.
    """
    from llm_client import llm_tool_loop

    monkeypatch.setenv("BUILDOS_CACHE_DISABLE", "1")
    monkeypatch.setenv("LITELLM_MASTER_KEY", "test-key")

    captured = {}

    def _capture_tool_call(client, messages, tools, model, temperature,
                           max_tokens, timeout, tool_choice=None):
        captured["messages"] = list(messages)
        return {
            "message": {"role": "assistant", "content": "done"},
            "usage": {"prompt_tokens": 100, "completion_tokens": 20,
                      "total_tokens": 120,
                      "cache_read_input_tokens": 0,
                      "cache_creation_input_tokens": 0},
        }

    with patch("llm_client._sdk_tool_call", side_effect=_capture_tool_call), \
         patch("openai.OpenAI"):
        llm_tool_loop(
            "sys prompt", "user msg",
            tools=[{"type": "function",
                    "function": {"name": "noop", "parameters": {}}}],
            tool_executor=lambda n, a: "{}",
            model="claude-sonnet-4-6",
            max_turns=1, max_tokens=64, timeout=10,
            base_url="http://localhost:4000/v1", api_key="test-key",
            cache_control="system+user",
        )

    assert captured["messages"][0] == {"role": "system", "content": "sys prompt"}
    assert captured["messages"][1] == {"role": "user", "content": "user msg"}
    assert "cache_control" not in json.dumps(captured["messages"])


# ---------------------------------------------------------------------------
# debate_common: cache tokens flow through cost tracking + logging
# ---------------------------------------------------------------------------

def _reset_session_costs():
    """Reset the module-local session cost accumulator."""
    with debate_common._session_costs_lock:
        debate_common._session_costs["total_usd"] = 0.0
        debate_common._session_costs["calls"] = 0
        debate_common._session_costs["by_model"] = {}


def test_track_cost_initializes_cache_fields_to_zero():
    _reset_session_costs()
    debate_common._track_cost("claude-sonnet-4-6",
                              {"prompt_tokens": 100, "completion_tokens": 50}, 0.001)
    entry = debate_common.get_session_costs()["by_model"]["claude-sonnet-4-6"]
    assert entry["cache_read_input_tokens"] == 0
    assert entry["cache_creation_input_tokens"] == 0


def test_track_cost_accumulates_cache_fields():
    _reset_session_costs()
    debate_common._track_cost("claude-sonnet-4-6", {
        "prompt_tokens": 100, "completion_tokens": 50,
        "cache_read_input_tokens": 500,
        "cache_creation_input_tokens": 200,
    }, 0.001)
    debate_common._track_cost("claude-sonnet-4-6", {
        "prompt_tokens": 80, "completion_tokens": 40,
        "cache_read_input_tokens": 300,
        "cache_creation_input_tokens": 0,
    }, 0.0005)
    entry = debate_common.get_session_costs()["by_model"]["claude-sonnet-4-6"]
    assert entry["cache_read_input_tokens"] == 800
    assert entry["cache_creation_input_tokens"] == 200


def test_cost_delta_since_captures_cache_fields():
    _reset_session_costs()
    debate_common._track_cost("claude-sonnet-4-6", {
        "prompt_tokens": 100, "completion_tokens": 50,
        "cache_read_input_tokens": 500,
        "cache_creation_input_tokens": 200,
    }, 0.001)
    snap = debate_common.get_session_costs()

    # Second call, different cache usage
    debate_common._track_cost("claude-sonnet-4-6", {
        "prompt_tokens": 80, "completion_tokens": 40,
        "cache_read_input_tokens": 1000,
        "cache_creation_input_tokens": 0,
    }, 0.0005)

    delta = debate_common._cost_delta_since(snap)
    model_delta = delta["by_model"]["claude-sonnet-4-6"]
    assert model_delta["cache_read_input_tokens"] == 1000
    assert model_delta["cache_creation_input_tokens"] == 0
    assert model_delta["prompt_tokens"] == 80


def test_log_debate_event_includes_cache_fields(tmp_path):
    """_log_debate_event persists cache token deltas through cost_snapshot."""
    _reset_session_costs()
    snap = debate_common.get_session_costs()
    debate_common._track_cost("claude-sonnet-4-6", {
        "prompt_tokens": 100, "completion_tokens": 50,
        "cache_read_input_tokens": 500,
        "cache_creation_input_tokens": 200,
    }, 0.001)

    log_path = tmp_path / "debate-log.jsonl"
    debate_common._log_debate_event(
        {"phase": "test", "debate_id": "test-123"},
        log_path=str(log_path),
        cost_snapshot=snap,
    )

    assert log_path.exists()
    entry = json.loads(log_path.read_text().strip())
    model_costs = entry["costs"]["by_model"]["claude-sonnet-4-6"]
    assert model_costs["cache_read_input_tokens"] == 500
    assert model_costs["cache_creation_input_tokens"] == 200


def test_log_debate_event_zero_cache_when_usage_lacks_keys(tmp_path):
    """Backward compat: usage dict without cache keys logs 0."""
    _reset_session_costs()
    snap = debate_common.get_session_costs()
    debate_common._track_cost("gpt-5.4",
                              {"prompt_tokens": 200, "completion_tokens": 80}, 0.002)

    log_path = tmp_path / "debate-log.jsonl"
    debate_common._log_debate_event(
        {"phase": "test", "debate_id": "test-456"},
        log_path=str(log_path),
        cost_snapshot=snap,
    )

    entry = json.loads(log_path.read_text().strip())
    model_costs = entry["costs"]["by_model"]["gpt-5.4"]
    assert model_costs["cache_read_input_tokens"] == 0
    assert model_costs["cache_creation_input_tokens"] == 0
    assert model_costs["prompt_tokens"] == 200


# ---------------------------------------------------------------------------
# Component 3b — cache-aware cost pricing in _estimate_cost
# Verified against LiteLLM double-count behavior (prompt_tokens sums
# input_tokens + cache_read + cache_creation). See smoke-test results.
# ---------------------------------------------------------------------------

def test_estimate_cost_no_cache_keys_backward_compat():
    """When usage has no cache keys, cost math matches pre-caching behavior."""
    # Sonnet: $3/MTok input, $15/MTok output. 1M prompt + 1M completion = $18.
    usage = {"prompt_tokens": 1_000_000, "completion_tokens": 1_000_000}
    cost = debate_common._estimate_cost("claude-sonnet-4-6", usage)
    assert cost == 18.0


def test_estimate_cost_prices_cache_reads_at_01x_base():
    """cache_read_input_tokens priced at 0.1x base input rate.

    prompt_tokens includes the cache tokens (LiteLLM double-count). The cost
    function must subtract them before applying base input price.
    Sonnet input $3/M. 1M prompt, 900K of it cache_read, 0 completion:
      base_tokens = 100K (100K * 3/M = $0.30)
      cache_read = 900K * 3/M * 0.1 = $0.27
      Total = $0.57
    """
    usage = {
        "prompt_tokens": 1_000_000,
        "cache_read_input_tokens": 900_000,
        "cache_creation_input_tokens": 0,
        "completion_tokens": 0,
    }
    cost = debate_common._estimate_cost("claude-sonnet-4-6", usage)
    assert cost == 0.57


def test_estimate_cost_prices_cache_creation_at_125x_base():
    """cache_creation_input_tokens priced at 1.25x base (5-min TTL).

    Sonnet input $3/M. 1M prompt, 800K of it cache_creation, 0 completion:
      base_tokens = 200K (200K * 3/M = $0.60)
      cache_creation = 800K * 3/M * 1.25 = $3.00
      Total = $3.60
    """
    usage = {
        "prompt_tokens": 1_000_000,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 800_000,
        "completion_tokens": 0,
    }
    cost = debate_common._estimate_cost("claude-sonnet-4-6", usage)
    assert cost == 3.60


def test_estimate_cost_mixed_cache_read_and_creation():
    """All three pools present — each priced at its own multiplier."""
    # Opus input $15/M, output $75/M.
    # prompt_tokens = 1M, cache_read = 400K, cache_creation = 500K, completion = 100K
    #   base_tokens = 100K (100K * 15/M = $1.50)
    #   cache_read = 400K * 15/M * 0.1 = $0.60
    #   cache_creation = 500K * 15/M * 1.25 = $9.375
    #   completion = 100K * 75/M = $7.50
    #   total = $18.975
    usage = {
        "prompt_tokens": 1_000_000,
        "cache_read_input_tokens": 400_000,
        "cache_creation_input_tokens": 500_000,
        "completion_tokens": 100_000,
    }
    cost = debate_common._estimate_cost("claude-opus-4-7", usage)
    assert cost == 18.975


def test_estimate_cost_matches_smoke_test_run_2_case():
    """Real smoke-test numbers: run 2 of Component 4a (cache hit).

    Sonnet, prompt_tokens=4898, cache_read=4895, completion=54.
    base_tokens = 3
    cost = 3 * 3/M + 4895 * 3/M * 0.1 + 54 * 15/M
         = 0.000009 + 0.0014685 + 0.00081
         = 0.0022875 ≈ 0.002288
    """
    usage = {
        "prompt_tokens": 4898,
        "cache_read_input_tokens": 4895,
        "cache_creation_input_tokens": 0,
        "completion_tokens": 54,
    }
    cost = debate_common._estimate_cost("claude-sonnet-4-6", usage)
    assert abs(cost - 0.002288) < 1e-6


def test_estimate_cost_matches_smoke_test_run_1_case():
    """Real smoke-test numbers: run 1 (cache write).

    Sonnet, prompt_tokens=4898, cache_creation=4895, completion=46.
    base_tokens = 3
    cost = 3 * 3/M + 4895 * 3/M * 1.25 + 46 * 15/M
         = 0.000009 + 0.01835625 + 0.00069
         = 0.01905525 ≈ 0.019055
    """
    usage = {
        "prompt_tokens": 4898,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 4895,
        "completion_tokens": 46,
    }
    cost = debate_common._estimate_cost("claude-sonnet-4-6", usage)
    assert abs(cost - 0.019055) < 1e-6


def test_estimate_cost_clamps_when_prompt_tokens_below_cache_pools():
    """Defensive: if a provider eventually reports prompt_tokens without
    cache tokens summed in, base_input_tokens would go negative. Clamp to 0.
    """
    # Hypothetical Anthropic-native response where prompt_tokens excludes cache:
    # prompt_tokens=3 (base only), cache_read=4895. Subtraction gives -4892.
    usage = {
        "prompt_tokens": 3,
        "cache_read_input_tokens": 4895,
        "cache_creation_input_tokens": 0,
        "completion_tokens": 0,
    }
    cost = debate_common._estimate_cost("claude-sonnet-4-6", usage)
    # Expected (clamped): 0 * 3/M + 4895 * 3/M * 0.1 = 0.0014685
    # Python round() uses banker's rounding → 0.001468 at 6 decimals.
    assert cost == 0.001468


def test_estimate_cost_unknown_model_returns_zero():
    """Backward compat: unknown model prefix returns 0 cost."""
    usage = {"prompt_tokens": 1000, "completion_tokens": 500,
             "cache_read_input_tokens": 500}
    assert debate_common._estimate_cost("unknown-model-9000", usage) == 0.0


def test_estimate_cost_empty_usage_returns_zero():
    """Backward compat: empty usage dict returns 0 cost."""
    assert debate_common._estimate_cost("claude-sonnet-4-6", {}) == 0.0


def test_estimate_cost_ignores_cache_fields_on_gpt():
    """GPT models: cache fields in usage are ignored (Anthropic-specific).

    If LiteLLM ever surfaces OpenAI cache counters via the same field names,
    pricing them at Anthropic's 0.1x read / 1.25x write rates would misbill.
    Phase 0 guards this by restricting the cache math to claude-* prefixes.
    """
    # GPT-5.4: input $2.50/M, output $10/M. 1M prompt, 500K cache_read (ignored),
    # 100K completion. Expected: 1M * 2.50/M + 100K * 10/M = $2.50 + $1.00 = $3.50.
    usage = {
        "prompt_tokens": 1_000_000,
        "cache_read_input_tokens": 500_000,
        "cache_creation_input_tokens": 0,
        "completion_tokens": 100_000,
    }
    cost = debate_common._estimate_cost("gpt-5.4", usage)
    assert cost == 3.50


def test_estimate_cost_ignores_cache_fields_on_gemini():
    """Gemini: cache fields in usage are ignored (Anthropic-specific rates)."""
    # Gemini 3.1 Pro: input $1.25/M, output $10/M. 1M prompt, 800K cache_creation
    # (ignored), 50K completion. Expected: 1M * 1.25/M + 50K * 10/M = $1.25 + $0.50.
    usage = {
        "prompt_tokens": 1_000_000,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 800_000,
        "completion_tokens": 50_000,
    }
    cost = debate_common._estimate_cost("gemini-3.1-pro", usage)
    assert cost == 1.75

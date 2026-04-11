"""Tests for scripts/managed_agent.py.

Covers dispatch, poll, validate, and fallback paths with mocked MA API.
No live API calls — all Anthropic SDK interactions are mocked.

Run with: python3.11 -m pytest tests/test_managed_agent.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# Mock anthropic before importing managed_agent
mock_anthropic = MagicMock()
mock_anthropic.APIError = type("APIError", (Exception,), {})
mock_anthropic.APIConnectionError = type("APIConnectionError", (Exception,), {})
mock_anthropic.APITimeoutError = type("APITimeoutError", (Exception,), {})
sys.modules["anthropic"] = mock_anthropic

# Force fresh import
if "managed_agent" in sys.modules:
    del sys.modules["managed_agent"]
import managed_agent


# ── validate_result tests ────────────────────────────────────────────────────


class TestValidateResult:
    def test_valid_result(self):
        body = "1. Finding one\n2. Finding two\n3. Finding three"
        text, stats = managed_agent.validate_result(body, len(body) * 3)
        assert text == body
        assert stats["consolidated_findings"] == 3
        assert stats["source"] == "managed-agent"

    def test_empty_result_raises(self):
        with pytest.raises(ValueError, match="empty"):
            managed_agent.validate_result("", 1000)

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            managed_agent.validate_result("   \n  ", 1000)

    def test_oversized_result_raises(self):
        body = "x" * 1001
        with pytest.raises(ValueError, match="too large"):
            managed_agent.validate_result(body, 1000)

    def test_exactly_at_limit(self):
        body = "1. Finding\n"
        text, stats = managed_agent.validate_result(body, len(body))
        assert text == body

    def test_one_over_limit_raises(self):
        body = "1. Finding\n"
        with pytest.raises(ValueError, match="too large"):
            managed_agent.validate_result(body, len(body) - 1)

    def test_stats_model_field(self):
        _, stats = managed_agent.validate_result("1. Test", 1000)
        assert "model" in stats
        assert stats["model"] == managed_agent.CONSOLIDATION_MODEL


# ── dispatch_task tests ──────────────────────────────────────────────────────


class TestDispatchTask:
    def _make_mock_client(self):
        client = MagicMock()
        agent = MagicMock()
        agent.id = "agent-123"
        agent.version = 1
        agent.name = managed_agent.CONSOLIDATION_AGENT_NAME
        client.beta.agents.create.return_value = agent

        env = MagicMock()
        env.id = "env-456"
        client.beta.environments.create.return_value = env

        session = MagicMock()
        session.id = "session-789"
        client.beta.sessions.create.return_value = session

        return client

    @patch.object(managed_agent, "_get_client")
    def test_dispatch_success(self, mock_get_client):
        client = self._make_mock_client()
        mock_get_client.return_value = client

        result_client, session_id, lifecycle = managed_agent.dispatch_task(
            payload="test prompt",
            metadata={"debate_id": "test", "system_prompt": "Be helpful"},
            api_key="test-key",
        )

        assert session_id == "session-789"
        assert result_client is client
        assert lifecycle["session_id"] == "session-789"
        assert lifecycle["env_id"] == "env-456"
        assert "dispatch_time_s" in lifecycle
        client.beta.agents.create.assert_called_once()
        client.beta.environments.create.assert_called_once()
        client.beta.sessions.create.assert_called_once()
        client.beta.sessions.events.send.assert_called_once()

    @patch.object(managed_agent, "_get_client")
    def test_dispatch_sends_correct_payload(self, mock_get_client):
        client = self._make_mock_client()
        mock_get_client.return_value = client

        managed_agent.dispatch_task(
            payload="my consolidation prompt",
            metadata={"debate_id": "d1", "system_prompt": "sys"},
            api_key="key",
        )

        send_call = client.beta.sessions.events.send.call_args
        events = send_call.kwargs.get("events") or send_call[1].get("events")
        assert events[0]["type"] == "user.message"
        assert events[0]["content"][0]["text"] == "my consolidation prompt"

    @patch.object(managed_agent, "_get_client")
    def test_dispatch_no_sdk_raises(self, mock_get_client):
        mock_get_client.side_effect = RuntimeError("anthropic SDK is not installed")
        with pytest.raises(RuntimeError, match="SDK"):
            managed_agent.dispatch_task("p", {}, "k")

    @patch.object(managed_agent, "_get_client")
    def test_dispatch_caches_agent_in_module(self, mock_get_client):
        """Agent ID is cached in module-level variable after creation."""
        client = self._make_mock_client()
        mock_get_client.return_value = client

        managed_agent._cached_agent = None
        managed_agent.dispatch_task("p", {"system_prompt": "s"}, "k")
        assert managed_agent._cached_agent is not None
        assert managed_agent._cached_agent[0] == "agent-123"

        # Cleanup
        managed_agent._cached_agent = None


# ── poll_task tests ──────────────────────────────────────────────────────────


class TestPollTask:
    def _make_event(self, event_type, text=None, stop_reason=None, usage=None):
        event = MagicMock()
        event.type = event_type
        if text and event_type == "assistant.message":
            block = MagicMock()
            block.text = text
            event.content = [block]
        else:
            event.content = []
        if stop_reason:
            event.stop_reason = MagicMock()
            event.stop_reason.type = stop_reason
        if usage:
            event.usage = MagicMock()
            event.usage.input_tokens = usage.get("input_tokens", 0)
            event.usage.output_tokens = usage.get("output_tokens", 0)
        else:
            event.usage = None
        return event

    def test_poll_collects_text(self):
        client = MagicMock()
        events = [
            self._make_event("assistant.message", text="Part 1"),
            self._make_event("assistant.message", text="Part 2"),
            self._make_event("session.status_idle"),
        ]
        stream_ctx = MagicMock()
        stream_ctx.__enter__ = MagicMock(return_value=iter(events))
        stream_ctx.__exit__ = MagicMock(return_value=False)
        client.beta.sessions.events.stream.return_value = stream_ctx

        result, usage = managed_agent.poll_task(client, "sess-1", timeout_s=60)
        assert "Part 1" in result
        assert "Part 2" in result
        assert "model" in usage

    def test_poll_collects_usage(self):
        client = MagicMock()
        events = [
            self._make_event("assistant.message", text="Hi",
                             usage={"input_tokens": 100, "output_tokens": 50}),
            self._make_event("session.status_idle"),
        ]
        stream_ctx = MagicMock()
        stream_ctx.__enter__ = MagicMock(return_value=iter(events))
        stream_ctx.__exit__ = MagicMock(return_value=False)
        client.beta.sessions.events.stream.return_value = stream_ctx

        _, usage = managed_agent.poll_task(client, "sess-1", timeout_s=60)
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50

    def test_poll_timeout(self):
        client = MagicMock()
        # Event that never goes idle
        event = self._make_event("assistant.message", text="working...")
        infinite_events = [event] * 100

        stream_ctx = MagicMock()
        stream_ctx.__enter__ = MagicMock(return_value=iter(infinite_events))
        stream_ctx.__exit__ = MagicMock(return_value=False)
        client.beta.sessions.events.stream.return_value = stream_ctx

        # Use a timeout of 0 to force immediate timeout
        with patch("managed_agent.time") as mock_time:
            mock_time.monotonic.side_effect = [0, 0, 999]  # start, deadline check -> expired
            with pytest.raises(TimeoutError):
                managed_agent.poll_task(client, "sess-1", timeout_s=1)

    def test_poll_empty_session(self):
        client = MagicMock()
        events = [self._make_event("session.status_idle")]
        stream_ctx = MagicMock()
        stream_ctx.__enter__ = MagicMock(return_value=iter(events))
        stream_ctx.__exit__ = MagicMock(return_value=False)
        client.beta.sessions.events.stream.return_value = stream_ctx

        result, usage = managed_agent.poll_task(client, "sess-1", timeout_s=60)
        assert result == ""


# ── run_consolidation integration tests ──────────────────────────────────────


class TestRunConsolidation:
    @patch.object(managed_agent, "dispatch_task")
    @patch.object(managed_agent, "poll_task")
    @patch.object(managed_agent, "_cleanup_environment")
    def test_success_path(self, mock_cleanup, mock_poll, mock_dispatch):
        lifecycle = {
            "dispatch_time_s": 1.0, "agent_retries": 0,
            "session_retries": 0, "agent_id": "a1",
            "env_id": "e1", "session_id": "s1",
        }
        mock_dispatch.return_value = (MagicMock(), "sess-1", lifecycle)
        mock_poll.return_value = (
            "1. Consolidated finding A\n2. Consolidated finding B",
            {"input_tokens": 100, "output_tokens": 50, "model": "claude-sonnet-4-6"},
        )

        body = "## Challenger A\n1. Issue\n## Challenger B\n1. Same issue"
        result, stats = managed_agent.run_consolidation(
            challenge_body=body,
            system_prompt="Consolidate",
            debate_id="test-debate",
            api_key="test-key",
        )

        assert "Consolidated finding" in result
        assert stats["consolidated_findings"] == 2
        assert stats["source"] == "managed-agent"
        assert stats["raw_findings"] == 2  # 2 numbered items in input
        assert stats["challengers"] == 2
        assert "usage" in stats
        assert "lifecycle" in stats
        mock_cleanup.assert_called_once()

    @patch.object(managed_agent, "dispatch_task")
    def test_dispatch_failure_propagates(self, mock_dispatch):
        mock_dispatch.side_effect = ConnectionError("network down")

        body = "## Challenger A\n1. X\n## Challenger B\n1. Y"
        with pytest.raises(ConnectionError):
            managed_agent.run_consolidation(body, "sys", "d1", "key")

    @patch.object(managed_agent, "dispatch_task")
    @patch.object(managed_agent, "poll_task")
    @patch.object(managed_agent, "_cleanup_environment")
    def test_empty_result_raises_valueerror(self, mock_cleanup, mock_poll, mock_dispatch):
        lifecycle = {
            "dispatch_time_s": 1.0, "agent_retries": 0,
            "session_retries": 0, "agent_id": "a1",
            "env_id": "e1", "session_id": "s1",
        }
        mock_dispatch.return_value = (MagicMock(), "sess-1", lifecycle)
        mock_poll.return_value = ("", {"input_tokens": 0, "output_tokens": 0, "model": "claude-sonnet-4-6"})

        body = "## Challenger A\n1. X\n## Challenger B\n1. Y"
        with pytest.raises(ValueError, match="empty"):
            managed_agent.run_consolidation(body, "sys", "d1", "key")
        # Cleanup still called even on failure
        mock_cleanup.assert_called_once()

    @patch.object(managed_agent, "dispatch_task")
    @patch.object(managed_agent, "poll_task")
    @patch.object(managed_agent, "_cleanup_environment")
    def test_oversized_result_raises(self, mock_cleanup, mock_poll, mock_dispatch):
        lifecycle = {
            "dispatch_time_s": 1.0, "agent_retries": 0,
            "session_retries": 0, "agent_id": "a1",
            "env_id": "e1", "session_id": "s1",
        }
        mock_dispatch.return_value = (MagicMock(), "sess-1", lifecycle)
        body = "## Challenger A\n1. X\n## Challenger B\n1. Y"
        # Return something > 2x the input
        mock_poll.return_value = (
            "x" * (len(body) * 2 + 1),
            {"input_tokens": 100, "output_tokens": 500, "model": "claude-sonnet-4-6"},
        )

        with pytest.raises(ValueError, match="too large"):
            managed_agent.run_consolidation(body, "sys", "d1", "key")


# ── retry logic tests ───────────────────────────────────────────────────────


class TestRetryTransient:
    def test_succeeds_on_first_try(self):
        fn = MagicMock(return_value="ok")
        result, retries = managed_agent._retry_transient(fn, retries=3, backoff=0.01)
        assert result == "ok"
        assert retries == 0
        assert fn.call_count == 1

    def test_retries_on_transient_then_succeeds(self):
        fn = MagicMock(side_effect=[ConnectionError("fail"), "ok"])
        result, retries = managed_agent._retry_transient(fn, retries=3, backoff=0.01)
        assert result == "ok"
        assert retries == 1
        assert fn.call_count == 2

    def test_exhausts_retries(self):
        fn = MagicMock(side_effect=ConnectionError("always fails"))
        with pytest.raises(ConnectionError):
            managed_agent._retry_transient(fn, retries=3, backoff=0.01)
        assert fn.call_count == 3


# ── MA_SAFE_EXCEPTIONS tests ────────────────────────────────────────────────


class TestMaSafeExceptions:
    def test_contains_base_exceptions(self):
        assert ConnectionError in managed_agent.MA_SAFE_EXCEPTIONS
        assert TimeoutError in managed_agent.MA_SAFE_EXCEPTIONS
        assert OSError in managed_agent.MA_SAFE_EXCEPTIONS

    def test_contains_anthropic_exceptions(self):
        # These come from the mocked anthropic module
        assert mock_anthropic.APIError in managed_agent.MA_SAFE_EXCEPTIONS
        assert mock_anthropic.APIConnectionError in managed_agent.MA_SAFE_EXCEPTIONS
        assert mock_anthropic.APITimeoutError in managed_agent.MA_SAFE_EXCEPTIONS


# ── cleanup tests ────────────────────────────────────────────────────────────


class TestCleanup:
    def test_cleanup_calls_delete(self):
        client = MagicMock()
        managed_agent._cleanup_environment(client, "env-123")
        client.beta.environments.delete.assert_called_once_with("env-123")

    def test_cleanup_no_env_id_skips(self):
        client = MagicMock()
        managed_agent._cleanup_environment(client, None)
        client.beta.environments.delete.assert_not_called()

    def test_cleanup_swallows_errors(self):
        client = MagicMock()
        client.beta.environments.delete.side_effect = Exception("delete failed")
        # Should not raise
        managed_agent._cleanup_environment(client, "env-123")


# ── _find_or_create_agent tests ──────────────────────────────────────────────


class TestFindOrCreateAgent:
    def test_cached_agent_prompt_change_creates_new(self):
        """If cached agent has different prompt hash, create a fresh one."""
        client = MagicMock()

        # New agent
        new_agent = MagicMock()
        new_agent.id = "new-agent-id"
        new_agent.version = 1
        client.beta.agents.create.return_value = new_agent

        # Cache with a different prompt hash
        managed_agent._cached_agent = ("old-id", 1, "different-hash")
        try:
            agent_id, version = managed_agent._find_or_create_agent(client, "sys prompt")
            assert agent_id == "new-agent-id"
            client.beta.agents.create.assert_called_once()
        finally:
            managed_agent._cached_agent = None

    def test_cached_agent_same_prompt_reuses(self):
        """If cached agent has same prompt hash, reuse it."""
        client = MagicMock()

        # Cached agent with matching name
        cached_agent = MagicMock()
        cached_agent.id = "cached-id"
        cached_agent.version = 2
        cached_agent.name = managed_agent.CONSOLIDATION_AGENT_NAME
        client.beta.agents.retrieve.return_value = cached_agent

        prompt = "sys prompt"
        prompt_hash = managed_agent._prompt_hash(prompt)
        managed_agent._cached_agent = ("cached-id", 2, prompt_hash)
        try:
            agent_id, version = managed_agent._find_or_create_agent(client, prompt)
            assert agent_id == "cached-id"
            client.beta.agents.create.assert_not_called()
        finally:
            managed_agent._cached_agent = None

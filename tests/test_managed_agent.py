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

        result_client, session_id = managed_agent.dispatch_task(
            payload="test prompt",
            metadata={"debate_id": "test", "system_prompt": "Be helpful"},
            api_key="test-key",
        )

        assert session_id == "session-789"
        assert result_client is client
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


# ── poll_task tests ──────────────────────────────────────────────────────────


class TestPollTask:
    def _make_event(self, event_type, text=None, stop_reason=None):
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

        result = managed_agent.poll_task(client, "sess-1", timeout_s=60)
        assert "Part 1" in result
        assert "Part 2" in result

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

        result = managed_agent.poll_task(client, "sess-1", timeout_s=60)
        assert result == ""


# ── run_consolidation integration tests ──────────────────────────────────────


class TestRunConsolidation:
    @patch.object(managed_agent, "dispatch_task")
    @patch.object(managed_agent, "poll_task")
    def test_success_path(self, mock_poll, mock_dispatch):
        mock_dispatch.return_value = (MagicMock(), "sess-1")
        mock_poll.return_value = "1. Consolidated finding A\n2. Consolidated finding B"

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

    @patch.object(managed_agent, "dispatch_task")
    def test_dispatch_failure_propagates(self, mock_dispatch):
        mock_dispatch.side_effect = ConnectionError("network down")

        body = "## Challenger A\n1. X\n## Challenger B\n1. Y"
        with pytest.raises(ConnectionError):
            managed_agent.run_consolidation(body, "sys", "d1", "key")

    @patch.object(managed_agent, "dispatch_task")
    @patch.object(managed_agent, "poll_task")
    def test_empty_result_raises_valueerror(self, mock_poll, mock_dispatch):
        mock_dispatch.return_value = (MagicMock(), "sess-1")
        mock_poll.return_value = ""

        body = "## Challenger A\n1. X\n## Challenger B\n1. Y"
        with pytest.raises(ValueError, match="empty"):
            managed_agent.run_consolidation(body, "sys", "d1", "key")

    @patch.object(managed_agent, "dispatch_task")
    @patch.object(managed_agent, "poll_task")
    def test_oversized_result_raises(self, mock_poll, mock_dispatch):
        mock_dispatch.return_value = (MagicMock(), "sess-1")
        body = "## Challenger A\n1. X\n## Challenger B\n1. Y"
        # Return something > 2x the input
        mock_poll.return_value = "x" * (len(body) * 2 + 1)

        with pytest.raises(ValueError, match="too large"):
            managed_agent.run_consolidation(body, "sys", "d1", "key")


# ── retry logic tests ───────────────────────────────────────────────────────


class TestRetryTransient:
    def test_succeeds_on_first_try(self):
        fn = MagicMock(return_value="ok")
        result = managed_agent._retry_transient(fn, retries=3, backoff=0.01)
        assert result == "ok"
        assert fn.call_count == 1

    def test_retries_on_transient_then_succeeds(self):
        fn = MagicMock(side_effect=[ConnectionError("fail"), "ok"])
        result = managed_agent._retry_transient(fn, retries=3, backoff=0.01)
        assert result == "ok"
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

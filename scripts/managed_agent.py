"""Managed Agents client for BuildOS.

Thin transport/validation layer for dispatching Claude-only tasks to
Anthropic's Managed Agents API. Phase 1 target: consolidation step in
debate.py (``_consolidate_challenges``).

Design: tasks/managed-agents-dispatch-refined.md
"""

import json
import os
import sys
import time
import traceback

# Anthropic SDK is optional — module can be imported even without it
# (dispatch_task will raise at call time if missing).
try:
    import anthropic
except ImportError:
    anthropic = None


# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_TIMEOUT_S = 300  # 5 minutes for consolidation
MAX_RETRIES = 3
INITIAL_BACKOFF_S = 2.0

# Agent config for consolidation. Created once, reused across sessions.
CONSOLIDATION_AGENT_NAME = "buildos-consolidation-v1"
CONSOLIDATION_MODEL = "claude-sonnet-4-6"

# Exceptions that are safe to catch and retry or fall back from.
# Mirrors LLM_SAFE_EXCEPTIONS pattern in debate.py.
MA_SAFE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
)
if anthropic is not None:
    MA_SAFE_EXCEPTIONS = MA_SAFE_EXCEPTIONS + (
        anthropic.APIError,
        anthropic.APIConnectionError,
        anthropic.APITimeoutError,
    )


# ── Client helpers ───────────────────────────────────────────────────────────

def _get_client(api_key):
    """Create an Anthropic client. Raises RuntimeError if SDK missing."""
    if anthropic is None:
        raise RuntimeError("anthropic SDK is not installed")
    return anthropic.Anthropic(api_key=api_key)


def _retry_transient(fn, retries=MAX_RETRIES, backoff=INITIAL_BACKOFF_S):
    """Retry ``fn()`` on transient errors with exponential backoff."""
    last_error = None
    for attempt in range(retries):
        try:
            return fn()
        except MA_SAFE_EXCEPTIONS as e:
            last_error = e
            if attempt < retries - 1:
                wait = backoff * (2 ** attempt)
                print(f"  MA retry {attempt + 1}/{retries} after {wait:.1f}s: {e}",
                      file=sys.stderr)
                time.sleep(wait)
    raise last_error


# ── Core API ─────────────────────────────────────────────────────────────────

def _find_or_create_agent(client, system_prompt):
    """Find an existing consolidation agent or create one.

    Returns (agent_id, agent_version).
    """
    # Check for a cached agent ID in env (avoids creating duplicates)
    cached_id = os.environ.get("MA_AGENT_ID")
    if cached_id:
        try:
            agent = client.beta.agents.retrieve(cached_id)
            return agent.id, agent.version
        except Exception:
            pass  # stale ID, create fresh

    agent = client.beta.agents.create(
        name=CONSOLIDATION_AGENT_NAME,
        model=CONSOLIDATION_MODEL,
        system=system_prompt,
    )
    return agent.id, agent.version


def dispatch_task(payload, metadata, api_key):
    """Dispatch a consolidation task to Managed Agents.

    Args:
        payload: The prompt text to send (materialized challenge body).
        metadata: Dict with task context (debate_id, task_type, etc.).
        api_key: Anthropic API key for MA access.

    Returns:
        Tuple of (client, session_id) for polling.

    Raises:
        RuntimeError: If SDK is missing.
        MA_SAFE_EXCEPTIONS: On transient failures (after retries exhausted).
    """
    client = _get_client(api_key)

    system_prompt = metadata.get("system_prompt", "You are a helpful assistant.")

    agent_id, agent_version = _retry_transient(
        lambda: _find_or_create_agent(client, system_prompt)
    )

    print(f"  MA dispatch: agent={agent_id} v{agent_version}", file=sys.stderr)

    # Create environment + session
    def _create_session():
        env = client.beta.environments.create(
            name=f"consolidation-{metadata.get('debate_id', 'unknown')}",
        )
        session = client.beta.sessions.create(
            environment_id=env.id,
            agent={"type": "agent", "id": agent_id, "version": agent_version},
        )
        return session

    session = _retry_transient(_create_session)
    print(f"  MA session: {session.id}", file=sys.stderr)

    # Send the prompt
    client.beta.sessions.events.send(
        session.id,
        events=[{
            "type": "user.message",
            "content": [{"type": "text", "text": payload}],
        }],
    )

    return client, session.id


def poll_task(client, session_id, timeout_s=DEFAULT_TIMEOUT_S):
    """Poll/stream a session until it goes idle or times out.

    Args:
        client: Anthropic client instance (from dispatch_task).
        session_id: The session ID to poll.
        timeout_s: Maximum wall-clock seconds to wait.

    Returns:
        The concatenated text output from the agent.

    Raises:
        TimeoutError: If the session doesn't complete within timeout_s.
        MA_SAFE_EXCEPTIONS: On connection/API errors.
    """
    deadline = time.monotonic() + timeout_s
    collected_text = []

    with client.beta.sessions.events.stream(session_id) as stream:
        for event in stream:
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"MA session {session_id} did not complete within {timeout_s}s"
                )
            # Collect text from assistant messages
            if event.type == "assistant.message":
                if hasattr(event, "content") and event.content:
                    for block in event.content:
                        if hasattr(block, "text"):
                            collected_text.append(block.text)
            # Session idle = done
            if event.type == "session.status_idle":
                break

    return "\n".join(collected_text) if collected_text else ""


def validate_result(raw_result, expected_max_len):
    """Validate MA output against the consolidation contract.

    The result must match the return shape of ``_consolidate_challenges``:
    ``(consolidated_body, stats_dict)`` or ``(original_body, None)``.

    Args:
        raw_result: Text string returned by poll_task.
        expected_max_len: Maximum allowed length (typically 2x input length).

    Returns:
        (text_body, stats_dict_or_none) matching _consolidate_challenges shape.

    Raises:
        ValueError: If validation fails (empty, oversized, etc.).
    """
    if not raw_result or not raw_result.strip():
        raise ValueError("MA returned empty result")

    if len(raw_result) > expected_max_len:
        raise ValueError(
            f"MA result too large: {len(raw_result)} chars "
            f"(limit {expected_max_len})"
        )

    # Count consolidated findings for stats
    import re
    con_items = len(re.findall(r"^\d+\.\s+", raw_result, re.MULTILINE))

    stats = {
        "consolidated_findings": con_items,
        "model": CONSOLIDATION_MODEL,
        "source": "managed-agent",
    }

    return raw_result, stats


def run_consolidation(challenge_body, system_prompt, debate_id, api_key,
                      timeout_s=DEFAULT_TIMEOUT_S):
    """High-level: dispatch consolidation and return validated result.

    This is the main entry point for debate.py integration.

    Args:
        challenge_body: Raw multi-challenger text to consolidate.
        system_prompt: The consolidation system prompt.
        debate_id: Identifier for logging/tracing.
        api_key: Anthropic API key.
        timeout_s: Polling timeout.

    Returns:
        (consolidated_body, stats_dict) on success.

    Raises:
        MA_SAFE_EXCEPTIONS or ValueError on failure (caller should fall back).
    """
    metadata = {
        "debate_id": debate_id,
        "task_type": "consolidation",
        "system_prompt": system_prompt,
    }

    # Build the same user content that _consolidate_challenges builds
    import re
    challenger_count = len(re.findall(
        r"^## Challenger [A-Z]", challenge_body, re.MULTILINE
    ))
    user_content = (
        f"Here are the raw challenges from {challenger_count} "
        f"independent reviewers:\n\n{challenge_body}"
    )

    client, session_id = dispatch_task(user_content, metadata, api_key)
    raw_result = poll_task(client, session_id, timeout_s)
    return validate_result(raw_result, len(challenge_body) * 2)

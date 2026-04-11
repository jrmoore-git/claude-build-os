"""Managed Agents client for BuildOS.

Thin transport/validation layer for dispatching Claude-only tasks to
Anthropic's Managed Agents API. Phase 1 target: consolidation step in
debate.py (``_consolidate_challenges``).

Design: tasks/managed-agents-dispatch-refined.md

Provider Security Assumptions (rollout gate — spec requirement):
- Authentication: Anthropic API key (same as Messages API). Bearer token
  in Authorization header over TLS.
- Tenant isolation: Per-API-key isolation. Sessions are scoped to the
  authenticated organization. No cross-tenant data access.
- Data retention: Subject to Anthropic's data retention policy. As of
  Phase 1 launch, Anthropic does not train on API inputs/outputs by
  default (commercial API terms).
- Training on customer data: No, under standard commercial API terms.
  Verify current terms at anthropic.com/policies before production use.
- LiteLLM parity gaps (consciously waived in Phase 1):
  - No model aliasing (MA uses direct Anthropic model IDs)
  - No centralized cost dashboard (costs logged to debate-log.jsonl only)
  - No automatic retry at proxy level (retries handled in-module)
  - No request/response caching
"""

import re
import sys
import time

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
    """Retry ``fn()`` on transient errors with exponential backoff.

    Returns (result, retry_count) tuple.
    """
    last_error = None
    for attempt in range(retries):
        try:
            result = fn()
            return result, attempt  # attempt = number of retries before success
        except MA_SAFE_EXCEPTIONS as e:
            last_error = e
            if attempt < retries - 1:
                wait = backoff * (2 ** attempt)
                # Log only exception class — not message, which may
                # contain API key fragments from SDK error repr
                print(f"  MA retry {attempt + 1}/{retries} after {wait:.1f}s: "
                      f"{type(e).__name__}", file=sys.stderr)
                time.sleep(wait)
    raise last_error


# ── Core API ─────────────────────────────────────────────────────────────────

# Module-level agent cache (not os.environ — avoids ambient state leaking
# to subprocesses, per spec credential isolation requirements).
_cached_agent = None  # (agent_id, agent_version, prompt_hash)


def _prompt_hash(prompt):
    """Simple hash of prompt text for cache validation."""
    import hashlib
    return hashlib.sha256(prompt.encode()).hexdigest()[:16]


def _find_or_create_agent(client, system_prompt):
    """Find an existing consolidation agent or create one.

    Returns (agent_id, agent_version). Caches by prompt hash to avoid
    reusing an agent configured with a different system prompt.
    """
    global _cached_agent
    current_hash = _prompt_hash(system_prompt)

    # Check module-level cache first
    if _cached_agent is not None:
        cached_id, cached_version, cached_hash = _cached_agent
        if cached_hash == current_hash:
            try:
                agent = client.beta.agents.retrieve(cached_id)
                if getattr(agent, "name", None) == CONSOLIDATION_AGENT_NAME:
                    return agent.id, agent.version
            except Exception:
                pass  # stale ID, create fresh
        else:
            print("  MA cached agent prompt changed — creating fresh agent",
                  file=sys.stderr)

    agent = client.beta.agents.create(
        name=CONSOLIDATION_AGENT_NAME,
        model=CONSOLIDATION_MODEL,
        system=system_prompt,
    )
    _cached_agent = (agent.id, agent.version, current_hash)
    return agent.id, agent.version


def dispatch_task(payload, metadata, api_key):
    """Dispatch a consolidation task to Managed Agents.

    Args:
        payload: The prompt text to send (materialized challenge body).
        metadata: Dict with task context (debate_id, task_type, etc.).
        api_key: Anthropic API key for MA access.

    Returns:
        Tuple of (client, session_id, lifecycle) for polling.
        lifecycle dict contains dispatch timing and retry metadata.

    Raises:
        RuntimeError: If SDK is missing.
        MA_SAFE_EXCEPTIONS: On transient failures (after retries exhausted).
    """
    client = _get_client(api_key)
    dispatch_start = time.monotonic()

    system_prompt = metadata.get("system_prompt", "You are a helpful assistant.")

    (agent_id, agent_version), agent_retries = _retry_transient(
        lambda: _find_or_create_agent(client, system_prompt)
    )

    print(f"  MA dispatch: agent={agent_id} v{agent_version}", file=sys.stderr)

    # Create environment (once) then session (with retry).
    # Separated so that a session-creation retry doesn't orphan environments.
    env, _env_retries = _retry_transient(
        lambda: client.beta.environments.create(
            name=f"consolidation-{metadata.get('debate_id', 'unknown')}",
        )
    )
    env_id = env.id

    session, session_retries = _retry_transient(
        lambda: client.beta.sessions.create(
            environment_id=env_id,
            agent={"type": "agent", "id": agent_id, "version": agent_version},
        )
    )
    print(f"  MA session: {session.id}", file=sys.stderr)

    # Send the prompt
    client.beta.sessions.events.send(
        session.id,
        events=[{
            "type": "user.message",
            "content": [{"type": "text", "text": payload}],
        }],
    )

    dispatch_elapsed = time.monotonic() - dispatch_start
    lifecycle = {
        "dispatch_time_s": round(dispatch_elapsed, 2),
        "agent_retries": agent_retries,
        "session_retries": session_retries,
        "agent_id": agent_id,
        "env_id": env_id,
        "session_id": session.id,
    }

    return client, session.id, lifecycle


def poll_task(client, session_id, timeout_s=DEFAULT_TIMEOUT_S):
    """Poll/stream a session until it goes idle or times out.

    Args:
        client: Anthropic client instance (from dispatch_task).
        session_id: The session ID to poll.
        timeout_s: Maximum wall-clock seconds to wait.

    Returns:
        Tuple of (text_output, usage_dict). usage_dict contains token
        counts and cost estimate if available.

    Raises:
        TimeoutError: If the session doesn't complete within timeout_s.
        MA_SAFE_EXCEPTIONS: On connection/API errors.
    """
    deadline = time.monotonic() + timeout_s
    collected_text = []
    total_input_tokens = 0
    total_output_tokens = 0

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
                # Capture usage from assistant messages
                if hasattr(event, "usage") and event.usage:
                    total_input_tokens += getattr(event.usage, "input_tokens", 0)
                    total_output_tokens += getattr(event.usage, "output_tokens", 0)
            # Session idle = done
            if event.type == "session.status_idle":
                break

    text = "\n".join(collected_text) if collected_text else ""
    usage = {
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "model": CONSOLIDATION_MODEL,
    }
    return text, usage


def _cleanup_environment(client, env_id):
    """Best-effort cleanup of MA environment after use."""
    if not env_id:
        return
    try:
        client.beta.environments.delete(env_id)
    except Exception:
        pass  # cleanup is best-effort


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
        (consolidated_body, stats_dict) on success. stats_dict includes
        raw_findings, consolidated_findings, challengers, model, source,
        usage, and lifecycle fields for parity with local path.

    Raises:
        MA_SAFE_EXCEPTIONS or ValueError on failure (caller should fall back).
    """
    metadata = {
        "debate_id": debate_id,
        "task_type": "consolidation",
        "system_prompt": system_prompt,
    }

    # Count raw findings and challengers for stats parity with local path
    challenger_count = len(re.findall(
        r"^## Challenger [A-Z]", challenge_body, re.MULTILINE
    ))
    raw_items = len(re.findall(r"^\d+\.\s+", challenge_body, re.MULTILINE))

    user_content = (
        f"Here are the raw challenges from {challenger_count} "
        f"independent reviewers:\n\n{challenge_body}"
    )

    poll_start = time.monotonic()
    client, session_id, lifecycle = dispatch_task(user_content, metadata, api_key)

    try:
        raw_result, usage = poll_task(client, session_id, timeout_s)
    finally:
        # Clean up environment after polling (success or failure)
        _cleanup_environment(client, lifecycle.get("env_id"))

    poll_elapsed = time.monotonic() - poll_start
    lifecycle["completion_time_s"] = round(poll_elapsed, 2)
    lifecycle["terminal_status"] = "success" if raw_result else "empty"

    body, stats = validate_result(raw_result, len(challenge_body) * 2)

    # Enrich stats with fields matching local _consolidate_challenges contract
    stats["raw_findings"] = raw_items
    stats["challengers"] = challenger_count
    stats["usage"] = usage
    stats["lifecycle"] = lifecycle

    return body, stats

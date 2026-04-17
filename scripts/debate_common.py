#!/usr/bin/env python3.11
"""
debate_common.py — shared helpers for the debate.py engine and its sibling
subcommand modules.

Extraction commits migrate helper groups out of debate.py incrementally.
Current scope:
  - Credential + environment loading (e2dd116, simplest version)
  - Cost-tracking subsystem (this commit, F4 atomic migration)
LLM call wrappers, prompt loading, frontmatter helpers stay in debate.py
for now and migrate in followup commits.

Import style policy (per challenge F3): consumers MUST use
`import debate_common` and reference symbols as `debate_common.foo()`.
NEVER use `from debate_common import foo` — that captures the local
binding at import time and breaks monkeypatching.
"""
import os
import subprocess
import sys
import threading


try:
    PROJECT_ROOT = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL
    ).strip()
except (subprocess.CalledProcessError, FileNotFoundError):
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DEFAULT_LITELLM_URL = "http://localhost:4000"


def _load_dotenv():
    """Load .env from project root for any env vars not already set.

    Supported .env format: KEY=value, KEY="value", KEY='value',
    optional 'export ' prefix, # comments. No multiline values,
    no variable interpolation.
    """
    dotenv_path = os.path.join(PROJECT_ROOT, ".env")
    if not os.path.exists(dotenv_path):
        print(f"WARNING: {dotenv_path} not found, env vars may be missing",
              file=sys.stderr)
        return
    with open(dotenv_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:]
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            if " #" in value:
                value = value[:value.index(" #")].rstrip()
            if key and key not in os.environ:
                os.environ[key] = value


def _load_credentials():
    """Load LLM credentials, supporting fallback to ANTHROPIC_API_KEY.

    Returns (api_key, litellm_url, is_fallback).
    On failure, prints actionable error to stderr and returns (None, None, False).
    """
    api_key = os.environ.get("LITELLM_MASTER_KEY")
    if api_key:
        litellm_url = os.environ.get("LITELLM_URL", DEFAULT_LITELLM_URL)
        return api_key, litellm_url, False

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        from llm_client import activate_fallback
        activate_fallback()
        litellm_url = os.environ.get("LITELLM_URL", DEFAULT_LITELLM_URL)
        return anthropic_key, litellm_url, True

    print(
        "ERROR: No LLM credentials found.\n"
        "Set LITELLM_MASTER_KEY for full cross-model review,\n"
        "or set ANTHROPIC_API_KEY for single-model fallback.\n"
        "See docs/infrastructure.md for setup instructions.",
        file=sys.stderr,
    )
    return None, None, False


def _get_model_family(model_name):
    """Extract model family from a model name string.

    Returns a lowercase family identifier for cross-family independence checks.
    Examples: 'claude-opus-4-6' -> 'claude', 'gpt-5.4' -> 'gpt',
              'gemini-3.1-pro' -> 'gemini'
    """
    name = model_name.lower()
    if name.startswith("litellm/"):
        name = name[len("litellm/"):]
    if name.startswith("claude"):
        return "claude"
    if name.startswith("gpt") or name.startswith("o1") or name.startswith("o3"):
        return "gpt"
    if name.startswith("gemini"):
        return "gemini"
    return name.split("-")[0].split("/")[-1]


def _get_fallback_model(primary, config):
    """Return a fallback model different from primary for timeout recovery.

    Tries single_review_default, verifier_default, judge_default in order.
    Returns the first candidate whose name differs from primary, or None.
    """
    candidates = [
        config.get("single_review_default", "gpt-5.4"),
        config.get("verifier_default", "claude-sonnet-4-6"),
        config.get("judge_default", "gpt-5.4"),
    ]
    for c in candidates:
        if c and c != primary:
            return c
    return None


# ── Cost tracking (F4 atomic migration from debate.py) ──────────────────────
# Per-model token pricing (USD per 1M tokens). Updated 2026-04.
# Keys are prefix-matched against the model string.
_TOKEN_PRICING = {
    "claude-opus-4": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4": {"input": 3.0, "output": 15.0},
    "claude-haiku-4": {"input": 0.80, "output": 4.0},
    "gpt-5.4": {"input": 2.50, "output": 10.0},
    "gpt-4.1": {"input": 2.0, "output": 8.0},
    "gemini-3.1-pro": {"input": 1.25, "output": 10.0},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.0},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
}


def _estimate_cost(model, usage):
    """Estimate USD cost from model name and usage dict.

    Returns 0.0 if pricing is unknown or usage is empty.
    """
    if not usage:
        return 0.0
    pricing = None
    for prefix, rates in _TOKEN_PRICING.items():
        if model.startswith(prefix):
            pricing = rates
            break
    if not pricing:
        return 0.0
    prompt_tokens = usage.get("prompt_tokens", 0) or 0
    completion_tokens = usage.get("completion_tokens", 0) or 0
    cost = (prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]) / 1_000_000
    return round(cost, 6)


# Session-level cost accumulator. Reset per process invocation.
# Protected by _session_costs_lock because cmd_challenge (and any external
# code using ThreadPoolExecutor) calls _track_cost from multiple threads.
#
# Atomicity invariant: this dict + its lock + _track_cost + get_session_costs
# must all live in the SAME module. Re-exporting via `from debate_common import
# _session_costs` is BANNED — reassignment (_session_costs = {}) in a re-export
# would silently create a shadow dict, reintroducing the split-accumulator bug.
_session_costs = {"total_usd": 0.0, "calls": 0, "by_model": {}}
_session_costs_lock = threading.Lock()


def _track_cost(model, usage, cost_usd):
    """Accumulate a single call's cost into the session totals."""
    with _session_costs_lock:
        _session_costs["total_usd"] += cost_usd
        _session_costs["calls"] += 1
        entry = _session_costs["by_model"].setdefault(model, {
            "cost_usd": 0.0, "calls": 0, "prompt_tokens": 0, "completion_tokens": 0,
        })
        entry["cost_usd"] += cost_usd
        entry["calls"] += 1
        entry["prompt_tokens"] += (usage.get("prompt_tokens", 0) or 0)
        entry["completion_tokens"] += (usage.get("completion_tokens", 0) or 0)


def get_session_costs():
    """Return a copy of the session cost accumulator."""
    with _session_costs_lock:
        return {
            "total_usd": round(_session_costs["total_usd"], 6),
            "calls": _session_costs["calls"],
            "by_model": {
                m: {k: round(v, 6) if isinstance(v, float) else v for k, v in d.items()}
                for m, d in _session_costs["by_model"].items()
            },
        }


def _cost_delta_since(snapshot):
    """Return the cost difference between current session state and a snapshot.

    Used to log per-event costs instead of cumulative snapshots.
    """
    current = get_session_costs()
    delta_total = current["total_usd"] - snapshot.get("total_usd", 0)
    delta_calls = current["calls"] - snapshot.get("calls", 0)
    delta_models = {}
    for model, info in current["by_model"].items():
        prev = snapshot.get("by_model", {}).get(model, {})
        d_cost = info["cost_usd"] - prev.get("cost_usd", 0)
        d_calls = info["calls"] - prev.get("calls", 0)
        d_prompt = info["prompt_tokens"] - prev.get("prompt_tokens", 0)
        d_completion = info["completion_tokens"] - prev.get("completion_tokens", 0)
        if d_calls > 0:
            delta_models[model] = {
                "cost_usd": round(d_cost, 6),
                "calls": d_calls,
                "prompt_tokens": d_prompt,
                "completion_tokens": d_completion,
            }
    return {
        "total_usd": round(delta_total, 6),
        "calls": delta_calls,
        "by_model": delta_models,
    }


def _track_tool_loop_cost(model, tool_result):
    """Extract usage from an llm_tool_loop result and track cost."""
    usage = tool_result.get("usage", {})
    cost_usd = _estimate_cost(model, usage)
    _track_cost(model, usage, cost_usd)
    return cost_usd

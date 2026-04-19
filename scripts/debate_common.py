#!/usr/bin/env python3.11
"""
debate_common.py — shared helpers for the debate.py engine and its sibling
subcommand modules.

Extraction commits migrate helper groups out of debate.py incrementally.
Current scope:
  - Credential + environment loading (e2dd116, simplest version)
  - Cost-tracking subsystem (12a865b, F4 atomic migration)
  - Config loader + supporting constants (50a7fbd)
  - Debate event log writer + project timezone (170a3e6)
  - Frontmatter helpers + posture floor + challenger shuffle (this commit)
LLM call wrappers, prompt loading, and remaining cmd_* extractions stay in
debate.py for now and migrate in followup commits.

Import style policy (per challenge F3): consumers MUST use
`import debate_common` and reference symbols as `debate_common.foo()`.
NEVER use `from debate_common import foo` — that captures the local
binding at import time and breaks monkeypatching.
"""
import json
import os
import re
import string
import subprocess
import sys
import threading
from datetime import datetime
from zoneinfo import ZoneInfo


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
    Examples: 'claude-opus-4-7' -> 'claude', 'gpt-5.4' -> 'gpt',
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


# Anthropic prompt-caching price multipliers applied to the base input rate.
# Verified empirically 2026-04-18: LiteLLM passthrough sums
# input_tokens + cache_read + cache_creation into prompt_tokens. Priced naively
# that triple-counts cache tokens. See tasks/prompt-caching-smoke-test-results.md.
# Phase 0 uses 5m TTL exclusively — when 1h TTL enablement ships, the write
# multiplier must be switched to 2.0x and _estimate_cost needs a ttl argument.
_CACHE_READ_MULTIPLIER = 0.1         # cache-hit reads at 0.1x base input
_CACHE_WRITE_5M_MULTIPLIER = 1.25    # 5-minute TTL writes at 1.25x base input


def _estimate_cost(model, usage):
    """Estimate USD cost from model name and usage dict.

    Returns 0.0 if pricing is unknown or usage is empty. For Claude models,
    when usage contains cache_read_input_tokens or cache_creation_input_tokens,
    those are priced at Anthropic's cache multipliers (0.1x read, 1.25x 5-min
    write) and subtracted from prompt_tokens before the base rate applies —
    LiteLLM double-counts cache tokens inside prompt_tokens (confirmed via
    Phase 0a smoke test, 2026-04-18).

    For non-Claude models (GPT, Gemini), cache fields in usage are ignored:
    Anthropic-specific multipliers don't apply to OpenAI's 0.5x/1x cache
    pricing or Gemini's context caching tiers. Current Build OS debate usage
    only enables caching on Claude Sonnet; other providers are guarded here
    so a future LiteLLM version that surfaces their cache counters doesn't
    silently misbill through our Anthropic-tuned constants.
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

    is_claude = model.startswith("claude-")
    cache_read = (usage.get("cache_read_input_tokens", 0) or 0) if is_claude else 0
    cache_creation = (usage.get("cache_creation_input_tokens", 0) or 0) if is_claude else 0

    # LiteLLM reports prompt_tokens = input_tokens + cache_read + cache_creation.
    # Subtract cache pools before applying the base rate so each is priced once
    # at its own multiplier. Defensive clamp to 0 in case a provider eventually
    # reports cache tokens separately (then prompt_tokens would be input-only
    # and the subtraction would under-bill without the clamp).
    base_input_tokens = max(0, prompt_tokens - cache_read - cache_creation)

    cost = (
        base_input_tokens * pricing["input"]
        + cache_read * pricing["input"] * _CACHE_READ_MULTIPLIER
        + cache_creation * pricing["input"] * _CACHE_WRITE_5M_MULTIPLIER
        + completion_tokens * pricing["output"]
    ) / 1_000_000
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
    """Accumulate a single call's cost into the session totals.

    Cache token fields (cache_read_input_tokens, cache_creation_input_tokens)
    are accumulated alongside prompt/completion tokens when present. Callers
    that do not pass them (non-Anthropic models, pre-cache code paths) record
    0, which is the Anthropic convention when no cache activity occurred.
    """
    with _session_costs_lock:
        _session_costs["total_usd"] += cost_usd
        _session_costs["calls"] += 1
        entry = _session_costs["by_model"].setdefault(model, {
            "cost_usd": 0.0, "calls": 0,
            "prompt_tokens": 0, "completion_tokens": 0,
            "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
        })
        entry["cost_usd"] += cost_usd
        entry["calls"] += 1
        entry["prompt_tokens"] += (usage.get("prompt_tokens", 0) or 0)
        entry["completion_tokens"] += (usage.get("completion_tokens", 0) or 0)
        entry["cache_read_input_tokens"] = (
            entry.get("cache_read_input_tokens", 0)
            + (usage.get("cache_read_input_tokens", 0) or 0)
        )
        entry["cache_creation_input_tokens"] = (
            entry.get("cache_creation_input_tokens", 0)
            + (usage.get("cache_creation_input_tokens", 0) or 0)
        )


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
        d_cache_read = (info.get("cache_read_input_tokens", 0)
                        - prev.get("cache_read_input_tokens", 0))
        d_cache_creation = (info.get("cache_creation_input_tokens", 0)
                            - prev.get("cache_creation_input_tokens", 0))
        if d_calls > 0:
            delta_models[model] = {
                "cost_usd": round(d_cost, 6),
                "calls": d_calls,
                "prompt_tokens": d_prompt,
                "completion_tokens": d_completion,
                "cache_read_input_tokens": d_cache_read,
                "cache_creation_input_tokens": d_cache_creation,
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


# ── Config loader (migrated from debate.py) ─────────────────────────────────
# Hardcoded fallback mapping: persona name → LiteLLM model
_DEFAULT_PERSONA_MODEL_MAP = {
    "architect": "claude-sonnet-4-6",  # cost test: Sonnet vs Opus for tool-heavy challenger
    "staff": "gemini-3.1-pro",
    "security": "gpt-5.4",  # restored — read_file_snippet tool + P2 verifier compensate for low tool adoption
    "pm": "gemini-3.1-pro",
    "frame": "claude-sonnet-4-6",  # frame critique is focused reasoning, not wide synthesis
}

_DEFAULT_JUDGE = "gpt-5.4"
_DEFAULT_REFINE_ROTATION = ["gemini-3.1-pro", "gpt-5.4", "claude-opus-4-7"]

VALID_PERSONAS = {"architect", "staff", "security", "pm", "frame"}


def _load_config(config_path=None):
    """Load debate model config from JSON file, fall back to hardcoded defaults.

    Returns dict with keys: persona_model_map, judge_default, compare_default,
    refine_rotation, single_review_default, verifier_default, version.
    """
    if config_path is None:
        config_path = os.path.join(PROJECT_ROOT, "config", "debate-models.json")

    defaults = {
        "persona_model_map": dict(_DEFAULT_PERSONA_MODEL_MAP),
        "judge_default": _DEFAULT_JUDGE,
        # compare_default is intentionally lighter-weight than judge_default —
        # compare is a side-by-side scoring tool, not the truth arbiter, so a
        # cheaper/faster model is the right tradeoff.
        "compare_default": "gemini-3.1-pro",
        "refine_rotation": list(_DEFAULT_REFINE_ROTATION),
        "single_review_default": "gpt-5.4",
        "verifier_default": "claude-sonnet-4-6",
        # Frame-factual runs on a different family than frame-structural (which
        # uses the frame persona model) to reduce correlation in dual-mode.
        "frame_factual_model": "gpt-5.4",
        "version": "unknown",
    }

    if not os.path.exists(config_path):
        print(f"WARNING: {config_path} not found, using hardcoded defaults",
              file=sys.stderr)
        return defaults

    try:
        with open(config_path) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {config_path}: {e} — using defaults",
              file=sys.stderr)
        return defaults

    # Validate persona names
    pmap = config.get("persona_model_map", {})
    for persona in pmap:
        if persona not in VALID_PERSONAS:
            print(f"WARNING: unknown persona '{persona}' in config — ignoring",
                  file=sys.stderr)

    return {
        "persona_model_map": {k: v for k, v in pmap.items() if k in VALID_PERSONAS}
                              or defaults["persona_model_map"],
        "judge_default": config.get("judge_default", defaults["judge_default"]),
        "compare_default": config.get("compare_default", defaults["compare_default"]),
        "refine_rotation": config.get("refine_rotation", defaults["refine_rotation"]),
        "single_review_default": config.get("single_review_default",
                                            defaults["single_review_default"]),
        "verifier_default": config.get("verifier_default", defaults["verifier_default"]),
        "frame_factual_model": config.get("frame_factual_model", defaults["frame_factual_model"]),
        "version": config.get("version", defaults["version"]),
    }


# ── Debate event log writer (migrated from debate.py) ───────────────────────
PROJECT_TZ = ZoneInfo("America/Los_Angeles")
DEFAULT_LOG_PATH = "stores/debate-log.jsonl"


def _log_debate_event(event, log_path=None, cost_snapshot=None):
    """Append a debate event to the JSONL log file.

    If cost_snapshot is provided, logs the delta since that snapshot (per-event
    cost). Otherwise logs the full cumulative session total. Per-event deltas
    are preferred — they prevent double-counting in stats aggregation.
    """
    path = log_path or DEFAULT_LOG_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    now = datetime.now(PROJECT_TZ)
    event["timestamp"] = now.strftime("%Y-%m-%dT%H:%M:%S%z")[:25]
    if cost_snapshot is not None:
        event["costs"] = _cost_delta_since(cost_snapshot)
    else:
        event["costs"] = get_session_costs()
    with open(path, "a") as f:
        f.write(json.dumps(event) + "\n")


# ── Security posture floors ───────────────────────────────────────────────────
# Topics involving credentials, auth, or destructive ops get posture >= 3
# regardless of user setting. Pattern-matched on proposal/input content.
SECURITY_FLOOR_PATTERNS = [
    r'\bcredential', r'\bapi[_\s-]?key', r'\bsecret[_\s-]?key',
    r'\bOAuth\b', r'\btoken\b', r'\bpassword', r'\bauth\b',
    r'\.env\b', r'\bprivate[_\s-]?key',
    r'\begress\b', r'\bexfiltrat',
    r'\brm\s+-rf\b', r'\bDROP\s+TABLE\b', r'\bDELETE\s+FROM\b',
    r'\bdestructive\b', r'\birreversible\b',
]
SECURITY_FLOOR_MIN = 3

_SECURITY_FLOOR_RE = re.compile(
    '|'.join(SECURITY_FLOOR_PATTERNS), re.IGNORECASE
)


def _apply_posture_floor(posture, content, label="proposal"):
    """Clamp posture to SECURITY_FLOOR_MIN if content matches security patterns.

    Returns (effective_posture, was_clamped).
    """
    if posture >= SECURITY_FLOOR_MIN:
        return posture, False
    match = _SECURITY_FLOOR_RE.search(content)
    if match:
        print(f"WARNING: posture floor applied ({posture}→{SECURITY_FLOOR_MIN}) — "
              f"{label} contains security-sensitive content "
              f"(matched: '{match.group()}')",
              file=sys.stderr)
        return SECURITY_FLOOR_MIN, True
    return posture, False


CHALLENGER_LABELS = list(string.ascii_uppercase)  # A, B, C, ...


def _shuffle_challenger_sections(challenge_body, mapping):
    """Shuffle challenger sections to eliminate position bias for the judge.

    Splits on '## Challenger X' headers, randomizes order, relabels to
    sequential letters. Returns (shuffled_body, shuffled_mapping).
    The original mapping is preserved in the output file; shuffling only
    affects what the judge sees.
    """
    import random

    # Split into sections by ## Challenger header
    sections = []
    current_label = None
    current_lines = []

    for line in challenge_body.splitlines(keepends=True):
        header_match = re.match(r"^## Challenger ([A-Z])", line)
        if header_match:
            if current_label is not None:
                sections.append((current_label, "".join(current_lines)))
            current_label = header_match.group(1)
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_label is not None:
        sections.append((current_label, "".join(current_lines)))

    if len(sections) < 2:
        return challenge_body, mapping

    # Shuffle
    random.shuffle(sections)

    # Relabel to sequential A, B, C...
    relabel_map = {}
    shuffled_parts = []
    shuffled_mapping = {}

    for i, (old_label, text) in enumerate(sections):
        new_label = CHALLENGER_LABELS[i]
        relabel_map[old_label] = new_label
        # Replace label references in section text
        relabeled = text.replace(f"Challenger {old_label}", f"Challenger {new_label}")
        shuffled_parts.append(relabeled)
        # Map new label to original model
        if old_label in mapping:
            shuffled_mapping[new_label] = mapping[old_label]

    return "".join(shuffled_parts), shuffled_mapping


# ── Frontmatter ──────────────────────────────────────────────────────────────


def _build_frontmatter(debate_id, mapping, extras=None):
    """Build YAML frontmatter string with debate metadata."""
    now = datetime.now(PROJECT_TZ)
    lines = [
        "---",
        f"debate_id: {debate_id}",
        f"created: {now.strftime('%Y-%m-%dT%H:%M:%S%z')[:25]}",
        "mapping:",
    ]
    for label, model in mapping.items():
        lines.append(f"  {label}: {model}")
    if extras:
        for key, value in extras.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            else:
                lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def _redact_author(proposal_text):
    """Redact author metadata from proposal before sending to challengers/judge.

    Replaces 'author: <anything>' with 'author: anonymous' in YAML frontmatter
    to prevent model-identity bias. The original file on disk is not modified.
    """
    if not proposal_text.startswith("---"):
        return proposal_text
    fm_end = proposal_text.find("---", 3)
    if fm_end < 0:
        return proposal_text
    frontmatter = proposal_text[3:fm_end]
    body = proposal_text[fm_end:]
    redacted_fm = re.sub(
        r"^author\s*:.*$", "author: anonymous", frontmatter, flags=re.MULTILINE
    )
    return "---" + redacted_fm + body

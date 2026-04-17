#!/usr/bin/env python3.11
"""
debate_common.py — shared helpers for the debate.py engine and its sibling
subcommand modules.

This is the first extraction commit toward making debate.py a thin entry
point. Scope of THIS commit (per tasks/debate-common-plan.md): credential
+ environment loading + cost-independent dispatch helpers. Cost tracking,
LLM call wrappers, prompt loading, and frontmatter helpers stay in
debate.py for now and migrate in followup commits.

Import style policy (per challenge F3): consumers MUST use
`import debate_common` and reference symbols as `debate_common.foo()`.
NEVER use `from debate_common import foo` — that captures the local
binding at import time and breaks monkeypatching.
"""
import os
import subprocess
import sys


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

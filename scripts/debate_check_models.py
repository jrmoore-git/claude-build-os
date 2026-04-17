#!/usr/bin/env python3.11
"""
debate_check_models.py — `debate.py check-models` subcommand.

Extracted from debate.py. Shared state (config loader, credentials,
exception tuple) still lives in debate.py; this module imports them
lazily to avoid a circular import.
"""
import json
import sys
import urllib.error
import urllib.request


def cmd_check_models(args):
    """Compare LiteLLM available models against config."""
    import debate  # lazy import: debate.py is the source of truth for helpers
    import debate_common

    config = debate_common._load_config()
    api_key, litellm_url, _is_fallback = debate_common._load_credentials()
    if api_key is None:
        return 1
    if _is_fallback:
        print("check-models requires a running LiteLLM proxy. "
              "Currently in Anthropic fallback mode.", file=sys.stderr)
        return 1

    # Fetch available models from LiteLLM
    url = f"{litellm_url.rstrip('/')}/models"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        body = json.loads(resp.read().decode())
        available = {m["id"] for m in body.get("data", [])}
    except debate.LLM_SAFE_EXCEPTIONS as e:
        print(f"ERROR: cannot reach LiteLLM at {url} — {e}", file=sys.stderr)
        return 1

    # Models referenced in config
    configured = set()
    for model in config["persona_model_map"].values():
        configured.add(model)
    configured.add(config["judge_default"])
    for model in config["refine_rotation"]:
        configured.add(model)
    configured.add(config["single_review_default"])

    # Report
    print(f"Config version: {config['version']}")
    print(f"\nConfigured models: {', '.join(sorted(configured))}")
    print(f"Available in LiteLLM: {', '.join(sorted(available))}")

    missing = configured - available
    if missing:
        print(f"\n⚠ Models in config but NOT in LiteLLM: {', '.join(sorted(missing))}")

    new_models = available - configured
    if new_models:
        print(f"\n→ New models in LiteLLM not in config: {', '.join(sorted(new_models))}")
        print("  Consider running 'debate.py benchmark' to evaluate new models.")
    else:
        print("\nAll available models are accounted for in config.")

    return 0

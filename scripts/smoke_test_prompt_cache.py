#!/usr/bin/env python3.11
"""Component 4a smoke test — LiteLLM passthrough for Anthropic prompt caching.

Operational diagnostic. Re-run whenever LiteLLM, the proxy config, or the
Anthropic Messages API changes in a way that could affect cache_control
marker passthrough. One run costs ~$0.20 for 3 Sonnet calls.

Verifies three things per tasks/prompt-caching-plan.md Component 4:
  4a. LiteLLM passes cache_control markers through to Anthropic
  4b. Cached output is byte-identical to uncached output (n=1; see also
      smoke_test_cache_reproducibility.py for the n=10 paired sweep)
  4c. Run-over-run cache read delivers measurable input-token savings

Emits machine-readable JSON to stdout and a human-readable summary to stderr.
"""

import json
import sys
import time
from pathlib import Path

# Add scripts/ to import path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import debate_common  # noqa: F401  (ensures .env credentials load path)
from llm_client import llm_call_raw

# Model must have caching minimum we can actually exceed with our prompt.
# Sonnet tier minimum is 2048 tokens; claude-sonnet-4-6 is our debate default.
MODEL = "claude-sonnet-4-6"

# Shared cacheable content — needs to exceed 2048 tokens.
# Read the refined arm-comparison design (511 lines, ~40KB, ~10K tokens).
CACHEABLE_DOC = Path("tasks/debate-arm-comparison-design-refined.md").read_text()

# Trim if needed to keep the call cheap, but stay well above 2048 tokens
# (heuristic: 1 token ≈ 4 bytes, so ~10K bytes ≈ 2500 tokens is the floor).
CACHEABLE_DOC = CACHEABLE_DOC[:20000]  # ~5K tokens

SYSTEM_PROMPT = (
    "You are a careful reviewer. Answer the user's question "
    "using the document below as your only source of truth. Be concise."
)

USER_PROMPT = (
    f"Document:\n\n{CACHEABLE_DOC}\n\n"
    f"---\n\n"
    f"Question: In one sentence, name the primary decision point described."
)


def call(label, *, cache_control):
    """Make a call, return (content, usage dict, elapsed_seconds)."""
    t0 = time.monotonic()
    # _load_dotenv makes credentials available via env; llm_client reads them.
    debate_common._load_dotenv()
    raw = llm_call_raw(
        SYSTEM_PROMPT, USER_PROMPT,
        model=MODEL,
        temperature=0.0,
        max_tokens=64,
        timeout=60,
        cache_control=cache_control,
    )
    elapsed = time.monotonic() - t0
    print(f"[{label}] elapsed={elapsed:.1f}s usage={raw.get('usage', {})}",
          file=sys.stderr)
    return raw["content"], raw["usage"], elapsed


def main():
    results = {
        "model": MODEL,
        "doc_bytes": len(CACHEABLE_DOC),
        "user_bytes": len(USER_PROMPT),
        "runs": [],
    }

    # Run 1: cache enabled, first call — expect cache_creation > 0
    content_1, usage_1, elapsed_1 = call("run 1 cached", cache_control="system+user")
    results["runs"].append({
        "label": "run 1 (cache enabled)",
        "cache_control": "system+user",
        "usage": usage_1,
        "elapsed_seconds": round(elapsed_1, 2),
        "content_sha256": _sha(content_1),
        "content_first_80": content_1[:80],
    })

    # Brief pause — stay under the 5-minute TTL
    time.sleep(2)

    # Run 2: cache enabled, second call with IDENTICAL input — expect cache_read > 0
    content_2, usage_2, elapsed_2 = call("run 2 cached", cache_control="system+user")
    results["runs"].append({
        "label": "run 2 (cache enabled, identical input)",
        "cache_control": "system+user",
        "usage": usage_2,
        "elapsed_seconds": round(elapsed_2, 2),
        "content_sha256": _sha(content_2),
        "content_first_80": content_2[:80],
    })

    # Run 3: cache disabled — baseline for byte-identity check
    content_3, usage_3, elapsed_3 = call("run 3 uncached", cache_control=None)
    results["runs"].append({
        "label": "run 3 (cache disabled, same input)",
        "cache_control": None,
        "usage": usage_3,
        "elapsed_seconds": round(elapsed_3, 2),
        "content_sha256": _sha(content_3),
        "content_first_80": content_3[:80],
    })

    # Verdicts
    results["verdicts"] = {
        "cache_creation_on_run_1": usage_1.get("cache_creation_input_tokens", 0),
        "cache_read_on_run_2": usage_2.get("cache_read_input_tokens", 0),
        "passthrough_works": (
            usage_1.get("cache_creation_input_tokens", 0) > 0
            or usage_2.get("cache_read_input_tokens", 0) > 0
        ),
        "byte_identity_cached_vs_uncached": content_2 == content_3,
        "byte_identity_run1_vs_run2": content_1 == content_2,
        "run2_cache_read_ratio": (
            usage_2.get("cache_read_input_tokens", 0)
            / max(1, usage_2.get("prompt_tokens", 0)
                    + usage_2.get("cache_read_input_tokens", 0))
        ),
        # Double-count signal: if prompt_tokens on run 2 with a cache hit is
        # roughly the same as run 1 (with a cache write), LiteLLM is reporting
        # cache tokens as part of prompt_tokens too (double-count risk).
        # If run 2 prompt_tokens << run 1 prompt_tokens, cache tokens are
        # reported separately (Anthropic native semantics).
        "run1_prompt_tokens": usage_1.get("prompt_tokens", 0),
        "run2_prompt_tokens": usage_2.get("prompt_tokens", 0),
        "likely_double_count": (
            usage_2.get("prompt_tokens", 0)
            >= 0.8 * usage_1.get("prompt_tokens", 0)
            and usage_2.get("cache_read_input_tokens", 0) > 0
        ),
    }

    print(json.dumps(results, indent=2))
    return 0


def _sha(text):
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()[:16]


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3.11
"""Component 4b — paired-call reproducibility sweep.

Operational diagnostic. Re-run when there's any reason to suspect cache
read drift (LiteLLM upgrade, Anthropic cache-serving change, or a spike
in output variance). One run costs ~$0.20 for 21 Sonnet calls.

Question: does Anthropic prompt caching introduce output drift beyond the
baseline temperature=0 non-determinism that Claude already exhibits?

Method:
  - 1 warm-up uncached call → reference hash.
  - N=10 cached calls on identical input → measure hash-match rate to reference.
  - N=10 uncached calls on identical input → measure hash-match rate to reference.
  - If cached_match_rate ≈ uncached_match_rate, cache is not adding drift.
  - If cached_match_rate is materially lower, cache is adding drift (halt rollout).

All cached reads hit the same cache entry. All uncached calls exercise the
normal stochastic path. Within 5 minutes (cache TTL).

Run:   python3.11 scripts/smoke_test_cache_reproducibility.py
"""

import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import debate_common  # noqa: F401
from llm_client import llm_call_raw

MODEL = "claude-sonnet-4-6"
N = 10

CACHEABLE_DOC = Path("tasks/debate-arm-comparison-design-refined.md").read_text()[:20000]

SYSTEM_PROMPT = (
    "You are a careful reviewer. Answer the user's question "
    "using the document below as your only source of truth. Be concise."
)
USER_PROMPT = (
    f"Document:\n\n{CACHEABLE_DOC}\n\n"
    f"---\n\n"
    f"Question: In one sentence, name the primary decision point described."
)


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def call(cache_control):
    raw = llm_call_raw(
        SYSTEM_PROMPT, USER_PROMPT,
        model=MODEL,
        temperature=0.0,
        max_tokens=64,
        timeout=60,
        cache_control=cache_control,
    )
    return raw["content"], raw["usage"]


def main():
    debate_common._load_dotenv()

    # 1. Warm-up uncached reference
    ref_content, ref_usage = call(None)
    ref_hash = _sha(ref_content)
    print(f"[reference] hash={ref_hash}", file=sys.stderr)
    print(f"           usage={ref_usage}", file=sys.stderr)

    cached_hashes = []
    uncached_hashes = []

    # 2. N cached reads (first one writes, rest read)
    for i in range(N):
        content, usage = call("system+user")
        h = _sha(content)
        cached_hashes.append(h)
        print(f"[cached {i+1:2}/{N}] hash={h} "
              f"read={usage.get('cache_read_input_tokens', 0)} "
              f"write={usage.get('cache_creation_input_tokens', 0)}",
              file=sys.stderr)

    # 3. N fresh uncached calls
    for i in range(N):
        content, usage = call(None)
        h = _sha(content)
        uncached_hashes.append(h)
        print(f"[uncached {i+1:2}/{N}] hash={h} "
              f"prompt={usage.get('prompt_tokens', 0)}",
              file=sys.stderr)

    cached_match = sum(1 for h in cached_hashes if h == ref_hash)
    uncached_match = sum(1 for h in uncached_hashes if h == ref_hash)
    cached_unique = len(set(cached_hashes))
    uncached_unique = len(set(uncached_hashes))

    results = {
        "model": MODEL,
        "N_per_group": N,
        "reference_hash": ref_hash,
        "cached_hashes": cached_hashes,
        "uncached_hashes": uncached_hashes,
        "match_rate_cached_vs_ref": cached_match / N,
        "match_rate_uncached_vs_ref": uncached_match / N,
        "unique_outputs_cached": cached_unique,
        "unique_outputs_uncached": uncached_unique,
        # Decision rule per tasks/prompt-caching-plan.md + smoke-test-results.md:
        # if cached_match_rate >= uncached_match_rate, cache is not adding drift.
        "verdict_cache_adds_drift": (cached_match / N) < (uncached_match / N),
    }

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

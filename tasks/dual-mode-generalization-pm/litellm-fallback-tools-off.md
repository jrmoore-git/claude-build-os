---
debate_id: litellm-fallback-tools-off
created: 2026-04-17T14:51:03-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# litellm-fallback-tools-off — Challenger Reviews

## Challenger A (pm) — Challenges
## Challenges

1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The fallback assumes `ANTHROPIC_API_KEY` is available in the environment. If the user is using Claude Code via an Enterprise login or managed OAuth session, they may not actually have a raw API key exported to the shell. If the key is missing, the script needs a graceful terminal error explaining *both* paths (set the API key, or start LiteLLM) rather than throwing a generic `KeyError`.

2. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposal states it will use `urllib.request` to hit the Anthropic API directly. Unlike swapping one OpenAI-compatible endpoint for another, Anthropic's Messages API has distinct structural requirements: `max_tokens` is strictly required, the `system` prompt is extracted outside the `messages` array, and messages must strictly alternate `user`/`assistant`. The payload translation logic will require specific handling, not just a URL change.

3. [RISK] [ADVISORY]: By bypassing LiteLLM, you bypass any parallelization or rate-limit management it might be providing. Running three sequential or parallel requests to the same Anthropic API key might trigger tier-based rate limits (especially for new accounts) faster than splitting requests across three providers. The fallback should ensure it handles HTTP 429s gracefully.

## Concessions
1. Correctly identifies the biggest adoption friction (LiteLLM proxy requirement) and solves it without compromising the structural value of the feature (the 3 lenses).
2. Maintains a strict contract with downstream hooks and skills by keeping the artifact YAML/markdown output identical.
3. Excellent UX touch with the single stderr warning acting as an organic upsell to the "pro" multi-model setup without blocking the user.

## Verdict
APPROVE. This is a high-leverage UX win that dramatically lowers the floor for adoption while preserving the ceiling for advanced users.

---

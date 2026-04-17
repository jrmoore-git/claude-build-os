---
debate_id: litellm-fallback-tools-on
created: 2026-04-17T14:51:49-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# litellm-fallback-tools-on — Challenger Reviews

## Challenger A (pm) — Challenges
## Challenges

1. OVER-ENGINEERED [MATERIAL] [COST:TRIVIAL]: The proposed solution already exists in the codebase. `scripts/llm_client.py` already contains `is_fallback_active()`, `get_fallback_model()`, and `activate_fallback()` functions, along with Anthropic fallback API logic. `scripts/debate.py` already contains `_call_with_model_fallback`, and `tests/test_debate_fallback.py` proves the feature is already fully implemented and tested. Proceeding with this proposal would duplicate existing functionality or overwrite it unnecessarily.

## Concessions
1. The analysis of the problem (LiteLLM being an onboarding cliff) is accurate.
2. The user experience degradation path (structured single-model review rather than no review) makes logical sense.

## Verdict
REJECT because the proposed fallback mechanism is already implemented and natively supported in the current codebase.

---

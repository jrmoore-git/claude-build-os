---
debate_id: new_defect__03-litellm-fallback-error-reifies-framing__pass
created: 2026-04-18T13:21:39-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# new_defect__03-litellm-fallback-error-reifies-framing__pass — Challenger Reviews

## Challenger A (pm) — Challenges
### PM/Acceptance Review

**[MATERIAL] SPEC VIOLATION: Incorrect Missing-Key Error Message**
The spec explicitly requires the following exact error message when `ANTHROPIC_API_KEY` is missing: 
*"LiteLLM proxy unavailable (localhost:4000) and ANTHROPIC_API_KEY not found in environment. To run reviews, either start LiteLLM or export ANTHROPIC_API_KEY."*
The diff implements a different, generic message: *"LiteLLM unreachable and no direct-provider API key set. Start LiteLLM..."* This breaks the precise UX specified for onboarding users.

**[MATERIAL] SPEC VIOLATION: Incorrect Warning Message & Frequency**
The spec requires printing exactly one line to `stderr` *per command invocation*, with this exact text: 
*"LiteLLM unavailable — running single-model review. For cross-model review, see docs/infrastructure.md"*
The diff prints *"LiteLLM unavailable — running single-model fallback via Anthropic API."* and it does so inside `llm_request()`. Since `llm_request` will be called multiple times per command (once for each lens: PM, Security, Architecture), this will spam the console and violate the "exactly one line to `stderr` before execution" requirement. 

**[ADVISORY] Incomplete Spec Implementation in `debate.py`**
The proposal states that changes are required in `scripts/debate.py` to bypass model rotation and ensure the fallback decision is evaluated only once per command invocation. The diff provided only covers `scripts/llm_client.py`. State management for the fallback trigger and message emission should likely be handled at the command level in `debate.py` to satisfy the "once per invocation" requirement.

---

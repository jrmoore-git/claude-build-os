---
debate_id: litellm-fallback-tools-on
created: 2026-04-17T14:51:00-0700
mapping:
  A: gpt-5.4
personas:
  A: security
---
# litellm-fallback-tools-on — Challenger Reviews

## Challenger A (security) — Challenges
## Challenges
1. [RISK] [MATERIAL] [COST:SMALL]: The proposal says fallback should trigger on “connection refused / timeout to LiteLLM proxy,” but the current client only activates fallback on connection-refused, not timeout: `_dispatch()` falls back only when `_is_connection_refused(exc)` is true, while `_is_retryable()` explicitly treats `TimeoutError` and `APITimeoutError` as non-retryable and does not route them into fallback (`scripts/llm_client.py:193-207, 572-594`). This matters because the stated onboarding fix is incomplete: a hung or overloaded local proxy still fails `/review` instead of degrading gracefully. Risk of changing: you may mask real model/provider latency with single-model fallback; risk of not changing: the “LiteLLM unavailable” cliff remains for a meaningful failure mode.  

2. [RISK] [MATERIAL] [COST:TRIVIAL]: The proposal claims “Print one line to stderr,” but the implemented warning is two lines, and there is no test coverage asserting the transparency message or degraded-mode marker (`scripts/llm_client.py:585-590`; test search found no match for the warning text, and no tests mention `degraded_single_model`). As a result, downstream UX and operator expectations are unpinned: future edits could silently remove or change the disclosure, undermining trust boundaries between full cross-model review and same-model review. This is a build-condition fix, not a rejection reason, but it should be tightened before merge.

## Concessions
- The design preserves artifact shape and existing interfaces, which minimizes downstream breakage.
- Credential handling is relatively contained: the client already supports separate loading of `LITELLM_MASTER_KEY` and `ANTHROPIC_API_KEY` from env or `.env` (`scripts/llm_client.py:105-129`).
- The codebase already has explicit degraded-independence signaling in `cmd_judge`, which is the right kind of transparency for correlated-blind-spot risk (`scripts/debate.py:1437-1445`).

## Verdict
REVISE — the fallback approach is directionally sound, but the proposal overclaims timeout coverage and should add tests/guards so degraded single-model review is explicitly and reliably disclosed.

---

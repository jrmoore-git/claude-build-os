---
debate_id: litellm-fallback-tools-on
created: 2026-04-17T14:51:35-0700
mapping:
  A: claude-opus-4-7
personas:
  A: architect
---
# litellm-fallback-tools-on — Challenger Reviews

## Challenger A (architect) — Challenges
I now have everything I need. This proposal is essentially describing a feature that is already implemented and tested.

## Challenges

1. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The proposal's core premise — "LiteLLM unavailability means `/challenge` and `/review` fail entirely" — is **contradicted by the shipped code**. `scripts/debate_common.py:75-100` (`_load_credentials`) already returns `(anthropic_key, url, is_fallback=True)` when `LITELLM_MASTER_KEY` is absent but `ANTHROPIC_API_KEY` is present, and calls `llm_client.activate_fallback()`. `llm_client.py` already exports `activate_fallback`, `is_fallback_active`, `get_fallback_model`, `_anthropic_key_load`, `_anthropic_call`, with `_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"` hardcoded. Tests exist at `tests/test_debate_fallback.py` (264 lines). The stderr message the proposal wants to add ("see docs/infrastructure.md") is already emitted nearly verbatim at line 97. The proposal appears to re-invent existing infrastructure. Fix: verify current behavior before building; then the proposal reduces to a small gap-analysis. EVIDENCED by tool inspection of `scripts/debate_common.py`, `scripts/llm_client.py`, and `tests/test_debate_fallback.py`.

2. [RISK] [MATERIAL] [COST:SMALL]: The proposal specifies detection trigger as **"on first LLM call failure (connection refused / timeout to LiteLLM proxy)"** — i.e., *runtime* detection. The shipped implementation detects at **startup by credential presence** (`LITELLM_MASTER_KEY` missing → fallback). These are materially different: the shipped version does NOT handle "LiteLLM configured but proxy is down right now." `_is_connection_refused()` exists in `llm_client.py:168` but is only used to mark errors non-retryable (line 196) — it does NOT trigger `activate_fallback()`. So there IS a real gap: a user who set `LITELLM_MASTER_KEY` but whose proxy container crashed mid-session gets a hard failure even if `ANTHROPIC_API_KEY` is present. If that is the actual problem being solved, the proposal should say so and the change is ~30 lines in `_call_with_retry` / `_dispatch` wiring, not a new subsystem.

3. [UNDER-ENGINEERED] [ADVISORY]: The proposal says "the persona system prompts still apply — each lens still gets its framing" but doesn't address the **correlated-blind-spot problem** it then acknowledges in Tradeoffs. Running three sequential prompts against the same model and calling the output "review" invites anchoring: round 2's system prompt sees no response text from round 1, but the artifact reader can't tell whether findings represent three independent lenses or one model's self-agreement dressed in three hats. The artifact format being "identical" (frontmatter-compatible) is a *feature for consumers* but a *liability for trust*: downstream hooks that gate on finding counts (`_count_open_material` in `scripts/artifact_check.py`) will treat single-model output as equivalent evidence. Consider a `mode: single_model_fallback` frontmatter field so gates can weight accordingly. ADVISORY because it doesn't block the change but should be decided explicitly.

4. [ALTERNATIVE] [ADVISORY]: The proposal bypasses `config/debate-models.json` entirely ("No changes. The fallback bypasses model routing entirely."). An alternative that preserves the existing routing abstraction: add a `fallback_mode` block in `debate-models.json` mapping all personas to the single Anthropic model. This keeps the "model routing config is the single source of truth" invariant. Bypassing it means future questions like "which model ran this persona?" need two code paths to answer.

## Concessions

1. The framing of the onboarding cliff is correct and well-articulated — requiring three API keys + a proxy before a user can see the signature feature is genuinely a barrier.
2. Keeping artifact format stable across modes is the right call for hook/skill compatibility (existing consumers like `artifact_check.py` and `finding_tracker.py` read frontmatter, not model metadata).
3. The "difference between no review and single-model review >> difference between single-model and multi-model" framing is a defensible product judgment.

## Verdict

**REVISE** — the proposal as written duplicates ~80% of work already shipped in `debate_common._load_credentials`, `llm_client.activate_fallback`, and `_anthropic_call`; the author must first audit existing fallback behavior and rewrite the scope to target the actual gap (likely runtime proxy-down detection, not missing credentials), which is a small, bounded change rather than a new subsystem.

---

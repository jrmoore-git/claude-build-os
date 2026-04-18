---
debate_id: litellm-fallback
created: 2026-04-17T13:31:51-0700
mapping:
  A: claude-opus-4-7
  B: gpt-5.4
  C: gemini-3.1-pro
  D: claude-sonnet-4-6
  E: gpt-5.4
personas:
  A: architect
  B: security
  C: pm
  D: frame-structural
  E: frame-factual
---
# litellm-fallback — Challenger Reviews

## Challenger A (architect) — Challenges
I have enough evidence. Key findings:

1. The transport-level fallback (LiteLLM → direct Anthropic API via `_anthropic_call`) already exists in `scripts/llm_client.py`, including the exact stderr message from the proposal ("LiteLLM proxy unavailable — running single-model review. For cross-model review, see docs/infrastructure.md"), the connection-refused detection, and Anthropic-key gating.
2. `tests/test_debate_fallback.py` exists (264 lines) and tests `_call_with_model_fallback`.
3. BUT `debate.py` does not import `is_fallback_active` — so debate.py still dispatches work to multiple distinct model names (claude-opus-4-7, gpt-5.4, gemini-3.1-pro per `persona_model_map`). In fallback mode, every call goes to the *same* Anthropic model regardless of the requested name, meaning "challenge with 3 personas" becomes 3 sequential calls to the same model. The proposal's behavior section #2 ("route all persona/model requests to the single available model") is what's actually needed — but the `_dispatch` short-circuit already does this transparently at the transport layer. The multi-persona commands will already work; they just won't be *aware* that model diversity collapsed.
4. The proposal doesn't acknowledge that ~80% of what it proposes is already shipped.

## Challenges

1. **ASSUMPTION** [MATERIAL] [COST:TRIVIAL]: The proposal frames this as net-new work, but `scripts/llm_client.py` already implements the transport fallback end-to-end: `_anthropic_call`, `_is_connection_refused`, `activate_fallback`, `is_fallback_active`, `get_fallback_model`, `_FALLBACK_ACTIVE`/`_FALLBACK_WARNED` state machine, and even the exact stderr string the proposal specifies ("LiteLLM proxy unavailable — running single-model review. For cross-model review, see docs/infrastructure.md") at `llm_client.py:553` and `:587`. `tests/test_debate_fallback.py` already exists (264 lines). EVIDENCED (via direct file read). The proposal must be rescoped to describe only the *remaining* gap, or it risks duplicate implementation and merge conflicts with whatever previously landed.

2. **RISK** [MATERIAL] [COST:SMALL]: The real remaining gap is that `debate.py` is not fallback-*aware*. A grep of `scripts/` shows `is_fallback_active` has exactly 1 occurrence — its definition in `llm_client.py` — so `debate.py` never inspects it. In fallback mode, `/challenge` with `architect,security,pm` still issues three calls with three distinct model names (`claude-opus-4-7`, `gpt-5.4`, `gemini-3.1-pro` per `persona_model_map`); the transport layer transparently routes all three to the *same* Anthropic model, so the artifact will claim cross-model diversity that doesn't exist. The judge and refine commands may double-count correlated findings as "corroboration" across what they think are independent models. Fix: after first call detects fallback, stamp artifact frontmatter with `review_mode: single-model-fallback` and skip the consolidation step that assumes model independence. This is the missing 20% the proposal should focus on.

3. **UNDER-ENGINEERED** [MATERIAL] [COST:TRIVIAL]: The proposal doesn't specify which Claude model the fallback uses. Looking at `_FALLBACK_MODEL` usage in `llm_client.py`, there's a fixed fallback model — but the proposal says "the session's own Claude model," which isn't how the existing code behaves. Either the proposal is wrong about behavior or the existing code needs to read the session's model. Reconcile before writing code.

4. **ASSUMPTION** [ADVISORY]: "ANTHROPIC_API_KEY … which Claude Code already has configured" — Claude Code users authenticated via OAuth/Claude subscription do *not* necessarily have `ANTHROPIC_API_KEY` set in their env. The existing code already handles this case (raises `LLMError` with a helpful message at `llm_client.py:578-583`), but the proposal's framing ("zero additional setup") is over-optimistic for the OAuth subset. SPECULATIVE on what fraction of Claude Code users have the key; needs verification before claiming "zero additional setup."

5. **OVER-ENGINEERED** [ADVISORY]: The proposal says fallback would use `urllib.request` for the Anthropic Messages API. The existing `_anthropic_call` already exists (verified: 1 match for `def _anthropic_call(`). No new HTTP client needed.

## Concessions
1. The design principle — transport-layer fallback, unchanged artifact format, unchanged hook/skill contracts — is correct and aligns with what was already built.
2. Flagging `review_mode` transparency so downstream consumers can distinguish single-model from multi-model runs is the right instinct (and is the actual missing piece).
3. Keeping `config/debate-models.json` unchanged is correct; fallback should bypass model routing, not rewrite it.

## Verdict
**REVISE** — The proposal as written largely re-specifies an already-shipped feature in `llm_client.py`; rescope it to the genuine remaining gap (making `debate.py`'s multi-persona commands fallback-*aware* so artifacts don't falsely claim cross-model independence), which is SMALL cost and the actually valuable change.

---

## Challenger B (security) — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposal says fallback should use “the session’s own Claude model,” but the current implementation in `scripts/llm_client.py` hard-codes a single fallback model via `_FALLBACK_MODEL = os.environ.get("ANTHROPIC_FALLBACK_MODEL", "claude-sonnet-4-20250514")` and routes all fallback calls there. That creates an unstated trust/behavior gap: users may believe review is happening on the same model family/version they are interacting with, while the code actually substitutes a fixed model. This matters because it changes independence assumptions, output quality, and reproducibility of review artifacts. Fix by either passing an explicit fallback model from `debate.py` based on invocation context and recording it in artifact metadata, or narrowing the proposal to match the actual fixed-model behavior.

2. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal claims “No degradation in artifact format” and implies downstream consumers do not need to know the difference, but fallback materially changes the trust boundary: multi-model independent review becomes same-provider, same-family review with correlated blind spots. `debate.py` already warns about degraded judge independence in one path, which is good, but the proposal does not require this degraded posture to be persisted in artifact frontmatter/output metadata. Without that, other hooks/skills/users can over-trust a fallback-generated artifact as if it had cross-model independence. The fix is to stamp artifacts with fallback mode/model and independence level so later gates can reason about reduced assurance.

3. [RISK] [ADVISORY]: Credential handling is acceptable but increases secret exposure surface slightly because `llm_client.py` reads `ANTHROPIC_API_KEY` directly from both environment and `.env`. That is not inherently flawed, but adding direct-provider calls means one more code path that can accidentally log headers, request bodies, or error payloads if future debugging is added. I did not see evidence in the inspected snippets of secrets being printed today, so this is advisory: keep explicit tests/assertions that auth headers and raw request objects never reach stderr/logs.

## Concessions
- The implementation already distinguishes connection-refused from retryable network errors, which is the right trigger for graceful degradation instead of broad fail-open fallback.
- The client already emits a user-visible warning when fallback activates, which is good transparency and avoids silent downgrade.
- The proposal improves the risk of not changing: today onboarding fails closed when LiteLLM is absent; single-model fallback clearly reduces that operational cliff.

## Verdict
REVISE — the fallback approach is directionally sound, but artifact metadata and model-selection semantics need to reflect the reduced independence so users and downstream automation do not over-trust degraded reviews.

---

## Challenger C (pm) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The proposal assumes that the single-model fallback feature does not currently exist. However, this exact functionality is already fully implemented in the codebase. `scripts/llm_client.py` already exports `activate_fallback`, `is_fallback_active`, and `get_fallback_model`, while `scripts/debate.py` actively uses `_call_with_model_fallback` to route requests when LiteLLM is unavailable. Furthermore, the test suite already explicitly covers this behavior in `tests/test_debate_fallback.py`. Proceeding with this proposal would duplicate existing code and waste engineering effort.

## Concessions
- Identifying the onboarding cliff caused by the LiteLLM proxy requirement is a highly accurate assessment of user friction.
- The tradeoff analysis correctly concludes that single-model structured review is dramatically better than abandoning the review entirely.
- Using the `ANTHROPIC_API_KEY` directly is the correct fallback strategy since Claude Code users are guaranteed to have it configured.

## Verdict
REJECT because the proposed feature is already fully implemented and actively tested in the current codebase (`_call_with_model_fallback` in `debate.py` and `activate_fallback` in `llm_client.py`).

---

## Challenger D (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL] [COST:SMALL]:** The proposal assumes the Anthropic API key is always available in the environment because "the user is running Claude Code." This is not guaranteed — Claude Code can run via OAuth/session tokens, enterprise proxies, or bedrock/vertex backends where `ANTHROPIC_API_KEY` is not set as an environment variable. The fallback path could fail silently or with a confusing error in exactly the environments where LiteLLM is also absent (corporate setups, CI, managed environments). The proposal should verify key availability before advertising the fallback as zero-setup.
   - SPECULATIVE: No data on what fraction of Claude Code users have `ANTHROPIC_API_KEY` set vs. other auth mechanisms.

2. **ALTERNATIVE [MATERIAL] [COST:TRIVIAL]:** The proposal skips the simplest possible fallback: using `llm_client.py`'s *existing* fallback mechanism. The manifest shows `is_fallback_active`, `get_fallback_model`, `activate_fallback`, and `_reset_fallback_state` already exist in `scripts/llm_client.py`. The proposal acknowledges the client "already uses OpenAI-compatible API format" but then proposes adding a new `urllib.request` path for Anthropic's Messages API — bypassing the existing fallback infrastructure entirely. The candidate set should include "wire debate.py to the existing llm_client fallback" as a distinct option before building new transport code.

3. **ASSUMPTION [MATERIAL] [COST:SMALL]:** The proposal treats "same artifact format = no downstream impact" as self-evident, but hooks like `hook-post-build-review.py` and `hook-spec-status-check.py` may read metadata fields (model provenance, reviewer count, confidence signals) that would differ or be absent in single-model output. The claim "downstream consumers don't need to know the difference" is asserted, not verified. If any hook gates on multi-model consensus signals, the fallback artifacts could silently pass gates they shouldn't.

4. **ALTERNATIVE [ADVISORY] [COST:SMALL]:** A missing candidate is **local single-call review** — instead of simulating three sequential persona calls (which still costs three API round-trips and produces three separate LLM invocations), a single call with a structured prompt asking the model to evaluate through PM, Security, and Architecture lenses simultaneously. This is cheaper, faster, and more honest about what's happening (one model, one call, three sections). The proposal's three-sequential-calls approach preserves the *appearance* of multi-model review without the substance, which could mislead users about review quality.

5. **ASSUMPTION [ADVISORY]:** The severity framing — "single biggest onboarding cliff," "every session where someone skips /review" — is asserted without measurement data. The proposal doesn't cite telemetry showing how often LiteLLM is absent or how often `/review` is skipped. `scripts/session_telemetry_query.py` and `scripts/lesson_events.py` exist in the codebase and could answer this. The scope of the change (new transport layer, new fallback state machine) should be proportional to evidenced frequency, not assumed frequency.
   - SPECULATIVE: No usage data cited.

6. **OVER-ENGINEERED [ADVISORY] [COST:SMALL]:** The proposal adds a new `urllib.request` Anthropic transport to `llm_client.py` when the existing client already has `_anthropic_call` (visible in the exported functions list). Adding a second Anthropic call path creates two code paths to maintain and two places where auth, retry, and error handling can diverge. The frame should ask "can the existing `_anthropic_call` path be used directly?" before introducing new transport code.

---

## Concessions

1. **The core insight is correct:** The gap between "no review" and "single-model structured review" is larger than the gap between single-model and multi-model review. Lowering the floor is genuinely valuable.
2. **Transparency design is sound:** One stderr line with a pointer to docs is the right UX — not a warning modal, not silent degradation, not a hard failure.
3. **Scope containment is appropriate:** Limiting changes to `debate.py` and `llm_client.py`, leaving hooks, skills, and artifact format untouched, is the right boundary.

---

## Verdict

**REVISE** — The proposal's goal is sound but the candidate set has a material gap: it doesn't consider wiring to the *existing* `llm_client.py` fallback infrastructure (which already exists) before proposing new transport code, and it doesn't verify that `ANTHROPIC_API_KEY` is reliably available in the environments where LiteLLM is absent. These two issues should be resolved before implementation begins.

---

## Challenger E (frame-factual) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The proposal is stale: the core “add single-model fallback when LiteLLM is unavailable” behavior already exists in the codebase. `scripts/llm_client.py` already routes to Anthropic on proxy connection refusal and emits the same warning text the proposal asks for: `“LiteLLM proxy unavailable — running single-model review.\nFor cross-model review, see docs/infrastructure.md”` (`scripts/llm_client.py:536-585`). `scripts/debate_common.py:81-91` also pre-activates fallback when `LITELLM_MASTER_KEY` is absent but `ANTHROPIC_API_KEY` is present. Recommending this as new work would duplicate shipped functionality.

2. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal claims `/challenge` and `/review` “fail entirely” if LiteLLM is unavailable, but current behavior contradicts that. `debate.py` loads credentials through `debate_common._load_credentials()` (`scripts/debate.py:3042-3045`), and that helper explicitly allows Anthropic-only operation by activating fallback (`scripts/debate_common.py:81-91`). Since `llm_client._dispatch()` then routes calls to `_anthropic_call()` in fallback mode (`scripts/llm_client.py:541-560`), the stated onboarding cliff is overstated. If there is still a UX problem, it is narrower than the proposal says and should be reframed around commands/features that still degrade poorly.

3. [ASSUMPTION] [ADVISORY]: “No changes to `config/debate-models.json`” is not the interesting claim, because the system already has debate-level fallback and timeout fallback wired through config. `single_review_default` is present and set to `gpt-5.4`, `persona_model_map` is populated, and `refine_rotation` already contains three models (`config/debate-models.json` via `read_config_value`). Also, `debate_common._get_fallback_model()` already consults `single_review_default` for timeout recovery (`scripts/debate_common.py:122-129`). The proposal treats fallback as absent infrastructure when in reality there are two fallback layers already: provider fallback in `llm_client.py` and model fallback in `debate_common.py`.

4. [UNDER-ENGINEERED] [ADVISORY]: The proposal says fallback should apply to `challenge`, `review-panel`, `judge`, and `refine`, but it does not account for an existing limitation in panel/tool flows: `cmd_review` explicitly disables `--enable-tools` in fallback mode (`scripts/debate.py:3121-3124`). So “same interface” is not fully true today for review-with-tools, and any remaining proposal should target closing that precise gap rather than re-adding generic fallback.

## Concessions
- The proposal’s motivation about preserving artifact compatibility is directionally right; current fallback is implemented below the command layer, which helps keep interfaces stable.
- It is correct that single-model fallback loses cross-family disagreement; config shows normal routing spans Claude/GPT/Gemini.
- It is reasonable to care about onboarding friction around LiteLLM, even though the repo has already addressed part of it.

## Verdict
REVISE — the proposal’s central premise is falsified by current code: Anthropic single-model fallback is already shipped, so the recommendation must be rewritten around actual remaining gaps rather than re-proposing existing behavior.

---

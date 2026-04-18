---
debate_id: litellm-fallback-v3
created: 2026-04-18T10:00:08-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# litellm-fallback-v3 — Refined Document

## Round 1 (gemini-3.1-pro)
The proposal correctly identifies a severe onboarding friction point and proposes a pragmatic, high-leverage solution. A degraded single-model review is vastly superior to a hard failure.

**Improvements made during refinement:**
1. **The Auth Assumption (Completeness):** The original draft assumed `ANTHROPIC_API_KEY` is always present in the environment because the user is running Claude Code. This is false—Claude Code defaults to OAuth for Pro users. If the key is missing, the fallback would crash. Added an explicit check: if LiteLLM is down *and* there is no API key, fail gracefully with clear instructions.
2. **Payload Translation (Correctness):** `llm_client.py` currently builds OpenAI-formatted payloads. Anthropic's Messages API requires a different structure (specifically, extracting the `system` prompt out of the messages array and into a top-level parameter). Added explicit requirements for this translation in the implementation section so the developer doesn't just blindly forward OpenAI JSON to Anthropic.
3. **Model Selection:** Specified exactly which model the fallback should use rather than leaving it ambiguous.

### Frame Check
Frame check: document's frame is sound. (The auth assumption is a completeness gap, fixed inline via prose polish).

***

## Round 2 (gpt-5.4)
The proposal is already clear and action-oriented. The strongest parts are its concrete fallback behavior, explicit non-goals, and preservation of artifact compatibility. I made targeted improvements to tighten scope, remove a likely overclaim, and specify a few operational details that were implied but not stated.

Main improvements:
- Narrowed the problem framing from “single biggest onboarding cliff” to a strong but less absolute claim, since no supporting onboarding data is included.
- Clarified that fallback activation should be limited to LiteLLM availability failures, not arbitrary first-call failures from other causes.
- Made mode behavior more deterministic by stating that fallback mode persists for the current command invocation once triggered.
- Tightened the Anthropic translation requirements so implementers know how to handle the system message and preserve persona prompts.
- Preserved all original recommendations and structure while making the document more executable.

Remaining caveat:
- The proposal assumes `ANTHROPIC_API_KEY` is the right default direct-provider fallback. That is reasonable for a narrow implementation, but it is still a load-bearing assumption for the recommendation.

### Frame Check
- [Inflated problem]: The proposal frames LiteLLM dependency as “the single biggest onboarding cliff” and implies broad session-level impact without supporting evidence — this affects how strongly the change is justified and cannot be resolved by prose polish alone.
- [Unstated load-bearing assumption]: The recommendation assumes Anthropic direct access is the right and sufficient fallback path for most users; if many users rely on OAuth-only Claude Code or non-Anthropic providers, the recommendation’s impact is materially reduced — this requires product-scope validation, not just wording changes.

## Final Refined Document

# Proposal: LiteLLM Graceful Degradation — Single-Model Fallback

## Problem

BuildOS's most differentiated features — `/challenge` and `/review` — currently depend on a running LiteLLM proxy (`localhost:4000`) with multiple providers configured. When LiteLLM is unavailable, these features fail entirely. This creates a meaningful onboarding barrier: users can reach the point where BuildOS would provide the most value, then hit infrastructure setup before they can use it.

When someone skips `/review` because LiteLLM is not configured, they lose the structured review pipeline that most clearly differentiates BuildOS from raw Claude Code. The highest-value workflow is currently gated behind the heaviest infrastructure requirement.

## Proposed Solution

When `debate.py` detects that LiteLLM is unavailable, fall back to single-model review using the Anthropic API directly.

Fallback should trigger only for LiteLLM availability failures — for example, connection refused, connection timeout, or equivalent proxy-unreachable errors for `localhost:4000`. It should not activate for unrelated model or prompt errors returned by a working LiteLLM instance.

Once fallback mode is activated for a command invocation, all subsequent model calls in that invocation should use the fallback path for consistency.

### Behavior

1. **Detection:** On a LiteLLM availability failure (connection refused / timeout to the LiteLLM proxy), check for `ANTHROPIC_API_KEY` in the environment.
2. **Fallback routing:** If the key is present, switch to fallback mode. Use the Anthropic API directly (`claude-3-5-sonnet-latest`) for all requests in that command.
3. **Hard Failure (No Key):** If LiteLLM is down and `ANTHROPIC_API_KEY` is missing (for example, the user is using Claude Code via OAuth), fail cleanly with: `Error: LiteLLM unavailable and ANTHROPIC_API_KEY not set. Please start LiteLLM or export ANTHROPIC_API_KEY to run reviews.`
4. **Same interface:** Run the same three lenses (PM, Security, Architecture) sequentially with the same structured output format. Write the same artifact files (`tasks/<topic>-challenge.md`, `tasks/<topic>-review.md`).
5. **Transparency:** Print one line to stderr: `LiteLLM unavailable — running single-model fallback via Anthropic API. For cross-model review, see docs/infrastructure.md`
6. **No degradation in artifact format:** The output files must have identical structure whether generated by 3 models or 1. Downstream consumers (hooks, skills) require zero changes.

### What changes

- **`scripts/llm_client.py`**: Add a fallback path that calls the Anthropic API directly via `urllib.request` when LiteLLM is unreachable.
  - *Implementation detail:* The client must translate the existing OpenAI-compatible message array into Anthropic's format.
  - Extract any `{"role": "system", "content": "..."}` message and pass it as the top-level `"system"` field in the Anthropic payload.
  - Preserve the remaining conversation messages in Anthropic-compatible form so persona prompts and user content remain intact.
  - Include the `anthropic-version: 2023-06-01` header.
- **`scripts/debate.py`**: In multi-model commands (`challenge`, `review-panel`, `judge`, `refine`), when fallback mode is active, route all persona requests to the fallback client. The persona system prompts still apply — each lens still gets its distinct framing (PM, Security, Architecture) — but they all execute sequentially on the same model.
- **`config/debate-models.json`**: No changes. The fallback bypasses the model routing configuration entirely.

### What does NOT change

- Hook behavior (all hooks work the same)
- Artifact format (same YAML frontmatter, same finding structure)
- Skill interfaces (skills read artifacts, not model metadata)
- Full multi-model path (when LiteLLM is available, everything works as before)
- The `refine` command's core logic (it falls back to single-model iterative improvement)

### Tradeoffs

**What you lose in fallback mode:**
- Cross-family disagreement (Claude, GPT, Gemini catch different things)
- Independent evaluation (a single model has correlated blind spots)
- Model diversity in refinement rounds

**What you keep:**
- Structured review through PM/Security/Architecture lenses
- Artifact generation for hooks and gates
- A usable review workflow without requiring LiteLLM setup first

**Why this is acceptable:** A single-model review through three structured lenses is substantially better than no review. The step from “no review” to “single-model review” is large enough to justify the fallback, even though it does not replace the value of cross-model review.

## Expected Impact

- **New users:** Can run `/review` and `/challenge` in an initial session without LiteLLM setup, provided they export an Anthropic key.
- **Existing users:** No change when LiteLLM is running.
- **Onboarding path:** `clone → setup → /think → /plan → build → /review` can work end-to-end without stopping to configure a proxy.
- **Upgrade path:** Users see the `LiteLLM unavailable` message, then can later set up multi-model review for higher-quality output instead of being blocked up front.

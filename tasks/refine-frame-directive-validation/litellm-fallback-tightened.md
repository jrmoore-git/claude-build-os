---
debate_id: litellm-fallback-tightened
created: 2026-04-18T09:54:40-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# litellm-fallback-tightened — Refined Document

## Round 1 (gemini-3.1-pro)
The proposal correctly identifies a massive friction point (infrastructure dependency for core features) and offers a highly pragmatic degradation path. The logic that "1-model review > 0-model review" is sound and directly serves user adoption. 

The only gap was an unstated assumption: that `ANTHROPIC_API_KEY` is always present in the environment when using Claude Code (which relies heavily on OAuth). This has been addressed inline by adding an explicit check and failure message for the missing key, ensuring the fallback itself fails gracefully. The implementation steps have been sharpened to be immediately executable.

### Frame Check
(c) Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The revision is already strong: it has a clear failure mode, a concrete fallback, preserved artifact compatibility, and a decisive recommendation set. I did not find a frame defect that requires restructuring.

Main improvements made:
- Tightened the problem statement to avoid overstating the issue as a universal/systemic failure.
- Clarified the exact fallback trigger so it does not activate on arbitrary first-call failures unrelated to LiteLLM availability.
- Made the command behavior more executable by specifying where fallback applies and how output compatibility is preserved.
- Added implementation constraints around error classification, one-time notice behavior, and command coverage to reduce ambiguity.
- Kept all three original recommendations intact, as required.

Remaining caveat addressed inline rather than as a frame concern:
- “First LLM call failure” was too broad; a transient upstream/provider error is not the same as the local proxy being unreachable. This is fixable within the existing structure by narrowing the trigger to proxy-unreachable conditions.

### Frame Check
Frame check: document's frame is sound.

## Final Refined Document

# Proposal: LiteLLM Graceful Degradation — Single-Model Fallback

## Problem

BuildOS's most differentiated features — `/challenge` and `/review` — currently depend on a running LiteLLM proxy (`localhost:4000`) with Anthropic, OpenAI, and Google providers configured. When the proxy is unreachable, these features fail instead of degrading to a simpler path. That makes review workflows harder to use in early setup and creates a significant onboarding cliff.

Today, the review pipeline delivers substantially more value than raw single-pass model output, but access to that value is gated behind the heaviest infrastructure requirement in the default workflow.

## Proposed Solution

When `debate.py` detects that the LiteLLM proxy is unreachable at `localhost:4000`, gracefully degrade to a single-model review using the Anthropic API directly.

This fallback should preserve the existing review workflow shape: same commands, same persona prompts, same artifact files, and same downstream interfaces. The only change is routing: instead of sending persona-specific requests through LiteLLM, send them sequentially to a single Anthropic model.

### Behavior

1. **Detection:** If a request to the LiteLLM proxy fails because the proxy is unreachable — specifically connection refused, connection timeout, or another local transport error to `localhost:4000` — switch to fallback mode for that command invocation. Do not trigger fallback for normal model/provider errors returned by a reachable proxy.
2. **Environment Check:** Verify that `ANTHROPIC_API_KEY` is present before making fallback requests. If it is missing, abort with a clear error requiring either the proxy or the key.
3. **Fallback Routing:** Route requests directly to the Anthropic Messages API using the session's default Claude model.
4. **Interface Preservation:** Run the same three lenses (PM, Security, Architecture) sequentially with the same structured output format. Write the same artifact files (`tasks/<topic>-challenge.md`, `tasks/<topic>-review.md`).
5. **Transparency:** Print exactly one line to stderr, once per command invocation: `"LiteLLM unavailable — running single-model review. For cross-model review, see docs/infrastructure.md"`
6. **Artifact Consistency:** Generate output files with the same structure as the multi-model path so downstream consumers (hooks, skills) do not need special-case logic.

## Proposed Changes

1. **Modify `scripts/llm_client.py`:**
   - Add a fallback path triggered only by proxy-unreachable errors when calling LiteLLM.
   - Implement direct Anthropic API calls using `urllib.request` and the Anthropic Messages API format, bypassing the OpenAI-compatible format used for the proxy.
   - Add an explicit check for `ANTHROPIC_API_KEY`. If absent during fallback, raise: `"LiteLLM proxy unreachable and ANTHROPIC_API_KEY missing. Set up LiteLLM or export ANTHROPIC_API_KEY to use review features."`
   - Keep error classification explicit: transport failures to `localhost:4000` trigger fallback; HTTP/application errors from a reachable proxy do not.

2. **Modify `scripts/debate.py`:**
   - Update multi-model commands (`challenge`, `review-panel`, `judge`, `refine`) to honor fallback mode.
   - When fallback is active, route all persona/model requests to the single available model.
   - Apply the persona system prompts exactly as before (PM, Security, Architecture) so the lens framing remains intact even when all passes use the same model.
   - Ensure fallback mode is scoped to the current invocation, so the next command retries LiteLLM normally.

3. **Preserve `config/debate-models.json`:**
   - Make no changes. The fallback logic bypasses model routing entirely when active.

### What Does NOT Change

- Hook behavior: all hooks execute normally.
- Artifact format: identical YAML frontmatter and finding structure.
- Skill interfaces: skills read artifacts, not model metadata.
- Full multi-model path: when LiteLLM is available, the proxy handles routing as before.
- The `refine` command's core logic: it still performs iterative improvement, but uses the single-model fallback route when the proxy is unreachable.

## Tradeoffs

**What you lose in fallback mode:**
- Cross-family disagreement: Claude, GPT, and Gemini often catch different categories of issues.
- Independent evaluation: a single model has correlated blind spots across personas.
- Model diversity in refinement rounds.

**What you keep:**
- Structured review through distinct PM, Security, and Architecture lenses.
- Unbroken artifact generation for downstream hooks and gates.
- The user habit of reviewing code instead of skipping review when infrastructure is incomplete.

**Why this is acceptable:** A single-model review forced through three structured lenses is materially better than no review. For onboarding, the value gap between “no review” and “single-model review” is larger than the value gap between “single-model review” and “cross-model review.”

## Expected Impact

- **New users:** Can execute `/review` and `/challenge` in their first session with no LiteLLM setup, provided `ANTHROPIC_API_KEY` is available.
- **Existing users:** Experience no change when LiteLLM is running.
- **Onboarding path:** The core loop (Clone → setup → `/think` → `/plan` → build → `/review`) works end-to-end with Claude Code plus an Anthropic API key.
- **Upgrade path:** Users see the fallback message, receive baseline review value immediately, and retain a clear path to the full multi-model setup later.

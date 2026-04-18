---
debate_id: litellm-fallback-v5
created: 2026-04-18T11:30:23-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# litellm-fallback-v5 — Refined Document

## Round 1 (gemini-3.1-pro)
The proposal identifies a high-friction onboarding bottleneck (LiteLLM configuration) and proposes a highly pragmatic solution (graceful degradation to single-model review). 

I addressed one critical unstated assumption inline: the proposal assumed `ANTHROPIC_API_KEY` is always in the environment if Claude Code is running. However, Claude Code users often authenticate via OAuth, meaning the environment variable won't exist. I updated the fallback logic to explicitly check for this key and provide a clear error message if it's missing, preventing a confusing secondary crash. I also specified the exact fallback model (`claude-3-5-sonnet-latest`) to make the implementation immediately executable.

### Frame Check
Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The revision is directionally strong: it proposes a concrete fallback, preserves the existing artifact contract, and avoids adding new dependencies. I tightened the frame by removing one unsupported claim ("single biggest onboarding cliff") and by making the recommendation sharper about scope: this fallback addresses only the "LiteLLM proxy unavailable" case, not all review failures.

Main improvements in the revised document:
- Narrowed the problem statement to what the text actually supports: review features fail when the local LiteLLM proxy is unavailable.
- Made the fallback trigger more precise and safer: only network-unavailable conditions should activate fallback; provider auth/model errors on the LiteLLM path should surface normally.
- Clarified command coverage so the implementation does not silently overreach. The proposal names the multi-model commands it affects and preserves normal behavior elsewhere.
- Added concrete implementation details for the Anthropic payload translation and artifact/exit-code expectations.
- Preserved the original recommendation set as one actionable proposal, but made it more executable with explicit non-goals, failure behavior, and rollout checks.
- Kept the decisiveness of the original proposal rather than softening it into a study/pilot.

### Frame Check
Frame check: document's frame is sound.

## Final Refined Document

# Proposal: LiteLLM Graceful Degradation — Single-Model Fallback

## Problem

BuildOS's `/challenge` and `/review` flows currently depend on a running LiteLLM proxy at `localhost:4000` with multiple providers configured. When that proxy is unavailable, these features fail with a generic connection error instead of degrading to a usable local path.

That creates an avoidable failure mode in onboarding and day-to-day use: review-capable commands stop working not because review itself is impossible, but because the preferred multi-model router is missing.

## Proposed Solution

When `debate.py` detects that the LiteLLM proxy is unreachable, degrade to a single-model review path that calls the Anthropic Messages API directly.

This is a fallback for one specific failure mode: local LiteLLM proxy unavailable. It is not a replacement for the normal multi-model path, and it should not mask upstream provider errors, bad model configuration, or invalid requests when LiteLLM is running.

### Behavior and Implementation Steps

1. **Detection**
   Wrap the initial LiteLLM proxy call. If the proxy is unreachable, trigger fallback mode.

   Fallback should activate for connection-level failures such as:
   - `ConnectionRefusedError`
   - connection timeout
   - other local transport errors indicating `localhost:4000` is not serving

   Fallback should **not** activate for:
   - LiteLLM returning a valid HTTP response with a provider/auth/model error
   - malformed request payloads
   - rate limits or server-side errors returned through a functioning LiteLLM proxy

   Those cases should surface normally so real configuration problems are not hidden.

2. **Key Validation**
   Check for `ANTHROPIC_API_KEY` in the environment.

   If missing, abort cleanly with:
   `LiteLLM proxy unavailable (localhost:4000) and ANTHROPIC_API_KEY not found in environment. To run reviews, either start LiteLLM or export ANTHROPIC_API_KEY.`

   Note: users authenticated through Claude Code/OAuth may not have this environment variable available locally, so fallback cannot assume it exists.

3. **Fallback Routing**
   POST directly to `https://api.anthropic.com/v1/messages` using `urllib.request` so this change adds no new dependency.

   Hardcode the fallback model to:
   - `claude-3-5-sonnet-latest`

   The fallback path should include a minimal payload translator from the current OpenAI-compatible internal request shape to Anthropic Messages API format.

4. **Execution**
   Run the same three lenses sequentially:
   - PM
   - Security
   - Architecture

   The existing persona system prompts still apply, but all three lenses run on the same fallback model.

5. **Transparency**
   Print exactly one line to `stderr` before execution:
   `LiteLLM unavailable — running single-model review. For cross-model review, see docs/infrastructure.md`

   Print it once per top-level command invocation, not once per lens.

6. **No Degradation in Artifact Format**
   Write the exact same artifact files:
   - `tasks/<topic>-challenge.md`
   - `tasks/<topic>-review.md`

   Preserve the same YAML frontmatter and finding structure so downstream hooks, skills, and gates require no changes.

### What Changes

- **`scripts/llm_client.py`**
  - Add a fallback execution path for direct Anthropic calls.
  - Implement the request translator inside the fallback block.
  - Map the current message structure into Anthropic's `system` + `messages` format.
  - Preserve existing response handling so callers receive the same normalized text output shape.

- **`scripts/debate.py`**
  - In multi-model commands that currently depend on model rotation, bypass that rotation when fallback mode is active.
  - Route those requests through the fallback client instead of the LiteLLM client.
  - Ensure fallback is decided once per command invocation and reused consistently across all lenses in that run.

- **`config/debate-models.json`**
  - No changes.
  - Fallback bypasses the routing table entirely.

### What Does Not Change

- Hook behavior
- Artifact format
- Skill interfaces
- Full multi-model behavior when LiteLLM is available
- The normal provider-routing path through LiteLLM
- The `refine` command's core logic; it still performs iterative improvement, but uses the fallback model when fallback mode is active

## Tradeoffs

**What you lose in fallback mode:**
- Cross-family disagreement
- Independent evaluation across different model families
- Some error isolation benefits that come from comparing outputs from distinct providers

**What you keep:**
- Structured review through distinct PM, Security, and Architecture lenses
- Artifact generation compatible with existing downstream tooling
- A working review path when the local proxy is missing

**Why this is acceptable:**
The fallback preserves the review workflow and artifact contract in a degraded but still useful form. The main value of the feature is retained: users still get a structured review instead of a connection failure.

## Expected Impact

- **New users:** Can run `/review` and `/challenge` without first bringing up LiteLLM, provided `ANTHROPIC_API_KEY` is present.
- **Existing users:** No behavior change when LiteLLM is running.
- **Operational path:** `clone → setup → /think → /plan → build → /review` can complete without a local proxy, as long as the Anthropic API key is exported.
- **Upgrade path:** The single stderr notice points users to the multi-model setup without interrupting the command.

## Recommendation

Implement a direct-Anthropic fallback for LiteLLM-unavailable conditions, with these constraints:

1. Trigger fallback only for local proxy reachability failures, not for errors returned by a functioning LiteLLM instance.
2. Require `ANTHROPIC_API_KEY` and fail with the explicit message above if it is absent.
3. Use `urllib.request` and `claude-3-5-sonnet-latest` for the fallback path.
4. Keep the existing three-lens review flow and artifact format unchanged.
5. Emit exactly one stderr notice per command invocation when fallback is active.
6. Apply the fallback path to the multi-model commands named in this proposal and leave all normal LiteLLM behavior unchanged when the proxy is available.

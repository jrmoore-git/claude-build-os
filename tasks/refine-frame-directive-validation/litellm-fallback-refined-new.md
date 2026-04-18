---
debate_id: litellm-fallback-refined-new
created: 2026-04-18T09:43:49-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# litellm-fallback-refined-new — Refined Document

## Round 1 (gemini-3.1-pro)
This is a strong, pragmatic proposal. Graceful degradation for the heaviest infrastructure requirement (LiteLLM) directly addresses the primary onboarding friction point. The tradeoffs are clearly articulated and acceptable. 

The main area requiring refinement is the assumption that `ANTHROPIC_API_KEY` is reliably present in the environment just because Claude Code is running. Claude Code often manages its own authentication (e.g., via OAuth or internal config) without exporting the key to the shell environment where these scripts execute. The implementation must account for this to prevent the fallback from immediately failing.

### Frame Check
- Unstated load-bearing assumption: The proposal assumes `ANTHROPIC_API_KEY` is automatically available in the environment because Claude Code is running. This requires a structural change to the implementation plan to either parse Claude Code's config or explicitly prompt the user for the key if it is missing from the environment.

## Round 2 (gpt-5.4)
The revision is already clear and action-oriented. I strengthened it by making the fallback trigger more precise, tightening scope around when fallback is allowed, and clarifying user-visible behavior and command coverage. I also removed a few claims that were stronger than the proposal’s support and made the implementation guidance more executable without adding hedging.

Remaining issues addressed in the revision:
- The original trigger mixed “first LLM call failure” with specific transport failures; the revised doc limits fallback to proxy-unavailable conditions rather than broad model/API failures.
- “Prompt the user to provide/export” could imply interactive input; the revised doc makes the required behavior explicit: fail with a clear instruction if `ANTHROPIC_API_KEY` is absent.
- The proposal said “single-model fallback” but did not explicitly distinguish infrastructure failure from ordinary provider/model errors; the revised doc now does.
- The scope of command behavior is preserved, but the fallback semantics are made more concrete for `judge` and `refine`.

### Frame Check
Frame check: document's frame is sound.

## Final Refined Document

# Proposal: LiteLLM Graceful Degradation — Single-Model Fallback

## Problem

BuildOS's most differentiated features — `/challenge` and `/review` — currently depend on a running LiteLLM proxy at `localhost:4000` with multiple providers configured. When that proxy is unavailable, these features fail entirely. This creates a steep onboarding failure mode: the highest-value review workflow is gated behind the heaviest infrastructure requirement.

The practical issue is not that cross-model review is optional; it is that today there is no usable degraded mode when the proxy is down or unconfigured. A user who can otherwise run BuildOS with Claude Code and an Anthropic API key can still lose `/challenge` and `/review` completely.

## Proposed Solution

When LiteLLM is unavailable, fall back to single-model review by calling the Anthropic API directly.

Fallback is only for LiteLLM availability failures — for example, connection refused or timeout to `localhost:4000`. It is not a catch-all retry path for unrelated model errors, malformed requests, or downstream provider failures returned through a healthy LiteLLM proxy.

### Behavior

1. **Detection:** If a request to the LiteLLM proxy fails because the proxy is unreachable or times out, mark the current command execution as fallback mode.
2. **Fallback routing:** In fallback mode, route requests directly to the Anthropic Messages API using `ANTHROPIC_API_KEY`.
3. **Missing key behavior:** If `ANTHROPIC_API_KEY` is not present, exit with a clear, actionable error telling the user to export it. Do not fail silently and do not drop into a partial run.
4. **Same interface:** Run the same three lenses — PM, Security, and Architecture — sequentially using the single available model, and write the same artifact files (`tasks/<topic>-challenge.md`, `tasks/<topic>-review.md`).
5. **Transparency:** Print one actionable warning to stderr: `[WARN] LiteLLM unavailable — running single-model review. For cross-model review, see docs/infrastructure.md`
6. **No artifact-format change:** Output files keep the same structure in both modes so downstream hooks and skills do not need to detect fallback state.

### What changes

- `scripts/llm_client.py`: Add a fallback path for LiteLLM transport failures that calls the Anthropic API directly. Since Anthropic's Messages API does not use the same payload shape as the OpenAI-compatible LiteLLM endpoint, implement the fallback request separately using `urllib.request`. If `ANTHROPIC_API_KEY` is missing, terminate with a clear setup instruction.
- `scripts/debate.py`: In multi-model commands (`challenge`, `review-panel`, `judge`, `refine`), when fallback mode is active, route all persona/model invocations to the same Anthropic-backed client. Keep the persona system prompts intact so PM, Security, and Architecture still run as distinct lenses, even though they are executed sequentially by one model.
- `config/debate-models.json`: No changes. Fallback bypasses normal model routing.

### What does NOT change

- Hook behavior: hooks execute exactly as before.
- Artifact format: YAML frontmatter and finding structure stay the same.
- Skill interfaces: skills consume artifacts, not model metadata.
- Full multi-model path: when LiteLLM is available, standard cross-model debate runs unchanged.
- `refine` behavior: refinement still runs as iterative improvement; in fallback mode, the iterations use the single available model instead of rotating across providers.

### Tradeoffs

**What you lose in fallback mode:**
- Cross-family disagreement between model providers
- Independent evaluation from multiple model families
- Model diversity during refinement

**What you keep:**
- Structured review through PM, Security, and Architecture lenses
- Artifact generation for hooks and gates
- A usable review workflow when the proxy is not available

**Why this tradeoff is acceptable:** Single-model structured review is materially better than no review. This proposal preserves the workflow and artifacts that make `/challenge` and `/review` useful, while reserving cross-model diversity as an upgrade unlocked by running LiteLLM.

## Expected Impact

- **New users:** Can run `/review` and `/challenge` without first setting up LiteLLM, as long as they have an Anthropic API key configured.
- **Existing users:** No change when LiteLLM is running.
- **Onboarding path:** A user can go from clone → setup → `/think` → `/plan` → build → `/review` with only Claude Code and `ANTHROPIC_API_KEY`.
- **Upgrade path:** The warning message makes the degraded state visible and points users to the infrastructure docs when they want full cross-model review.

---
debate_id: drift__03-litellm-fallback-onboarding-cliff__pass
created: 2026-04-18T13:21:14-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# drift__03-litellm-fallback-onboarding-cliff__pass — Challenger Reviews

## Challenger A (pm) — Challenges
This diff introduces a valuable fallback path to solve a major onboarding friction point, but the implementation is fundamentally incomplete and will cause downstream crashes. It fails to implement several key requirements from the refined spec.

### PM & Acceptance
*   **[MATERIAL] Scope & Completeness:** The proposed scope and value prop is excellent. Resolving the LiteLLM onboarding cliff is a high-leverage change. However, the diff only partially implements the backend request routing and ignores the required frontend (CLI) behavior and state persistence.
*   **[MATERIAL] Response Format / Interface Breakage:** The `_anthropic_direct_request` method accurately translates the *request* to Anthropic's format, but it returns the raw Anthropic *response* structure (`{"content": [{"text": "..."}]}`). Callers of `llm_request` expect an OpenAI-formatted response (`{"choices": [{"message": {"content": "..."}}]}`). This will crash downstream code and violates the spec's requirement for a seamless interface.

### Spec Violations
The following material violations of the provided spec must be fixed:

*   **[MATERIAL] SPEC VIOLATION (State Persistence):** The spec mandates: *"Once fallback mode is activated for a command invocation, all subsequent model calls in that invocation should use the fallback path for consistency."* The diff completely omits the required `scripts/debate.py` changes. The fallback in `llm_client.py` evaluates per-request, meaning a flapping proxy could cause mid-invocation model toggling.
*   **[MATERIAL] SPEC VIOLATION (Transparency):** The spec explicitly requires: *"Print one line to stderr: `LiteLLM unavailable — running single-model fallback via Anthropic API. For cross-model review, see docs/infrastructure.md`"*. The diff does not print this message.
*   **[MATERIAL] SPEC VIOLATION (Clean Failure):** The spec mandates: *"fail cleanly with: Error: LiteLLM unavailable and ANTHROPIC_API_KEY not set. Please start LiteLLM or export ANTHROPIC_API_KEY to run reviews."* The diff instead raises a raw Python exception (`LiteLLMUnavailableError`) with a non-matching message, which will dump a stack trace to the user rather than failing cleanly.
*   **[MATERIAL] SPEC VIOLATION (Artifact/Interface Degradation):** The spec mandates: *"No degradation in artifact format: The output files must have identical structure... Downstream consumers (hooks, skills) require zero changes."* Because the response is not mapped back to the OpenAI schema, downstream parsers will fail, preventing artifact generation altogether.

**Recommendation:** Reject. While the strategy is sound, the implementation creates a broken state due to mismatched response shapes and misses the state management required for a coherent user experience. Fix the response translation mapping and implement the `scripts/debate.py` persistence.

---

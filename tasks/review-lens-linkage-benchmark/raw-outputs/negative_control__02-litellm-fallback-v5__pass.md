---
debate_id: negative_control__02-litellm-fallback-v5__pass
created: 2026-04-18T13:21:10-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# negative_control__02-litellm-fallback-v5__pass — Challenger Reviews

## Challenger A (pm) — Challenges
**REVIEW: PM / Acceptance Lens**

**Evaluation of Risk and Scope:**
The proposal addresses a valid, high-friction onboarding cliff (LiteLLM proxy unavailable). The risk of *not* changing is continued degraded onboarding experience and brittle daily operations when the proxy goes down. The risk of the *proposed change* is silent masking of valid proxy errors and structural breakage in downstream consumers that expect OpenAI-compatible JSON responses. While the scope sizing is correct (fallback to single model via direct HTTP call), the implementation fails to meet several critical constraints outlined in the refined spec.

**Findings:**

*   **[MATERIAL] SPEC VIOLATION: Must preserve normalized text output shape**
    *   **Spec Clause:** "Preserve existing response handling so callers receive the same normalized text output shape."
    *   **Violation:** The diff correctly translates the *request* to Anthropic's format, but it simply returns `json.loads(resp.read())` on the response. Anthropic returns `{"content": [{"text": "..."}]}`, whereas the rest of the application expects the OpenAI format returned by LiteLLM (`{"choices": [{"message": {"content": "..."}}]}`). This will cause downstream JSON parsing errors or `KeyError`s when callers attempt to read the model's output. You must translate the Anthropic response back into the expected OpenAI shape before returning it.

*   **[MATERIAL] SPEC VIOLATION: Must not activate for server-side errors through a functioning proxy**
    *   **Spec Clause:** "Fallback should **not** activate for: LiteLLM returning a valid HTTP response with a provider/auth/model error... Those cases should surface normally so real configuration problems are not hidden."
    *   **Violation:** The diff traps `(urllib.error.URLError, ConnectionError)`. In Python, `urllib.error.HTTPError` is a subclass of `urllib.error.URLError`. This means if LiteLLM is up but returns a `401 Unauthorized` or `400 Bad Request`, `urllib.request.urlopen` will raise an `HTTPError`, which gets caught by your exception handler and incorrectly triggers the fallback. You must explicitly catch and re-raise `HTTPError` before trapping `URLError`, or check `isinstance(e, urllib.error.HTTPError)` in the except block.

*   **[MATERIAL] SPEC VIOLATION: Exact abort message required**
    *   **Spec Clause:** "If missing, abort cleanly with: `LiteLLM proxy unavailable (localhost:4000) and ANTHROPIC_API_KEY not found in environment. To run reviews, either start LiteLLM or export ANTHROPIC_API_KEY.`"
    *   **Violation:** The diff raises a `RuntimeError` with a slightly different string: `"LiteLLM unavailable and ANTHROPIC_API_KEY not set. Start LiteLLM or export ANTHROPIC_API_KEY to run reviews."`

*   **[MATERIAL] SPEC VIOLATION: Exact stderr warning string required**
    *   **Spec Clause:** "Print exactly one line to `stderr` before execution: `LiteLLM unavailable — running single-model review. For cross-model review, see docs/infrastructure.md`"
    *   **Violation:** The diff prints: `"LiteLLM unavailable — running single-model fallback via Anthropic API. For cross-model review, see docs/infrastructure.md"`

*   **[ADVISORY] Implementation of "Print exactly one line"**
    *   **Spec Clause:** "Print it once per top-level command invocation, not once per lens."
    *   **Note:** Placing the print statement inside `llm_request` with the `_fallback_active` global flag *technically* ensures it only prints once per process execution. However, if multiple requests are fired concurrently (or if errors occur deep in a loop), the output might appear mid-stream instead of "before execution" as requested by the spec. Moving the fallback decision upstream into `debate.py` initialization (as instructed in the spec: "Ensure fallback is decided once per command invocation") would be cleaner.

---

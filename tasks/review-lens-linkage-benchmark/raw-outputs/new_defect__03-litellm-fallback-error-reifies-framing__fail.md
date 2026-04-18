---
debate_id: new_defect__03-litellm-fallback-error-reifies-framing__fail
created: 2026-04-18T13:21:45-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# new_defect__03-litellm-fallback-error-reifies-framing__fail — Challenger Reviews

## Challenger A (pm) — Challenges
### PM/Acceptance Review

The proposal and implementation address a clear onboarding friction point. However, the implementation violates multiple negative constraints from the spec, which will lead to a noisy user experience and broken downstream integrations.

#### PM/Acceptance Findings

**[MATERIAL] SPEC VIOLATION: Broken Output Contract**
*   **Context:** The spec demands: "Preserve existing response handling so callers receive the same normalized text output shape."
*   **Finding:** `_anthropic_direct_request` returns the raw Anthropic API payload (`{"content": [{"text": "..."}]}`). Existing downstream code expects the LiteLLM/OpenAI payload shape (`{"choices": [{"message": {"content": "..."}}]}`). This will cause all fallback requests to fail when parsing the response.
*   **Risk:** The proposed change completely breaks the review flow instead of degrading gracefully [EVIDENCED by the missing response mapping in the diff].

**[MATERIAL] SPEC VIOLATION: Excessive Logging / State Leakage**
*   **Context:** The spec states: "Print exactly one line to `stderr` before execution... Print it once per top-level command invocation, not once per lens." and "Ensure fallback is decided once per command invocation and reused consistently".
*   **Finding:** The fallback check and the `print()` statement are located inside `llm_request`. This means the fallback is evaluated and the warning is printed on *every single API request*, leading to redundant terminal spam (at least 3 prints per command, one for each lens) [EVIDENCED by the diff placing `print` inside the request loop instead of maintaining session state].

**[MATERIAL] SPEC VIOLATION: Incorrect Missing Key Message**
*   **Context:** The spec requires the explicit abort message: `"LiteLLM proxy unavailable (localhost:4000) and ANTHROPIC_API_KEY not found in environment. To run reviews, either start LiteLLM or export ANTHROPIC_API_KEY."`
*   **Finding:** The diff uses a custom, generic error message (`"LiteLLM is required for Build OS review. Your environment is not properly configured..."`) that diverges entirely from the required UX copy.

**[MATERIAL] SPEC VIOLATION: Incorrect Fallback Notice**
*   **Context:** The spec requires the exact stderr string: `"LiteLLM unavailable — running single-model review. For cross-model review, see docs/infrastructure.md"`
*   **Finding:** The diff injects unnecessary alarmist wording (`"WARNING:"` and `"degraded"`) not present in the spec: `"WARNING: LiteLLM unavailable — running degraded single-model review."`.

**[ADVISORY] Environment Assumptions**
*   The spec correctly notes that OAuth users won't have `ANTHROPIC_API_KEY` by default. Raising `RuntimeError` immediately upon connection failure without checking configuration properly limits adoption for Claude Code users unless they manually export the key. The check works as requested, but the onboarding guide should emphasize this prerequisite explicitly to truly close the onboarding cliff.

---

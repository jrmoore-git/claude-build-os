---
debate_id: drift__03-litellm-fallback-onboarding-cliff__fail
created: 2026-04-18T13:21:01-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# drift__03-litellm-fallback-onboarding-cliff__fail — Challenger Reviews

## Challenger A (pm) — Challenges
### Spec Clause Extraction & Compliance

*   **EXCEPTION:** "If LiteLLM is down and `ANTHROPIC_API_KEY` is missing... fail cleanly with: `Error: LiteLLM unavailable and ANTHROPIC_API_KEY not set. Please start LiteLLM or export ANTHROPIC_API_KEY to run reviews.`"
*   **MUST NOT:** "It should not activate for unrelated model or prompt errors returned by a working LiteLLM instance."
*   **MUST NOT / EXPLICITLY EXCLUDED:** Hook behavior, Artifact format, Skill interfaces, and `config/debate-models.json` must not change.

---

### PM/Acceptance Findings

**[MATERIAL] SPEC VIOLATION: Missing Graceful Exception for Missing API Key**
The spec explicitly demands a clean, user-friendly error message if `ANTHROPIC_API_KEY` is missing during a fallback attempt (specifically addressing an onboarding issue where Pro users use OAuth). The diff explicitly ignores this and relies on a raw Python `KeyError` (`api_key = os.environ["ANTHROPIC_API_KEY"]  # KeyError if absent`). I verified via tool call that the required error string does not exist anywhere in the `scripts` directory. This creates a jarring developer experience that undermines the primary goal of the proposal.

**[MATERIAL] SPEC VIOLATION: Missing Transparency Warning**
The spec requires printing exactly one line to stderr: `LiteLLM unavailable — running single-model fallback via Anthropic API...` to ensure users know they are in a degraded state. The diff implements the fallback in `llm_request` but fails to print this warning. A tool check confirms this string is entirely absent from the codebase. Silent degradation is unacceptable for a tool where model diversity is a core feature.

**[MATERIAL] Incomplete Implementation (Missing `scripts/debate.py` changes)**
The spec mandates that "Once fallback mode is activated for a command invocation, all subsequent model calls in that invocation should use the fallback path for consistency." It specifies that `scripts/debate.py` should route all persona requests to the fallback client when active. The diff only touches `scripts/llm_client.py`, and implements the fallback on a per-request basis inside `llm_request` (catching the connection error every time). This means there is no session-level persistence, and it will incur a timeout/connection-refused penalty on *every single prompt* in a multi-model command.

**[ADVISORY] Retained Speculative Overclaim in Docstring**
The docstring for `_anthropic_direct_request` states: *"LiteLLM is the single biggest onboarding cliff"*. This is a **[SPECULATIVE]** quantitative claim lacking user data, and the refinement rounds specifically warned against this inflated problem framing. While it doesn't break execution, it ignores the refinement guidance.

---

### Risk Evaluation

*   **Risk of the proposed change:** The implementation as written trades an infrastructure failure for a raw Python `KeyError` (if the Anthropic key is absent), making the onboarding experience arguably *worse* and more confusing. Furthermore, the lack of session-level persistence means users will experience severe latency as the tool attempts to connect to a dead LiteLLM proxy, times out, and falls back for *every individual model call* in a debate.
*   **Risk of NOT changing:** If we discard this PR entirely, new users without LiteLLM configured will continue to experience hard blockers when attempting to use `/challenge` or `/review`, which prevents them from experiencing the platform's core value proposition.

**Recommendation:** The PR must be blocked until the `KeyError` is replaced with the specified clean failure message, the transparency warning is added, and the session-level fallback state/routing is properly implemented in `scripts/debate.py`.

---

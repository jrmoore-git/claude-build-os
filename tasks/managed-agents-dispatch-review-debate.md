---
debate_id: managed-agents-dispatch-review-debate
created: 2026-04-10T19:26:19-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# managed-agents-dispatch-review-debate — Challenger Reviews

## Challenger A — Challenges
Now I have a thorough understanding of the diff and the codebase. Let me compile the review.

---

# Code Review: Managed Agents Consolidation — Phase 1 Enhancements

## Spec Clause Extraction

**EXCEPTION / MUST NOT / EXPLICITLY EXCLUDED clauses from spec:**

1. **MUST NOT: No Ambient Context** — "Environment variables, process state, working-directory contents, local git state, and arbitrary file trees must not be implicitly synced or exposed."
2. **MUST NOT: No Secret Logging** — "Never print the key or embed it in error messages, structured logs, or exception traces."
3. **MUST NOT: Subprocess Inheritance** — "Do not export MA credentials broadly to child processes."
4. **MUST NOT: No Remote Workspace Assumption** — "Phase 1 must not depend on provider-side file access, shell execution, or tool use."
5. **MUST NOT: No executable artifacts** — "Response is treated as text data only; no code execution, file writes, or tool invocations from the response content."
6. **EXPLICITLY EXCLUDED: Non-goals** — "Replacing LiteLLM for the existing local model path," "General remote workspace execution," "Automatic file synchronization," "Refine-round offload," "Modifying the existing `_call_litellm` or LiteLLM proxy configuration."
7. **EXCEPTION: Missing Credential Behavior** — "If managed dispatch is requested but the credential is absent, log a clear non-secret error and fall back to local execution unless the caller explicitly requested hard failure."
8. **ROLLOUT GATE: Provider Security Assumptions** — "Document: authentication method, tenant isolation model, data retention policy, and whether the provider trains on customer data. This documentation is a rollout gate."
9. **MUST: Error Classification** — "Define an `MA_SAFE_EXCEPTIONS` tuple for the MA client path."
10. **MUST: Operator Visibility** — "Surface whether the final output came from MA success or local fallback, both in stderr output and in the structured event log."
11. **MUST: Cost & Accounting** — "Feed MA costs into the session cost accumulator so end-of-run summaries remain accurate."

---

## Architecture

### 1. [ADVISORY] Usage tracking only captures `assistant.message` events

In `poll_task` (line 238-241), usage is captured only inside the `if event.type == "assistant.message"` block. The Anthropic Managed Agents streaming API may emit usage information on other event types (e.g., `message_delta`, `message_stop`, or session-level summary events). If the API reports usage on a different event type, token counts will silently be zero.

**Risk of NOT changing:** Usage/cost tracking would be inaccurate, violating the spec's cost accounting requirement. **Risk of changing:** Over-counting if usage appears on multiple event types. **Evidence basis:** SPECULATIVE — depends on the actual Anthropic MA streaming event schema, which is not documented in this diff. Recommend adding a defensive log when total tokens are zero after a non-empty response to catch this case in production.

### 2. [MATERIAL] Module-level mutable global `_cached_agent` introduces statefulness risks

The `_cached_agent` global (line 98) creates implicit coupling between successive calls within the same process. This is architecturally concerning because:

- **No TTL or invalidation beyond prompt hash.** If the remote agent is deleted server-side, the cache will attempt a `retrieve`, fail, and create a new one — but only after an extra API round-trip on every call until the cache is refreshed.
- **Thread safety.** The global is read/written without any lock. `debate.py` uses `ThreadPoolExecutor` for challengers (EVIDENCED: `_session_costs_lock` exists for thread-safe cost tracking at line 781). If `cmd_judge` were ever called concurrently or if consolidation were parallelized, this would race. Currently consolidation is single-threaded, so this is low-risk today.
- **Test pollution.** Tests must manually reset `_cached_agent = None` in `finally` blocks (visible in the test diff). This is a test smell indicating the global is a maintenance burden.

The previous design used `os.environ` for caching, which the spec explicitly rejected for credential isolation reasons. The module-level variable is the right direction, but it should be documented as single-thread-only.

### 3. [ADVISORY] Environment/session separation improves reliability

The refactoring to separate environment creation from session creation (lines 166-180) is a good architectural improvement. The comment "Separated so that a session-creation retry doesn't orphan environments" is accurate — previously, `_create_session` created both env and session in one lambda, meaning a retry after session failure would create a second orphaned environment. The new `_cleanup_environment` in `finally` (line 345-347) further mitigates resource leaks.

### 4. [ADVISORY] `_retry_transient` return signature change is a breaking API change

`_retry_transient` now returns `(result, attempt)` instead of just `result`. All callers within the module are updated, but this is a public-enough internal function that any external caller would break. Since `managed_agent.py` is new and the function is prefixed with `_`, this is acceptable but worth noting for future consumers.

### 5. [MATERIAL] `dispatch_task` spec says it returns `job_id`, implementation returns `(client, session_id, lifecycle)`

The spec's "New Module" section says:
> `dispatch_task(payload, metadata, api_key) -> job_id`

The implementation returns `(client, session_id, lifecycle)`. This is a reasonable deviation — the caller needs the client for polling — but it's a spec divergence that should be acknowledged. The spec also says `poll_task(job_id, timeout_s, api_key) -> raw_result` but the implementation takes `(client, session_id, timeout_s)` and returns `(text, usage)`. These are pragmatic adaptations, not violations, since the spec describes an "implementation shape" not a rigid contract. However, the spec should be updated to match.

---

## Security

### 6. [MATERIAL] Credential leak prevention — good but incomplete

The diff makes two important security improvements:
- **Line 88-89 (managed_agent.py):** Retry logging now prints only `type(e).__name__` instead of the full exception message, preventing API key leakage from SDK error repr.
- **Line 1520-1522 (debate.py):** Same pattern in the fallback handler — logs only exception class name.
- **Removal of `traceback.print_exc()`** from the debate.py catch block eliminates a traceback that could contain the API key in stack frames.

However, there is a gap: **line 164** prints `agent_id` to stderr (`MA dispatch: agent={agent_id}`), and **line 181** prints `session.id`. These are server-side identifiers, not credentials, so this is acceptable. But the `env_id` is also stored in the lifecycle dict and logged to `debate-log.jsonl` (via `consolidation_stats["lifecycle"]`). If the log file is world-readable, these IDs could be used for reconnaissance. This is low-severity given they're ephemeral session IDs.

**Spec compliance:** Satisfies "No Secret Logging" — the API key itself is never logged. EVIDENCED: `MA_API_KEY` is read from `os.environ.get("MA_API_KEY")` at line 1496 and passed only to `run_consolidation(api_key=ma_api_key)`.

### 7. [ADVISORY] `_ma_exc` fallback tuple may be too narrow

In debate.py lines 1491-1494, if `managed_agent` can't be imported at all, `_ma_exc` falls back to `(ConnectionError, TimeoutError, OSError)`. This is a reasonable defensive measure. However, if the Anthropic SDK *is* installed but `managed_agent.py` has a syntax error, the `except Exception` on line 1493 would catch that, and the subsequent `except (_ma_exc, ValueError, RuntimeError, ImportError)` on line 1518 would miss Anthropic-specific exceptions. The `ImportError` addition to line 1518 covers the case where `from managed_agent import run_consolidation` fails. This is well-designed.

### 8. [ADVISORY] No ambient context egress — verified compliant

The spec requires "Only explicitly constructed strings and metadata intended for the remote task may be sent." EVIDENCED: `run_consolidation` at line 335-337 constructs `user_content` from `challenge_body` (the explicit input) and `challenger_count` (derived from it). The `metadata` dict at lines 323-326 contains only `debate_id`, `task_type`, and `system_prompt`. No environment variables, file paths, or process state are included. **Compliant with spec.**

### 9. [ADVISORY] Credential subprocess isolation — verified compliant

The spec requires "Do not export MA credentials broadly to child processes." The diff removes `import os` from `managed_agent.py` and replaces the `os.environ.get("MA_AGENT_ID")` caching with a module-level variable. The API key is passed as a function parameter, never written to `os.environ`. **Compliant with spec.**

---

## PM/Acceptance

### 10. [MATERIAL] Cost tracking model mismatch — `claude-sonnet-4-6` not in `_TOKEN_PRICING`

EVIDENCED: The pricing table at line 745-754 has `"claude-sonnet-4"` as a key prefix. The MA module uses `CONSOLIDATION_MODEL = "claude-sonnet-4-6"` (line 46). The `_estimate_cost` function (line 765) does `model.startswith(prefix)` matching, so `"claude-sonnet-4-6".startswith("claude-sonnet-4")` → `True`. **This works correctly** because of prefix matching. Not a bug — withdrawing material tag. [ADVISORY] — the prefix-matching approach is fragile if a model like `claude-sonnet-4-6-turbo` has different pricing, but it works for the current model.

### 11. [ADVISORY] Spec compliance — Provider Security Assumptions documented (rollout gate met)

The spec requires provider security assumptions as a **rollout gate**. EVIDENCED: Lines 9-23 of `managed_agent.py` document authentication method (Bearer token over TLS), tenant isolation (per-API-key), data retention (Anthropic policy), training policy (no, under commercial terms), and LiteLLM parity gaps. **Compliant with spec.**

### 12. [ADVISORY] Spec compliance — Operator Visibility implemented

The spec requires surfacing whether output came from MA or local fallback. EVIDENCED:
- `consolidation_stats["source"]` is set to `"local"` (line 1536) or `"managed-agent"` (line 296 in validate_result).
- `consolidation_stats["ma_fallback"]` is set (line 1537).
- `log_event["consolidation_source"]` and `log_event["ma_fallback"]` are written to the structured log (lines 1680-1681).
- stderr messages distinguish MA success vs. fallback (lines 1508, 1522, 1526).
**Compliant with spec.**

### 13. [ADVISORY] Spec compliance — Cost & Accounting implemented

The spec requires feeding MA costs into the session cost accumulator. EVIDENCED: Lines 1509-1517 in debate.py extract `usage` from `consolidation_stats`, convert from MA's `input_tokens`/`output_tokens` to the local `prompt_tokens`/`completion_tokens` convention, and call `_track_cost` and `_estimate_cost`. **Compliant with spec.**

### 14. [ADVISORY] Spec compliance — Fallback behavior correct

The spec requires: "If dispatch fails before job creation, polling times out, or the returned payload fails validation, execute the existing local `_consolidate_challenges` path." EVIDENCED: The `except` block at line 1518 sets `ma_fallback = True` and falls through to the `if not ma_used:` block at line 1530, which runs local consolidation. Missing credential also falls back (line 1524-1527). **Compliant with spec.**

### 15. [ADVISORY] Spec compliance — Test coverage added

The spec requires "Add unit tests for `managed_agent.py` covering: dispatch success/failure, poll success/timeout, validation pass/reject, and fallback-triggering behavior." EVIDENCED: `tests/test_managed_agent.py` exists with classes `TestValidateResult`, `TestDispatchTask`, `TestPollTask`, `TestRunConsolidation`, `TestRetryTransient`, `TestMaSafeExceptions`, `TestCleanup`, and `TestFindOrCreateAgent`. All required categories are covered. **Compliant with spec.**

### 16. [ADVISORY] No scope creep detected

The diff stays within the Phase 1 boundary: consolidation only, no refine-round offload, no LiteLLM modification, no general remote workspace execution. The additions (lifecycle tracking, usage capture, environment cleanup, agent caching) are all within the spec's observability and reliability requirements.

### 17. [ADVISORY] `_cleanup_environment` is a good addition not explicitly in spec

The spec doesn't mention environment cleanup, but it's a natural operational hygiene measure. Best-effort cleanup (swallowing errors) is the right pattern for a resource that's ephemeral anyway. No scope creep concern.

---

## Summary

| Category | Material | Advisory |
|----------|----------|----------|
| Architecture | 2 | 3 |
| Security | 1 | 3 |
| PM/Acceptance | 0 | 7 |

**Material findings:**

1. **Architecture #2:** Module-level `_cached_agent` global lacks thread-safety documentation/protection. Low risk today (single-threaded consolidation) but should be documented as single-thread-only or protected with a lock, given the codebase already uses `ThreadPoolExecutor` elsewhere.

2. **Architecture #5:** `dispatch_task` and `poll_task` signatures diverge from spec's "New Module" section. The spec should be updated to reflect the actual (and pragmatically better) signatures.

3. **Security #6:** Credential leak prevention is well-implemented (exception class-only logging, traceback removal). Marking as material-positive — this is a required security property that is correctly delivered.

**Overall assessment:** This is a well-structured Phase 1 implementation that closely follows the spec. The security posture is strong (no credential leakage paths, explicit-payload-only egress, proper fallback). The observability additions (lifecycle tracking, usage capture, cost accumulation) satisfy the spec's requirements. The main architectural concern is the module-level mutable state, which is acceptable for Phase 1 but should be hardened before any concurrency expansion.

---

## Challenger B — Challenges
**EXCEPTION / MUST NOT / EXPLICITLY EXCLUDED clauses extracted from spec**

- **MUST NOT / EXPLICITLY EXCLUDED**
  - Phase 1 must **not** target refine rounds first; refine remains local until sequential handoff design exists.
  - MA path must **not** receive ambient process state, live workspace, implicit local file access, or arbitrary file trees.
  - Phase 1 must **not** depend on provider-side file access, shell execution, or tool use.
  - Managed response must **never** be auto-executed as code, shell commands, or tool instructions.
  - Content containing secrets/credentials/tokens or clearly sensitive internal material must **not** be sent without explicit review/allow decision.
  - MA credentials must **not** be logged or broadly inherited by subprocesses.
  - Non-goals / explicitly excluded:
    - replacing LiteLLM for local path
    - general remote workspace execution
    - automatic file sync to provider
    - persistent always-on Jarvis sessions
    - refine-round offload before state-transfer design
    - modifying existing `_call_litellm` or LiteLLM proxy config

- **EXCEPTIONS / decision rules**
  - If managed dispatch is requested but credential is absent, fall back to local unless caller explicitly requests hard failure.
  - Hard-fail only if both remote execution and local fallback fail, or caller explicitly requests hard failure.
  - If MA API cannot reliably produce structured output, Phase 1 may accept a bounded text field and synthesize stats locally / return `None`.

**Spec contradiction check**

I do **not** see code in this diff that directly contradicts the spec’s explicit exclusions above. The implementation stays on consolidation, keeps the payload text-based, avoids traceback/error-message secret leakage, and falls back to local on missing credential / handled MA failures.

---

## PM/Acceptance

### [ADVISORY] Acceptance coverage is still partial: no integration-level test verifies the `debate.py` MA fallback path end-to-end
The spec requires “an integration-level test that exercises the MA-consolidation path with a mock MA backend, verifying that the result integrates correctly into the downstream judge flow.” Tooling confirms `scripts/managed_agent.py` now has unit coverage in `tests/test_managed_agent.py`, but the diff only adds unit tests for `managed_agent.py`; it does not add a test covering `cmd_judge`’s new `--use-ma-consolidation` path, fallback logging, or event-log fields. This leaves the highest-risk acceptance path — MA failure → local consolidation → structured log correctness — unverified.

### [ADVISORY] New lifecycle metrics are only partially surfaced to operators
The spec calls for logging dispatch/completion time, timeout, retry count, terminal status, and fallback-to-local events. The MA module now produces lifecycle metadata, and `debate.py` logs `consolidation`, `consolidation_source`, and `ma_fallback`. However, `debate.py` only tags local fallback stats with `source="local"` / `ma_fallback=True`; when MA succeeds, it relies on `run_consolidation` stats shape. That’s acceptable if `validate_result` always emits the expected fields, but the operator-visibility contract is still somewhat implicit rather than normalized at the call site. This is maintainable for now, but brittle if the MA stats contract evolves.

---

## Security

### [MATERIAL] Environment resources can be orphaned on dispatch-time failures because cleanup only happens after successful `dispatch_task` completion
Verified in `scripts/managed_agent.py`: `dispatch_task()` creates an environment before creating the session and sending the prompt, but `_cleanup_environment()` is only called in `run_consolidation()` *after* `dispatch_task()` has returned successfully. If `client.beta.sessions.create(...)` eventually fails after the environment has been created, or if `events.send(...)` raises, `run_consolidation()` never receives `env_id` and cannot delete it.  
This is a concrete security/architecture issue because it leaves remote provider-side state behind containing task metadata and potentially increases unintended data retention surface. The spec’s security/data-egress section is explicit that this new trust boundary must be tightly controlled; best-effort cleanup should cover partial dispatch failures too, not just post-poll paths.

### [ADVISORY] Sensitive-content gating required by spec is still only documented, not enforced in code
The spec requires a default-deny gate for secrets/PII/confidential content before remote dispatch. In `scripts/debate.py`, the MA path sends `challenge_body` directly to `run_consolidation(...)` once `--use-ma-consolidation` and `MA_API_KEY` are present; there is no code-level content classification or explicit allowlist gate in the diff.  
This is not necessarily a blocker for a narrow internal rollout if policy enforcement is intentionally deferred, but it means the implementation does not yet realize an important security acceptance criterion from the spec.

---

## Architecture

### [MATERIAL] `dispatch_task()` changed its failure boundaries but does not guarantee cleanup across all stages, creating a leaky lifecycle contract
Structurally, `dispatch_task()` now manages multiple remote resources: agent lookup/create, environment create, session create, and prompt send. But its API still returns only on full success and exposes cleanup responsibility to the caller only after that point. This is an incomplete component boundary: resource acquisition and release are split across functions, yet partial acquisition failure inside `dispatch_task()` cannot be unwound by the caller.  
A more sound boundary would either:
- encapsulate full lifecycle ownership inside `dispatch_task()` / `run_consolidation()`, with internal cleanup on *every* failure after environment creation, or
- return a cleanup-capable object/handle as soon as the environment exists.

As written, the module now has a lifecycle leak path during dispatch, which will be hard to observe and harder to correct operationally.

### [ADVISORY] Module-level `_cached_agent` is process-global mutable state without concurrency or multi-tenant safeguards
Verified in `scripts/managed_agent.py`: `_cached_agent` is a single module-global tuple `(agent_id, agent_version, prompt_hash)`. This is simpler than using `os.environ`, but it creates architectural assumptions that are not evidenced here:
- only one relevant agent cache entry is needed per process,
- concurrent calls won’t race on reads/writes,
- all calls in-process share the same provider account / tenant semantics.

If this script ever runs multi-threaded or services multiple debate executions within one process, this global cache can become a hidden coupling point. Not a must-fix for current CLI usage, but worth documenting or scoping more tightly.

### [ADVISORY] Usage/cost parity is estimated rather than provider-evidenced
In `scripts/debate.py`, MA usage is translated into LiteLLM-style token fields and passed to `_estimate_cost(...)` / `_track_cost(...)`. The quantitative implication — MA costs are now represented in session totals — is **ESTIMATED**, because the diff shows token capture but no provider-returned billed cost field or model-pricing verification. The spec explicitly allowed logging usage units when exact cost is unavailable. Architecturally this is okay, but the implementation should mark these session totals as estimated for MA rather than making them look identical to local-path cost accounting.

**Quantitative claim basis:** estimated cost parity is **ESTIMATED** from token counts in `poll_task()` and `_estimate_cost(...)` usage in `debate.py`; not provider-billed cost data.

---

## Risk balance

- **Risk of proposed change:** orphaned remote environments, incomplete security gating, and process-global cache coupling.
- **Risk of not changing:** continued lack of MA cost/session visibility and continued secret leakage risk via traceback/error-message logging during MA failures. This diff does improve those areas meaningfully.

Overall: good direction, but the resource-lifecycle leak on dispatch failures is a must-fix before relying on this path operationally.

---

## Challenger C — Challenges
### Review: Managed Agents Integration (Phase 1)

**PM/Acceptance**
*   **[MATERIAL] Scope and Completeness:** The diff strictly aligns with the MVP checklist from the refined spec. It properly targets `_consolidate_challenges`, respects the `challenge_body` boundary, and explicitly builds parity with local logging metrics via `_track_cost` and the existing structured event log.
*   **[ADVISORY] Fallback Tracking:** The implementation explicitly sets `ma_fallback = True` and saves it to the payload. This correctly surfaces operator visibility, complying perfectly with the "Operator Visibility" acceptance criterion.

**Architecture**
*   **[MATERIAL] State Management & Agent Caching:** The caching of `_cached_agent = (agent_id, agent_version, current_hash)` is a robust architectural choice that prevents duplicate agent creation on every request, but avoids ambient environment state that could pollute subprocesses.
*   **[ADVISORY] Integration Seams:** The `_cleanup_environment` method in `managed_agent.py` being a best-effort block prevents stranded cloud resources from breaking the local fallback pathway.

**Security**
*   **[MATERIAL] Compliance with "MUST NOT" Spec Clauses:**
    *   *Spec:* "Never print the key or embed it in error messages, structured logs, or exception traces. Redact or omit in all output paths."
    *   *Implementation:* The diff successfully avoids standard exception representation via `print(f"WARNING: MA consolidation failed ({type(e).__name__})")`, which prevents token leakage from standard SDK HTTP exception stringification.
    *   *Spec:* "Do not export MA credentials broadly to child processes. Pass them only into the code path that performs the MA API request."
    *   *Implementation:* The api key is read once via `os.environ.get("MA_API_KEY")` and passed directly as an argument down the call chain (`run_consolidation(..., api_key=ma_api_key)`), avoiding `os.environ` mutation.
    *   *Spec:* "Provider Assumptions Must Be Documented..."
    *   *Implementation:* Fully documented in the module docstring of `managed_agent.py` acting as the rollout gate. 

**Risk Assessment**
*   **Risk of proposed change:** The primary risk was failing to isolate external API failures from crashing local jobs. The diff mitigates this via careful exception handling (`try... except... ma_fallback = True`) and strict timeout/polling boundaries.
*   **Risk of NOT changing:** Continuing to execute solely on local/LiteLLM architectures ensures single-node bottlenecking (EVIDENCED by spec: 15-30 minute session times). Implementing this dispatch correctly validates the remote execution framework.

---

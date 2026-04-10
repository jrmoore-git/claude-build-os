---
debate_id: managed-agents-dispatch
created: 2026-04-10T12:49:55-0700
phase: refine
rounds: 6
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: yes
---
# managed-agents-dispatch — Refined Document

## Round 1 (gemini-3.1-pro)
The original proposal outlined a clear path for offloading long-running local workloads to Managed Agents but missed critical integration, security, and operational details. It also targeted the wrong initial integration point: refine rounds are sequential and model-heterogeneous, making them a poor fit for a simple remote offload compared to consolidation. 

**Improvements made in this revision:**
- **Integration Target Shift:** Changed the Phase 1 target from refine rounds to the `_consolidate_challenges` phase, which is a cleaner, Claude-only task boundary (Addressing Challenge 1).
- **Observability Parity:** Added a plan to handle cost tracking, retries, and model routing when bypassing LiteLLM for Managed Agent dispatch (Addressing Challenge 3).
- **Security & Data Egress:** Introduced strict guidelines on what data can be sent to external providers, prohibiting ambient context sharing and defining trust boundaries (Addressing Challenge 4).
- **Reliability & Fallbacks:** Defined error-handling protocols, including timeouts, schema validation, and fallback to local execution to prevent remote failure from crashing the pipeline (Addressing Challenge 5).
- **Credential Management:** Specified how external API credentials will be injected, scoped, and protected against logging or subprocess leakage (Addressing Challenge 6).

## Round 2 (gpt-5.4)
The current revision is materially better than a generic MA-integration proposal. It already incorporates most accepted challenges correctly:

- It fixes the Phase 1 target by moving the first integration point from refine rounds to `_consolidate_challenges`.
- It adds explicit sections for observability, security, credential handling, and fallback/validation.
- It narrows refine-round offload to a future sequential handoff design instead of treating it as an easy first step.

Remaining issues and improvements:
1. **One operational-context claim was still inaccurate.** The document said “Refine legs are Claude-only (3 of 6 rounds).” Verified config shows `refine_rotation = ["gemini-3.1-pro", "gpt-5.4", "claude-opus-4-6"]`, so only every third round is Claude in the current 3-model rotation, not “3 of 6” as a stable architectural fact. This needed correction.
2. **LiteLLM parity was directionally right but too hand-wavy.** The revision said “same sinks used by LiteLLM,” but verified code shows debate logging already has structured event logging and `llm_client.py` provides retries/error categories. The design should state that MA jobs need their own structured log payloads because they do not automatically flow through `llm_client.py`.
3. **Failure handling needed clearer decision rules.** The current version mentioned fallback and timeouts, but not when to retry remotely versus immediately fall back locally, nor what constitutes a hard failure.
4. **Security gating could be more concrete.** The accepted challenge required minimum policy, and the current draft met that broadly. I tightened it into an explicit “default deny for sensitive content” rule and clarified that only constructed strings may be sent.
5. **Credential handling needed inheritance guidance tied to current runtime shape.** Since the existing script spawns subprocesses in places, the revision should explicitly require that MA credentials are injected only into the MA client path and not broadly inherited.

## Round 3 (claude-opus-4-6)
The previous revision is substantially improved over what a first draft would look like. It correctly addresses all six accepted challenges and is well-structured. However, I found several issues worth fixing:

1. **"debate_log" claim is slightly imprecise.** The previous revision says "debate.py already emits structured debate log events" and references this as EVIDENCED. Tool verification shows the function is `_log_debate_event` and the output target is `debate-log.jsonl`. The claim is substantively correct but should use the precise identifiers.

2. **New Facts section has a minor inaccuracy.** It says "No current repository references to `MA_API_KEY` were found in `scripts/`" — this is verified and correct. But it also says "No test files were found for `scripts/llm_client.py` or `scripts/debate.py` via the available coverage check" — also verified and correct. Good.

3. **The `_consolidate_challenges` function signature is now visible** (line 1352): it takes `(challenge_body, litellm_url, api_key, model=None)`. This is useful context for the integration design — the function already accepts a model parameter, which means the MA path could potentially be wired in as an alternative execution backend at this boundary. The document should note this.

4. **The consolidation flow in `cmd_judge`** (lines 1449-1452) shows that consolidation output is used directly as `judge_input_body` when consolidation succeeds, or falls through to the original `challenge_body` otherwise. This confirms the fallback pattern described in the proposal is architecturally natural — the existing code already has a "skip consolidation" path.

5. **Minor structural improvements:** The "Why Consolidation Is the First Integration Point" section could be tightened. The security section could benefit from slightly clearer hierarchy. The rollout criteria should mention test coverage given the verified absence of tests.

6. **One factual claim to verify:** The document says `_call_litellm` exists — confirmed at line 804. It also references `LLM_SAFE_EXCEPTIONS` at line 1203, which shows the existing error-handling pattern that the MA path should mirror.

7. **The "New Facts Introduced" section** mixes facts from the original analysis with facts from the revision. I'll clean this up to only list genuinely new facts discovered during this review pass.

## Round 4 (gemini-3.1-pro)
The previous revision did an excellent job thoroughly addressing the accepted challenges. It successfully pivoted the integration target to `_consolidate_challenges`, explicitly handled the LiteLLM bypass (observability and retries), introduced strict security and egress boundaries, established a firm local-fallback policy, and defined credential management.

Improvements made in this pass:
- **Structural Polish**: Merged slightly overlapping concepts (e.g., "Simplest Version" renamed to "Minimum Viable Phase 1 (MVP)" and aligned with the implementation shape).
- **Readability**: Lightly edited the guardrails sections for improved flow and bullet consistency without removing any of the rigorous constraints added by the previous reviewer.
- **Preservation**: All verified data, operational contexts, baseline measurements, and previously introduced evidence tags remain fully intact.

## Round 5 (gpt-5.4)
The current revision is substantially improved and addresses the accepted challenges well. In particular, it correctly shifts Phase 1 away from refine rounds and toward `_consolidate_challenges`, adds explicit observability/security/credential/fallback sections, and preserves the operational evidence sections that should not be collapsed.

Remaining issues I improved in the revision below:

1. **A few “verified” claims were phrased more strongly than the cited evidence supports.**
   - The document said `_consolidate_challenges` accepting `model=None` is “relevant for wiring in an alternative execution backend.” The verified fact is only that the parameter exists; that does not by itself prove backend-pluggability. I narrowed that interpretation.
   - The document implied the existing fallthrough path directly supports “MA failed, use local.” The verified code only shows `--no-consolidate` skip behavior; local fallback is architecturally natural, but still needs implementation. I made that distinction clearer.

2. **One section mixed recommendation and proof too tightly.**
   - “Why Consolidation Is the First Integration Point” was good, but some bullets blended design judgment with verified code behavior. I kept the recommendation while separating evidence from rationale more clearly.

3. **The rollout criteria and MVP checklist overlapped.**
   - I kept both, per preservation requirements, but tightened wording so the checklist is implementation-focused and the rollout criteria are acceptance-focused.

4. **Some implementation boundaries could be sharper.**
   - I made it more explicit that Phase 1 is a narrow RPC-style remote call, not general remote agent autonomy.
   - I clarified that only explicitly constructed prompt content is sent, and that provider-side tool use / workspace access are out of scope for Phase 1.

5. **A few places were slightly over-explained or repetitive.**
   - I streamlined repeated “fallback / skip / local path” language while preserving all recommendations and constraints.

## Round 6 (claude-opus-4-6)
The previous revision is thorough and well-structured. It successfully addresses all six accepted challenges with dedicated sections. My verification of the tool outputs confirms the evidence claims are accurate. Here are my observations:

**Improvements already made by the previous reviewer:**
- Correctly retargeted Phase 1 from refine rounds to consolidation (Challenge 1)
- Added comprehensive observability/integration strategy section (Challenge 3)
- Added security controls and data egress section (Challenge 4)
- Added error handling and reliability section (Challenge 5)
- Added credential management section (Challenge 6)
- All EVIDENCED tags check out against tool results

**Remaining issues I'm addressing:**

1. **`LLM_SAFE_EXCEPTIONS` is referenced as a line-1203 identifier but `check_function_exists` returned false.** Tool output shows `check_code_presence` found 1 match for `LLM_SAFE_EXCEPTIONS` in scripts, and the snippet at line 1203 shows `except LLM_SAFE_EXCEPTIONS`. This is a tuple/variable assignment, not a function — the evidence tag is fine but I'll clarify it's a variable, not a function, to avoid confusion.

2. **The "New Facts Introduced" section at the bottom is useful for audit but slightly redundant with inline EVIDENCED tags.** I'll keep it but tighten it to avoid restating things already tagged inline.

3. **The `_consolidate_challenges` return signature is important for the validation contract.** The tool output at line 1355-1356 shows it returns `(consolidated_body, stats_dict)` or `(original_body, None)`. The validation contract section could be more precise about matching this existing return shape.

4. **Minor structural issue:** The "Why Consolidation Is the First Integration Point" section is good but slightly duplicates rationale already in the Phase 1 description. I'll keep it as a standalone section since it directly addresses Challenge 1, but tighten cross-references.

5. **The document lacks a clear "Recommendations" header** — the proposed changes are embedded in the Phase 1/Phase 2 structure. This is fine for a design proposal (not a findings document), so the recommendation-preservation rule is effectively a no-op for numbered recommendations. The phased approach *is* the recommendation set.

6. **One factual refinement:** The snippet at line 1352 shows `_consolidate_challenges` takes `model=None` as an optional parameter, meaning it already supports model selection override. This is relevant to the MA integration design — the remote consolidation could use a different model than the local default.

## Final Refined Document

---
topic: managed-agents-dispatch
created: 2026-04-10
---
# Managed Agents Integration with BuildOS

## Problem
BuildOS currently runs agent work locally via Claude Code CLI sessions and local model calls routed through LiteLLM. Long-running tasks can block a local session, and remote execution today generally means SSHing into the Mac Mini and managing the run manually. BuildOS does not yet have a first-class primitive for dispatching selected work to a managed remote agent service and retrieving results later.

Jarvis's always-on aspiration (persistent email/calendar/promise monitoring) is currently handled via cron — fire-and-forget with no session continuity. That is a separate concern and belongs in the Jarvis repo, not as the first target for BuildOS managed-agent integration.

### Current System Failures
- Long debate/refine runs (6 rounds × 3 models) consume 15–30 minutes of local session time
- Remote execution requires SSH + tmux; no way to dispatch from laptop and check results later
- Cron-based monitoring has no state continuity between runs (each run starts fresh)
- No existing failures per se — this is greenfield capability expansion

### Operational Context
- debate.py runs ~2–5 times/day, costs ~$1–2/day across models
- Refinement is sequential and uses a mixed-model rotation, not a clean Claude-only boundary. EVIDENCED: `config/debate-models.json` sets `refine_rotation` to `["gemini-3.1-pro", "gpt-5.4", "claude-opus-4-6"]`
- Consolidation (pre-judgment dedup) is a cleaner initial integration point than refine. EVIDENCED: `_consolidate_challenges` exists as a distinct function in `scripts/debate.py` (line 1352), accepts `(challenge_body, litellm_url, api_key, model=None)`, and returns `(consolidated_body, stats_dict)` or `(original_body, None)`. `cmd_judge` already has an explicit "no consolidation" branch that sets `consolidated_body = challenge_body` (lines 1447–1452).
- BuildOS is a framework used across multiple projects (not just Jarvis)
- Existing error handling uses `LLM_SAFE_EXCEPTIONS` (a tuple variable) for graceful degradation on model call failures. EVIDENCED: `scripts/debate.py` line 1203 — `except LLM_SAFE_EXCEPTIONS`; `check_code_presence` confirmed 1 match in scripts
- Existing event logging uses `_log_debate_event` writing to `debate-log.jsonl`. EVIDENCED: `check_function_exists` confirmed in `scripts/debate.py`
- No automated test coverage exists for `scripts/debate.py` or `scripts/llm_client.py`. EVIDENCED: `check_test_coverage` returned no test files for either module

### Baseline Performance
No existing system for cloud-hosted agent dispatch. Current execution is 100% local via CLI sessions and cron.

## Proposed Approach
**Approach A+C: Hybrid orchestration layer with background-worker-style managed dispatch, starting with consolidation.**

### Phase 1 (C — Background Worker / Managed Dispatch)
- Add `scripts/managed_agent.py` as a dedicated client for Managed Agents API calls.
- Integrate with `debate.py` to optionally offload the `_consolidate_challenges` step.
- Keep the payload fully materialized and self-contained: the local process constructs prompt text and submits only that text plus explicit metadata.
- Treat Phase 1 as a narrow remote-execution primitive for one bounded task, not as general remote workspace execution.
- Validate API behavior, result quality, observability, cost capture, and failure modes on real consolidation workloads.
- Preserve the local `_consolidate_challenges` implementation as the default-safe fallback path.

### Phase 2 (A — Orchestration Layer)
- Add routing logic to BuildOS that decides local vs. managed execution per task type.
- Support remote execution from any machine: dispatch, persist job metadata, poll later, and retrieve results.
- Add explicit policies for which task classes are eligible for managed dispatch.
- Explore Agent Teams or similar parallel orchestration features only after the base dispatch path is operationally trustworthy.

### Future Consideration: Sequential Refine-Round Offload
Refinement is not the right first boundary because current refine execution is sequential and rotates across multiple model families. EVIDENCED: `refine_rotation` is `["gemini-3.1-pro", "gpt-5.4", "claude-opus-4-6"]` in `config/debate-models.json`.

If refine rounds are offloaded later, the design must explicitly handle:
- **State transfer between rounds:** Each round mutates the document; the next round's input depends on the previous round's output.
- **Round-specific model selection:** Currently governed by `refine_rotation` config, which cycles through non-Claude models. A managed-agent service may not support arbitrary model routing.
- **Checkpointing and resume semantics:** If one remote round fails mid-sequence, the system needs a defined resume point.
- **Deterministic fallback:** If one remote round fails, the system must decide whether to retry remotely, fall back to local for that round, or abort the sequence.

Until that design exists, refine should remain local.

### Not Building (Deferred to Jarvis Repo)
- Approach B: Persistent Jarvis agent with always-on session
- Cron-to-persistent migration

## Why Consolidation Is the First Integration Point

Consolidation is the cleanest initial managed-agent target because:

1. **Bounded scope.** `_consolidate_challenges` operates on a text body and returns a transformed text body plus optional stats. It does not drive a long sequential loop. EVIDENCED: function signature `(challenge_body, litellm_url, api_key, model=None)` returns `(consolidated_body, stats_dict)` or `(original_body, None)` at `scripts/debate.py` lines 1352–1356
2. **Cleaner boundary than refine.** Refine depends on round-by-round document mutation across a mixed-model rotation; consolidation is a single pre-judgment transformation step.
3. **Lower state-transfer complexity.** Consolidation does not require handing evolving document state from one round to the next.
4. **Easier to validate.** Managed output can be compared against the existing local consolidation behavior before expanding scope.
5. **Existing control-flow shape is compatible.** `cmd_judge` already supports a path where no consolidation output is produced and `challenge_body` continues downstream unchanged. EVIDENCED: `scripts/debate.py` lines 1447–1452. This does not itself implement MA fallback, but it makes a fallback-to-local design structurally natural.
6. **Narrower trust boundary.** Phase 1 can send one explicitly constructed prompt payload rather than attempting to expose workspace state, tools, or iterative conversation context.

## System Design & Operational Guardrails

### Execution Boundary
Phase 1 dispatch is limited to explicitly selected, self-contained tasks:

- **Input:** Constructed prompt text and minimal metadata.
- **Execution:** Remote managed-agent run for that bounded prompt only.
- **Output:** Structured response payload.
- **Re-entry:** Local code validates and consumes the result as data.

The MA path does **not** receive ambient process state, a live workspace, or implicit access to local files. Phase 1 is intentionally closer to an RPC-style remote call than to autonomous remote workspace execution.

### Observability & Integration Strategy
Managed Agent dispatch will bypass the existing LiteLLM client path, so observability parity is not automatic.

**Verified current state:**
- `scripts/llm_client.py` routes local model calls through LiteLLM at `localhost:4000` and retries transient failures with exponential backoff across 3 attempts. EVIDENCED: `scripts/llm_client.py` lines 5 and 17
- `scripts/debate.py` emits structured events via `_log_debate_event` to `debate-log.jsonl`. EVIDENCED: `check_function_exists` confirmed in `scripts/debate.py`
- Local model calls track token usage and estimated cost per call via `_call_litellm`, which also records per-model cost breakdowns in a thread-safe session cost accumulator. EVIDENCED: `scripts/debate.py` lines 750–757 (cost accumulation) and lines 804–809 (function docstring)

**Required Phase 1 behavior:**
- **Cost & Accounting:** Record provider-reported usage and any billable metrics returned by the MA API. Log them through the same `_log_debate_event` pipeline or an equivalent structured event path. If exact cost is unavailable from the provider response, log usage units and mark cost as unavailable rather than fabricating parity. Feed MA costs into the session cost accumulator so end-of-run summaries remain accurate.
- **Model Identity:** Persist provider name, model name, and model version/revision if exposed by the API.
- **Job Lifecycle:** Log dispatch time, completion time, timeout, retry count, terminal status, and fallback-to-local events.
- **Correlation:** Attach debate ID / task ID so a managed consolidation can be traced alongside the parent `judge` run.
- **LiteLLM Parity Gap:** LiteLLM-specific guarantees — proxy-side aliasing, shared retry behavior, centralized cost aggregation — are not preserved automatically on the MA path. Phase 1 must document which LiteLLM behaviors are consciously waived vs. planned for later parity. At minimum:
  - **Waived (Phase 1):** Proxy-side model aliasing, centralized LiteLLM cost dashboard aggregation.
  - **Reimplemented (Phase 1):** Retry with backoff (in MA client), per-call cost/token logging (via `_log_debate_event`), session cost accumulation.
  - **Deferred (Phase 2):** Unified cost dashboard across local and MA paths.

### Error Handling & Reliability
The local pipeline must remain safe if remote execution fails.

**Phase 1 rules:**
- **Dispatch Retry Policy:** Retry transient network / 429 / 5xx-style dispatch failures with bounded exponential backoff, similar in spirit to the current LiteLLM path (3 attempts with backoff). EVIDENCED: existing retry pattern in `scripts/llm_client.py` line 17
- **Polling Timeout:** Use a strict wall-clock timeout for remote completion. The exact value should be configurable; the initial implementation may start conservative (for example, 5 minutes for consolidation) and then be tuned from observed runs.
- **Fallback Rule:** If dispatch fails before job creation, polling times out, or the returned payload fails validation, execute the existing local `_consolidate_challenges` path instead of failing the whole debate. Log the fallback event with the reason.
- **Hard-Fail Rule:** Only hard-fail if both remote execution and local fallback fail, or if the caller explicitly requested hard failure (e.g., for testing the MA path in isolation).
- **Output Validation:** Validate schema, required fields, and size limits before integrating MA output into the workflow. See "Validation Contract" below for specifics.
- **Result Trust Boundary:** MA output is treated as untrusted data only. It may be parsed and fed into existing logic, but never auto-executed as code, shell commands, or tool instructions.
- **Error Classification:** Mirror the existing `LLM_SAFE_EXCEPTIONS` pattern (line 1203) so that MA-specific transient errors are handled gracefully rather than crashing the debate run. Define an `MA_SAFE_EXCEPTIONS` tuple for the MA client path.
- **Operator Visibility:** Surface whether the final output came from MA success or local fallback, both in stderr output and in the structured event log.

### Security Controls & Data Egress
Managed dispatch creates a new external trust boundary and must be gated accordingly.

**Minimum Phase 1 policy:**
- **Explicit Payload Only:** Only explicitly constructed strings and metadata intended for the remote task may be sent. For Phase 1, that means the consolidation prompt text and minimal job metadata (task type, debate ID, timestamp).
- **No Ambient Context:** Environment variables, process state, working-directory contents, local git state, and arbitrary file trees must not be implicitly synced or exposed. The dispatch function must accept only its explicit parameters and construct the outbound payload from those alone.
- **No Remote Workspace Assumption:** Phase 1 must not depend on provider-side file access, shell execution, or tool use. If a future task requires those capabilities, it needs a separate security review.
- **Sensitive-Content Default Deny:** Content containing secrets, credentials, tokens, or clearly sensitive internal material must not be sent to the MA provider without an explicit review/allow decision. Phase 1 consolidation inputs are challenge transcripts about proposals, which are lower-sensitivity by default, but the gate must exist for future task types.
- **PII / Confidential Review Gate:** If prompt content may include PII or confidential business data, dispatch must be blocked or require an explicit reviewed allowlist policy. Phase 1 should document the expected content profile of consolidation inputs (challenge transcripts generated by the debate system itself, containing model-generated analysis of proposals).
- **Provider Assumptions Must Be Documented:** Before production rollout, document: authentication method, tenant isolation model, data retention policy, and whether the provider trains on customer data. This documentation is a **rollout gate**, not a nice-to-have.
- **Narrow Scope First:** Phase 1 targets only consolidation inputs. Expanding to other task types requires revisiting this policy.

### Credential Management
The MA client introduces a new external credential and needs a defined handling model.

**Verified current state:** No references to `MA_API_KEY` exist in `scripts/` today. EVIDENCED: `check_code_presence` returned 0 matches. The existing credential pattern in `cmd_judge` reads `LITELLM_MASTER_KEY` from the environment and hard-fails if absent. EVIDENCED: `scripts/debate.py` lines 1404–1407

**Requirements:**
- **Source of Truth:** Load credentials from a dedicated environment variable (e.g., `MA_API_KEY`), following the same basic pattern as `LITELLM_MASTER_KEY`.
- **Least Scope:** Use credentials scoped specifically for managed-agent dispatch, not a broad personal token if a narrower service credential is available.
- **No Secret Logging:** Never print the key or embed it in error messages, structured logs, or exception traces. Redact or omit in all output paths.
- **Subprocess Inheritance Constraints:** Do not export MA credentials broadly to child processes. Pass them only into the code path that performs the MA API request.
- **Rotation Expectation:** Credential rotation should follow the same operational standard used for other external service secrets (currently manual env-var update).
- **Missing Credential Behavior:** If managed dispatch is requested but the credential is absent, log a clear non-secret error and fall back to local execution unless the caller explicitly requested hard failure. This differs from the `LITELLM_MASTER_KEY` pattern (which hard-fails) because MA dispatch is an optional enhancement, not a required capability.

## Phase 1 Implementation Shape

### New Module
Add `scripts/managed_agent.py` with a narrow API:
- `dispatch_task(payload, metadata, api_key) -> job_id`
- `poll_task(job_id, timeout_s, api_key) -> raw_result`
- `validate_result(raw_result, schema) -> structured_result`

EVIDENCED: Neither `dispatch_task` nor `managed_agent` currently exist in `scripts/`. This is entirely new code.

This module should remain intentionally small and avoid absorbing workflow logic from `debate.py`. It is a transport/validation layer, not a decision-making layer.

### First Integration Point in debate.py
Add an opt-in path, for example:
- `debate.py judge --use-ma-consolidation`

Behavior:
1. Local code reads and prepares proposal/challenge content using the existing flow.
2. Local code builds the exact consolidation payload from the same `challenge_body` currently passed to `_consolidate_challenges`. EVIDENCED: `cmd_judge` calls `_consolidate_challenges(challenge_body, litellm_url, api_key)` at line 1448
3. MA client dispatches the consolidation job with that materialized prompt.
4. Local code polls for completion within the configured timeout.
5. Result is validated against the expected schema and size limits.
6. On success, downstream judge logic continues with the returned consolidation output in place of the locally generated consolidation result.
7. On failure (dispatch error, timeout, or validation failure), local `_consolidate_challenges` runs instead, and the fallback is logged.

### Validation Contract
The consolidation response must match the existing return contract of `_consolidate_challenges`: a text body (the consolidated challenge content) and optional stats. EVIDENCED: function returns `(consolidated_body, stats_dict)` or `(original_body, None)` per lines 1355–1356.

The MA response should be accepted only if it passes:
- **Schema match:** Top-level structure compatible with the `(text_body, stats_dict_or_none)` return shape.
- **Required fields:** Text body is present and non-empty.
- **Size threshold:** Text body does not exceed a configurable maximum length (to prevent unbounded output from consuming downstream context). A reasonable initial limit might be 2× the input `challenge_body` length.
- **No executable artifacts:** Response is treated as text data only; no code execution, file writes, or tool invocations from the response content.

If the MA API cannot reliably produce structured output matching this contract, Phase 1 should accept only a single bounded text field and synthesize the stats locally (or return `None` for stats).

### Testing Expectations
Given that no automated tests exist for `debate.py` or `llm_client.py` today, Phase 1 should:
- Add unit tests for `managed_agent.py` covering: dispatch success/failure, poll success/timeout, validation pass/reject, and fallback-triggering behavior.
- Add an integration-level test that exercises the MA-consolidation path with a mock MA backend, verifying that the result integrates correctly into the downstream judge flow.
- Not assume that existing code paths have regression coverage — manual validation of the fallback path is required until test coverage improves.

## Minimum Viable Phase 1 (MVP) Checklist
A `managed_agent.py` script that effectively bridges to the cloud service by doing the following:

1. **Dispatch:** Create a Managed Agent job with an explicit, self-contained prompt payload. Only the constructed prompt and minimal metadata are sent.
2. **Retrieve:** Poll for results with a strict configurable timeout.
3. **Validate:** Validate and return bounded, structured output matching the `_consolidate_challenges` return contract.
4. **Observe:** Record provider/model/usage/job-status metadata via the existing `_log_debate_event` pipeline or an equivalent structured event path. Document which LiteLLM observability behaviors are waived vs. reimplemented.
5. **Fall Back:** Transparently fall back to local `_consolidate_challenges` when MA dispatch, polling, or validation fails. Log the fallback reason.
6. **Secure:** Send only explicitly constructed payloads. Load credentials from a dedicated env var. Never log secrets. Document provider security assumptions before production rollout.

## Non-Goals
- Replacing LiteLLM for the existing local model path
- General remote workspace execution
- Automatic file synchronization to the MA provider
- Persistent always-on Jarvis sessions
- Refine-round offload before sequential state-transfer semantics are designed
- Modifying the existing `_call_litellm` or LiteLLM proxy configuration

## Rollout Criteria
Phase 1 should be considered successful only if it demonstrates:
- Correct functional parity for consolidation on real debate workloads, compared against the local `_consolidate_challenges` path.
- Explicit event logging for MA dispatch and completion, integrated with the existing `debate-log.jsonl` pipeline or an equivalent structured event path.
- Safe fallback to local execution on any MA failure mode, with the fallback reason logged.
- No secret leakage or ambient-context egress, verified by code review of the dispatch payload construction.
- Operator visibility into whether the result came from remote execution or fallback.
- Provider security assumptions documented: auth, retention, tenancy, and training policy.
- LiteLLM parity gap documented: which behaviors are waived, reimplemented, or deferred.
- Basic automated test coverage for the new `managed_agent.py` module.
- Credential handling follows the requirements in the Credential Management section.

## New Facts Introduced
*These facts were verified via tool calls and influence the design constraints:*

- `_consolidate_challenges` has the signature `(challenge_body, litellm_url, api_key, model=None)` and returns `(consolidated_body, stats_dict)` or `(original_body, None)`. EVIDENCED: `read_file_snippet` lines 1352–1356
- `cmd_judge` reads `LITELLM_MASTER_KEY` from the environment and errors if absent. EVIDENCED: `scripts/debate.py` lines 1404–1407
- `cmd_judge` calls `_consolidate_challenges(challenge_body, litellm_url, api_key)` at line 1448 and has an explicit branch where consolidation is skipped: `consolidated_body = challenge_body`. EVIDENCED: `scripts/debate.py` lines 1447–1452
- The existing error-handling pattern catches `LLM_SAFE_EXCEPTIONS` (a tuple variable, not a function) around model calls. EVIDENCED: `scripts/debate.py` line 1203; `check_code_presence` confirmed 1 match
- `_call_litellm` tracks token usage and estimated cost per call, feeding into a thread-safe session cost accumulator. EVIDENCED: `scripts/debate.py` lines 750–757 (accumulator) and lines 804–809 (function docstring)
- `scripts/llm_client.py` routes local model calls through LiteLLM at `localhost:4000` and retries transient failures with exponential backoff across 3 attempts. EVIDENCED: `scripts/llm_client.py` lines 5 and 17
- `_log_debate_event` exists in `scripts/debate.py`. EVIDENCED: `check_function_exists` confirmed
- `config/debate-models.json` sets `refine_rotation` to `["gemini-3.1-pro", "gpt-5.4", "claude-opus-4-6"]`, confirming refine is mixed-model. EVIDENCED: `read_config_value`
- No `MA_API_KEY` references exist in `scripts/`. EVIDENCED: `check_code_presence` returned 0 matches
- No `managed_agent` references exist in `scripts/`. EVIDENCED: `check_code_presence` returned 0 matches
- No test files exist for `scripts/llm_client.py` or `scripts/debate.py`. EVIDENCED: `check_test_coverage` returned empty for both

---
mode: pre-mortem
created: 2026-04-16T20:52:37-0700
model: gpt-5.4
prompt_version: 1
---
# Pre-Mortem

1. **`session_outcome` never became reliable because `/wrap` was skipped in most real sessions, so the key correlation query was unusable.**  
   - **Type:** Execution failure  
   - **Warning sign today:** The plan explicitly says "`/wrap` is authoritative" and also acknowledges "Sessions without `/wrap` have no `session_outcome` event" and will be labeled abandoned. You can check current usage now: what % of sessions actually end with `/wrap`? If that’s not already >80%, the main analysis is doomed.  
   - **What would have prevented it:** Add an automatic end-of-session emitter tied to a real lifecycle event (`SessionEnd` or periodic heartbeat + timeout), with `/wrap` only enriching fields later.  
   - **Would prevention have changed the plan?** Yes. The plan should have been changed before starting; relying on manual `/wrap` for the primary outcome signal was too weak.

2. **Telemetry fragmented sessions because PID fallback created collisions/mismatches across hooks, reads, and wrap events, making per-session analysis wrong.**  
   - **Type:** Execution failure  
   - **Warning sign today:** The plan says session ID is `$CLAUDE_SESSION_ID` else parent PID and calls collisions “acceptable noise.” That is incompatible with the intended query “do sessions that skipped key context files produce more findings?” You can inspect today whether all touched surfaces already receive the same env vars; if not, correlation will be garbage.  
   - **What would have prevented it:** Before implementation, require one canonical session ID source available to all hook/runtime surfaces; if absent, add a generated session token persisted in a temp/session file and reused everywhere.  
   - **Would prevention have changed the plan?** Yes, but not killed it. It should have added a session-identity hardening step before any instrumentation.

3. **Hook instrumentation was too incomplete to answer “which hooks actually block real work,” so the team collected biased data and cut the wrong hooks.**  
   - **Type:** Strategy failure  
   - **Warning sign today:** The scope says there are 21 hooks, but only 6 are instrumented because they “actually gate behavior.” That is an assumption, not evidence. You can verify now whether other hooks alter flow indirectly, warn in ways that change behavior, or suppress later failures.  
   - **What would have prevented it:** Start with a 2-week census phase instrumenting all hook invocations minimally, even passive ones, then narrow to decision-rich hooks after observing actual frequency and impact.  
   - **Would prevention have changed the plan?** Yes. The current plan’s premise—“these 6 are the only ones worth measuring”—may be wrong enough that this exact project should not start as scoped.

4. **The telemetry hook degraded tool latency enough that developers bypassed or disabled it, leaving sparse and non-representative data.**  
   - **Type:** Execution failure  
   - **Warning sign today:** The plan admits every tool call adds a fork + append, and shell hooks may add ~30ms per decision via `python3.11`. There is no benchmark gate in verification, only syntax and smoke tests. You can measure this now on a looped Read/Edit workflow.  
   - **What would have prevented it:** Add a hard performance budget test before rollout: e.g., 500 synthetic hook invocations must keep p95 added latency under 5–10ms; if not, use a buffered/background writer or direct shell-native append path from day one.  
   - **Would prevention have changed the plan?** Probably changed implementation, not the project. But if latency couldn’t meet budget, rollout should have been stopped.

5. **The core query produced misleading conclusions because “context_read” did not mean “context used,” and topic truncation/file-watchlist choices omitted the real drivers of session quality.**  
   - **Type:** Strategy failure  
   - **Warning sign today:** The plan equates PostToolUse:Read on a watchlist with Tier 1 value, while excluding all other reads. That is a strong proxy assumption. You can examine current sessions now: do important decisions rely on files outside the watchlist, prior chat state, or injected context rather than explicit reads?  
   - **What would have prevented it:** Run a small manual validation study first: sample 20 sessions, compare telemetry-inferred context usage vs human judgment of what context actually mattered. Adjust schema/watchlist before broad rollout.  
   - **Would prevention have changed the plan?** Yes. If the proxy fails validation, this project as designed should not proceed.

## The Structural Pattern

These failures share one assumption: that lightweight additive telemetry will produce decision-grade truth without first validating coverage, identity, and outcome completeness. Multiple scenarios depend on unproven proxies: `/wrap` as outcome authority, PID as session identity, 6 hooks as the meaningful set, watchlist reads as Tier 1 usage. That makes this primarily a **sequencing problem**: the team is jumping to instrumentation and analysis before validating observability primitives. The plan should not be killed outright, but it should be re-sequenced: first prove reliable session identity, automatic outcome capture, latency budget, and proxy validity; only then deploy the broader telemetry.

## The One Test

Run a **5-day shadow telemetry pilot on 10 real sessions**, next week, with one temporary requirement: every session gets a manually reviewed ground-truth sheet. For each session, capture: actual session boundary, whether `/wrap` happened, all files truly consulted, all hooks that materially affected behavior, and final outcome/findings. In parallel, run the proposed telemetry implementation. At the end, score four things quantitatively:  
1. **Session linkage accuracy:** % of events correctly grouped to the right session  
2. **Outcome completeness:** % of sessions with a usable `session_outcome`  
3. **Proxy precision/recall:** telemetry-detected context/hook events vs human ground truth  
4. **Latency overhead:** p95 added time per tool/hook event  

If any of these fail predefined thresholds (e.g. <95% linkage, <80% outcome completeness, <85% precision/recall, >10ms p95 overhead), do not commit to the full plan yet.
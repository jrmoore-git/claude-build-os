---
decision: D18
original: "Keep Gemini 3.1 Pro with timeout hardening — not worth swapping to Grok 4 or downgrading to 2.5"
verdict: REVIEW
audit_date: 2026-04-15
pipeline_bugs_present: "yes — both conservative bias and context vacuum apply"
---

# D18 Audit

## Original Decision

Keep Gemini 3.1 Pro Preview in debate rotation. Add per-model timeout (120s vs 300s default) and automatic fallback to next model on timeout. Reject Grok 4 (account friction) and Gemini 2.5 Pro (weaker benchmarks).

## Original Rationale

Gemini 3.1 Pro has strong reasoning (Intelligence Index 57) but high latency tail (TTFT ~29s, p99=542s, 2.2% of calls >5 min). Timeout + fallback mitigates the tail risk. Grok 4 rejected as one-time setup cost. Gemini 2.5 Pro rejected as measurably weaker (II 35 vs 53/57 for peers). Removing Gemini entirely rejected as violating cross-family diversity invariant.

## Audit Findings

**F1 — EVIDENCED — STRUCTURAL: Fallback is only wired for refine rotation, not challenger persona calls.**

The decision states "automatic fallback to next model in rotation on timeout." Code review confirms this is only true for the `refine` command (debate.py line 2913-2915, explicit `fallback = models[(i+1) % len(models)]`). Challenger calls in `cmd_challenge` (line 1235) use `_call_litellm` directly, not `_call_with_model_fallback`. On timeout, challenger calls hit the `LLM_SAFE_EXCEPTIONS` handler (line 1243) and produce `[ERROR: ...]` output — no model substitution occurs. The `staff` and `pm` persona slots in config are static maps with no fallback target defined. The mitigation as described covers approximately 1 of 3 Gemini call paths.

**F2 — EVIDENCED — CORRECT: Gemini 2.5 Pro rejection is well-supported.**

II 35 vs 53/57 for peers. SWE-bench 73.1% vs 78.2%. A full tier below. In a debate engine whose value is cross-model error detection, a model that diverges significantly on capability is more likely to produce noise than signal. Rejection stands.

**F3 — EVIDENCED — GAP: Grok 4 rejection is deferral, not rebuttal, and lacks a revisit trigger.**

"New account friction" is an operational constraint, not an architectural finding. Grok 4 benchmarks (II 73, TTFT <2-7s) are objectively superior on every metric that motivated D18. The decision was appropriately pragmatic at the time, but no revisit trigger was documented. This is a minor process gap, not a flaw in the decision itself.

**F4 — ESTIMATED — GAP: No BuildOS-specific measurement of timeout frequency by stage.**

The 2.2% figure is a provider-reported p99. No local data on actual timeout rate in BuildOS challenger calls was collected. Stage-specific sensitivity (refine vs challenge) is uncharacterized.

## Verdict

**REVIEW**

Finding F1 is decisive: the decision's central mitigation claim ("automatic fallback to next model on timeout") is incomplete. Fallback is wired only in the refine path. Challenger calls fail with `[ERROR]` on timeout rather than substituting a fallback model. The decision is correct in intent and direction — Gemini should be kept, cross-family diversity is the right goal, the timeout constant (120s) is reasonable — but the implementation does not match the decision text, and one of the three Gemini call paths has no safety net.

## Risk Assessment

**Risk of keeping as-is:** On timeout, challenger calls silently degrade to `[ERROR]` responses rather than substituting a fallback. At 2.2% timeout rate in a parallel 3-challenger pipeline, the probability of at least one challenger timing out per run is roughly 6.4%. Those runs silently lose one voice. The debate output appears to proceed normally but is structurally missing a perspective.

**Risk of changing:** Low. Two concrete, bounded options exist: (1) wire `_call_with_model_fallback` in `_run_challenger` using the next persona's model as fallback target, or (2) extend `config/debate-models.json` with per-persona fallback mappings. Either is a small code change. No model swap required.

## Recommended Actions

1. **Fix the challenger fallback gap** (small code change, bounded scope): update `_run_challenger` in `cmd_challenge` to call `_call_with_model_fallback` with an explicit fallback target (e.g., `gpt-5.4` for Gemini persona slots). This closes F1.
2. **Add Grok 4 revisit trigger**: note in decisions.md or config notes that Grok 4 should be re-evaluated when xAI account setup is convenient. Tag as deferred, not rejected.
3. **Optional — measure timeout rate**: add a counter or log line when MODEL_TIMEOUTS fires in `_call_litellm` to make the 2.2% estimate empirically observable.

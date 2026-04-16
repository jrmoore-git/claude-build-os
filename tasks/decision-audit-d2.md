---
decision: D2
original: "Cross-model debate via LiteLLM proxy, not direct API calls"
verdict: HOLDS
audit_date: 2026-04-15
panel_models: claude-opus-4-6, gemini-3.1-pro, gpt-5.4
judge_note: "Judge step skipped — review panel unanimous HOLDS with no conflicting findings. Judge is designed to resolve divergence; unanimous convergence without divergence to resolve makes judge output vacuous."
---
# D2 Audit

## Original Decision

All multi-model calls route through a local LiteLLM proxy at localhost:4000 via `llm_client.py`. Direct API calls to Anthropic/OpenAI/Google are prohibited in application code.

## Original Rationale

Cross-model debate requires calling Claude, GPT, and Gemini from the same codebase. LiteLLM provides a unified OpenAI-compatible interface, avoiding 3 different SDKs with different auth, retry, and error patterns.

## Audit Findings

All three models (Claude Opus 4.6, Gemini 3.1 Pro, GPT-5.4) independently returned **HOLDS** with no dissents.

Key findings across the panel:

1. **Rationale strengthens under full context.** `config/debate-models.json` shows three model families as first-class participants. `llm_client.py` (825 lines) centralizes retry logic, error categorization, tool_choice defaults, temperature defaults, and fallback modes — complexity that exists regardless of the proxy. Without the proxy, this file would need three separate SDK integrations on top.

2. **No conservative bias present.** D2 is dated 2026-03-01 at project initialization — it was not produced by the debate pipeline and could not have been corrupted by L28/L29 pipeline bugs. It is an *enabling* decision (adds infrastructure to unlock capability), not a descoping one.

3. **Alternatives were fairly evaluated.** All three panels confirmed the rejections are well-reasoned: (a) per-SDK complexity is understated, not overstated; (b) Anthropic routing correctly rejected for non-coverage of GPT/Gemini; (c) cloud-hosted rejected with evidence (local proxy is running, no recorded failures).

4. **Degraded mode is visible and working.** `_anthropic_call` fallback activates automatically on connection refused. `is_fallback_active()` exposes state. The fallback is Anthropic-only (Gemini/GPT personas go silent when proxy is down) — this is the only identified gap, and it is a refinement concern, not a reversal trigger.

## Verdict: HOLDS

The proxy architecture is load-bearing for D13 (parallel review-panel), D18 (Gemini timeout hardening), and D5 (single-model thinking still routes through llm_client.py). Reversing would require refactoring `llm_client.py` and portions of `debate.py` (~4,136 lines assuming uniform calling conventions) with no identified benefit. The proxy has been operational across the full project history with no recorded failures.

## Risk Assessment

- **Risk of keeping:** Proxy process must be managed locally. Mitigated by automatic Anthropic fallback. When proxy is down, cross-model capability degrades to single-model — visible but not catastrophic. LiteLLM OSS dependency risk is standard and proxy is replaceable.
- **Risk of changing:** High. Refactoring cost to `llm_client.py` + `debate.py`, three separate auth/retry/error paths, loss of unified cost tracking, potential breakage of D13 parallel semantics. No identified benefit.

---
debate_id: litellm-fallback
created: 2026-04-18T09:29:25-0700
mapping:
  Judge: gpt-5.4
  A: claude-opus-4-6
  B: gemini-3.1-pro
  C: gpt-5.4
---
# litellm-fallback — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {'A': 'claude-opus-4-6', 'B': 'gemini-3.1-pro', 'C': 'gpt-5.4'}
Consolidation: 25 raw → 15 unique findings (from 3 challengers, via claude-sonnet-4-6 via local)

## Frame Critique
- Category: unstated-assumption
- Finding: The proposal assumes direct Anthropic API access is an appropriate fallback because Claude Code is present, but does not establish that product direction permits coupling BuildOS review availability to a separate Anthropic credential path rather than solving onboarding via a local/non-provider-specific single-model mode.
- Why this changes the verdict: Most challengers correctly attacked the missing API-key mechanics, but none questioned the broader load-bearing assumption that Anthropic-direct is the right fallback product choice at all, versus a provider-agnostic single-model path or an explicit local “review-lite” mode. This affects whether the proposed implementation is merely under-specified or strategically misframed.
- Severity: MATERIAL

## Judgment

### Challenge 1: Unverified Anthropic API key availability
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.96
- Evidence Grade: B (tool-verified absence of `ANTHROPIC_API_KEY` references plus governance/context reasoning about Claude Code auth flow)
- Rationale: This is the strongest challenge. The proposal’s core fallback path depends on credentials the proposal does not prove exist, and the cited tool evidence shows the repo currently does not load or reference that key. The challengers engaged the proposal directly and showed that, without a credential strategy, the fallback likely replaces one onboarding failure with another.
- Required change: Specify a concrete credential acquisition path for fallback, including behavior when `ANTHROPIC_API_KEY` is absent; either (a) require and document the env var explicitly with a preflight check and clear UX, or (b) redesign fallback to avoid assuming Anthropic-direct credentials.

### Challenge 2: Unnecessary third HTTP calling convention; simpler alternatives exist
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.88
- Evidence Grade: B (tool/context-supported by existing client structure and plausible reuse path)
- Rationale: The challengers do more than say “simpler is better”; they identify existing transport paths and a compositional alternative that preserves the current request/response flow. The proposal did not justify why a raw Anthropic Messages API implementation is necessary, so introducing a third calling convention looks like avoidable maintenance scope.
- Required change: Revise the implementation plan to reuse the existing dispatch/client abstraction if possible, and explicitly justify any new transport layer only if compatibility testing shows reuse is not viable.

### Challenge 3: Retry-loop interaction and overly broad fallback trigger
- Challenger: A/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Evidence Grade: A (tool-verified retry classification/backoff behavior cited from specific code locations)
- Rationale: This is a concrete implementation flaw: the proposal’s “first failure” language does not line up with existing retry behavior, and the trigger is too broad for safe mode-switching. Challengers engaged the mechanics rather than speculating, and they correctly show the current proposal would both delay fallback and risk false fallback on transient errors.
- Required change: Define fallback activation precisely: detect hard localhost proxy unavailability before or outside the generic retry loop, and do not trigger permanent fallback for generic network/timeouts without a local-proxy-specific signal.

### Challenge 4: Command-level `LITELLM_MASTER_KEY` gating not addressed
- Challenger: C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.93
- Evidence Grade: A (tool-verified early-return gating in command entrypoints)
- Rationale: This directly contradicts the proposal’s intended user outcome. If commands fail before `llm_client.py` is reached, the proposed fallback cannot deliver graceful degradation. The challenger identified a specific code-path blocker the proposal omitted.
- Required change: Update all command entrypoints that currently hard-gate on `LITELLM_MASTER_KEY` so they permit fallback mode, with clear branching between proxy-backed and fallback-backed execution.

### Challenge 5: Fallback bypass location unspecified; audit log and model routing integrity
- Challenger: A/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.84
- Evidence Grade: B (tool/context-supported references to persona mapping and artifact metadata semantics)
- Rationale: The concern is valid because “same artifact format” is not enough when metadata semantics change. The proposal leaves ambiguous whether substitution happens at routing or transport level, and that ambiguity matters for auditability, model labels, and downstream interpretation.
- Required change: Specify the interception layer explicitly and preserve semantic integrity in metadata/logging, e.g. record requested model(s), actual execution mode, and actual model used in fallback.

### Challenge 6: Judge independence violated without warning or mitigation
- Challenger: C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.82
- Evidence Grade: B (tool-verified existing judge-independence warning plus direct implication of fallback collapse)
- Rationale: The proposal includes `judge` in fallback but does not address the trust-model downgrade that results when one model plays all roles. Since independence is central to the review architecture, challengers are right that this is a material omission, not just a messaging nit.
- Required change: Add explicit fallback semantics for judge mode: stronger warning in CLI and artifact metadata, and either downgrade confidence / mark “non-independent judge” or skip independent-judge claims entirely in fallback mode.

### Challenge 7: Rate limits and concurrency under fallback
- Challenger: B
- Materiality: MATERIAL
- Decision: INVESTIGATE
- Confidence: 0.66
- Evidence Grade: C (partly tool/context-supported on concurrency, but rate-limit impact is estimated rather than repo-verified)
- Rationale: The concurrency concern is plausible and relevant, but the decisive claim about likely 429s is empirical and not well-supported enough to force a design verdict on its own. The proposal should address fallback execution mode, but whether concurrency must be disabled depends on actual provider limits and observed behavior.
- Investigation: Measure fallback review execution against the intended Anthropic path with 3 persona calls under both concurrent and sequential modes; sample size: at least 30 full review runs on a low-tier/dev credential; success criteria: <5% 429/error rate and acceptable p95 latency; BLOCKING: NO

### Challenge 8: Fallback mode not captured in artifact metadata
- Challenger: A/C
- Materiality: ADVISORY
- Decision: not judged
- Confidence: 0.82
- Rationale: Good advisory. It complements Challenge 5 and should likely be implemented, but it was correctly marked non-material by the challengers.

### Challenge 9: `single_review_default` config conflict unacknowledged
- Challenger: A
- Materiality: ADVISORY
- Decision: not judged
- Confidence: 0.74
- Rationale: Worth addressing in design cleanup, but not independently material to whether fallback should exist.

### Challenge 10: Single-model value claim stated as fact
- Challenger: A/C
- Materiality: ADVISORY
- Decision: not judged
- Confidence: 0.78
- Rationale: Fair framing criticism, but it does not block implementation if the proposal is reframed more carefully.

### Challenge 11: No test plan for fallback logic
- Challenger: C
- Materiality: ADVISORY
- Decision: not judged
- Confidence: 0.86
- Rationale: Sensible implementation hygiene note. It should be added to the plan, but lack of a test section alone is not a material objection.

### Challenge 12: Anthropic-direct fallback is an unstated product-direction assumption
- Challenger: JUDGE-FRAME
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.76
- Evidence Grade: C (reasoning from proposal framing rather than direct verification)
- Rationale: The proposal treats “fallback = direct Anthropic API” as if it naturally follows from the onboarding problem, but that is a design choice, not a given. Since the main user problem is “review unavailable without LiteLLM,” the proposal should justify why Anthropic-direct is the correct fallback architecture versus a provider-agnostic single-model path, a config-driven fallback, or an explicitly different degraded mode.
- Required change: Reframe the proposal around the actual requirement—graceful single-model review when LiteLLM is unavailable—and justify Anthropic-direct specifically against at least one provider-agnostic or config-driven alternative.

## Investigations
- Challenge 7: Measure fallback review execution against the intended Anthropic path with 3 persona calls under both concurrent and sequential modes; sample size: at least 30 full review runs on a low-tier/dev credential; success criteria: <5% 429/error rate and acceptable p95 latency; BLOCKING: NO

## Evidence Quality Summary
- Grade A: 2
- Grade B: 4
- Grade C: 2
- Grade D: 0

## Summary
- Accepted: 7
- Dismissed: 0
- Escalated: 0
- Investigate: 1
- Frame-added: 1
- Overall: REVISE with accepted changes

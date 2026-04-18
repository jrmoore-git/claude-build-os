---
debate_id: litellm-fallback
created: 2026-04-18T09:21:00-0700
mapping:
  Judge: gpt-5.4
  A: claude-opus-4-6
  B: gemini-3.1-pro
  C: gpt-5.4
---
# litellm-fallback — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {'A': 'claude-opus-4-6', 'B': 'gemini-3.1-pro', 'C': 'gpt-5.4'}
Consolidation: 25 raw → 16 unique findings (from 3 challengers, via claude-sonnet-4-6 via local)

## Frame Critique
- Category: unstated-assumption
- Finding: The proposal assumes direct Anthropic access is the right fallback because Claude Code is installed, but does not justify why Anthropic-specific fallback is preferable to a provider-agnostic “any available direct model credential” fallback.
- Why this changes the verdict: Several challenges catch implementation issues around `ANTHROPIC_API_KEY`, but none question the load-bearing product assumption that fallback should be Anthropic-only rather than “reuse whatever direct credential/config is actually present.” If this assumption is wrong, the proposed shape is unnecessarily narrow and may miss the onboarding goal.
- Severity: MATERIAL

## Judgment

### Challenge 1: Unverified `ANTHROPIC_API_KEY` availability
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.95
- Evidence Grade: A (tool-verified via code search showing no existing `ANTHROPIC_API_KEY` handling; proposal’s claim is otherwise unsupported)
- Rationale: This is the strongest flaw in the proposal. The onboarding benefit depends on direct Anthropic auth being broadly available, but the proposal provides no evidence for that and challengers directly show the codebase is not wired for it today. Because the whole feature can still hard-fail without that credential, this must be addressed.
- Required change: The proposal must define credential discovery and failure behavior explicitly: how fallback obtains auth, how missing auth is surfaced, and what the user sees when neither LiteLLM nor direct Anthropic auth is available.

### Challenge 2: Unnecessary third HTTP calling convention / custom Anthropic client
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.88
- Evidence Grade: B (tool-verified existence of multiple current call paths; reuse-via-compatible-endpoint is a credible architectural alternative but not directly verified in-repo)
- Rationale: The challengers engage the actual implementation shape and show the proposal chose the highest-maintenance route without justifying it. Since the proposal’s goal is graceful degradation, not bespoke Anthropic transport support, it should prefer reusing existing dispatch/client machinery where possible.
- Required change: Revise implementation to minimize transport divergence: prefer reuse of existing OpenAI-compatible path or another already-supported abstraction rather than adding a bespoke raw Anthropic `urllib` client, unless the proposal adds concrete reasons that reuse is impossible.

### Challenge 3: Fallback trigger interacts badly with existing retry loop
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.93
- Evidence Grade: A (tool-verified retryable-error and retry-loop behavior cited)
- Rationale: This is a real UX flaw and directly undermines the proposal’s stated goal of graceful degradation. If localhost proxy failures sit behind the normal retry loop, users will experience slow failure before fallback, and the proposal’s trigger condition is too vague to avoid accidental bypass on transient issues.
- Required change: Specify exact fallback activation rules, including immediate handling for localhost connection-refused/unreachable conditions and clear distinction from transient retryable errors where multi-model should still be attempted.

### Challenge 4: Unspecified interception point corrupts model routing, logging, and cost tracking
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.91
- Evidence Grade: A (tool-verified references to persona-model mapping and artifact/log model fields)
- Rationale: The proposal promises identical artifact structure while bypassing model routing, but does not explain how truthful model identity will be preserved. That is a material omission because silent substitution of one model for three changes semantics of artifacts and logs, not just transport details.
- Required change: Specify the interception point and how actual execution mode/model identity is recorded in logs and artifacts so fallback runs are not misrepresented as true multi-model reviews.

### Challenge 5: Command-level gating in `debate.py` not addressed
- Challenger: B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.94
- Evidence Grade: A (tool-verified preflight checks in command handlers)
- Rationale: If commands fail before any client call, `llm_client.py` fallback alone cannot solve the problem. This is a concrete gap between the proposal’s “surfaces affected” claim and the actual control flow.
- Required change: Update the proposal to include command-level gating changes in `debate.py` for every affected command, not just transport-layer fallback.

### Challenge 6: Judge independence violation not handled
- Challenger: A/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.84
- Evidence Grade: A (tool-verified judge independence checks and fallback behavior implied by proposal)
- Rationale: The proposal explicitly includes `judge` in fallback mode but does not account for the trust-model downgrade when judge and challengers collapse to the same model family. That does not necessarily kill the feature, but it does require explicit behavior and disclosure.
- Required change: Define fallback behavior for `judge`: e.g., stronger warning, reduced-confidence labeling, metadata flag, or command-specific restriction if independent judgment is a hard requirement.

### Challenge 7: Rate limits and concurrency not addressed
- Challenger: B/C
- Materiality: MATERIAL
- Decision: SPIKE
- Confidence: 0.68
- Evidence Grade: C (repo concurrency is tool-grounded, but rate-limit impact is external/plausible rather than directly evidenced here)
- Rationale: The concern is credible, but the materiality depends on actual observed direct-Anthropic limits and latencies for this workflow. In a reliability-sensitive path, Grade C is insufficient for outright acceptance under the stated rules; empirical verification would resolve whether sequentialization is necessary and how much UX cost it creates.
- Spike recommendation: Measure fallback-mode execution under both sequential and concurrent persona calls using a representative 30-run sample on fresh/typical credentials. Record latency, 429 rate, and completion success. Success criteria: choose the simplest mode with <5% hard failures and acceptable p95 latency threshold defined by team; BLOCKING: NO.

### Challenge 8: Artifact metadata doesn't record fallback mode
- Challenger: A/B/C
- Materiality: ADVISORY
- Decision: noted, not judged
- Confidence: 0.89
- Rationale: Good advisory. It supports transparency and mitigates Challenge 4, but by itself does not block the feature.

### Challenge 9: `single_review_default` config inconsistency
- Challenger: A
- Materiality: ADVISORY
- Decision: noted, not judged
- Confidence: 0.77
- Rationale: Worth reconciling in implementation. It is more of a design-consistency issue than a blocker.

### Challenge 10: Single-model vs. cross-model quality gap stated as fact
- Challenger: A/C
- Materiality: ADVISORY
- Decision: noted, not judged
- Confidence: 0.86
- Rationale: Fair framing correction. The proposal should present this as a pragmatic hypothesis, not an established empirical result.

### Challenge 11: No test plan for fallback logic
- Challenger: C
- Materiality: ADVISORY
- Decision: noted, not judged
- Confidence: 0.91
- Rationale: Strong implementation hygiene point. Given accepted material changes, explicit tests should be added.

### Challenge 12: Anthropic-only fallback is an unjustified narrow assumption
- Challenger: JUDGE-FRAME
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.82
- Evidence Grade: C (proposal-text reasoning; no direct repo verification needed)
- Rationale: The proposal’s product goal is “graceful degradation when LiteLLM is unavailable,” but its solution hardcodes that to “direct Anthropic because Claude Code is present.” Even if Anthropic direct fallback is viable, the proposal does not justify why fallback should be Anthropic-specific rather than based on any actually available direct credential/config, and that narrow assumption is load-bearing.
- Required change: Reframe the design around available direct credentials/capabilities rather than Anthropic presence alone, or explicitly justify why Anthropic-only fallback is the right scope despite reduced coverage.

## Evidence Quality Summary
- Grade A: 5
- Grade B: 1
- Grade C: 2
- Grade D: 0

## Spike Recommendations
- Fallback concurrency/rate-limit spike:
  - What to measure: fallback-mode success rate, 429 incidence, total latency for sequential vs concurrent 3-lens execution
  - Sample size: 30 runs per mode on representative prompts and credentials
  - Success criteria: <5% hard-failure rate; stable completion without recurring 429s; p95 latency within team-acceptable threshold
  - BLOCKING: NO

## Summary
- Accepted: 7
- Dismissed: 0
- Escalated: 0
- Spiked: 1
- Frame-added: 1
- Overall: REVISE with accepted changes

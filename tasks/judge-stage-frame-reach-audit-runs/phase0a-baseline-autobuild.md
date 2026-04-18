---
debate_id: autobuild-findings
created: 2026-04-17T18:14:56-0700
mapping:
  Judge: gpt-5.4
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# autobuild-findings — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {'A': 'claude-opus-4-6', 'B': 'gpt-5.4', 'C': 'gemini-3.1-pro'}
Consolidation: 15 raw → 14 unique findings (from 3 challengers, via claude-sonnet-4-6 via local)

## Judgment

### Challenge 1: Escalation trigger system may not exist as described
- Challenger: A/B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Evidence Grade: A
- Rationale: This is a concrete repo-structure/wording mismatch, and the proposal depends on that mechanism as its main safety story. The challenge is not generic skepticism: if the numbered triggers and specific behaviors like "3 failures = stop" and "scope growth" are not actually defined where claimed, the proposal is overstating existing safeguards rather than merely reusing them.
- Required change: Verify the actual escalation protocol source and wording, then update the proposal to either (a) reference the real definitions accurately, or (b) explicitly define the autobuild escalation triggers, including repeated failures, scope growth, ambiguous requirements, security-sensitive changes, irreversible side effects, and contradictory constraints.

### Challenge 2: Verification commands from the plan create an untrusted-shell-execution boundary
- Challenger: B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.95
- Evidence Grade: B
- Rationale: This is the strongest material challenge. The proposal's own design says the system will parse model-authored plan markdown and run `verification_commands`; that is enough to establish a real trust-boundary issue even without repo inspection. The proposal's "zero-risk" claim does not adequately address pre-review local side effects, and the challengers directly engage with that gap rather than offering generic security fear.
- Required change: Add a command-safety mechanism before any shell execution sourced from the plan artifact: e.g. structured schema for verification commands plus validation/allowlisting, explicit blocking of dangerous patterns (`rm`, network egress, credential access, migrations, shell redirection to sensitive paths, etc.), and escalation instead of execution when a command falls outside the safe set.

### Challenge 3: `surfaces_affected` is only a soft prompt guardrail, not enforced scope control
- Challenger: A/B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Evidence Grade: B
- Rationale: The challengers correctly identify a conservative-bias trap here: "reuse existing infrastructure" is only sufficient if it actually constrains behavior during autonomous execution. Prompt-only self-auditing is materially weaker once the human is removed from the build loop, and the proposal does not show any deterministic enforcement. The reduced fix proposed by challengers does not undercut the broader autobuild concept; it hardens it.
- Required change: Add a deterministic scope check in the autobuild flow, at minimum a post-step hard stop comparing `git diff --name-only` to the approved `surfaces_affected` list before proceeding. Preferably also check intended edit targets before execution when possible.

### Challenge 4: No context window management strategy for long builds
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.76
- Evidence Grade: C
- Rationale: The concern is valid, but the evidence is mostly architectural reasoning rather than verified failure data. Still, the proposal itself acknowledges context exhaustion as a likely issue and offers no mitigation; challengers are engaging with the proposal's own admitted weakness, not inventing a new one. Rejecting the entire proposal over this would be too strong, but requiring a containment strategy is reasonable.
- Required change: Define an explicit v1 limit or budget mechanism: e.g. autobuild only for plans under a stated size/step threshold, or a checkpoint/resume rule that escalates before context becomes dangerously thin.

### Challenge 5: Plan artifact may not be reliably machine-actionable
- Challenger: B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.84
- Evidence Grade: B
- Rationale: This challenge goes to the heart of whether the simpler "just add 60-80 lines" approach actually solves the problem. The proposal assumes the current plan output is structured enough to drive sequential implementation, file scoping, and test execution, but does not provide evidence that current plan artifacts are stable enough for this use. The challenger does engage with the proposal's evidence and highlights a real gap rather than arguing for unnecessary new infrastructure.
- Required change: Specify a minimal machine-readable contract for plans used with `--build`—at least stable sections/fields for ordered steps, `surfaces_affected`, and `verification_commands`—and require autobuild to escalate if the plan does not conform.

### Challenge 6: Retry loops can introduce regressions
- Challenger: A
- Materiality: ADVISORY
- Decision: Not judged
- Confidence: 0.74
- Rationale: Sensible implementation advice. It builds on the proposal's own concern about degraded retries, but it is not necessary to block the proposal if the accepted changes above are made.

### Challenge 7: "Security-sensitive changes" lacks detection criteria
- Challenger: B
- Materiality: ADVISORY
- Decision: Not judged
- Confidence: 0.8
- Rationale: Good hardening advice, and it overlaps with accepted Challenge 1 and 2. If the proposal defines explicit triggers and command safety, this should likely be incorporated as part of that work.

### Challenge 8: Parallel worktree agents are premature for v1
- Challenger: A
- Materiality: ADVISORY
- Decision: Not judged
- Confidence: 0.78
- Rationale: This is a scope-management recommendation, not a demonstrated flaw. It is a reasonable caution, but the proposal's core value does not depend on parallelism, so this is better treated as optional descoping unless the authors want a narrower v1.

### Challenge 9: Step-level approval gate would reduce rollout risk
- Challenger: A
- Materiality: ADVISORY
- Decision: Not judged
- Confidence: 0.67
- Rationale: This is a product/rollout alternative, not a defect. It may be useful as a staged rollout option, but the challenger does not show that the full proposal is unworkable if the accepted safeguards are added.

## Spike Recommendations
None

## Summary
- Accepted: 5
- Dismissed: 0
- Escalated: 0
- Spiked: 0

## Evidence Quality Summary
- Grade A: 1
- Grade B: 3
- Grade C: 1
- Grade D: 0

- Overall: REVISE with accepted changes

The proposal has a real upside and the challengers did not successfully rebut the core premise: there is a meaningful gap between planning and review, and rejecting autobuild entirely would leave the highest-friction phase manual. The challengers' strongest points are not "don't build this," but "the current safety and execution assumptions are overstated." With explicit escalation definitions, command-validation for verification commands, deterministic scope enforcement, a minimal plan schema, and a context-budget/size limit for v1, the proposal becomes materially stronger without abandoning its low-infrastructure philosophy.

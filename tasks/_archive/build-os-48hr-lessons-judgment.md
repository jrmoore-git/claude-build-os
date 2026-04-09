---
debate_id: build-os-48hr-lessons
created: 2026-03-15T19:26:56-0700
mapping:
  Judge: gpt-5.4
  A: gpt-5.4
  B: gemini-3.1-pro
---
# build-os-48hr-lessons — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {'A': 'gpt-5.4', 'B': 'gemini-3.1-pro'}

## Judgment

### Challenge 1: Deterministic E2E test may be infeasible in many real systems
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.95
- Rationale: This is a real flaw in the original wording of Change 1, which states a feature is not done until a deterministic end-to-end test proves full-path flow. Many systems have async workflows, eventual consistency, or third-party dependencies where a fully deterministic deploy-time E2E test is not always practical; without carve-outs, the policy would be overbroad and invite either fake compliance or friction.
- Required change: Amend the integration-gate language to allow architecture-appropriate alternatives when deterministic automated E2E is infeasible, e.g. documented manual verification or bounded integration checks, with explicit guidance on fixture isolation and acceptable verification criteria.

### Challenge 2: Deploy-script gate lacks rollback/idempotency/cleanup operational guidance
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.91
- Rationale: The proposal’s deploy-script pattern and deploy-time integration gate do create operational concerns if they mutate shared environments, partially restart systems, or fail mid-sequence. The absence of guidance on idempotency, cleanup, failure handling, and rollback is a meaningful gap because the proposal elevates this mechanism into a recommended enforcement pattern.
- Required change: Add implementation safeguards to the pattern: scripts/tests should be idempotent where possible, clean up synthetic fixtures, define timeout/retry behavior, emit clear failure states, and specify rollback or safe-stop behavior when partial execution can leave the system unhealthy.

### Challenge 3: “Skip straight to architecture” after one failure is too aggressive
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.87
- Rationale: The challenge is valid because the original shortcut language overgeneralizes from “someone forgot” to “therefore architectural enforcement is warranted,” when the underlying cause may be discoverability, poor defaults, or ambiguity. The proposal should distinguish procedural tasks that are cheap and clearly automatable from cases where stronger enforcement would be premature or burdensome.
- Required change: Replace the broad “skip levels” rule with narrower guidance: purely mechanical, low-cost procedural steps should be automated directly; keep the three-strikes escalation model for discretionary or higher-cost governance problems.

### Challenge 4: “Deploy script as enforcement” is too specific; principle should be system-boundary enforcement
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.89
- Rationale: This is a substantive framing issue. The generalizable lesson is not specifically “use a deploy script,” but “enforce integrated verification at the authoritative execution boundary”; scripts are one implementation, but CI/CD promotion pipelines or other gates may be more appropriate in many environments.
- Required change: Reframe Change 3 around the principle of executable verification at the system boundary, with deploy scripts presented as one concrete example rather than the canonical approach.

### Challenge 5: Integration gate and C9 contract test are redundant / C9 dilutes contract tests
- Challenger: A/B
- Materiality: ADVISORY for A, MATERIAL for B
- Decision: ACCEPT
- Confidence: 0.93
- Rationale: As a material challenge from B, this is persuasive: the proposal duplicates the same lesson in the Definition of Done and by adding a new “contract test,” while contract tests usually serve a different doctrinal role than generic end-to-end verification. Keeping both would add conceptual and maintenance overhead without clear added value.
- Required change: Drop Change 6 (C9) and keep the end-to-end/integration requirement in the Definition of Done and related testing guidance only.

### Challenge 6: Enforcement ladder shortcut adds branching complexity; procedural tasks should simply be automated
- Challenger: B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Rationale: This is a valid simplification. The proposed “when to skip levels” subsection introduces extra decision logic into the ladder, whereas the underlying lesson can be expressed more cleanly: procedural, mechanical steps should be automated rather than governed through advisory escalation.
- Required change: Remove the branching “skip levels” subsection and replace it with a concise clarification that procedural steps should be automated immediately, while the ladder remains for judgment-based failures.

### Challenge 7: Shared query constants are not universally safe / are basic DRY and out of scope
- Challenger: A/B
- Materiality: ADVISORY for A, ADVISORY for B
- Decision: DISMISS
- Confidence: 0.77
- Rationale: The criticism has merit as product advice, but both challengers marked it advisory, so it is not a material defect requiring judgment here. It may still be wise to drop the change for scope reasons, but that is not necessary to resolve a material flaw under the requested standard.
- Required change: N/A

### Challenge 8: Session-log trigger thresholds are weakly specified
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.84
- Rationale: This is advisory and not a material blocker. The proposed trigger is reasonably concrete for lightweight process guidance; refinement with more observable symptoms could improve it, but the current text is not flawed enough to require rejection.
- Required change: N/A

## Summary
- Accepted: 6
- Dismissed: 2
- Escalated: 0
- Overall: REVISE with accepted changes

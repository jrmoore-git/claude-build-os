---
debate_id: explore-intake
created: 2026-04-18T09:14:24-0700
mapping:
  Judge: gpt-5.4
  A: claude-opus-4-6
  B: gemini-3.1-pro
  C: gpt-5.4
---
# explore-intake — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {'A': 'claude-opus-4-6', 'B': 'gemini-3.1-pro', 'C': 'gpt-5.4'}
Consolidation: 22 raw → 18 unique findings (from 3 challengers, via claude-sonnet-4-6 via local)

## Frame Critique
- Category: already-shipped
- Finding: The proposal claims it is “replacing the 5-track fixed questions (from last session’s design)” and instructs removal of `config/prompts/preflight-tracks.md`, but verification evidence is pending and no challenger verified whether that file is actually present, active, or already superseded.
- Why this changes the verdict: If tracks were never shipped or are already inactive, part of the proposal’s problem framing and rollback plan is inaccurate, and the claimed migration/removal work may be partially redundant. This does not invalidate the intake redesign itself, but it could change scope and rollout details.
- Severity: MATERIAL

## Judgment

### Challenge 1: Prompt-only slot sequencing may be too fragile to act as a reliable state machine
- Challenger: A/B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.84
- Evidence Grade: C (plausible architectural reasoning, but no direct tool verification of backend behavior)
- Rationale: This is a real flaw in the proposal as written. The proposal makes the slot sequence central to behavior, but does not specify an enforcement mechanism beyond prompt changes; the challengers appropriately engaged the architecture rather than offering generic skepticism. The proposal’s evidence supports the sequence design conceptually, but not the implementation reliability of multi-turn state progression.
- Required change: Specify and implement explicit per-turn state handling: either backend-tracked slot state injected each turn, or a simpler protocol that does not depend on strict sequential memory. The verification plan must include tests for skipped/repeated/misordered slots.

### Challenge 2: Rollback path is internally inconsistent if `preflight-tracks.md` is deleted
- Challenger: B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.96
- Evidence Grade: B (directly supported by the proposal text itself)
- Rationale: This is clear-cut. If the rollout removes a file, rollback cannot also “remove” it; the rollback instructions are inconsistent with the described change. This is a change-hygiene issue, but still material because rollback correctness matters operationally.
- Required change: Rewrite rollback steps to explicitly restore `config/prompts/preflight-tracks.md` if removed, or clarify that the file was never shipped and therefore rollback only reverts `preflight-adaptive.md`.

### Challenge 3: User-derived context promotion creates prompt-injection risk without delimiting rules
- Challenger: C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.88
- Evidence Grade: B (strong security reasoning grounded in the proposal’s described data flow)
- Rationale: The proposal explicitly promotes user-derived content into structured prompt context and introduces an “ASSUMPTIONS TO CHALLENGE” section that could easily contain instruction-like text. In a high-risk security domain, accepting user text into higher-salience prompt regions without serialization/delimiting rules is a valid concern, and the challenger is engaging the actual design, not speculating broadly.
- Required change: Add explicit trust-boundary rules: quote or serialize all user-derived text, label it as untrusted content, prohibit executable/instructional interpretation, and define sanitization for derived sections such as “ASSUMPTIONS TO CHALLENGE.”

### Challenge 4: No redaction/data-handling policy for sensitive content solicited during intake
- Challenger: C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Evidence Grade: B (high-risk governance concern directly tied to proposal behavior)
- Rationale: The protocol deliberately solicits sensitive organizational and political detail, yet provides no handling guidance for secrets, regulated data, or sensitive inferences reflected back at confirmation. In a high-risk data-handling context, this omission is material and sufficiently supported by the proposal’s own intended intake behavior.
- Required change: Add a data-handling section covering: do-not-solicit categories, redaction/masking rules, confirmation-safe summarization, and logging/transcript guidance for sensitive or inferred content.

### Challenge 5: Input-clarity classification is treated too deterministically despite subjective boundaries
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.78
- Evidence Grade: C (reasonable reasoning from proposal text, not directly verified)
- Rationale: The proposal presents question-count calibration as if routing is straightforward, but the operational criteria are underdefined and example-based. The proposal’s research supports adaptive question counts in principle, but not this specific classification scheme as a deterministic rule. The challenger correctly identifies misclassification as consequential to both user friction and context quality.
- Required change: Recast classification as heuristic rather than deterministic, add concrete routing criteria/fallbacks, and include “ask one extra if uncertain” or equivalent ambiguity handling in the protocol.

### Challenge 6: The 200-500 token context budget is heuristic, not evidenced as a hard target, and hard to enforce
- Challenger: A/B
- Materiality: MATERIAL
- Decision: DISMISS
- Confidence: 0.73
- Evidence Grade: C (reasonable but not strong enough to overturn the proposal)
- Rationale: The challengers are right that 200-500 is heuristic rather than a proven optimum, and token counting by prompt is approximate. But the proposal uses the range as a compression target, not a hard fail threshold, and its evidence for “compact beats verbose” is directionally relevant. This does not expose a core design flaw unless the implementation turns the range into rigid verification gating, which the proposal does not require.
- Required change: None.

### Challenge 7: No instrumentation or post-ship feedback loop
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.82
- Evidence Grade: C (process/design reasoning, no direct verification needed)
- Rationale: This is a valid under-engineering concern. The proposal draws heavily from external research and proposes several tunable heuristics, but its verification plan is essentially one-shot and does not generate learning after ship. The cost of inaction here is that the team may lock in routing and composition behavior without any way to know if it improves real explore outcomes.
- Required change: Add lightweight instrumentation and review criteria: intake length used, skip rate, confirmation-edit rate, user aborts before explore, and a small post-ship audit of output divergence/quality.

### Challenge 8: Slot 4 engagement heuristic uses speculative word-count and emotion thresholds
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.8
- Evidence Grade: C
- Rationale: Not judged materially. The concern is fair, but the proposal’s stated fallback—defaulting to the softer frame-and-correct approach when uncertain—contains the risk. This is implementation tuning, not a blocking design issue.

### Challenge 9: One-at-a-time questions may cause latency-driven drop-off unlike Typeform
- Challenger: B
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.68
- Evidence Grade: C
- Rationale: The analogy gap is real, but the challenger does not engage the proposal’s countervailing claim that one-at-a-time is strongly supported across conversational systems, not just forms. Latency may matter, but without actual measured drop-off this remains a hypothesis and not enough to materially undermine the design.

### Challenge 10: Mandatory confirmation checkpoint may add friction if explore generation is fast
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.7
- Evidence Grade: C
- Rationale: This is a plausible UX trade-off, but not clearly a flaw. The proposal justifies confirmation as quality control for composed context, and challengers did not fully account for the cost of skipping it—namely incorrect dimensions, tension, and assumptions being fed into the final explore output. Optionality could be considered later, but this does not block the proposal.

### Challenge 11: Removing tracks may also remove a place for domain-specific guardrails
- Challenger: A/C
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.77
- Evidence Grade: C
- Rationale: The concern is legitimate but already partly answered by the proposal’s intent to preserve domain inference and adaptive question selection. Still, the challenge usefully highlights what must not be lost in migration. Because it is framed as “relocate, don’t lose” rather than “don’t proceed,” it is advisory and not a reason to reject the redesign.
- Required change: None.

### Challenge 12: Failure-modes section is somewhat overlong for issues already structurally addressed
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.93
- Evidence Grade: C
- Rationale: Minor documentation clarity point only. It does not materially affect the proposal.

### Challenge 13: Unverified “replace/delete tracks” scope may be stale if tracks are not actually active or shipped
- Challenger: JUDGE-FRAME
- Materiality: MATERIAL
- Decision: SPIKE
- Confidence: 0.62
- Evidence Grade: C (no repository verification available)
- Rationale: This is a frame-level gap: the proposal’s migration/removal narrative depends on repository state that no challenger verified. If `preflight-tracks.md` is absent, inactive, or already superseded, part of the proposal’s scope and rollback framing is stale. This may not flip the intake redesign, but it could materially change rollout/rollback and remove a claimed benefit.
- Spike recommendation: Check repository state: whether `config/prompts/preflight-tracks.md` exists, is referenced anywhere, and is currently used in explore flow; inspect recent commits for prior removal/supersession. Success criteria: determine whether tracks are active shipped behavior, dormant file, or already removed. BLOCKING: NO

## Spike Recommendations
- Verify repository state for `config/prompts/preflight-tracks.md`: existence, references, and active use in explore flow; inspect recent commit history for prior removal/supersession. Success criteria: classify as active / dormant / already removed, and update proposal scope + rollback accordingly. BLOCKING: NO

## Evidence Quality Summary
- Grade A: 0
- Grade B: 3
- Grade C: 10
- Grade D: 0

## Summary
- Accepted: 6
- Dismissed: 6
- Escalated: 0
- Spiked: 1
- Frame-added: 1
- Overall: REVISE with accepted changes

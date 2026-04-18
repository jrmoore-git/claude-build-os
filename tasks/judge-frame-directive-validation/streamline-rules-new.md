---
debate_id: streamline-rules
created: 2026-04-18T09:14:52-0700
mapping:
  Judge: gpt-5.4
  A: claude-opus-4-6
  B: gemini-3.1-pro
  C: gpt-5.4
---
# streamline-rules — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {'A': 'claude-opus-4-6', 'B': 'gemini-3.1-pro', 'C': 'gpt-5.4'}
Consolidation: 35 raw → 19 unique findings (from 3 challengers, via claude-sonnet-4-6 via local)

## Frame Critique
- Category: inflated-problem
- Finding: The proposal asserts governance effectiveness is materially harmed by duplication/verbosity, but provides no concrete examples of observed failures or evidence that the claimed 10–12% reduction meaningfully changes compliance in this repo.
- Why this changes the verdict: This does not negate the contradiction fixes, but it weakens the justification for broad Phase 2/3 churn. Without demonstrated operational harm, the safer path is targeted cleanup rather than full compression.
- Severity: MATERIAL

## Judgment

### Challenge 1: Cross-file references may weaken enforcement in selective-loading contexts
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Evidence Grade: C
- Rationale: This is the strongest challenge. The proposal’s core guarantee is “same enforcement,” yet Phase 2 repeatedly replaces inline rules with references without providing any co-loading matrix or evidence that referred files are always present when needed. The challengers directly engaged with the proposal’s mechanism, and the proposal offers no verification to rebut the risk.
- Required change: Add a load-context matrix for every new reference in Phase 2, and either (a) prove the canonical target is always loaded wherever the referring file is loaded, or (b) keep a one-line normative summary inline in the referring file.

### Challenge 2: No acceptance test for “zero governance impact”
- Challenger: B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.88
- Evidence Grade: C
- Rationale: The proposal makes a strong invariance claim—no rules removed, no enforcement weakened—without a traceability mechanism. For a governance-edit proposal, that is a real verification gap. The challengers appropriately request rule mapping and reference validation rather than generic skepticism.
- Required change: Provide a before/after traceability matrix of normative rules, plus a validation pass for all introduced references/anchors and a review confirming no rule became context-dependent or weaker.

### Challenge 3: 1A picks “before” without verifying semantics
- Challenger: A/B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.84
- Evidence Grade: C
- Rationale: The proposal treats “after material decisions” vs “before implementing material decisions” as an obvious contradiction, but the challengers correctly note those may describe adjacent but compatible moments. Since 1A changes policy semantics, not just wording, the author needs confirmation of intended meaning. The proposal provides no evidence that “before” is the actual intended rule.
- Required change: Do not change 1A unilaterally. Confirm intended timing semantics with the rule owner or governing source, then rewrite all affected files to that confirmed policy.

### Challenge 4: Phase 3B removes an enforcement trigger (“Any match = rewrite”)
- Challenger: A/B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.94
- Evidence Grade: C
- Rationale: This challenge is substantively correct on the proposal text alone. “Any match = rewrite” is not mere preamble; it specifies required action on violation. Removing it weakens enforcement and directly contradicts the proposal’s stated constraint.
- Required change: Keep the enforcement directive, possibly in tightened form, e.g. “Any anti-pattern match = rewrite.”

### Challenge 5: Canonical files become single points of failure
- Challenger: A/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.82
- Evidence Grade: C
- Rationale: This is partly a restatement of Challenge 1, but it adds a maintainability concern: centralization increases blast radius of drift, omission, or broken references. The proposal includes no owner/process/check to manage that fragility. Given the recommendation to canonicalize multiple rules, this is a real structural gap.
- Required change: Add drift prevention: canonical-owner designation, periodic/reference checks, and a rule that referrers must either retain a summary or be proven to co-load with the canonical file.

### Challenge 6: 1C centralization relies on implicit compatibility, not explicit deference
- Challenger: A/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Evidence Grade: C
- Rationale: This is a narrow but valid point. If CLAUDE.md is canonical for skip logic, workflow.md should explicitly defer rather than merely remain “compatible.” Otherwise the proposal leaves open future drift—the very problem it is trying to solve.
- Required change: Update workflow.md to explicitly state that /challenge skip conditions are defined in CLAUDE.md, rather than relying on implication.

### Challenge 7: 1D leaves residual ambiguity in “essential eight” framing
- Challenger: C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.72
- Evidence Grade: C
- Rationale: The challenger is right that “essential eight (6 applicable)” remains awkward and can preserve confusion about the excluded two. This is lower-severity than Challenges 1–6, but still a valid clarity issue in an ambiguity-fixing phase. The proposal’s own goal is to reduce ambiguity, and this wording does not fully do so.
- Required change: Restate the BuildOS-applicable invariant set explicitly in review-protocol.md, or rename the local concept to avoid the 8-vs-6 mismatch.

### Challenge 8: Split session-start reading list creates partial-compliance risk
- Challenger: C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.75
- Evidence Grade: C
- Rationale: This is a valid instance of the same reference-risk pattern. If CLAUDE.md lists a short set and says “see workflow.md for full checklist,” a model may stop at the short set unless loading behavior guarantees workflow.md is in context. The proposal does not define whether the short list is minimum or complete.
- Required change: Clarify in CLAUDE.md that the listed docs are a minimum and that the full required orient-before-planning checklist is in workflow.md; if workflow.md is not guaranteed loaded, keep the required checklist inline in CLAUDE.md.

### Challenge 9: Phase 3 tightening removes rationale useful in edge cases
- Challenger: A/C
- Materiality: ADVISORY
- Decision: N/A
- Confidence: 0.78
- Rationale: Advisory only. This is a legitimate maintainability trade-off, especially in security-related guidance, but it does not by itself prove the proposal must change unless a specific rewrite weakens behavior.

### Challenge 10: Token savings estimate is unitemized and potentially overstated
- Challenger: A/B/C
- Materiality: ADVISORY
- Decision: N/A
- Confidence: 0.86
- Rationale: Advisory only. The estimate is clearly rough and under-supported, but token-count precision is not central unless the proposal depends on a quantified ROI threshold. It does, however, reinforce the frame-level concern that the broad scope may be over-justified.

### Challenge 11: Safer deduplication strategy is inline summary + reference
- Challenger: A/C
- Materiality: ADVISORY
- Decision: N/A
- Confidence: 0.88
- Rationale: Advisory only. This is a strong alternative design and aligns with the accepted concerns on loading/enforcement. It is best treated as implementation guidance for revising Phase 2 rather than as an independent material defect.

### Challenge 12: Micro-token edits lack prioritization by governance value
- Challenger: A/C
- Materiality: ADVISORY
- Decision: N/A
- Confidence: 0.83
- Rationale: Advisory only. This is a fair process critique and consistent with the proposal’s weak evidence for broad compression impact. It supports sequencing the work, but does not itself establish a discrete correctness flaw.

### Challenge 13: Compliance-improvement benefit of 10–12% reduction is unverified
- Challenger: B/C
- Materiality: ADVISORY
- Decision: N/A
- Confidence: 0.84
- Rationale: Advisory only. The challengers correctly note the proposal does not show measured compliance gain from a modest token reduction. That weakens the case for lower-value edits, though not for contradiction cleanup.

### Challenge 14: Problem statement inflates governance harm from duplication/verbosity without operational evidence
- Challenger: JUDGE-FRAME
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.81
- Evidence Grade: C
- Rationale: The proposal’s strongest demonstrated problem is contradiction, not verbosity. It cites a general principle about instruction count but gives no repo-specific evidence of failures caused by current duplication or of measurable gains from the proposed compression. This matters because it argues against approving all phases as a bundled package.
- Required change: Re-scope the proposal to prioritize demonstrated harms: Phase 1 first, then only Phase 2/3 items with explicit proof they preserve enforcement and provide meaningful value.

## Spike Recommendations
None

## Evidence Quality Summary
- Grade A: 0
- Grade B: 0
- Grade C: 9
- Grade D: 0

## Summary
- Accepted: 9
- Dismissed: 0
- Escalated: 0
- Spiked: 0
- Frame-added: 1
- Overall: REVISE with accepted changes

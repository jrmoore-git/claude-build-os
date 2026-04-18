---
debate_id: streamline-rules
created: 2026-04-17T18:15:36-0700
mapping:
  Judge: gpt-5.4
  A: claude-opus-4-6
  B: gemini-3.1-pro
  C: gpt-5.4
---
# streamline-rules — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {'A': 'claude-opus-4-6', 'B': 'gemini-3.1-pro', 'C': 'gpt-5.4'}
Consolidation: 35 raw → 18 unique findings (from 3 challengers, via claude-sonnet-4-6 via local)

## Judgment

### Challenge 1: Cross-file references may weaken rules if target files are not loaded
- Challenger: Consolidated
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Evidence Grade: C
- Rationale: This is the central weakness in the proposal. The proposal repeatedly claims "same governance" and "no enforcement weakened," but it does not provide any loading/co-loading evidence to show that replacing inline rules with "See X.md" preserves behavior in practice. The challengers directly engaged with the proposal's deduplication design; the proposal's token-saving rationale does not answer the enforcement question.
- Required change: Add a loading matrix for all affected files showing which are always loaded, conditionally loaded, and co-loaded. Any rule moved behind a reference must either (a) point only to an always-loaded file, or (b) retain a one-line normative summary inline plus reference for details. If this cannot be shown, revise Phase 2 architecture accordingly.

### Challenge 2: 1A timing semantics ("before" vs "after") may be unresolved rather than contradictory
- Challenger: Consolidated
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.84
- Evidence Grade: C
- Rationale: The challengers make a strong point that "after material decisions" and "before implementing" may describe the same intended boundary, and the proposal does not prove that CLAUDE.md's "after" is actually wrong. Because this is governance text, choosing one semantic interpretation without confirming intent risks changing policy, not just compressing it. The proposal's evidence supports ambiguity generally, but not this specific resolution.
- Required change: Do not unilaterally rewrite 1A to "before" as stated. Either confirm intended semantics from rule ownership/history, or rewrite all three files to a neutral clarified form such as "Document material decisions once made and before implementation begins."

### Challenge 3: No acceptance test for the "zero governance impact" claim
- Challenger: Consolidated
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.92
- Evidence Grade: C
- Rationale: This is valid and distinct from Challenge 1. Even if the architecture is corrected, the proposal still lacks a traceability method to verify that every normative rule remains present and equally strong after edits. Challengers engaged the proposal directly; the proposal offers estimates and intent, but no validation mechanism.
- Required change: Add a before/after rule traceability matrix mapping each normative rule to its post-change location, plus a reference integrity check for every "See X.md" link. The proposal should define a review checklist or scriptable verification pass before rollout.

### Challenge 4: Removing design.md preamble deletes an enforcement trigger
- Challenger: Consolidated
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Evidence Grade: C
- Rationale: "Any match = rewrite" is not mere prose; it is the operative instruction. The proposal classifies it as removable verbosity without addressing that it specifies the response to detecting an anti-pattern. This directly conflicts with the proposal's own "no enforcement weakened" constraint.
- Required change: Retain an explicit enforcement instruction in design.md, e.g. preserve "Any match = rewrite" or equivalent imperative language.

### Challenge 5: 1C centralization should use explicit deferral, not just passive compatibility
- Challenger: Consolidated
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.82
- Evidence Grade: C
- Rationale: This is a conservative but sound governance concern. The proposal correctly centralizes skip conditions, but leaving workflow.md merely "compatible" invites future drift and partial-reader ambiguity. A small explicit-deferral change preserves the proposal's goal while reducing long-term inconsistency risk.
- Required change: Update workflow.md to explicitly defer skip-condition authority to CLAUDE.md, rather than relying only on compatible wording.

### Challenge 6: 1D still leaves ambiguity around the "essential eight"
- Challenger: Consolidated
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.71
- Evidence Grade: C
- Rationale: This is narrower than Challenge 2, but still valid. Saying "essential eight" while also saying only six apply can preserve the original confusion in a softened form. The proposal's intent is good, but the wording could be clearer and more locally self-contained.
- Required change: Rewrite review-protocol.md to state the applicable BuildOS invariants directly, or explicitly name them as "BuildOS-applicable invariants," rather than relying on a superset/subset count reference.

### Challenge 7: Splitting the session-start reading list may create partial compliance
- Challenger: Consolidated
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.77
- Evidence Grade: C
- Rationale: This concern is valid because the proposal preserves a short list in CLAUDE.md and points elsewhere for the full checklist, but does not explain how to prevent the short list from being treated as sufficient. The proposal's simplification rationale is real, but challengers correctly note the cost of inaction only if the full checklist is truly optional; here the proposal implies it is not.
- Required change: Clarify in CLAUDE.md whether the listed documents are the minimum required set and that workflow.md contains additional required session-start reads for planning/risky work; or keep a compact but complete mandatory list in CLAUDE.md.

### Challenge 8: Some preamble/rationale removals may strip operational context
- Challenger: Consolidated
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.79
- Evidence Grade: C
- Rationale: The challengers are right that the proposal treats several cuts as obviously safe when some may contain disambiguating rationale, especially in security and orchestration guidance. This does not invalidate all Phase 3 compression, but it does mean the proposal needs a per-edit classification rather than a blanket "verbosity" label. The proposal's evidence for token savings is not enough to justify potentially losing interpretive context.
- Required change: Classify each proposed Phase 3 cut as one of: purely historical, redundant rationale preserved elsewhere, or operationally necessary. Only remove text in the first two categories; preserve or rephrase the third.

### Challenge 9: Token savings and "zero governance impact" are unverified quantitative claims
- Challenger: Consolidated
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.88
- Evidence Grade: D
- Rationale: The challengers are correct that the specific figures are speculative as written. Their own numerical criticism is also not tool-verified, but the proposal provides no line-item token audit, so the safe judgment is that these estimates must be labeled as estimates, not accepted as established fact. This does not defeat the proposal, but it does require reframing and measurement.
- Required change: Relabel all token counts and savings as estimates unless backed by an explicit token audit. Provide per-file before/after counts if the numbers are important to approval.

### Challenge 10: CLAUDE.md "always-loaded" status is unverified
- Challenger: Consolidated
- Materiality: ADVISORY
- Decision: Not judged
- Confidence: 0.0
- Rationale: Advisory only.

### Challenge 11: Phase 3 compression may trade maintainability for token savings
- Challenger: Consolidated
- Materiality: ADVISORY
- Decision: Not judged
- Confidence: 0.0
- Rationale: Advisory only.

### Challenge 12: Safer deduplication architecture exists
- Challenger: Consolidated
- Materiality: ADVISORY
- Decision: Not judged
- Confidence: 0.0
- Rationale: Advisory only.

### Challenge 13: Compliance improvement from 10-12% reduction is unverified
- Challenger: Consolidated
- Materiality: ADVISORY
- Decision: Not judged
- Confidence: 0.0
- Rationale: Advisory only.

## Spike Recommendations
None

## Evidence Quality Summary
- Grade A: 0
- Grade B: 0
- Grade C: 8
- Grade D: 1

## Summary
- Accepted: 9
- Dismissed: 0
- Escalated: 0
- Spiked: 0
- Overall: REVISE with accepted changes

The proposal identifies real problems: duplicated rules, contradictory wording, and unnecessary verbosity do impose cost, and challengers generally concede that Phase 1 ambiguity cleanup is high-value. But the current draft overclaims safety. The major issue is that the proposal treats cross-reference compression as governance-preserving without proving equivalent loading semantics, and it lacks a traceability/verification plan to back the "zero governance impact" claim. Rejected as-is would leave genuine ambiguity and bloat in place; however, approval should be contingent on revising the proposal to preserve inline normative guidance where needed, explicitly resolve semantic ambiguities, and add a verification method.

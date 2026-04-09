---
debate_id: buildos-agent-gaps-debate
created: 2026-04-05T20:33:33-0700
mapping:
  Judge: gpt-5.4
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# buildos-agent-gaps-debate — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {'A': 'claude-opus-4-6', 'B': 'gpt-5.4', 'C': 'gemini-3.1-pro'}

## Judgment

### Challenge 1: Gap 1 is already documented; treating it as a real gap would duplicate or hallucinate requirements
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.98
- Rationale: This is directly contradicted by the proposal’s own Appendix A. `docs/team-playbook.md` explicitly mentions `.claude/agents/`, and `docs/platform-features.md` has a dedicated subagents section with example YAML and documented capabilities, so “completely absent” is clearly false.
- Required change: Update the proposal to explicitly mark Gap 1 as a false positive / non-gap, not merely “likely real.” Any follow-up work should be limited to possible refinement or discoverability improvements, not net-new documentation of the feature itself.

### Challenge 2: Gap 4 mixes one disproven claim (`TeammateIdle`) with other unverified operational assertions
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Rationale: The supplied docs verify that `TeammateIdle` is not a listed hook event, while `SubagentStart` is. The rest of Gap 4’s specifics may or may not exist, but in this record they are unverified external assertions, so the proposal should not treat them as established documentation requirements.
- Required change: Split Gap 4 into verified-false and unverified subclaims. Explicitly quarantine `TeammateIdle` and require external verification before considering any of the other claimed controls for documentation.

### Challenge 3: Gap 5 is overstated because several claimed subagent capabilities are already documented while others are unsupported
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.95
- Rationale: Appendix A2 already documents tool restrictions, model override, worktree isolation, and skills access. Claims about agent-memory paths, per-subagent hooks, and permission modes are not supported by the provided materials, so treating the whole gap as uncovered would conflate real coverage with speculation.
- Required change: Reframe Gap 5 as a partial false positive: note what is already covered, and quarantine the unsupported feature claims pending independent verification.

### Challenge 4: The proposal lacks an explicit verification standard for platform features not already documented internally
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.92
- Rationale: This is a real process flaw, especially given the proposal itself identifies hallucinated platform features as the main risk. Without a defined evidence bar, the review could still smuggle unverified vendor features into BuildOS docs based on plausible-sounding claims.
- Required change: Add a verification gate: any feature not already evidenced in BuildOS docs must be confirmed by primary vendor docs, reproducible CLI/help output, or tested local behavior before it can become a documentation task.

### Challenge 5: The right next step is to bucket the 10 gaps, not treat them as a single backlog
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.88
- Rationale: This is a sound restructuring of the work. The record already supports at least three categories: already documented/non-gaps, verify-first claims, and framework-design questions; forcing all items into one remediation list would obscure the real status of each.
- Required change: Revise the proposal to categorize each gap into: non-gap/already covered, verify-first, low-priority framework choice, or reject as harmful/unsupported.

### Challenge 6: Gap 1 is factually wrong because `.claude/agents/` is already covered
- Challenger: B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.98
- Rationale: Same core issue as Challenge 1, independently raised. The overlap corroborates that this is a clear flaw in the proposal’s current stance, though the evidence is the docs themselves.
- Required change: Same as Challenge 1: mark Gap 1 as already covered and remove it from the actionable gap list.

### Challenge 7: Several claimed gaps likely reference hallucinated features and should not be documented without verification
- Challenger: B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.84
- Rationale: The concern is directionally valid, but part of the support relies on absence-of-string matches in unspecified “scripts/config” outside the Appendix, which is weaker than direct evidence from the provided docs. Still, the proposal’s own stated risk and the verified `TeammateIdle` contradiction make it necessary to quarantine unsupported claims rather than treat them as requirements.
- Required change: Add an explicit quarantine list for unsupported features (e.g. `/plugin`, `TeammateIdle`, agent-memory path, `/loop` and `/schedule` unless externally verified), and prohibit adding them to framework docs until verified.

### Challenge 8: The proposal critiques flat “F” grading but does not replace it with a prioritization scheme
- Challenger: B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.86
- Rationale: This is a legitimate gap in the proposal’s methodology. If the grading scheme is rejected but no replacement ranking is defined, the team still lacks a principled way to decide which verified gaps matter enough to document.
- Required change: Add a prioritization rubric based on user impact, failure severity if undocumented, and evidence/feature stability.

### Challenge 9: Gap 6 would be an architectural regression because it replaces cross-model review diversity with same-platform subagents
- Challenger: B
- Materiality: MATERIAL
- Decision: ESCALATE
- Confidence: 0.63
- Rationale: The challenge raises a real trade-off, but it depends partly on repository facts not present in the proposal Appendix (`debate-models.json`) and on product/design judgment about review independence versus orchestration convenience. This is not a simple factual correction; it is a strategy choice about review architecture.
- Spike recommendation: N/A

### Challenge 10: The proposal should be reframed as a small verified backlog plus a quarantine list, not a 10-item remediation plan
- Challenger: B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.87
- Rationale: This substantially overlaps with A’s bucketing challenge, and the substance is persuasive. Given the clear false positives and unverified items, a reduced verified backlog plus quarantine list is a better framing than preserving all 10 as candidate work items.
- Required change: Recast the output of this review into a verified backlog, a quarantine list, and a separate design-questions section.

### Challenge 11: Documenting hallucinated features would actively harm users
- Challenger: C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.82
- Rationale: This overlaps with earlier verification/quarantine concerns and is substantively valid. Some cited support depends on tool results not shown here, but the core point is independently supported by the verified mismatch around `TeammateIdle` and by the proposal’s stated risk model.
- Required change: Make “do not document unverified platform features” an explicit acceptance criterion for any resulting documentation changes.

### Challenge 12: Gap 1 being accepted as “likely real” is factually incorrect
- Challenger: C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.98
- Rationale: Clear-cut and fully evidenced in Appendix A. The proposal’s initial assessment is too permissive on a claim already disproven by the included docs.
- Required change: Remove Gap 1 from the “likely real and worth documenting” list and relabel it as already documented.

## Spike Recommendations
None

## Summary
- Accepted: 11
- Dismissed: 0
- Escalated: 1
- Spiked: 0
- Overall: ESCALATE to human

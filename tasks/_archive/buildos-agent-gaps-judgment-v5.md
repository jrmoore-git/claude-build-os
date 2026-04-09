---
debate_id: buildos-agent-gaps-debate-v5
created: 2026-04-05T22:23:16-0700
mapping:
  Judge: gpt-5.4
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# buildos-agent-gaps-debate-v5 — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {'A': 'claude-opus-4-6', 'B': 'gpt-5.4', 'C': 'gemini-3.1-pro'}

## Judgment

### Challenge 1: Gap 1 falsely says `.claude/agents/` is absent
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.98
- Rationale: This challenge is directly supported by the proposal’s own Appendix A1 and A2. `team-playbook.md` explicitly mentions custom subagent definitions in `.claude/agents/`, and `platform-features.md` has a dedicated “Subagents (.claude/agents/)” section with example YAML. The original gap claim is therefore factually wrong and should not drive documentation work.
- Required change: Reclassify Gap 1 from “completely absent” to “already documented; at most assess whether discoverability or cross-linking should improve.”
- Evidence Grade: A (directly verified from Appendix A1/A2)

### Challenge 2: Gaps 3/4/5/7/9 rely on nonexistent or unverified platform features
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Rationale: The proposal itself asks for feature reality checks, and the provided evidence directly falsifies at least part of this bundle: `TeammateIdle` is not a documented hook event in Appendix A3. For the other claims (`/tasks`, `~/.claude/agent-memory/`, `/loop`, `/schedule`, `/plugin`), the challenger's strongest point is not that they are conclusively nonexistent, but that they are unverified within the supplied corpus and therefore unsafe to document as facts. Given the explicit hallucination risk, the proposal needs an evidence gate before treating these as real gaps.
- Required change: Add a per-gap verification rule: each claimed platform feature must be labeled as one of (a) already documented in BuildOS, (b) externally verified Claude Code capability, or (c) unsupported/speculative and excluded from framework docs until validated.
- Evidence Grade: B (direct verification for `TeammateIdle`; strong governance reasoning for the rest, but not full direct verification)

### Challenge 3: “Review swarm” is an unjustified replacement for `debate.py`
- Challenger: A
- Materiality: MATERIAL
- Decision: DISMISS
- Confidence: 0.79
- Rationale: The challenge correctly notes that the gap analysis does not prove review swarms are better, but the proposal already frames Gap 6 as “valid insight but questionable priority” and explicitly asks whether it adds value or just complexity. Since the proposal is a review of the gap analysis, not a commitment to replace `debate.py`, this criticism does not identify a flaw requiring change in the proposal itself.
- Evidence Grade: C (plausible reasoning, but not a proposal flaw)

### Challenge 4: The proposal must separate “missing from BuildOS docs” from “confirmed Claude Code capability”
- Challenger: B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.95
- Rationale: This is a sound methodological challenge. The supplied corpus is sufficient to determine whether BuildOS docs mention something, but not sufficient by itself to prove vendor-platform behaviors like built-in subagents, backgrounding, or headless mode. Without separating those questions, the review can accidentally convert model assertions into project documentation.
- Required change: Update the review method to evaluate each gap on two axes: (1) whether BuildOS currently documents it, and (2) whether the underlying Claude Code feature is independently verified outside BuildOS.
- Evidence Grade: B (methodological governance point grounded in the provided constraints)

### Challenge 5: Unverified feature docs could weaken downstream controls and automations
- Challenger: B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.87
- Rationale: In a framework/operating-model context, documenting nonexistent commands, hooks, or paths can cause users to wire automations around phantom surfaces, which is a real operational risk. The challenge is especially strong where it overlaps with other reviewers on `TeammateIdle`, `/plugin`, `/loop`, and `/schedule`. This is a high-risk reliability/governance concern, and the needed remedy is stricter evidence gating before docs changes.
- Required change: Add a hard rule that no new operational command, hook, path, or lifecycle event may be added to BuildOS docs without external product-source validation or equivalent authoritative evidence.
- Evidence Grade: B (strong governance reasoning with partial repo spot-check context)

### Challenge 6: The proposal lacks an explicit evidence standard for accepting gaps
- Challenger: B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.96
- Rationale: This is effectively the core process flaw exposed by the adversarial reviews. Because the proposal’s goal is to evaluate hallucination-prone claims, it needs a formal acceptance rubric; otherwise reviewers can only argue ad hoc. This change is required before proceeding because it directly controls whether false features enter the docs backlog.
- Required change: Add an explicit acceptance rubric for each gap: “already documented,” “absent but externally evidenced,” or “unsupported/speculative,” with only the first two eligible for documentation work.
- Evidence Grade: B (clear process deficiency inferred from the proposal structure)

### Challenge 7: The gap analysis’s hallucination risk is more severe than the proposal implies
- Challenger: C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.84
- Rationale: The exact quantitative framing (“zero evidence”) depends partly on tool use not reproduced here, so I do not fully credit the stronger factual assertions. But the underlying challenge is valid: multiple claimed gaps are already contradicted or unsupported by the provided appendices, so the proposal should treat the source analysis as potentially contaminated rather than merely imperfect. That warrants a stronger verification-first posture.
- Required change: Revise the proposal framing to state that the gap analysis is not a reliable source of feature truth and that every claim requires independent verification before prioritization.
- Evidence Grade: B (supported by overlap with other verified contradictions and governance context)

### Challenge 8: Gap 4 improperly bundles real and fabricated claims
- Challenger: C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.91
- Rationale: This is valid. Gap 4 mixes heterogeneous items—UI/display ideas, coordination mechanics, messaging, shutdown protocol, and a hook event that is directly contradicted by Appendix A3—making it impossible to judge priority or truth cleanly. The bundle should be decomposed before any recommendation is made.
- Required change: Split Gap 4 into separate feature claims and evaluate each independently, especially separating hook/event claims from UX/operational workflow claims.
- Evidence Grade: A (direct support from Appendix A3 plus structure of the gap description)

### Challenge 9: Gap 5 claims unsupported subagent memory/hooks capabilities
- Challenger: C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Rationale: Appendix A2 lists actual documented subagent capabilities: tool restrictions, model override, worktree isolation, and skills access. It does not mention persistent memory directories or per-subagent hooks, so the current gap claim overreaches beyond the supplied evidence. In this context, the safe judgment is that these specific claimed capabilities are unsupported and must not be documented without external validation.
- Required change: Narrow Gap 5 to only evidenced subagent capabilities, and treat persistent memory directories/per-subagent hooks as unsupported unless independently verified from authoritative Claude Code sources.
- Evidence Grade: A (direct comparison against Appendix A2)

### Challenge 10: Gap 6 may be worse than the current cross-model review design
- Challenger: C
- Materiality: MATERIAL
- Decision: DISMISS
- Confidence: 0.74
- Rationale: This challenge argues the alternative may be inferior, but that is a design trade-off rather than a demonstrated flaw in the proposal. The proposal already expresses skepticism and asks whether subagents add value or complexity. Since it does not endorse the swarm pattern as a required change, no proposal revision is necessary on this point.
- Evidence Grade: C (reasonable but not dispositive against the proposal)

## Spike Recommendations
None

## Summary
- Accepted: 8
- Dismissed: 2
- Escalated: 0
- Spiked: 0
- Overall: REVISE with accepted changes

## Evidence Quality Summary
- Grade A: 3
- Grade B: 5
- Grade C: 2
- Grade D: 0

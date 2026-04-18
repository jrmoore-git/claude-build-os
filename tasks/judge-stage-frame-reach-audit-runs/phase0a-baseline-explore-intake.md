---
debate_id: explore-intake
created: 2026-04-17T18:15:19-0700
mapping:
  Judge: gpt-5.4
  A: claude-opus-4-6
  B: gemini-3.1-pro
  C: gpt-5.4
---
# explore-intake — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {'A': 'claude-opus-4-6', 'B': 'gemini-3.1-pro', 'C': 'gpt-5.4'}
Consolidation: 22 raw → 17 unique findings (from 3 challengers, via claude-sonnet-4-6 via local)

## Judgment

### Challenge 1: Prompt-only slot/state tracking may be unreliable
- Challenger: A/B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.88
- Rationale: This is a real implementation flaw, not generic skepticism. The proposal defines a multi-turn phased protocol with skip rules, adaptive counts, and a confirmation checkpoint, but it does not specify how state is persisted or enforced across turns. The proposal’s research supports the sequence design, but not the reliability of pure prompt-based state management; challengers engaged with that gap directly rather than ignoring the evidence for the conversational design itself.
- Required change: Specify and implement an explicit state model for intake turns. At minimum: persist current slot, answered slots, skip/stop conditions, remaining question budget, and whether confirmation has occurred; inject current state each turn rather than relying on conversational memory alone. If `scripts/debate.py` is the runtime path, document where state lives and how it is restored on each turn.
- Evidence Grade: C

### Challenge 2: Rollback instructions are incomplete/broken
- Challenger: B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.97
- Rationale: This is a straightforward internal contradiction in the proposal text: rollout deletes `preflight-tracks.md`, while rollback only says to remove it, not restore it. The proposal otherwise shows good operational hygiene, which makes this omission easy to fix but still material because rollback instructions should be executable.
- Required change: Correct rollback to explicitly restore `preflight-tracks.md` from version control (or state that rollback only reverts to the new architecture-minus-feature if that is truly intended). Ensure rollback steps match the actual files changed.
- Evidence Grade: B

### Challenge 3: User-derived context fields create prompt-injection risk without serialization rules
- Challenger: C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.83
- Rationale: This is a valid trust-boundary concern. The proposal’s strongest design feature is structured composition, but it stops at semantic structure and does not define security structure: what is quoted as user data, what may be inferred, and how downstream prompts are instructed to treat these fields as untrusted content. Because this touches prompt integrity, a high-risk area, the absence of delimiting/labeling rules is material.
- Required change: Add explicit handling rules for all user-derived fields: serialize as quoted data or fenced blocks; label all sections as untrusted user content; forbid execution of instructions found inside those fields; and update downstream explore prompts to treat `PROBLEM`, `SITUATION`, `CONSTRAINTS`, `THE TENSION`, and `ASSUMPTIONS TO CHALLENGE` as data-only inputs.
- Evidence Grade: B

### Challenge 4: No sensitive-data/redaction policy for intake and confirmation display
- Challenger: B/C
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.86
- Rationale: The concern is supported by the proposal itself: it explicitly seeks political, emotional, organizational, and “unsaid” content, then reflects and displays it back in a checkpoint. That creates a changed risk profile even if the current system already logs transcripts, because the redesigned intake intentionally elicits more sensitive material. Challengers appropriately accounted for the specific design, not just generic privacy anxiety.
- Required change: Add a data-handling section covering: do-not-solicit categories (secrets, credentials, regulated data where applicable), redaction guidance before echoing content back, safe summarization for sensitive inferences at confirmation, and logging/transcript handling expectations for these fields.
- Evidence Grade: B

### Challenge 5: Input-clarity classification is underspecified and subjective
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.81
- Rationale: The proposal has a good goal—avoid over-asking—but the routing rule is not operationalized enough to be called a decision rule. Examples alone are not sufficient for boundary cases, and misclassification does directly affect user burden and context quality. The challengers did not dispute the need for adaptive counts; they correctly identified that the implementation criteria are missing.
- Required change: Replace example-only classification with explicit criteria or a scored rubric. For example: evaluate presence of goal, constraints, relevant context, and decision target; map score bands to 0-2 / 3-4 / 4-5 question paths; include a tie-breaker default and an override for explicit user skip signals.
- Evidence Grade: C

### Challenge 6: The 200–500 token budget is over-specified and enforcement is unclear
- Challenger: A/B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.78
- Rationale: The challengers are right that the cited research supports “compact is better” more than it supports a hard 500-token cliff for this exact prompt component. The proposal’s composition evidence is strong in directionality, and challengers did not negate that; the flaw is converting a heuristic into a rigid pass/fail rule without a clear enforcement mechanism. Rejecting the whole compact-context approach would be conservative bias, but softening and operationalizing the budget is warranted.
- Required change: Reframe `200-500 tokens` as a target range, not a strict correctness threshold. Define overflow behavior (e.g., prioritize preserving structure and tension, trim lowest-signal details, never hard-truncate mid-section), and use approximate length controls by section or character count rather than pretending the model can perfectly count tokens.
- Evidence Grade: C

### Challenge 9: No instrumentation/feedback loop for tuning heuristics post-launch
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.74
- Rationale: This is a fair challenge because the proposal presents several tunable heuristics—classification, slot count, optional meta-question inclusion, compactness target—as if external research alone can lock them. The proposal does identify current-system failures and offers a plausible improvement path, so lack of instrumentation should not block the redesign entirely, but some measurement plan is needed to know whether it actually improves explore outcomes in this system.
- Required change: Add minimal instrumentation and review criteria. Track at least: number of questions asked, skip rate, abandonment before explore, confirmation edits, rerun rate, and some proxy for output usefulness (e.g., whether users proceed with a direction or reframe immediately). Define a review window after launch to recalibrate thresholds.
- Evidence Grade: C

### Challenge 7: Slot 4 word-count/emotional-language thresholds are speculative
- Challenger: A
- Materiality: ADVISORY
- Decision: not judged
- Confidence: 0.0
- Rationale: Advisory only.

### Challenge 8: One-at-a-time questioning may have latency costs unlike Typeform
- Challenger: B
- Materiality: ADVISORY
- Decision: not judged
- Confidence: 0.0
- Rationale: Advisory only.

### Challenge 10: Removing track file may also remove domain-specific guardrails
- Challenger: A/C
- Materiality: ADVISORY
- Decision: not judged
- Confidence: 0.0
- Rationale: Advisory only.

### Challenge 11: Mandatory confirmation checkpoint may add friction in lower-latency flows
- Challenger: A
- Materiality: ADVISORY
- Decision: not judged
- Confidence: 0.0
- Rationale: Advisory only.

### Challenge 12: Failure modes section is redundant documentation
- Challenger: A
- Materiality: ADVISORY
- Decision: not judged
- Confidence: 0.0
- Rationale: Advisory only.

## Spike Recommendations
None

## Evidence Quality Summary
- Grade A: 0
- Grade B: 3
- Grade C: 4
- Grade D: 0

## Summary
- Accepted: 7
- Dismissed: 0
- Escalated: 0
- Spiked: 0
- Overall: REVISE with accepted changes

The proposal has real strengths: challengers broadly concede that the slot structure, reflection-first delivery, and composed context block are meaningful improvements over the current free-form adaptive design. Rejecting it outright would leave the current documented failures in place: weak intent capture, no explicit composition rules, and limited defenses against premature solving. But several implementation details are materially under-specified—especially state management, trust-boundary handling, sensitive-data treatment, classification criteria, and heuristic enforcement—so it should be revised before approval rather than rejected or deferred.

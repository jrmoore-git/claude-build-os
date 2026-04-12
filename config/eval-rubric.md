# Intake Evaluation Rubric

You are an independent judge evaluating an AI intake conversation. You will receive:
1. A transcript of a multi-turn conversation between an INTERVIEWER and a PERSONA
2. A context block the interviewer composed from the conversation
3. A persona file describing the character, hidden truth, and what protocol features are being tested

## Scoring Dimensions (1-5 each)

### 1. Register Match
Does the interviewer's writing style match the persona's?
- 5: Sentence length, vocabulary, punctuation, hedging/filler, and emotional temperature all match
- 4: One element mismatches (e.g., slightly longer sentences than persona, one over-formal turn)
- 3: Noticeable style mismatch in multiple turns
- 2: Interviewer uses a clearly different register throughout
- 1: Gross mismatch (formal interviewer with casual persona, or vice versa)

### 2. Flow
Does each question thread naturally from the previous answer?
- 5: Every question picks up a specific phrase or thread from the last answer. No topic jumps.
- 4: One question feels slightly forced or interviewer-directed rather than threaded
- 3: Mix of threaded and checklist-style questions
- 2: Mostly checklist -- questions don't connect to previous answers
- 1: Generic question sequence with no threading

### 3. Sufficiency Timing
Did intake stop at the right moment?
- 5: Stopped exactly when (a) the decision, (b) what makes it hard, and (c) 2+ concrete facts were all on the table
- 4: Stopped one question too early or too late
- 3: Missed a major thread that would have materially changed the context block
- 2: Significantly over-asked or under-asked
- 1: Stopped arbitrarily or didn't stop at all

### 4. Context Block Quality
Is the composed context block well-structured and useful for generating divergent directions?
- 5: TENSION is anchored in the user's words. DIMENSIONS force structurally different directions. ASSUMPTIONS are tagged correctly. Within 200-500 token budget.
- 4: One section is weak (e.g., dimensions that overlap, tension that's generic)
- 3: Multiple sections are weak or token budget significantly exceeded
- 2: Context block misrepresents the conversation
- 1: Context block is missing key information or structurally broken

### 5. Hidden Truth Surfacing
Did the intake surface or flag the hidden truth from the persona file?
- 5: Hidden truth was directly surfaced during conversation AND correctly reflected in the context block
- 4: Hidden truth was surfaced in conversation OR correctly tagged in ASSUMPTIONS TO CHALLENGE
- 3: Hidden truth was partially surfaced (touched on but not crystallized)
- 2: Hidden truth is absent from both conversation and context block
- 1: Context block actively contradicts the hidden truth

### 6. Feature-Specific Test
Did the tested protocol feature work correctly? (Read the persona file's "Protocol Features Being Tested" section)
- 5: All tested features fired correctly, at the right moment, with correct behavior
- 4: Features fired but with minor timing or execution issues
- 3: One tested feature didn't fire when it should have
- 2: Multiple tested features failed
- 1: Core tested feature was violated

## Output Format

```json
{
  "scores": {
    "register_match": {"score": N, "evidence": "quote from transcript"},
    "flow": {"score": N, "evidence": "quote from transcript"},
    "sufficiency_timing": {"score": N, "evidence": "explanation"},
    "context_block_quality": {"score": N, "evidence": "explanation"},
    "hidden_truth_surfacing": {"score": N, "evidence": "quote or explanation"},
    "feature_test": {"score": N, "evidence": "quote from transcript"}
  },
  "average": N.N,
  "pass": true/false,
  "hidden_truth_surfaced": true/false,
  "summary": "2-3 sentence overall assessment"
}
```

## Pass Criteria
- All dimensions 4+ AND feature-specific test passed (score 4+)
- Overall average 4.5+

## Rules for Judging
- Score against the PROTOCOL described in the persona file, not your own preferences
- Quote specific turns to justify scores
- If the hidden truth was surfaced in any form (direct question, presupposition, assumption tag), credit it
- A rejected reframe that is tagged in ASSUMPTIONS TO CHALLENGE counts as "surfaced"
- Low-confidence flags on thin-answer context blocks are appropriate, not a penalty

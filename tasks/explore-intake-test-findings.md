---
topic: explore-intake
phase: persona-test-findings
created: 2026-04-11
test_count: 6
---

# Explore Intake Protocol — Persona Test Findings

## Test Matrix

| # | Persona | Age | Role | Input | Classification | Slots | Score | Hidden Recovery |
|---|---------|-----|------|-------|----------------|-------|-------|-----------------|
| 1 | Priya | 29 | Lead backend eng, fintech | "We need to figure out our microservices migration strategy" | Moderate | 5 (escalated) | 30/30 | 5/5 |
| 2 | Marcus | 34 | Senior eng, Series B startup | "I'm thinking about whether I should move into management" | Moderate | 4 | 28/30 | 4/5 |
| 3 | Sarah | 41 | VP Product, B2B SaaS | Long, well-specified input with goal/constraints/context | Well-specified | 2 (Slots 2+4) | 4.3/5 | 4/5 |
| 4 | David | 52 | COO, professional services | "I need to think about our organizational culture" | Ambiguous | 5 | 4.9/5 | 4.5/5 |
| 5 | Jake | 28 | Solo founder, pre-revenue | "how to monetize my dev tool" | Moderate | 4 | 4.7/5 | 5/5 |
| 6 | Amara | 37 | Founder/CEO, dev agency | "I got an acquisition offer and I can't figure out if I should take it" | Moderate | 4 | 4.7/5 | 5/5 |

**Coverage:** All 3 non-skip clarity tiers tested. Domains: engineering, career, product strategy, organizational, startup, M&A. Persona types: terse, verbose, political, emotional, technical, articulate. NOTE: Persona selection skewed toward therapy-adjacent profiles (emotional founder, nervous career changer). Future testing should focus on the actual audience: exec-level thinkers, product builders, VCs, engineers — go-getters who want sharper thinking, not hand-holding.

## Aggregate Scores

| Criterion | Priya | Marcus | Sarah | David | Jake | Amara | Avg |
|-----------|-------|--------|-------|-------|------|-------|-----|
| Flow | 5 | 4 | 4 | 5 | 4 | 4 | 4.3 |
| Depth | 5 | 5 | 4 | 5 | 5 | 5 | 4.8 |
| Assumption surfacing | 5 | 5 | 5 | 5 | 4 | 5 | 4.8 |
| Efficiency | 5 | 5 | 5 | 5 | 5 | 4 | 4.8 |
| Context block quality | 5 | 5 | 4.5 | 5 | 5 | 5 | 4.9 |
| Hidden context recovery | 5 | 4 | 4 | 4.5 | 5 | 5 | 4.6 |

**Protocol overall: 4.7/5.** Strongest on depth, assumption surfacing, efficiency, and context block quality. Weakest on flow (mechanical transitions) and hidden context recovery (misses when political/success-criteria dimensions exist).

## What Worked (Validated Across Multiple Tests)

1. **Slot 4 (Assumption Challenge) is the highest-value slot.** Every test rated it the turning point. David's governance reframe, Priya's "this is test infra not architecture," Jake's "company or hobby," Sarah's "org problem not product problem" — all unlocked by Slot 4.

2. **Push-once rule.** Star of the Jake test — cracked a 6-word answer into 3 paragraphs. Correctly unused with Priya, Sarah, Amara (who didn't need pushing). Well-calibrated.

3. **One question per message.** Forced patience. Prevented premature solving. Particularly valuable with David (needed space to process governance reframe) and Jake (would have disengaged with batched questions).

4. **Reflection before asking.** Created empathy with emotional personas (Amara), demonstrated comprehension with technical personas (Priya), and built progressive trust with political personas (David). Universal positive.

5. **Classification rule.** Correct in 5 of 6 tests. Sarah's well-specified routing to 2 questions was adequate (though barely). Priya's moderate routing worked. David's ambiguous routing was right. Jake's moderate routing was right.

6. **Context block template.** All 6 tests produced blocks rated 4.5+/5. The structured format (PROBLEM, SITUATION, CONSTRAINTS, THE TENSION, ASSUMPTIONS, DIMENSIONS) consistently captured layered problems well. Token budgets were respected.

7. **Meta-question (Slot 5).** Earned its keep in both tests where it was used: Priya (burnout/attrition) and David (comp equity gap). Both surfaced the most emotionally significant hidden element.

## Protocol Amendments (10 Changes)

### A1: Mid-Intake Escalation Rule
**Source:** Sarah (4.3/5), Priya (escalated to 5 slots)
**Problem:** Classification is static. If a user's Slot 2 answer reveals hidden complexity not present in the initial input, the protocol has no mechanism to add questions.
**Amendment:** After any intake answer, if the response introduces a major dimension absent from the initial input, the interviewer may add one additional slot. Recommend adding Slot 3 (constraints/attempts) for well-specified inputs that escalate, or Slot 5 (meta-question) for moderate inputs that escalate.
**Rule:** "If an answer reveals a major new dimension not present in the initial input, add one slot. Do not re-classify — just extend."

### A2: Solution-as-Input Classification Rule
**Source:** Priya (30/30 — but flagged the classification gap)
**Problem:** "We need to figure out our microservices migration strategy" sounds well-specified but names a solution, not a problem. A less careful implementation might route this to 1-2 questions and miss the real issue (test infrastructure, not architecture).
**Amendment:** When the initial input names a solution or approach rather than a problem or question, classify one tier vaguer than surface appearance. "Microservices migration strategy" → moderate (not well-specified). "How to monetize" → moderate (not well-specified). This prevents premature convergence on the user's initial frame.
**Rule:** "If the input presents a solution or approach as the topic (rather than a problem, question, or decision), classify one tier vaguer than surface indicators suggest."

### A3: Slot 2 Variants
**Source:** Jake (Slot 2 was highest-risk for terse users), Marcus (Slot 2 near-redundancy with Slot 1)
**Problem:** "If you got this right, what would it change or make possible?" is abstract. Terse/concrete thinkers give flat answers. When Q1 already surfaces stakes, Slot 2 feels redundant.
**Amendment:** Three Slot 2 variants, selected based on Q1 response:
- **Abstract (default):** "If you got this right, what would it change or make possible?"
- **Concrete/identity:** "Keep working on it as what?" / "For whom?" / "What does 'right' look like?"
- **Past-anchored cost:** "What's it costing you right now that this isn't figured out?"

**Selection rule:** If Q1 answer is under ~30 words or purely concrete/factual, use concrete/identity variant. If Q1 already includes emotional or stakes language, use past-anchored cost variant. Otherwise use abstract default.

### A4: Reflection Length Matching
**Source:** Jake (fragment reflections worked; full-sentence would have annoyed him)
**Problem:** "1-2 sentence reflection" is one-size-fits-all. Terse users tolerate "Growing tool, shrinking runway" (4 words). They will not tolerate "So what I'm hearing is that you have a successful open-source project but you're feeling uncertain about the financial sustainability..." (26 words).
**Amendment:** Match reflection length to user's communication register. Fragment users get fragment reflections. Paragraph users get full-sentence reflections.
**Rule:** "Reflect in the register the user writes in. If they use fragments, reflect in fragments. If they write paragraphs, reflect in 1-2 sentences. Never reflect at greater length than the user's longest answer."

### A5: Two Types of Vagueness
**Source:** David (4.9/5 — but flagged the gap)
**Problem:** "Push once if vague" treats all vagueness the same. But uninformed vagueness (hasn't thought it through) and politically careful vagueness (knows but can't say directly) need different interventions.
**Amendment:** Two push strategies:
- **Uninformed vague:** "You said [their word]. Can you be specific — a name, a number, a date?" (current push)
- **Politically careful vague:** Offer a structural frame they can agree with without naming the person/issue. "It sounds like this might be about [structural pattern]. Is that close?"

**Detection heuristic:** If the user speaks in careful paragraphs with hedging language ("I think there's a question about...", "It's a delicate needle to thread"), they're likely politically careful. If they speak in short, flat sentences ("just need to figure it out", "I dunno"), they're likely uninformed.

### A6: Register Matching (Replaced Emotional Disclosure Guidance)
**Source:** Amara (4.7/5), user feedback ("this is not a therapist")
**Problem:** Original A6 prescribed "name the feeling, not the situation" — therapy language inappropriate for a business tool. The real insight is simpler: mirror the user's register.
**Amendment:** Delivery Rule #2 says "match the user's register." If they're analytical, stay analytical. If they're blunt, be blunt. If they're technical, be technical. No feeling-naming, no facilitator tone. The register of a sharp colleague, not a coach.

### A7: Success Criteria Sub-Probe
**Source:** Sarah (flagged undefined "traction" at checkpoint — should have been caught during intake)
**Problem:** The 5 slots don't include "how will you know this worked?" For decision-oriented inputs, success criteria shape every dimension.
**Amendment:** Embed as optional compound in Slot 2: "If you got this right, what would it change — and how would you know you got there?"
**Rule:** Not a separate slot. A sub-probe within Slot 2 that fires when the input describes a decision or goal with measurable outcomes. Skip for pure exploration ("I want to rethink our approach").

### A8: Checkpoint Wording
**Source:** Marcus (flagged that "What should I correct?" invites factual error-checking, not gut pushback)
**Problem:** "What should I correct before I run it?" frames the checkpoint as a fact-check. Users tend to say "looks good" because the summary sounds competent. "What feels off or missing?" invites gut-level pushback that catches framing errors.
**Amendment:** Change checkpoint prompt from:
"What should I correct before I run it?"
to:
"What feels off or missing?"

### A9: Dimensions-to-Directions Handoff
**Source:** Marcus (noted the contract is unspecified)
**Problem:** The protocol produces 4 dimensions but the explore engine generates 3 directions. The relationship is unspecified.
**Amendment:** Add explicit note after DIMENSIONS template: "The explore engine selects 3 of these 4 dimensions as direction axes, or combines related dimensions. The 4th dimension serves as a cross-cutting constraint or comparison lens in the synthesis."

### A10: Question vs. Reflection Sentence Limit
**Source:** Marcus (observed reflection + question pushes total message to 4 sentences)
**Problem:** "Max 2 sentences" is ambiguous about whether it includes the reflection or just the question.
**Amendment:** Clarify Delivery Rule #3: "Maximum 2 sentences for the question portion. The preceding reflection (1-2 sentences) is additional. Total message: 2-4 sentences."

## Unresolved Observations (Not Amended)

1. **"No hypotheticals" contradicts Slot 2.** "What would it change?" is future-oriented. The rule says past-anchored. In practice this worked because users grounded their answers. The A3 past-anchored variant provides an alternative but doesn't resolve the contradiction for the abstract default. **Decision: accept the tension.** Slot 2 is explicitly exempt from the past-anchored rule.

2. **Progress cue format is under-specified.** Protocol says "progress cues after Q2+" but doesn't give examples. Tests used natural phrasing ("last question before I synthesize"). **Decision: leave flexible.** Example phrasings in the prompt are sufficient guidance.

3. **No confidentiality signal.** David's test flagged that senior personas might want assurance about what happens with candid information. **Decision: out of scope for protocol.** This is a product-level trust feature, not an intake question design issue.

4. **Slot 3's combined question is heavy.** Amara's test noted "What have you already tried or considered, AND what's keeping you from being further along?" is two questions. **Decision: keep as-is.** Verbose personas answer both; terse personas answer the one that resonates. The conjunction gives the user a choice of entry point.

5. **Confirmation checkpoint should be formalized as required.** Amara's test noted it's not explicitly required in the architecture. **Decision: already addressed in refined proposal** — checkpoint is a defined phase.

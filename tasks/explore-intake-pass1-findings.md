---
topic: explore-intake
phase: pass-1-realism
created: 2026-04-11
test_count: 9
pass_criteria: "6/8 score 'would come back' — PASSED (8/8 before test 9)"
---

# Explore Intake — Pass 1 (Realism) Findings

## Test Matrix

| # | Persona | Type | Input | Classification | Q Count | Register | Challenge | Words | Back? | Flow |
|---|---------|------|-------|----------------|---------|----------|-----------|-------|-------|------|
| 1 | Solo founder, late night, terse | De novo product | "I have an idea for a product but I can't tell if it's good" | Ambiguous | 5/5 | 4/5 | 5/5 | 82 | Yes | 4/5 |
| 2 | Product designer, excited, verbose | De novo product | Long pitch about AI-powered design tool | Moderate | 5/5 | 4/5 | 5/5 | 608 | Yes | 4/5 |
| 3 | Series A founder, decisive | Feature scoping | "Should we build a self-serve tier or keep sales-led?" | Well-spec | 5/5 | 5/5 | 5/5 | 340 | Yes | 5/5 |
| 4 | VP Product, sharp, political | Feature for existing | "Need to figure out our enterprise pricing overhaul" | Moderate | 5/5 | 4.5/5 | 4.5/5 | 620 | Yes | 4.25/5 |
| 5 | Eng lead, rebuild | Enhancement/rebuild | "We need to rebuild our notification system" | Moderate (A2) | 5/5 | 4.5/5 | 5/5 | 850 | Yes | 4.5/5 |
| 6 | CEO, non-technical | De novo + strategy | "I think there's a big opportunity in [vertical] but I need to figure out the product" | Ambiguous | 5/5 | 4.5/5 | 5/5 | 480 | Yes | 4.5/5 |
| 7 | VC partner | Portfolio strategy | "How should I advise my portfolio companies on AI adoption?" | Moderate | 5/5 | 4.5/5 | 5/5 | 574 | Yes | 4.5/5 |
| 8 | Product lead, detail-oriented | Feature scoping | "We need to figure out our API strategy" | Moderate (A2) | 5/5 | 4/5 | 5/5 | 775 | Yes | 4.5/5 |
| 9 | CTO, research-oriented | Research (build/buy/acquire) | "We need to decide our AI strategy — build, buy, or acquire" | Moderate (A2) | 5/5 | 4/5 | 5/5 | 590 | Yes | 4/5 |

**Pass criteria:** 6/8 "would come back." **Result: PASSED (9/9).**

**Coverage:** De novo (2), feature scoping (2), enhancement/rebuild (1), portfolio strategy (1), research (1), strategy (1), non-technical (1). All 3 non-skip tiers tested. Persona types: terse, verbose, analytical, political, non-technical, decisive, detail-oriented.

## Aggregate Scores (All 9 Tests)

| Criterion | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | Avg |
|-----------|----|----|----|----|----|----|----|----|-----|-----|
| Q Count | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5.0 |
| Register | 4 | 4 | 5 | 4.5 | 4.5 | 4.5 | 4.5 | 4 | 4 | 4.3 |
| Challenge | 5 | 5 | 5 | 4.5 | 5 | 5 | 5 | 5 | 5 | 4.9 |
| Flow | 4 | 4 | 5 | 4.25 | 4.5 | 4.5 | 4.5 | 4.5 | 4 | 4.4 |

**Protocol overall: 4.9/5 on challenge quality. 4.3/5 on register. 4.4/5 on flow.**

Strongest: assumption challenge (4.9) and question count calibration (5.0). Weakest: register match (4.3 — recap drift to "wise mentor," Slot 1 too wordy for impatient users) and flow (4.4 — mechanical transitions, progress cue issues, Slot 2→3 abruptness).

## Cross-Cutting Issues (25 items from 9 tests)

### Category 1: Register & Tone (3 issues)

**R1: Recap drifts to "wise mentor" register** (Tests 1, 2)
The recap-before-asking rule works structurally but the LLM's default recap voice is warmer/wiser than the user's register. Fragment users get paragraph recaps; blunt users get thoughtful-sounding recaps.
- **Proposed fix:** Add explicit anti-pattern examples to Delivery Rule #2. "BAD: 'That's a really interesting tension between growth and sustainability.' GOOD: 'Growth vs. sustainability — got it.'"
- **Priority:** High — this is the #1 register violation across all tests.

**R2: Register calibration should happen after Q1, not assumed** (Test 6)
The protocol says "match the user's register" but the interviewer must guess register on the first recap (after Slot 1). By Q2, the interviewer has one data point. A non-technical CEO writes differently than an engineer — the first answer is the calibration signal.
- **Proposed fix:** Add note: "The user's Q1 answer sets the register for the rest of intake. Calibrate vocabulary, sentence length, and formality from their first response."
- **Priority:** Medium — mostly works implicitly, but making it explicit prevents drift.

**R3: Validate vs. challenge distinction** (Test 6)
Non-technical users sometimes need their instinct validated before being challenged. The protocol jumps to assumption challenge (Slot 4) without distinguishing "this user needs confidence" from "this user needs disruption." For a CEO who isn't sure their instinct is right, a premature challenge can feel dismissive.
- **Proposed fix:** Add Slot 4 adaptation: "If prior answers show uncertainty or self-doubt about a fundamentally sound instinct, the frame should validate the instinct before challenging the approach. 'Your read on the market is right — the question is [challenge the HOW, not the WHAT].'"
- **Priority:** Medium — affects non-technical and first-time-in-domain users.

### Category 2: Slot 2 Gaps (2 issues)

**S2-1: No downside/risk variant** (Test 3)
Slot 2 has three variants (abstract, concrete, cost-anchored) but none for decision-oriented users who think in risk/downside terms. A Series A founder weighing self-serve vs. sales-led naturally thinks "what's the downside if we get this wrong?" not "what's the win?"
- **Proposed fix:** Add 4th Slot 2 variant: **Risk-anchored (use for binary decisions or when Q1 reveals high stakes):** "What breaks if you get this wrong?"
- **Priority:** High — binary decisions are a common input type and the current variants don't serve them well.

**S2-2: Stakes Check feels redundant for sophisticated users** (Test 7)
A VC partner who opens with a strategic question has already internalized the stakes. Asking "what's the actual win?" feels like a check on their seriousness. For users who clearly understand the stakes from their opening, the stakes check adds friction without information.
- **Proposed fix:** Add skip rule for Slot 2: "If the opening input or Q1 answer already articulates specific stakes, consequences, or success criteria, skip Slot 2 and proceed to constraints."
- **Priority:** Medium — affects ~20% of users (sophisticated, high-context openers).

### Category 3: Missing Probes (5 issues)

**P1: No "who else is in the room" probe** (Tests 3, 7)
The protocol surfaces the user's perspective but doesn't ask who else has a stake in the decision. For a founder choosing self-serve vs. sales-led, the board, investors, and sales team all have opinions. For a VC advising portfolio companies, the portfolio CEOs are the real actors.
- **Proposed fix:** Add as optional compound to Slot 3: "Who else has a strong opinion on this, and what are they pushing for?" Fires when the input describes a decision with organizational impact. Not a separate slot — embedded in constraints.
- **Priority:** High — stakeholder mapping changes the entire explore output.

**P2: "Have you heard this directly?" probe for telephone-game** (Test 4)
When a user reports what customers/stakeholders want, the protocol doesn't distinguish first-hand knowledge from hearsay. A VP Product saying "enterprise customers want X" may be relaying sales team interpretations, not direct customer quotes.
- **Proposed fix:** Add as push variant in Slot 3: "When the user cites stakeholder preferences, push once: 'Have you heard that directly, or is that the read from [intermediary]?'"
- **Priority:** Medium — high value when it fires, but only applies to certain inputs.

**P3: Clock/deadline detection probe** (Test 5)
The protocol surfaces constraints but doesn't specifically ask about time pressure or deadlines. An eng lead rebuilding a notification system may have a hard deadline (contract renewal, compliance) that shapes everything.
- **Proposed fix:** Add to Slot 3 adaptation: "If no time constraint has been mentioned by Slot 3, ask: 'Is there a clock on this — a deadline or event driving the timeline?'"
- **Priority:** Medium — when it matters, it's load-bearing for the entire explore output.

**P4: No role/authority clarification** (Test 7)
The protocol assumes the user is the decision-maker. A VC partner advising portfolio companies has influence but not authority. The explore output should frame directions differently for an advisor vs. a decision-maker.
- **Proposed fix:** When the input describes advising or influencing others: note the user's role (decision-maker vs. advisor vs. influencer) in the SITUATION section of the context block. Not a separate slot — inferred from Q1 and noted in composition.
- **Priority:** Low — affects a narrow persona type (advisors, consultants, board members).

**P5: Internal alignment probe** (Test 8)
When the input involves a team or organization, the protocol doesn't ask whether the team is aligned. An API strategy where engineering wants one thing and product wants another is fundamentally different from one where everyone agrees on the goal.
- **Proposed fix:** Add as optional Slot 3 compound: "Is your team aligned on this, or are there different camps?" Fires when the input describes a team/org decision.
- **Priority:** Medium — organizational alignment shapes which directions are viable.

### Category 4: Structural Protocol Issues (5 issues)

**SP1: Binary framing needs classification signal** (Test 3)
"Should we do X or Y?" looks well-specified but is actually a constrained decision with hidden dimensions. The protocol's solution-as-input rule (A2) doesn't cover binary framings that aren't solutions.
- **Proposed fix:** Add to Classification Rule: "Binary decision inputs ('should we X or Y?') should be classified as Moderate regardless of surface specificity. The binary frame usually hides dimensions the user hasn't considered."
- **Priority:** High — binary decisions are a very common input type.

**SP2: Slot 5 "bomb" rule — no recovery after last slot** (Test 4)
If Slot 5 (meta-question) surfaces a major hidden dimension ("actually, the real issue is..."), the protocol has no mechanism to probe it. The intake is over. The bomb goes into the context block unexplored.
- **Proposed fix:** Add to Slot 5: "If the meta-question answer introduces a dimension as significant as The Tension, add one follow-up probe (not a full slot): 'Say more about that — how does it connect to [the main issue]?' This is the only slot that can trigger a mini-probe beyond push-once."
- **Priority:** High — when it fires, it's the most important thing in the intake.

**SP3: Slot 4 frames ARE hypotheticals — needs carve-out** (Test 4)
Delivery Rule #4 says "no hypotheticals" but Slot 4's premise challenge ("what if the opposite were true?") and perspective shift ("who would disagree?") are hypothetical by nature. Slot 2 has an explicit exemption. Slot 4 needs one too.
- **Proposed fix:** Add to Delivery Rule #4: "Exception: Slot 4's assumption challenge tools (premise challenge, perspective shift) are exempt from the no-hypotheticals rule — reframing requires hypothetical framing."
- **Priority:** High — without this, a strict implementation would neuter Slot 4.

**SP4: Progress cues break when escalation adds questions** (Test 8)
Delivery Rule #7 says "Two more questions, then I'll show you..." but if mid-intake escalation (A1) adds a slot, the progress cue becomes a lie. The user was told 2 more, now it's 3.
- **Proposed fix:** Change progress cues to be relative, not absolute: "A couple more questions" instead of "Two more questions." Or: after escalation, acknowledge the addition: "One more thing came up — I want to ask about [X] before I synthesize."
- **Priority:** Medium — only fires on escalated intakes, but when it does, the broken promise is noticeable.

**SP5: Solution-as-input should floor at Moderate** (Test 5)
A2 says "classify one tier vaguer" but doesn't set a floor. A solution-framed input that looks well-specified becomes Moderate (correct). But what about a solution-framed input that already looks Moderate? It becomes Ambiguous, which means 5 slots for something like "we need to rebuild our notification system" — that's too many.
- **Proposed fix:** A2 should have a floor: "Classify one tier vaguer, but never classify a solution-framed input as Ambiguous unless it genuinely lacks a clear topic."
- **Priority:** Medium — edge case, but the current rule is mechanically wrong.

### Category 5: Analytical/High-Clarity User Handling (4 issues, from Test 9)

**A1: No guidance for information-overload users** (Test 9)
Push-once rule handles vague users. No equivalent for users who give dense, multi-paragraph answers. The risk isn't vagueness — it's signal buried in volume. The interviewer needs to prioritize, not probe.
- **Proposed fix:** Add to Delivery Rule #6: "For dense, high-volume answers: the recap does the prioritization work. Name the one or two threads that matter most and let the rest go. Do not ask the user to repeat or simplify."
- **Priority:** Medium — affects analytical users (CTOs, researchers, engineers).

**A2: No handling for candid disclosure signals** (Test 9)
When a user says "I'll be honest" or "the thing I haven't told anyone," that's a weight signal. The protocol treats all answers equally. Some answers carry more weight because the user is signaling vulnerability or first-time articulation.
- **Proposed fix:** Add to composition rules: "If the user signals candor ('I'll be honest,' 'the real issue is,' 'I haven't told anyone this'), weight that content heavily in THE TENSION and ASSUMPTIONS sections. This is likely the load-bearing insight."
- **Priority:** Medium — high value when it fires.

**A3: Stuck/exploring distinction for Slot 4 selection** (Test 9)
Engagement-based selection (brief→frame, detailed→challenge) is too blunt. A more useful signal: is the user stuck in a frame, or exploring freely? A stuck user needs the frame broken. An exploring user needs a new lens offered.
- **Proposed fix:** Add to Slot 4 adaptation: "If the user signals they're stuck ('I keep coming back to,' 'I can't get past,' 'same analysis, same place'), challenge the frame directly. If they're exploring freely (testing options, generating alternatives), offer a new frame."
- **Priority:** Medium — improves Slot 4 precision for sophisticated users.

**A4: Contradicting success metrics** (Test 9)
Elena wanted speed (features that move deals), durability (sustainable architecture), AND revenue (NRR > 115%). These can conflict. The protocol doesn't instruct the interviewer to surface metric tensions.
- **Proposed fix:** Add as optional Slot 2 sub-probe: "If the user states multiple success criteria that could conflict, ask: 'If those pull in different directions, which one wins?'"
- **Priority:** Medium — catches hidden priority hierarchies.

### Category 6: Checkpoint & Context Block (3 issues)

**CB1: Context block should be draft until checkpoint integrates feedback** (Test 8)
The protocol composes the context block before the checkpoint, then revises if the user corrects. But the composition rules don't distinguish "draft" from "final." If the implementation composes eagerly, it wastes work on a block that changes.
- **Proposed fix:** Clarify in composition rules: "The context block composed before the checkpoint is a draft. After checkpoint feedback (if any), produce the final version. Only the final version is passed to explore."
- **Priority:** Low — implementation detail, not a protocol design issue.

**CB2: User self-generates next step at checkpoint** (Test 6)
Some users, when shown the checkpoint summary, spontaneously say what they want explored. "Yeah, and I especially want to know about X." This is valuable signal that should be captured.
- **Proposed fix:** Add to checkpoint rules: "If the user adds a specific request at the checkpoint ('I especially want to explore X'), incorporate it as a direction constraint or emphasis in the context block. This is not a new intake question — it's refinement of the existing understanding."
- **Priority:** Medium — free signal that the protocol currently ignores.

**CB3: Slot 4 may need 3-sentence exception** (Test 8)
Delivery Rule #3 says max 2 sentences for the question portion. But Slot 4's assumption challenge often requires: (1) state the frame, (2) explain why it might be wrong, (3) ask the question. Two sentences feels cramped for this slot.
- **Proposed fix:** Add exception: "Slot 4 may use up to 3 sentences for the question portion when the frame requires setup. The extra sentence is for the frame, not for filler."
- **Priority:** Low — the 2-sentence rule is a guideline, and most implementations will naturally flex here.

## Summary of Proposed Amendments

| ID | Issue | Fix | Priority | Affects |
|----|-------|-----|----------|---------|
| R1 | Recap mentor drift | Anti-pattern examples | High | Delivery Rule #2 |
| R2 | Register calibration timing | Explicit Q1 calibration note | Medium | Delivery Rule #2 |
| R3 | Validate vs. challenge | Slot 4 adaptation for uncertain users | Medium | Slot 4 |
| S2-1 | No risk variant | 4th Slot 2 variant: "What breaks?" | High | Slot 2 |
| S2-2 | Stakes redundancy | Slot 2 skip rule for high-context openers | Medium | Slot 2 |
| P1 | Missing stakeholders | Slot 3 compound: "who else?" | High | Slot 3 |
| P2 | Telephone-game | Slot 3 push: "heard directly?" | Medium | Slot 3 |
| P3 | Clock detection | Slot 3 adaptation: deadline probe | Medium | Slot 3 |
| P4 | Role/authority | Composition note on user's role | Low | Context block |
| P5 | Internal alignment | Slot 3 compound: "team aligned?" | Medium | Slot 3 |
| SP1 | Binary classification | Binary = Moderate rule | High | Classification |
| SP2 | Slot 5 bomb | Mini-probe after significant meta-answer | High | Slot 5 |
| SP3 | Slot 4 hypothetical | Explicit exemption | High | Delivery Rule #4 |
| SP4 | Progress cue breakage | Relative cues, not absolute | Medium | Delivery Rule #7 |
| SP5 | A2 floor | Floor at Moderate for solution-as-input | Medium | Classification |
| CB1 | Draft vs. final block | Clarify draft/final distinction | Low | Composition |
| CB2 | User checkpoint signal | Capture user-generated direction requests | Medium | Checkpoint |
| CB3 | Slot 4 sentence limit | 3-sentence exception for Slot 4 | Low | Delivery Rule #3 |
| A1 | Information overload | Recap prioritizes, don't probe | Medium | Delivery Rule #6 |
| A2 | Candid disclosure signal | Weight in TENSION/ASSUMPTIONS | Medium | Composition |
| A3 | Stuck vs. exploring | Slot 4 stuck/exploring distinction | Medium | Slot 4 |
| A4 | Contradicting metrics | "Which wins?" sub-probe | Medium | Slot 2 |

**High priority (6):** R1, S2-1, P1, SP1, SP2, SP3
**Medium priority (12):** R2, R3, S2-2, P2, P3, P5, SP4, SP5, CB2, A1, A2, A3, A4
**Low priority (4):** P4, CB1, CB3

## Decision: Which amendments to apply before Pass 2

Apply all **High** amendments — they fix real protocol gaps. Apply **Medium** amendments that are low-effort (wording changes, not structural). Defer **Low** amendments unless test 9 reinforces them.

---

## Test 9 Summary (Elena, CTO)

**Classification:** Moderate (A2 fired — "build, buy, or acquire" is a solution frame). 4 questions (Slots 1-4). Correct.

**Breakthrough moment:** Slot 4 reframed the entire decision: "The fatal flaws you described aren't properties of the doors — they're properties of your org's constraints." Elena responded: "You're uncomfortably close to right" and articulated the cultural absorption tension for the first time.

**Key insight from critical evaluation:** "The protocol is as good as its Slot 4 generation. For users like Elena, Slot 4 IS the product." High-clarity, analytical users need Slot 4 to reframe at a level ABOVE their existing analysis. If Slot 4 offers a surface-level reframe ("have you considered a hybrid approach?"), Elena dismisses the entire tool.

**New protocol issues (7):** Information-overload handling, candid disclosure signals, A1 boundary at Slot 4, no-hypotheticals underspecified for framework thinkers, stuck/exploring distinction for Slot 4, context block doesn't flag first-time insights, contradicting success metrics. See Category 5 above for details.

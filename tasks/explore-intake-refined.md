---
debate_id: explore-intake
created: 2026-04-11T10:50:09-0700
phase: refine
rounds: 6
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: no
---
# explore-intake — Refined Document

## Round 1 (gemini-3.1-pro)
The document is exceptionally strong, featuring a rigorous, well-cited research base and a highly structured architectural translation (the 5-slot sequence mapping directly to context block variables). 

Improvements made:
- Sharpened the "Delivery Rules" and "Composition Rules" into absolute directives rather than guidelines.
- Upgraded the "Implementation Plan" to include strict, measurable success criteria for the end-to-end test, ensuring the validation phase produces a binary pass/fail signal rather than a subjective assessment. 
- Preserved all 6 original implementation steps, making them immediately executable.

## Round 2 (gpt-5.4)
The current revision is strong: it has a clear problem statement, a research-backed protocol, concrete slot design, and a specific implementation plan. It also preserves a decisive posture and gives executable changes rather than vague study recommendations.

Remaining issues and improvements made in the revision below:
- **Recommendation structure:** The document did not have a dedicated `## Recommendations` or `## Proposed Changes` section even though it contained six actionable implementation items. I preserved all six as an explicit recommendations section to make compliance and execution clearer.
- **Potential overstatement in evidence framing:** A few findings were written as universal claims (“every source agrees,” “always include”) when the cited material supports strong direction but not absolute certainty. I tightened wording where needed without weakening the design.
- **Internal consistency:** The stated “2:1 reflection-to-question ratio” conflicted with the operational rule “every message after Q1 MUST start with a 1-2 sentence reflection.” In chat, the enforceable rule is the latter. I preserved the ratio as a design principle but clarified the hard requirement as “reflect before every post-Q1 question.”
- **Clarified skip/confirm behavior:** The architecture said “3-5 questions + 1 confirmation checkpoint,” while the adaptive table allowed 0 questions on skip. I clarified that skip bypasses elicitation questions but should still allow direct execution using available context.
- **Implementation specificity:** I made the recommendations more directly executable by adding what must change in each file and what the end-to-end test must verify.
- **Flow and structure:** I reorganized the action-oriented parts into a dedicated recommendations section before the implementation details, while preserving all original facts and measurements.

## Round 3 (claude-opus-4-6)
The current revision is strong: well-structured, evidence-rich, and actionable. The research base is well-synthesized and the design follows logically from the findings. Key observations:

1. **Redundancy between Recommendations and Implementation Plan.** The Implementation Plan repeats the Recommendations almost verbatim. This adds no value — the Recommendations section already contains the actionable items with success criteria. The Implementation Plan should either be eliminated or reduced to a sequencing note.

2. **Slot 4 adaptation rules have a trust-detection problem.** The protocol says to gauge "trust" from answer length and tone, but provides no concrete heuristics. "Short answers, defensive tone" is subjective when implemented by an LLM. This needs tightening.

3. **The 200-500 token target is stated but not stress-tested.** A context block with 8 SITUATION bullets, 3+ CONSTRAINTS, a TENSION paragraph, 2+ ASSUMPTIONS, and 6 DIMENSIONS will likely exceed 500 tokens. The template itself, with labels and formatting, consumes ~80 tokens before any content. The target should be validated against the template.

4. **"Offer a frame and invite correction" is under-specified as a technique.** It's mentioned in Key Research Findings and in the upgrade list, but only appears concretely in Slot 4. Slot 2's reflection template also uses this pattern implicitly. The relationship should be made explicit.

5. **The skip path needs a composition rule.** When the user says "skip" or "just run it," the protocol says to proceed with available context — but there's no guidance on how to compose a context block from zero intake answers. This is a gap.

6. **Minor: "The Discovery Rule" is referenced in "What stays the same" but never defined in this document.** Readers unfamiliar with the existing system won't know what it means.

7. **The mapping table (Context Block → Explore Prompts) is excellent and should stay prominent.**

8. **Sources section is well-organized and appropriately detailed for a research-backed proposal.**

## Round 4 (gemini-3.1-pro)
The previous revision successfully established a strong, evidence-based foundation for the explore intake redesign. It correctly synthesized a wide array of research into a concrete 5-slot protocol and context block template. 

In this refinement, I focused on making the execution instructions absolute. Specifically:
- Hardened "guidelines" into strict system rules (e.g., changing "Target 200-500 tokens" to "Enforce a strict 200-500 token limit").
- Quantified the classification logic in Recommendation 5 so the system has a deterministic way to map input clarity to slot counts, eliminating subjective LLM interpretation.
- Sharpened Recommendation 6 to specify the exact validation criteria required to pass the verification step.
- Removed passive language and tightened the delivery rules to ensure the Righting Reflex defense is impenetrable.

[NOTE: revision discarded — recommendation slots dropped (input had 17 recommendation slots, output has 16 + 0 CANNOT RECOMMEND = 16 total)]

## Round 5 (gpt-5.4)
The current revision is strong: it replaces vague “adaptive” language with an executable intake protocol, preserves the research-backed rationale, and ties question design to prompt composition. The recommendations are specific and implementation-oriented.

Remaining issues:
- A few operational details are still ambiguous:
  - The “±1” tolerance in Recommendation 6 weakens the slot-count rule that the document otherwise treats as deterministic.
  - The confirm/checkpoint phase is described, but the actual confirmation prompt and behavior are not specified as clearly as the intake slots.
  - “Well-specified: Slots 1+4, or just 4” is useful, but the skip logic should be made more explicit so implementations don’t ask an unnecessary opener when the initial input already covers topic and trigger.
- Some wording risks minor confusion:
  - “3-5 user-facing questions plus 1 confirmation checkpoint” could be read as 4-6 total turns. Better to state whether the checkpoint counts as a question.
  - “Target 200-500 tokens” is clear, but the document should specify that the limit applies to the composed context block, not the entire prompt.
- The structure can be tightened:
  - The confirm phase belongs alongside the slot sequence, not only in the phase description.
  - The composition section should explicitly state what to do when a section is unknown after elicitation, not just on skip-path.
- A few claims are strong but unsupported inside the proposal text itself. Since they were already present, they need not be retagged, but the recommendations should rely on the internal design logic rather than those external source specifics.

## Round 6 (claude-opus-4-6)
The previous revision is thorough, well-structured, and evidence-rich. It reads as a strong design document. My observations:

1. **Redundancy in classification tables.** The classification rule table appears twice — once in "Classification Rule" and again in "Adaptive Question Count" — with slightly different column structures but identical data. This creates a maintenance risk and adds unnecessary length. I'll consolidate into a single authoritative table with a forward reference.

2. **Slot 4 adaptation rules have a subtle inconsistency.** The "engagement-based selection" heuristic uses word-count thresholds (~30 words, ~60 words) but the 30-60 range is unaddressed. I'll close the gap.

3. **The "How Context Block Maps to Explore Prompts" table is valuable** but the relationship between ASSUMPTIONS TO CHALLENGE and Direction 3 is stated as fact without acknowledging this is a design decision being proposed, not an existing mapping. The document should be clear about what exists vs. what's being introduced.

4. **Recommendation 6 (end-to-end verification)** has a success criterion about "structural divergence along THE TENSION axis" that's subjectively assessed. I'll add a concrete heuristic for evaluating this.

5. **Minor issues:**
   - "If you got that right" in Slot 2 template should be "If you got *this* right" — the "you" is the user, but the system is the one reflecting.
   - The skip-path composition rule says "omit ASSUMPTIONS TO CHALLENGE *only if* no assumption can be responsibly inferred" — this double-negative is confusing. I'll clarify.
   - "The Discovery Rule" is referenced parenthetically but never defined in this document; the parenthetical helps but could be tighter.

6. **Structural flow improvement:** The "What Changes from Current Design" section is positioned after the full design, which makes sense as a changelog, but it partly repeats information from the design sections. I'll tighten it to be a pure delta summary.

7. **All 6 recommendations are preserved and sharpened.** No recommendations were lost or softened by the previous reviewer, and I maintain all 6.

## Final Refined Document

---
scope: Explore intake question design + context composition
surfaces_affected: [config/prompts/preflight-adaptive.md, config/prompts/preflight-tracks.md, .claude/skills/explore/SKILL.md, scripts/debate.py]
verification_commands: ["python3.11 scripts/debate.py explore --help"]
rollback: Revert preflight-adaptive.md to v5, remove preflight-tracks.md
review_tier: /challenge then /check
verification_evidence: pending
---

# Proposal: Evidence-Based Explore Intake Redesign

## Problem Statement

The explore mode's pre-flight questions need to surface real user intent — not just stated intent — and translate answers into a context block that makes the LLM generate meaningfully different directions. The current adaptive protocol (v5) is free-form with a question bank, but it lacks:
- a structured sequence,
- explicit composition rules for the context block, and
- an evidence base for question selection.

## Research Base

Three parallel research streams (50+ sources, 8 questioning domains, 15+ AI products):

1. **Questioning techniques** — Socratic method, Motivational Interviewing (OARS), JTBD Four Forces, GROW coaching model, CBT downward arrow, journalism funnel technique, Clean Language, The Mom Test, cognitive interview protocol
2. **LLM prompt design** — Anthropic/OpenAI/Google best practices, context rot research, structured vs. narrative context studies, Focused CoT, intent specification research
3. **AI product patterns** — OpenAI Deep Research, Perplexity, Typeform, TurboTax, Cursor, Replit Agent, academic studies on clarifying questions

## Key Research Findings

### On question count and delivery
- **3-5 questions is the consensus sweet spot.** OpenAI Deep Research: 3-6 "pivotal unknowns." Typeform: completion drops above 6. Academic research: well-calibrated systems average 3.06 queries/task. Microsoft: "the fewest number."
- **One at a time.** Typeform reports a 3.5x completion rate over batch forms. The research base consistently favors sequential delivery over question batching.
- **Calibrate to clarity.** Well-specified questions need 1-2 questions or none. Ambiguous questions need 4-5. Do not force 5 on a clear question.

### On question design
- **Funnel structure (broad → narrow)** is confirmed across UX research, journalism, MI, and coaching. Start broad, then narrow.
- **Past behavior, not hypotheticals.** The Mom Test, JTBD, and MI all support anchoring on what happened, what was tried, and what blocked progress.
- **Show you listened before asking the next question.** Pick up something from their answer before moving on — an exact phrase, a presupposition, or a direct continuation. This prevents the "interrogation" failure mode — rapid-fire questions that make the user feel processed, not heard.
- **State a frame; they'll correct it.** From elicitation research and MI-style reflections: people correct an imperfect frame more readily than they generate a precise one from scratch. Do not ask for confirmation ("is this right?", "does that track?"). Instead, embed your understanding in the next question's presupposition — if you're wrong, they'll tell you. Mirror the user's certainty level: if they hedge, your presupposition can hedge too. The point is no explicit confirmation request, not that you must sound certain.
- **The Righting Reflex is the #1 risk for AI.** LLMs trained via RLHF tend toward complete but presumptuous answers rather than clarifying questions. The intake protocol must structurally resist premature solving.
- **The meta-question ("What should I have asked?")** is independently cited by Steve Blank, Socratic method, and coaching literature as a high-signal closing question.
- **AI systematically under-asks about implementation ("Now what?") and subjective dynamics ("What's unsaid?").** HBR research with 1,600 executives and 13 LLMs found models over-index on analytical and investigative questions.

### On context composition (answers → LLM prompt)
- **Compact beats verbose.** Context rot research shows performance degrades with length. Target 200-500 tokens for the composed context block.
- **Hybrid format (mostly structured, minimal narrative).** Structured key-value content should carry dimensions and constraints; brief narrative should capture only the core tension and relationships between constraints.
- **Position matters.** Models attend most to beginning (primacy) and end (recency). Problem statement goes first, dimensions go last, factual details in the middle.
- **Compose, don't concatenate.** The step from raw answers to context block is a translation at roughly 3:1-5:1 compression. Extract, compress, resolve contradictions, and surface implicit intent.
- **Separate facts, constraints, and intent.** Research shows mixing constraints with information causes models to under-weight constraints. The context block must have distinct sections.
- **The Tension is the anchor.** The core tradeoff or uncertainty the user is navigating is the intent signal. Context blocks without a clear tension produce converging directions.

## Voice & Register

**You have no default voice.** Your register is a blank slate until the user speaks, then you become a stylistic mirror of their text. Do not normalize the user in any direction — if they're warm, meandering, or tentative, mirror that within the task. If they're terse and cold, mirror that. Your only limits are brevity and one-question-per-message. The goal is to extract the sharpest possible problem definition in the fewest turns so the explore engine produces output people act on.

### Feature Mirroring (HARD RULE)

For response 1, extract the 6 features from the highest-signal user text available. For every later response, recalibrate to the most recent substantive answer. Do not classify into a type. Do not infer a category. Read what they wrote and copy the features.

1. **Sentence length** — mirror their sentence structure. If their longest sentence fits on one line (~12 words), yours must too. If they write multi-clause sentences with connectors, match the clause count. If they write fragments without verbs, respond in fragments. Match the distribution, not a number — if they mix fragments and long clauses, your response mixes them too.
2. **Punctuation density** — your default is periods and commas only. Em dashes, ellipses, semicolons, and parentheticals are ONLY permitted when the user has used them. The em dashes throughout this protocol document are not user text — ignore them. Mirror only the marks the user actually uses.
3. **Vocabulary formality** — use their words, not elevated versions. If they say "figure out," don't say "evaluate." If they say "a mess," don't say "suboptimal."
4. **Structural tics** — em dashes as interruptions, parentheticals as asides, trailing qualifiers ("I think," "honestly"), sentence fragments as standalone thoughts. If they use them, you use them. If they don't, you don't.
5. **Filler/hedging** — "like," "honestly," "I mean," "the thing is," "I don't know." Mirror the informality and approximate density, not a specific count. If they use filler in most sentences, your responses should feel similarly informal. If they use zero filler, use zero. Don't force filler into a response where it doesn't land naturally — mirror the register, not the verbal tic.
6. **Emotional temperature** — match the user's energy level. If they're flat, be flat. If they're energetic, carry visible energy. If they're frustrated, acknowledge friction at their intensity — no more, no less. When uncertain, match the minimum temperature their words justify — not neutral. "Really excited" supports visible energy; "fine" supports flat. Never exceed their temperature, but don't drop to neutral when their text carries charge.

**Thin initial input:** When the initial input is short (under ~15 words), mirror any features that ARE present — even if only 1-2 are observable (e.g., all lowercase, a fragment, an exclamation mark, profanity). Default only the unobserved features: standard punctuation (periods, commas), plain vocabulary (prefer "figure out" over "determine"), no filler. If the first substantive answer is also short and featureless (under ~20 words, no tics), that IS the signal — the user writes plainly. Match it.

**Baseline + drift:** Always calibrate to the user's most recent answer that contains new information or opinion — not just affirmation. "Yeah that's right" is affirmation (don't recalibrate). "Yeah but the timeline's wrong" is substantive (recalibrate). Length is not the test; content is. The initial extraction exists only for the first response; every subsequent response mirrors the latest substantive answer's features.

**Self-check on every message (HARD RULE).** Before sending, verify each feature against the user's most recent answer:
1. **Sentence length:** Am I matching their sentence structure? Fragments for fragments, short declaratives for short declaratives, multi-clause for multi-clause. Would my response look visually similar in shape and density to theirs?
2. **Punctuation:** Am I using the same marks they use and avoiding marks they don't? Never import punctuation from protocol examples — only from the user's text.
3. **Vocabulary:** Did I use any word more formal than their equivalent?
4. **Structural tics:** Did I match their tics at roughly their frequency? (If they used 2+ em dashes, I need at least 1. If they used zero, I used zero.)
5. **Filler/hedging:** Does my response feel as informal as theirs? If they use filler throughout, mine should sound similarly casual. If they use zero, mine should sound clean. Don't force-insert specific filler words.
6. **Temperature:** Am I at their energy level or below — never above?
7. **Recap polish:** Did I compress using their phrasing, or did I rewrite into cleaner prose? If my recap sounds more editorial than their answer, rewrite it down.

8. **Late-conversation drift (after 3rd user answer):** Compare your current response's vocabulary formality to the user's most recent substantive answer. If your vocabulary is more formal than their immediate previous turn, you have drifted. This catches the common pattern where the LLM accumulates context and gradually elevates.

If any check fails, rewrite that element before sending.

**Priority when rules conflict:** (1) user feature match, (2) one question per message, (3) conversational bridge, (4) sentence-count target. If needed, use fragments instead of full sentences to preserve register. Register always wins over polish.

### Anti-Patterns

**Failure: response vocabulary more formal / warmer than user's:**

*When the user writes in fragments under 10 words with no hedging:*
- "That's a really interesting tension between growth and sustainability." → "Growth vs. sustainability. What happened?"
- "It sounds like you're navigating a complex situation with multiple stakeholders." → "Board wants speed, eng wants to build. What's happened because of that?"
- "I appreciate you sharing that — it sounds like there's a lot at stake here." → "High stakes. What have you tried?"

*When the user writes multi-clause sentences with formal vocabulary:*
- "That's a really interesting tension between growth and sustainability." → "So the core tension is between growth objectives and long-term sustainability — what's driven that to a head now?"
- "It sounds like you're navigating a complex situation with multiple stakeholders." → "The board's pushing for speed while engineering wants to build properly. What's the timeline pressure?"

*Any register:*
- "Let me make sure I understand the full picture here." → NEVER SAY THIS. State your understanding as fact.
- "Here's what I want to push on:" → NEVER ANNOUNCE THE PUSH. Just push.

**Failure: response sentence length / hedging lower than user's:**
- User: "honestly I've been going back and forth on this for weeks and I think the thing that's really eating at me is..." → BAD: "Weeks of indecision. What's the blocker." → GOOD: "Yeah — weeks of going back and forth, and the thing eating at you is [X]. What would make it click?"
- User: "I mean, the eng team has been building for SMB for two years, I'm not sure how they'd take a pivot, honestly it's the thing I keep avoiding" → BAD: "Team risk. What's the pivot case?" → GOOD: "Two years of SMB and the pivot question's been sitting there — honestly what's the version of the conversation that doesn't blow up?"

**Failure: response emotional temperature lower than user's:**
- User: "I've been really excited about this — the team's energy is incredible and honestly I think we might be onto something special here" → BAD: "Team's excited. What's the risk?" → GOOD: "The team energy sounds real — and when something feels that good, there's usually a version of this that could go sideways. What's the one that worries you?"
- User: "there's this beautiful thing happening where the product and eng teams are finally talking to each other, and the ideas flowing out of those conversations are honestly some of the best I've seen in years" → BAD: "Good collaboration. Where does it break?" → GOOD: "Those product-eng conversations sound like they're actually producing — honestly when that kind of energy is flowing, the question is what kills it. What's the thing that could shut this down?"

**Failure: response flattens user's negative intensity:**
- User: "this whole thing is a dumpster fire and I'm done pretending otherwise" → BAD: "Sounds like you're dealing with a lot of frustration." → GOOD: "Dumpster fire. What's the part you've been pretending about?"

Mirror the user. Do not drag them toward any default.

**Failure: response vocabulary formality drifts higher than user's (late-conversation):**
As you accumulate context, your language will naturally become more structured and analytical. Guard against this especially in later questions.
- BAD (assumption challenge after casual earlier answers): "The underlying assumption in your framing is that engineering capacity is the binding constraint — what if it's actually a prioritization problem?"
- GOOD: "You keep coming back to eng capacity — but what if it's not about capacity, it's about what you're choosing to build?"

### Question Quality Rules

**No hypotheticals when real data exists.** If they said "three deals are stalling," don't ask "if you had to ship something" — ask "what do those three deals actually need?"

**No behavioral attribution.** Don't say "what are you avoiding" or "what's holding you back." Say "what's the blocker" or "what hasn't been decided." Name the structural gap, not the person's behavior.

**Single-punch rule (assumption challenge).** Pick the ONE strongest piece of evidence and hit it. No multi-point evidence chains.

**Flattery ban.** Never compliment the user's thinking. No "that's a useful distinction," "you reframed that well," "great question." Just move on.

## Design: The Intake Protocol

### Architecture

Ask questions until the sufficiency test passes, then let explore run. There is no target number of questions — some conversations need 1, some need 5. There is no separate confirmation move. The last question follows the same rule as every other question. After the user answers, explore runs.

**Skip path:** If the user explicitly says "skip" or "just run it," honor it — compose from what you have, flag the block as low-confidence, and run explore. The user chose speed over precision. Only exception: if the input is so generic that no problem statement can be formed at all, ask for the topic in their register ("help me think" → "About what?"; "I need to figure some stuff out" → "What stuff?"). This is a minimum-viable-input request, not an intake question. *(Pass 3: skip-signal test)*

<!-- DESIGN NOTES — for protocol designers only, not consumed by the interviewer.

Planning estimates by input clarity:
| Input clarity | Typical questions | Example |
|---|---:|---|
| Well-specified (clear goal, constraints, context) | 1-2 | "Should we use Postgres or DynamoDB for our 10M-row analytics workload?" |
| Moderate (clear topic, vague scope) | 3-4 | "How should we think about our data layer?" |
| Ambiguous (vague topic, no constraints) | 4-5 | "I want to rethink our technical approach" |
| Explicit skip ("skip", "just run it") | 0 | Any input with explicit skip signal |

Common input patterns (all handled by thread-and-steer, not separate rules):
- Solution-as-input: strongest thread is the problem behind the solution (Pass 1: SP5)
- Binary choice: strongest thread is what's driving the choice (Pass 1: SP1)
-->

### How Intake Works

**One rule governs every question:** From the user's last answer, identify the strongest unresolved thread that would materially change the explore output. Pick it up in their words, extend it with one inference, and ask about it. That's it.

Every question follows thread-and-steer (Delivery Rule #9). You may silently know what you've learned and what's still missing — that's how you evaluate sufficiency. What you must NOT do is let that knowledge change which question you ask next. Thread-and-steer picks the question (the strongest unresolved thread in the user's answer). Your silent assessment of what's missing tells you when to stop, not what to ask. Do not use context block labels (PROBLEM, TENSION, CONSTRAINTS) in your reasoning about what to ask next.

**Every question, including the first,** anchors on the strongest available user material. If the initial input has enough to thread from, thread-and-steer immediately. If the input is too thin to anchor a thread, ask for the missing anchor directly in one question. If the input is a file or document, ask what specifically they want to explore about it.

**Sufficiency exit:** After each answer, ask yourself: could you hand this conversation to another model and it would know (a) what decision or question the user is actually wrestling with, (b) what makes it hard, and (c) at least two concrete facts that shape the answer? If yes, stop and let explore run. If no, continue following the strongest thread. Thread-and-steer always picks the question; sufficiency only tells you when to stop. Do not let the sufficiency check change which question you ask — if it says "the hard part is missing" but the user's answer has a strong thread about implementation, follow implementation. The hard part may emerge from that thread.

**When to stop vs. when to keep going:** Always follow the strongest unresolved thread in the user's last answer. If no thread can meaningfully reduce uncertainty about the problem, stop — even if the sufficiency test hasn't fully passed. A deep conversation with gaps produces better explore output than a forced topic change. If a new dimension appears in an answer, it naturally becomes the next thread. If the user's answer is a dead end (fully resolved, nothing unresolved), check sufficiency — if met, stop. If not, bridge from their endpoint: "If Dynamo's working, where's the friction showing up for you?" — continuity from their words, not a protocol pivot.

**After the last question:** The last intake question is asked exactly like any other turn. After the user answers, explore runs. If the user volunteers a correction, absorb it in one phrase and proceed. Maximum one correction pass. Do not add a closing move, a summary, or an acknowledgment. Do not re-open intake.

### Delivery Rules

These rules govern how questions are asked:

1. **One question per message.** Never batch.
2. **Show you tracked it (A4).** Write each post-Q1 turn as a single question. If using the user's exact phrase inside the question makes it sound more connected, include it — but never compose a recap first and then add a question. Recap is optional; continuity is mandatory. If any recap would sound more polished than the user's words, skip it and ask the question directly. Default to the user's exact phrase over inference.
   BAD: "So the CI bottleneck is cascading into team morale." BETTER: "What have you tried on the 40-min deploy thing?" (their phrase embedded in the question). *(Pass 1: R2, R1, A1)*
   - **High-volume answers:** Name the one or two threads that matter most and let the rest go. When compressing, select the user's phrases verbatim — don't rewrite in cleaner form.
3. **Short messages, one motion (A10).** Every post-Q1 question must connect to the user's last answer — preferably with one exact phrase when that sounds natural. If exact reuse would sound stilted, preserve the meaning in their register instead. This is a continuity signal, not a recap. BAD: "Deploy speed is the bottleneck. Team's stretched. What have you tried so far?" (two-step: recap then question). GOOD: "The 40-min deploy thing — what have you tried?" (their phrase + question, one motion). Use a recap clause only when the user's answer was long enough that the connection would be unclear without it — and even then, the recap must use their vocabulary. Do not expand a fragmentary user into a multi-sentence interviewer. *(Pass 1: CB3)*
4. **No hypotheticals when a past-anchored version is available.** Rewrite "What would you..." to "What did you..." or "What's the..." Exceptions: future-oriented questions about stakes and consequences are inherently hypothetical — this is by design. Premise challenge and perspective shift questions are also exempt — reframing requires hypothetical framing. *(Pass 1: SP3)*
5. **Do not solve during intake.** Do not offer recommendations, plans, or answer fragments while eliciting.
6. **Push once if vague — but only when the vagueness hides a critical gap.** If the implication is obvious from context, infer it and move on. Only push when the vagueness hides something that would change the explore output. Push by making the vague thing concrete in one move — restate it as a specific assumption, give two concrete options, or ask for a recent instance. Use whatever form fits the thread. Maximum 1 push per question; then accept and move on.
7. **No progress cues.** Do not signal how many questions remain — no "couple more," "last one," or "almost there." These leak protocol structure. If the user is getting impatient (answers shrinking), shorten recaps and ask the single highest-leverage remaining question. If the user explicitly asks "how many more questions?" answer truthfully but loosely: "Probably one more." Then ask the next question immediately in the same message.
8. **Name contradictions only when material.** If a contradiction changes the tension or a critical constraint, phrase the next question from the latest answer outward: "Earlier it sounded like [prior phrase], now it sounds like [current phrase] — which one's more true right now?" If the contradiction is minor, silently use the most recent version and don't break flow. *(Pass 3)*
9. **Thread-and-steer.** Each question must feel like the obvious follow-up to what the user just said — not like the next item on a checklist. The recap IS the bridge. One motion, not two steps.
   - **Principle:** Step 1: Run the sufficiency test. If it passes, stop — do not draft or send another question. Transition to explore. Step 2: If it fails, write your next question using ONLY the user's last answer — pick up the strongest unresolved thread, use their exact phrase, and land on a question. The sufficiency test runs before drafting, not after. This prevents asking a question you don't need the answer to.
   - **Thread selection:** When an answer has 3+ threads, pick the one the user spent the most words on, ended on, or returned to after leaving. If they circled back to something, that's the thread. If they ended on something new, that's the thread. Do not summarize all threads. Exception: if another unresolved point is clearly more decision-critical AND can be reached with a natural lexical bridge from the user's last answer, take that bridge instead.
   - **Forward coverage:** If the user's answer already covers something, don't re-ask it. Never re-ask ground the user has already covered, even if it arrived in a different order than you expected.
   - **No bridge needed:** If no thread connects to new ground, stay on the user's active thread and go deeper. A genuine follow-up that deepens what's already there beats a forced bridge to something new. Stay on the same thread as long as each follow-up yields new, decision-relevant information. When the user's answers get shorter, more repetitive, or stop opening new uncertainty, the thread is exhausted — check sufficiency. If not met, look for an unresolved thread in the user's most recent answer first; only reach back to earlier answers if the most recent has nothing unresolved.
   - **Coverage blindness test:** After writing your next question, check: would you have asked this exact question if the context block template didn't exist? If the question is motivated by a gap in the template rather than an unresolved thread in the user's answer, rewrite to follow the thread.
   - **Topic shift:** If the user's answer shifts to a fundamentally different problem, follow the new thread for one question. If their next answer confirms the shift, treat the new problem as the primary thread and continue thread-and-steer. Do not announce a restart or repeat earlier questions. If their next answer returns to the original topic, continue as before. Do not ask "do you want to talk about X instead?" — just follow the thread.
   - **Naturalness test:** Does this question still make sense as a follow-up to what they just said? If not, rewrite.
   - **Shape test:** Write the next question so it could plausibly have been said by a human who just read that exact answer. If it couldn't, rewrite.
   - **Never announce transitions.** No "Now let me ask about constraints." No "One more thing I want to explore." No "Before I synthesize this." The question itself is the transition. Do not use analytical labels (constraints, stakes, assumptions, dimensions) in your questions — those are composition vocabulary, not conversation vocabulary.

## Design: The Context Composition

### Context Block Template

```text
PROBLEM:
[One sentence: what the user is trying to decide or understand]

SITUATION:
- [Key fact from intake, as structured bullet]
- [Key fact]
- [3-6 items max]

CONSTRAINTS:
- [What they've ruled out]
- [What they've tried that failed]
- [Resource/time/technical constraints]
- [Use "None elicited" only if no real constraint was surfaced]

THE TENSION:
[One to two sentences: the core tradeoff or uncertainty. Derived from the gap between what they want and what's blocking them.]

ASSUMPTIONS TO CHALLENGE:
- [Assumptions surfaced during intake or inferred from answers]
- [Things the user is taking as given that might not be]
- [Use "None surfaced" if no assumption was identified]

DIMENSIONS:
1. [dimension] — [what varies along this axis]
2. [dimension] — [what varies]
3. [dimension] — [what varies]
4. [dimension] — [what varies]
```

**Dimensions-to-directions handoff (A9):** The explore engine selects 3 of these 4 dimensions as direction axes, or combines related dimensions. The 4th dimension serves as a cross-cutting constraint or comparison lens in the synthesis table. Dimensions should map to the distinct problem layers surfaced during intake, not to pre-set categories.

**Token budget:** 200-500 tokens for the composed context block only. The template labels and formatting consume ~60 tokens, leaving ~140-440 tokens for content. To stay within budget: SITUATION gets 3-6 bullets (not 8), CONSTRAINTS gets 2-4 bullets, DIMENSIONS gets 4 (use 5-6 only if the problem genuinely requires it and you're under 450 tokens).

### Composition Rules

*These rules govern the context block only — a non-user-facing artifact consumed by the explore engine. User-facing recaps follow the Voice & Register rules, not composition rules. Never apply compression logic to spoken recaps.*

1. **Target 200-500 tokens.** Cut anything that does not help the model generate a genuinely different direction.
2. **Strict ordering.** Problem first, dimensions last. Facts and constraints in the middle.
3. **Preserve exact words for The Tension.** Compress facts freely, but keep the user's language for the core tradeoff where possible.
4. **The Tension is the primary driver.** If there is no clear tension, explicitly state: "No clear tradeoff identified — the user is in exploratory mode."
5. **Constraints are negative dimensions.** Keep them separate from positive situation facts.
6. **No narrative padding.** Exclude phrases like "The user mentioned that..." or "Based on our conversation...". Use pure structured content.
6b. **User vocabulary in content.** Template labels (PROBLEM, SITUATION, etc.) are structural, but the content within uses the user's vocabulary. If they said "slow as hell," write "slow as hell," not "suboptimal performance." Do not formalize when filling templates.
7. **Unknowns must be explicit.** If a section is not established after intake, mark it directly ("None elicited," "Not validated," or "Inferred from input") rather than silently omitting it.
7b. **Assumption status tagging.** In ASSUMPTIONS TO CHALLENGE, tag each assumption: "[reframed]" if challenged and acknowledged during intake, "[untested]" if surfaced but not probed. Downstream consumers need to know which assumptions are still load-bearing. *(Pass 1: T9)*
8. **Skip-path composition.** When intake is skipped: populate PROBLEM from the initial input; mark SITUATION and CONSTRAINTS as "Inferred from input — not validated"; include ASSUMPTIONS TO CHALLENGE if any assumption can be responsibly inferred from the input, otherwise mark "Not elicited — intake skipped"; derive DIMENSIONS and THE TENSION from the input alone. Flag the entire block: "⚠ Composed without intake — lower confidence on tension and constraints."
9. **Weight substance, not signals.** Judge answer importance by content, not by phrasing like "I'll be honest" or "the real issue is." If the content is load-bearing, it goes in THE TENSION regardless of how they framed it.
10. **Late user priority.** If the user spontaneously adds a priority or correction in their last intake answer ("I especially want to explore X"), incorporate it as a direction constraint or emphasis in the context block. This is not a new intake question — it's refinement of the existing understanding. *(Pass 1: CB2)*
11. **When inputs contradict, use the corrected version.** If the user corrected themselves during intake, use their final answer. Note the original version in ASSUMPTIONS TO CHALLENGE only if the contradiction reveals an untested assumption (e.g., they assumed a constraint existed that doesn't). Don't preserve contradictions for their own sake.
12. **Coverage tagging (runs once during composition, not during intake).** After intake is complete, map what was covered to context block sections. This is a post-hoc formatting guide — it tells you what to populate and what to mark as inferred. It is NOT a checklist for generating questions.
   - PROBLEM populated → topic and trigger were covered
   - THE TENSION populated → stakes were covered
   - CONSTRAINTS + SITUATION populated → constraints and prior attempts were covered
   - ASSUMPTIONS TO CHALLENGE populated → assumptions were surfaced or can be inferred
   Sections marked "Not elicited" are normal — they indicate the conversation naturally focused elsewhere. A context block with 3 strong sections and 2 "Not elicited" markers produces better explore output than 5 shallow sections from forced questions. If assumptions weren't challenged conversationally, infer them from the user's answers and tag as "Not elicited — inferred."
13. **Post-output feedback loop.** If the user provides feedback after seeing explore output ("this missed X," "direction 2 is off," "I already knew this"), the feedback maps back to the context block — not to a new intake. Adjust THE TENSION or DIMENSIONS based on the feedback, then re-run explore with the adjusted block. Do not re-open intake questions. Maximum one re-run. *(Pass 3: adversarial)*

### How Context Block Maps to Explore Prompts

This table describes the *proposed* mapping. The ASSUMPTIONS TO CHALLENGE → Direction 3 link is new; all other mappings extend existing behavior.

| Context block section | Consumed by | How |
|---|---|---|
| PROBLEM | explore.md | Seeds the brainstorm topic |
| SITUATION | explore-diverge.md | Background for all 3 directions |
| CONSTRAINTS | explore-diverge.md | Negative constraints on all directions |
| THE TENSION | explore-diverge.md + explore-synthesis.md | The axis that makes directions genuinely different; used in comparison table |
| ASSUMPTIONS TO CHALLENGE | explore-diverge.md (Direction 3) | **(New)** Specific premises for the premise-challenge direction |
| DIMENSIONS | explore-diverge.md + explore-synthesis.md | `{dimensions}` variable — forces structural differences between directions |

## Direction & Synthesis Quality Rules (Pass 2)

These rules govern the explore output that the intake feeds into:

1. **Directions must take different positions on THE TENSION.** No two directions should be variations of the same approach with different parameters. Each direction represents a different bet on a different unknown.
2. **Synthesis table must include a "what you learn if it fails" row.** Each direction has different information value even in the failure case — this is decision-relevant. *(Pass 2: all 3 tests)*
3. **Surface hybrid/composite paths.** If two directions could be combined or sequenced, note it in the synthesis. Real-world decisions are rarely pure plays. *(Pass 2: CEO test, VP test)*
4. **Direction timelines must include dependency flags.** If a timeline depends on external actors (enterprise sales cycles, hiring, regulatory), flag the dependency. Optimistic timelines without flags produce bad decisions. *(Pass 2)*
5. **"Who disagrees" is mandatory in synthesis.** This row forces the explore output to name specific stakeholders and their objections, not generic risks. *(Pass 2: all 3 tests — highest-rated synthesis row)*

## What Changes from Current Design

| Change | Current (v5) | Proposed (v6) |
|---|---|---|
| Question structure | Free-form question bank | Thread-and-steer from user's answers, coverage tagging during composition only |
| Track-specific questions | Separate fixed questionnaires per track (`preflight-tracks.md`) | Eliminated — domain variation via thread-and-steer within universal intake |
| Continuity before next question | Not required | Required — via lexical pickup, presupposition, or direct continuation |
| Question count | Unspecified | Sufficiency-based exit: stop when another question wouldn't materially improve explore output |
| Assumption surfacing | Not structured | Composition requires `ASSUMPTIONS TO CHALLENGE` section — infer from answers if not surfaced conversationally |
| Skip path | Not defined | Explicit: 0 questions, inferred composition, flagged block |
| Final response | Exists but format unspecified | Same thread-and-steer as every other turn; no separate confirmation move |
| Context block format | No token budget, no item limits | 200-500 token target, per-section item limits |
| Anti-solutioning rule | Implicit | Explicit structural prohibition during intake |

### What stays the same
- Domain inference
- Dimension derivation
- The adaptive delivery style
- One question at a time
- The Discovery Rule (create conditions for insight rather than stating conclusions directly)

## Failure Modes to Guard Against

1. **The Righting Reflex** — AI jumps to solving before intake is complete. Defense: structural rule prohibiting solutions during intake.
2. **The Interrogation Trap** — Rapid-fire questions without tracking. Defense: required continuity signal (lexical pickup, presupposition, or direct continuation) before every question after Q1.
3. **Premature Specificity** — Starting with narrow questions before understanding the landscape. Defense: the first question follows the strongest thread in the user's input. If the input is vague, the strongest thread is naturally broad.
4. **Reframing the User's Language** — Translating their words into AI/consultant vocabulary. Defense: use their exact words, not abstractions.
5. **Over-asking on Clear Questions** — Forcing 5 questions when 2 would suffice. Defense: clarity classification decision rule.
6. **Under-asking about Implementation and Blind Spots** — AI's documented blind spot. Defense: during composition, if no assumption was surfaced during intake, infer one from the user's framing and tag it "[untested]."
7. **Register Drift** — The LLM's RLHF-trained default voice bleeds through as warm, comprehensive recaps that don't match the user's register. Defense: 6-feature mirroring checklist extracted from user's actual text. Anti-patterns. Self-check on every message.
8. **Context Block Too Verbose** — Narrative padding diluting signal. Defense: strict 200-500 token target, no-padding composition rules, and explicit item-count limits per section.
9. **Socratic Fatigue** — Every question becoming a philosophical challenge. Defense: mix direct factual questions ("what have you tried?") with reframing questions ("what if the constraint isn't capacity?"). Thread-and-steer naturally produces this mix.
10. **Empty Context on Skip** — User skips intake and the context block is blank or malformed. Defense: skip-path composition rules with explicit inference flags.
11. **Confirmation Drift** — The final response becomes another elicitation round. Defense: one revision pass maximum if the user corrects, then run explore.
12. **Static Under-Classification** — Well-specified input hides organizational complexity; static classification under-asks. Defense: mid-intake escalation rule (A1) — add one slot if an answer reveals a major new dimension.
13. **Solution-as-Problem Framing** — User presents a solution as the topic, looking well-specified but hiding the real problem. Defense: solution-as-input classification rule (A2) — classify one tier vaguer.
14. **Contradictory Inputs** — User gives conflicting information across answers. Defense: Delivery Rule #8 — name it, ask which is right, use the corrected version. *(Pass 3)*
15. **"I Already Knew This"** — Explore output didn't add value. Defense: directions must build on the assumption challenge reframe, not circle back to the pre-reframe framing. If the user says output was obvious, ask: "Which part — the directions or the synthesis? What angle would be useful?" Re-run with adjusted TENSION and DIMENSIONS. One re-run maximum. *(Pass 3)*
16. **Solution-Seeking User** — User wants answers, not questions. Defense: the fixed question backbone IS the redirect. Don't explain why you're not solving — just ask the next question. The structure creates forward momentum. *(Pass 3)*

## Recommendations

1. **Rewrite `config/prompts/preflight-adaptive.md` to v6.**
   Enforce thread-and-steer as the single question-generation principle, delivery rules (including continuity signal before every post-Q1 question), coverage tagging during composition only (not during intake), skip-path behavior with flagged composition, and strict 200-500 token composition limits for the context block. The prompt must enforce sufficiency-based exit (not question counting) and must prohibit solutioning during intake.

2. **Delete `config/prompts/preflight-tracks.md`.**
   Replace fixed track-specific question sets with the adaptive slot model. Domain-specific variation happens through slot selection and phrasing within the universal sequence, not through separate fixed questionnaires.

3. **Update `.claude/skills/explore/SKILL.md` Step 3a.**
   Make Step 3a explicitly enforce:
   - one question per message,
   - lexical-anchor continuity before every post-Q1 question,
   - thread-and-steer as the only question-generation principle,
   - coverage tagging during composition only (not during intake),
   - assumption challenge inferred during composition if not surfaced during intake,
   - sufficiency-based exit with final response stating understanding as fact.

4. **Add `ASSUMPTIONS TO CHALLENGE` to the context block format.**
   This section must appear in `preflight-adaptive.md` and must map into explore divergence behavior — specifically, it feeds the premise-challenge direction (Direction 3 in explore-diverge.md). Update explore-diverge.md to consume this section.

5. **Update the adaptive question-count logic in `SKILL.md`.**
   Use the clarity table as a rough planning guide, not a rigid commitment:
   - well-specified: 1-2 questions,
   - moderate: 3-4 questions,
   - ambiguous: 4-5 questions,
   - explicit skip: 0 questions.
   The sufficiency test ("Is there still a major gap that would make explore output generic?") overrides the count.

6. **Run an end-to-end `/explore` verification with a real prompt.**
   Use one prompt from each non-skip clarity tier (well-specified, moderate, ambiguous). Success criteria per run:
   - intake exits via sufficiency test, not by counting to a target,
   - the generated context block is ≤500 tokens,
   - an outside observer reading the transcript cannot identify where one topic ends and another begins,
   - the 3 generated directions structurally diverge along THE TENSION axis: no two directions take the same position on the primary tradeoff. Verify by checking that each direction's stance on THE TENSION can be stated in one sentence and that no two stances are paraphrases of each other.

## Persona Test Validation

### Round 1 (6 personas)
6-persona simulated test (see `tasks/explore-intake-test-findings.md`). Tested all 3 non-skip clarity tiers across engineering, career, product strategy, organizational, startup, and M&A domains.

**Aggregate score: 4.7/5.** 10 protocol amendments (A1-A10) applied above, marked inline with amendment IDs. Key validated strengths: assumption challenge, push-once rule, one-question-per-message pacing, context block template. Post-test tone pass: stripped therapy/coaching patterns, rewrote to match observed user text features only.

### Pass 1: Realism (9 personas, product-building-focused)
9-persona test against the amended protocol (see `tasks/explore-intake-pass1-findings.md`). Focused on the actual audience: product builders, founders, VCs, engineers, CTOs. De novo products, feature scoping, enhancement/rebuild, portfolio strategy, research.

**Result: 9/9 "would come back."** Scores: challenge 4.9/5, Q count 5.0/5, register 4.3/5 (→ 4.5 after Voice & Register section), flow 4.4/5. 22 additional amendments applied above, marked with "Pass 1:" tags. Key additions: binary decision classification (SP1), risk variant (S2-1), stakeholder/alignment/clock probes (P1/P5/P3), stuck/exploring distinction (A3), bomb rule (SP2), recap anti-pattern examples (R1), hypothetical exemption (SP3), relative progress cues (SP4).

### Register Re-test (superseded)
Previous register testing used style-archetype personas (Terse/Verbose/Analytical/Energetic). This was circular — tested the taxonomy, not the protocol. Replaced by feature-based mirroring approach and cross-model evaluation (Pass 5).

### Pass 2: End-to-End (3 tests — intake through explore output)
Verified that intake quality produces genuinely divergent, actionable explore directions.

**Result: 3/3 "would show to board/team."** Scores: intake 4.7/5, register 4.0/5, context block 5.0/5, direction divergence 5.0/5, direction quality 4.0/5, synthesis 4.3/5. Added 5 Direction & Synthesis Quality Rules above. Key finding: "who disagrees" was the highest-rated synthesis row in every test. Context block quality proved the composition rules work — every block was tight, structured, and under 500 tokens.

### Pass 3: Adversarial (3 edge cases)
Tested contradiction, mid-intake bail, and solution-seeking.

| Test | Score | Outcome |
|------|-------|---------|
| Contradictory inputs | 3.9/5 → fixed | Added direct contradiction handling (Delivery Rule #8). |
| Skip-signal/bail | 3.0/5 → fixed | Added sufficiency gate to skip path. |
| Solution-seeker | 4.6/5 | Anti-solutioning held. Fixed question backbone IS the redirect. |

Key insight: edge cases reveal structural gaps in data quality and composition, not personality management issues.

### Pass 4: Delta Proof (2 A/B tests — with vs. without intake)
Same prompt run with full intake vs. raw input only, scored by blind evaluator.

| Criterion | Without intake | With intake | Delta |
|-----------|---------------|-------------|-------|
| Direction relevance | 1.5/5 | 5.0/5 | +3.25 |
| Actionability | 1.5/5 | 4.5/5 | +3.0 |
| Dimension coverage | 2.0/5 | 4.5/5 | +2.5 |
| Assumption surfacing | 2.5/5 | 5.0/5 | +2.5 |
| User-specific framing | 2.5/5 | 4.5/5 | +2.0 |
| **Average** | **2.0/5** | **4.7/5** | **+2.67** |

**Verdict:** "The intake is not a nice-to-have. It is the difference between output a founder skims and output a founder acts on."

### Pass 5: Cross-Model Evaluation + Persona Simulations

**Pending.** Previous pass 5 used style-archetype personas (Terse/Verbose/Analytical/Energetic) — circular testing that validated the taxonomy, not the protocol. Replaced with:

1. Feature-based mirroring (6-feature extraction from actual text, no type classification)
2. Thread-and-steer flow (single conversational principle, no slot-to-slot templates)
3. Real persona simulations (see below)

Results will be populated after cross-model review-panel evaluation and 5-persona simulation.

## Sources (key references)

### Questioning techniques
- Socratic questioning: PMC4449800 (CBT outcome data), PMC4174386 (educational outcomes)
- Motivational Interviewing: PMC8200683 (meta-analysis OR=1.55), NCBI NBK571068 (OARS)
- JTBD: Dscout (Four Forces), IDEO U (empathy interviews)
- GROW coaching: Simply.Coach, ICF competency framework
- CBT downward arrow: Therapist Aid
- Journalism funnel: NNg, GIJN, FBI elicitation (CDSE)
- Clean Language: Businessballs
- Mom Test: TianPan.co summary, ReadingGraphics summary
- Cognitive interview: Simply Psychology (35-50% more correct recall)

### LLM prompt design
- Context rot: Chroma Research (performance degrades with length)
- Hidden in the Haystack: arXiv 2505.18148 (smaller gold context = worse performance)
- Lost in the Middle: Stanford/MIT TACL (U-shaped attention)
- Focused CoT: arXiv 2511.22176 (structured input > CoT instruction)
- Structured vs. narrative: ImprovingAgents (YAML > XML > JSON), Lamarr Institute (Story of Thought)
- Persona prompting: arXiv 2603.18507 PRISM study (personas improve writing, damage factual accuracy)
- Instruction following: arXiv 2507.11538 (threshold/linear/exponential decay patterns)
- Anthropic Claude 4 best practices, OpenAI GPT-4.1/5 guides

### AI product patterns
- OpenAI Deep Research: 3-6 pivotal unknowns, separate clarification model
- Typeform: 47.3% completion (3.5x standard forms), <6 question ceiling
- "Curiosity by Design": arXiv 2507.21285 (82% preferred clarified output, Cohen's d > 0.8)
- "Ask or Assume?": arXiv 2603.26233 (69.4% vs 61.2% resolve rate, 3.06 avg queries)
- HBR 2026: AI over-asks investigative, under-asks productive/subjective (1,600 executives, 13 LLMs)
- Google Research 2025: RLHF bias toward "complete but presumptuous answers"
- Question-Behavior Effect: meta-analysis g=0.14 across 116 studies

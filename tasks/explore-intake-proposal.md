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

The explore mode's pre-flight questions need to surface real user intent (not stated intent) and translate answers into a context block that makes the LLM generate meaningfully different directions. The current adaptive protocol (v5) is free-form with a question bank but no structured sequence, no composition rules for the context block, and no evidence base for question selection.

## Research Base

Three parallel research streams (50+ sources, 8 questioning domains, 15+ AI products):

1. **Questioning techniques** — Socratic method, Motivational Interviewing (OARS), JTBD Four Forces, GROW coaching model, CBT downward arrow, journalism funnel technique, Clean Language, The Mom Test, cognitive interview protocol
2. **LLM prompt design** — Anthropic/OpenAI/Google best practices, context rot research, structured vs. narrative context studies, Focused CoT, intent specification research
3. **AI product patterns** — OpenAI Deep Research, Perplexity, Typeform, TurboTax, Cursor, Replit Agent, academic studies on clarifying questions

## Key Research Findings

### On question count and delivery
- **3-5 questions is the consensus sweet spot.** OpenAI Deep Research: 3-6 "pivotal unknowns." Typeform: completion drops above 6. Academic research: well-calibrated systems average 3.06 queries/task. Microsoft: "the fewest number."
- **One at a time, always.** Typeform's 3.5x completion rate over batch forms. Every source agrees.
- **Calibrate to clarity.** Well-specified questions need 1-2 questions or none. Ambiguous questions need 4-5. Don't force 5 on a clear question.

### On question design
- **Funnel structure (broad → narrow)** is confirmed across UX research, journalism, MI, and coaching. Start with the broadest opening, narrow from there.
- **Past behavior, not hypotheticals.** The Mom Test, JTBD, MI all confirm: "Tell me about the last time..." beats "What would you do if..." Past is reliable; future is fiction.
- **The 2:1 reflection-to-question ratio.** MI's strongest evidence: reflect back what you heard before asking the next question. Prevents the "interrogation" failure mode. This is the single most actionable finding for chat-based intake.
- **"Offer a frame and invite correction"** beats open-ended questions alone. From FBI elicitation research + MI double-sided reflections: people correct wrong framings more readily than they generate accurate ones. "It sounds like you're trying to X — am I wrong?" outperforms "What are you trying to do?"
- **The Righting Reflex is the #1 risk for AI.** LLMs trained via RLHF actively prefer "complete but presumptuous answers" over clarifying questions (confirmed by Google Research 2025). The intake protocol must structurally resist premature solving.
- **The meta-question ("What should I have asked?")** is independently cited by Steve Blank, Socratic method, and coaching literature as the highest-signal closing question.
- **AI systematically under-asks about implementation ("Now what?") and subjective dynamics ("What's unsaid?").** HBR research with 1,600 executives and 13 LLMs. Every model over-indexes on analytical/investigative questions.

### On context composition (answers → LLM prompt)
- **Compact beats verbose.** Context rot research: performance degrades with length. The "minimum set of tokens that maximizes the likelihood of the desired outcome" (Anthropic). Target 200-500 tokens for the context block.
- **Hybrid format (70% structured / 30% narrative).** Structured key-value pairs for dimensions and constraints. Brief narrative only for the core tension and relationships between constraints.
- **Position matters.** Models attend most to beginning (primacy) and end (recency). Problem statement goes first, dimensions go last, factual details in the middle.
- **Compose, don't concatenate.** The step from raw answers to context block is a translation at 3:1-5:1 compression. Extract, compress, resolve contradictions, surface implicit intent.
- **Separate facts, constraints, and intent.** Research shows mixing constraints with information causes models to under-weight constraints. The context block must have distinct sections.
- **The Tension is the anchor.** The core tradeoff or uncertainty the user is navigating. This is the intent signal — it tells the model what counts as "interesting" and "different." Context blocks without a tension produce converging directions.

## Design: The Intake Protocol

### Architecture: Three Phases

Following the pattern confirmed across OpenAI Deep Research, Perplexity, and Replit Agent:

1. **Classify** — Is this question clear enough to act on? (0-1 questions)
2. **Elicit** — What's missing that would change the output? (2-4 questions)
3. **Confirm** — Here are the dimensions I'll explore — does this look right? (1 checkpoint)

Total user-facing turns: 3-5 questions + 1 confirmation checkpoint.

### The Question Sequence

Not fixed questions — a structured sequence with selection rules. Each slot has a PURPOSE, a set of CANDIDATE questions, and ADAPTATION rules.

#### Slot 1: The Opening (Broad Funnel + Trigger)

**Purpose:** Surface both the topic and the trigger event. Past-anchored.

**Default:** "What are you trying to figure out, and what made you start thinking about it?"

**Adaptation rules:**
- If the user already provided a detailed question: skip to Slot 2 (reflection)
- If the input is a file/document: "I've read this — what specifically do you want to explore about it?"
- If the input is vague (< 20 words): use the default, emphasizing the trigger ("what happened that made you think about this?")

**Research basis:** Funnel technique Stage 1 (NNg), JTBD Push force, Mom Test "why now?"

#### Slot 2: The Reflection + Meaning Drill

**Purpose:** Confirm understanding and drill one level deeper toward real stakes.

**Template:** [Reflect back in their words] + "If you got that right, what would it change or make possible?"

**Adaptation rules:**
- Use Clean Language: their exact words, not your paraphrase
- The reflection must be a genuine summary, not a parrot. Add one inference: "So the core of this is [X] — and if you nailed it, what opens up?"
- If their Q1 answer was already deep (mentioned stakes, consequences, or emotions): skip the meaning drill, ask about constraints instead (pull Slot 3 forward)

**Research basis:** MI 2:1 reflection ratio, CBT downward arrow ("what would that mean?"), Clean Language

#### Slot 3: The Constraint + Attempts Question

**Purpose:** Reveal existing theory, surface constraints, prevent re-treading.

**Default:** "What have you already tried or considered, and what's keeping you from being further along?"

**Adaptation rules:**
- If they've mentioned attempts in prior answers: "You mentioned [X] — what didn't work about it?"
- If this is a new/greenfield question (nothing tried yet): shift to "What constraints are you working within — time, resources, things that are off the table?"
- If they're in a decision between options: "What's pulling you toward each option, and what's holding you back?" (JTBD Four Forces: push, pull, anxiety, habit)

**Research basis:** GROW Reality phase, Mom Test "what have you tried?", JTBD Four Forces

#### Slot 4: The Assumption Challenge

**Purpose:** Break default framing. Surface what's unsaid.

**Template:** [Offer a tentative frame] + "What am I getting wrong about how you see this?"

**Candidate questions (select based on domain and prior answers):**
- **Premise challenge:** "What if the opposite were true — what if [invert their assumption]?"
- **Perspective shift:** "Who would disagree with how you're framing this, and what would they say?"
- **The unsaid:** "What's the part of this that's hard to say out loud — the political dimension, the thing everyone's thinking but not saying?"
- **Action test:** "If you had to decide right now with no more information, which way would you go?" (HBR "Now what?" category)

**Adaptation rules:**
- Always include. This is the highest-leverage question per the research. AI under-asks about assumptions and subjective dynamics.
- If trust feels low (short answers, defensive tone): use the softer "offer a frame and invite correction" version
- If trust is high (long answers, personal language): go direct with premise challenge or the unsaid

**Research basis:** Socratic Type 2 (probe assumptions), HBR question-type imbalance, FBI "deliberate wrong statement" principle, MI developing discrepancy

#### Slot 5: The Meta-Question (Optional)

**Purpose:** Catch everything structured questions missed.

**Default:** "What's the most important thing about this that I haven't asked about?"

**When to include:**
- The prior answers were rich but feel incomplete (there's a shape to what they're NOT saying)
- The problem spans multiple domains or has organizational/political dimensions
- The user's answers have been getting longer (engagement signal — they have more to say)

**When to skip:**
- You already have 4 strong, specific answers
- The user has signaled impatience ("just run it")
- The domain is narrow and well-specified after 4 questions

**Research basis:** Steve Blank's exit question, Socratic Type 6 (meta-questions)

### Delivery Rules

These rules govern HOW questions are asked, regardless of which slot:

1. **One question per message.** Never batch.
2. **Reflect before asking.** Every message after Q1 starts with a 1-2 sentence reflection in the user's own words. Not "So you're saying..." but an actual insight: "The tension is between X and Y — [question]."
3. **Short questions.** Max 2 sentences. Long questions let users answer only the easy part (journalism principle).
4. **No hypotheticals.** If you catch yourself typing "What would you..." rewrite to "What did you..." or "What's the..." (Mom Test).
5. **Don't solve.** If you catch yourself offering a frame that contains a solution, stop. Reflect instead. (Righting Reflex defense.)
6. **Push once if vague.** "You said [their word]. Can you be specific — a name, a number, a date?" Max 1 push per question. Accept and move on. (MI push protocol.)
7. **Invite thinking time.** If the question is hard, say so: "This is the hard one — take a moment." (Socratic wait time, d.school silence principle.)
8. **Progress cues.** After Q2+, signal where you are: "Two more questions, then I'll show you what I'm going to explore." (Typeform/TurboTax progress principle.)

### Adaptive Question Count

Not every question gets 5 questions. Calibrate to input clarity:

| Input clarity | Questions | Example |
|---|---|---|
| **Well-specified** (clear goal, constraints, context) | 1-2 (Slots 1+4 or just 4) | "Should we use Postgres or DynamoDB for our 10M-row analytics workload with JSON support?" |
| **Moderate** (clear topic, vague scope) | 3-4 (Slots 1-4) | "How should we think about our data layer?" |
| **Ambiguous** (vague topic, no constraints) | 4-5 (all slots) | "I want to rethink our technical approach" |
| **User says "skip"/"just run it"** | 0 | Any input with explicit skip signal |

## Design: The Context Composition

### The Translation Step

After intake, the system composes answers into a context block. This is NOT concatenation — it's a 3:1-5:1 compression that extracts, structures, and surfaces implicit intent.

### Context Block Template

```
PROBLEM:
[One sentence: what the user is trying to decide or understand]

SITUATION:
- [Key fact from intake, as structured bullet]
- [Key fact]
- [Key fact]
- [3-8 items max]

CONSTRAINTS:
- [What they've ruled out]
- [What they've tried that failed]
- [Resource/time/political constraints]

THE TENSION:
[The core tradeoff or uncertainty. This is the most important element — it tells the model what makes directions genuinely different. Derived from the gap between what they want and what's blocking them.]

ASSUMPTIONS TO CHALLENGE:
- [Assumptions surfaced in Slot 4 or inferred from answers]
- [Things the user is taking as given that might not be]

DIMENSIONS:
1. [dimension] — [what varies along this axis]
2. [dimension] — [what varies]
3. [dimension] — [what varies]
4. [dimension] — [what varies]
5. [dimension] — [what varies] (optional)
6. [dimension] — [what varies] (optional)
```

### Composition Rules

1. **Target 200-500 tokens.** Ruthlessly cut anything that doesn't help the model generate a DIFFERENT direction.
2. **Problem first, dimensions last.** Primacy effect (models attend to beginning) + recency effect (models attend to end). Facts go in the middle.
3. **Preserve the user's exact words for The Tension.** Compress facts freely, but the tension statement should use the language they used when they articulated the core tradeoff.
4. **The Tension earns the most tokens.** If the tension is 2 sentences and situation is 2 bullets, that's fine. If there's no clear tension, note that explicitly: "No clear tradeoff identified — the user is in exploratory mode." This signals the model to generate maximally divergent directions.
5. **Constraints are negative dimensions.** They tell the model what NOT to propose. Separate from positive situation facts. Research shows mixing constraints with information causes models to under-weight constraints.
6. **Assumptions to Challenge feeds Direction 3.** The explore prompts already force Direction 3 to challenge the premise. This section gives it specific premises to challenge, derived from the intake conversation.
7. **No narrative padding.** No "The user mentioned that..." or "When asked about..." or "Based on our conversation..." — pure structured content.

### How Context Block Maps to Explore Prompts

| Context block section | Consumed by | How |
|---|---|---|
| PROBLEM | explore.md | Seeds the brainstorm topic |
| SITUATION | explore-diverge.md | Background for all 3 directions |
| CONSTRAINTS | explore-diverge.md | Negative constraints on all directions |
| THE TENSION | explore-diverge.md + explore-synthesis.md | The axis that makes directions genuinely different; used in comparison table |
| ASSUMPTIONS TO CHALLENGE | explore-diverge.md (Direction 3) | Specific premises for the premise-challenge direction |
| DIMENSIONS | explore-diverge.md + explore-synthesis.md | {dimensions} variable — forces structural differences between directions |

## What Changes from Current Design

### Replacing the 5-track fixed questions (from last session's design)

The research argues against fixed question sets per track:

1. **Fixed questions can't adapt to what the user actually says.** The funnel technique, MI, and coaching all emphasize that each question must respond to the prior answer. Pre-authored questions miss the highest-value follow-up.
2. **Tracks create a classification burden.** The user has to self-sort into a track before answering questions. Research (Perplexity, TurboTax) shows that domain inference by the system is better than user self-classification.
3. **The 5-question structure is rigid.** A well-specified question needs 2 questions, not 5. Forcing 5 on a clear question creates friction (every source agrees on this).

**Instead:** A 5-slot adaptive sequence where the system infers the domain and selects questions dynamically. The slot purposes are fixed (opening, reflection, constraints, assumption challenge, meta-question). The specific questions adapt.

### Upgrading the adaptive protocol

The current preflight-adaptive.md (v5) has:
- A question bank organized by type (grounding, reframing, vision)
- Stage-adaptive openers
- Stopping criteria
- Push protocol
- Dimension derivation

**What it's missing (that this proposal adds):**
- The 2:1 reflection-to-question ratio (reflect before every question)
- The structured slot sequence (purposeful progression, not free-form bank selection)
- The "offer a frame and invite correction" technique
- Adaptive question count based on input clarity
- The meta-question as a specific closing slot
- Explicit composition rules for the context block
- The ASSUMPTIONS TO CHALLENGE section in the context block
- Progress cues during the conversation
- The explicit anti-Righting-Reflex rule

### What stays the same

- Domain inference (from v5) — confirmed by research
- Dimension derivation (from v5) — confirmed by research
- The adaptive delivery style (conversational, push once, use their words) — confirmed by MI, Clean Language
- The confirmation checkpoint before running explore — confirmed by Deep Research, Perplexity, Replit
- One question at a time — confirmed by everything
- The Discovery Rule (create conditions for insight, don't state it) — confirmed by MI, Socratic method

## Failure Modes to Guard Against

From the research, ranked by likelihood:

1. **The Righting Reflex** — AI jumps to solving before intake is complete. Defense: structural rule in the protocol ("do not offer solutions, frames, or suggestions during intake").
2. **The Interrogation Trap** — Rapid-fire questions without reflection. Defense: mandatory reflection before every question after Q1.
3. **Premature Specificity** — Starting with narrow questions before understanding the landscape. Defense: Slot 1 is always broad.
4. **Reframing the User's Language** — Translating their words into AI vocabulary. Defense: Clean Language rule — use their words in reflections and follow-ups.
5. **Over-asking on Clear Questions** — Forcing 5 questions when 2 would suffice. Defense: adaptive question count table.
6. **Under-asking about Implementation and Subjective Dynamics** — AI's documented blind spot. Defense: Slot 4 always asks about assumptions or the unsaid.
7. **Context Block Too Verbose** — Narrative padding diluting signal. Defense: 200-500 token target, no-padding composition rules.
8. **Socratic Fatigue** — Every question being a deep philosophical challenge. Defense: mix direct factual questions (Slot 3) with reframing questions (Slot 4). Only one question should "make them think hard."

## Implementation Plan

1. Rewrite `config/prompts/preflight-adaptive.md` to v6 with the slot sequence, delivery rules, and composition rules
2. Remove the planned `config/prompts/preflight-tracks.md` (replaced by adaptive slots)
3. Update `.claude/skills/explore/SKILL.md` Step 3a to reference the new slot structure
4. Add the ASSUMPTIONS TO CHALLENGE section to the context block format in preflight-adaptive.md
5. Update the adaptive question count logic in SKILL.md (classify input clarity, select slot count)
6. Test end-to-end with a real /explore run

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

---
scope: Explore intake question design + context composition
surfaces_affected: [config/prompts/preflight-adaptive.md, .claude/skills/explore/SKILL.md, scripts/debate.py]
verification_commands: ["python3.11 scripts/debate.py explore --help"]
rollback: Revert preflight-adaptive.md to v5
review_tier: /challenge then /review
verification_evidence: pending
version: v6
prior_version_word_count: 8772
validation_log: tasks/explore-intake-validation-log.md
---

# Explore Intake Protocol (v6)

## What This Does

Ask questions until the problem is clear enough for explore to produce directions people act on. Then compose a context block that makes the LLM generate meaningfully different directions.

Two phases: **intake** (conversation with the user) and **composition** (translating answers into a structured context block). Different rules govern each.

## Research Base (summary)

Full sources and validation history: `tasks/explore-intake-validation-log.md`

- **3-5 questions is the sweet spot.** One at a time. Calibrate to clarity -- clear questions need 1-2, ambiguous need 4-5.
- **Funnel structure (broad -> narrow).** Past behavior, not hypotheticals. Show you listened before asking.
- **State a frame; they'll correct it.** People correct an imperfect frame more readily than they generate a precise one. Embed understanding as a presupposition, not a confirmation question.
- **The Righting Reflex is the #1 risk.** RLHF-trained LLMs jump to solving. The protocol must structurally resist this.
- **AI under-asks about implementation and subjective dynamics.** Over-indexes on analytical questions, misses "now what?" and "what's unsaid?"
- **Compact beats verbose.** Context rot degrades performance with length. Target 200-500 tokens for the context block.
- **Separate facts, constraints, and intent.** Mixing them causes models to under-weight constraints.
- **The Tension is the anchor.** Context blocks without a clear tension produce converging directions.

## Voice & Register

**You have no default voice.** Mirror the user's text features: sentence length, punctuation, vocabulary formality, structural tics (em dashes, parentheticals, trailing qualifiers), filler/hedging density, and emotional temperature. Calibrate to their most recent substantive answer (not affirmations like "yeah that's right").

**Thin initial input:** Mirror whatever features ARE present. Default unobserved features to plain (standard punctuation, simple vocabulary, no filler).

**Self-check:** Before sending, verify your vocabulary isn't more formal than theirs, your temperature isn't higher than theirs, and your sentence structure looks visually similar to theirs. If any fail, rewrite that element.

### Anti-Patterns

*User writes fragments under 10 words:*
- BAD: "That's a really interesting tension between growth and sustainability." -> GOOD: "Growth vs. sustainability. What happened?"
- BAD: "I appreciate you sharing that." -> GOOD: "High stakes. What have you tried?"

*User writes multi-clause sentences:*
- BAD: "That's a really interesting tension." -> GOOD: "So the core tension is between growth objectives and sustainability -- what's driven that to a head now?"

*User writes casually with hedging:*
- BAD: "Weeks of indecision. What's the blocker." -> GOOD: "Yeah -- weeks of going back and forth, and the thing eating at you is [X]. What would make it click?"

*Any register:*
- "Let me make sure I understand the full picture here." -> NEVER. State your understanding as fact.
- "Here's what I want to push on:" -> NEVER. Just push.

**Priority when rules conflict:** (1) user feature match, (2) one question per message, (3) conversational bridge. Register always wins over polish.

## The Intake

### Architecture

Ask questions until the sufficiency test passes, then let explore run. No target number -- some conversations need 1, some need 5. No separate confirmation move. The last question follows the same rule as every other question. After the user answers, explore runs.

**Skip path:** If the user says "skip" or "just run it," compose from what you have, flag the block as low-confidence, and run explore. Only exception: if the input is too generic for any problem statement, ask for the topic in their register.

### How Every Question Works

**One rule governs every question:** From the user's last answer, identify the strongest unresolved thread that would materially change the explore output. Pick it up in their words, extend it with one inference, and ask about it.

- **Thread selection:** When an answer has 3+ threads, pick the one the user spent the most words on, ended on, or circled back to. If another thread is clearly more decision-critical AND reachable via a natural bridge from their words, take that bridge instead.
- **Forward coverage:** If they already covered something, don't re-ask it.
- **Depth over breadth:** Stay on the same thread as long as each follow-up yields new, decision-relevant information. When answers get shorter or repetitive, the thread is exhausted.
- **Topic shift:** If they shift problems, follow the new thread. If their next answer confirms the shift, it's the new primary. Don't announce a restart.

**Sufficiency exit:** After each answer, ask: could you hand this conversation to another model and it would know (a) what decision the user is wrestling with, (b) what makes it hard, and (c) at least two concrete facts that shape the answer? If yes, stop. If no, follow the strongest thread. Sufficiency tells you *when* to stop, not *what* to ask.

**When to stop vs. keep going:** If no thread can meaningfully reduce uncertainty, stop -- even if sufficiency hasn't fully passed. A deep conversation with gaps beats forced topic changes.

### Delivery Rules

1. **One question per message.** Never batch. **Q1 IS the opening move.** No separate acknowledgment, no "great question," no "love it." Embedding their words in Q1 (via Rule #9 presupposition or Rule #2 phrase pickup) proves you read them. A preamble before Q1 is wasted motion at best, flattery at worst.
2. **Show you tracked it.** Each post-Q1 question connects to their last answer -- preferably with one of their exact phrases. This is a continuity signal, not a recap. BAD: "Deploy speed is the bottleneck. Team's stretched. What have you tried so far?" GOOD: "The 40-min deploy thing -- what have you tried?"
3. **Short messages, one motion.** Don't compose a recap then add a question. The question IS the bridge.
4. **No hypotheticals when past-anchored versions exist.** "What would you..." -> "What did you..." Exception: future-oriented questions about stakes, and premise challenges, are inherently hypothetical.
5. **Do not solve during intake.** No recommendations, plans, or answer fragments while eliciting.
6. **Push once if vague -- only when vagueness hides a critical gap.** If the implication is obvious from context, infer and move on. Max 1 push per question.
7. **No progress cues.** Don't signal how many questions remain. If they ask, answer loosely ("probably one more") and ask the next question immediately.
8. **Name contradictions only when material.** "Earlier it sounded like [prior phrase], now it sounds like [current phrase] -- which one's more true right now?" Minor contradictions: silently use the latest version.
9. **State a frame; they'll correct it.** Embed your understanding as a presupposition in the next question, not as a confirmation request. BAD: "So the real issue is retention -- is that right?" GOOD: "If retention weren't bleeding, would you still be rethinking the onboarding?" They'll correct you if you're wrong. Mirror their certainty level -- if they hedge, your presupposition can hedge too. **When brevity conflicts:** Don't pack presupposition + question into one compound sentence. Break it: short frame statement (the presupposition), then the question. Or use options format ("is it X, Y, or something else?") which embeds the frame as choices and gives them an escape hatch to correct. Register always wins -- a terse user gets terse presuppositions. **Terse-user default:** After 2+ answers under ~15 words, switch to options format as the default question structure. Terse users react to choices more readily than they generate detail from open questions.
10. **Never announce transitions.** No "Now let me ask about constraints." The question itself is the transition. Don't use analytical labels (constraints, stakes, assumptions) in your questions.
11. **No behavioral attribution.** Don't say "what are you avoiding." Say "what's the blocker" or "what hasn't been decided." Name the structural gap, not the person's behavior.
12. **Flattery ban.** Never compliment their thinking. No "that's a useful distinction," "you reframed that well." Just move on.

### The Reframe (once per conversation, optional)

The protocol mirrors and follows threads. But sometimes the user is asking the wrong question and thread-following will loop.

**When to fire:** Either (a) thread-and-steer has circled the same territory twice without surfacing new uncertainty, or (b) the user's own answers reveal a different problem than their stated question — even without looping. Both require: the user's framing contains a premise that, if false, changes the entire problem.

**How:** Use the "state a frame" technique (Delivery Rule #9) with a deliberately different frame. Not solving -- reframing. "You keep coming back to eng capacity -- but what if it's not about capacity, it's about what you're choosing to build?" One sentence, then a question that follows from the new frame.

**Constraints:** Maximum once per conversation. If they reject the reframe, accept immediately and return to their thread. The reframe is an offer, not an argument.

### The Meta-Question (sufficiency escape hatch)

When thread-and-steer has exhausted visible threads but sufficiency hasn't passed, ask: "What should I have asked you that I didn't?" This surfaces blind spots the protocol can't reach through thread-following alone. Use at most once, and only when genuinely stuck.

## The Composition

*These rules govern the context block -- a non-user-facing artifact consumed by the explore engine. User-facing messages follow Voice & Register, not these rules.*

### Context Block Template

```text
PROBLEM:
[One sentence: what the user is trying to decide or understand]

SITUATION:
- [Key fact from intake, as structured bullet]
- [3-6 items max]

CONSTRAINTS:
- [What they've ruled out, tried and failed, resource/time/technical limits]
- [Use "None elicited" only if nothing was surfaced]

THE TENSION:
[1-2 sentences: the core tradeoff or uncertainty. The gap between what they want and what's blocking them.]

ASSUMPTIONS TO CHALLENGE:
- [Things the user is taking as given that might not be] [reframed], [untested], or [inferred]
- [inferred] = user didn't state this, interviewer connected dots from their answers. Explore should generate at least one direction that challenges an inference.
- [Use "None surfaced" if none identified]

DIMENSIONS:
1. [dimension] -- [what varies along this axis]
2. [dimension] -- [what varies]
3. [dimension] -- [what varies]
4. [dimension] -- [what varies]
```

**Token budget:** 200-500 tokens. Template labels consume ~60 tokens, leaving ~140-440 for content. SITUATION: 3-6 bullets. CONSTRAINTS: 2-4 bullets. DIMENSIONS: 4 (use 5-6 only if genuinely needed and under 450 tokens).

### Composition Rules

1. **200-500 tokens.** Cut anything that doesn't help generate a different direction.
2. **Strict ordering.** Problem first, dimensions last. Facts and constraints in the middle.
3. **Preserve the user's language for The Tension.** Compress facts freely.
4. **No Tension? Say so.** "No clear tradeoff identified -- the user is in exploratory mode."
5. **Constraints are negative dimensions.** Keep separate from positive situation facts.
6. **No narrative padding.** No "The user mentioned that..." Pure structured content.
7. **User vocabulary in content.** Template labels are structural; content uses their words. If they said "slow as hell," write "slow as hell."
8. **Unknowns must be explicit.** "None elicited," "Not validated," or "Inferred from input." Never silently omit.
9. **Implementation and blind spot check.** If no implementation thread ("now what?") or stakeholder-dynamics thread ("what's unsaid?") was covered during intake, infer one for ASSUMPTIONS TO CHALLENGE and tag it [untested]. AI systematically under-asks here.
10. **Skip-path composition.** When intake is skipped: populate PROBLEM from input; mark SITUATION and CONSTRAINTS as "Inferred from input -- not validated"; infer ASSUMPTIONS if possible; derive DIMENSIONS and TENSION from input alone. Flag: "Composed without intake -- lower confidence."
11. **Late user priority.** If the user adds a priority or correction in their last answer, incorporate it. This is refinement, not a new intake question.
12. **When inputs contradict, use the corrected version.** Note the original in ASSUMPTIONS only if the contradiction reveals an untested assumption.
13. **Post-output feedback loop.** If the user says explore output missed something, adjust TENSION or DIMENSIONS and re-run. Don't re-open intake. Max one re-run.

### How Context Block Maps to Explore

| Section | Consumed by | How |
|---|---|---|
| PROBLEM | explore.md | Seeds the brainstorm topic |
| SITUATION | explore-diverge.md | Background for all 3 directions |
| CONSTRAINTS | explore-diverge.md | Negative constraints on all directions |
| THE TENSION | explore-diverge + synthesis | The axis that makes directions different |
| ASSUMPTIONS TO CHALLENGE | explore-diverge (Direction 3) | Specific premises for the premise-challenge direction |
| DIMENSIONS | explore-diverge + synthesis | Forces structural differences between directions |

## Direction & Synthesis Quality Rules

1. **Directions must take different positions on THE TENSION.** Each direction is a different bet on a different unknown.
2. **Synthesis table must include "what you learn if it fails."** Different information value even in failure.
3. **Surface hybrid/composite paths.** Real decisions are rarely pure plays.
4. **Direction timelines must flag dependencies.** External actors (sales cycles, hiring, regulatory) get flagged.
5. **"Who disagrees" is mandatory in synthesis.** Name specific stakeholders and objections, not generic risks.

## Worked Examples

### Example 1: Well-specified input (1-2 questions)

**User input:** "Should we use Postgres or DynamoDB for our 10M-row analytics workload that needs sub-second queries?"

**Intake:**
> Q1: "Sub-second on 10M rows -- what's the query pattern? Dashboard aggregations, or ad-hoc slicing?"

User: "Mostly pre-built dashboards with 5-6 standard views, but the data team wants ad-hoc access too"

> Q2: "The data team's ad-hoc access -- how often does that happen today, and what breaks when it's slow?"

User: "Maybe twice a week, and honestly they just export to CSV and use pandas when the current system chokes"

*Sufficiency passes: clear decision, clear tension (standard dashboards vs. ad-hoc flexibility), two concrete facts (5-6 standard views, twice-weekly ad-hoc with CSV workaround).*

**Context block (187 tokens):**
```
PROBLEM:
Choose between Postgres and DynamoDB for a 10M-row analytics workload.

SITUATION:
- 10M rows, sub-second query requirement
- 5-6 pre-built dashboard views (primary use case)
- Data team needs ad-hoc access ~2x/week
- Current workaround: export to CSV, use pandas

CONSTRAINTS:
- Sub-second latency on standard views is non-negotiable

THE TENSION:
Optimizing for pre-built dashboard speed (DynamoDB's strength) vs. ad-hoc query flexibility (Postgres's strength). The data team's workaround suggests ad-hoc matters more than the team admits.

ASSUMPTIONS TO CHALLENGE:
- "10M rows requires a specialized solution" -- Postgres handles this natively with proper indexing [untested]
- "Sub-second and ad-hoc are competing requirements" [untested]

DIMENSIONS:
1. Query flexibility -- fixed views vs. arbitrary SQL
2. Operational complexity -- managed service vs. self-hosted tuning
3. Data team autonomy -- self-serve analytics vs. eng-mediated
4. Cost at scale -- per-query pricing vs. compute provisioning
```

### Example 2: Ambiguous input (4-5 questions)

**User input:** "I want to rethink our technical approach"

**Intake:**
> Q1: "What happened that made you want to rethink it?"

User: "We've been building for 18 months and we're still not shipping fast enough. Every feature takes 3x what we estimate."

> Q2: "The 3x estimates -- what's a recent one where that happened?"

User: "We estimated the billing integration at 2 weeks. Took 6. Half of it was fighting our own abstractions."

> Q3: "Fighting your own abstractions -- which ones?"

User: "The shared service layer. We built it early to avoid duplication but now every team has to understand the whole thing to change anything. And honestly the duplication we were avoiding wasn't that bad."

> Q4: "If you ripped out the shared service layer tomorrow, what breaks?"

User: "Auth and billing depend on it. Everything else could probably go back to owning their own code. I think the real question is whether we refactor gradually or just accept the duplication and move fast."

*Sufficiency passes: decision identified (refactor vs. accept duplication), tension clear (shared abstractions slowing delivery), concrete facts (6-week billing integration, auth/billing dependencies).*

**Context block (231 tokens):**
```
PROBLEM:
Whether to refactor the shared service layer gradually or accept duplication to ship faster.

SITUATION:
- 18 months in, features take 3x estimates
- Shared service layer built early to prevent duplication
- Every team must understand the whole layer to change anything
- Billing integration: estimated 2 weeks, took 6 -- half fighting abstractions
- Auth and billing depend on shared layer; everything else could decouple

CONSTRAINTS:
- Auth and billing can't decouple without significant work
- "The duplication we were avoiding wasn't that bad"

THE TENSION:
The shared service layer was built to prevent duplication but now causes 3x slowdowns. The duplication it prevents may cost less than the coupling it creates.

ASSUMPTIONS TO CHALLENGE:
- "We need a shared service layer to avoid duplication" -- the original duplication may have been cheaper [reframed]
- "Gradual refactoring is safer than ripping out" [untested]

DIMENSIONS:
1. Decoupling strategy -- gradual extraction vs. hard cutover vs. strangler pattern
2. Team autonomy -- shared ownership vs. service-per-team
3. Migration risk -- auth/billing first vs. leave hardest for last
4. Duplication tolerance -- zero-duplication vs. bounded-duplication policy
```

### Example 3: Reframe in action

**User input:** "how do I hire faster, we've had 3 senior eng roles open for 4 months"

**Intake:**
> Q1: "4 months on 3 roles -- what's happening in the pipeline? Getting candidates but losing them, or not getting candidates?"

User: "We get plenty of applicants but the good ones drop after the technical interview. Last month we lost two to competitors who moved faster."

> Q2: "The two you lost -- how long from first contact to offer?"

User: "About 5 weeks. The technical interview is a 2-day take-home plus a half-day onsite."

> Q3 (reframe): "You're optimizing the hiring speed, but 2-day take-home plus half-day onsite is 2.5 days of candidate time. What if the problem isn't how fast you move -- it's how much you're asking them to invest before they know if they want the job?"

User: "...huh. Yeah, the take-home was designed when we were a hot startup and candidates were willing to invest. We're not that anymore."

*Sufficiency passes: reframe landed, decision shifted from "hire faster" to "reduce candidate investment," concrete facts (5-week timeline, 2.5-day candidate commitment, 2 lost candidates).*

## What Changes from v5

| Change | v5 | v6 |
|---|---|---|
| Question structure | Free-form question bank | Thread-and-steer from user's answers |
| Track-specific questions | Separate fixed questionnaires | Eliminated -- domain variation via thread-and-steer |
| Continuity | Not required | Required via lexical pickup or presupposition |
| Question count | Unspecified | Sufficiency-based exit |
| Reframe mechanism | None | Once per conversation, when thread-following loops |
| Meta-question | Not used | Sufficiency escape hatch |
| Frame embedding | Confirmation requests ("is this right?") | Presupposition (state a frame, they'll correct it) |
| Implementation blind spot | Not addressed | Composition Rule #9 checks for it |
| Context block format | No token budget, no item limits | 200-500 tokens, per-section limits |
| Worked examples | None | 3 examples: well-specified, ambiguous, reframe |
| Validation history | Inline | Extracted to explore-intake-validation-log.md |

## Failure Modes

1. **Righting Reflex** -- AI solves before intake completes. Defense: structural prohibition (Delivery Rule #5).
2. **Interrogation Trap** -- rapid-fire without tracking. Defense: required continuity signal (Delivery Rule #2).
3. **Register Drift** -- LLM vocabulary elevates over the conversation. Defense: self-check on every message, anti-patterns above.
4. **Context Block Bloat** -- narrative padding. Defense: 200-500 token target, no-padding composition rules.
5. **Over-asking on Clear Questions** -- forcing 5 when 2 suffice. Defense: sufficiency-based exit.
6. **Implementation Blind Spot** -- AI under-asks about "now what?" Defense: Composition Rule #9.
7. **Confirmation Drift** -- final response becomes another elicitation round. Defense: max one correction pass, then explore runs.
8. **"I Already Knew This"** -- explore output didn't add value. Defense: post-output feedback loop (Composition Rule #13).

## Recommendations

1. **Rewrite `config/prompts/preflight-adaptive.md` to v6.** Enforce thread-and-steer, delivery rules, composition rules, sufficiency-based exit, skip-path, and 200-500 token limits.
2. **Update `.claude/skills/explore/SKILL.md` Step 2a.** Thread-and-steer as the only question-generation principle. Remove question bank references. Add reframe mechanism and meta-question.
3. **Add `ASSUMPTIONS TO CHALLENGE` to context block format.** Map into explore-diverge.md Direction 3.
4. **Run end-to-end verification** with one prompt per clarity tier. Success: sufficiency-based exit, context block <=500 tokens, directions structurally diverge along THE TENSION.

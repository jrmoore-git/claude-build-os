---
version: 4
last_updated: 2026-04-10
changelog: "v4: Premise-challenge constraint added — last direction MUST reject or reframe the question. Dimension enforcement tightened to explicit 3-of-N check. ERRC grid made optional (use when it adds insight). Questions adapted: keep Why now + Workaround (universal), 10x/analogy optional."
---
You will be given a question or problem statement. Previous directions have \
already been proposed.

PREVIOUS DIRECTIONS (you must NOT repeat or lightly vary any of these):

{previous_directions}

You must propose something STRUCTURALLY different. Not a cosmetic variation — \
a direction that makes different assumptions, targets different outcomes, \
or uses a different mechanism.

{dimensions}

**You are generating Direction {direction_number} of {total_directions}.**

**DIVERGENCE RULES based on position:**

**If this is NOT the last direction:** You must ACCEPT the question's \
premise but propose a fundamentally different MECHANISM. Same problem, \
different solution type. If previous directions proposed structural changes, \
propose a process change (or vice versa). If they proposed building, propose \
buying, outsourcing, or eliminating the need. Do NOT challenge the premise \
yet.

**If this IS the last direction ({total_directions} of {total_directions}):** \
You MUST reject or reframe the question's premise. Do not accept the problem \
as stated. Challenge what the question assumes is true, necessary, or worth \
solving. Your brainstorm must include at least 3 options that say "the \
question is wrong because..."

## Phase 1: Brainstorm

Brainstorm 6-8 options that satisfy the divergence requirement. For each, \
tag which dimensions differ from ALL previous directions. You need at \
least 3 dimensions different. Include at least 2 that feel uncomfortable \
or contrarian. Do not evaluate yet.

## Phase 2: Develop

Pick the most interesting and develop it fully.

{context}

**Optional: ERRC grid** — Use if it adds genuine insight for this type \
of problem. Skip if it feels forced.

| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| ... | ... | ... | ... |

Your direction must answer:
1. **Why now?** What changed that makes this possible or necessary?
2. **What's the workaround?** What are people doing without this?

And optionally (use when they add insight, skip when they feel forced):
3. **10x on which axis?** Name the one dimension.
4. **Adjacent analogy:** Where did this pattern work in another domain?

Rules:
- Be specific. Name the first concrete action, who it affects, what changes.
- Do not hedge. Make your case.
- Timelines must be grounded. If you state a duration ("6 months", "8 weeks"),
  cite what takes that long and why. Comparable evidence ("Team X did similar
  in Y weeks") beats invented estimates. If you don't have evidence for a
  timeline, say "timeline depends on [specific unknown]" — not a fake number.
- Do not invent multi-phase rollouts for comfort. Each phase must produce a
  decision signal the previous phase couldn't. "Shadow mode → staging →
  production" is three phases; justify why two wouldn't work.
- Keep Phase 2 under 800 words.

Output format:

## Brainstorm
[6-8 one-line directions with dimension tags]

## Direction: [one-line name]

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| ... | ... | ... | ... |

## The Argument
[Why this is the right direction, answering the 4 questions above.]

## First Move
[What you'd do first.]

## Why This Beats the Alternatives
[What's wrong with the obvious approaches AND the previous directions.]

## Biggest Risk
[The one thing most likely to kill this.]

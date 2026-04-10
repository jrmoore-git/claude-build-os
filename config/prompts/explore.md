---
version: 1
last_updated: 2026-04-10
changelog: "v1: Added two-phase thinking (brainstorm then commit), 5 strategic questions, constraint-based framing, context slot. Research-backed: split diverge/commit, analogy injection, premise-challenging."
---
You will be given a question or problem statement about a product, strategy, \
or architectural decision. Your job is to propose a sharp, specific direction.

Do this in TWO PHASES. Do not skip Phase 1.

## Phase 1: Brainstorm (do NOT evaluate yet)

List 8-10 possible directions. Each is one sentence. Include:
- At least 2 that are obvious/conventional
- At least 3 that feel weird, risky, or unfashionable
- At least 1 that no mainstream VC would fund
- At least 1 that reframes the problem entirely (the question is wrong)

Do not evaluate or rank them. Just list.

## Phase 2: Develop the most interesting direction

Pick the direction from your brainstorm that is MOST INTERESTING — not \
most safe, not most obvious. Develop it into a full argument.

{context}

Your developed direction MUST answer these 5 questions:
1. **Why now?** What specific change (technology, behavior, market, \
regulation) makes this possible today but not 2 years ago?
2. **What's the workaround?** What are potential users doing today without \
this product? Workarounds reveal proven demand.
3. **Moment of abandonment:** Where do users quit the current workflow? \
Design backward from that point — the product's job is to skip past it.
4. **10x on which axis?** Not "better overall" — name the ONE dimension \
where this is 10x better. Is it good enough on every other dimension, \
or does a weakness kill adoption?
5. **Adjacent analogy:** Name a product in a different market where this \
same pattern worked. What was the mechanism, and why does it transfer?

Rules:
- Be specific. Name the first customer, first use case, first dollar.
- Do not hedge. Make your case.
- Keep Phase 2 under 800 words. Phase 1 is a short list.

Output format:

## Brainstorm
[8-10 one-line directions]

## Direction: [one-line name]

## The Argument
[Why this is the right direction, answering the 5 questions above.]

## First Move
[What you'd build or do first. Specific enough to start next week.]

## Why This Beats the Alternatives
[What's wrong with the 2-3 most obvious approaches.]

## Biggest Risk
[The one thing most likely to kill this. Be honest.]

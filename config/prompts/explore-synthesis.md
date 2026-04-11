---
version: 3
last_updated: 2026-04-10
changelog: "v3: Domain-agnostic rewrite. Replaced hardcoded product clustering dimensions (customer/product form/business model/distribution) with {dimensions} variable. Kept fork-first format, 150-word cap, comparison table."
---
You are synthesizing {n} independent proposals for the same question. \
Each takes a different direction.

Your job: distill these into EXACTLY 3 bets and present them in a \
specific format that makes the real choice clear.

## Step 1: Cluster and verify differentiation

From the {n} proposals, cluster into exactly 3 bets. The 3 bets MUST \
differ on at least 2 of the following dimensions:

{dimensions}

Escalating scope (same thing but bigger) is NOT a distinct bet. If all \
3 bets take the same approach with minor variations, you have \
failed — go back and recombine until 2+ dimensions differ.

Bet A MUST be the obvious/direct answer to the question.

## Step 2: Fork statement

State the fork FIRST, before any details:

"The real choice is [Bet A: name] vs [Bet B: name] vs [Bet C: name]."

One sentence. This is the headline.

## Step 3: Bet details (150 words HARD CAP per bet)

For each bet, write EXACTLY this structure in 150 words or fewer:

**Bet [A/B/C]: [Name]**
[Argument: why this bet, what makes it work]
**First move:** [What you'd do next week]
**Sacrifice:** [What you give up by choosing this path]

150 words is a hard cap. Count them. Cut ruthlessly.

## Step 4: Comparison table

| | Timeline | Risk | What you learn | Strategic sacrifice |
|---|----------|------|----------------|---------------------|
| **Bet A** | ... | ... | ... | ... |
| **Bet B** | ... | ... | ... | ... |
| **Bet C** | ... | ... | ... | ... |

Column definitions:
- **Timeline**: How long until you know if this works? Must be grounded in
  evidence (comparable projects, team velocity, known scope). If the timeline
  is invented, write "unknown — depends on [X]" not a fake number.
- **Risk**: What could go wrong in execution? (operational/execution risk)
- **What you learn**: What do you know after this that you don't know now?
- **Strategic sacrifice**: What position or optionality you give up by \
choosing this path? (strategy, not execution)

Risk = execution. Sacrifice = strategy. Do NOT blur them.

## Output format

```
## The Fork

[Fork statement]

## Bet A: [Name]
[150 words max]

## Bet B: [Name]
[150 words max]

## Bet C: [Name]
[150 words max]

## Comparison

[Table]
```

Keep the entire output under 700 words. Be direct. No preamble.

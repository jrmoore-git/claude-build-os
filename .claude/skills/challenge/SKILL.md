---
name: challenge
description: "Principal engineer asking 'should we build this?' Cross-model gate before /plan. Prevents scope creep and unnecessary abstractions."
user-invocable: true
---

# /challenge — Should We Build This?

Cross-model gate that evaluates whether proposed work is necessary and appropriately scoped. Run before `/plan` for any non-trivial change.

## Procedure

### Step 1: Get topic

If the user provided a topic as an argument, use it. Otherwise ask: "What's the topic name for this challenge? (e.g., `review-skill-restructure`)"

### Step 2: Check for prior work

Check for a `/think` brief:
```bash
test -f tasks/<topic>-think.md && echo "found" || echo "none"
```

If found, read it — this provides problem context.

### Step 3: Ensure proposal exists

Check for `tasks/<topic>-proposal.md`:
```bash
test -f tasks/<topic>-proposal.md && echo "found" || echo "none"
```

If missing:
- If a think brief exists, synthesize a brief proposal (1-2 paragraphs) covering: what problem, why now, proposed approach.
- If no think brief either, ask the user: "Describe what you want to build and why."
- Write to `tasks/<topic>-proposal.md`.

### Step 4: Enrich context

Pull relevant lessons and decisions:
```bash
python3 scripts/enrich_context.py --proposal tasks/<topic>-proposal.md
```

If enrichment returns results, create a temp file with the proposal + a `## Prior Context` section appended. Use the temp file as input to the challenge. Original proposal stays untouched.

### Step 5: Run cross-model challenge

Select personas based on the proposal content:
- **Base personas (always):** architect, security, pm
- **Add `product` IF** the proposal introduces a new user-facing feature or changes user workflow (NOT for refactors, infrastructure, or backend-only changes)
- **Add `design` IF** the proposal touches frontend files (CSS, UI components) (NOT for backend-only changes)

```bash
python3 scripts/debate.py challenge \
  --proposal <enriched or original proposal> \
  --personas architect,security,pm[,product][,design] \
  --output tasks/<topic>-challenge.md
```

Parse JSON stdout. If status is `"ok"` or `"partial"`, continue to Step 6. If all challengers failed, fall through to Step 5b.

### Step 5b: Degraded fallback

If `debate.py` fails entirely (connection error, timeout, all models down):

Self-challenge with these 4 questions:
1. What problem are we solving? What evidence exists that it matters?
2. What's the simplest version that tests the hypothesis?
3. What should we explicitly NOT build?
4. What is the cheapest test of whether this works?

Write answers to `tasks/<topic>-challenge.md` with frontmatter. Include a `MATERIAL` tag on any substantive concern so `artifact_check.py` recognizes this as a valid challenge artifact:
```yaml
---
debate_id: <topic>
created: <ISO datetime>
phase: challenge
status: degraded
producer: claude-opus
note: "Cross-model debate unavailable. Single-model self-challenge."
---
```

### Step 6: Synthesize recommendation

Read `tasks/<topic>-challenge.md`. Based on the findings, recommend one of:

- **proceed** — No material objections. Go to `/plan`.
- **simplify** — Valid idea, but scope needs reduction. State what to cut.
- **pause** — Needs more information or prerequisites. State what's missing.
- **reject** — Cost exceeds benefit or conflicts with existing architecture. State why.

Display:
```
## Challenge Result: <PROCEED|SIMPLIFY|PAUSE|REJECT>

<1-3 sentence summary>

Artifacts: tasks/<topic>-challenge.md
Next: /plan <topic>
```

### Step 7: Handoff

- If **proceed**: "Run `/plan <topic>` to generate the build plan."
- If **simplify**: "Revise your approach, then `/plan <topic>`."
- If **pause** or **reject**: "Address the concerns above before proceeding."

---
name: think
description: "Senior engineer pushing back on assumptions before planning. Structured brainstorming for new features; lightweight pass-through for bugfixes and docs."
user-invocable: true
---

# /think — Structured Brainstorming

Push back on assumptions, clarify the real problem, then produce a brief that `/plan` consumes.

## Pushback Posture

When responding to the user during this skill, follow these patterns:

- Instead of agreeing with a proposal, state what you'd push back on first.
- Instead of "that could work", state whether it WILL work and what's missing.
- Instead of "there are many approaches", pick one and say what evidence would change your mind.
- Instead of hedging ("you might want to consider..."), take a position and defend it.

Your job is to stress-test the idea, not validate it. Be direct, specific, and constructive. For low-risk requests (bugfixes, docs, tests), keep pushback minimal and focus on clarifying the fix.

## Procedure

### Step 1: Context pull

Read current project state for grounding:
```bash
cat docs/current-state.md
```

Read the last 3 session-log entries:
```bash
tail -100 tasks/session-log.md
```

If the user provided a topic, search for relevant lessons:
```bash
python3 scripts/recall_search.py <topic keywords> --files lessons,decisions
```

### Step 2: Triage

Classify the request before deciding how hard to push back:

- **Bugfix / test / docs / trivial refactor** (changes confined to existing behavior, no new interfaces or architecture) → Skip to Step 4 (synthesize brief). Ask only: "What's broken and what's the fix?" No forcing questions needed.
- **New feature / abstraction / scope expansion / design change** (new interfaces, new user-visible behavior, architectural shifts) → Continue to Step 3.

If unclear, ask: "Is this a fix for something broken, or a new capability?" One question, then route.

### Step 3: Forcing questions

Work through these questions with the user. Ask them one at a time — wait for an answer before asking the next. Skip any that are already answered by prior context.

1. **"What outcome are you after?"** — Get the goal, not the solution. If they say "build X", ask what breaks without X.
2. **"What's the current workaround? What does it cost?"** — Tests urgency. If there's no workaround and no cost, it may not be worth building.
3. **"What's the smallest version that tests whether this works?"** — Push toward MVP. Reject scope that isn't needed to validate the core idea.
4. **"How does this serve the user?"** — Reframe in terms of the user's workflow. If this is a net-new feature or product capability, briefly consider: does this reduce app-switching? Does it make the core loop faster? Does it close a gap that forces the user to open another tool? Skip this question entirely for bugfixes, refactors, docs, and infrastructure work.
5. **"What does the product become?"** (new features only — NEVER for bugfixes, refactors, docs, or infrastructure) — Zoom out one level. If this feature ships and succeeds, how does it change what the product IS? Does it move the product closer to its core vision? Or does it add surface area without advancing that vision? One sentence is enough — the point is to gut-check alignment, not write a PRD.

**Escape hatch:** If the user declines to answer a forcing question in two separate messages (e.g., "just build it", "I already know what I want", or answering with a dismissive one-liner twice), ask the single most critical remaining question, then move to Step 4. Don't block progress — the brief will reflect whatever gaps remain as `[UNKNOWN]`.

### Step 4: Synthesize brief

After the conversation, extract the user's topic name (ask if unclear). Write `tasks/<topic>-think.md`:

```markdown
## Problem Statement
<What the user is actually trying to solve — in their words, refined>

## Proposed Approach
<The approach that emerged from discussion>

## Key Assumptions
- <assumption 1> — verified? <yes/no/untested>
- <assumption 2> — verified? <yes/no/untested>

## Risks
- <risk 1>
- <risk 2>

## Simplest Testable Version
<The MVP that tests the core hypothesis with minimum effort>
```

**Completeness check:** Before writing, verify the brief has non-empty content for Problem Statement, Proposed Approach, and Simplest Testable Version. If any is missing, flag it to the user: "The brief is missing [field] — want to fill it in or leave it flagged as unknown?" Write the brief either way, marking gaps with `[UNKNOWN — not discussed]`.

### Step 5: Handoff

Tell the user:
- "Brief written to `tasks/<topic>-think.md`."
- "Run `/plan` when ready to generate the implementation plan."

## Output

The brief file is informal — no YAML frontmatter required. It's input for `/plan`, not a gate artifact.

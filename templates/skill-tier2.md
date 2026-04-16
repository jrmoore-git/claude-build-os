---
name: SKILL_NAME
description: "One-line summary of what this skill does. Use when [trigger condition]. Defers to: /other-skill for [what]."
version: 1.0.0
user-invocable: true
---

# /SKILL_NAME — Short Title

One-sentence summary of what this skill does and why it exists.

## Procedure

### Step 1: [First action]

[What to do, what to check, what to read.]

### Step 2: [Second action]

[What to do next. If this skill calls debate.py, include the invocation here.]

<!-- If this skill calls debate.py, uncomment and fill in:
```bash
python3.11 scripts/debate.py [subcommand] \
  --proposal tasks/<slug>-proposal.md \
  --output tasks/<slug>-output.md
```
If debate.py fails or is unavailable, fall back to [describe fallback behavior].
-->

### Step 3: [Output]

[Write artifacts to disk. Format the conversation output.]

## Safety Rules

- NEVER [describe what this skill must never do].
- Do not [second prohibition relevant to this skill's domain].
- **Output silence** — Do not emit text between tool calls. Single formatted output at the end only.

## Output Format

Primary artifact: `tasks/<slug>-[artifact].md`

Conversation output:
```
[Define the exact shape of what the user sees at the end.]
```

## Completion

Report status:
- **DONE** — All steps completed successfully.
- **DONE_WITH_CONCERNS** — Completed with issues to note.
- **BLOCKED** — Cannot proceed. State the blocker.
- **NEEDS_CONTEXT** — Missing information needed to continue.

---
name: wrap-session
description: "End-of-session wrap-up. Checks doc hygiene, writes docs/current-state.md and tasks/handoff.md, appends to tasks/session-log.md, and commits everything."
metadata:
  {
    "requires": { "bins": ["git"] },
  }
---

# Wrap Session

End-of-session documentation and commit. Run when the user says "wrap up" or "end session."

## Safety Rules

- **NEVER skip the commit.** Documentation without a commit is lost between sessions.
- **NEVER fabricate status.** Only report what you can verify from git diff, file contents, and conversation context.
- **NEVER output full file contents** — brief confirmation of what was written to each file.
- **If there are uncommitted code changes**, commit those first (separate commit), then commit the wrap docs.

## Procedure

### Step 1 — Check doc hygiene

Run to see what changed this session:

```bash
git diff HEAD --name-only 2>/dev/null; git status --short
```

Check specifically:

- `tasks/lessons.md` — if new patterns were learned this session but this file was NOT modified, warn: "lessons.md not updated — [what should be added]"
- `tasks/decisions.md` — if architectural decisions were made this session but this file was NOT modified, warn: "decisions.md not updated — [what should be added]"

Report: "lessons.md updated" or "lessons.md NOT updated"
Report: "decisions.md updated" or "decisions.md NOT updated"

### Step 2 — Gather change summary

```bash
git diff HEAD --stat 2>/dev/null
git log --oneline -5
```

Produce a plain-language bullet list: what was built or fixed, not file names. Example: "Fixed timezone bug in notification skill" not "Modified skills/notification/SKILL.md".

### Step 3 — Identify blockers and next action

Read recent session context and:

```bash
head -60 tasks/todo.md 2>/dev/null || true
```

Identify:
- **Blockers:** what is explicitly blocked (waiting on user, external dependency, deferred)
- **Next action:** the single most important thing to do at the start of the next session

### Step 4 — Write docs/current-state.md

Overwrite `docs/current-state.md` with:

```
# Current State — YYYY-MM-DD

## What Changed This Session
- [plain-language bullet per logical change, not per file]

## Current Blockers
- [blocker 1] — [what's needed to unblock]
- None identified (if none)

## Next Action
[one sentence — the first thing next session should do]

## Recent Commits
[last 3 from: git log --oneline -3]
```

### Step 5 — Write tasks/handoff.md

Overwrite `tasks/handoff.md` with:

```
# Handoff — YYYY-MM-DD

## Session Focus
[one sentence: what this session accomplished]

## Decided
- [key decisions made, or "None"]

## Implemented
- [what was built or changed]

## NOT Finished
- [what remains, blockers, or "Nothing outstanding"]

## Next Session Should
1. [most important first action]
2. [second if applicable]

## Key Files Changed
[git diff HEAD --name-only output, trimmed to relevant files]

## Doc Hygiene Warnings
[any warnings from Step 1, or "None"]
```

### Step 6 — Append to tasks/session-log.md

Append to `tasks/session-log.md` (do not overwrite — append after the last `---`):

```

---

## YYYY-MM-DD — [session topic in 5-8 words]

**Decided:**
- [bullets, or "None"]

**Implemented:**
- [bullets]

**Not Finished:** [what remains or blockers, one line]

**Next Session:** [first thing to do]

```

### Step 7 — Commit

Stage and commit all wrap docs:

```bash
git add docs/current-state.md tasks/handoff.md tasks/session-log.md
# Also stage lessons.md / tasks/decisions.md if they were updated this session but not yet committed
git status --short
git commit -m "Session wrap YYYY-MM-DD: [one-line summary]

No doc updates beyond session-log, handoff, and current-state.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

Report the commit hash and: "Session wrapped. Next: [next action from Step 3]."

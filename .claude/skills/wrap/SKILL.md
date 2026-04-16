---
name: wrap
description: "End-of-session wrap-up. Use when the user says 'wrap up', 'end session', 'wrap it up', or 'close out'. Checks doc hygiene, writes docs/current-state.md and tasks/handoff.md, appends to tasks/session-log.md, and commits everything."
user-invocable: true
version: 1.0.0
lint-exempt: ["output-silence"]
metadata:
  {
    "emoji": "📦",
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

- `tasks/lessons.md` — if new patterns were learned this session but this file was NOT modified, warn: "⚠ lessons.md not updated — [what should be added]"
- `tasks/decisions.md` — if architectural decisions were made this session but this file was NOT modified, warn: "⚠ decisions.md not updated — [what should be added]"

Report: "✓ lessons.md updated" or "⚠ lessons.md NOT updated"
Report: "✓ decisions.md updated" or "⚠ decisions.md NOT updated"

### Step 1b — Governance check — session-scoped (what did THIS session create or break?)

Checks only governance items this session touched. Not a global scan.

```bash
# What governance files did this session modify?
gov_changed=$(git diff HEAD --name-only -- tasks/lessons.md tasks/decisions.md 2>/dev/null)

# If no governance files changed, skip entirely — nothing to check
```

**If governance files changed**, run targeted checks on the diff:

```bash
# Extract lesson IDs added/modified this session
new_lessons=$(git diff HEAD -- tasks/lessons.md | grep '^+|' | grep -oE 'L[0-9]+' | sort -u)

# Extract decision IDs added/modified this session
new_decisions=$(git diff HEAD -- tasks/decisions.md | grep '^+|' | grep -oE 'D[0-9]+' | sort -u)
```

**For each new/modified item, check:**
- Lessons with `[Resolved` tag still in active table → "archive before wrapping?"
- Lessons with `[PROMOTED -> rules/X.md]` → verify `rules/X.md` exists
- Lessons that say "promoted to" in text but lack `[PROMOTED ->]` tag → flag missing tag
- Decisions with `Superseded by: D##` → verify D## exists
- New cross-references → verify targets exist

**Output only if something's wrong:**
```
## Session Governance Check
- New/modified: L19, L21, D45
- ⚠ L17 has [Resolved] tag but is still in active table — archive?
- ⚠ L21 says "promoted to rules/X.md" but [PROMOTED ->] tag is missing
```

If all new items are well-formed: emit nothing.

**Also check global limits** (cheap — always run):
- Active count >25: "⚠ Lessons at N/30 — approaching limit."
- Active count >30: "⚠ Lessons OVER target (N/30) — triage needed."
- Days since last full scan >7: "⚠ Full /healthcheck overdue (N days) — auto-triggering." Same `[healthcheck]` marker in session-log that `/start` checks — whichever runs first resets the clock for both.

**Auto-trigger escalation:** If this session added 3+ new governance items (`new_lessons` + `new_decisions` count ≥ 3), run the targeted `/healthcheck` scan (not full — just the items from this session plus their cross-refs). Escalate to full scan only if the targeted check finds cross-ref integrity issues. Also auto-trigger full scan if >7 days since last `[healthcheck]` marker (catches the case where `/start` was skipped).

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
- **Blockers:** what is explicitly blocked (waiting on the user, external dependency, deferred)
- **Next action:** the single most important thing to do at the start of the next session

### Step 4 — Write docs/current-state.md

**Read each file immediately before writing it.** Parallel sessions' Stop hooks can modify `current-state.md` and `handoff.md` between tool calls (via `mark_current_state_stale()`). A Read from Step 1 will be stale by the time you Write here. Read → Write must be adjacent with no intervening tool calls.

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
[any ⚠ warnings from Step 1, or "None"]
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

### Step 6b — BuildOS sync check

Check if any framework files diverged from the BuildOS repo this session:

```bash
bash scripts/buildos-sync.sh --dry-run 2>/dev/null | grep -E 'CHANGED|NEW|Summary'
```

If any files are CHANGED or NEW, report:
"⚠ BuildOS out of sync — N framework files changed. Run `bash scripts/buildos-sync.sh --push` to update."

If all unchanged or the script doesn't exist, skip silently.

### Step 7 — Clean up worktrees

Prune stale agent worktrees that have no unique work:

```bash
git worktree list
```

For each worktree:
- If it has **0 commits ahead of main** and **no uncommitted changes**: remove it with `git worktree remove <path>` and delete the branch with `git branch -D <branch>`.
- If it has **uncommitted changes**: warn "⚠ worktree <name> has uncommitted work — triage before removing."
- If it has **commits ahead of main**: warn "⚠ worktree <name> has N unmerged commits — triage before removing."

Only auto-remove worktrees that are clean and fully merged. Report what was cleaned and what was left.

## Output Format

Progress bullets during each step (doc hygiene warnings, change summaries, blocker identification). Final output: commit hash and next-action recommendation.

### Step 8 — Commit

Stage and commit all wrap docs:

```bash
git add docs/current-state.md tasks/handoff.md tasks/session-log.md
# Also stage lessons.md / tasks/decisions.md if they were updated this session but not yet committed
git status --short
git commit -m "Session wrap YYYY-MM-DD: [one-line summary]

No doc updates beyond session-log, handoff, and current-state.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

Report the commit hash and: "Session wrapped. Next: [next action from Step 3]."

## Completion

Report status:
- **DONE** — Session wrapped, docs committed, next action identified.
- **DONE_WITH_CONCERNS** — Wrapped with issues (e.g., uncommitted code changes, stale governance items).
- **BLOCKED** — Cannot wrap. State the blocker.
- **NEEDS_CONTEXT** — Missing information needed to write accurate wrap docs.

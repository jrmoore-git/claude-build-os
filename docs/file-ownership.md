# File Ownership Protocol

Which skill owns which file, and in what order skills run at session close.

## File owners

| File | Owner skill | Other skills may... |
|------|-------------|---------------------|
| `tasks/handoff.md` | `/handoff` | Read. `/sync` may flag incomplete work but does not write the full handoff. |
| `tasks/session-log.md` | `/handoff` | Append only (never overwrite previous entries). |
| `docs/current-state.md` | `/sync` | `/handoff` may also update if state changed and `/sync` wasn't run. |
| `tasks/decisions.md` | `/capture` or `/sync` | Append only. Entries are numbered and never modified after writing. |
| `tasks/lessons.md` | `/capture` or `/sync` | Append only. Promote recurring lessons to `.claude/rules/` and archive. |
| `docs/project-prd.md` | `/sync` | Read by `/recall`, `/plan`, `/review`. |
| `.claude/rules/*.md` | Manual or `/setup` | Read by Claude automatically. Promoted from lessons.md when recurring. |
| `CLAUDE.md` | Manual or `/setup` | Read by Claude automatically on every turn. |
| `tasks/plan-*.md` | `/plan` | Read by `/review`. Deleted after successful implementation (optional). |
| `tasks/review-*.md` | `/review` | Read by `/review-x`. |
| `tasks/*-challenge.md` | `/challenge` | Read by `/plan` Phase 0. Stale after 7 days. |

## Session-log vs handoff

These serve different purposes and should not be confused:

- **`session-log.md`** — Historical record. Append-only. What happened, when, and what was decided. Never overwritten.
- **`handoff.md`** — Forward-looking transfer state. Overwritten each session. What the next session needs to know and do.

Both capture "what's done" and "what's not done" — but session-log records it for posterity, while handoff records it for action.

## Session close sequence

Run skills in this order at session end:

```
1. /sync     — update source-of-truth docs (decisions, lessons, PRD, current-state)
2. /handoff  — read updated state, write forward-looking handoff
3. git commit
```

Running `/handoff` before `/sync` produces a stale handoff. Running `/sync` after `/handoff` may update docs that the handoff doesn't reflect.

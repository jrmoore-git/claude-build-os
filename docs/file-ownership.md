# File Ownership Protocol

Which skill owns which file, and in what order skills run at session close.

## File owners

| File | Owner skill | Other skills may... |
|------|-------------|---------------------|
| `tasks/handoff.md` | `/wrap` | Overwritten each session close. |
| `tasks/session-log.md` | `/wrap` | Append only (never overwrite previous entries). |
| `docs/current-state.md` | `/wrap` | `hook-stop-autocommit.py` injects a `⚠ STALE` marker on unclean session exit. |
| `tasks/decisions.md` | `/log` or `/sync` | Append only. Entries are numbered and never modified after writing. |
| `tasks/lessons.md` | `/log` or `/sync` | Append only. Promote recurring lessons to `.claude/rules/` and archive. |
| `docs/project-prd.md` | `/sync` | Read by `/start`, `/plan`, `/review`. |
| `.claude/rules/*.md` | Manual or `/setup` | Read by Claude automatically. Promoted from lessons.md when recurring. |
| `CLAUDE.md` | Manual or `/setup` | Read by Claude automatically on every turn. |
| `tasks/plan-*.md` | `/plan` | Read by `/review`. Deleted after successful implementation (optional). |
| `tasks/review-*.md` | `/review` | Read by `/review --second-opinion`. |
| `tasks/*-challenge.md` | `/challenge` | Read by `/plan` Phase 0. Stale after 7 days. |

## Session-log vs handoff

These serve different purposes and should not be confused:

- **`session-log.md`** — Historical record. Append-only. What happened, when, and what was decided. Never overwritten.
- **`handoff.md`** — Forward-looking transfer state. Overwritten each session. What the next session needs to know and do.

Both capture "what's done" and "what's not done" — but session-log records it for posterity, while handoff records it for action.

## Session close sequence

Run `/wrap` at session end. It handles everything in one command:

1. Check doc hygiene (lessons.md, decisions.md updated?)
2. Write `docs/current-state.md`
3. Write `tasks/handoff.md`
4. Append to `tasks/session-log.md`
5. Check BuildOS sync status
6. Commit all wrap docs

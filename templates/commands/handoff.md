# Write Session Handoff

Write a handoff document so the next session can pick up where you left off.

## Procedure

1. Read the current `tasks/handoff.md` if it exists
2. Write an updated handoff covering:

```markdown
## Current focus
[What we were working on this session]

## What's done
- [Completed items with evidence]

## What's not done
- [Remaining items]
- [Blockers]

## Next session should
1. [First concrete action]
2. [Second concrete action]

## Open questions
- [Anything unresolved]
```

3. Also update `docs/current-state.md` if project truth changed
4. Also update `tasks/decisions.md` if decisions were made this session
5. Also update `tasks/lessons.md` if surprises occurred

## Rules
- The handoff must be concrete. "Continue working" is not a handoff.
- Include what was verified and what was not.
- If work is incomplete, say exactly where you stopped and what the next step is.

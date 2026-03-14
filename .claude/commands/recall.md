# Session Recall

Load relevant context before starting work. This is the "retrieve before planning" rule made executable.

## Procedure

1. **Read the handoff** — if `tasks/handoff.md` exists, read it. This tells you what the last session was working on, what's unfinished, and what to do next.

2. **Read current state** — if `docs/current-state.md` exists, read it. This tells you what is true right now: blockers, recent changes, verified state.

3. **Scan recent decisions** — if `tasks/decisions.md` exists, read the last 5-10 entries. These are settled choices that should not be relitigated.

4. **Scan relevant lessons** — if `tasks/lessons.md` exists, scan for lessons related to the area you're about to work in. Don't load all lessons — load relevant ones.

5. **Read relevant PRD sections** — if `docs/project-prd.md` exists and you know what area you're working in, read only the relevant section. Don't load the whole PRD.

## Output

After loading context, produce a brief orientation:

```
## Session Context
- **Last session:** [what happened, from handoff]
- **Current state:** [blockers, recent changes]
- **Relevant decisions:** [D## titles that apply]
- **Relevant lessons:** [L## titles that apply]
- **Starting point:** [what to do first]
```

## Rules
- Do NOT load everything. Load what's relevant to this session's work.
- If no handoff exists, say so — this is the first session or context was lost.
- If the user hasn't said what they want to work on, ask before loading context.
- Keep the orientation to 10 lines or fewer. Brevity is the point.

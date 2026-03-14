---
name: triage
description: Classify incoming information and route it to where it belongs
user-invocable: true
---

# Triage Incoming Information

Classify incoming information and route it to where it belongs.

## When to use
Run when you have new inputs to process: meeting notes, research findings, brainstorm output, feedback, bug reports, or any unstructured information that needs to be organized.

## Procedure

1. **Gather inputs** — Read the specified source (file, clipboard, conversation history, or inbox)

2. **Classify each item** as one of:
   - **Decision** — a choice that was made → add to `tasks/decisions.md`
   - **Lesson** — a mistake, surprise, or pattern → add to `tasks/lessons.md`
   - **Task** — something that needs to be done → add to the project's task tracker
   - **Reference** — useful information to keep → route to the relevant doc
   - **Noise** — not actionable, not worth keeping → skip

3. **Route** — move each item to its destination with an assertion-style title

4. **Report** — summarize what was routed where

## Output

```
## Triage Results
- Decisions: [count] → tasks/decisions.md
- Lessons: [count] → tasks/lessons.md
- Tasks: [count] → [destination]
- Reference: [count] → [destinations]
- Skipped: [count]
```

## Rules
- Every item is either routed, explicitly deferred with a reason, or explicitly skipped. No items are silently ignored.
- Use assertion-style titles: "JWT cookie auth bridges Django sessions cleanly" not "Authentication notes"
- If unsure where something belongs, ask the user rather than guessing.

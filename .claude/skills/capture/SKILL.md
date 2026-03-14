---
name: capture
description: Extract decisions, lessons, and action items from conversations or documents
user-invocable: true
---

# Capture Decisions and Lessons

Extract decisions, lessons, and action items from a conversation, meeting, or document.

## When to use
After meetings, design sessions, code reviews, or any conversation where decisions were made or lessons emerged. These are the most common source of institutional knowledge that never makes it to disk.

## Procedure

1. **Read the source** — the user will point you to a conversation, transcript, document, or describe what happened

2. **Extract decisions** — any choice that was made, with rationale
   - Format: assertion-style title, decision, rationale, alternatives considered, date
   - Add to `tasks/decisions.md` with the next available number

3. **Extract lessons** — any surprise, mistake, or pattern worth remembering
   - Format: assertion-style title, source, rule
   - Add to `tasks/lessons.md` with the next available number

4. **Extract action items** — anything that needs to be done
   - List with owner (if known) and deadline (if stated)
   - Present to the user for task tracking

5. **Report** — summarize what was captured

## Output

```
## Captured from [source]
- Decisions: [count] added to decisions.md
- Lessons: [count] added to lessons.md
- Action items: [count] (listed below)

### Action Items
1. [Action] — [Owner] — [Deadline or "no deadline stated"]
```

## Rules
- Do not invent decisions or lessons that weren't actually stated or implied in the source.
- Use assertion-style titles: the title IS the takeaway.
- If the source is ambiguous about whether something was decided, flag it as "possible decision — confirm with team."
- Dates matter. Record when decisions were made, not just what was decided.

---
name: plan
description: Research the system, then write a plan to disk before executing
user-invocable: true
---

# Plan Before Building

Research the system, then write a plan to disk before executing.

## When to use this command

Use `/plan` when:
- More than 3 files may change
- Auth, security, state transitions, or integrations are involved
- User-facing behavior is changing
- Multiple tracks need coordination
- You're unsure about the approach

Skip `/plan` for: one-line fixes, obvious edits, trivial config changes.

## Procedure

### Phase 1: Research
1. Read the relevant code, docs, and existing patterns
2. Understand what exists before proposing changes
3. Check `tasks/lessons.md` for relevant gotchas
4. Check `tasks/decisions.md` for settled choices in this area

### Phase 2: Write the plan
Create a plan file at `tasks/plan-[topic].md` with:

```markdown
# Plan: [what you're doing]

## What and why
[One paragraph. What are we building/changing and why.]

## Files affected
[List every file this will touch]

## Approach
[Numbered steps. Each step is a concrete action.]

## What done looks like
[Specific, verifiable criteria. Not "it works" — how you prove it works.]

## Risks
[What could go wrong. What's the rollback if it does.]
```

### Phase 3: Verify
Present the plan to the user. Wait for approval before executing.

## Rules
- The plan goes to disk, not just conversation. Disk survives compaction.
- The plan should be short. If it exceeds one page, the task should be split.
- Do not start implementing until the plan is reviewed.
- If something goes wrong during execution, stop and re-plan. Don't push through a broken plan.

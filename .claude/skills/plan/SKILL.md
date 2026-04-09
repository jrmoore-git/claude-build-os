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

### Phase 0: Challenge check
Before planning, assess whether the proposed work introduces **any** of:
- **New abstractions** (classes, modules, services, wrappers)
- **New dependencies** (packages, external APIs)
- **New infrastructure** (config surfaces, schema changes, feature flags)
- **Generalization** (making something "reusable," "extensible," "future-proof")
- **Scope expansion** (work beyond the stated ask)

A single trigger is enough — this is intentionally aggressive. False positives (unnecessary challenge) cost minutes; false negatives (skipped challenge on something that needed it) cost hours of rework. If any apply:
1. Check for `tasks/<topic-slug>-challenge.md` where `topic_slug` matches exactly
2. Verify artifact is less than 7 days old and has all required sections
3. Read the recommendation:
   - `proceed` → continue to Phase 1
   - `simplify` → plan must implement the artifact's "Simpler alternative" section, not the original scope. Confirm with user before proceeding.
   - `pause` → hard stop. Surface what evidence is needed before planning can proceed.
   - `reject` → hard stop. Do not plan. Surface the rejection rationale.
4. If artifact is missing, stale, or malformed → run `/challenge` first, then return

**Skip this check for:** bugfixes, test-only changes, docs, refactors that reduce abstractions, `[TRIVIAL]` (≤2 files, no new abstractions, describable in one sentence).

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

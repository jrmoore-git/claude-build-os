---
title: "Autobuild Mode: Autonomous Build-Test-Iterate Loop"
type: proposal
status: draft
date: 2026-04-16
---

# Proposal: Autobuild Mode for Build OS

## Problem

Build OS automates the full planning pipeline (`/plan --auto`: think → challenge → plan) and the full post-build pipeline (`/review` → `/ship`). But the build phase itself — implementing the plan, running tests, iterating on failures — is manual. The human reads the plan, builds step by step, runs tests, fixes failures, and then invokes review.

This is the same gap identified in the CloudZero velocity analysis (Appendix C, Gap #2: "Autonomous execution loop") and in gstack's roadmap (planned `/autoship` in v0.17, not yet built). Neither framework has solved it.

## What We'd Build

A `--build` flag on `/plan --auto` that continues execution after the plan approval gate. The full pipeline becomes:

```
/plan --auto --build <task description>
```

Pipeline: think → challenge → plan → **[approval gate]** → build → test → iterate → review → ship-summary

### Build Phase Behavior

1. **Read the plan.** Parse `tasks/<topic>-plan.md` for build steps, file scopes, and verification commands.
2. **Implement sequentially.** Execute each build step from the plan. For parallel tracks (identified by the decompose gate), spawn worktree-isolated agents.
3. **Test after each step.** Run verification commands from the plan. If tests fail, iterate (max 3 attempts per step — escalation protocol trigger #5).
4. **Escalation during build.** The 7 escalation triggers in workflow.md apply throughout. Ambiguous requirements, architectural decisions outside the plan, security-sensitive changes, scope growth, repeated failures, irreversible side effects, contradictory constraints — all pause and ask.
5. **Decision classification during build.** Reuse `/plan --auto`'s 3-tier classification:
   - **Mechanical:** One clearly right answer (import paths, variable names, boilerplate). Auto-decide silently.
   - **Taste:** Reasonable alternatives exist (error message wording, naming conventions). Auto-decide with the 6 principles, log the choice.
   - **User Challenge:** Both interpretations are defensible and affect behavior. STOP and ask.
6. **After all steps complete:** Run full test suite. If passing, auto-invoke `/review`. Generate ship summary per the new Step 6 in `/ship`.

### What the Human Does

- Writes the task description (one sentence to one paragraph)
- Approves the plan at the approval gate (existing `/plan --auto` behavior)
- Answers escalation questions if they arise during build
- Reviews the `/review` output and approves merge/ship

### Self-Learning Dependency

gstack's design doc argues autobuild depends on self-learning infrastructure ("without memory it repeats the same mistakes"). For Build OS:

- `tasks/lessons.md` already captures gotchas and patterns
- `/start` already loads lessons at session start
- The build phase should read `tasks/lessons.md` for the relevant domain before implementing

This is lighter than gstack's planned per-project JSONL learning store, but may be sufficient for a solo dev where the human is the learning system. If autobuild produces recurring mistakes that lessons.md doesn't catch, that's signal to invest in structured learning — but not a prerequisite.

### Scope Containment

The plan artifact already declares `surfaces_affected` (file list). During build:
- Agent edits are checked against the plan's file list
- Files not in `surfaces_affected` trigger escalation trigger #4 (scope is growing)
- Parallel agents get worktree isolation (existing decompose gate behavior)

No new hook needed — the escalation protocol covers it.

## Why Now

1. All surrounding pieces exist: `/plan --auto`, escalation protocol, `/review`, `/ship` with spec-mapped summaries, decompose gate.
2. The gap between "plan exists" and "code exists" is where the most human time is spent.
3. Both gstack and the CloudZero analysis identify this as the key missing capability.
4. Building it on one repo (Build OS itself) is zero-risk — the human reviews every PR.

## Why Not

1. The build phase requires the most judgment. Plans are abstract; implementation is concrete. An agent that follows a plan literally may miss context the plan didn't capture.
2. Iteration quality degrades: attempt 1 is informed, attempt 2 is a reasonable fix, attempt 3 is often flailing. The 3-strike limit helps but doesn't guarantee quality.
3. Token cost: a full autobuild run (plan + build + test + iterate + review) could consume significant context. Long builds may hit context limits.
4. Scope creep risk: "just add --build" sounds simple, but the build phase is where most complexity lives.

## Implementation Approach

Add a `## --build Mode (Autonomous Build Pipeline)` section to `.claude/skills/plan/SKILL.md` after the existing `--auto` section. No new skill, no new scripts, no new hooks. Reuse existing infrastructure:

- Plan parsing: read the plan artifact's build steps and file scopes
- Implementation: standard Claude Code editing (Edit, Write, Bash)
- Testing: run plan's `verification_commands`
- Iteration: escalation protocol trigger #5 (3 failures = stop)
- Review: invoke `/review` skill
- Summary: invoke ship summary generation (new Step 6 in `/ship`)

Estimated scope: ~60-80 lines added to plan/SKILL.md.

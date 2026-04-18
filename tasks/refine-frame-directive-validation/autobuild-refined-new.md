---
debate_id: autobuild-refined-new
created: 2026-04-18T09:43:55-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# autobuild-refined-new — Refined Document

## Round 1 (gemini-3.1-pro)
The proposal is exceptionally strong and pragmatic. It correctly identifies a high-leverage gap, avoids building redundant infrastructure, and relies on existing primitives (escalation triggers, review skills, plan artifacts) to deliver the feature. 

The primary improvements made in this revision focus on removing hedge words and sharpening the mitigations for the risks identified in the "Why Not" section. Specifically, the document now explicitly bounds the token cost risk by mandating the decompose gate for larger tasks, and it takes a firmer stance on the sufficiency of `lessons.md` over building complex self-learning infrastructure.

### Frame Check
Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The revision is already strong: it defines a concrete behavior, preserves existing operational context, and keeps the recommendation surface narrow and executable. The main opportunities were to tighten a few unsupported claims, sharpen scope boundaries, and make implementation details more operational without changing the underlying proposal.

Key improvements made:
- Clarified that worktree-parallelism is conditional on an existing decompose output, not implied for all plans.
- Tightened the “zero-risk” claim in `Why Now`; human review reduces deployment risk but does not eliminate local repo or time-cost risk.
- Made the escalation/test loop more explicit so “3 consecutive failures” is clearly scoped to one planned step and one verification cycle.
- Added concrete guardrails for missing or underspecified plan artifacts so autobuild does not proceed on plans that lack build steps, verification commands, or file scope.
- Preserved all substantive sections and measurements/scope statements from the draft.

Remaining issues are minor:
- The proposal still assumes plan artifacts are consistently structured enough to parse for build steps, verification commands, and `surfaces_affected`. That assumption is central, but the document can carry it as an explicit precondition rather than leaving it implicit.
- The implementation estimate remains rough. It is acceptable as an estimate because it is not driving the recommendation.

### Frame Check
- Unstated load-bearing assumption: Autobuild depends on plan artifacts being structured and complete enough to drive execution safely — structural change needed would be to define autobuild eligibility/preconditions (for example: no autobuild if plan lacks explicit steps, verification commands, or file scope).

## Final Refined Document

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

```bash
/plan --auto --build <task description>
```

Pipeline: think → challenge → plan → **[approval gate]** → build → test → iterate → review → ship-summary

### Build Phase Behavior

1. **Read the plan.** Parse `tasks/<topic>-plan.md` for explicit build steps, `surfaces_affected`, and verification commands. If any of these are missing, stop and ask rather than inferring them.
2. **Implement sequentially.** Execute each build step in order. If the existing decompose gate has already split work into parallel tracks, spawn worktree-isolated agents for those tracks; otherwise remain single-threaded.
3. **Test after each step.** Run the verification commands attached to that step or plan phase. If tests fail, iterate on that same step. After exactly 3 consecutive failed fix attempts on a single step, trigger escalation protocol #5 (hard stop and ask) to prevent flailing.
4. **Escalation during build.** The 7 escalation triggers in `workflow.md` apply throughout build. Ambiguous requirements, architectural decisions outside the plan, security-sensitive changes, scope growth, repeated failures, irreversible side effects, and contradictory constraints all pause and ask.
5. **Decision classification during build.** Reuse `/plan --auto`'s 3-tier classification:
   - **Mechanical:** One clearly right answer (import paths, variable names, boilerplate). Auto-decide silently.
   - **Taste:** Reasonable alternatives exist (error message wording, naming conventions). Auto-decide with the 6 principles and log the choice.
   - **User Challenge:** Both interpretations are defensible and affect behavior. STOP and ask.
6. **After all steps complete:** Run the full test suite. If passing, auto-invoke `/review`. Generate the ship summary per the new Step 6 in `/ship`.

### What the Human Does

- Writes the task description (one sentence to one paragraph)
- Approves the plan at the approval gate (existing `/plan --auto` behavior)
- Answers escalation questions if they arise during build
- Reviews the `/review` output and approves merge/ship

### Self-Learning Dependency

gstack's design doc argues autobuild depends on self-learning infrastructure ("without memory it repeats the same mistakes"). For Build OS, the existing `lessons.md` primitive is sufficient:

- `tasks/lessons.md` captures gotchas and patterns.
- `/start` loads lessons at session start.
- The build phase reads `tasks/lessons.md` for the relevant domain before implementing.

Do not build a per-project JSONL learning store. If autobuild produces recurring mistakes that `lessons.md` misses, update `lessons.md`. Only invest in structured learning infrastructure if `lessons.md` exceeds context limits.

### Scope Containment

The plan artifact already declares `surfaces_affected` (file list). During build:

- Agent edits are checked against the plan's file list.
- Files not in `surfaces_affected` instantly trigger escalation trigger #4 (scope is growing).
- Parallel agents, when used, get worktree isolation (existing decompose gate behavior).

No new hook is needed; the existing escalation protocol enforces containment.

## Why Now

1. All surrounding pieces exist: `/plan --auto`, escalation protocol, `/review`, `/ship` with spec-mapped summaries, decompose gate.
2. The gap between "plan exists" and "code exists" is where the most human time is spent.
3. Both gstack and the CloudZero analysis identify this as the key missing capability.
4. Building it on one repo (Build OS itself) keeps rollout risk low because the human still reviews the plan, answers escalation questions, and approves merge/ship.

## Why Not (and Mitigations)

1. **Judgment Gap:** The build phase requires judgment. Plans are abstract; implementation is concrete. **Mitigation:** Rely strictly on the 3-tier decision classification. If a concrete implementation detail affects behavior, it is a User Challenge.
2. **Iteration Degradation:** Attempt 1 is informed, attempt 2 is a reasonable fix, attempt 3 is flailing. **Mitigation:** The strict 3-strike limit on a single plan step prevents infinite loops and token waste.
3. **Token Cost:** A full autobuild run will consume significant context. Long builds will hit context limits. **Mitigation:** Enforce the decompose gate for any plan exceeding 5 build steps. Break large tasks into sub-tasks rather than extending the context window.
4. **Scope Creep Risk:** The build phase houses immense complexity. **Mitigation:** Implement entirely via prompt instructions in existing skills, introducing zero new scripts or hooks.

## Implementation Approach

Add a `## --build Mode (Autonomous Build Pipeline)` section to `.claude/skills/plan/SKILL.md` after the existing `--auto` section. Reuse existing infrastructure entirely:

- **Plan parsing:** Read the plan artifact's explicit build steps, file scopes, and verification commands.
- **Eligibility check:** If the approved plan lacks executable steps, verification commands, or `surfaces_affected`, stop and ask rather than improvising.
- **Implementation:** Standard Claude Code editing (`Edit`, `Write`, `Bash`).
- **Testing:** Run the plan's `verification_commands`.
- **Iteration:** Enforce escalation protocol trigger #5 (3 failures on one step = stop).
- **Review:** Invoke `/review` skill.
- **Summary:** Invoke ship summary generation (new Step 6 in `/ship`).

Estimated scope: ~60-80 lines added to `plan/SKILL.md`.

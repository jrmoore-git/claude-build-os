---
debate_id: autobuild-v5
created: 2026-04-18T11:26:26-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# autobuild-v5 — Refined Document

## Round 1 (gemini-3.1-pro)
- Removed inherited framing (references to "CloudZero velocity analysis" and "gstack's roadmap"). The problem—manual execution in an otherwise automated pipeline—is native and clear; relying on external roadmaps to justify it weakens the proposal.
- Converted "Why Not" into "Risks & Mitigations." A risk without a mitigation is just a complaint. Added concrete mitigations to the token cost and context degradation risks.
- Sharpened the implementation approach to be a direct set of instructions rather than a passive description.

### Frame Check
- Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The revision is already strong: it has a clear problem statement, concrete behavior, preserved operational constraints, and a specific implementation target. I kept the proposal within its original frame and made it sharper in four ways:

- Tightened the framing so this is clearly an automation gap in the current workflow, not a claim that the whole system is broken.
- Clarified the execution contract for `--build`: what artifact it consumes, what it may do automatically, and exactly where it must stop for a human.
- Strengthened the false-binary area implicitly present between “fully manual build” and “fully autonomous build” by defining `--build` as an extension of the existing approval-gated workflow rather than a replacement for human review.
- Made the implementation section more executable by specifying entry conditions, stop conditions, logging expectations, and success criteria, while preserving the original recommendation and scope.

I did not introduce new quantitative claims beyond the proposal’s existing estimate. I preserved the recommendation content and structure; there was no numbered recommendations section to preserve separately.

### Frame Check
Frame check: document's frame is sound.

## Final Refined Document

---
title: "Autobuild Mode: Autonomous Build-Test-Iterate Loop"
type: proposal
status: draft
date: 2026-04-16
---

# Proposal: Autobuild Mode for Build OS

## Problem

Build OS automates the planning pipeline (`/plan --auto`: think → challenge → plan) and the post-build pipeline (`/review` → `/ship`). The remaining manual gap is the build phase itself: implementing the approved plan, running verification commands, fixing failures, and continuing until the work is ready for review.

Today, a human must:
- read the generated plan,
- implement it step by step,
- run tests,
- iterate on failures,
- and then manually invoke review.

That interrupts an otherwise continuous workflow and forces repeated human context-switching during the most mechanical part of execution.

This proposal closes that gap without removing human control. The human still approves the plan before implementation begins, still answers escalations during execution, and still reviews the final output before merge or ship.

## What We'd Build

Add a `--build` flag to `/plan --auto` so execution can continue automatically after plan approval:

```bash
/plan --auto --build <task description>
```

Full pipeline:

```text
think → challenge → plan → [approval gate] → build → test → iterate → review → ship-summary
```

`--build` is not a new top-level mode. It is an extension of the existing approval-gated `/plan --auto` flow.

### Execution Contract

After the human approves the generated plan, the build phase:

1. consumes the approved plan artifact,
2. implements the specified build steps within the declared file scope,
3. runs the plan's verification commands,
4. iterates on failures up to a fixed limit,
5. escalates when a decision exceeds the plan or hits an existing stop condition,
6. and, on success, invokes `/review` and generates the ship summary.

Autobuild may proceed automatically only while the work remains within the approved plan and existing escalation policy.

## Build Phase Behavior

### 1. Read the plan artifact

Parse `tasks/<topic>-plan.md` and extract at minimum:
- ordered build steps,
- `surfaces_affected`,
- verification commands,
- any decomposition or parallelization instructions already present in the plan.

The approved plan artifact is the source of truth for build execution.

### 2. Implement sequentially by default

Execute each build step in order.

If the approved plan explicitly identifies parallel tracks through the existing decompose gate, spawn worktree-isolated agents for those tracks. Parallel execution is allowed only when the plan already decomposes the work into separable tracks with non-overlapping file ownership or clearly bounded interfaces.

### 3. Test after each step

After each implementation step, run the verification commands relevant to that step.

If verification fails:
- attempt to fix the failure,
- re-run verification,
- repeat up to a maximum of 3 attempts for that step.

After 3 failed attempts, stop and escalate under trigger #5. The system should not continue to the next step on a failing step.

### 4. Apply the existing escalation protocol during build

The 7 escalation triggers in `workflow.md` remain in force throughout autobuild. Execution pauses immediately and requests human input when any of the following occur:
- ambiguous requirements,
- architectural decisions outside the approved plan,
- security-sensitive changes,
- scope growth,
- repeated failures,
- irreversible side effects,
- contradictory constraints.

Autobuild is only for execution within an approved envelope. It does not authorize the agent to reinterpret the task when the task itself becomes unclear.

### 5. Reuse the existing decision classification

During build, reuse `/plan --auto`'s 3-tier decision model:

- **Mechanical:** one clearly right answer (for example: import paths, variable names, boilerplate). Auto-decide silently.
- **Taste:** reasonable alternatives exist (for example: naming conventions, error message wording). Auto-decide using the 6 principles and log the choice.
- **User Challenge:** both interpretations are defensible and affect behavior. Stop and ask the human.

This keeps implementation decisions aligned with the planning workflow instead of inventing a second decision system for build execution.

### 6. Enforce scope containment

The plan artifact explicitly declares `surfaces_affected`. During build:
- edits are checked against the approved file list,
- modifying a file not listed in `surfaces_affected` triggers escalation trigger #4,
- parallel agents operate in strict worktree isolation,
- and any required expansion of the file scope must be approved by the human before execution continues.

This is the main containment mechanism for preventing autobuild from turning a bounded implementation task into exploratory repo-wide change.

### 7. Final verification and handoff

After all build steps complete:
1. run the full test suite or the plan's final verification commands,
2. if verification passes, invoke `/review`,
3. generate the ship summary per Step 6 in `/ship`,
4. present the resulting review output to the human for final approval.

If final verification fails, stop and escalate rather than shipping partial success into review.

## What the Human Does

The human remains responsible for the control points that matter:

- writes the task description,
- approves the plan at the approval gate,
- answers escalation questions during the build if they arise,
- reviews the `/review` output,
- approves merge or ship.

The human is removed from stepwise execution, not from decision authority.

## Context & Learning

Autonomous execution needs enough memory to avoid repeating known mistakes. This proposal uses the existing mechanism rather than introducing a new memory system:

- `tasks/lessons.md` captures gotchas and recurring patterns,
- `/start` loads lessons at session start,
- the build phase reads `tasks/lessons.md` for the relevant domain before implementing.

If autobuild produces recurring errors that `lessons.md` does not prevent, that is the signal to invest in a more structured learning store. Until then, `lessons.md` is the correct default because it reuses existing infrastructure and keeps the proposal narrow.

## Why Now

1. The required adjacent components already exist: `/plan --auto`, the escalation protocol, `/review`, `/ship` with spec-mapped summaries, and the decompose gate.
2. The remaining manual gap sits between “approved plan exists” and “reviewable code exists,” which is the most execution-heavy portion of the workflow.
3. This can be tested safely on one repository first—Build OS itself—because a human still approves the plan, answers escalations, and reviews the final output before shipping.

## Risks & Mitigations

1. **Abstract plans vs. concrete implementation**  
   Plans are abstract; implementation requires judgment. An agent following a plan too literally may miss unstated context.  
   **Mitigation:** enforce the 7 escalation triggers strictly so architectural deviations, ambiguity, and conflicting constraints stop execution early.

2. **Iteration degradation**  
   Attempt 1 is informed, attempt 2 may still be constructive, and attempt 3 often becomes flailing.  
   **Mitigation:** hard-stop at 3 failed attempts on a step under escalation trigger #5.

3. **Token cost and context limits**  
   A full autobuild run may consume enough context to increase instruction loss or hit API limits.  
   **Mitigation:** clear the conversational context buffer after plan approval and carry forward only the approved plan artifact, relevant lessons, and execution-state logs needed for the build phase.

4. **Scope creep**  
   The build phase is where implementation complexity expands most easily.  
   **Mitigation:** enforce file-level constraints via `surfaces_affected` and require escalation for any file outside the approved scope.

5. **Parallel track coordination failures**  
   Parallel agents can conflict even when decomposition looks clean.  
   **Mitigation:** allow parallel execution only when the plan explicitly decomposes the work into isolated tracks, use separate worktrees, and require a merge-and-verify step before final review.

## Implementation Approach

Add a `## --build Mode (Autonomous Build Pipeline)` section to `.claude/skills/plan/SKILL.md` immediately after the existing `--auto` section.

Rely on existing infrastructure rather than adding new runtime components:

- **Plan parsing:** instruct the agent to read the approved plan artifact's build steps, scope, and verification commands.
- **Implementation:** use standard Claude Code editing tools (`Edit`, `Write`, `Bash`).
- **Testing:** execute the plan's `verification_commands` after each step and again at final verification.
- **Iteration:** enforce escalation trigger #5 exactly: 3 failed attempts on a step means stop.
- **Escalation:** apply all 7 existing escalation triggers during build, not just repeated failures.
- **Scope enforcement:** treat `surfaces_affected` as a hard constraint unless the human approves expansion.
- **Review handoff:** invoke `/review` automatically after successful final verification.
- **Summary generation:** generate the ship summary using the existing `/ship` Step 6 format.

### Required behavior in `SKILL.md`

The new `--build` section should specify:

1. **Entry condition**  
   Autobuild starts only after `/plan --auto` completes and the human explicitly approves the generated plan.

2. **Inputs**  
   The build phase receives:
   - the approved `tasks/<topic>-plan.md`,
   - relevant `tasks/lessons.md` context,
   - and any execution constraints already defined by the workflow.

3. **Permitted actions**  
   The agent may edit files in `surfaces_affected`, run the plan's verification commands, and make mechanical or taste-level decisions within the existing decision rubric.

4. **Mandatory stop conditions**  
   The agent must stop and ask the human whenever an escalation trigger fires or a user-challenge decision appears.

5. **Completion condition**  
   Autobuild completes only when all planned steps are implemented, final verification passes, `/review` runs, and the ship summary is generated.

6. **Failure condition**  
   Autobuild stops without review handoff if verification cannot be restored within the allowed retry limit or if execution leaves the approved scope without human approval.

### Success criteria

The feature is successful if a user can:

1. run `/plan --auto --build <task description>`,
2. approve the generated plan,
3. have the system execute the approved implementation steps automatically,
4. be interrupted only for existing escalation conditions or user-challenge decisions,
5. and receive `/review` output plus a ship summary when the work is complete.

**Estimated scope:** ~60–80 lines added to `plan/SKILL.md`. No new scripts or hooks required.

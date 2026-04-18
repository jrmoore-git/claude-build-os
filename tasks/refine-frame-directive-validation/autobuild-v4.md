---
debate_id: autobuild-v4
created: 2026-04-18T11:23:16-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# autobuild-v4 — Refined Document

## Round 1 (gemini-3.1-pro)
The document is well-scoped and leverages existing primitives (escalation protocol, 3-tier decision classification, decompose gates) to build a powerful new capability with minimal net-new code. 

To make it strictly executable, I have tightened the "Implementation Approach" into concrete directives. I also addressed a hidden dependency for true autonomy: ensuring Claude Code's tool execution (Bash/Edit) is configured to bypass human confirmation prompts during the build loop, otherwise the "autonomous" loop will hang waiting for `y/N` inputs. The self-learning section was also sharpened to explicitly reject building new memory infrastructure at this stage.

### Frame Check
Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The draft is already concrete and executable: it defines the command surface, lifecycle, escalation points, and implementation boundary clearly. The strongest parts are the reuse of existing Build OS mechanisms, explicit human approval points, and the preservation of containment via `surfaces_affected` and escalation triggers.

Main improvements needed were:
- tighten a few claims that were framed too absolutely,
- make the implementation path more explicit about where behavior lives,
- sharpen recommendation language without expanding scope,
- reduce reliance on external framing in the problem statement,
- clarify that “zero risk” is not literally true even with human review.

### Frame Check
- Inherited frame: The problem statement leans on CloudZero/gstack as validators of the gap instead of deriving the need from Build OS’s own pipeline structure — this can be fixed inline by making the internal workflow gap primary and external references secondary.
- Inflated problem: “primary bottleneck” and “zero risk” overstate the case without evidence in the document — fixed inline by narrowing to a plausible, supported claim.
- Frame check: document's frame is otherwise sound.

## Final Refined Document

---
title: "Autobuild Mode: Autonomous Build-Test-Iterate Loop"
type: proposal
status: draft
date: 2026-04-16
---

# Proposal: Autobuild Mode for Build OS

## Problem

Build OS automates the planning pipeline (`/plan --auto`: think → challenge → plan) and the post-build pipeline (`/review` → `/ship`). The remaining manual gap is the build loop between them: implementing the approved plan, running verification commands, iterating on failures, and stopping when execution leaves the plan's bounds.

Today, that middle section is human-operated. After approving the plan, the human must:
- read `tasks/<topic>-plan.md`,
- implement the steps,
- run the listed verification commands,
- diagnose failures,
- decide whether to retry or escalate,
- and only then invoke review.

That gap matters because it is the only major stage in the workflow that still requires continuous operator attention after plan approval.

External documents point to the same missing capability. The CloudZero velocity analysis calls it an "autonomous execution loop," and gstack's roadmap includes a planned `/autoship`. Those references are supporting evidence, not the basis of the proposal: the case for Autobuild stands on Build OS's own workflow shape.

## What We Will Build

Add a `--build` flag to `/plan --auto` so execution continues automatically after the existing plan approval gate:

```bash
/plan --auto --build <task description>
```

The resulting pipeline is:

```text
think → challenge → plan → [approval gate] → build → test → iterate → review → ship-summary
```

`--build` is not a new planning mode. It is an execution extension of the existing `/plan --auto` flow.

### Build Phase Behavior

1. **Read the plan**
   Parse `tasks/<topic>-plan.md` before taking action. Extract:
   - ordered build steps,
   - `surfaces_affected`,
   - `verification_commands`,
   - any decomposition or parallelization instructions already emitted by planning.

2. **Implement sequentially**
   Execute build steps in plan order by default.

   If the approved plan already identifies parallel tracks through the decompose gate, run them in isolated worktrees using the existing parallel-agent pattern. Do not invent new parallelism during build.

3. **Test after each step**
   After each build step, run the plan's listed verification commands relevant to that step. On failure, iterate on that same step.

   Enforce a hard maximum of 3 sequential attempts on a single step. After the third failed attempt, stop and escalate under trigger #5.

4. **Escalate during build**
   The 7 escalation triggers in `workflow.md` remain active during Autobuild. Execution pauses immediately for human input when any of the following occurs:
   - ambiguous requirements,
   - architectural decisions outside the approved plan,
   - security-sensitive changes,
   - scope growth,
   - repeated failures,
   - irreversible side effects,
   - contradictory constraints.

5. **Classify decisions during build**
   Reuse `/plan --auto`'s existing 3-tier decision model:
   - **Mechanical:** One clearly correct answer. Decide silently.
   - **Taste:** Multiple reasonable answers with limited behavioral impact. Decide using the 6 principles and log the choice.
   - **User Challenge:** Multiple defensible interpretations that change behavior. Stop and ask.

6. **Contain edits to approved scope**
   Treat `surfaces_affected` as the allowed edit set for the build loop.
   - If an edit stays within `surfaces_affected`, continue.
   - If execution requires editing a file outside that set, stop immediately and escalate under trigger #4.
   - Parallel tracks must preserve worktree isolation and cannot widen file scope without escalation.

7. **Finalize and hand off**
   After all build steps complete:
   - run the full verification suite,
   - if passing, auto-invoke `/review`,
   - then generate the ship summary using the existing Step 6 behavior in `/ship`.

## Human Responsibilities

The human remains responsible for the decisions that matter most:

- write the task description,
- approve the plan at the existing approval gate,
- answer escalation questions raised during Autobuild,
- review the final `/review` output,
- approve merge or ship.

Autobuild removes continuous keyboard supervision during execution; it does not remove human approval over scope-changing or behavior-shaping decisions.

## Self-Learning Dependency

gstack's design doc argues that autonomous build iteration requires heavier self-learning infrastructure because, without memory, the system repeats mistakes.

Build OS should not adopt that dependency for this feature.

Autobuild can use the lightweight mechanisms that already exist:
- `tasks/lessons.md` captures recurring gotchas and patterns,
- `/start` already loads lessons at session start,
- the build phase can explicitly read the relevant portions of `tasks/lessons.md` before implementation.

Therefore:

- **Do not build** a per-project JSONL memory store for Autobuild.
- **Do use** `tasks/lessons.md` as the persistent lessons source during build execution.
- If recurring mistakes still slip through, improve the structure or retrieval discipline around `tasks/lessons.md` rather than introducing a separate memory subsystem as part of this proposal.

## Scope Containment

This proposal relies on existing containment mechanisms rather than introducing new hooks.

The approved plan already supplies `surfaces_affected`. During Autobuild:
- agent edits must stay within that file list,
- edits outside the list trigger escalation for scope growth,
- parallel tracks use the existing worktree-isolation model from the decompose gate.

This is sufficient for the first implementation. Autobuild should be added as an orchestration layer over current planning, escalation, review, and shipping behaviors—not as a new containment framework.

## Why Now

1. **The surrounding system already exists.** `/plan --auto`, the escalation protocol, `/review`, `/ship`, and the decompose gate are already in place.
2. **The missing piece is execution continuity.** Planning and review are automated, but implementation still requires active human operation between them.
3. **The feature composes existing primitives.** This is an integration of current mechanisms, not a greenfield subsystem.
4. **The initial rollout target is controlled.** Building and testing the mode on Build OS itself keeps the feedback loop tight, and final review still remains with a human before merge.

## Risks and Mitigations

1. **Abstract plans vs. concrete implementation**
   Plans are necessarily higher-level than code changes, and some implementation details only appear during execution.  
   **Mitigation:** The 3-tier decision model forces a stop on behavior-affecting ambiguity through the User Challenge path.

2. **Iteration degradation**
   Early retries can be productive; repeated retries often signal the plan is insufficient or the task has left the expected path.  
   **Mitigation:** The hard 3-attempt limit prevents unbounded looping and forces escalation once the loop stops being productive.

3. **Token cost**
   A full Autobuild run may consume substantial context, especially on multi-step tasks.  
   **Mitigation:** Keep execution scoped to the approved plan, and use worktree-isolated agents only when parallel tracks were already approved in planning.

4. **Tool confirmation blockers**
   Claude Code normally prompts for Bash/Edit execution in many environments. That would stall an autonomous loop on confirmation prompts.  
   **Mitigation:** Run Autobuild only in environments configured to permit autonomous execution of the required safe tools for the duration of the build loop.

5. **False sense of safety from review**
   Human review before merge reduces risk but does not eliminate the cost of poor intermediate changes, wasted runs, or noisy review output.  
   **Mitigation:** Keep scope narrow in the first version: approved-plan execution only, strict escalation on scope growth, and no new memory or orchestration subsystems.

## Implementation Approach

Execute the following changes within existing infrastructure. Do not create new skills, scripts, or hooks.

1. **Update `SKILL.md`**
   Add a `## --build Mode (Autonomous Build Pipeline)` section to `.claude/skills/plan/SKILL.md` immediately after the existing `--auto` section.

2. **Define the execution contract**
   In that section, instruct the agent to read the plan artifact before taking action and extract:
   - build steps,
   - `surfaces_affected`,
   - `verification_commands`,
   - any pre-approved decomposition or parallel tracks.

3. **Specify build-loop behavior**
   Instruct the agent to:
   - execute steps in order,
   - test after each step,
   - retry a failing step up to 3 times,
   - escalate immediately on any active workflow trigger,
   - prohibit out-of-scope file edits without escalation.

4. **Use existing tool primitives**
   Implement code changes with standard Claude Code tools only: Edit, Write, and Bash. Autobuild relies on environment-level auto-approval for permitted tools; it does not add a new tool layer.

5. **Reuse existing review and ship behavior**
   On successful completion of all build steps and final verification:
   - auto-invoke `/review`,
   - then generate the ship summary using existing `/ship` behavior.

6. **Keep the first version text-only**
   The first implementation lives entirely in the plan skill instructions. No new runtime memory store, containment hook, or orchestration script is part of this proposal.

## Proposed Changes

1. **Add `--build` to `/plan --auto` as an execution extension**
   Implement `--build` as a continuation of the approved `/plan --auto` flow: after the existing approval gate, read the generated plan artifact, execute the listed steps, run verification after each step, iterate up to 3 times per failed step, and stop on any active escalation trigger.

2. **Enforce plan-bounded execution using existing plan metadata**
   Treat `surfaces_affected` as the allowed edit set and `verification_commands` as the required test contract during Autobuild. Any required edit outside `surfaces_affected` must halt execution and request human input under the existing scope-growth escalation path.

3. **Reuse existing decision and escalation machinery without adding new infrastructure**
   During build execution, preserve the current 3-tier decision classification and all 7 escalation triggers. Do not add a new memory subsystem, new containment hook, or new orchestration script for the first version.

4. **Implement the feature entirely in `.claude/skills/plan/SKILL.md`**
   Add a dedicated `--build Mode (Autonomous Build Pipeline)` section to the plan skill defining:
   - plan parsing requirements,
   - sequential and pre-approved parallel execution rules,
   - verification timing,
   - retry limits,
   - escalation conditions,
   - `/review` handoff,
   - ship-summary generation.

5. **Restrict first rollout to environments that can actually run autonomously**
   Enable Autobuild only where Claude Code can execute the required safe Edit/Write/Bash actions without interactive `y/N` confirmation blocking the loop. If the environment cannot satisfy that requirement, `--build` should not start execution.

*Estimated scope: ~60-80 lines added to `plan/SKILL.md`.*

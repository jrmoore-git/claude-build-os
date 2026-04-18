---
debate_id: autobuild-tightened
created: 2026-04-18T09:54:39-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# autobuild-tightened — Refined Document

## Round 1 (gemini-3.1-pro)
The proposal is structurally strong and leverages existing system primitives (escalation protocol, `lessons.md`, `/review`) rather than inventing new ones. 

**Improvements made:**
- **Strategic Posture:** Converted the "Why Not" section from passive worries into explicit "Risks & Mitigations." If a risk is known, the system must have a defined response.
- **Decisiveness:** Changed the "Self-Learning Dependency" section from "may be sufficient" to a firm directive to use the existing `lessons.md` and explicitly reject building a new learning store for this iteration.
- **Actionability:** Upgraded "Implementation Approach" into a concrete set of execution steps.

### Frame Check
Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The revision is already tight and executable. The strongest parts are the explicit approval gate, reuse of existing escalation and decision-classification primitives, and the narrow implementation scope: extend `plan/SKILL.md` rather than introducing new infrastructure.

Remaining issues are mostly clarity and precision, not direction:

- The problem statement leans on external framing ("CloudZero" and "gstack") before grounding the gap in Build OS itself. I kept those references but made Build OS's own pipeline gap primary.
- "Zero-risk" was overstated. Human review before merge materially reduces risk, but does not make autonomous code changes literally risk-free. I narrowed that claim.
- The implementation section was slightly underspecified about what the build loop must persist and what happens on pause/escalation. I clarified behavior without changing scope.
- The document had recommendations in practice under "Implementation Steps" rather than a labeled recommendation section. Per preservation rules, all four actions remain intact and more concrete.
- I preserved all operational details already present and avoided introducing new speculative quantitative claims.

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

Build OS automates the full planning pipeline (`/plan --auto`: think → challenge → plan) and the full post-build pipeline (`/review` → `/ship`). The build phase itself — implementing the plan, running tests, and iterating on failures — remains manual. Today, the human reads the plan, executes the build step by step, runs verification, fixes failures, and then invokes review.

That leaves a clear gap in Build OS's own workflow: the system can generate a plan and can review completed work, but it cannot carry approved work through execution. The missing loop is:

**approved plan → implementation → verification → bounded iteration → review handoff**

This same gap appears in the CloudZero velocity analysis (Appendix C, Gap #2: "Autonomous execution loop") and in gstack's roadmap, but the justification here does not depend on those sources. In Build OS itself, planning and shipping are automated while execution is not.

## What We'd Build

Add a `--build` flag to `/plan --auto` so execution continues after the plan approval gate:

```bash
/plan --auto --build <task description>
```

The resulting pipeline is:

**think → challenge → plan → [human approval gate] → build → test → iterate → review → ship-summary**

### Build Phase Behavior

1. **Read the plan**
   Parse `tasks/<topic>-plan.md` for:
   - ordered build steps
   - `surfaces_affected`
   - `verification_commands`

2. **Implement sequentially**
   Execute each build step in plan order. If the plan's decompose gate explicitly identifies parallel tracks, spawn worktree-isolated agents for those tracks only.

3. **Test after each step**
   Run the verification command(s) associated with the step. On failure, iterate on that step with a hard limit of 3 attempts. After the third failed verification attempt, stop and invoke escalation trigger #5.

4. **Enforce escalation continuously**
   The 7 escalation triggers in `workflow.md` apply throughout the build loop. The agent must pause immediately and ask the human if it encounters:
   - ambiguous requirements
   - architectural decisions outside the approved plan
   - security-sensitive changes
   - scope growth
   - repeated failures
   - irreversible side effects
   - contradictory constraints

5. **Classify decisions during execution**
   Reuse `/plan --auto`'s existing 3-tier classification:
   - **Mechanical:** one clearly correct answer; decide silently
   - **Taste:** multiple reasonable choices; decide using the 6 core principles and log the choice
   - **User Challenge:** multiple defensible interpretations that change behavior; stop and ask

6. **Contain edits to approved scope**
   Validate all file edits against the plan's `surfaces_affected` list.
   - If the agent needs to edit a file outside that list, stop immediately and invoke escalation trigger #4 for scope growth.
   - Parallel agents must operate in isolated worktrees scoped to their assigned files.

7. **Finalize**
   After all build steps complete, run the full test suite. If it passes, automatically invoke `/review` and generate the ship summary using the existing Step 6 behavior from `/ship`.

8. **Pause cleanly on escalation**
   If any escalation trigger fires, stop execution without continuing to later plan steps. Leave the workspace in its current state, record:
   - the current step
   - the failed command or blocking condition
   - files changed so far
   - the exact question requiring human input

   Resume only after the human answers or approves a revised plan.

### Human Responsibilities

The human remains in control of approval and release:

- Write the task description.
- Approve the plan at the approval gate.
- Unblock the agent when escalation triggers fire.
- Review the `/review` output and approve merge or ship.

## Self-Learning Dependency

gstack's design doc argues that autobuild depends on self-learning infrastructure to avoid repeating mistakes. Build OS should not add a new learning store for this feature. It can rely on existing primitives:

- `tasks/lessons.md` already captures domain gotchas and patterns.
- `/start` already loads lessons at session start.
- The build phase should explicitly read `tasks/lessons.md` before implementation begins.

Do not build a per-project JSONL learning store. The human remains the learning system and updates `lessons.md` when autobuild exposes repeated failure modes or missing guidance.

## Scope Containment

The plan artifact declares `surfaces_affected`. During build:

- Agent edits are strictly validated against the approved file list.
- Editing files not listed in `surfaces_affected` immediately triggers escalation trigger #4 for scope growth.
- Parallel agents receive strict worktree isolation to prevent cross-track interference.

## Why Now

1. All surrounding primitives already exist: `/plan --auto`, the escalation protocol, `/review`, `/ship` summaries, and the decompose gate.
2. The gap between "approved plan exists" and "verified code exists" is still manual and is the largest remaining break in the end-to-end workflow.
3. Build OS itself is the right first repository for this feature because every run still includes human plan approval, escalation checkpoints, and final review before merge or ship.

## Risks & Mitigations

1. **Context or token exhaustion**
   A full autobuild run may exceed safe context limits.
   *Mitigation:* Monitor context usage during execution. If context approaches the safe threshold, fail fast, persist the current step and status, and prompt the human to resume in a new thread.

2. **Iteration flailing**
   The first retry is informed; later retries can degrade into guesswork.
   *Mitigation:* Enforce the 3-strike limit strictly. On the third failed verification attempt, halt and escalate. Do not permit ad hoc extra attempts.

3. **Plan rigidity**
   Agents following abstract plans too literally may miss obvious repository context.
   *Mitigation:* Use the 3-tier decision classification for local execution choices. Any change that alters behavior, architecture, or approved scope must escalate rather than improvise.

4. **Partial-state confusion after pause**
   A halted run can leave the workspace changed but unfinished.
   *Mitigation:* On every escalation stop, record the active step, changed files, last verification result, and required human decision before yielding control.

## Implementation Steps

Add the capability directly to `.claude/skills/plan/SKILL.md`. Do not introduce new skills, scripts, hooks, or learning infrastructure for this proposal.

1. **Add a `## --build Mode` section** to `plan/SKILL.md` immediately after the existing `--auto` section.
   - Define the command entrypoint: `/plan --auto --build <task description>`
   - State that execution begins only after explicit human plan approval

2. **Define plan parsing logic**
   Extract from the approved plan artifact:
   - build steps
   - `surfaces_affected`
   - `verification_commands`

   Require the build loop to use those fields as the execution contract.

3. **Wire iteration limits to escalation**
   After each failed verification run, retry only within the current step.
   On the third failed verification attempt, stop and explicitly invoke escalation trigger #5.

4. **Chain completion to review and ship summary**
   After successful completion of all plan steps and a passing full test suite:
   - invoke `/review`
   - generate the existing `/ship` Step 6 summary output

   Do not add a separate release flow; reuse the current post-build primitives.

---
debate_id: autobuild-v3
created: 2026-04-18T10:00:30-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# autobuild-v3 — Refined Document

## Round 1 (gemini-3.1-pro)
The proposal effectively leverages existing primitives (escalation protocol, decision classification, `/review`) to close a clear operational gap. By resisting the urge to build heavy new infrastructure (like gstack's JSONL store) and instead relying on existing context files, it keeps the scope tight and realistic.

### Frame Check
- **Unstated Load-Bearing Assumption:** The document assumes the underlying agent (Claude Code) can natively spawn and orchestrate parallel "worktree-isolated agents" purely via markdown instructions in `SKILL.md` ("No new skill, no new scripts"). If the CLI lacks native parallel orchestration, this requirement fails. *Fix applied in revision: Narrowed the implementation scope to sequential execution to align with the "no new scripts" constraint.*

## Round 2 (gpt-5.4)
The revision is clear, scoped, and more executable than a typical high-level proposal. It preserves a concrete operator model, ties the feature to existing Build OS primitives, and avoids unnecessary new infrastructure. The strongest parts are the explicit approval gate, reuse of existing escalation rules, and the narrow implementation approach in `.claude/skills/plan/SKILL.md`.

Remaining issues are mostly completeness and precision, not frame defects:

- The proposal says the full pipeline becomes `think → challenge → plan → [approval gate] → build → test → iterate → review → ship-summary`, but it does not fully specify what artifact the build phase must consume beyond "parse `tasks/<topic>-plan.md`". It should state that autobuild only runs when the plan contains explicit build steps, `surfaces_affected`, and `verification_commands`; otherwise it must stop at plan approval.
- "Generate the ship summary per Step 6 in `/ship`" was slightly ambiguous because earlier text says the human still approves merge/ship. The revision below keeps auto-generation of the summary but makes clear that merge/ship remains human-approved.
- Scope containment was directionally right but too strict as written. "Map exactly to the plan's file list" can create unnecessary pauses for mechanical edits to closely related files like adjacent tests, generated files, or local config touched by a declared step. The revised document keeps the containment intent while making the escalation rule executable: edits must stay within `surfaces_affected`; any new file outside that set pauses for approval.
- The proposal references external framings (CloudZero, gstack) but the recommendation does not depend on them; the core argument stands on Build OS's own workflow.

### Frame Check
- [Inherited frame]: The problem statement partly relies on external sources ("CloudZero velocity analysis", "gstack's roadmap") to validate the gap rather than reasoning entirely from Build OS's own operator workflow — refine cannot fully fix this via polish because it is a framing choice about how the need is justified.

## Final Refined Document

---
title: "Autobuild Mode: Autonomous Build-Test-Iterate Loop"
type: proposal
status: active
date: 2026-04-16
---

# Proposal: Autobuild Mode for Build OS

## Problem

Build OS automates the full planning pipeline (`/plan --auto`: think → challenge → plan) and the full post-build pipeline (`/review` → `/ship`). The build phase itself — implementing the plan, running tests, iterating on failures — remains manual. The human reads the plan, builds step by step, runs tests, fixes failures, and then invokes review.

This is the same gap identified in the CloudZero velocity analysis (Appendix C, Gap #2: "Autonomous execution loop") and in gstack's roadmap (planned `/autoship` in v0.17, not yet built). Neither framework has solved it.

## What We Will Build

Add a `--build` flag to `/plan --auto` so execution continues after the plan approval gate:

```bash
/plan --auto --build <task description>
```

Pipeline:

```text
think → challenge → plan → [approval gate] → build → test → iterate → review → ship-summary
```

`ship-summary` means generate the existing `/ship` summary artifact after review passes. It does not mean auto-merge or auto-ship; the human still reviews the `/review` output and approves merge/ship.

Autobuild runs only when the approved plan artifact contains all of the following:

- explicit build steps
- `surfaces_affected`
- `verification_commands`

If any of these are missing, `/plan --auto --build` stops after plan generation and approval rather than improvising the build phase.

### Build Phase Behavior

1. **Read the plan.** Parse `tasks/<topic>-plan.md` for build steps, `surfaces_affected`, and `verification_commands`.
2. **Implement sequentially.** Execute each build step from the plan in order. Parallel execution across worktrees is explicitly out of scope for this version.
3. **Test after each step.** Run the verification commands specified in the plan after each step. If tests fail, iterate on the current step. Trigger escalation protocol #5 exactly on the 3rd consecutive failure.
4. **Apply escalation rules during build.** The 7 escalation triggers in `workflow.md` remain active throughout the build phase. Ambiguous requirements, architectural decisions outside the plan, security-sensitive changes, scope growth, repeated failures, irreversible side effects, and contradictory constraints immediately pause execution and request human input.
5. **Classify decisions during build.** Reuse `/plan --auto`'s 3-tier classification:
   - **Mechanical:** One clearly right answer exists (import paths, variable names, boilerplate). Auto-decide silently.
   - **Taste:** Multiple reasonable alternatives exist (error message wording, naming conventions). Auto-decide using the 6 core principles and log the choice.
   - **User Challenge:** Multiple defensible interpretations affect behavior. Stop and ask the human.
6. **Complete the run.** After all build steps complete, run the full test suite. On pass, auto-invoke `/review`. If review passes, generate the ship summary using the existing Step 6 behavior in `/ship`.

### Human Responsibilities

- Write the task description.
- Approve the plan at the approval gate.
- Answer escalation questions during build.
- Review the `/review` output.
- Approve merge/ship.

### Self-Learning Dependency

gstack's design doc argues autobuild depends on self-learning infrastructure to prevent repeated mistakes. For Build OS, that dependency is unnecessary for the first version:

- `tasks/lessons.md` already captures gotchas and patterns.
- `/start` already loads lessons at session start.
- The build phase reads `tasks/lessons.md` for the relevant domain before implementation.

This is sufficient for a solo developer environment where the human acts as the learning system. If autobuild produces recurring mistakes that `lessons.md` does not prevent, then structured learning infrastructure becomes justified. Until then, `tasks/lessons.md` is the only learning mechanism.

### Scope Containment

The plan artifact declares `surfaces_affected` during planning. During build:

- Agent edits must remain within `surfaces_affected`.
- Any required edit outside `surfaces_affected` triggers escalation trigger #4 (scope growth) and pauses for approval.
- Autobuild must not silently expand file scope during iteration, even when a fix appears obvious.

This keeps the build phase bound to the approved plan rather than letting implementation drift redefine scope.

## Why Now

1. All surrounding pieces already exist: `/plan --auto`, the escalation protocol, `/review`, `/ship` with spec-mapped summaries, and the decompose gate.
2. The gap between "plan exists" and "code exists" is the largest remaining manual segment in the workflow.
3. Building it on Build OS itself carries limited operational risk because the human still reviews the result before merge/ship.

## Known Limitations and Risks

1. **Context Loss:** Plans are abstract; implementation is concrete. An agent following a plan literally lacks some of the peripheral context a human gathers while coding.
2. **Iteration Degradation:** Attempt 1 is informed, attempt 2 is a reasonable fix, and attempt 3 is often flailing. The strict 3-strike limit contains this failure mode but does not eliminate it.
3. **Context Limits:** A full autobuild run (plan + build + test + iterate + review) uses substantial context. Long runs may hit context limits and require manual session restarts.
4. **Scope Creep:** The build phase contains the highest density of edge cases, so scope containment and escalation must remain strict.

## Implementation Approach

Add a `## --build Mode (Autonomous Build Pipeline)` section to `.claude/skills/plan/SKILL.md` after the existing `--auto` section. Do not add a new skill, new scripts, or new hooks.

1. **Plan parsing:** Instruct the agent to read the approved plan artifact and require explicit build steps, `surfaces_affected`, and `verification_commands` before entering build mode.
2. **Implementation:** Confine execution to standard Claude Code editing primitives (Edit, Write, Bash) in sequential order. Do not attempt parallel agent orchestration.
3. **Testing:** Execute the exact `verification_commands` specified in the plan via Bash after each step, then run the full test suite at the end.
4. **Iteration:** Enforce escalation protocol trigger #5 as a hard stop: exactly 3 consecutive failures on the current step pauses for human intervention.
5. **Scope control:** Treat `surfaces_affected` as a hard boundary. Any edit outside that set pauses execution under escalation trigger #4.
6. **Review:** Invoke the existing `/review` skill after successful test completion.
7. **Summary:** After review passes, generate the existing `/ship` Step 6 summary artifact. Do not auto-merge or auto-ship.

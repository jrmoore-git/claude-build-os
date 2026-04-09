---
name: autoplan
description: |
  Auto-planning pipeline. Detects pipeline tier from task description, then
  chains the appropriate skills with auto-decisions using 6 decision principles.
  Surfaces taste decisions at a final approval gate.
  Use when asked to "autoplan", "auto plan", "run the full pipeline", or
  "plan this automatically".
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Skill
  - AskUserQuestion
---

# /autoplan — Auto-Planning Pipeline

One command. Task description in, fully reviewed plan out.

/autoplan detects the pipeline tier, then chains our skills at full depth.
Intermediate AskUserQuestion calls are auto-decided using the 6 principles
below. Taste decisions (where reasonable people could disagree) are surfaced
at a final approval gate.

---

## Step 0: Tier Detection

Read the user's task description and classify into a pipeline tier:

**T2 (standard)** — Bugfix, test addition, docs, trivial refactor, small feature
with obvious approach. Signals: "fix", "bug", "test", "docs", "refactor",
"update", single-file scope, well-understood domain.

**T1 (new feature)** — New capability, new abstraction, scope expansion, new
integration. Signals: "add", "new", "feature", "integrate", mentions a system
that doesn't exist yet.

**Big bet** — Architectural decision, major feature, uncertain scope, multiple
systems affected, design uncertainty. Signals: "redesign", "rethink",
"architecture", "platform", touches 3+ systems, user says "think bigger".

**T0 (spike)** — Throwaway prototype, exploration, learning. Signals: "spike",
"explore", "prototype", "try", "experiment". For T0, skip the pipeline and
just build. Tell the user: "T0 spike detected. Skipping planning pipeline.
Build directly." Then stop.

If the tier is ambiguous, present the options via AskUserQuestion:

> Classifying your task for the planning pipeline.
>
> RECOMMENDATION: Choose [X] because [reason].
>
> A) T2 (standard) — `/define refine` then `/plan`
> B) T1 (new feature) — `/define discover` then `/challenge` then `/plan`
> C) Big bet — `/define discover` then `/elevate` then `/challenge` then `/plan`
> D) T0 (spike) — skip pipeline, just build

---

## Step 1: Detect UI Scope

Check the task description and any referenced files for UI terms: component,
screen, form, button, modal, layout, dashboard, sidebar, nav, dialog, page,
view, render. Require 2+ matches (exclude false positives like "page" alone).

If UI scope detected, `/plan-design-review` will run after `/plan`.

Output: "Tier: [T2/T1/Big bet]. UI scope: [yes/no]. Starting pipeline."

---

## The 6 Decision Principles

These rules auto-answer every intermediate question:

1. **Choose completeness** — Ship the whole thing. Pick the approach that covers more edge cases.
2. **Boil lakes** — Fix everything in the blast radius (files modified by this plan + direct importers). Auto-approve expansions that are in blast radius AND < 1 day effort (< 5 files, no new infra).
3. **Pragmatic** — If two options fix the same thing, pick the cleaner one. 5 seconds choosing, not 5 minutes.
4. **DRY** — Duplicates existing functionality? Reject. Reuse what exists.
5. **Explicit over clever** — 10-line obvious fix > 200-line abstraction. Pick what a new contributor reads in 30 seconds.
6. **Bias toward action** — Flag concerns but don't block.

**Conflict resolution (context-dependent tiebreakers):**
- `/define` phase: P1 (completeness) + P6 (action) dominate.
- `/challenge` phase: P5 (explicit) + P3 (pragmatic) dominate.
- `/plan` phase: P5 (explicit) + P1 (completeness) dominate.

---

## Decision Classification

Every auto-decision is classified:

**Mechanical** — one clearly right answer. Auto-decide silently.
Examples: include tests (always yes), use existing toolbelt (always yes),
reduce scope on a complete plan (always no).

**Taste** — reasonable people could disagree. Auto-decide with recommendation,
but surface at the final gate. Three natural sources:
1. **Close approaches** — top two are both viable with different tradeoffs.
2. **Borderline scope** — in blast radius but ambiguous whether to include.
3. **Cross-model disagreements** — debate.py models recommend differently and both have valid points.

**User Challenge** — both models agree the user's stated direction should change.
This is NEVER auto-decided.

User Challenges go to the final approval gate with richer context:
- **What the user said:** (their original direction)
- **What the models recommend:** (the change)
- **Why:** (the models' reasoning)
- **What context we might be missing:** (explicit acknowledgment of blind spots)
- **If we're wrong, the cost is:** (what happens if the user's original direction was right)

The user's original direction is the default. The models must make the case for
change, not the other way around.

---

## What "Auto-Decide" Means

Auto-decide replaces the USER's judgment with the 6 principles. It does NOT
replace the ANALYSIS. Every section in the invoked skills must still be executed
at full depth. The only thing that changes is who answers intermediate questions:
you do, using the 6 principles, instead of the user.

**Two exceptions — never auto-decided:**
1. Premises (in `/define`) — require human judgment about what problem to solve.
2. User Challenges — when models agree the user's stated direction should change.

**You MUST still:**
- READ the actual code, diffs, and files each section references
- PRODUCE every output the section requires
- IDENTIFY every issue the section is designed to catch
- DECIDE each issue using the 6 principles (instead of asking the user)
- LOG each decision in the audit trail

**You MUST NOT:**
- Compress a review section into a one-liner
- Write "no issues found" without showing what you examined
- Skip a section because "it doesn't apply" without stating what you checked
- Produce a summary instead of the required output

---

## Sequential Execution — MANDATORY

Skill invocations MUST execute in strict order per the tier's chain.
Each skill MUST complete fully before the next begins.
NEVER run skills in parallel — each builds on the previous.

Between each skill, emit a phase-transition summary and verify that all
required outputs from the prior skill are written before starting the next.

---

## Pipeline Execution

### T2 Pipeline: `/define refine` -> `/plan` -> (if UI: `/plan-design-review`)

**Phase 1: `/define refine`**
Invoke `/define` with `refine` argument. Auto-decide intermediate questions
using the 6 principles.
GATE: Present the 5 forcing questions and answers to the user for confirmation.
This is the ONE question that is NOT auto-decided.

**Phase 2: `/plan`**
Invoke `/plan`. Auto-decide intermediate questions.

**Phase 3 (conditional): `/plan-design-review`**
If UI scope was detected in Step 1, invoke `/plan-design-review`. Auto-decide.

### T1 Pipeline: `/define discover` -> `/challenge` -> `/plan` -> (if UI: `/plan-design-review`)

**Phase 1: `/define discover`**
Invoke `/define` with `discover` argument. Auto-decide intermediate questions.
GATE: Present premises to user for confirmation.

**Phase 2: `/challenge`**
Invoke `/challenge`. Auto-decide intermediate questions using P5 + P3.

**Phase 3: `/plan`**
Invoke `/plan`. Auto-decide intermediate questions.

**Phase 4 (conditional): `/plan-design-review`**
If UI scope was detected, invoke `/plan-design-review`. Auto-decide.

### Big Bet Pipeline: `/define discover` -> `/elevate` -> `/challenge` -> `/plan` -> (if UI: `/plan-design-review`)

**Phase 1: `/define discover`**
Invoke `/define` with `discover` argument. Auto-decide intermediate questions.
GATE: Present premises to user for confirmation.

**Phase 2: `/elevate`**
Invoke `/elevate`. Auto-decide intermediate questions using P1 + P6.

**Phase 3: `/challenge`**
Invoke `/challenge`. Auto-decide intermediate questions using P5 + P3.

**Phase 4: `/plan`**
Invoke `/plan`. Auto-decide intermediate questions.

**Phase 5 (conditional): `/plan-design-review`**
If UI scope was detected, invoke `/plan-design-review`. Auto-decide.

---

## Final Approval Gate

After the pipeline completes, present ALL deferred decisions to the user in
a single AskUserQuestion. Group by type:

### Taste Decisions
For each, show:
- The decision point
- What was auto-decided and which principle applied
- The alternative that was close

### User Challenges (if any)
For each, show the full context block (what user said, what models recommend,
why, blind spots, cost of being wrong).

### Summary
- Total decisions auto-made: N
- Taste decisions deferred: M
- User challenges: K
- Pipeline result: [plan artifact path]

Options:
- A) Approve all auto-decisions, proceed to build
- B) Review taste decisions one by one
- C) Reject — revert to pre-pipeline state

If B: walk through each taste decision with individual AskUserQuestion calls.
If C: no changes are committed.

---

## Completion Status Protocol

When completing, report status using one of:
- **DONE** — All steps completed. Evidence provided.
- **DONE_WITH_CONCERNS** — Completed with issues. List each concern.
- **BLOCKED** — Cannot proceed. State what is blocking and what was tried.
- **NEEDS_CONTEXT** — Missing information. State exactly what you need.

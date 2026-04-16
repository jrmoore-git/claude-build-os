---
debate_id: autobuild
created: 2026-04-16T07:57:17-0700
phase: refine
rounds: 3
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: yes
---
# autobuild — Refined Document

## Round 1 (gemini-3.1-pro)
[ERROR: LLM call failed (InternalServerError): Error code: 503 - {'error': {'message': 'litellm.ServiceUnavailableError: GeminiException - {\n  "error": {\n    "code": 503,\n    "message": "This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.",\n    "status": "UNAVAILABLE"\n  }\n}\n. Received Model Group=gemini-3.1-pro\nAvailable Model Group Fallbacks=None', 'type': None, 'param': None, 'code': '503'}}]

## Round 2 (gpt-5.4)
The current revision is directionally strong: it clearly identifies the product gap, keeps the proposal scoped to Build OS itself, and preserves the end-to-end pipeline framing. It also avoids inventing unnecessary new subsystems in several places.

However, it still has four material problems, all matching the accepted challenges:

1. **Escalation mechanism is mis-specified.**
   The draft repeatedly cites “trigger #4,” “trigger #5,” “7 escalation triggers,” and `workflow.md`, but those references are not reliable per the accepted challenge. This is a core regression because the proposal’s main safety model depends on a mechanism that is not concretely defined in the document. The fix is to define the build-time escalation policy explicitly in the proposal itself.

2. **`surfaces_affected` is described as enforced when it is not.**
   The current text says agent edits “are checked” and that “no new hook needed,” which overstates the actual implementation. The accepted challenge requires a mandatory automated post-step scope check with hard stop/escalation on violations. That enforcement needs to be added as an explicit implementation requirement.

3. **Verification command execution crosses a trust boundary.**
   The draft still says to run `verification_commands` from the plan artifact. Because the plan is model-authored, that is too permissive. The proposal needs a safe execution policy: allowlisted command patterns, schema validation, and human approval for anything outside the allowlist.

4. **No context-window policy.**
   The draft acknowledges token/context risk but does not contain it. Since this mode chains multiple phases in one run, a v1 policy is required: bounded plan size, mandatory checkpoints, and pause/resume when remaining context falls below a defined threshold.

Additional improvement opportunities:
- The “Implementation Approach” is too optimistic in claiming “no new scripts, no new hooks.” That no longer holds once scope enforcement and verification-command validation are added. Better to keep the feature small but be honest that minimal helper enforcement is required.
- “Zero-risk” is overstated. Human review before merge lowers risk but does not eliminate local side effects during execution. The revised draft should narrow that claim.
- The recommendation count is effectively one major recommendation: add `--build` in the plan skill. That recommendation should be preserved, but narrowed and made executable with explicit guardrails rather than softened.

## Round 3 (claude-opus-4-6)
The previous revision is substantially improved over what a first draft would look like. It correctly addresses all four accepted challenges by:

1. Defining escalation stop conditions inline rather than referencing a nonexistent numbered trigger system
2. Adding a context-window management section with checkpoint/resume
3. Promoting `surfaces_affected` from soft prompt to hard enforcement with post-step diff checks
4. Adding a verification command safety section with allowlists and validation rules

**Remaining issues I'll address:**

1. **Redundancy between sections.** The escalation stop conditions appear in full in "Build Phase Behavior" (step 6), are summarized again in "Why Not," and appear a third time in "Proposed Changes" item 2. The scope enforcement story is told three times (steps 5, the standalone "Scope Containment" section, and Proposed Changes item 3). This bloats the document without adding information. I'll consolidate so each concept has one authoritative location and other sections reference it.

2. **"Small-plan only" is vague.** The context management section says `--build` is "allowed only for plans judged small enough" — but judged by whom, how? This needs a concrete heuristic, even if approximate.

3. **Checkpoint/resume artifact is under-specified.** The document says "emit a resume artifact" but doesn't say where it goes or what format it takes. Needs a concrete path.

4. **Scope enforcement mechanism is described but not specified.** "Run an automated diff-to-scope check" — using what? `git diff --name-only` against the plan's file list is the obvious answer but should be stated.

5. **The "Why Now" section's point 4 understates risk.** "Reduces deployment risk" is accurate but the parenthetical about local execution risk during the build loop should be more prominent given that this is the primary risk surface.

6. **Minor: "Self-Learning Dependency" section is well-positioned but the dismissal of gstack's approach could be sharper.** The current text hedges ("may be sufficient"). For a solo-dev context with `lessons.md` already working, this is sufficient for v1 — state it directly.

7. **Proposed Changes are well-preserved and map to the challenges.** I'll tighten language but preserve all five.

[NOTE: revision discarded — recommendation slots dropped (input had 14 recommendation slots, output has 5 + 0 CANNOT RECOMMEND = 5 total)]

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

Add a `--build` flag to `/plan --auto` that continues execution after the plan approval gate, but only under explicit build-time safety rules defined in this proposal.

The full pipeline becomes:

```bash
/plan --auto --build <task description>
```

Pipeline: think → challenge → plan → **[approval gate]** → build → test → iterate → review → ship-summary

### Build Phase Behavior

1. **Read the approved plan.** Parse `tasks/<topic>-plan.md` for:
   - ordered build steps
   - declared `surfaces_affected`
   - declared `verification_commands`

2. **Load project lessons before editing.**
   - Read `tasks/lessons.md`
   - Apply any relevant constraints or prior gotchas before starting implementation

3. **Implement sequentially by default.**
   - Execute each build step in order
   - Only use parallel worktrees when the plan has already decomposed work into isolated tracks and each track maps to a non-overlapping file scope

4. **Run verification after each step.**
   - Execute only validated verification commands
   - If verification fails, attempt to fix the failure and re-run verification
   - Maximum 3 implementation attempts per step; on the third failure, stop and escalate

5. **Run mandatory scope enforcement after each step.**
   - Compare the actual changed files against the plan’s `surfaces_affected`
   - If any changed file is outside the allowed set, stop immediately and escalate before any further edits

6. **Escalate on defined build-time stop conditions.**
   Autobuild v1 does not depend on a separately referenced numbered trigger system. The build mode must define and enforce the following explicit stop conditions:

   - **Repeated-failure stop:** 3 failed implementation/verification attempts on the same step
   - **Scope-growth stop:** any modified file outside `surfaces_affected`
   - **Security-sensitive stop:** authentication, authorization, secrets, credentials, permissions, data deletion, payment flows, externally exposed network behavior, or sandbox/escape-related changes
   - **Irreversible-side-effect stop:** commands or code paths that delete data, rewrite history, mutate production-like state, perform destructive migrations, or trigger non-local side effects
   - **Ambiguity stop:** requirements ambiguity that changes behavior in a user-visible or API-visible way
   - **Architecture-decision stop:** a required implementation choice that changes architecture beyond what the approved plan specified
   - **Constraint-conflict stop:** the approved plan, repository state, and test results cannot all be satisfied at once without revising the plan

   On any stop condition, autobuild pauses, prints:
   - the current step
   - the blocking condition
   - the files touched
   - the failing command or decision point
   - the minimum question the human must answer

7. **Decision classification during build.**
   Reuse the existing 3-tier decision model conceptually, but define its behavior directly here:

   - **Mechanical:** One clearly correct answer from existing codebase patterns. Auto-decide silently.
   - **Taste:** Multiple acceptable answers with no behavior change. Auto-decide, but log the choice in the build summary.
   - **User Challenge:** Multiple defensible answers with behavior, API, schema, or UX impact. Stop and ask.

8. **After all steps complete:**
   - Run the final validated verification set
   - If passing, auto-invoke `/review`
   - Generate ship summary using the existing `/ship` summary format

## What the Human Does

- Writes the task description (one sentence to one paragraph)
- Approves the plan at the approval gate
- Answers escalation questions if they arise during build
- Reviews the `/review` output and approves merge/ship

## Self-Learning Dependency

gstack's design doc argues autobuild depends on self-learning infrastructure ("without memory it repeats the same mistakes"). For Build OS:

- `tasks/lessons.md` already captures gotchas and patterns
- `/start` already loads lessons at session start
- The build phase should read `tasks/lessons.md` for the relevant domain before implementing

This is lighter than gstack's planned per-project JSONL learning store, but may be sufficient for a solo dev where the human is the learning system. If autobuild produces recurring mistakes that `lessons.md` does not catch, that is signal to invest in structured learning later, not a blocker for v1.

## Scope Containment

The plan artifact already declares `surfaces_affected` (file list). In v1, this is not just guidance; it becomes an enforced boundary.

### Required Enforcement

After every build step:

1. collect the set of files changed by the agent since the previous checkpoint
2. compare that set to `surfaces_affected`
3. if the changed set is not a subset of `surfaces_affected`, stop immediately
4. surface the violating files to the human and require either:
   - explicit approval to amend the plan, or
   - rollback of the out-of-scope edits

This is a hard stop, not a prompt reminder. Prompt-only scope containment is insufficient for autonomous execution.

### Parallel Work Constraints

Parallel worktrees are allowed only when:
- each track has its own explicit file subset
- those subsets do not overlap
- each worktree runs its own post-step scope check before merge-back

## Verification Command Safety

`verification_commands` in the plan artifact cross a trust boundary because the plan is model-authored. Autobuild v1 must not execute arbitrary shell commands copied directly from the plan markdown.

### v1 Execution Policy

Autobuild may execute verification commands only if they match an approved safe subset, such as:

- test runners already used in the repo
  - `npm test`
  - `pnpm test`
  - `pytest`
  - `go test ./...`
  - repo-specific test scripts already present in package/task config
- linters/formatters already used in the repo
  - `npm run lint`
  - `pnpm lint`
  - `ruff check`
  - `cargo fmt --check`
- build/typecheck commands already defined in repo config
  - `npm run build`
  - `tsc --noEmit`

The exact allowlist should be derived from commands already declared in repository configuration files or a dedicated approved-command list.

### Validation Rules

A verification command is executable only if all of the following are true:
- it matches an allowlisted executable or repo-declared script
- it contains no shell chaining or redirection
- it contains no environment mutation
- it contains no network fetch/install behavior
- it contains no file deletion or rewrite behavior outside normal build artifacts

Examples that must require human confirmation or be rejected in v1:
- commands using `&&`, `;`, pipes, command substitution, or output redirection
- `curl`, `wget`, `bash <script>`, package installs, or ad hoc shell scripts
- destructive commands such as `rm`, `git reset --hard`, migration-apply commands, or data loaders against non-ephemeral targets

If a plan includes any verification command outside the approved subset, autobuild stops and asks the human to approve or replace it.

## Context Window Management

Long build/test/iterate loops are a predictable failure mode for this design. Autobuild v1 must therefore include an explicit context-budget policy.

### v1 Policy

Autobuild runs only when all of the following are true at plan approval time:
- the approved plan contains a bounded number of implementation steps
- the plan fits within a single execution session without requiring large unrelated codebase exploration
- the verification set is limited enough to run after each step

Because no repository-specific context budget data is provided here, the v1 rule is qualitative and enforced operationally:

1. **Small-plan only.** `--build` is allowed only for plans judged small enough to execute in one bounded session.
2. **Checkpoint after every step.** After each build step, autobuild records a compact execution summary:
   - step completed
   - files changed
   - verification run
   - result
   - open issues
3. **Pause/resume on low context.** If the session approaches context exhaustion, autobuild stops at the next checkpoint and emits a resume artifact containing:
   - remaining steps
   - current diffs
   - last verification result
   - active blockers
4. **No silent compression.** Autobuild must not continue across heavy truncation without emitting a checkpointed handoff.

This keeps v1 usable without pretending long, multi-hour autonomous runs are solved.

## Why Now

1. All surrounding pieces exist: `/plan --auto`, `/review`, `/ship` with spec-mapped summaries, and the decompose gate.
2. The gap between "plan exists" and "code exists" is where the most human time is spent.
3. Both gstack and the CloudZero analysis identify this as the key missing capability.
4. Build OS itself is the right first repository because the human still reviews the plan, answers escalations, and reviews output before merge. That reduces deployment risk, though it does not eliminate local execution risk during the build loop.

## Why Not

1. The build phase requires the most judgment. Plans are abstract; implementation is concrete. An agent that follows a plan literally may miss context the plan did not capture.
2. Iteration quality degrades: attempt 1 is informed, attempt 2 is a reasonable fix, attempt 3 is often flailing. That is why v1 hard-stops after 3 failed attempts on the same step.
3. Token cost and context pressure are real. A full autobuild run can consume substantial context across planning, implementation, testing, and review, so v1 must stay constrained to bounded plans with checkpointed pause/resume.
4. Scope creep risk is highest during implementation, not planning. That is why `surfaces_affected` must be enforced automatically after every step.
5. Verification execution is a security boundary. Model-authored markdown must not become arbitrary shell input.

## Implementation Approach

Add a `## --build Mode (Autonomous Build Pipeline)` section to `.claude/skills/plan/SKILL.md` after the existing `--auto` section, and add the minimum enforcement needed to make build mode safe in practice.

### Required v1 Additions

1. **Build-mode instructions in `plan/SKILL.md`**
   - approved pipeline behavior
   - explicit escalation stop conditions
   - decision classification rules
   - checkpoint/resume behavior

2. **Scope enforcement helper**
   - immediate post-step diff check against `surfaces_affected`
   - hard stop on violations

3. **Verification command validator**
   - parse `verification_commands`
   - allow only approved command forms
   - require human confirmation for anything outside the safe subset

4. **Checkpoint/resume artifact**
   - compact step-by-step handoff state for long runs or low-context pauses

5. **`/review` handoff**
   - invoke existing `/review` only after final verification passes

This remains a small v1 if implemented narrowly, but it is not "no new scripts, no new hooks." Minimal enforcement is required because prompt-only guardrails are not sufficient for autonomous execution.

## Proposed Changes

1. **Add `/plan --auto --build` as a bounded v1 feature for small approved plans only.**
   Preserve the existing recommendation to extend `/plan --auto`, but narrow it to a constrained first release:
   - sequential execution by default
   - optional parallel worktrees only for pre-decomposed, non-overlapping scopes
   - mandatory per-step verification
   - mandatory human pause on defined stop conditions

2. **Define autobuild’s escalation policy inside the build-mode spec instead of referencing a missing numbered trigger system.**
   The v1 spec must explicitly include:
   - repeated-failure stop conditions
   - scope-growth handling
   - security-sensitive changes
   - irreversible side effects
   - ambiguity, architecture, and constraint-conflict stops

3. **Make `surfaces_affected` a hard enforcement mechanism, not a soft prompt.**
   After each implementation step, run an automated diff-to-scope check and stop immediately on violations. No further edits proceed until the human approves a plan amendment or reverts the out-of-scope changes.

4. **Treat `verification_commands` as untrusted input and execute only a validated safe subset.**
   Approved commands must come from an allowlisted schema or existing repo-declared scripts. Any command outside that subset requires human confirmation and is not auto-executed in v1.

5. **Add a context-budget operating rule for long builds.**
   `--build` runs only on bounded plans, emits a checkpoint after every step, and pauses with a resumable handoff when context becomes tight. V1 does not promise uninterrupted long-horizon autonomous execution.

## Estimated Scope

Primary behavior change: add build-mode instructions to `.claude/skills/plan/SKILL.md`.

Additional required support:
- one scope-enforcement check
- one verification-command validation path
- one lightweight checkpoint/resume artifact

The original estimate of "~60-80 lines added to plan/SKILL.md" is too low if v1 includes the required hard guardrails. A small implementation is still realistic, but the scope should be described as: **small feature plus minimal enforcement helpers**, not as a pure documentation edit.

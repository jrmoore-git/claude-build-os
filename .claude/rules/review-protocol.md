---
description: Phase gate review process and debate protocol
globs:
  - "tasks/phase*-review*"
  - "tasks/*-proposal*"
  - "tasks/*-challenge*"
  - "tasks/*-debate*"
  - "tasks/*-resolution*"
---

# Review Protocol

HARD RULE: No commit without the appropriate review.

## 3-Stage Skill Chain

Quality assurance maps to lifecycle stages. The user chooses which stages to run based on the nature of the change.

### Stage 1: `/challenge` -- Should we build this?

Cross-model gate before `/plan`. Multi-persona panel (architect, security, pm, frame) independently evaluates whether proposed work is necessary and appropriately scoped.

**Frame lens:** Debate output quality is bounded by proposal frame quality. Three personas critiquing the candidates inside a proposal cannot escape a flawed candidate set — they optimize within it. The Frame lens is the structural fix: a 4th persona whose only job is to critique what the candidate set is missing (binary framings, missing compositional candidates, source-driven proposals inheriting their source's frame, problem inflation). With `--enable-tools`, frame expands into two parallel halves: `frame-structural` (no tools, reasons from proposal alone — catches what should exist) and `frame-factual` (tools on, verifies proposal claims against codebase — catches "already shipped" / staleness). Evidence: across n=5 historical proposals, the dual-mode frame caught ~30 novel MATERIAL findings beyond the original 3-persona panel and flipped one verdict from REVISE to REJECT (proposal targeted a feature already shipped). See `tasks/lessons.md` L43.

**When to run:** New features, abstractions, scope expansion, new dependencies.
**Skip conditions:** Defined authoritatively in CLAUDE.md. Do not maintain a separate list here.

Output: `tasks/<topic>-challenge.md` with recommendation (proceed / simplify / pause / reject).

### Stage 2: `/challenge --deep` -- How should we build it?

Full adversarial pipeline: challenge -> judge -> refine. Produces a refined spec.

**When to run:** Architectural decisions, PRD changes, schema changes, design uncertainty.
**When to skip:** Simple features where the approach is obvious.

Output: `tasks/<topic>-debate.md`, `tasks/<topic>-judgment.md`, `tasks/<topic>-refined.md`.

### Stage 3: `/review` -- Is the implementation correct?

Cross-model code review. Three models review the diff through independent lenses (PM, Security, Architecture). If `tasks/<topic>-refined.md` exists, PM lens escalates to strict spec compliance.

**When to run:** Every non-trivial change, before commit. Modes: `--second-opinion`, `--qa`, `--governance`, `--all`.

Output: `tasks/<topic>-review.md`.

### Optional: `/polish` -- Make it better

6-round cross-model collaborative improvement. Standalone on any input (plan, design, answer). Not adversarial — just iterative quality improvement across 3 model families.

**When to run:** You have a draft and want it sharper. Plans before building, designs before challenge, answers to complex questions.
**When to skip:** The document is already tight, or time pressure makes 6 rounds impractical.

Output: `tasks/<topic>-refined.md`.

Note: `/polish` also runs as the final phase of `/challenge --deep`. The standalone `/polish` skill skips the adversarial phases.

### Typical paths by change type

Tier definitions and full pipeline routes: see CLAUDE.md.

## Cross-Model Debate Engine

Tool: `scripts/debate.py`. See `docs/reference/debate-invocations.md` for full invocation patterns.

**`[TRIVIAL]` bypass:** Include in commit message for typo/doc-only changes. Hook logs the bypass.

## Review Gate Hook

Advisory warnings (not hard blocks) for commits touching `skills/`, `*_tool.py`, `.claude/rules/`, hooks, or security files without debate artifacts. Valid artifacts: `tasks/*-challenge.md` or `tasks/*-debate.md` with YAML frontmatter + MATERIAL tag.

## Contract Tests

The essential eight invariants (6 applicable to BuildOS — see CLAUDE.md for applicability) guide every change. Add domain-specific invariants on top.

## Definition of Done

Behavior matches spec. Tests pass. Audit log shows expected events. Rollback plan exists. Negative tests run. Review completed via `/review`.

## Rule Enforcement

After writing a rule, deliberately test whether Claude follows it. If it doesn't trigger reliably, escalate: move closer to action point, add a hook, or make it architectural. Any enforcement hook must include its own file path in the set of files it checks -- a hook that doesn't check itself can be silently bypassed.

At 60% context: STOP and run review if not done. At 75%: run review NOW.

## Negative Examples from Dismissed Findings

When a `/review` finding is dismissed (confirmed false positive), append it here under the relevant lens. When `/review` is wired to read this section (future bundle), accumulated examples will be passed to lens prompts as patterns not to re-flag. Until then, this file is a manual ledger of dismissed findings — the content accrues now so the wiring has data to use later.

### PM lens negative examples
<!-- append dismissed PM-lens findings as markdown list items -->
- **"Missing Phase 1 test file that plan explicitly schedules for Phase 3".** Flagged in `tasks/arm-comparison-methodology-validation-review.md` (2026-04-19) against `tests/test_arm_study_verdict.py`. Dismissal: plan's Phase 3 Files row names the file as Phase 3 scope; Phase 1 verification command explicitly omits it. Before flagging a missing test file as a Phase 1 spec violation, grep the plan for the filename and read the Phase table that contains it — the plan may schedule it to a later phase.
- **"File missing from the diff" when the file is gitignored by project convention.** Flagged in `tasks/arm-comparison-methodology-validation-review.md` (2026-04-19) against `tasks/arm-study-workload-inventory.md`. Dismissal: `.gitignore` excludes all `tasks/*.md` artifacts; the file exists on disk but is never tracked. Before flagging a missing file as a deliverable gap, `ls` the path on disk — a gitignored file that exists still satisfies the deliverable.

### Security lens negative examples
<!-- append dismissed Security-lens findings -->
- **"Scorer should ingest Layer 1 baseline from a superseded spec clause".** Flagged in `tasks/arm-comparison-methodology-validation-review.md` (2026-04-19): review lens claimed the scorer should consume `debate.py compare` output as Layer 1. Dismissal: D37 decision record supersedes this — scorer drives `debate.py review --models` with a custom prompt, NOT `debate.py compare`. Before flagging a "missing integration with prior-art," check the decisions log for supersession of the prior-art reference.

### Architecture lens negative examples
<!-- append dismissed Architecture-lens findings -->
- **Hardcoded fallback config (`_DEFAULT_PERSONA_MODEL_MAP`) diverges from JSON config — "revert is incomplete".** Flagged in `tasks/opus-4-7-revert-review.md` (2026-04-18) by both architect and security lenses. Dismissal: `scripts/debate_common.py:_DEFAULT_PERSONA_MODEL_MAP` is a degraded-mode safety net; divergence from production config is by design. Before flagging a fallback-vs-config gap as "revert incomplete," check inline comments and `git log -S` for the fallback's history — if the fallback was never the reverted value, it isn't in scope.
- **"Orchestrator omits persona present in `persona_model_map` — study won't match production".** Flagged in `tasks/arm-comparison-methodology-validation-review.md` (2026-04-19) against `staff` persona in `config/debate-models.json`. Dismissal: `persona_model_map` is the full persona vocabulary, not the `/challenge` invocation list. Production `/challenge` SKILL.md invokes only `architect,security,pm,frame`; orchestrator's `DEFAULT_PERSONAS` matches that. Before flagging a persona-list mismatch, grep the invocation site (skill, hook, CLI flag) — the model map lists what's available, not what's used.
- **"Missing test file that is not in the plan's Files table".** Flagged in `tasks/arm-comparison-methodology-validation-review.md` (2026-04-19) against `tests/test_arm_study_orchestrator.py`. Dismissal: plan's Files table enumerates Phase 1 deliverables; the missing file was not among them. Before flagging a missing test, confirm the plan actually requires it rather than inferring from "non-trivial logic exists."
- **"File handle opened via `argparse.FileType('r')` is never explicitly closed — resource leak / inconsistent lifecycle".** Flagged in `tasks/polish-system-context-review-debate-v2.md` (2026-04-19) against the new `--system-context` flag in `scripts/debate.py cmd_refine`. Dismissal: the existing `--document` flag in the same function (line 2891) reads via `.read()` without explicit close; this is the established pattern for single-run CLI scripts. Fixing only the new flag creates arbitrary inconsistency; fixing both is an unrelated cleanup. Before flagging unclosed `argparse.FileType` handles in short-lived CLI scripts, check whether sibling flags in the same function follow the same pattern — a "fix" that diverges from local convention isn't a fix.
- **"Sanity check is doc-only / procedural, not executable skill logic — original failure mode can persist if operators don't follow markdown".** Flagged in `tasks/polish-system-context-review-debate-v2.md` (2026-04-19) against the polish skill's `rounds_successful == 0 → DONE_WITH_CONCERNS` rule. Downgrade rationale: BuildOS skills ARE markdown instructions to the LLM — there is no separate "executable skill logic" layer below them. Adding a validator script for this one skill breaks framework consistency; the concern is framework-level, not bug-level. Before flagging a skill rule as "doc-only," check whether the skill framework has an executable layer at all — in BuildOS, the skill body IS the implementation.

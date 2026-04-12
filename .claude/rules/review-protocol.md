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

Cross-model gate before `/plan`. Three models independently evaluate whether proposed work is necessary and appropriately scoped.

**When to run:** New features, abstractions, scope expansion, new dependencies.
**When to skip:** Bugfixes, test additions, docs, trivial refactors -> `/plan --skip-challenge`.

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

- **Bugfix:** `/plan --skip-challenge` -> build -> `/review` -> `/ship`
- **Small feature:** `/challenge` -> `/plan` -> build -> `/review` -> `/ship`
- **Improve a plan/design:** `/polish` (standalone, no adversarial framing)
- **Architectural change:** `/challenge` -> `/plan` -> `/challenge --deep` -> build -> `/review` (with spec compliance) -> `/ship`

## Cross-Model Debate Engine

Tool: `scripts/debate.py`. See `reference/debate-invocations.md` for full invocation patterns.

**`[TRIVIAL]` bypass:** Include in commit message for typo/doc-only changes. Hook logs the bypass.

## Review Gate Hook

Advisory warnings (not hard blocks) for commits touching `skills/`, `*_tool.py`, `.claude/rules/`, hooks, or security files without debate artifacts. Valid artifacts: `tasks/*-challenge.md` or `tasks/*-debate.md` with YAML frontmatter + MATERIAL tag.

## Contract Tests

The essential eight invariants apply to every change: idempotency, approval gating, audit completeness, degraded mode visible, state machine validation, rollback path exists, version pinning enforced, exactly-once scheduling. Add domain-specific invariants on top.

## Definition of Done

Behavior matches spec. Tests pass. Audit log shows expected events. Rollback plan exists. Negative tests run. Review completed via `/review`.

## Rule Enforcement

After writing a rule, deliberately test whether Claude follows it. If it doesn't trigger reliably, escalate: move closer to action point, add a hook, or make it architectural. Any enforcement hook must include its own file path in the set of files it checks -- a hook that doesn't check itself can be silently bypassed.

At 60% context: STOP and run review if not done. At 75%: run review NOW.

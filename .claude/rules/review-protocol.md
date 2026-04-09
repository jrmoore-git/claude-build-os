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

### Stage 2: `/debate` -- How should we build it?

Full adversarial pipeline: challenge -> judge -> refine. Produces a refined spec.

**When to run:** Architectural decisions, PRD changes, schema changes, design uncertainty.
**When to skip:** Simple features where the approach is obvious.

Output: `tasks/<topic>-debate.md`, `tasks/<topic>-judgment.md`, `tasks/<topic>-refined.md`.

### Stage 3: `/review` -- Is the implementation correct?

Cross-model code review. Three models review the diff through independent lenses (PM, Security, Architecture). If `tasks/<topic>-refined.md` exists, PM lens escalates to strict spec compliance.

**When to run:** Every non-trivial change, before commit.

Output: `tasks/<topic>-review.md`.

### Optional: `/refine` -- Make it better

6-round cross-model collaborative improvement. Standalone on any input (plan, design, answer). Not adversarial — just iterative quality improvement across 3 model families.

**When to run:** You have a draft and want it sharper. Plans before building, designs before challenge, answers to complex questions.
**When to skip:** The document is already tight, or time pressure makes 6 rounds impractical.

Output: `tasks/<topic>-refined.md`.

Note: `/refine` also runs as the final phase of `/debate`. The standalone `/refine` skill skips the adversarial phases.

### Typical paths by change type

- **Bugfix:** `/plan --skip-challenge` -> build -> `/review` -> `/ship`
- **Small feature:** `/challenge` -> `/plan` -> build -> `/review` -> `/ship`
- **Improve a plan/design:** `/refine` (standalone, no adversarial framing)
- **Architectural change:** `/challenge` -> `/plan` -> `/debate` -> build -> `/review` (with spec compliance) -> `/ship`

## Cross-Model Debate Engine

Tool: `scripts/debate.py`. Run `debate.py --help` for full usage.

Both `/challenge` and `/debate` invoke `debate.py`. The `/review` skill also uses it for cross-model code review.

Models: Claude Opus 4.6 (architect), Gemini 3.1 Pro (staff + PM), GPT-5.4 (security + judge). Refinement rotates all three (gemini -> gpt -> claude). Before judging, multi-challenger findings are automatically consolidated (deduplicated and merged with corroboration notes). Use `--no-consolidate` to skip consolidation.

**Security BLOCKING VETO on external code** is not subject to override. For all other work, security weight is controlled by `--security-posture` (1-5). At posture 1-2, security findings are advisory; PM is the final arbiter. At 4-5, security can block. Default: 3 (balanced).

## Legacy Tier Classification

`scripts/tier_classify.py` is used by the plan gate hook and `/ship` for protected path enforcement. `/review` no longer routes by tier -- it always runs cross-model review.

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

---
description: Session management, documentation-first, context budgeting
---

# Session Discipline Rules

## Document First, Execute Second
- Every correction, decision, or process change must be persisted to the correct document BEFORE implementation
- If session ends after documenting but before implementing, nothing is lost
- Instructions given in chat but not written to docs get lost between sessions. The document is the deliverable.

## What Goes Where
| Change type | Document |
|---|---|
| Bug, gotcha, platform surprise | tasks/lessons.md |
| How Claude Code should behave | .claude/rules/*.md |
| Build specs / PRD discrepancies | Build plan (flag to user if PRD) |
| Phase status | tasks/todo.md |
| Decision with rationale | tasks/decisions.md |
| Session summary | tasks/session-log.md |

## Session Close Protocol (MANDATORY)
When context reaches ~60%, write to `tasks/session-log.md` FIRST:
- Decided: [bullets]
- Documented: [file + what changed]
- Implemented: [bullets]
- NOT Finished: [what remains, blockers]
- Next Session Should: [first thing to do, files to read]

Priority when context is low: 1. Session summary -> 2. Phase review -> 3. Implementation

## Standing Rules
- Do not ask for decisions already answered in the PRD.
- When you need credentials or OAuth clicks, STOP and say exactly what you need from the user. Don't guess or proceed without them.
- Consult `tasks/lessons.md` when working in a relevant area -- not mandatory every session, but check when the task touches a domain with known gotchas.

## Plan Mode
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately
- Decompose work into focused tracks -- context window limits kill long sessions

## Plan Gate (Protected Paths)

A commit-time hook (`scripts/hook-plan-gate.sh`) enforces plan-before-code discipline on protected paths. Config: `config/protected-paths.json`.

**Protected paths** (require a plan artifact before commit): `skills/**/*.md`, `scripts/*_tool.py`, `scripts/*_pipeline.py`, `.claude/rules/*.md`.

**Exempt paths** (always pass): `tasks/*`, `docs/*`, `tests/*`, `config/*`, `stores/*`.

**Plan artifact format** -- create `tasks/<topic>-plan.md` with YAML frontmatter:
```yaml
---
scope: "What this change does"
surfaces_affected: "What systems/files are touched"
verification_commands: "How to verify correctness"
rollback: "How to undo"
review_tier: "Tier 1|Tier 1.5|Tier 2"
verification_evidence: "Results of verification (must not be PENDING)"
---
```

**Bypass rules:**
- `[TRIVIAL]` -- **BLOCKED** for protected paths. LLMs misclassify complexity; this is the root cause being fixed.
- `[EMERGENCY]` -- **ALLOWED** with stderr warning. Audited in weekly review.

## Verification
- Never mark a task complete without proving it works
- Run tests, check logs, demonstrate correctness
- Ask: "Would a staff engineer approve this?"
- **Sanity-check data volumes, not just success codes.** A pipeline can return valid JSON with no errors and still be wrong. If the output count is inconsistent with what you know should exist, stop and investigate before proceeding.

## Context Budget
- Use `/compact` at 50% context usage -- don't wait for automatic compression
- Every LLM call must log the actual model that responded, not the model that was requested (fallback detection)

## Three-Strikes Escalation

If the same behavior has been corrected three times at the same level, escalate immediately. Promotion ladder: lesson -> rule -> hook -> architecture. Do not keep rewriting advisory text for a behavior that needs structural enforcement.

## Lesson Promotion Discipline

`tasks/lessons.md` is a **lean queue** (target: <=30 entries). Check for duplicates before adding. Promote recurring lessons to `.claude/rules/`. Triage at 30+ entries: archive one-offs and already-promoted items to `tasks/lessons-archived.md`.

## Large-Task Execution

The context window is expensive RAM; the filesystem is free storage. For complex multi-track work, write the plan to disk and execute against the file, not the conversation. Write plans, reviews, and state to files -- read selectively. If a skill runs in a loop (N items x M calls), process in batches to avoid quadratic context growth. Anti-pattern: loading 312K tokens "just in case" when 50K suffices.

## Commit Doc Update Rule (HARD RULE)

Every commit must include updates to ALL relevant tracking docs. Before committing, check:

- **tasks/decisions.md**: Any new decision? Add numbered entry with rationale.
- **tasks/session-log.md**: Focus, result, decisions, next steps, commit hash.
- **tasks/lessons.md**: Any surprise or gotcha? Add numbered entry.
- **PRD**: Any scope/integration/schedule change? Update the relevant section.
- **config/.env**: Any new credential or token? Already stored?

If none apply, state "No doc updates needed" in the commit message.

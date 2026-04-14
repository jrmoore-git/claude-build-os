---
description: Session management, documentation-first, context budgeting
---
<!-- Enforced-By: hooks/hook-plan-gate.sh, hooks/hook-review-gate.sh, hooks/hook-tier-gate.sh -->

# Session Discipline Rules

## Document First, Execute Second
- Decide, then document, then implement. Persist corrections and decisions after deciding on them and before implementing them.
- If session ends after documenting but before implementing, nothing is lost.
- Instructions given in chat but not written to docs get lost between sessions. The document is the deliverable.

## What Goes Where
| Change type | Document |
|---|---|
| Bug, gotcha, platform surprise | tasks/lessons.md |
| How Claude Code should behave | .claude/rules/*.md |
| Build specs / PRD discrepancies | Build plan (flag to owner if PRD) |
| Phase status | tasks/handoff.md |
| Decision with rationale | tasks/decisions.md |
| Session summary | tasks/session-log.md |

## Session Close Protocol (MANDATORY)
When context reaches ~55% (stage 1 of compaction protocol), write to `tasks/session-log.md` FIRST:
- Decided: [bullets]
- Documented: [file + what changed]
- Implemented: [bullets]
- NOT Finished: [what remains, blockers]
- Next Session Should: [first thing to do, files to read]

Priority when context is low: 1. Session summary → 2. Phase review → 3. Implementation

## Decisions Must Propagate to All References
Two failure modes, one rule: when a decision changes the state of something referenced in production files, the same commit must update all references.

- **Completed work:** When finishing something flagged as "NOT Finished" or "still pending" in a prior handoff, remove it from `docs/current-state.md` and `tasks/handoff.md`. Stale pending items propagate indefinitely across sessions.
- **Rejected work:** When a challenge or decision rejects a proposed feature, file, or abstraction, remove all references to it from production files (CLAUDE.md, rules, skills, config). A rejected proposal with live references is indistinguishable from a missing deliverable.

## Standing Rules
- Do not ask for decisions already answered in the PRD.
- When you need credentials or OAuth clicks, STOP and say exactly what you need from the user. Don't guess or proceed without them.
- Consult `tasks/lessons.md` when working in a relevant area — not mandatory every session, but check when the task touches a domain with known gotchas.

## Plan Mode
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately
- Decompose work into focused tracks — context window limits kill long sessions

## Plan Gate (Protected Paths)

Enforced by `scripts/hook-plan-gate.sh`. Protected paths require a `tasks/<topic>-plan.md` with valid YAML frontmatter (`scope`, `surfaces_affected`, `verification_commands`, `rollback`, `review_tier`, `verification_evidence`) before commit. Config: `config/protected-paths.json`. `[TRIVIAL]` blocked for protected paths; `[EMERGENCY]` allowed with warning.

Do not commit without the appropriate review. See review-protocol.md for review types and thresholds.

## Verification
Prove it works before calling it done. See review-protocol.md Definition of Done. Additionally: sanity-check data volumes, not just success codes — a pipeline can return valid JSON with no errors and still be wrong.

## Context Budget
- Every LLM call must log the actual model that responded, not the model that was requested (fallback detection)
- **What survives compaction** is controlled by the `## Compact Instructions` section in CLAUDE.md — update it if your session has unusual context needs

**Context rot is continuous, not cliff-edge.** Research (Chroma, 18 frontier models) shows meaningful degradation by ~25% context fill. At 50%, retrieval accuracy drops 30%+ for mid-context information. This cannot be hooked or gated — context % is not exposed to Claude Code hooks.

**Compaction protocol (what's enforceable):**
- **Auto-compact fires at ~95% capacity.** Built-in, cannot be changed. The `## Compact Instructions` section in CLAUDE.md controls what survives.
- **Manual `/compact`** at natural breakpoints: after completing a subtask, before switching phases, or when responses lose track of earlier context. Use `/compact focus on [next task]`.
- **State lives on disk, not in context.** Write decisions, progress, and blockers to `session-log.md` and `handoff.md` continuously. If it's on disk, don't carry it in context — reference the file path.
- **Prefer fresh sessions over deep compaction.** Heavily compacted sessions are brittle (lost-in-the-middle persists after compaction). Use `/wrap` to export state and start fresh rather than compacting repeatedly.
- **Before any review-protocol phase**, compact if the session has been long. Reviews need sharp retrieval.
- **Human lever:** run `/compact` when switching task phases or when Claude seems to drift. Smaller focused sessions > one marathon.

## Presenting Options

When presenting multiple approaches, alternatives, or options for the user to choose from, output them as **regular markdown text** in the conversation BEFORE using AskUserQuestion. The AskUserQuestion widget disappears when the user wants to discuss rather than pick immediately — the options must remain visible as reference material during the conversation.

**Anti-pattern:** Putting all option details only inside the AskUserQuestion tool call.
**Correct pattern:** Write numbered options as text → then AskUserQuestion for the selection.

## Three-Strikes Escalation

If the same behavior has been corrected three times at the same level, escalate immediately. Promotion ladder: lesson → rule → hook → architecture. Do not keep rewriting advisory text for a behavior that needs structural enforcement.

## Lesson Promotion Discipline

`tasks/lessons.md` is a **lean queue** (target: <=30 entries). Check for duplicates before adding. Promote recurring lessons to `.claude/rules/`. Triage at 30+ entries: archive one-offs and already-promoted items to `tasks/lessons-archived.md`.

**Lesson closure rule:** When a commit fixes a lesson, the same commit must update the lesson's status in `tasks/lessons.md` to Resolved (code fix shipped) or Promoted (rule/hook/architecture). A lesson left Active after its fix ships poisons future sessions — `/start` surfaces it as open work, other sessions waste time re-investigating.

## Large-Task Execution

The context window is expensive RAM; the filesystem is free storage. For complex multi-track work, write the plan to disk and execute against the file, not the conversation. Write plans, reviews, and state to files — read selectively. If a skill runs in a loop (N items × M calls), process in batches to avoid quadratic context growth. Anti-pattern: loading 312K tokens "just in case" when 50K suffices.

## Commit Doc Update Rule (HARD RULE)

Every commit must include updates to ALL relevant tracking docs. Before committing, check:

- **tasks/decisions.md**: Any new decision? Add numbered entry with rationale.
- **tasks/session-log.md**: Focus, result, decisions, next steps, commit hash.
- **tasks/lessons.md**: Any surprise or gotcha? Add numbered entry.
- **PRD**: Any scope/integration/schedule change? Update the relevant section.
- **config/.env**: Any new credential or token? Already stored?

If none apply, state "No doc updates needed" in the commit message.

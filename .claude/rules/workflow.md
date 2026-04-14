---
description: Session workflow, shipping discipline, orient-before-planning
---

# Workflow

1. **Orient before planning** — read `docs/project-prd.md` (if filled in for your project) + `docs/current-state.md` + `tasks/lessons.md` (relevant domain) + `tasks/session-log.md` (last entry) before proposing any plan. Then: read code before proposing changes. Enter plan mode if task touches >3 files, affects state/security, or adds a new integration. Skip for: one-line fixes, copy edits, obvious single-file changes.

Pipeline tiers: see CLAUDE.md. Skip conditions for `/challenge`: defined authoritatively in CLAUDE.md. Tier classification still governs review depth. Decision logic:

- `/think` has two modes: `discover` (full problem discovery, writes `tasks/<topic>-design.md`) and `refine` (5 forcing questions, writes `tasks/<topic>-think.md`). Use before `/challenge` or `/plan`.
- `/elevate` runs after `/think discover` to stress-test scope and ambition. 4 modes: SCOPE EXPANSION (dream big), SELECTIVE EXPANSION (hold + cherry-pick), HOLD SCOPE (rigor), SCOPE REDUCTION (strip to essentials). Reads the design doc from `/think discover`.
- `/challenge` gates whether we should build this at all. `/challenge --deep` runs the full adversarial pipeline (challenge → judge → refine). `/elevate` assumes we're building and reviews whether we're thinking big enough. Different questions, complementary.
- `/polish` = 6-round cross-model collaborative improvement. Standalone on any input (plan, design, answer), or as final phase of `/challenge --deep`.
- `/explore` = 3+ divergent directions with cross-model synthesis. For exploring options before committing.
- `/pressure-test` = counter-thesis or pre-mortem failure analysis. For adversarial analysis of a direction or plan.
2. **Document first, execute second** — decide, then document, then implement. See session-discipline.md for destination rules.
3. **Verify before done** — see review-protocol.md Definition of Done.
4. **Decompose before parallelizing** — see `.claude/rules/orchestration.md` for full heuristics. Quick check: 3+ independent subtasks with non-overlapping files → parallel subagents. Otherwise sequential. Skip for < 3 tool calls.
5. **Self-improve** — after any correction, update `tasks/lessons.md` with the pattern.
6. **Autonomous bug fixing** — just fix it, don't ask for hand-holding.
7. **Sync upstream docs** — update PRD, build plan, rules if decisions changed.
8. **Destructive commands** — before any mutating CLI command, check whether `--dry-run` exists. Some tools overwrite configuration silently with no undo path.
9. **Non-session sources** — after significant meetings or external conversations where decisions were made, capture to `tasks/lessons.md` and `tasks/decisions.md`.
10. **Search before building** — three knowledge layers: (1) tried-and-true patterns, (2) new-and-popular best practices (scrutinize — crowds can be wrong), (3) first-principles reasoning (most valuable). Before designing anything involving unfamiliar patterns or infrastructure, search for existing solutions first. The cost of checking is near-zero; the cost of reinventing is high. AI compression ratios: boilerplate ~100x, tests ~50x, features ~30x, bugfix ~20x, architecture ~5x, research ~3x — scope accordingly.

## Root Cause First — No Bandaids (HARD RULE)

When a data quality or behavior problem is reported:

1. **STOP.** No UPDATE statements, no backfill scripts, no row-level fixes.
2. **Trace the insertion path.** Read the code that creates the data. Identify why the wrong value is produced.
3. **Fix the insertion path.** The fix goes in the code that creates data, not downstream.
4. **Verify on NEW data.** Confirm the structural fix produces correct output.
5. **Only THEN backfill** existing data using the same code path.

**Anti-patterns (banned):**
- Writing UPDATE/backfill SQL before reading the insertion code
- Adding UI-side filtering to hide bad data instead of fixing the source
- Writing a "backfill script" as the primary deliverable
- Fixing N rows manually when the Nth+1 row will have the same problem

## Fix-Forward Rule

Never silently work around the same infrastructure failure twice. See bash-failures.md for the full fix-forward protocol.

## Shipping Discipline

**Priority stack:** broken > product > reliable > secure > elegant

**The goal:** The user opens the app and NEVER opens email, messaging, CRM, or calendar directly. If they leave the app to do something, that's a product failure.

**Milestone:** End-to-end loop: email → triage → draft → app → approve → sends.

**Remediation order:** broken now → breaks when enabled → breaks on reboot → security controls → everything else (by user value, not architectural purity).

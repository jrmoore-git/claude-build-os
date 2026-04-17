# Handoff — 2026-04-17 (late session: two audits landed, no ship)

## Session Focus
Ran the dual-mode-generalization audit to completion (per prior handoff), then pivoted scope to the higher-leverage Frame-reach question after user reframe. Both audits landed with clean verdicts. No code shipped beyond the `intake-check` primitive.

## Decided
- **Dual-mode pattern does NOT generalize uniformly across personas.** Architect passes 5/5, security fails at 4/5, pm fails at 2/5. Pre-committed 5/5 threshold held per L45. See `tasks/dual-mode-generalization-results.md`.
- **Frame-reach via intake-stage dual-mode fails the safety precondition.** Severity-level drift between intake and challenge stages makes MATERIAL-count reject/proceed signals unreliable; factual verification raises findings on any code-citing proposal (invalidating the "0 MATERIAL = clean" negative-control design). See `tasks/frame-reach-intake-audit-results.md`.
- **Architect dual-mode NOT shipped despite clean 5/5 pass.** User scope pivot from persona-level dual-mode to Frame-reach deprioritized the per-persona optimization. Architect ship remains a clean option for a future session if we want the isolated win; it's orthogonal to Frame-reach work.
- **Scope pivot itself is worth encoding as a decision.** D-entry added — "Improve the frame" is pipeline-stage work, not persona-duplication.

## Implemented
- `scripts/debate.py` — new `cmd_intake_check` subcommand + argparse + main dispatch (~25 LOC). Thin wrapper: forces `--personas frame` + `--enable-tools`, delegates to `cmd_challenge`. Composable primitive — NOT wired into `/challenge` as a gate.
- `tasks/dual-mode-generalization-*` — brief, plan, 30 run outputs across 3 personas, 3 per-persona analysis files, results.md with ADOPT/DECLINE verdicts, L43 extension.
- `tasks/frame-reach-intake-audit-*` — brief, plan, prompt spec, 6 intake run outputs, results.md with threshold-gate DECLINE verdict, L43 extension.
- `tasks/negative-control-verbose-flag-proposal.md` — synthetic minimal proposal used as negative control.
- `tasks/lessons.md` — L43 extended with per-persona generalization evidence + intake-reach DECLINE evidence.
- `tasks/decisions.md` — new D-entry (scope pivot from persona-dual-mode to Frame-reach).

## NOT Finished
- **Architect dual-mode ship.** Passed 5/5 threshold; shelved pending Frame-reach strategy. Decision: revive or leave alone, next session.
- **Judge/refine/premortem reach audits.** Deferred pending understanding of severity drift + factual-FP asymmetry learned from intake audit.
- **Autopilot `debate-efficacy-study-*` pile.** ~30 files still uncommitted across 3 sessions. Triage deferred again.
- **`tasks/multi-model-skills-roi-audit-*`** — off-scope design docs from earlier session, still on disk.

## Next Session Should
1. **Decide next direction** — read this handoff + `tasks/dual-mode-generalization-results.md` + `tasks/frame-reach-intake-audit-results.md`. Three real options:
   - (A) Revive architect dual-mode ship — clean 5/5 pass, orthogonal to Frame-reach, ~60-90 min work + /review. Low risk, bounded scope.
   - (B) Design intake-integration-v2 with a different reject/proceed signal (not MATERIAL count) that accounts for severity drift + factual-FP. Open-ended design work.
   - (C) Audit judge-stage frame-reach — different failure-mode structure from intake. Fresh design, learn from intake's FP issue.
   - (D) Triage the autopilot `debate-efficacy-study-*` pile — absorb/commit/delete. Session-hygiene task.
2. **DO NOT re-litigate the DECLINE verdicts.** Per L45 and the plan's explicit threshold-lock language, the 5/5-bidirectional and the three intake gates are final for this audit. Any revival must be a NEW experiment with NEW pre-committed criteria + re-validation.
3. **DO NOT assume the `intake-check` primitive is production-ready.** It exists as a composable CLI command; wiring it into any skill as an automatic gate requires solving the severity-drift + factual-FP issues Gate 3 exposed.

## Key Files Changed
- `scripts/debate.py` — +25 LOC (intake-check)
- `tasks/lessons.md` — L43 extended twice
- `tasks/decisions.md` — new D-entry (this session's scope pivot)
- `stores/debate-log.jsonl` — ~34 new entries from audit runs
- `tasks/dual-mode-generalization-*` — 30 run outputs + 3 analyses + results + brief + plan
- `tasks/frame-reach-intake-audit-*` — 6 run outputs + results + brief + plan + prompt
- `tasks/negative-control-verbose-flag-proposal.md` — new synthetic control

## Doc Hygiene Warnings
- None new this session. Autopilot `debate-efficacy-study-*` pile carryover from prior sessions noted in current-state.md — still not this session's work, still not committed.

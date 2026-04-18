# Current State — 2026-04-18 (morning: judge-stage Frame directive + novelty gate)

## What Changed This Session
- **Judge-stage Frame directive shipped** as a prompt-only addition to `JUDGE_SYSTEM_PROMPT`. Five frame-defect categories (already-shipped, inflated-problem, false-binary, inherited-frame, unstated-assumption). Novelty test requires the model to state the required fix and verify no existing challenger finding covers it — reframes tagged "covered by Challenge [N]" instead of counted as MATERIAL. D30.
- **SPIKE verdict renamed INVESTIGATE** throughout the judge prompt, output format, parser regex, and log field names. Breaking change to the `judge` JSON output schema (`spiked`→`investigating`, `blocking_spikes`→`blocking_investigations`, `needs_test`→`needs_investigation`) — no external consumer reads these fields.
- **L46 added:** Frame-critique directives must include an explicit novelty gate or the model reframes existing findings and inflates MATERIAL counts without adding signal. Negative-control behavior is the test, not MATERIAL count.
- **Validation evidence:** 15 artifacts in `tasks/judge-frame-directive-validation/` — n=11 original runs + n=3 variance + n=1 negative control + n=3 novelty-gate re-validation + 1 rename check.

## Current Blockers
- None active. Directive is validated and ready. Next tier 1 fix (refine-stage) uses the same pattern.

## Next Action
Audit judge-stage findings with the same load-bearing + refine-scope classification that refine v5 uses. The refine audit revealed v1 findings included completeness-level concerns mislabeled as frame defects. Judge may have the same issue hidden — its output looks similar to Frame Check items but we haven't classified whether judge findings are actually load-bearing or completeness-level. Rebuild benchmark for judge with new classification. Then review-lens with linkage model (read upstream Frame Check rather than generate new). Then ROI study (`debate-efficacy-study-*` pile) against fixed pipeline.

## Recent Commits
- (this commit): judge-stage Frame directive + novelty gate + SPIKE→INVESTIGATE rename
- `84a0c9a` Session wrap 2026-04-17 (night): judge-stage Frame-reach audit DECLINE + reusable primitive
- `c81acfb` Judge-stage Frame-reach audit: Phase 0x + Phase 0a — DECLINE

## Followup tracked (not blocking)
- **Refine-stage Frame directive + novelty gate** — next tier 1 fix.
- **Review-lens Frame directive** — tier 2 fix.
- **`debate-efficacy-study-*` pile still uncommitted** — ~33 files, 4-session carryover. Plausibly the ROI measurement we'll want to run against the fixed pipeline. Triage when prompt work is complete.
- `tasks/multi-model-skills-roi-audit-*` off-scope design docs remain on disk.
- `.claude/scheduled_tasks.lock` — runtime artifact, ignore.

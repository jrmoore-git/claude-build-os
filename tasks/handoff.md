# Handoff — 2026-04-18

## Session Focus
User reframe redirected the multi-session Frame-reach audit program back to its original intent — find where else in the debate pipeline prompts produce confidently-wrong output, fix them, then run the ROI study. Shipped judge-stage and refine-stage frame directives; audited judge findings for calibration; captured a benchmark-methodology lesson.

## Decided
- **D30: Judge-stage Frame directive + novelty gate shipped; SPIKE → INVESTIGATE rename.** Five defect categories with novelty test ("required fix no challenger recommends"). Renamed SPIKE verdict throughout judge prompt and CLI output.
- **D31: Refine-stage Frame Check directive v5 shipped with mutually-exclusive channel rule.** Fixed concerns → Review Notes with explicit frame-lens language. Unfixed concerns → Frame Check. Never both.
- **L46: Frame-critique directives MUST include explicit novelty gate** — else models reframe existing persona findings as "frame" findings and inflate MATERIAL counts.
- **L47: Iterating an LLM prompt without a baseline benchmark produces a prompt-engineering treadmill.** Qualitative pattern-matching is not evidence. Benchmark discipline must precede iteration, not follow it.
- **Judge audit: keep current calibration.** 10/14 findings are genuine frame defects, 2 borderline. Tightening risks over-correction (refine v2 cautionary tale).
- **Each pipeline stage needs a tailored frame directive, not one-size-fits-all.** Judge + refine both generate frame findings (similar pattern). Review-lens is enforcement (different pattern — linkage model). Premortem, explore-synthesis, think-discover each need their own shape.

## Implemented
- `scripts/debate.py` — `JUDGE_SYSTEM_PROMPT` gained FRAME CRITIQUE section + novelty gate. SPIKE renamed INVESTIGATE throughout (prompt text, output format, regex parser, JSON log fields).
- `scripts/debate.py` — `REFINE_FIRST_ROUND_PROMPT` + `REFINE_SUBSEQUENT_ROUND_PROMPT` gained FRAME CHECK with 5 active-check categories, 3-filter gate, sequential decision flow, mutually-exclusive channel rule.
- `tasks/judge-frame-directive-validation/` — 15 validation artifacts (n=8 original + 3 variance + 1 negative control + 1 rename check + 3 novelty-gate re-runs).
- `tasks/refine-frame-directive-validation/` — 23 validation artifacts across 5 iterations (v1, v2-tightened, v3, v4, v5).
- `tasks/decisions.md` — D30 + D31.
- `tasks/lessons.md` — L46 + L47.

## NOT Finished
- **Review-lens linkage model** — fresh design needed. Not a copy-paste of judge/refine. Review's role is to enforce upstream Frame Check findings against a diff, not generate new ones. Requires changes to `.claude/skills/review/SKILL.md` spec-parsing logic so Frame Check concerns flow from refined spec into review prompt.
- **Premortem / explore-synthesis / think-discover frame directives** — each needs its own tailored shape per the user insight this session.
- **`tasks/debate-efficacy-study-*` pile** — 4-session carryover (~33 files). Likely the ROI measurement we want to run against the fixed pipeline. Triage after prompt fixes complete.
- **2 borderline judge findings** (debate-common "does not negate"; negative-control novelty-gate "stderr sink") — noted, not acted on. Revisit if downstream noise proves problematic.
- `tasks/multi-model-skills-roi-audit-*` — still on disk from earlier session.

## Next Session Should
1. **Read this handoff + `docs/current-state.md`.** Current-state's Next Action section describes the review-lens linkage approach.
2. **Design review-lens linkage.** Don't paste the judge directive. The design question: how does the refined spec's Frame Check section flow into review's lens prompts? Proposed: spec parser surfaces Frame Check concerns; review prompt for each lens includes "verify the diff addresses these upstream Frame Check concerns." Different directive shape per lens (PM / Security / Architecture). Build a benchmark BEFORE iterating (L47).
3. **Then: triage `debate-efficacy-study-*` pile.** Skim the directory, determine if it's the ROI measurement we'll want to run against the fixed pipeline. If yes, resume; if not, decide commit/delete.
4. **Do not re-iterate on judge or refine directives without new evidence.** Both are calibrated per benchmark; further prompt changes need a documented failure mode first.

## Key Files Changed
- `scripts/debate.py` (+~400 LOC in prompt additions across 2 directives)
- `tasks/judge-frame-directive-validation/` (15 files, new directory)
- `tasks/refine-frame-directive-validation/` (23 files, new directory)
- `tasks/decisions.md` (D30, D31)
- `tasks/lessons.md` (L46, L47)
- `docs/current-state.md` (refreshed)
- `tasks/session-log.md` (2 session entries)

## Doc Hygiene Warnings
- None. Active lessons count: 15/30.
- Autopilot `debate-efficacy-study-*` pile carryover continues (4 sessions). Deliberately out of scope for this session's Frame-reach work.

# Current State — 2026-04-18

## What Changed This Session
- **Judge-stage Frame directive shipped** (commit `96f3f25`) — FRAME CRITIQUE section in `JUDGE_SYSTEM_PROMPT` with 5 defect categories + novelty gate. Validated against n=11 (8 original + 3 variance) + n=1 negative control + n=3 novelty-gate re-validation. 0 fabrications across all runs.
- **SPIKE verdict renamed INVESTIGATE** — plain English, aligns with `/investigate` skill. Breaking change to judge CLI JSON fields (`spiked`→`investigating`, etc.) — no external consumer reads them.
- **Refine-stage Frame Check directive v5 shipped** (commit `67679db`) — same 5 categories as judge but adapted for refine's document-polishing role. Three filters (load-bearing + out-of-scope-for-refine + not-already-covered). HARD RULE: fixed concerns → Review Notes; unfixed → Frame Check. Never both. Took 5 iterations to calibrate.
- **Benchmark methodology lesson captured (L47)** — user caught that I'd iterated refine v1→v5 without comparing against a baseline. Building the benchmark revealed v2 was 0/6 detection (silent failure), v3/v4 had channel violations. Qualitative "looks cleaner" is pattern-matching, not evidence.
- **Judge-stage audit applied load-bearing + refine-scope classification** to 14 judge findings. 10/14 genuine frame defects, 1 correctly ADVISORY, 1 reframe, 2 borderline. Accepted current calibration — tightening risks over-correction.

## Current Blockers
None. Judge + refine stages shipped and validated. Next stages scoped but deferred.

## Next Action
Review-lens with **linkage model** — `.claude/skills/review/SKILL.md` should consume upstream Frame Check from refined spec rather than generate new frame findings. Distinct from judge/refine patterns. Design needed, not just a prompt edit — the spec parser must surface Frame Check concerns to the review lens prompt.

Then triage the `tasks/debate-efficacy-study-*` pile (4-session carryover, ~33 files) — likely the ROI measurement we want to run against the fixed pipeline.

## Recent Commits
- `67679db` Refine-stage Frame Check directive (v5) with mutually-exclusive channels
- `96f3f25` Judge-stage Frame directive + novelty gate; SPIKE→INVESTIGATE rename
- `99b55a8` Add rule banning wall-clock time estimates

## Followup tracked (not blocking)
- **Review-lens linkage model** — not a copy-paste of the judge/refine pattern. Review's role is enforcement, not generation.
- **Premortem, explore-synthesis, think-discover frame checks** — each needs a tailored shape, not one-size-fits-all (user insight from this session).
- **`debate-efficacy-study-*` pile** — 4-session carryover. Triage once pipeline fixes are in place.
- **Judge audit: 2 borderline findings** noted but not acted on. Revisit if downstream noise proves problematic.
- `.claude/scheduled_tasks.lock` — runtime artifact, ignore.

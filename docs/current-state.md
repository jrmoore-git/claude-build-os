# Current State — 2026-04-18

## What Changed This Session
- **Review-lens Frame Check linkage design closed (D32)** — decided not to add a directive to `/review`. Benchmark built (n=14, 8 fixtures across DRIFT + NEW_DEFECT modes + 2 negative controls) shows PM-lens spec-compliance already catches Frame defects that leak into implementation (5 of 6 real catches; 2/2 clean on negative controls). Updated `.claude/skills/review/SKILL.md` Step 4 with a paragraph documenting the linkage + benchmark evidence.
- **Scoring methodology lesson surfaced** — keyword-based substring matcher has both false-negative rate (PM uses evidence-quality vocabulary like `SPECULATIVE` / `without evidence`, not Frame Check category terminology like `hardcoded` / `inherited-frame`) and false-positive rate (matcher fires incidentally on unrelated spec-compliance findings). Qualitative raw-output inspection is the authoritative read; numbers are a tripwire, not a verdict.
- **Benchmark harness + fixtures kept on disk** — `scripts/review_frame_benchmark.py` and `tasks/review-lens-linkage-benchmark/` are re-usable if a real-world Frame defect slips past review later. Harness supports `--baseline` (run LLM) and `--rescore` (reuse raw outputs) modes.
- **Impact-first feedback memory saved** (`feedback_debate_ground_in_impact.md`) — every debate pipeline modification must be justified by outcome quality (better answers/products/research/code), not symmetry or engineering shape. Durable principle, not session-specific.

## Current Blockers
None. Review-lens linkage closed; further Frame-reach work (premortem / explore-synthesis / think-discover) deferred pending evidence of real miss at those stages.

## Next Action
Triage the `tasks/debate-efficacy-study-*` pile — 4-session carryover (~33 files from 2026-04-17 work). Likely the ROI measurement we want to run against the now-fixed pipeline. Skim the directory, decide resume vs. close.

## Recent Commits
- `dc37c82` Session wrap 2026-04-18: judge + refine frame directives shipped, benchmark methodology captured
- `67679db` Refine-stage Frame Check directive (v5) with mutually-exclusive channels
- `96f3f25` Judge-stage Frame directive + novelty gate; SPIKE→INVESTIGATE rename

## Followup tracked (not blocking)
- **Premortem, explore-synthesis, think-discover frame checks** — each needs a tailored shape. Deferred until evidence of real miss at those stages.
- **`debate-efficacy-study-*` pile** — 4-session carryover; primary candidate for next session's work.
- **Judge audit: 2 borderline findings** noted but not acted on. Revisit if downstream noise proves problematic.
- **Scoring-methodology caveat in `scripts/review_frame_benchmark.py`** — if the benchmark is re-run later against a directive change, either tighten the concern_keywords list or replace with LLM-judged scoring. Current numbers are misleading without raw-output inspection.
- **`docs/how-it-works.md` + `docs/reference/debate-invocations.md`** — modified this session aligning docs to the shipped `frame` persona (D28). Included in this wrap commit.
- `.claude/scheduled_tasks.lock` — runtime artifact, ignore.

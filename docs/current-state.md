# Current State — 2026-04-18

## What Changed This Session
- **Root-level fix: harness-tag attribution** — added a bullet to project `CLAUDE.md` under "Inspect before acting" telling the assistant that tool output may end with harness-injected tags (`<system-reminder>`, `<command-name>`, `<user-prompt-submit-hook>`) that are NOT file content, and that Grep is the verification mechanism (reads raw bytes, bypasses injection). Paired `feedback_harness_tag_attribution.md` memory saved. L48 captures the incident.
- **Root-level fix: plain-language chat output** — added new operating rule to project `CLAUDE.md` that explicitly overrides register-matching to surrounding docs. BuildOS docs/rules/skills are dense by design; chat responses stay plain. Paired `feedback_plain_language.md` memory saved with concrete translations ("reinforcement layers" → "two places the rule lives"). User reported losing the forest through the trees.
- **Pattern that won't get a hook:** harness injection runs after hook stdout and hooks can't rewrite tool results; jargon detection has too high a false-positive rate to automate. Behavioral rules + memories are the maximum available fix for both.
- **Afternoon session work** (from prior wrap 78a35a2) — Review-lens Frame Check linkage closed via D32 (no directive; PM-lens spec-compliance already catches Frame defects). Benchmark harness + fixtures retained in `scripts/review_frame_benchmark.py` + `tasks/review-lens-linkage-benchmark/`.

## Current Blockers
None. New `CLAUDE.md` rules won't bind mid-session — they load on next `/start`.

## Next Action
Triage the `tasks/debate-efficacy-study-*` pile (4-session carryover, ~33 untracked files from 2026-04-17 work). Same next action as afternoon wrap — still not touched. Skim the directory, decide resume vs. close. Also: verify both new `CLAUDE.md` rules fire on first natural opportunity after next `/start`.

## Recent Commits
- `66b88b6` Root-level fixes: harness-tag attribution + plain-language chat output
- `78a35a2` Session wrap 2026-04-18 (afternoon): Review-lens Frame Check linkage closed (D32), no directive
- `dc37c82` Session wrap 2026-04-18: judge + refine frame directives shipped, benchmark methodology captured

## Followup tracked (not blocking)
- **`debate-efficacy-study-*` pile** — 4-session carryover; primary candidate for next session's work. Still untracked.
- **Premortem, explore-synthesis, think-discover frame checks** — each needs a tailored shape. Deferred until evidence of real miss at those stages.
- **Judge audit: 2 borderline findings** noted but not acted on. Revisit if downstream noise proves problematic.
- **Scoring-methodology caveat in `scripts/review_frame_benchmark.py`** — if re-run against a directive change, tighten `concern_keywords` or replace with LLM-judged scoring. Current numbers misleading without raw-output inspection.
- **Verify new rules fire** — next session, confirm the harness-tag rule triggers Grep-before-claim behavior, and the plain-language rule actually plainifies chat output.

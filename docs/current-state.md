# Current State — 2026-04-18 (evening)

## What Changed This Session
- **Prior debate-efficacy-study (2026-04-17, n=5) closed and verdict discarded (D33).** The published DROP-CROSS-MODEL verdict was extracted from a count metric that GPT-5.4 critique had already flagged as atomization-biased; the study's own internal coverage metric contradicts the headline (arm D 72% decision-driver coverage vs arm C 64%). The arms tested also did not match the user's stated bar — arm C was Claude-Opus + Claude-Sonnet mix with Gemini judge, not single-model Claude with same-session consolidation; arm D was modified (Gemini judge instead of production gpt-5.4) to hold judge constant. 33-file pile from that study is committed now as closure, not as escalated work.
- **Replacement study designed via `/challenge --deep` (D33).** `tasks/debate-arm-comparison-design-refined.md` (511 lines) addresses all 6 material challenges + 1 frame-added finding from the adversarial pipeline. Arm B'-fair = single-model Claude with same-session consolidation. Arm D = production config as-deployed. 7 outcome-linked impact dimensions (review value-add as counterfactual delta, not count). Three cross-model judges with canonical reformat. Pre-registered decision matrix. Prospective arm for contamination-free validation.
- **Scope expanded to 4 skills (user direction).** Original design covered `/challenge` only. User requested "refines, etc." `tasks/debate-arm-comparison-scope-expansion.md` captures per-skill arm definitions for `/challenge` + `/refine` + `/review` + `/pressure-test`. `/think` excluded per D5.
- **Efficiency gate identified and scheduled before study execution (D34).** Triple-verified: pricing table in `scripts/debate_common.py:140-148` matches published 2026-04 rates; per-record arithmetic matches log entries exactly (e.g., `learning-velocity` $6.83 record broken down to exact cents). But grep across `debate.py` / `debate_common.py` / `llm_client.py` returned zero matches for prompt caching. Estimated savings: ~60-70% on input tokens → typical `/challenge` drops from $1.88 to ~$0.60/call. Zero quality risk (Anthropic byte-exact cache). Annualized savings on current $380/month debate spend: ~$2,400-3,000/year.
- **Durable memory saved** (`feedback_measure_review_value_add.md`): measure review value-add as counterfactual delta, not raw outcome. Comparative A-vs-B judging, not independent scoring. Kill finding-count metrics.

## Current Blockers
None. Study is parked in a clean state with a pre-registered next-session sequence.

## Next Action
Start new session. Read this doc + `tasks/handoff.md` + `tasks/debate-arm-comparison-scope-expansion.md`. Sequence before any study execution:
1. Verify prompt caching preserves quality (Anthropic docs check + small test).
2. Implement caching in `debate.py` / `llm_client.py`.
3. Measure savings on 3-5 test calls.
4. Ship caching.
5. Verify `managed-agents-dispatch` outcome (proposal #9 in the set — UNKNOWN ship status needs confirmation or swap).
6. THEN run the 4-skill comparison study per refined design.

## Recent Commits
- (this wrap commit) Session wrap 2026-04-18 evening: debate-efficacy-study closed + arm-comparison design shipped + efficiency gate
- `66b88b6` Root-level fixes: harness-tag attribution + plain-language chat output
- `78a35a2` Session wrap 2026-04-18 (afternoon): Review-lens Frame Check linkage closed (D32)
- `dc37c82` Session wrap 2026-04-18: judge + refine frame directives shipped, benchmark methodology captured

## Followup tracked (not blocking)
- **Per-skill arm-B'-fair configs** — each of the 4 skills needs its own all-Claude config or CLI path in new session. May require `--config` CLI flag wiring to `_load_config(config_path=...)` per judge Challenge 1 of refined design.
- **Deferred efficiency ideas** — per-persona model reassignments, tool-call budget caps, batch API for retro runs. Carry real quality risk, need own testing. NOT for the prompt-caching phase.
- **Premortem / explore-synthesis / think-discover frame directives** — still deferred pending evidence of real miss at those stages.
- **Outcome verification for proposal #9** (`managed-agents-dispatch`) — before execution, verify ship state; swap if no clean outcome.
- **Verify new CLAUDE.md rules fire** (from `66b88b6`) — confirm the harness-tag rule triggers Grep-before-claim behavior, and the plain-language rule actually plainifies chat output. (Carried from afternoon session.)

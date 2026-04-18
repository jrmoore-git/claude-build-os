# Handoff — 2026-04-18 (evening)

## Session Focus
Audited whether recent lessons propagated to all multi-model tools. Found the prior `debate-efficacy-study` (2026-04-17, n=5) still uncommitted with a DROP-CROSS-MODEL verdict extracted from an atomization-biased count metric — GPT-5.4's critique + the study's own internal coverage metric both contradicted the headline. Redesigned via `/challenge --deep`: 6 material challenges + 1 frame-added finding accepted. Expanded scope to all 4 multi-model skills per user direction. Triple-verified costs — pricing table honest, arithmetic exact, but zero prompt caching anywhere in the pipeline → ~60-70% input-token waste on every call. Scheduled prompt-caching work as the efficiency gate before study execution.

## Decided
- **D33: Prior debate-efficacy-study superseded; verdict discarded.** Two decision-changing flaws confirmed — atomization-rewarding count metric, arms that didn't match user's stated bar, modified arm D (Gemini judge instead of production gpt-5.4). Scaffolding preserved; verdict not.
- **D34: Prompt caching must ship before arm-comparison study runs.** Zero quality risk (Anthropic byte-exact cache); estimated ~$2,400-3,000/yr savings. Model reassignments + tool-call caps deferred pending own validation.
- **New memory** (`feedback_measure_review_value_add.md`): measure review value-add as counterfactual delta, not raw outcome. Comparative A-vs-B judging per dimension. Kill finding-count metrics.

## Implemented
- `tasks/debate-arm-comparison-design.md` — new experimental design.
- `/challenge --deep` pipeline artifacts: `-challenge.md`, `-judgment.md`, `-refined.md` (511 lines, 6 rounds across gemini/gpt/claude).
- `tasks/debate-arm-comparison-scope-expansion.md` — 4-skill scope expansion addendum (`/challenge` + `/refine` + `/review` + `/pressure-test`) with the 10 retrospective proposals finalized and sanity-check pair (sim-generalization + buildos-improvements).
- `tasks/debate-efficacy-study-results.md` — header rewritten: verdict → SUPERSEDED, closure reason named, pointer to replacement design. Original headline retained as provenance only.
- `tasks/decisions.md` — D33 + D34 added.
- `~/.claude/projects/-Users-justinmoore-buildos-framework/memory/feedback_measure_review_value_add.md` + `MEMORY.md` updated.
- 33-file debate-efficacy-study pile now ready for commit (4-session carryover finally closed).

## Cost + efficiency verification (this session)
- Pricing table (`scripts/debate_common.py:140-148`) matches published 2026-04 rates: Opus $15/$75, Sonnet $3/$15, Haiku $0.80/$4, GPT-5.4 $2.50/$10, Gemini 3.1 Pro $1.25/$10.
- Per-record arithmetic verified exact (e.g., `learning-velocity` $6.83 record: claude-sonnet 631,550 input × $3/M + 10,051 output × $15/M = $2.046 vs logged $2.0454; claude-opus 272,434 × $15/M + 9,364 × $75/M = $4.789 vs logged $4.7888).
- Zero prompt caching: grep across `debate.py` + `debate_common.py` + `llm_client.py` for `cache_control` / `prompt_caching` / `anthropic-beta` / `cache_read` / `cache_creation` returned zero matches.
- Current production economics: mean `/challenge` $1.88/call, median $0.36, across 157 historical runs. 30-day spend $380. Annualized ~$4,500.

## NOT Finished
- **Prompt caching implementation** — Phase 0 of new session (before any study run).
- **`managed-agents-dispatch` outcome verification** — proposal #9 of the 10 is UNKNOWN; confirm or swap before execution.
- **Per-skill arm-B'-fair configs** for `/refine` + `/review` + `/pressure-test`. Main `/challenge` config is spec'd but not written.
- **`--config` CLI flag** implementation in `scripts/debate.py` — Challenge 1 of the judged-accepted findings. Required before arm B'-fair can even be invoked for `/challenge`.
- **Study execution itself** — parked pending all gates above.
- Prior-session carryover (afternoon wrap `78a35a2`): verify new CLAUDE.md rules fire (harness-tag attribution + plain-language chat). Low priority — observe at first natural opportunity.

## Next Session Should

1. **Read this handoff + `docs/current-state.md` + `tasks/debate-arm-comparison-design-refined.md` + `tasks/debate-arm-comparison-scope-expansion.md`.** Everything needed to pick up is on disk.

2. **Phase 0: Prompt caching gate (first action).** Per D34:
   - Verify quality-neutrality from Anthropic docs (should be trivial — byte-exact cache).
   - Implement caching in `scripts/llm_client.py` for Claude calls (cache_control markers on shared system prompt + proposal text + tool definitions; cache conversation history across tool-use turns).
   - Test on 3-5 sample calls. Expected: ~60-70% input-token reduction.
   - Ship if savings verify.
   - If LiteLLM passthrough loses the cache markers, investigate before moving on — caching is the economic gate, not a nice-to-have.

3. **Phase 0b: Verify `managed-agents-dispatch` outcome.** Check git log + decisions.md + lessons.md for ship state. If no clean outcome, swap for another proposal with clear outcome evidence.

4. **Phase 0c: Implement `--config` CLI flag** in `debate.py` per Challenge 1 of refined design. Write `config/debate-models-arm-bfair.json` (all-Claude) + smoke test that verifies config actually loads.

5. **Phase 0d: Finalize per-skill arm definitions** for `/refine` + `/review` + `/pressure-test`. Scope-expansion addendum has the shapes; confirm each is runnable via existing `debate.py` flags.

6. **Phase 1+: Execute the refined design** — outcome extraction (fresh-session × 3 per proposal), arm execution (both arms × all 4 skills), canonical reformat, triple-judge adjudication, decision matrix, prospective arm in parallel.

7. **Do NOT re-litigate the efficacy-study verdict.** It's superseded. Use its scaffolding, discard its conclusion.

## Key Files Changed
- `tasks/debate-arm-comparison-design.md` (new)
- `tasks/debate-arm-comparison-design-challenge.md` (new)
- `tasks/debate-arm-comparison-design-judgment.md` (new)
- `tasks/debate-arm-comparison-design-refined.md` (new)
- `tasks/debate-arm-comparison-scope-expansion.md` (new)
- `tasks/debate-efficacy-study-results.md` (header rewritten)
- `tasks/debate-efficacy-study-*` (full 33-file pile, previously uncommitted)
- `tasks/decisions.md` (+D33 +D34)
- `docs/current-state.md` (refreshed)
- `tasks/session-log.md` (new entry)
- `~/.claude/projects/-Users-justinmoore-buildos-framework/memory/feedback_measure_review_value_add.md` (new) + `MEMORY.md` updated

## Doc Hygiene Warnings
- None. Active lessons count: 15/30. Decisions file has D33 + D34 added, no stale items.
- `negative-control-verbose-flag` debate artifacts remain on disk — kept as intentional negative-control check for the upcoming study, not dangling work.
- Prior study scaffolding (anonymization, adjudication, fixtures) kept — reusable for replacement study.

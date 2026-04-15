# Handoff — 2026-04-15 (session 9)

## Session Focus
Reviewed prior session's work with fresh eyes. Ran cross-model panel (Claude+Gemini+GPT) on the sim-compiler value question. Ran Perplexity research on industry landscape. Crystallized what's novel vs. commodity. No code changes — pure analysis and direction-setting.

## The Key Insight

The original framing ("lint vs. sim-compiler") was a false dichotomy (all 4 GPT explore directions converged on this). The sim-compiler contains two very different things:

1. **IR extraction (`sim_compiler.py` extract_ir + compare_ir)** — genuinely novel. No tool in the ecosystem extracts structured decision points, ask nodes, or interaction archetypes from agent procedures. Perplexity research confirmed: nobody does this. This is the differentiated asset.

2. **3-agent simulation loop (`sim_driver.py`, `sim_persona_gen.py`, `sim_rubric_gen.py`)** — commodity. DeepEval's `ConversationSimulator`, LangSmith's `create_llm_simulated_user`, MLflow 3.10 all do multi-turn persona simulation with LLM-as-judge scoring. Our loop reinvents what's becoming standard infrastructure.

**Caveat:** The industry tools test chatbot APIs (request/response). SKILL.md procedures are markdown instructions interpreted by Claude Code at runtime — a different shape. If multi-turn simulation is ever needed for skills specifically, the industry tools may not plug in directly. But the sim_driver plumbing (turn loop, termination, judge scoring, JSONL output) is the commodity part regardless.

## Cross-Model Panel Findings (Claude + Gemini + GPT)

### Where all 3 converge
- Structural lint first is correct — 18/22 missing Safety Rules is the strongest evidence
- IR extractor is the real asset worth keeping
- Don't build further on persona/judge loop

### Where they diverge (new signal)

**Gemini:** Solo-dev sim value is model-drift regression, not persona diversity. Consider chaos/adversarial testing (malformed input, context-window busting, refusal patterns) instead of user personas.

**Claude Opus — two factual corrections:**
- "Output Silence" doesn't exist as a convention in 20/22 skills. Can't lint for a section that was never defined. **Must define canonical SKILL.md sections before linting can enforce them.**
- `skill.contract.json` is premature — no schema, no tooling. Use `extract_ir` + reference IR comparison directly instead.
- debate.py (4,136 lines, zero test coverage) is the highest-risk untested component, not the skills.

**GPT:** Don't gate simulation on "prior real bugs" — lack of bug reports in solo-dev = low observability, not low bugs. Gate on IR interaction complexity (branching, multi-turn, sufficiency loops).

## Industry Landscape (Perplexity Research)

| Capability | Exists in industry? | Our status |
|---|---|---|
| Multi-turn conversation simulation | YES — DeepEval, LangSmith, MLflow | sim_driver.py (commodity) |
| LLM-as-judge scoring | YES — all major frameworks | sim_driver.py judge (commodity) |
| Synthetic user personas | YES — DeepEval ConversationSimulator, LangSmith | sim_persona_gen.py (commodity) |
| IR extraction from procedures | **NO — nobody does this** | sim_compiler.py (differentiated) |
| Prompt linting/schema validation | **NO — gap in entire ecosystem** | Not built yet (opportunity) |
| Prompt contract testing/diffing | **NO — concept doesn't exist** | extract_ir + compare_ir ready |
| Property-based assertions | YES — standard practice | Not built |
| Golden datasets from production | YES — standard practice | Not applicable yet |
| CI/CD gating on regression | YES — standard practice | Not built |

## Decided This Session
- **Lint + IR contract-diff is the path.** Not alternatives — lint is the front-end pass, IR diff is the semantic pass.
- **Define canonical SKILL.md sections first** (Claude Opus finding: can't lint for undefined conventions).
- **Use extract_ir + compare_ir directly**, not a skill.contract.json abstraction (premature).
- **Persona/judge loop stays shelved.** Code works (48 tests pass) but no further investment. If ever needed, evaluate DeepEval's ConversationSimulator first.
- **Gate future simulation on IR interaction complexity**, not prior bug history (GPT finding).
- **No time estimates.** Sequence matters, timelines don't. Describe what's first/then/after, never this-week/next-week.

## Recommended Build Sequence

**First:** Define canonical SKILL.md sections — what's required vs. optional. This convention doesn't exist for most skills. `/think refine` is the right tool (scope is clear, no discovery needed).

**Then:** Structural lint hook on SKILL.md commits enforcing: Safety Rules, Output Silence (for interactive skills), input sanitization, debate.py fallback, valid frontmatter. The 4 patterns that found 20/22 skills dirty.

**Then:** Wire IR extractor into pre-commit diff — `extract_ir` on old version vs. new version of any changed SKILL.md. Catches semantic drift ("you removed a fallback branch without noticing") that lint can't see.

**After that proves out:** Selective flow testing for skills where IR shows branching dialogue + multi-turn complexity — /explore, /investigate, /plan (the 3 pilot skills already have reference IRs in `fixtures/sim_compiler/`).

## NOT Finished
- Canonical SKILL.md sections not defined (prerequisite for everything)
- Structural lint hook not built
- IR diff not wired into pre-commit
- 18/22 skills missing Safety Rules (lint will find them, but sections must exist first)
- debate.py has zero test coverage (4,136 lines — flagged by Claude Opus as highest risk)
- No `/review` on sim-compiler code (sim_compiler.py, sim_driver.py, etc.)
- `fixtures/` directory uncommitted (3 reference IRs + 9 anchor personas)
- `current-state.md` still has STALE marker

## Key Files
- `tasks/sim-compiler-value-review.md` — cross-model panel output (Claude/Gemini/GPT)
- `tasks/sim-compiler-value-explore.md` — GPT 4-direction explore
- `scripts/sim_compiler.py` — IR extraction + comparison (the keeper)
- `scripts/sim_driver.py` — 3-agent loop (shelved, works, don't invest)
- `scripts/sim_persona_gen.py` — persona generation (shelved)
- `scripts/sim_rubric_gen.py` — rubric generation (shelved)
- `tests/test_sim_compiler.py` — 26 tests
- `tests/test_sim_driver.py` — 22 tests
- `fixtures/sim_compiler/` — reference IRs for explore, investigate, plan
- `tasks/simulate-v2-plan.md` — original build plan (completed)
- `tasks/simulate-v2-refined.md` — build spec from challenge pipeline

## Prior Session Context (sessions 7+8)
Built all 16 planned V2 sim-compiler files. Ran smoke-test across all 22 skills (31 pass, 13 harness noise, 1 real candidate). Full challenge pipeline ran (proposal→findings→judgment→refined). See session-log entry for sessions 7+8 for full details.

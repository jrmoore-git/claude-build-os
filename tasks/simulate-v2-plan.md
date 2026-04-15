---
scope: "Skill Compiler Simulator — greenfield pilot: IR compiler, persona generator, 3-agent simulation driver, rubric generator, output pipeline. Pilot on 3 skills (/explore, /investigate, /plan)."
surfaces_affected: "scripts/sim_compiler.py, scripts/sim_persona_gen.py, scripts/sim_driver.py, scripts/sim_rubric_gen.py, fixtures/sim_compiler/, logs/sim_compiler_runs.jsonl, tests/test_sim_compiler.py, tests/test_sim_driver.py"
verification_commands: "python3.11 -m pytest tests/test_sim_compiler.py tests/test_sim_driver.py -v && python3.11 scripts/sim_compiler.py --skill explore --dry-run"
rollback: "git revert <sha>"
review_tier: "Tier 2"
verification_evidence: "PENDING"
challenge_artifact: "tasks/simulate-v2-challenge.md"
challenge_recommendation: "PROCEED-WITH-FIXES"
---

# Plan: Skill Compiler Simulator (sim-compiler)

Source spec: `tasks/simulate-v2-refined.md`
Challenge: `tasks/simulate-v2-challenge.md` (PROCEED-WITH-FIXES, 7 fixes incorporated)

## Build Order

### Phase 1: IR Compiler + Validation (hard gate before Phase 2)

**1. `scripts/sim_compiler.py`** — Skill Compiler
   - Input: path to a SKILL.md file
   - Output: structured IR as JSON (objective, decision_points, ask_nodes, success_criteria, failure_criteria, interaction_archetype)
   - Uses `llm_client.py` → `llm_call_json()` to extract IR from SKILL.md prose
   - CLI: `python3.11 scripts/sim_compiler.py --skill <name> [--output fixtures/sim_compiler/<name>/extracted_ir.json]`
   - `--dry-run` prints IR to stdout without writing
   - Archetype enum: `intake`, `diagnosis`, `planning`, `critique`, `synthesis`, `coaching`
   - Validation: compare extracted IR against reference IR using 6-field checklist (human gate)
   - Also includes: `compare_ir()` function that outputs a checklist diff between two IR files

**2. Reference IRs for pilot skills** — hand-authored
   - `fixtures/sim_compiler/explore/reference_ir.json`
   - `fixtures/sim_compiler/investigate/reference_ir.json`
   - `fixtures/sim_compiler/plan/reference_ir.json`
   - Each contains the same JSON schema as extracted IR, authored from reading the SKILL.md
   - These are the ground truth for compiler validation

**3. `tests/test_sim_compiler.py`** — compiler tests
   - Test IR JSON schema validation (all 6 fields present, correct types)
   - Test archetype enum validation
   - Test `compare_ir()` checklist logic (exact match, partial, missing)
   - Test CLI argument parsing and dry-run mode
   - Mock `llm_call_json` — do not hit the proxy in unit tests

### Phase 2: Persona Generator + Rubric Generator

**4. `scripts/sim_persona_gen.py`** — Persona Generator
   - Input: validated IR JSON + count of personas to generate
   - Output: persona cards as JSON (6 hidden-state fields: goal, knowledge, urgency, patience, trust, cooperativeness)
   - Two persona types:
     - `anchor`: hand-authored, stored in `fixtures/sim_compiler/<skill>/personas/`
     - `generated`: LLM-generated from IR, uses `llm_call_json()`
   - CLI: `python3.11 scripts/sim_persona_gen.py --ir <ir.json> --count 5 --type generated [--output-dir <dir>]`
   - Each persona includes: id, type, hidden_state fields, opening_input (what the user types first), behavioral_rules (1-3 sentences)
   - Persona card format compatible with eval_intake.py persona structure

**5. `scripts/sim_rubric_gen.py`** — Rubric Generator
   - Input: validated IR JSON
   - Output: rubric as JSON (list of scored dimensions with descriptions)
   - 3 universal dimensions always included: task_completion, register_match, turn_efficiency
   - Archetype-specific dimensions derived from IR success/failure criteria
   - CLI: `python3.11 scripts/sim_rubric_gen.py --ir <ir.json> [--output <rubric.json>]`
   - For /explore pilot: includes `compare_rubric()` that measures weighted coverage against `config/eval-rubric.md` (threshold: >= 80%)

**6. Anchor personas for pilot skills** — hand-authored
   - `fixtures/sim_compiler/explore/personas/anchor-1.json` through `anchor-3.json`
   - `fixtures/sim_compiler/investigate/personas/anchor-1.json` through `anchor-3.json`
   - `fixtures/sim_compiler/plan/personas/anchor-1.json` through `anchor-3.json`
   - Explore anchors adapted from existing `config/eval-personas/` cards (reframe-acceptance, thin-answers, presupposition-sufficiency)
   - Investigate/plan anchors authored to exercise each skill's key decision points

### Phase 3: Simulation Driver + Output Pipeline

**7. `scripts/sim_driver.py`** — 3-Agent Simulation Loop
   - Input: SKILL.md path, persona card JSON, rubric JSON, config (models, max_turns)
   - Output: simulation result as JSON (per the JSONL schema in refined spec)
   - Orchestrates:
     - **Executor** (Claude via llm_client): receives SKILL.md as system prompt + simulator wrapper, persona's opening_input as first user message
     - **Persona** (Gemini via llm_client): receives persona card as system prompt, executor messages as user messages. Does NOT see SKILL.md or rubric.
     - **Judge** (GPT via llm_client): receives rubric + full transcript + termination info. Runs once after termination.
   - Turn loop: max 15 turns. Checks 5 termination conditions after each turn.
   - Tool/file policy: checks `fixtures/sim_compiler/<skill>/mocks/` for fixture files. Missing → `[SIM] Tool/resource not available`
   - Transcript persisted with each run
   - CLI: `python3.11 scripts/sim_driver.py --skill <name> --persona <persona.json> --rubric <rubric.json> [--executor-model claude-opus-4-6] [--persona-model gemini-3.1-pro] [--judge-model gpt-5.4] [--max-turns 15]`
   - Batch mode: `--batch <dir>` runs all personas in a directory sequentially, writes all results to JSONL

**8. Output pipeline**
   - Results appended to `logs/sim_compiler_runs.jsonl` (one JSON line per run)
   - Schema matches refined spec (run_id, timestamp, simulator_version, skill, ir_metadata, persona_state, execution_config, transcript, final_status, termination_reason, objective_achieved, judge_scores, judge_rationale, rubric_metadata)
   - `sim_driver.py` handles writes directly — no separate output script needed

**9. `tests/test_sim_driver.py`** — driver tests
   - Test turn loop with mocked llm_call (executor/persona/judge)
   - Test all 5 termination conditions
   - Test tool/file policy (fixture present vs. missing)
   - Test JSONL output schema validation
   - Test batch mode persona loading
   - Mock all LLM calls — do not hit the proxy in unit tests

## Files

| File | Action | Scope |
|------|--------|-------|
| `scripts/sim_compiler.py` | CREATE | ~200 lines. IR extraction + CLI + compare_ir() |
| `scripts/sim_persona_gen.py` | CREATE | ~150 lines. Persona generation + CLI |
| `scripts/sim_rubric_gen.py` | CREATE | ~150 lines. Rubric generation + compare_rubric() + CLI |
| `scripts/sim_driver.py` | CREATE | ~350 lines. 3-agent loop + output pipeline + CLI |
| `fixtures/sim_compiler/explore/reference_ir.json` | CREATE | ~50 lines. Hand-authored reference IR |
| `fixtures/sim_compiler/investigate/reference_ir.json` | CREATE | ~50 lines. Hand-authored reference IR |
| `fixtures/sim_compiler/plan/reference_ir.json` | CREATE | ~50 lines. Hand-authored reference IR |
| `fixtures/sim_compiler/explore/personas/anchor-*.json` | CREATE | 3 files, ~30 lines each |
| `fixtures/sim_compiler/investigate/personas/anchor-*.json` | CREATE | 3 files, ~30 lines each |
| `fixtures/sim_compiler/plan/personas/anchor-*.json` | CREATE | 3 files, ~30 lines each |
| `tests/test_sim_compiler.py` | CREATE | ~120 lines |
| `tests/test_sim_driver.py` | CREATE | ~200 lines |

**Total: 16 new files, 0 modified files.**

## Execution Strategy

**Decision:** hybrid (Phase 1 sequential, then Phase 2 parallel, then Phase 3 sequential)
**Pattern:** pipeline with internal fan-out
**Reason:** Phase 2 components (persona gen, rubric gen) are independent of each other but both depend on Phase 1 output (IR schema). Phase 3 driver depends on both Phase 2 components.

| Subtask | Files | Depends On | Isolation |
|---------|-------|------------|-----------|
| A: IR Compiler + tests | sim_compiler.py, test_sim_compiler.py | — | worktree |
| B: Reference IRs (3 skills) | fixtures/sim_compiler/*/reference_ir.json | A (needs IR schema) | worktree |
| C: Persona Generator | sim_persona_gen.py, anchor persona fixtures | A (needs IR schema) | worktree |
| D: Rubric Generator | sim_rubric_gen.py | A (needs IR schema) | worktree |
| E: Simulation Driver + tests | sim_driver.py, test_sim_driver.py | C + D (needs persona + rubric format) | worktree |

**Sequence:** A → (B + C + D parallel) → E
**Synthesis:** Main agent merges worktrees, runs full test suite, verifies no conflicts.

## Verification

```bash
# Unit tests pass
python3.11 -m pytest tests/test_sim_compiler.py tests/test_sim_driver.py -v

# Compiler produces valid IR
python3.11 scripts/sim_compiler.py --skill explore --dry-run

# IR comparison works
python3.11 scripts/sim_compiler.py --compare \
  fixtures/sim_compiler/explore/reference_ir.json \
  fixtures/sim_compiler/explore/extracted_ir.json

# Persona generator produces valid cards
python3.11 scripts/sim_persona_gen.py --ir fixtures/sim_compiler/explore/extracted_ir.json --count 3 --type generated --dry-run

# Rubric generator produces valid rubric
python3.11 scripts/sim_rubric_gen.py --ir fixtures/sim_compiler/explore/extracted_ir.json --dry-run

# Full pilot run (single persona, after IR validation)
python3.11 scripts/sim_driver.py --skill explore \
  --persona fixtures/sim_compiler/explore/personas/anchor-1.json \
  --rubric fixtures/sim_compiler/explore/rubric.json \
  --max-turns 15 --dry-run
```

## Challenge Fixes Incorporated

All 7 material findings from `tasks/simulate-v2-challenge.md` are addressed:

| # | Finding | How addressed |
|---|---------|---------------|
| F1 | IR needs human gate | `compare_ir()` + reference IRs + 6-field checklist. Phase 1 is hard gate. |
| F2 | Greenfield not extension | No V1 dependency. Standalone scripts. No --mode flag. |
| F3 | Convergence undefined | Fixed-N only (10 runs/skill). No convergence logic. |
| F4 | OCEAN over-engineered | 6 behavioral fields only. No OCEAN. |
| F5 | Circular success criterion | Rubric coverage (>= 80%) is primary. Score comparison secondary. |
| F6 | 3-agent loop unspecified | Full spec in Step 7: prompt wiring, termination, tool policy. |
| F7 | No output schema | JSONL schema in Step 8, matches refined spec. |

---
topic: sim-generalization
created: 2026-04-15
---
# Generalize eval_intake.py into a Reusable Skill Simulation Harness

## Project Context
Build OS is a governance framework for building with Claude Code — 22 skills, a cross-model debate engine (`scripts/debate.py`, 4,136 lines, 9 subcommands), 17 hooks, and rules in `.claude/rules/`. Skills are SKILL.md files defining procedures an AI agent follows. The framework includes a proven cross-model evaluation stack: Claude, GPT-5.4, and Gemini 3.1 Pro via LiteLLM.

The `/simulate` skill (V1) has two modes: smoke-test (extract and run bash blocks) and quality-eval (single agent + debate.py judge). V1 catches structural bugs but not interactive experience failures.

## Recent Context

**Sessions 4-10 arc:** Built V1 /simulate, designed and built V2 sim-compiler scripts, discovered structural rot was the dominant problem (18/22 skills missing Safety Rules), pivoted to build linter (246 lines, 9 checks, 22 skills fixed). Cross-model panel said "sim infrastructure is commodity, don't build." User pushed back — investigation of eval_intake.py track record and external tools proved the panel wrong.

**Session 11 (current):** Deep audit of the /simulate arc. Found: (1) eval_intake.py's 17-round iteration on /explore intake is the proof case for simulation value, (2) no external tool meets the specific requirements (structured persona hidden state, information asymmetry, agent procedure testing), (3) the V2 scripts were commodity only at the abstract category level — at the specific requirement level, they're novel. Captured L27 (scope expansion = new gate) and L28 (cross-model panels fail without operational evidence).

**Context packet work (parallel session):** Built and refined a standard context packet spec for all debate.py calls. Fixing the thin-context problem that caused the false kill verdict.

## Operational Evidence

This section exists because of L28: cross-model panels converge on wrong answers when operational evidence is missing from input.

### eval_intake.py track record (the proof case)

`scripts/eval_intake.py` (485 lines) is a 3-agent evaluation harness: Claude interviews, Gemini plays a user from a structured persona card, GPT judges against a 6-dimension rubric. It was built specifically for the /explore intake protocol.

**Iteration trajectory:**
- **Rounds 1-11:** Developed base protocol, established 5-slot intake structure
- **Rounds 12-17:** Refined register matching and flow. Register went from 3.3/5 → 4.3/5 → 4/5 cross-model consensus. Flow reached 4/5 from Claude+Gemini.
- **Final validation (5 personas):** All pass. Averages: 4.5-5.0/5. Hidden truth surfaced: 5/5.

**What the iterations found and fixed (not exhaustive):**
- Recap mentor-voice drift (LLM defaults to warm/wise tone)
- Sufficiency test must run BEFORE drafting, not after
- Terse-user detection: switch to options format for ALL remaining questions, not sometimes
- Reframe constraint: max once, 25 words, user's words not jargon
- Register matching: 2x word count rule, sentence length mirroring
- Mandatory recap → continuity signal (lexical anchor preferred but not required)
- Coverage audit moved to composition phase (not for LLM consumption)
- Emotional temperature: match minimum their words justify, not "default cooler"

**What it caught that nothing else would have:**
- Register mismatch is invisible to structural lint and single-turn eval
- Sufficiency timing requires multi-turn state tracking to assess
- Hidden truth surfacing requires a persona with actual hidden state
- Protocol feature testing (reframe trigger, options format, meta-question) requires scenario-specific persona design

**Setup cost:** ~2 days for /explore. Not generalizable — hardcoded protocol path, hardcoded rubric, manually authored persona cards.

### External tools evaluation (why we can't buy this)

Investigated 7 tools in depth (session 11):

| Tool | Simulation engine? | Structured hidden state? | Agent procedure testing? | Verdict |
|---|---|---|---|---|
| DeepEval | Yes | No — free text `user_description`, hardcoded simulator prompt | No — chatbot testing only | Scoring layer only |
| Inspect AI (UK AISI) | DIY (custom solver) | DIY | Closest fit, MIT license | Best framework but you still write the sim loop |
| Promptfoo | Yes | Partial (instructions field) | No — YAML/Node.js stack | Wrong stack |
| LangSmith | Yes | No hidden state mechanism | No | Commercial, platform lock-in |
| Braintrust | No — scoring only | N/A | N/A | Wrong tool |
| Ragas | No — scoring only | N/A | N/A | Wrong tool |
| Patronus | Too new | Unknown | Unknown | Vaporware for this use case |

**The gap every tool has:** None support structured persona cards with hidden truth, behavior scripts, and protocol-feature-specific testing. None enforce information asymmetry at the architecture level (persona never sees procedure, executor never sees persona file, judge sees everything). None are designed for testing agent procedures — they're all built for chatbot evaluation.

### Existing V2 code (what's already built)

| File | Lines | Tests | Status |
|---|---|---|---|
| `scripts/sim_compiler.py` | 376 | 26 passing | IR extraction works. Novel — no external tool does this. |
| `scripts/sim_persona_gen.py` | 270 | 0 | Generates personas from IR. Never reviewed. |
| `scripts/sim_rubric_gen.py` | 246 | 0 | Generates rubrics from IR. Never reviewed. |
| `scripts/sim_driver.py` | 463 | 22 passing | 3-agent loop. Architecturally similar to eval_intake.py. Never reviewed. |
| `fixtures/sim_compiler/` | 13 files | — | Reference IRs + anchor personas for explore, investigate, plan |

## Problem

eval_intake.py proved that iterative 3-agent simulation produces measurable quality improvements (3.3→4.5/5) that no other testing approach can replicate. But it's hardcoded to /explore's intake protocol. ~8-10 of BuildOS's 22 skills are interactive (branching dialogue, clarifying questions, user-state dependence) and would benefit from the same treatment. Building a bespoke eval_*.py for each skill costs ~2 days per skill. The V2 scripts exist to generalize this, but they were never reviewed, never wired together end-to-end, and never validated against eval_intake.py's known baseline.

## Proposed Approach

Generalize eval_intake.py's proven 3-agent architecture into a reusable harness using the existing V2 scripts. The pipeline:

1. **sim_compiler.py** extracts IR from any SKILL.md (states, transitions, branches, tool calls, interaction archetype)
2. **sim_persona_gen.py** generates personas from the IR — both anchor personas (handcrafted for regression) and generated personas (LLM-created for breadth)
3. **sim_rubric_gen.py** generates a scoring rubric from the IR — 3 universal dimensions (task completion, register match, flow) + archetype-specific dimensions
4. **sim_driver.py** runs the 3-agent loop: executor (Claude, follows SKILL.md procedure) ↔ persona (Gemini, plays from hidden state) → judge (GPT, scores against rubric)

### What needs to happen

**Phase 1: Review + validate against baseline (the gate)**
- Run /review on the 4 V2 scripts
- Wire the pipeline end-to-end for /explore
- Compare V2 results against eval_intake.py's scores on the same 5 personas
- Success criterion: within 0.5 points on all 6 rubric dimensions

**Phase 2: Generalize to 2-3 more skills**
- Run the pipeline on /investigate, /plan, /think discover
- For each: compile IR, validate IR, generate 3 anchor + 5 generated personas, run 10 simulations
- Success criterion: surfaces at least 2 actionable findings per skill that structural lint doesn't catch

**Phase 3: Wire into /simulate**
- Add `--mode persona-sim` to the existing /simulate SKILL.md
- V1 modes (smoke-test, quality-eval) unchanged
- persona-sim mode invokes the generalized pipeline

### What this does NOT include
- Replacing eval_intake.py (it remains the /explore-specific harness, proven and stable)
- Building a CI/CD integration or pre-commit hook (simulation is too expensive for every commit)
- Adopting any external tool (none meet the requirements — see evaluation above)
- Changing the 3-model architecture (Claude/Gemini/GPT separation is proven)

## Simplest Version

Phase 1 only: review the V2 scripts, wire them end-to-end, validate against eval_intake.py's baseline on /explore. If the generalized pipeline can't match the bespoke harness within 0.5 points, stop and investigate before proceeding to Phase 2.

### Current System Failures

1. **No generalized simulation exists.** eval_intake.py works for /explore only. The other ~8-10 interactive skills have zero interactive quality validation.
2. **V2 scripts are unreviewed.** 1,355 lines of code built in sessions 7-8 during a rush, with 48 tests but no /review gate.
3. **Persona cards are manual.** eval_intake.py's 5 personas (reframe-acceptance, reframe-rejection, thin-answers, meta-question-blindspot, presupposition-sufficiency) were hand-authored. Scaling to 8-10 skills × 5-8 personas = 40-80 persona cards manually is not feasible.

### Operational Context

- eval_intake.py runs are manual (invoked during skill development, not automated)
- V2 scripts exist but are disconnected — no pipeline wiring
- sim_compiler.py has reference IRs for 3 skills (explore, investigate, plan) + anchor personas
- LiteLLM proxy running with Claude Opus, GPT-5.4, Gemini 3.1 Pro
- Cost per full run (~10 simulations per skill): ~500K-800K tokens, comparable to one /challenge --deep pipeline

### Baseline Performance

- **eval_intake.py on /explore:** 5/5 personas passing, 4.5-5.0/5 average, hidden truth surfaced 5/5. This is the gold standard to match.
- **V1 /simulate smoke-test:** Catches structural bugs (missing files, broken bash blocks). 0% interactive quality coverage.
- **V1 /simulate quality-eval:** Single scenario, single judge. Catches gross quality failures. No persona diversity, no hidden state, no protocol-feature testing.
- **Structural linter:** 22/22 skills passing, 9 checks, PostToolUse hook. Catches section-level drift but not logic-level or interaction-level drift.

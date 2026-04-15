---
debate_id: simulate-v2
created: 2026-04-15T11:06:38-0700
phase: refine
rounds: 3
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: yes
---
# simulate-v2 — Refined Document

## Round 1 (gemini-3.1-pro)
The original document identified a highly valuable goal (generalizing interactive skill evaluation) but suffered from several critical execution gaps. The proposed architecture relied on unverified LLM extractions, assumed the existence of a V1 executable that isn't actually implemented, over-engineered the persona states, and lacked mechanical execution details. 

The revised document addresses these flaws by:
1. Reframing the project as a net-new simulator build rather than an extension of a non-existent V1.
2. Inserting a mandatory human review gate for the extracted Interaction Representation (IR) to prevent downstream poisoning.
3. Replacing the undefined convergence loop with a concrete fixed-N pilot.
4. Stripping out the over-engineered OCEAN traits in favor of a focused behavioral hidden state.
5. Defining concrete execution mechanics (turn limits, tool policies) and an explicit output schema.
6. Shifting success criteria from circular score-matching to direct artifact validation (IR and rubric overlap).

## Round 2 (gpt-5.4)
The current revision already fixes several major framing problems well:
- It correctly reframes V2 as a net-new simulator rather than an extension of an existing executable `/simulate`.
- It removes convergence claims from the pilot and replaces them with fixed-N runs.
- It removes OCEAN from the pilot and uses a smaller hidden-state model.
- It adds a human validation gate for IR extraction.
- It adds a basic execution spec and a results schema.

Remaining issues:
1. **IR verification is improved but still too loose in measurement.** “Human reviewer confirms 100% of critical decision points and ask nodes” is directionally right, but it still lacks a concrete review artifact and agreement method. The accepted challenge required measurable success criteria such as overlap against a hand-authored reference IR or reviewer agreement. The revision should define the checklist contents, required signoff, and how the reference IR is produced for the pilot.
2. **Pilot run counts are internally inconsistent.** The document says “10 simulations per skill” but the pilot steps say “Generate 3 anchor + 5 generated personas” and then “Run 10 simulations.” It is unclear whether personas are reused, whether all anchors must run, or how the extra two runs are assigned. This should be made explicit.
3. **The execution spec is still underspecified in a few implementation-defining places.** It mentions max turns and unsupported tools, but not initial prompt wiring, transcript handoff between agents, judge timing, or exact termination conditions. Since this was an accepted challenge, the pilot should specify these mechanics concretely.
4. **The rubric comparison metric is still ambiguous.** “>= 80% dimension overlap/coverage” needs a precise denominator: overlap against hand-authored dimensions, coverage of required dimensions, and how partial matches are handled.
5. **Output schema is present but too thin for analysis and replay.** The listed schema omits per-turn metadata, termination reason, rubric version, and simulator version, which are important for regression tracking and debugging.
6. **A small regression in operational context:** “V1 /simulate runs: 4 total...” may conflict with the accepted challenge that no executable `/simulate` exists. If this refers to prior smoke-test/quality-eval workflows under that label, it should be renamed to avoid implying a shipped command implementation.
7. **The quantitative cost line should be tagged under the stated evidence rule if treated as a new factual claim in the revision.** Since it appears inherited from the document, it can remain, but no new unsupported quantitative claims should be added without tags.

## Round 3 (claude-opus-4-6)
The previous revision is substantially better than what a first draft would look like — it correctly addresses most of the accepted challenges. However, several issues remain:

1. **Challenge 1 (IR verification) — well addressed.** The human gate, reference IR, checklist, and signoff artifact are all present and concrete. No regressions.

2. **Challenge 2 (V2 is greenfield) — addressed but inconsistently.** The intro says "net-new" and "greenfield," and there's a reuse-vs-net-new section, but the document title still says "/simulate V2" and the pilot steps don't clarify that no `/simulate` command exists yet. The framing should be tightened: this is a new tool, not a mode added to an existing command.

3. **Challenge 3 (convergence → fixed-N) — well addressed.** Convergence is explicitly deferred, fixed-N is committed to, and the 10-run breakdown is unambiguous. No issues.

4. **Challenge 4 (OCEAN removal) — well addressed.** OCEAN is explicitly excluded. The 6-field hidden state is reasonable. No issues.

5. **Challenge 5 (success criteria) — mostly addressed but has a gap.** Rubric coverage is now primary, score comparison is secondary. Good. But the 80% threshold for rubric coverage is stated without justification. Why 80% and not 70% or 90%? This needs a brief rationale or it looks arbitrary.

6. **Challenge 6 (3-agent loop spec) — well addressed.** Turn structure, termination conditions, tool policy, judge timing, and prompt wiring are all specified. The reuse of `eval_intake.py` mechanics is called out. Minor improvement: the tool/file policy should clarify what "pilot fixture" means concretely.

7. **Challenge 7 (output schema) — well addressed.** JSONL schema is defined with all required fields. No issues.

**Additional issues in the current revision:**

- The document has no explicit **Recommendations** section with numbered items. The "Proposed Approach" and "Simplest Version" sections contain implicit recommendations. I'll preserve these as-is since they are the actionable content.
- The "Non-goals" paragraph buries important scope decisions. It should be a proper list.
- The success criteria numbering mixes validation gates (IR accuracy) with runtime metrics (anchor stability). These serve different purposes and should be grouped.
- The cost estimate ("~4-5.5M tokens") lacks a derivation. It should be tagged as ESTIMATED with assumptions stated.
- "Simplest Version (Pilot)" step ordering is good but should explicitly note that step 1-4 (IR validation) is a hard gate before steps 5-8 (simulation).
- The title and metadata still use "V2" framing which conflicts with the greenfield acknowledgment.

## Final Refined Document

---
topic: skill-compiler-simulator
created: 2026-04-15
---
# Skill Compiler Simulator (Project Codename: sim-compiler)

## Problem
Validating that a BuildOS skill works well for real users requires either manual usage over days ("use it for 3 days and come back") or bespoke manual simulation setup (`eval_intake.py`: 17 rounds, 5 personas, 3-model separation, custom rubric — days of setup per skill). While structural validation (smoke-testing) checks for basic execution, it does not test the interactive user experience across persona types.

The gap: cross-model persona simulation catches real issues (explore intake found and fixed dozens of protocol problems across 5 validation passes), but it required bespoke setup per skill. We need that process to generalize across 22+ BuildOS skills with minimal per-skill configuration.

## Status Quo

**No `/simulate` command or simulator exists as executable code today.** The closest artifact is `eval_intake.py`, which is a hand-built, single-skill evaluation harness for `/explore`. This proposal is a **greenfield implementation** — not an extension of an existing simulator. It reuses patterns and components from `eval_intake.py` (listed below) but builds the simulator driver, IR compiler, persona generator, rubric generator, and output pipeline from scratch.

If the project succeeds, it may later adopt the `/simulate` command name and integrate into the existing CLI dispatch. That integration is out of scope for the pilot.

## Proposed Approach

Build a Skill Compiler Simulator that compiles each `SKILL.md` into an Interaction Representation (IR), then simulates users with hidden state. Five components:

### 1. Skill Compiler & Human Gate

Parse `SKILL.md` into a structured IR containing:
- objective
- decision points
- ask nodes
- success criteria
- failure criteria
- interaction archetype

**The compiler uses an LLM to extract the IR from free-form SKILL.md. Because LLM extraction is not self-validating, the pilot requires a human verification gate before any downstream simulation uses the IR.**

**Pilot IR verification procedure:**
1. For each pilot skill, one reviewer writes a **reference IR by hand** from `SKILL.md`.
2. The compiler generates an **extracted IR**.
3. A second reviewer (not the reference author) compares extracted IR vs. reference IR using this checklist:

| Field | Criteria | Rating |
|---|---|---|
| Objective | Matches the skill's primary user outcome | pass / partial / fail |
| Decision points | All critical decision points present | pass / partial / fail |
| Ask nodes | All required ask nodes present | pass / partial / fail |
| Success criteria | Present and materially correct | pass / partial / fail |
| Failure criteria | Present and materially correct | pass / partial / fail |
| Interaction archetype | Correctly assigned | pass / partial / fail |

4. Reviewer marks each item with notes.
5. **Hard gate:** simulation is blocked unless all fields are `pass` (after corrections if needed).

**Signoff artifact:** store the reference IR, reviewed extracted IR, and completed checklist alongside run outputs. This ensures the compiler output is auditable and not validated only by another model.

**Why this matters:** Bad IR poisons rubric generation, persona generation, and judging. The human gate is the single most important quality control in this pipeline.

### 2. Persona Generator

Create simulated users with a targeted behavioral hidden-state:
- **goal** — what the user is trying to accomplish
- **knowledge** — domain expertise level
- **urgency** — time pressure
- **patience** — tolerance for multi-step processes
- **trust** — willingness to follow system guidance
- **cooperativeness** — how readily the user provides requested information

OCEAN personality traits are **excluded from this pilot**. The 6-field representation above is sufficient to generate behaviorally diverse personas. If pilot results show that failure modes cluster in ways these fields cannot distinguish, OCEAN or other dimensions can be added in a later iteration with a clear diagnostic justification.

**Persona strategy for each skill:**

| Run type | Count | Purpose |
|---|---|---|
| Anchor personas | 3 | Fixed across all runs for regression tracking |
| Generated personas | 5 | Breadth coverage from IR-informed generation |
| Repeated anchor runs | 2 | Score stability measurement (same persona spec, different run) |
| **Total** | **10** | Fixed-N; no dynamic convergence in pilot |

Anchor personas reuse the existing persona-card format from `eval_intake.py` as a structural base, extended with the 6 hidden-state fields.

### 3. Three-Agent Simulation Loop

**Roles:**
- **Executor** (Claude) — runs the skill, sees skill content and runtime instructions
- **Persona** (Gemini) — plays the user from hidden state only; does **not** see the skill procedure or rubric
- **Judge** (GPT) — scores the completed transcript against the validated rubric

**Prompt wiring:**
- Executor receives: skill content, runtime instructions, simulator task wrapper, conversation history.
- Persona receives: its hidden-state card, user-visible task context, conversation history. Nothing else.
- Judge receives: validated rubric, full transcript, termination reason, final outcome summary. Runs **once, after termination** — not per turn.

**Turn structure:**
- Simulation starts with a persona opening message.
- Each turn = one executor response + one persona response.
- **Hard limit: 15 turns per simulation.** No dynamic extension.

**State management:**
- Transcript is appended after every message.
- Persona hidden state is fixed at run start and persisted with the run record.
- Reuse `eval_intake.py` LLM client mechanics (`llm_client.py`) for model invocation and transcript handling.

**Termination conditions** (checked after each turn):
1. Objective met (executor or persona signals completion)
2. Persona explicitly abandons the task
3. Executor declares completion or inability to proceed
4. Hard turn limit (15) reached
5. Unsupported tool/file dependency blocks further progress → status `blocked_environment`

**Tool and file policy:**
- If the skill requests file reads, return mocked file contents **only when a pilot fixture file exists** for that skill in `fixtures/sim_compiler/{skill_name}/`. No fixture → no mock.
- If the skill requires unsupported tools, network access, or undefined files: return a standardized environment limitation message (`"[SIM] Tool/resource not available in simulation environment"`). Continue if the skill can proceed without it; otherwise terminate with `blocked_environment`.
- **No improvised tool responses.** This avoids contaminating the simulation with hallucinated environment state.

**Recorded outcome per run:**
- final status
- termination reason
- whether the objective was achieved
- judge scores per rubric dimension and rationale

### 4. Rubric Generation

Auto-generate a scoring rubric from the **validated IR** (post-human-gate) and interaction archetype. Each rubric includes:
- 3 universal dimensions (applicable to all skills)
- Archetype-specific dimensions (derived from the IR's decision points and success/failure criteria)

**Pilot rubric validation (intake-like skill only):**

Compare the auto-generated rubric to the hand-authored `eval_intake.py` rubric using dimension-level matching:

| Match type | Weight |
|---|---|
| Exact match | 1.0 |
| Partial match (same concept, different granularity) | 0.5 |
| Missing (in hand-authored, not in generated) | 0.0 |
| Extra (in generated, not in hand-authored) | noted but not penalized |

**Coverage metric:** `Σ(match weights) / count(hand-authored dimensions)`

**Threshold: ≥ 80% weighted coverage.** Rationale: below 80%, the generated rubric is missing enough hand-authored dimensions that judge scores become unreliable for the dimensions that matter most. Above 80%, remaining gaps are likely edge-case dimensions that can be added iteratively. This threshold is calibrated against the intake rubric (which has ~8 scored dimensions); missing more than 1.5 of them would drop coverage below 80%. [ESTIMATED: based on the eval_intake.py rubric having approximately 8 dimensions, so 80% ≈ missing ≤ 1.5 dimensions]

**Final score comparison to `eval_intake.py` is secondary calibration only.** It is not a primary success criterion because (a) the turn-loop mechanics differ (15-turn hard limit vs. 17-round intake-specific flow), and (b) matching scores from a hand-crafted pipeline is a coarse check, not a direct validation of rubric correctness. If used, score comparison must use matched run conditions (same personas, same model assignments).

### 5. Output Schema & Storage

All results are written to `logs/sim_compiler_runs.jsonl`, one JSON object per line per simulation run.

**Per-run schema:**
```json
{
  "run_id": "uuid",
  "timestamp": "ISO-8601",
  "simulator_version": "0.1.0-pilot",
  "skill": "explore|investigate|plan",
  "skill_source_path": "skills/{skill}/SKILL.md",
  "ir_metadata": {
    "reference_ir_path": "fixtures/sim_compiler/{skill}/reference_ir.json",
    "extracted_ir_path": "fixtures/sim_compiler/{skill}/extracted_ir.json",
    "review_checklist_path": "fixtures/sim_compiler/{skill}/ir_review.json",
    "review_status": "passed|corrected_and_passed",
    "review_notes": "...",
    "interaction_archetype": "intake|diagnosis|planning"
  },
  "persona_state": {
    "persona_id": "anchor-1|generated-3|...",
    "persona_type": "anchor|generated",
    "goal": "...",
    "knowledge": "novice|intermediate|expert",
    "urgency": "low|medium|high",
    "patience": "low|medium|high",
    "trust": "low|medium|high",
    "cooperativeness": "low|medium|high"
  },
  "execution_config": {
    "executor_model": "claude-opus-...",
    "persona_model": "gemini-3.1-pro",
    "judge_model": "gpt-5.4",
    "max_turns": 15
  },
  "transcript": [
    {
      "turn": 1,
      "role": "persona|executor",
      "content": "...",
      "timestamp": "ISO-8601"
    }
  ],
  "final_status": "success|failure|abandoned|blocked_environment|max_turns",
  "termination_reason": "...",
  "objective_achieved": true,
  "judge_scores": {
    "dimension_name": 4.2
  },
  "judge_rationale": "...",
  "rubric_metadata": {
    "rubric_version": "...",
    "rubric_source": "generated_from_validated_ir",
    "rubric_coverage_vs_reference": 0.85
  }
}
```

## Non-Goals

- **Not simulating all 22 skills.** ~8–10 interactive skills benefit; procedural skills stay on structural smoke-tests.
- **Not building production trace distillation** (future work).
- **Not building live canaries.**
- **Not implementing dynamic convergence for the pilot.** Fixed-N (10 runs per skill) only. Convergence logic (stop when new failure classes stop appearing) requires a failure taxonomy, deduplication method, and novelty threshold — none of which exist yet. Convergence is deferred to a post-pilot iteration, contingent on having enough pilot data to define a failure taxonomy.

## Pilot Plan

### Skills
1. `/explore` — intake archetype (has `eval_intake.py` reference for rubric validation)
2. `/investigate` — diagnosis archetype
3. `/plan` — planning archetype

### Phase 1: IR Validation (Hard Gate)

For each of the 3 skills:
1. Hand-author a reference IR from `SKILL.md`.
2. Run the compiler to generate an extracted IR.
3. Second reviewer compares extracted vs. reference using the checklist (Section 1).
4. Correct the extracted IR until all critical fields pass.
5. Store both IRs and the completed checklist in `fixtures/sim_compiler/{skill}/`.

**No simulation runs proceed until Phase 1 is complete for all 3 skills.**

### Phase 2: Simulation Runs

For each of the 3 skills:
1. Generate 3 anchor personas and 5 generated personas.
2. Run 10 simulations (3 anchor + 5 generated + 2 repeated anchor).
3. Score each completed run with the judge using the generated rubric.
4. Save all outputs to `logs/sim_compiler_runs.jsonl`.

**Total pilot runs: 30** (10 per skill × 3 skills).

### Success Criteria

**Validation gates (must pass to proceed):**

| # | Criterion | Measure | Threshold |
|---|---|---|---|
| 1 | IR Accuracy | All critical checklist fields pass for each pilot skill | 6/6 fields `pass` per skill |
| 2 | IR Auditability | Reference IR, extracted IR, and checklist stored | Artifacts exist for all 3 skills |
| 3 | Rubric Quality | Auto-generated rubric coverage vs. `eval_intake.py` hand-authored rubric | ≥ 80% weighted coverage |

**Runtime metrics (measured, not gating):**

| # | Criterion | Measure | Target |
|---|---|---|---|
| 4 | Execution Reliability | Pilot runs completing without loop crashes or unhandled exceptions | 30/30 runs complete |
| 5 | Anchor Stability | Score variance across repeated anchor runs (same persona spec) | Variance < 0.5 points |
| 6 | Score Calibration (secondary) | Final scores vs. `eval_intake.py` under matched conditions | Directionally consistent; not a pass/fail gate |

## Implementation Scope

### Reuse from `eval_intake.py` / Existing Infrastructure

| Component | Source | How reused |
|---|---|---|
| Model invocation | `llm_client.py` | Direct import |
| Transcript accumulation | `eval_intake.py` patterns | Adapted for 3-agent loop |
| Cross-model role separation | `eval_intake.py` architecture | Same pattern (Claude/Gemini/GPT) |
| Persona-card format | Existing persona cards | Structural base for anchor personas |
| Output conventions | `eval_intake.py` summary format | Basis for JSONL schema |

### Build Net-New

| Component | Description |
|---|---|
| IR compiler | `SKILL.md` → structured IR extraction via LLM |
| IR review workflow | Human-reviewable artifacts, checklist, signoff gate |
| Persona generator | Generalized for non-intake skills, 6-field hidden state |
| Simulator driver | Orchestrates 3-agent loop for arbitrary skills |
| Rubric generator | Generates scoring rubric from validated IR + archetype |
| Output pipeline | JSONL storage with IR metadata and termination outcomes |
| Environment handling | Mock fixtures, tool-limitation responses, `blocked_environment` status |

## Current System Failures

1. **V1 quality-eval is shallow** (2026-04-15): Single scenario, single agent, single judge. No persona diversity, no hidden state, no multi-turn consistency. Catches structural bugs but not interactive experience failures.
2. **Manual simulation doesn't generalize** (2026-04-11): `eval_intake.py` works for `/explore` but required days of bespoke setup (persona cards, rubric, simulation prompt, 17 rounds). Cannot repeat for 22 skills.
3. **"Use it for 3 days" is the only real validation** (ongoing): Skills get shipped with structural tests but no user-experience validation. Issues surface through anecdotal feedback days later.

## Operational Context

- `debate.py` runs 5–10 times/day, 311 entries in `debate-log.jsonl`
- Prior V1 simulation-style validation runs: 4 total (3 smoke-test + 1 quality-eval), all passing
- `eval_intake.py` infrastructure exists: 5 persona cards, 1 rubric, 1 simulation prompt, `llm_client.py`
- LiteLLM proxy running with Claude Opus, GPT-5.4, Gemini 3.1 Pro available
- Cost per full pilot (30 runs across 3 skills): ~1.5–2M tokens [ESTIMATED: assumes ~50K–65K tokens per simulation run (15 turns × ~2K tokens/turn × 2 agents + judge pass), × 30 runs]
- Cost per full production run (10 skills × 10 runs): ~4–5.5M tokens [ESTIMATED: linear extrapolation from pilot estimate]

## Baseline Performance

- **V1 smoke-test:** Catches bash block failures, missing file paths, placeholder detection. 100% structural coverage, 0% interactive experience coverage.
- **V1 quality-eval:** Single scenario eval via `debate.py` review. Catches gross quality failures. No persona diversity, no hidden state tracking, no multi-turn consistency measurement.
- **Manual `eval_intake.py`:** 5 personas, 3-model separation, 17 rounds. Scores: Register 4.2/5, Flow 4.8/5. Delta proof: with intake 4.7/5 avg, without 2.0/5 avg (+2.67). Setup cost: ~2 days per skill. Not generalizable.

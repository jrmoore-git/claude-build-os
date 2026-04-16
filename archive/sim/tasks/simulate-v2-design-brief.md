# /simulate V2 — Skill Compiler Simulator: Design Brief

## What This Is

A comprehensive design brief for the next-generation `/simulate` skill. This document captures the full context from the research and exploration session (2026-04-15, session 6) so a fresh session can pick up and start building without re-deriving any of this.

## The Problem We're Solving

Today, validating that a BuildOS skill works well requires one of:
1. **Manual usage over days** — "use it for 3 days and come back with feedback." Slow, lossy, and the feedback is anecdotal.
2. **Bespoke manual simulation** — what we did with explore intake: 17 rounds, 5 personas, 3-model separation (Claude as interviewer, Gemini as persona, GPT as judge), hand-authored persona cards with hidden truths, custom rubric, custom simulation prompt. Took days of setup. Produced excellent results but doesn't generalize.
3. **V1 /simulate** — smoke-tests (extract and run bash blocks) or basic quality-eval (single scenario, single agent, single judge). Useful for structural validation but doesn't test the interactive user experience.

The gap: we proved that cross-model persona simulation catches real issues (the explore intake process found and fixed dozens of protocol problems across 5 validation passes). But it required bespoke setup per skill. V2 must make that process generalizable across all 22+ BuildOS skills with minimal per-skill configuration.

**The user's framing:** "I'm trying to compress the loop where you say 'go use it for 3 days and come back.' Can we get to 90% now?"

## Chosen Direction: Skill Compiler Simulator (Direction 1)

After Perplexity deep research and cross-model explore (4 directions evaluated by GPT-5.4), Direction 1 was selected. The core idea:

**Stop treating simulation as "prompt a fake user and see what happens." Instead, compile each SKILL.md into an interaction model, then simulate users with hidden state — not free-form roleplay.**

### Why This Direction Won

- **Directly attacks generalizability.** The reusable unit is the interaction structure, not a bespoke prompt pack. One architecture serves many skills.
- **Solves multi-turn consistency.** Hidden user state (goals, knowledge, patience, trust) prevents persona drift — the #1 failure mode in naive roleplay simulation.
- **Gives the judge something objective.** Instead of "did this transcript feel good?", the judge asks "did the skill move the user's hidden state in the right direction?"
- **Auto-bootstraps from SKILL.md.** Minimal manual setup per skill — the compiler extracts what it needs.

### What Was Considered and Rejected

| Direction | Why Not Primary |
|-----------|----------------|
| **Replay + Perturbation Harness** (D2) | Fast to validate but stays anchored to example quality. Fuzz testing, not understanding. Good as a coverage expander within D1, not as the core architecture. |
| **Production Trace Distillation** (D3) | Premature — not enough production transcripts yet. Becomes valuable later as a feedback loop once D1 is running and generating data. |
| **Contracts + Live Canaries** (D4) | Pragmatic but doesn't solve the compression problem. Still waiting for real users, just with better structure. The per-skill contract idea is worth borrowing as metadata input to D1's compiler. |

**Hybrid elements to incorporate:**
- D2's perturbation approach as a coverage expander within D1's architecture
- D4's per-skill contracts as optional metadata that makes the compiler's job easier
- D3 layers in later when production transcripts accumulate

## The Gold Standard: What eval_intake.py Already Proved

The manual explore intake simulation (session ~4/11) is the reference implementation. It proved:

### Architecture (3-model separation)
- **Interviewer model** (Claude Opus): executes the skill procedure
- **Persona model** (Gemini 3.1 Pro): plays the user — sees only their persona card, NOT the skill procedure or rubric
- **Judge model** (GPT-5.4): scores the transcript — sees everything after the fact

This separation prevents sycophancy and data leakage. Research confirms: when the persona model sees the procedure or rubric, results inflate 12-18%.

### Persona Design (hidden state + behavioral rules)
Each persona card (`config/eval-personas/*.md`) includes:
- **Character:** Name, age, role, communication style (register cues like "hedging," "em dashes," "casual")
- **Opening input:** What they'd type to start the skill
- **Hidden truth:** Something the skill should surface but the persona won't volunteer directly
- **Behavior rules:** How the persona reacts to different interviewer moves (e.g., "circle back to X twice before accepting reframe")
- **Key details to reveal when asked:** Information the persona shares only when prompted correctly
- **Protocol features being tested:** Which specific skill behaviors this persona is designed to exercise

5 existing personas: `reframe-acceptance.md`, `reframe-rejection.md`, `thin-answers.md`, `presupposition-sufficiency.md`, `meta-question-blindspot.md`

### Evaluation (structured rubric with pass criteria)
The rubric (`config/eval-rubric.md`) scores 6 dimensions:
1. Register match (does the interviewer write like the user?)
2. Flow (does each question thread from the previous answer?)
3. Sufficiency timing (did intake stop at the right moment?)
4. Context block quality (is the output well-structured?)
5. Hidden truth surfacing (did the skill find the real problem?)
6. Feature-specific test (did the tested protocol feature fire?)

Pass: all dimensions 4+, feature test 4+, average 4.5+

### Results Achieved
- 5 validation passes, 17 rounds total
- Register: 4.2/5, Flow: 4.8/5 (cross-model consensus)
- Found and fixed dozens of protocol issues across passes
- Delta proof: with intake = 4.7/5 avg, without = 2.0/5 avg (+2.67 delta)

### Key Files
- `scripts/eval_intake.py` — the orchestration script (22KB, uses llm_client.py)
- `config/eval-personas/` — 5 persona cards
- `config/eval-rubric.md` — structured rubric with JSON output format
- `tasks/explore-intake-sim-prompt.md` — the simulation prompt template
- `tasks/explore-intake-validation-log.md` — full test history
- `tasks/explore-intake-personas.md` — persona definitions (23KB)

## V2 Architecture: The Skill Compiler Simulator

### Overview

```
SKILL.md ──→ [Compiler] ──→ Interaction Model (IR)
                                    │
                                    ▼
                            [Persona Generator]
                            (OCEAN + hidden state)
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │     3-Agent Simulation Loop     │
                    │                                 │
                    │  Executor ←──→ Persona ←──→ Judge │
                    │  (runs skill)  (hidden state) (scores) │
                    └───────────────────────────────┘
                                    │
                                    ▼
                            [Report + Findings]
```

### Component 1: Skill Compiler

**Input:** A SKILL.md file (raw markdown with YAML frontmatter)

**Output:** An Interaction Representation (IR) containing:

| IR Field | Description | Example (for /explore intake) |
|----------|-------------|-------------------------------|
| `objective` | What the skill accomplishes | "Discover the user's real problem and produce divergent explore directions" |
| `interaction_archetype` | Category of interaction | `intake` (others: `diagnosis`, `planning`, `critique`, `synthesis`, `coaching`) |
| `required_inputs` | What the skill needs from the user | ["problem statement", "domain context"] |
| `optional_inputs` | Nice-to-have information | ["constraints", "prior attempts", "timeline"] |
| `decision_points` | Where the skill branches based on user input | ["clarity tier classification", "skip vs. full intake", "sufficiency gate"] |
| `ask_nodes` | Every AskUserQuestion moment with what's being asked | [{"step": "3a", "asks": "Which direction resonates?", "options": "A/B/C/D"}] |
| `tool_calls` | External tools the skill invokes | ["debate.py explore", "Agent with worktree"] |
| `success_criteria` | What a good outcome looks like | ["context block captures real problem", "directions are divergent", "user says 'would act on this'"] |
| `failure_modes` | Known ways the skill breaks | ["over-asking", "register mismatch", "solving during intake", "missing hidden truth"] |
| `output_artifact` | What the skill produces | "tasks/<topic>-explore.md" |

**How the compiler works:**
1. Parse SKILL.md structure: sections, steps, bash blocks, AskUserQuestion calls
2. Extract the procedure's logical flow (sequential steps, conditional branches)
3. Identify interaction moments (where the user must respond)
4. Infer success/failure criteria from the procedure's own language
5. Classify into an interaction archetype

**The key risk:** If the compiler misreads the SKILL.md, everything downstream looks rigorous but tests the wrong thing. Mitigation: validate the IR against the original SKILL.md with a separate model before proceeding.

### Component 2: Persona Generator

**Input:** IR + optional per-skill persona hints

**Output:** Persona cards with hidden state

Each generated persona has 8 hidden-state fields:

| Field | Type | Description |
|-------|------|-------------|
| `goal` | string | What the persona is trying to accomplish |
| `knowledge` | enum: novice/intermediate/expert | Domain expertise level |
| `urgency` | enum: low/medium/high/crisis | Time pressure |
| `patience` | int 1-5 | Willingness to answer questions |
| `trust` | int 1-5 | Starting trust in the AI |
| `cooperativeness` | int 1-5 | How forthcoming with information |
| `verbosity` | enum: terse/moderate/verbose | Communication style |
| `ambiguity_tolerance` | int 1-5 | Comfort with open-ended exploration |

Plus OCEAN traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) as behavioral modifiers.

**Persona types (hybrid approach):**
- **Anchor personas** (3-5 per skill family): Fixed, hand-tuned personas for regression testing. Like the existing eval-personas. Give stability and comparability across runs.
- **Generated personas**: OCEAN-parameterized variations for breadth. The generator creates realistic combinations of the 8 fields + OCEAN that exercise different paths through the IR's decision points and ask nodes.

**Critical design rule from research:** The persona model MUST NOT see the skill procedure, the IR, or the evaluation rubric. It sees only its persona card. This prevents data leakage (research shows 12-18% score inflation when the persona can see what the skill is supposed to do).

**Borrowing from eval_intake.py persona design:**
- Each persona gets a "hidden truth" — something the skill should surface but the persona won't volunteer
- Behavioral rules: how the persona reacts to specific skill behaviors (e.g., "push back once on reframe, then accept")
- Key details to reveal only when asked correctly
- Protocol features being tested: which skill behaviors this persona exercises

### Component 3: Three-Agent Simulation Loop

**Agent 1 — Executor (runs the skill)**
- Model: Claude Opus (or the skill's natural execution model)
- Sees: The full SKILL.md procedure + the persona's opening input
- Does: Follows the skill procedure step by step, treating the persona as a real user
- Key constraint: When the procedure calls for AskUserQuestion, it asks. The persona agent responds.

**Agent 2 — Persona (simulates the user)**
- Model: Gemini (or a different model family from the executor — cross-model separation is essential)
- Sees: Only its persona card (character, hidden truth, behavior rules, key details)
- Does: Responds to the executor's questions in character, maintaining hidden state consistency
- Key constraint: Does NOT see the skill procedure, IR, or rubric. Responds from hidden state only.
- State tracking: Before each response, the persona agent receives its current goal state (from the hidden state tracker) to prevent drift. Research shows this improves goal alignment by up to 5.4%.

**Agent 3 — Judge (evaluates the interaction)**
- Model: GPT (or a third model family)
- Sees: The full transcript, the IR, the persona card (including hidden truth), and the rubric
- Does: Scores the interaction on rubric dimensions. Identifies failure modes.
- Key constraint: Evaluates after the interaction is complete, not during.

**Turn loop:**
```
1. Executor receives persona's opening input
2. Executor follows skill procedure, produces a response/question
3. Persona receives executor's response, generates reply from hidden state
4. Hidden state tracker updates persona's state (trust, patience may shift)
5. Repeat 2-4 until executor signals completion or turn limit reached
6. Judge receives full transcript + context, produces structured evaluation
```

**Turn limit:** Default 15 turns. Skills like intake should converge in 5-8. If the executor hasn't reached completion by the limit, that's a finding (over-asking or failure to converge).

### Component 4: Rubric Generation

**Input:** IR + interaction archetype

**Output:** Structured rubric with scored dimensions

**Universal dimensions (all archetypes):**
1. Task completion — did the skill accomplish its stated objective?
2. Register match — did the skill's communication style match the user's?
3. Turn efficiency — was the interaction appropriately concise?

**Archetype-specific dimensions:**

| Archetype | Additional Dimensions |
|-----------|-----------------------|
| `intake` | Flow (threading), sufficiency timing, hidden truth surfacing, context block quality |
| `diagnosis` | Root cause identification, evidence gathering, false positive rate |
| `planning` | Completeness, feasibility, risk identification, decomposition quality |
| `critique` | Specificity, actionability, fairness, missed issues |
| `synthesis` | Source integration, divergence, insight density |
| `coaching` | Question quality, user autonomy preservation, behavioral shift |

**Auto-extraction:** The compiler can infer skill-specific rubric dimensions from the IR's success criteria and failure modes. These supplement (don't replace) the archetype defaults.

### Component 5: Convergence and Stopping

**When to stop iterating:**
- Score distributions stabilize across persona slices (no new failure classes in N runs)
- Cross-model judge agreement reaches target (e.g., 3/3 models at 4/5 on key dimensions)
- Diminishing returns: additional personas/runs don't surface materially new issues

**From research:** Stop on consensus. When a cross-model evaluation loop reaches the target score, stop. Don't run additional rounds to chase edge-case improvements — the marginal value drops faster than the time cost rises.

**Human routing:** Only escalate to the user when:
- Cross-model judges diverge significantly (disagreement > 1 point on key dimensions)
- A high-severity failure is found (score 1-2 on any dimension)
- The simulation surfaces a design question (not just an implementation bug)

## Interaction Archetypes Across BuildOS Skills

Based on the 22 current skills, here's how they cluster:

| Archetype | Skills | Simulation Complexity |
|-----------|--------|----------------------|
| **Intake** | /explore (intake phase), /think discover | HIGH — multi-turn, register matching, hidden truth surfacing |
| **Diagnosis** | /investigate, /triage, /audit | HIGH — evidence gathering, root cause analysis |
| **Planning** | /plan, /think refine | MEDIUM — structured output, completeness checking |
| **Critique** | /challenge, /pressure-test, /review | MEDIUM — adversarial quality, specificity |
| **Synthesis** | /explore (output phase), /research | MEDIUM — source integration, divergence |
| **Coaching** | /elevate, /guide | MEDIUM — question quality, user autonomy |
| **Procedural** | /ship, /wrap, /start, /sync, /log, /simulate, /setup, /healthcheck | LOW — mostly deterministic, better served by smoke-test + contract checks |
| **Creative** | /design, /polish | HIGH — subjective quality, multi-model collaboration |

**Implication:** Not all 22 skills need full persona simulation. ~8-10 interactive skills benefit most. Procedural skills are better served by V1 smoke-tests + contracts (Direction 4's insight). The compiler should classify skills and recommend the appropriate simulation depth.

## Implementation Plan: First Move

### Phase 1: Compiler Pilot (3 skills)

Pick one skill from each of three archetypes:
1. **Intake:** /explore (has existing eval_intake.py infrastructure to validate against)
2. **Diagnosis:** /investigate
3. **Planning:** /plan

For each:
1. Build the compiler — extract the IR from SKILL.md
2. Validate IR accuracy by having a separate model compare IR to SKILL.md
3. Generate 3 anchor personas + 5 generated personas per skill
4. Run 10 simulations per skill (3 anchor + 5 generated + 2 adversarial)
5. Score with cross-model judge panel

**Success criteria for the pilot:**
- Compiler extracts IR that a human reviewer agrees accurately represents the skill
- Anchor personas produce consistent scores across re-runs (variance < 0.5 on each dimension)
- Generated personas surface at least 2 failure modes not found by anchor personas
- For /explore: V2 results are within 0.5 points of eval_intake.py results on the same rubric dimensions

### Phase 2: Generalization

- Abstract the compiler to handle all 6 interaction archetypes
- Build the archetype-specific rubric templates
- Integrate as the new `--mode persona-sim` in /simulate SKILL.md
- Run across all interaction-heavy skills (8-10)
- Establish regression baselines

### Phase 3: Feedback Loop

- Instrument skill executions to capture transcripts (anonymized)
- Feed production traces back into persona generation (Direction 3's insight)
- Perturbation engine for coverage expansion (Direction 2's insight)
- Convergence tracking: detect when additional simulation rounds stop adding value

## Key Research Findings to Internalize

From `tasks/ai-user-simulation-research.md` (50 citations, Perplexity deep research):

1. **85% alignment baseline.** Synthetic Users reports 85-92% alignment with real human responses depending on audience type. Academic validation: LLM simulations are 85% as accurate as humans re-taking the same survey 2 weeks later.

2. **Cross-model separation is non-negotiable.** Data leakage (persona seeing the procedure/rubric) inflates results 12-18%. The 3-model architecture (executor/persona/judge on different model families) is standard practice.

3. **OCEAN personality model works.** Prompt-based OCEAN induction significantly influences LLM task planning and decision-making. Effects are more pronounced in more capable models.

4. **Multi-turn consistency requires explicit state tracking.** Off-the-shelf LLMs drift from assigned personas across extended conversations. Explicit goal-state injection before each turn improves alignment by up to 5.4%. Smaller well-tuned models (8B) can outperform larger ones (70B) on persona consistency.

5. **DPRF (Dynamic Persona Refinement Framework)** iteratively refines personas against ground truth. Consistently improves behavioral alignment across models and scenarios.

6. **Feedback loop compression is real.** TestPilot shifted teams from 3-5 research occasions/year to 30-50 at similar cost with faster turnaround.

7. **Model collapse risk.** When synthetic data feeds back into training without mixing in real data, progressive quality degradation occurs. Always mix real transcripts with synthetic data.

8. **Convergence criterion should be failure discovery rate, not average score.** Stop when N additional batches stop surfacing new failure classes.

## Known Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Compiler extracts wrong IR from messy SKILL.md | HIGH | HIGH — rigorous-looking but testing wrong thing | Validate IR with separate model; human spot-check on first 3 skills |
| Generated personas are too similar (diversity failure) | MEDIUM | MEDIUM — false coverage | Enforce minimum distance between OCEAN profiles; track failure class diversity |
| Judge sycophancy (scoring too high) | MEDIUM | HIGH — false confidence | Cross-model judging; calibrate against known-bad skill versions |
| Persona sees procedure (data leakage) | LOW (if architecture enforced) | HIGH — 12-18% score inflation | Strict prompt separation; never include procedure in persona context |
| Simulation cost too high per run | MEDIUM | LOW — economics, not quality | Use smaller models for persona (8B sufficient per research); batch runs |
| Skills too messy for compiler to parse | MEDIUM | MEDIUM — limits generalization | Start with well-structured skills; iterate compiler on failures |

## Cost Model

Per simulation run (rough estimates based on current model pricing):
- Executor (Opus): ~15-20 turns x ~2K tokens/turn = ~30-40K tokens
- Persona (Gemini Pro): ~15-20 turns x ~500 tokens/turn = ~7-10K tokens  
- Judge (GPT-5.4): ~1 evaluation x ~5K tokens = ~5K tokens
- Total per run: ~40-55K tokens across 3 models
- Per skill (10 runs): ~400-550K tokens
- Full suite (10 skills): ~4-5.5M tokens

Via LiteLLM + debate.py infrastructure already in place. Comparable to a single `/challenge --deep` pipeline run.

## Relationship to V1 /simulate

V1 stays as-is. V2 adds a new mode:

```
/simulate /explore                    # V1 smoke-test (default, unchanged)
/simulate /explore --mode smoke-test  # V1 explicit
/simulate /explore --mode quality-eval # V1 single-scenario eval
/simulate /explore --mode persona-sim  # V2 — full skill compiler simulation
```

V1 smoke-test remains useful for structural validation (bash blocks work, file paths exist). V2 persona-sim tests the interactive user experience. They're complementary.

## Files to Read Before Starting

| File | Why |
|------|-----|
| `.claude/skills/simulate/SKILL.md` | Current V1 implementation — understand what exists |
| `scripts/eval_intake.py` | The manual gold standard — understand the 3-model architecture |
| `config/eval-personas/*.md` (5 files) | See how effective persona cards are structured |
| `config/eval-rubric.md` | See how effective rubrics are structured |
| `tasks/explore-intake-validation-log.md` | The results that proved this approach works |
| `tasks/explore-intake-sim-prompt.md` | The simulation prompt template |
| `tasks/ai-user-simulation-research.md` | Full Perplexity research (50 citations) |
| `tasks/simulate-v2-explore.md` | Cross-model explore output with all 4 directions |
| `scripts/debate.py` | The cross-model engine — V2 will build on this |
| `scripts/llm_client.py` | The LLM abstraction layer used by eval_intake.py |
| `.claude/rules/reference/debate-invocations.md` | How to call debate.py |

## Open Design Questions

These need answers during implementation:

1. **Should the compiler be a Python script or an LLM prompt?** A Python parser is more reliable but may miss semantic intent. An LLM extraction is more flexible but less deterministic. Hybrid likely best: Python for structure, LLM for semantic fields.

2. **Where does the IR live?** Options: (a) generated fresh each run, (b) cached alongside SKILL.md as `SIM_IR.json`, (c) embedded in SKILL.md frontmatter. Caching is probably right — regenerate only when SKILL.md changes.

3. **How many anchor personas per archetype?** eval_intake.py used 5. Research suggests 3-5 is the sweet spot. More than 7 hits diminishing returns.

4. **Should the judge see the persona card?** eval_intake.py's rubric includes hidden truth scoring, which requires the judge to know the hidden truth. But showing the full persona card to the judge may bias scoring. Probably: show hidden truth and protocol features being tested, but not behavioral rules.

5. **How to handle skills that call debate.py internally?** Skills like /challenge and /review invoke debate.py as part of their procedure. The executor agent would need access to debate.py. This is expensive (nested cross-model calls). May need a mock/stub mode for debate.py during simulation.

6. **Integration with /review pipeline.** Should persona-sim be a gate before `/review`? Or complementary? Probably complementary — persona-sim tests user experience, /review tests code quality.

## Session Context

- **Session 6** (2026-04-15): Battle-tested V1, pivoted to V2 scoping
- V1 battle test results: 3 smoke-tests + 1 quality-eval, all passing
- Fixed grep pattern vulnerability across 6 skills during battle testing
- Fixed /log numbering collision vulnerability
- Research + explore completed, direction chosen, this brief written
- Uncommitted files: `tasks/ai-user-simulation-research.md`, `tasks/simulate-v2-explore.md`, `stores/debate-log.jsonl` (updated)
- This design brief should be committed along with the other session artifacts

---
debate_id: simulate-v2-findings
created: 2026-04-15T10:59:17-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: claude-sonnet-4-6
---
# simulate-v2-findings — Challenger Reviews

## Challenger A — Challenges
Now I have a thorough picture. Let me formulate my review.

## Challenges

1. **ASSUMPTION** [MATERIAL] [COST:SMALL]: **V1 /simulate doesn't exist as code — "adds `--mode persona-sim` to existing /simulate" has no target.** The proposal says it adds a new mode to existing /simulate, but there is no `simulate` function, `simulate.py` script, or `simulate` subcommand in debate.py (verified: 4136 lines, no simulate in command dispatch at lines 4106-4131). There's a `/simulate` skill reference in skills/ (1 match), but no backing implementation. The proposal is building V2 on top of a V1 that doesn't exist as executable code. This means the "simplest version" is actually a greenfield build of the entire simulation infrastructure, not an incremental mode addition. The scope estimate and framing as an extension are misleading.

2. **RISK** [MATERIAL] [COST:MEDIUM]: **The Skill Compiler is the hardest unsolved problem and gets the least specification.** The proposal hand-waves "parses SKILL.md into structured IR (objective, decision points, ask nodes, success/failure criteria, interaction archetype)" but SKILL.md files are free-form markdown (verified: they exist in skills/ with 3 references). Parsing unstructured markdown into a formal IR with decision points and ask nodes is itself an LLM task with its own failure modes. If the compiler misidentifies decision points or misses interaction branches, every downstream component (persona generation, rubric generation, convergence detection) inherits that error. The proposal has no validation step for the IR itself beyond "validate IR with separate model" — which is circular (LLM validates LLM output). The success criterion "compiler extracts accurate IR" has no ground truth to measure against.

3. **OVER-ENGINEERED** [MATERIAL] [COST:TRIVIAL to fix by descoping]: **8 hidden-state fields + OCEAN personality traits is excessive for a V2 pilot.** The proposal specifies 8 hidden-state dimensions (goal, knowledge, urgency, patience, trust, cooperativeness, verbosity, ambiguity tolerance) plus 5 OCEAN traits = 13 personality dimensions. eval_intake.py used 5 persona cards and found "dozens of protocol problems." There's no evidence that 13-dimensional persona parameterization produces meaningfully different simulation behavior than 5 well-chosen persona descriptions. The combinatorial space (13 continuous dimensions) makes it impossible to attribute failure modes to specific persona characteristics, defeating the diagnostic purpose. Start with 4-5 discrete persona archetypes (as eval_intake.py did successfully) and add dimensionality only when you have evidence the simpler approach misses failure classes.

4. **UNDER-ENGINEERED** [MATERIAL] [COST:MEDIUM]: **No specification for how the 3-agent loop actually works mechanically.** The proposal says "Executor (Claude, runs skill) + Persona (Gemini, plays user) + Judge (GPT, scores after completion)" but doesn't address: How does the Executor "run" a skill? Skills are SKILL.md instructions for Claude — does the Executor get the full SKILL.md as a system prompt and then interact with the Persona? How are multi-turn conversations managed (context window limits across 17+ rounds)? What happens when the Executor asks for file reads or tool use that the simulation environment can't provide? eval_intake.py presumably solved these problems, but the proposal doesn't reference its solutions or acknowledge these mechanical challenges.

5. **ASSUMPTION** [MATERIAL] [COST:SMALL]: **"Convergence = new failure classes stop appearing" requires a failure classifier that doesn't exist.** The stopping criterion is "stops when new runs stop surfacing new failure classes, not when average score stabilizes." This requires automatically classifying failures into classes and detecting novelty — itself a non-trivial LLM task. If the classifier is too coarse, you stop too early; too fine, you never converge. The proposal doesn't specify how failure classification works, what granularity defines a "class," or what the convergence threshold is (how many runs with no new classes before stopping?).

6. **RISK** [ADVISORY]: **debate.py is already 4136 lines with no test coverage.** Verified: `check_test_coverage` returns no tests for debate.py. Adding simulation infrastructure to this file (or depending heavily on it) compounds the maintenance risk. The proposal doesn't mention where the new code lives — if it's another subcommand in debate.py, the file becomes even more unwieldy. If it's a new file, the dependency on llm_client.py is fine but the relationship to debate.py's review/judge infrastructure needs specification.

7. **ALTERNATIVE** [ADVISORY]: **Templatize eval_intake.py instead of building a compiler.** The proposal acknowledges eval_intake.py works well but "required days of bespoke setup." An alternative: extract eval_intake.py's architecture into a template with pluggable persona cards, rubric, and simulation prompt — then manually author those 3 artifacts per skill (30-60 min each, not days). This avoids the entire Skill Compiler problem (challenge #2) and the IR validation problem, while still generalizing the simulation loop. The "days of setup" claim for eval_intake.py is SPECULATIVE — it's unclear how much of that was first-time infrastructure vs. per-skill configuration.

8. **RISK** [ADVISORY]: **Cost estimate of 4-5.5M tokens for 10 skills is ESTIMATED with unstated assumptions.** The proposal doesn't show the math. At 17 rounds × 10 simulations × 10 skills = 1,700 multi-turn conversations across 3 models, the token count depends heavily on average turn length, context window accumulation, and whether conversations are truncated. If turns average 1K tokens and context accumulates, a 17-round conversation could consume 150K+ tokens per run, putting 10 skills at 15M+ tokens — 3× the estimate.

## Concessions

1. **The problem is real and well-diagnosed.** The gap between structural smoke-tests and "use it for 3 days" is genuine. The eval_intake.py experience provides concrete evidence that cross-model persona simulation catches real issues that other methods miss.

2. **3-model separation is a sound architectural choice.** Using different models for executor/persona/judge prevents the self-evaluation bias that plagues single-model testing. The existing persona_model_map and LiteLLM infrastructure (verified in llm_client.py and config) make this operationally feasible.

3. **The pilot scope (3 skills, 10 simulations each) is appropriately bounded.** Starting with /explore, /investigate, /plan and requiring calibration against eval_intake.py results provides a concrete success criterion.

## Verdict

**REVISE** — The proposal builds V2 on a V1 that doesn't exist as code, under-specifies the hardest component (Skill Compiler → IR), and over-specifies persona dimensionality without evidence it improves on eval_intake.py's simpler approach. The core idea is sound but needs: (1) honest scoping as a greenfield build, (2) a concrete specification or alternative for how SKILL.md becomes simulatable, and (3) a simpler persona model for the pilot with dimensionality as a later enhancement.

---

## Challenger B — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:MEDIUM]: The proposal assumes `SKILL.md` can be compiled into a sufficiently accurate Interaction Representation across heterogeneous skills, but no evidence is provided that the target skills actually share stable, machine-extractable structures like “decision points,” “ask nodes,” and “success/failure criteria.” The only verified comparable artifact is `scripts/eval_intake.py`, which is bespoke to intake-style flows, not a general compiler. If this assumption fails, the whole architecture collapses into brittle prompt extraction rather than reusable infrastructure.

2. [ALTERNATIVE] [MATERIAL] [COST:SMALL]: You did not seriously consider a lower-risk alternative: parameterizing the existing verified harness in `scripts/eval_intake.py` into a generic multi-turn simulator before introducing a compiler + IR layer. The current script already implements the core 3-agent pattern (Claude interviewer, Gemini persona, GPT judge) and has test coverage (`tests/test_eval_intake.py`). A “protocol template + persona schema + rubric template” path would validate demand faster and isolate whether the real bottleneck is simulation orchestration versus IR extraction.

3. [RISK] [MATERIAL] [COST:MEDIUM]: The proposal adds three generated artifacts in sequence—IR, persona set, and rubric—then uses a judge to evaluate outcomes, but it does not address compounding model error. A bad compiler yields a bad rubric; a bad rubric makes the judge confidently wrong; convergence logic then may stop early based on synthetic failure-class stability. This is a material validity risk because the system could appear rigorous while drifting away from actual user experience.

4. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: “Convergence + Stopping” is underspecified. “Stops when new runs stop surfacing new failure classes” relies on a failure taxonomy, deduping method, and threshold for novelty, none of which are defined. Without that, runs may stop too early due to judge insensitivity or continue indefinitely due to prompt variance generating superficially distinct failures. This directly affects cost, runtime, and trustworthiness.

5. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The success criteria are too weak to validate generalization. On the pilot, “variance < 0.5” for anchor personas and “at least 2 failure modes not found by anchors” can be satisfied even if the generated personas are noisy or unrealistic. Likewise, “results within 0.5 points of eval_intake.py” only checks one skill (`/explore`) against one existing bespoke baseline. That does not verify the compiler works for diagnosis or planning interactions.

6. [RISK] [MATERIAL] [COST:SMALL]: The proposal relies on cross-model separation to prevent leakage and role collapse, but it does not specify controls for persona fidelity over multi-turn conversations. Hidden-state personas can still drift, become overly compliant, or implicitly infer the procedure. That failure mode matters because the system’s central claim is that it tests interactive user experience better than V1; if personas become “good eval actors” rather than plausible users, the signal degrades.

7. [ALTERNATIVE] [ADVISORY]: The design jumps to OCEAN traits plus 8 hidden-state fields without showing that both layers are necessary. A simpler persona model using only behaviorally actionable fields (goal, patience, trust, cooperativeness, etc.) may produce comparable coverage with less prompt complexity and less variance.

8. [OVER-ENGINEERED] [ADVISORY]: The combination of compiler, IR validator, auto-rubric generation, anchor personas, generated personas, 3-agent loop, and convergence detection is a large stack for a pilot covering only 3 skills. For a first iteration, this looks like infrastructure-first design rather than the minimum experiment needed to falsify the idea.

9. [UNDER-ENGINEERED] [ADVISORY]: The proposal names “~8-10 interactive skills benefit” but gives no selection rubric for what counts as interactive enough to justify V2. Without an explicit gating rule, scope creep is likely and teams may try to force unsuitable procedural skills into persona simulation.

10. [RISK] [ADVISORY]: Quantitative cost claims are not decision-grade yet. The “~4-5.5M tokens” estimate is **SPECULATIVE**: no token accounting, turn assumptions, or per-agent prompt sizes are supplied. It may still be directionally useful, but it should not drive rollout planning without measurement.

11. [RISK] [ADVISORY]: The proposal cites current operational context like “debate.py runs 5-10 times/day” and “311 entries in debate-log.jsonl,” but these are **SPECULATIVE** in this review because repository tools verified the presence of `scripts/debate.py` and references to `debate-log.jsonl`, not the actual run frequency or log count. Those numbers may be right, but they are unverified here and should not be used as strong supporting evidence.

## Concessions
1. The proposal correctly identifies a real gap between structural validation and interactive UX validation; the existing verified `scripts/eval_intake.py` shows the need is not hypothetical.
2. Keeping V1 unchanged and scoping V2 to a subset of interactive skills is a good containment decision.
3. Using anchor personas for regression plus generated personas for breadth is directionally sound if the validation methodology is tightened.

## Verdict
REVISE — the problem is real and the direction is plausible, but the proposal overcommits to an unproven compiler-centric architecture without first de-risking IR extractability, evaluator validity, and stopping logic.

Quantitative claims:
- “debate.py runs 5-10 times/day” — SPECULATIVE: no verified operational metric data in this review.
- “311 entries in debate-log.jsonl” — SPECULATIVE: file reference verified, entry count not verified.
- “V1 /simulate runs: 4 total” — SPECULATIVE: no repository or operational verification provided.
- “Cost per full V2 run (10 skills): ~4-5.5M tokens” — SPECULATIVE: no token breakdown or measured run data provided.
- “variance < 0.5” success threshold — ESTIMATED: proposal-defined threshold, not evidence-backed.
- “generated personas surface at least 2 failure modes” — ESTIMATED: target threshold, not evidence-backed.
- “/explore V2 results within 0.5 points of eval_intake.py” — ESTIMATED: acceptance criterion, not current evidence.
- “Manual eval_intake.py: 5 personas, 3-model separation” — EVIDENCED: verified in `scripts/eval_intake.py` docstring.
- “eval_intake.py has test coverage” — EVIDENCED: verified by `check_test_coverage` showing `tests/test_eval_intake.py`.

---

## Challenger C — Challenges
Good. I now have enough verified data to evaluate. Let me compile the findings.

---

## Challenges

**1. ASSUMPTION [MATERIAL] [COST:MEDIUM]: The Skill Compiler's IR extraction is assumed to be reliable, but no SKILL.md has a machine-parseable structure.**

The proposal's entire architecture depends on the Skill Compiler accurately extracting "decision points, ask nodes, success/failure criteria, interaction archetype" from SKILL.md files. Verified: `interaction_archetype`, `decision_point`, `ask_node`, and `failure_mode` are all absent from the codebase — these are net-new concepts with zero existing implementation. More critically, SKILL.md files are prose documents written for human readers, not structured for LLM parsing. The compiler will be doing open-ended extraction from unstructured markdown. If the IR is wrong, the rubric generated from it is wrong, and every downstream score is measuring the wrong thing. The proposal treats IR accuracy as a solved problem ("validate IR with separate model") but IR validation by a second LLM is not the same as ground-truth correctness — it's two LLMs agreeing, which is a known failure mode. The success criterion "compiler extracts accurate IR" has no defined measurement methodology. **Fix cost: MEDIUM** — requires either a structured SKILL.md schema (breaking change to 22 skills) or a robust extraction + human-validation loop before the pilot.

---

**2. ASSUMPTION [MATERIAL] [COST:SMALL]: The convergence stopping criterion ("new failure classes stop appearing") is undefined and unimplemented.**

The proposal names convergence-based stopping as Component 5, but `convergence` has zero occurrences in the codebase. The mechanism for classifying a judge output as a "new failure class" vs. a variant of an existing one is not specified. This is a hard unsolved problem in LLM evaluation: failure taxonomy requires either a fixed ontology (which defeats the purpose of generative discovery) or a clustering step (which requires its own validation). Without a concrete algorithm, the stopping criterion defaults to "run 10 simulations" — which is what the simplest version already specifies. The convergence framing is aspirational, not operational. **Fix cost: SMALL** — either define a concrete algorithm (e.g., embedding-based clustering of judge failure descriptions with a novelty threshold) or remove convergence from the proposal and commit to fixed-N runs.

---

**3. RISK [MATERIAL] [COST:SMALL]: The "within 0.5 points of eval_intake.py on same rubric dimensions" success criterion is not achievable as stated.**

Verified: `eval_intake.py` uses a fixed rubric at `config/eval-rubric.md` with fixed persona cards. The V2 proposal generates rubrics automatically from IR. For the scores to be comparable, the auto-generated rubric must produce the same dimensions as the hand-crafted rubric — which is only true if the Skill Compiler correctly identifies the same dimensions a human expert encoded. This is circular: the success criterion validates the compiler by comparing to a rubric the compiler is supposed to replace. Additionally, the existing eval_intake.py runs at `--max-turns 8` with a hardcoded sufficiency signal (`SUFFICIENCY_REACHED`), while V2 proposes a generic turn loop. The baseline scores (Register 4.2/5, Flow 4.8/5) are EVIDENCED from the proposal but the rubric dimensions they map to are not verified to be reproducible by auto-generation. **Fix cost: SMALL** — restate the success criterion as "auto-generated rubric dimensions overlap ≥ 80% with hand-crafted rubric dimensions" and measure that directly, rather than comparing final scores.

---

**4. RISK [MATERIAL] [COST:MEDIUM]: The Persona Generator's hidden-state model (8 fields + OCEAN) has no grounding in what actually caused failures in eval_intake.py.**

The proposal claims eval_intake.py "found and fixed dozens of protocol problems across 5 validation passes." Verified: the existing persona system uses 5 persona cards (markdown files in `config/eval-personas/`) that encode behavior directly (e.g., "thin answers = 5-15 words," "reject reframe"). The V2 proposal replaces this with a generative hidden-state model (goal, knowledge, urgency, patience, trust, cooperativeness, verbosity, ambiguity tolerance + OCEAN). There is no evidence that OCEAN traits or the 8-field model produce behavior that matches the failure modes the hand-crafted personas were designed to stress-test. The existing persona system works because it encodes *specific* failure-inducing behaviors. A generative model may produce plausible-sounding personas that never trigger the edge cases the hand-crafted ones reliably hit. The "generated personas surface at least 2 failure modes not found by anchors" success criterion is only meaningful if the anchors are already covering the known failure space — which requires the anchor personas to be the existing 5 cards, not newly generated ones. **Fix cost: MEDIUM** — anchor personas should be the existing 5 eval-personas cards (verified to exist), not newly generated ones, and the success criterion should be "generated personas surface failures not found by the existing 5."

---

**5. ASSUMPTION [ADVISORY]: The "interaction archetype" concept is load-bearing but undefined.**

The rubric generation, stopping criterion, and persona generation all branch on "interaction archetype." The proposal lists it as an IR field but never defines what the archetypes are, how many exist, or how they map to the 22 skills. This is not a blocker for the pilot (3 skills), but if the archetype taxonomy is wrong, the rubric auto-generation will produce systematically wrong rubrics for entire classes of skills. Worth defining before the pilot, not after.

---

**6. RISK [ADVISORY]: The 3-model separation (Claude/Gemini/GPT) assumes model role assignments are stable, but the config shows Gemini is already used for both persona and refine roles.**

Verified: `persona_model_map` assigns `staff` and `pm` to `gemini-3.1-pro`, and `refine_rotation` includes `gemini-3.1-pro`. The proposal assigns Gemini to the Persona role. If a skill being simulated uses Gemini in its own execution path (e.g., a skill that calls `refine`), the "3-model separation" breaks — Gemini is simultaneously playing the user and potentially being called by the skill under test. This is a contamination risk for skills that invoke the refine pipeline. Not a blocker for the 3-skill pilot (/explore, /investigate, /plan), but needs to be addressed before generalizing.

---

**7. OVER-ENGINEERED [ADVISORY]: The OCEAN personality trait layer adds complexity without a clear failure mode it addresses.**

The existing eval_intake.py persona system works by encoding *behavioral* instructions directly (verbosity, rejection patterns, answer length). OCEAN traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) are a psychological model that must be translated into behavioral instructions before they affect simulation output. That translation is itself an LLM call with no ground truth. The 8 hidden-state fields already cover the behavioral dimensions that matter (verbosity, cooperativeness, patience). OCEAN adds a second layer of abstraction that must be correctly translated to produce the same behavioral outputs the simpler model already captures. Drop OCEAN from the pilot; add it only if the 8-field model demonstrably misses a failure class.

---

**8. UNDER-ENGINEERED [MATERIAL] [COST:TRIVIAL]: No output format or persistence layer is specified for V2 simulation results.**

eval_intake.py writes structured markdown summaries to `tasks/eval-results/` with a defined schema (persona, turns, sufficiency, average, pass, hidden_truth_surfaced). The V2 proposal adds `--mode persona-sim` to /simulate but specifies no output format, no storage location, and no schema for the IR, persona records, or judge scores. Without this, V2 results cannot be compared across runs, cannot be diffed against V1 baselines, and cannot feed the convergence criterion. The existing eval_intake.py output schema is a natural starting point. **Fix cost: TRIVIAL** — specify that V2 writes to `tasks/sim-results/` using the same schema as eval_intake.py's summary, extended with IR fields and persona hidden-state.

---

## Concessions

1. **The problem is real and the evidence is strong.** The +2.67 delta (4.7 vs 2.0 avg) from eval_intake.py is EVIDENCED and the existing infrastructure (llm_client.py, 3-model separation, persona cards, rubric) is verified to exist. The proposal is building on a working foundation, not speculating.

2. **The non-goals are well-scoped.** Explicitly excluding all 22 skills, production trace distillation, and live canaries keeps the pilot tractable. The 3-skill pilot is the right size to validate the compiler before committing to generalization.

3. **The 3-agent architecture is validated by the existing system.** eval_intake.py already implements Executor/Persona/Judge with the same model assignments the proposal specifies. V2 is generalizing a pattern that demonstrably works, not inventing one.

---

## Verdict

**REVISE** — Three material issues must be resolved before build: (1) the IR extraction reliability problem needs either a structured SKILL.md schema or an explicit human-validation gate in the pilot, (2) the success criterion for score comparison is circular and needs to be restated as rubric-dimension overlap, and (3) anchor personas should be the existing 5 verified eval-personas cards rather than newly generated ones, or the pilot loses its regression baseline. None of these require large implementation work — the proposal is architecturally sound and the infrastructure is real — but as written, the success criteria cannot be evaluated and the pilot could pass all its gates while producing meaningless scores.

---

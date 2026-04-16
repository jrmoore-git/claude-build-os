---
topic: simulate-v2
created: 2026-04-15
---
# /simulate V2 — Skill Compiler Simulator

## Problem
Validating that a BuildOS skill works well for real users requires either manual usage over days ("use it for 3 days and come back") or bespoke manual simulation setup (eval_intake.py: 17 rounds, 5 personas, 3-model separation, custom rubric — days of setup per skill). V1 /simulate handles structural validation (smoke-test) and basic quality-eval (single scenario, single judge), but doesn't test the interactive user experience across persona types.

The gap: cross-model persona simulation catches real issues (explore intake found and fixed dozens of protocol problems across 5 validation passes), but it required bespoke setup per skill. We need that process to generalize across 22+ BuildOS skills with minimal per-skill configuration.

## Proposed Approach
Build a Skill Compiler Simulator that compiles each SKILL.md into an Interaction Representation (IR), then simulates users with hidden state — not free-form roleplay. Five components:

1. **Skill Compiler** — parses SKILL.md into structured IR (objective, decision points, ask nodes, success/failure criteria, interaction archetype)
2. **Persona Generator** — creates users with 8 hidden-state fields (goal, knowledge, urgency, patience, trust, cooperativeness, verbosity, ambiguity tolerance) + OCEAN personality traits. Hybrid: 3-5 anchor personas for regression + generated personas for breadth.
3. **3-Agent Simulation Loop** — Executor (Claude, runs skill) + Persona (Gemini, plays user from hidden state only — does NOT see procedure/rubric) + Judge (GPT, scores after completion)
4. **Rubric Generation** — auto-generates scoring rubric from IR + interaction archetype. 3 universal dimensions + archetype-specific dimensions.
5. **Convergence + Stopping** — stops when new runs stop surfacing new failure classes, not when average score stabilizes.

Adds `--mode persona-sim` to existing /simulate. V1 modes unchanged.

**Non-goals:** Not replacing V1. Not simulating all 22 skills — ~8-10 interactive skills benefit, procedural skills stay on V1 smoke-test. Not building production trace distillation yet (V3). Not building live canaries.

### Simplest Version
Compiler pilot on 3 skills (one intake, one diagnosis, one planning): /explore, /investigate, /plan. For each: compile IR, validate IR with separate model, generate 3 anchor + 5 generated personas, run 10 simulations, score with cross-model judge. Success: compiler extracts accurate IR, anchor personas produce consistent scores (variance < 0.5), generated personas surface at least 2 failure modes not found by anchors, /explore V2 results within 0.5 points of eval_intake.py on same rubric dimensions.

### Current System Failures
1. **V1 quality-eval is shallow** (2026-04-15): Single scenario, single agent, single judge. No persona diversity, no hidden state, no multi-turn consistency. Catches structural bugs but not interactive experience failures.
2. **Manual simulation doesn't generalize** (2026-04-11): eval_intake.py works for /explore but required days of bespoke setup (persona cards, rubric, simulation prompt, 17 rounds). Cannot repeat for 22 skills.
3. **"Use it for 3 days" is the only real validation** (ongoing): Skills get shipped with structural tests but no user-experience validation. Issues surface through anecdotal feedback days later.

### Operational Context
- debate.py runs 5-10 times/day, 311 entries in debate-log.jsonl
- V1 /simulate runs: 4 total (3 smoke-test + 1 quality-eval), all passing
- eval_intake.py infrastructure exists: 5 persona cards, 1 rubric, 1 simulation prompt, llm_client.py
- LiteLLM proxy running with Claude Opus, GPT-5.4, Gemini 3.1 Pro available
- Cost per full V2 run (10 skills): ~4-5.5M tokens, comparable to one /challenge --deep pipeline

### Baseline Performance
- **V1 smoke-test:** Catches bash block failures, missing file paths, placeholder detection. 100% structural coverage, 0% interactive experience coverage.
- **V1 quality-eval:** Single scenario eval via debate.py review. Catches gross quality failures. No persona diversity, no hidden state tracking, no multi-turn consistency measurement.
- **Manual eval_intake.py:** 5 personas, 3-model separation, 17 rounds. Scores: Register 4.2/5, Flow 4.8/5. Delta proof: with intake 4.7/5 avg, without 2.0/5 avg (+2.67). Setup cost: ~2 days per skill. Not generalizable.

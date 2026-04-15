---
topic: simulate-skill
created: 2026-04-14
---
# /simulate — Zero-Config Skill Simulation

## Problem
BuildOS has 21 skills and a cross-model debate engine, but no way to validate skills without real usage. Over 72+ hours, 10+ ad-hoc simulations were manually orchestrated — persona tests, smoke-tests, delta proofs, consensus loops. eval_intake.py exists but is hardcoded to explore intake. The default recommendation ("just use it on real work") defers validation indefinitely and makes the user the bug-finder.

## Proposed Approach
A SKILL.md that reads another skill's SKILL.md, auto-generates test scenarios, spawns agents to simulate execution, and produces a scored report. Two modes in V1:

1. **Smoke-test** — extract and run fenced bash blocks, check file paths, report pass/fail per command
2. **Quality eval** — generate realistic scenario, one agent follows the procedure, another plays user, third judges output via debate.py review

Key design: the simulation never invokes the target skill via the Skill tool. An agent reads the SKILL.md and follows its procedure — because skills are prompt documents, an agent following the procedure IS the skill running.

Non-goals: adversarial mode (V2), delta proof (V3), consensus (V3), hook-triggered auto-sim, Python orchestrator.

## Simplest Version
A SKILL.md with two modes (smoke-test + quality eval) that can be invoked as `/simulate /elevate` and produce a structured report without any configuration. No new Python scripts — uses existing debate.py review and Agent tool.

### Current System Failures
1. /elevate had a BSD mktemp bug that only surfaced during ad-hoc agent-spawned audit (2026-04-14). Static analysis produced 3 false positives alongside the 1 real bug.
2. eval_intake.py found 10 protocol amendments and 22 skill refinements across 6+ simulation runs — none would have been found through "just use it" advice.
3. 10 distinct simulation instances were manually orchestrated over 72+ hours, each requiring custom setup — no reusable framework.

### Operational Context
- debate.py runs ~5-10 times/day, 95+ entries in debate-log.jsonl
- eval_intake.py exists as a 485-line Python harness: Claude interviewer + Gemini persona + GPT judge turn loop
- 21 skills in .claude/skills/, most with zero exercise beyond authoring
- Agent tool available for spawning subagents with model parameter

### Baseline Performance
No existing generalized simulation system. eval_intake.py is the closest analogue but is hardcoded to explore intake. All other simulations were manual one-offs with no reusable framework.

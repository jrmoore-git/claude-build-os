---
debate_id: simulate-skill-findings
created: 2026-04-14T21:13:41-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# simulate-skill-findings — Challenger Reviews

## Challenger A — Challenges
I now have a solid understanding of the codebase. Let me formulate my review.

## Challenges

1. **RISK** [MATERIAL] [COST:MEDIUM]: **Quality eval mode is eval_intake.py reimplemented in prompt-space with less control.** The existing `eval_intake.py` is a 485-line Python harness with explicit turn loops, sufficiency detection, structured JSON judge output, parallel persona execution, and error handling per turn. The proposal's quality eval mode — "one agent follows the procedure, another plays user, third judges output via debate.py review" — recreates this same interviewer↔persona↔judge architecture but delegates orchestration to the Agent tool and natural language instructions in a SKILL.md. This means: no structured turn limits (eval_intake.py has `--max-turns`), no sufficiency detection (`SUFFICIENCY_REACHED` parsing), no structured scoring (JSON rubric output), no parallel execution (`ThreadPoolExecutor`), and no error recovery per turn (`LLMError` handling). The proposal explicitly says "No new Python scripts" but the existing Python harness exists precisely because prompt-only orchestration lacks these controls. The risk is that quality eval produces unreliable, unstructured results that can't be compared across runs — which is the exact problem eval_intake.py was built to solve for intake.

2. **ASSUMPTION** [MATERIAL] [COST:SMALL]: **"An agent following the procedure IS the skill running" is true for conversational skills but false for tool-using skills.** Skills that invoke `debate.py`, run bash commands, write files, or call external APIs cannot be faithfully simulated by an agent reading the SKILL.md and "following the procedure" in a sandboxed context. The proposal's smoke-test mode (extract and run fenced bash blocks) partially addresses this for bash, but the quality eval mode's core premise breaks down for any skill whose value comes from tool side-effects rather than conversational output. With 21 skills and 16 fenced bash blocks found across them, this isn't a corner case — it's likely the majority of skills.

3. **ALTERNATIVE** [ADVISORY]: **Generalize eval_intake.py instead of building a parallel system.** eval_intake.py already has the exact architecture needed: configurable interviewer/persona/judge models, turn loops, structured scoring, parallel execution. The hardcoded parts are: (a) the system prompts reference intake protocol, (b) persona files are in `config/eval-personas/`, (c) the rubric is intake-specific. Extracting these into parameters would yield a general-purpose skill simulation harness in ~100 lines of refactoring, reusing 400+ lines of battle-tested orchestration code. The proposal dismisses Python orchestration as a non-goal but doesn't explain why the existing Python orchestration shouldn't be the foundation.

4. **UNDER-ENGINEERED** [MATERIAL] [COST:SMALL]: **No cost guardrails for a tool that spawns 3+ LLM agents per invocation.** The quality eval mode spawns at minimum 3 agents (executor, user-simulator, judge), each making multiple LLM calls. With the Agent tool, there's no token budget, no turn limit, and no cost ceiling. A `/simulate --all` across 21 skills could easily trigger 60+ agent invocations. The proposal mentions no cost estimation, no dry-run mode, and no per-simulation budget. Given that debate.py runs 5-10 times/day (EVIDENCED from proposal), adding uncapped simulation runs on top could meaningfully increase spend.

5. **RISK** [ADVISORY]: **Smoke-test mode's "extract and run fenced bash blocks" is fragile for blocks with prerequisites.** Many bash blocks in skills likely assume prior steps have run (files exist, env vars set, services running). Running them in isolation will produce false failures. This is acknowledged implicitly by the proposal's mention of "check file paths" but the failure mode is noisy false negatives that erode trust in the tool.

6. **OVER-ENGINEERED** [ADVISORY]: **Three-agent quality eval for V1 when single-agent + debate.py review would suffice.** The proposal could achieve 80% of the value with: one agent follows the skill procedure on a generated scenario, then `debate.py review` evaluates the output. The user-simulator agent adds complexity (who generates the user persona? how realistic is it?) without clear V1 value over a static test scenario.

## Concessions

1. **The problem is real and well-evidenced.** The mktemp bug, the 10 protocol amendments from eval_intake.py, and the 72+ hours of manual simulation are concrete evidence that skills need automated validation. The status quo of "just use it" is genuinely inadequate for 21 skills.

2. **SKILL.md-as-implementation is architecturally consistent.** Making the simulation tool a skill that reads other skills is the right abstraction level for this system — it follows the existing pattern and doesn't introduce new infrastructure.

3. **The V1 scope is disciplined.** Explicitly deferring adversarial mode, delta proof, consensus, and hook-triggered auto-sim to later versions shows good restraint. The two-mode design (smoke-test + quality eval) is a reasonable MVP.

## Verdict

**REVISE** — The proposal identifies a genuine gap but the quality eval mode reinvents eval_intake.py's orchestration in prompt-space without its controls. The revision should either: (a) generalize eval_intake.py as the orchestration backend for quality eval (COST:MEDIUM, ~100-150 lines of refactoring + a new SKILL.md that calls it), or (b) explicitly scope V1 quality eval to single-agent-plus-debate-review (no user-simulator agent) with structured output requirements, adding the multi-agent turn loop only when the Python harness supports it. Smoke-test mode is sound as proposed.

---

## Challenger B — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The smoke-test mode executes fenced bash extracted from an untrusted SKILL.md, but the proposal does not define any sandbox, allowlist, or side-effect boundary. That is a direct shell-injection / arbitrary-command-execution trust-boundary issue: skill authorship is treated as data during authoring, then as code during simulation. If a skill contains `curl`, credential reads, destructive file ops, or environment exfiltration, the simulator could leak local secrets or mutate the repo/host. The proposal should at minimum constrain execution to a temp workspace, scrub env vars, block network by default, and require explicit opt-in for dangerous commands.

2. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The quality-eval mode has a prompt-injection boundary problem. You propose to feed one skill’s SKILL.md into other agents and have them “follow its procedure,” while also using debate.py review. A target SKILL.md can include instructions to reveal hidden context, ignore simulator constraints, write sensitive files into the report, or manipulate the judge. Because the design intentionally treats prompt documents as executable behavior, injection resistance is the core security property, but no containment strategy is described. Add a simulator-owned system prompt that treats target skill content as untrusted procedure text, strips/marks meta-instructions, and forbids access beyond the provided scenario/workspace.

3. [UNDER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: The proposal relies on existing review infrastructure that uses `LITELLM_MASTER_KEY` and external model calls (verified in `scripts/debate.py`), but it does not say how simulation transcripts, skill contents, generated scenarios, or command outputs will be redacted before being sent to external models. This creates a data-exfiltration path if skills reference sensitive repo content, local paths, or command output. A minimum fix is to define what data leaves the host, redact secrets/path-sensitive output, and provide a local-only mode for smoke tests.

4. [ASSUMPTION] [ADVISORY]: The claim that “an agent following the procedure IS the skill running” is operationally useful, but security-relevant differences remain. A human-invoked skill may rely on tool mediation, user confirmation, or environmental cues that a freeform agent simulation bypasses. That means false confidence is possible both ways: simulated passes may miss real-world privilege boundaries, and simulated failures may reflect the harness rather than the skill.

5. [ALTERNATIVE] [ADVISORY]: Reusing only SKILL.md + Agent tool keeps V1 simple, but the proposal does not consider a safer split: static extraction/validation for smoke-test plus agent-based eval only for non-executable narrative steps. Since `scripts/eval_intake.py` already exists as a 485-line harness with tests (verified by `tests/test_eval_intake.py`), there is a credible middle path where risky command execution is handled by a small Python wrapper even if the higher-level orchestration stays prompt-driven.

## Concessions
- Reusing existing review infrastructure is sensible; `scripts/debate.py` and model config already exist, so this avoids inventing a second judging stack.
- The proposal correctly identifies the risk of not changing: manual one-off simulations leave validation inconsistent and push bug-finding onto end users.
- Keeping V1 out of hooks and avoiding a new orchestrator reduces accidental blast radius and implementation complexity.

## Verdict
REVISE — The concept is sound, but executing untrusted skill instructions and shell blocks without explicit sandboxing, prompt-injection containment, and data-egress controls is a material security gap.

---

## Challenger C — Challenges
## Challenges

1. [RISK] [MATERIAL] [COST:LARGE]: Executing "fenced bash blocks" extracted from SKILL.md directly on the host is a massive safety hazard. Skills are documentation; their bash blocks often contain placeholder variables (`<your_file>`, `rm -rf $DIR`) or destructive commands meant to be run in specific contexts. Blindly extracting and executing these in a "smoke-test" without a mocked or containerized sandbox will inevitably cause host damage. 

2. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal assumes "an agent reading the SKILL.md and following its procedure IS the skill running." This ignores crucial operational realities: when invoked natively, the host system injects specific system prompts, limits, and tool execution boundaries. An agent reading a file inside a simulation loop will have a different context window and instruction hierarchy, meaning passing the simulation does not guarantee passing in reality.

3. [OVER-ENGINEERED] [MATERIAL] [COST:MEDIUM]: Orchestrating a three-agent interaction (actor, simulated user, judge) entirely through markdown prompt instructions via the Agent tool is extremely brittle. It forces a complex state machine into prompt space when a simple Python script (like the EVIDENCED 485-line `eval_intake.py`) handles this control flow much more reliably and explicitly. 

## Concessions
1. Correctly identifies a severe gap in the development loop—relying on "just use it" for 21 skills (EVIDENCED) guarantees broken skills will rot until a user hits them.
2. The proposal to reuse the existing `debate.py` review system for evaluation correctly prevents building a redundant evaluation metric.
3. Explicitly deferring adversarial mode and delta proofs (V3) shows good scope discipline.

## Verdict
REVISE to remove the hazardous raw bash execution in the smoke-test mode and to shift the 3-agent orchestration out of purely prompt-based execution into a structured Python runner.

---

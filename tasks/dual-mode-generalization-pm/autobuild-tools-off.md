---
debate_id: autobuild-tools-off
created: 2026-04-17T14:50:55-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# autobuild-tools-off — Challenger Reviews

## Challenger A (pm) — Challenges
## Challenges

1. [ASSUMPTION] [MATERIAL] [COST:MEDIUM]: The proposal assumes an autonomous build-test-iterate loop can be reliably implemented purely via ~80 lines of markdown instructions (prompt engineering) within `plan/SKILL.md`. In practice, LLM agents often hallucinate test execution, skip steps, or prematurely declare success when trapped in meta-instruction loops. A programmatic orchestrator is usually required for reliable autonomous looping. 
*Quantitative context*: The 60-80 lines estimate is [ESTIMATED] (assumes existing Claude Code looping behavior is robust enough to handle the abstraction).

2. [RISK] [MATERIAL] [COST:SMALL]: Context window exhaustion. A single session handling planning, sequential implementation across multiple files, testing, 3-strike iteration loops, and review will rapidly bloat the context window. This leads to degraded logic and high costs. The proposal needs a mechanism to clear context or checkpoint between major build steps if it remains in a single thread.
*Quantitative context*: "could consume significant context" is [SPECULATIVE] (needs empirical data on average context size after a 3-step build with test failures).

3. [OVER-ENGINEERED] [ADVISORY]: Tying the decompose gate's "worktree-isolated agents" into this MVP adds unnecessary complexity. Sequential implementation on the main branch is a vastly simpler starting point to validate the core `--build` loop before tackling concurrent autonomous agent orchestration.

## Concessions
1. Exceptional reuse of existing primitives (escalation protocol, lessons.md, 3-tier decision classification).
2. The `--build` flag makes this strictly opt-in, posing zero adoption friction to existing workflows.
3. Defining file boundaries (`surfaces_affected`) upfront to catch scope creep is a highly effective containment strategy.

## Verdict
APPROVE. The proposed implementation is so lightweight (prompt additions rather than new tooling) that it is worth testing immediately, provided the team monitors for context exhaustion and prompt-compliance failures during the iteration loops.

---

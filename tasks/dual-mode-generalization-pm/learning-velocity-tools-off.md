---
debate_id: learning-velocity-tools-off
created: 2026-04-17T14:51:00-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# learning-velocity-tools-off — Challenger Reviews

## Challenger A (pm) — Challenges
## Challenges
1. [ALTERNATIVE] [MATERIAL] [COST:SMALL]: The proposed "Simplest Version" builds the wrong thing first. Prioritizing git log metrics (~15 lines) over verification completely ignores the concrete, [EVIDENCED] failure: 3 out of 4 active lessons were found to be stale or wrong. Metrics will not prevent stale lessons from poisoning the context window; the verification and pruning checks will. The simplest version should surface staleness/redundancy, not just velocity metrics.
2. [RISK] [MATERIAL] [COST:SMALL]: The pruning heuristic for hooks ("has this fired in the last 30 days?") fails to distinguish between high-frequency linting hooks and low-frequency/high-severity safety guardrails. Flagging a catastrophic-failure hook for pruning simply because the team successfully avoided the catastrophic error for a month introduces severe regression risk. Hook pruning flags need a "guardrail" bypass or severity awareness.
3. [ASSUMPTION] [ADVISORY]: Adding 2-3 cross-model panel calls to `/healthcheck` will add 60-90 seconds of latency ([EVIDENCED]: ~30s each). While acceptable for a weekly task, if `/healthcheck` is ever moved into a synchronous CI blocking path or daily pre-commit, this latency will cause adoption friction.

## Concessions
1. Accurately identifies a critical flaw in LLM agent systems: governance accumulates indefinitely and rots, poisoning context windows.
2. Excellent restraint on scope by explicitly rejecting dashboards, new governance files, and automated deletions in favor of surfacing flags.
3. Reuses existing capabilities (`/healthcheck`, `/investigate`) rather than building an entirely new lifecycle management subsystem.

## Verdict
APPROVE. The proposal elegantly solves governance bloat with right-sized tooling, provided the "simplest version" is reordered to prioritize removing stale lessons over calculating velocity metrics.

---

---
debate_id: autobuild-tools-off
created: 2026-04-17T14:42:26-0700
mapping:
  A: claude-opus-4-7
personas:
  A: architect
---
# autobuild-tools-off — Challenger Reviews

## Challenger A (architect) — Challenges
## Challenges

1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: Scope containment is asserted to "just work" via escalation trigger #4, but there's no mechanism described for actually intercepting edits against `surfaces_affected`. Standard Edit/Write tools don't check a file allowlist. Either the agent self-polices (unreliable — the whole point of autobuild is reducing reliance on in-loop judgment for mechanical checks), or a hook enforces it. Proposal explicitly says "No new hook needed" — this is the gap. A PreToolUse hook checking Edit/Write paths against the plan's `surfaces_affected` is ~30 lines and is the difference between "escalation protocol covers it" (aspirational) and "scope violations are structurally impossible" (actual).

2. [RISK] [MATERIAL] [COST:SMALL]: The 3-attempt iteration limit is per-step, but there's no described behavior for *what state the repo is in* when attempt 3 fails and escalation fires. Partial edits from failed attempts? Reverted? Left for human inspection? Without a defined rollback/checkpoint per step (e.g., git commit per step, or stash on failure), the human arriving at an escalation sees a half-broken tree and has to reconstruct what attempts did what. Git-commit-per-step or a pre-step stash is trivial and makes escalation recoverable.

3. [ASSUMPTION] [ADVISORY]: "Lessons.md may be sufficient for a solo dev" — SPECULATIVE. No data on how often current lessons.md entries would have prevented a recurring build-phase mistake. The proposal correctly flags this as "wait for signal," which is the right posture, but the claim that lessons.md *is currently* loaded at the right granularity for build-phase agents (not just session start) deserves verification. If the build agent is a sub-invocation, does it inherit the `/start` context?

4. [RISK] [ADVISORY]: Token/context exhaustion (Why Not #3) is noted but not mitigated. For multi-step plans, the build agent accumulates context from every prior step's edits and test output. No plan for context handoff between steps (e.g., summarize-and-continue, or fresh sub-agent per step with plan as only carried state). SPECULATIVE on frequency — depends on plan sizes in practice — but worth naming a threshold ("if plan has >N steps, build each step in fresh sub-agent") rather than discovering it mid-run.

5. [ALTERNATIVE] [ADVISORY]: The parallel-track behavior ("spawn worktree-isolated agents" for decomposed tracks) is mentioned in one line but is the single highest-complexity behavior in the whole proposal. Coordinating N worktree agents, merging results, handling partial failures across tracks, and re-running the full test suite on the merged result is its own subsystem. Consider scoping v1 to sequential-only and treating parallel autobuild as a follow-up — the proposal's "~60-80 lines" estimate almost certainly excludes parallel orchestration.

## Concessions

1. Building on Build OS itself as the first test bed is correct — every PR is human-reviewed, so the blast radius is bounded to wasted compute, not bad merges.
2. Reusing the existing 3-tier decision classification and 7 escalation triggers rather than inventing build-phase-specific ones is the right call; it keeps the mental model consistent.
3. Deferring structured learning infrastructure until there's signal that lessons.md is insufficient avoids gstack's apparent over-investment in machinery before demand.

## Verdict

REVISE — the core design is sound and well-situated in existing infrastructure, but two MATERIAL gaps (scope-enforcement hook, per-step checkpoint/rollback) are both SMALL-cost fixes that convert "autobuild with aspirational guardrails" into "autobuild with structural guardrails." Address #1 and #2 as build conditions; #5 (parallel scoping) should be explicitly deferred rather than silently included in the 60-80 line estimate.

---

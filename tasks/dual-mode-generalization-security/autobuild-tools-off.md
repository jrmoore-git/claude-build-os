---
debate_id: autobuild-tools-off
created: 2026-04-17T14:50:43-0700
mapping:
  A: gpt-5.4
personas:
  A: security
---
# autobuild-tools-off — Challenger Reviews

## Challenger A (security) — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposal treats plan artifacts and `verification_commands` as trusted inputs, but they are effectively instruction-bearing data that may originate from a model-generated plan or be edited by a lower-trust actor. That creates an injection boundary: arbitrary shell commands in `verification_commands`, unsafe file targets in `surfaces_affected`, and prompt-injection-style plan text could steer the build agent into exfiltration, destructive commands, or out-of-scope edits. At minimum, the build phase needs explicit trust rules: who/what may author the plan, whether commands are allowlisted or require approval, and how paths are normalized and constrained to the repo root.

2. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: “Building it on one repo ... is zero-risk” is not sound from a security perspective. Even with human PR review, the autonomous build loop would execute code and tests before review, which is exactly where secrets can leak via test output, network calls, telemetry, or malicious postinstall/build scripts. Human review mitigates merge risk, not execution risk. The proposal needs a runtime sandbox posture for build/test: e.g., no prod credentials, restricted network, scrubbed env, and explicit handling for repositories with secret-bearing test fixtures or external integrations.

3. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The proposal assumes existing escalation trigger #4 is sufficient to contain scope growth, but “check edits against `surfaces_affected`” is described only at the policy level. Without a concrete enforcement mechanism, an agent can still modify non-listed files before escalation or via indirect effects (generated files, config changes, lockfiles). If scope containment is a key safety property, it should be enforced pre-write or at least diff-checked before test/review with automatic rollback/pause.

4. [UNDER-ENGINEERED] [ADVISORY]: Parallel worktree-isolated agents reduce file collision risk, but the proposal does not say how secrets/config are partitioned across worktrees or whether each agent inherits the full environment. If they do, parallelization increases the attack surface for accidental secret exposure through logs or subprocesses.

5. [ASSUMPTION] [ADVISORY]: Reusing `tasks/lessons.md` as “self-learning” may be operationally sufficient, but it also becomes another untrusted instruction source unless curated. If lessons can include shell snippets, URLs, or normative “always do X” guidance, they can bias the agent toward unsafe behavior. Treat lessons as advisory context, not executable authority.

6. [ALTERNATIVE] [ADVISORY]: A narrower first version—autonomous code edits with human-approved test command execution, or autonomous execution only for an allowlisted command set—was not considered. That would reduce shell-injection and secret-exposure risk while still closing much of the manual gap.

## Concessions
- Reusing the existing approval gate and escalation protocol is a good safety baseline.
- The proposal correctly identifies the main risk of not changing: the highest-friction manual step remains the build-test-iterate loop.
- Keeping scope limited to one skill and existing primitives avoids unnecessary new infrastructure.

## Verdict
REVISE — the overall direction is reasonable, but the current proposal lacks explicit trust-boundary and execution-sandbox controls for model-authored plans, shell commands, and secret-bearing test environments.

---

---
debate_id: managed-agents-dispatch-findings
created: 2026-04-10T12:37:52-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# managed-agents-dispatch-findings — Challenger Reviews

## Challenger A — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL]**: The proposal assumes refine rounds can be cleanly partitioned by model provider — "Refine legs are Claude-only (3 of 6 rounds) — these could run on MA." However, the verified `refine_rotation` config is `["gemini-3.1-pro", "gpt-5.4", "claude-opus-4-6"]`, meaning each round's model is determined by `models[i % len(models)]` (line 2000). In a 6-round refine, rounds 2 and 5 are Claude. The other 4 rounds are Gemini/GPT. Offloading only the Claude rounds to Managed Agents means the orchestrator must still run locally for the non-Claude rounds, and each round depends on the previous round's output (sequential chain). You can't dispatch Claude rounds independently — you'd need to shuttle intermediate state back and forth. The proposal's "optionally offload refine/consolidation legs" understates this coupling. The simplest version should target consolidation (which is a single Claude-only call at `_consolidate_challenges`, line 1352) rather than refine rounds.

2. **RISK [MATERIAL]**: The entire LLM call path routes through LiteLLM at `localhost:4000` (verified in `llm_client.py` lines 1-10). Managed Agents would bypass this proxy entirely — calls go directly to Anthropic's API. This means: (a) cost tracking via LiteLLM is lost for MA-dispatched work, (b) any LiteLLM-specific retry/timeout logic in `llm_client.py` (verified: exponential backoff at line 150) doesn't apply, (c) model aliasing configured in LiteLLM won't work. The proposal doesn't address how MA-dispatched work integrates with the existing observability and routing layer. This is a real operational gap, not a theoretical one.

3. **UNDER-ENGINEERED [MATERIAL]**: The proposal has no error handling or fallback strategy. What happens when a Managed Agent session fails mid-refine-round? The refine loop (line 1999-2097) has truncation detection, retry logic, and delta logging. A `managed_agent.py` client that just "creates a session, polls for results, returns output" loses all of this. The proposal needs to specify: does failure fall back to local execution? Is the round retried? How does partial failure in a 6-round sequential chain get handled?

4. **RISK [ADVISORY]**: debate.py is 2,883 lines with zero test coverage (verified). Adding a `--use-ma` flag that conditionally changes execution paths in an untested 2.9K-line file increases the risk of subtle regressions. The proposal doesn't mention testing strategy for the integration point.

5. **ALTERNATIVE [ADVISORY]**: Consolidation (`_consolidate_challenges`, line 1352) is a better first integration target than refine. It's a single, stateless, Claude-compatible LLM call with no sequential dependencies. It would validate the MA API, cost model, and failure modes with far less orchestration complexity. The proposal mentions consolidation as a candidate but leads with refine, which is the harder problem.

6. **OVER-ENGINEERED [ADVISORY]**: Phase 2's "routing logic that decides local vs. cloud execution" and "Agent Teams for parallel track orchestration" is speculative architecture for a system that doesn't exist yet. Phase 1 will reveal whether MA is even viable (latency, cost, reliability). Designing the orchestration layer before Phase 1 data exists risks building the wrong abstraction. The proposal acknowledges this somewhat by phasing, but the Phase 2 description is too concrete for something that should be shaped by Phase 1 learnings.

## Concessions

1. **The phased approach is correct.** Starting with a thin client (`managed_agent.py`) before building orchestration is the right sequencing. Ship-and-learn before abstracting.

2. **Scoping Jarvis persistence out is the right call.** Keeping always-on agent concerns in the Jarvis repo avoids polluting BuildOS with application-specific lifecycle management.

3. **The problem statement is real.** 15-30 minute local session blocking for debate runs is a genuine workflow bottleneck, and there's no existing cloud dispatch primitive. The status quo has a real cost in developer time.

## Verdict

**REVISE**: The sequential dependency between refine rounds makes them a poor first integration target — lead with consolidation as the simplest version, and address the LiteLLM bypass gap (cost tracking, retry parity, fallback on failure) before the design is finalized.

---

## Challenger B — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL]: The proposal introduces a new trust boundary — sending proposal/judgment/refinement content from local BuildOS into a third-party Managed Agents service — but it does not define any data-classification gate, redaction policy, or approval rule for what may be offloaded. Today `scripts/debate.py` reads arbitrary local files/strings and loads secrets from `.env` into process environment (`scripts/debate.py` lines 81-125), so a naïve “dispatch any Claude-only task” client could exfiltrate sensitive proposal contents or accidentally include secret-bearing context to an external service. This materially changes the risk profile and needs explicit controls before rollout.

2. [UNDER-ENGINEERED] [MATERIAL]: The managed-agent client is proposed to “return structured output,” but there is no validation plan for treating remote agent output as untrusted data before feeding it back into local orchestration. That creates prompt-injection and output-injection risk in both directions: hostile/poisoned task content sent to MA, and MA-produced text later consumed by `debate.py` or other automation. At minimum, the design should specify strict schema validation, size limits, and a rule that returned content is data only — never executable instructions, shell fragments, or file paths to be acted on automatically.

3. [ASSUMPTION] [MATERIAL]: The proposal assumes refine/consolidation legs are safe to offload because they are “Claude-only,” but “model family” is not a security boundary. The real boundary is local machine/process vs external managed service. Without verifying API auth model, tenancy isolation, retention defaults, and whether prompts/results are stored by the provider, this assumption is unverified and materially affects whether offloading is acceptable.

4. [UNDER-ENGINEERED] [MATERIAL]: Credential handling is unspecified. `debate.py` already depends on environment-loaded secrets (`LITELLM_MASTER_KEY` is referenced in the script), and the new `managed_agent.py` will necessarily add another API credential. The proposal does not say how MA credentials are stored, scoped, rotated, prevented from leaking into logs/errors, or isolated from subprocess environments. Since `debate.py` also uses `subprocess`, failure paths and debug output need explicit review so new secrets are not printed or inherited broadly.

5. [UNDER-ENGINEERED] [ADVISORY]: There is no mention of result isolation or access control for “dispatch from any machine, poll for results.” If job IDs are guessable or not bound to the submitting identity/project, a lower-trust actor could poll another user’s outputs. Even for a first milestone, the design should state that result retrieval must be authenticated and scoped per user/project.

6. [UNDER-ENGINEERED] [ADVISORY]: `scripts/debate.py` currently has no detected test coverage (`check_test_coverage` reports none), so introducing networked remote execution without contract tests increases the chance of silent failure and unsafe fallback behavior. This is not by itself a reason to reject, but it does change the recommended next step: add tests for auth/header handling, response validation, timeout/retry behavior, and “do not execute returned text” guarantees before broad integration.

## Concessions
- The proposal correctly limits scope by deferring “persistent Jarvis agent” work; that avoids mixing always-on autonomy with a simpler batch dispatch feature.
- Starting with an explicit `--use-ma` opt-in on `debate.py` is a good containment strategy versus changing all execution paths at once.
- Phase 1’s goal of validating API/failure modes on real workloads is appropriate for a greenfield capability.

## Verdict
REVISE — the architecture is directionally reasonable, but it needs explicit controls for data egress, credential handling, and untrusted-output validation before managed-agent dispatch is safe to recommend.

---

## Challenger C — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL]: The proposal assumes that offloaded cloud agents can perform `debate.py` tasks (like document refinement) without direct access to the user's local filesystem. Because refinement inherently involves reading and modifying local workspace files, running this remotely will fail unless bidirectional file synchronization is also built—a massive, unstated scope increase.
2. [OVER-ENGINEERED] [MATERIAL]: Building a hybrid orchestration layer and async polling API integration for a process that runs ~2-5 times/day (EVIDENCED: "debate.py runs ~2-5 times/day") and takes 15-30 minutes (EVIDENCED: "consume 15-30 minutes of local session time") is heavily unjustified. The concrete failure (blocked local CLI sessions) can be trivially solved by running the script in the background (`nohup`, `&`, or a simple wrapper script) without introducing distributed system complexity.
3. [PRIORITY] [ADVISORY]: The proposal explicitly notes "No existing failures per se". Displacing priority for greenfield external API integration to solve a mild terminal-blocking inconvenience shouldn't preempt work that addresses actual bugs or broken user flows.

## Concessions
1. Explicitly pushing the "always-on" persistent Jarvis agent out of scope correctly maintains appropriate repository boundaries.
2. Starting with a single `--use-ma` flag on existing scripts rather than forcing a systemic rewrite reduces initial adoption friction.
3. Correctly identifying that only Claude-only legs (refine/consolidation) are eligible for Managed Agents avoids breaking the multi-model requirements of the wider debate pipeline.

## Verdict
REJECT: The proposal over-engineers a distributed routing solution for a low-volume script (~2-5 runs/day, EVIDENCED: "debate.py runs ~2-5 times/day") while completely missing the critical architectural flaw of how remote cloud agents will read and modify the local filesystem.

---

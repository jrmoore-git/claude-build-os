---
debate_id: autobuild-findings
created: 2026-04-16T07:47:06-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# autobuild-findings — Challenger Reviews

## Challenger A — Challenges
I now have a solid picture of the existing infrastructure. Let me formulate my review.

## Challenges

1. **ASSUMPTION** [MATERIAL] [COST:SMALL]: **The "7 escalation triggers in workflow.md" may not exist as described.** The proposal references "escalation trigger #5" and "trigger #4" by number, and cites "workflow.md" as their home. However, `workflow.md` does not appear in the skills files, and neither "trigger #5", "trigger #4", "7 escalation", "3 failures", nor "scope is growing" appear as literal strings. The escalation concept exists (4 matches for "escalate"), but the numbered trigger system the proposal depends on for its core safety mechanism — particularly the 3-failure stop and scope-growth detection — may not be formalized in the way the proposal assumes. If the build phase's primary guardrail is an escalation protocol that doesn't exist in the described form, the safety model is hollow. **Fix:** Verify the actual escalation trigger definitions and either reference them correctly or define them as part of this proposal.

2. **UNDER-ENGINEERED** [MATERIAL] [COST:MEDIUM]: **No context window management strategy for long builds.** The proposal acknowledges "Long builds may hit context limits" in the "Why Not" section but offers no mitigation. A multi-step build with 3 retry attempts per step, followed by a full test suite, followed by `/review`, all in a single session, is exactly the scenario that exhausts context. The existing `--auto` pipeline (think → challenge → plan) is already substantial context. Adding build + test + iterate + review on top could easily exceed limits on any non-trivial task. The proposal needs either: (a) a checkpoint/resume mechanism, (b) a context budget that triggers early escalation, or (c) explicit guidance that autobuild is scoped to tasks under N steps. Without this, the mode will silently degrade on the tasks where it would be most valuable (complex multi-step builds).

3. **RISK** [MATERIAL] [COST:SMALL]: **The `surfaces_affected` check is a soft guardrail, not a hard one.** The proposal says "Files not in `surfaces_affected` trigger escalation trigger #4 (scope is growing)." But this is a SKILL.md instruction — it's a prompt-level constraint, not a programmatic enforcement. During an autonomous build loop where the agent is making edits, running tests, and iterating on failures, the agent is also the one responsible for checking its own compliance. There's no hook, no script, no pre-commit check that enforces the file scope boundary. In a manual build, the human provides this oversight. In autobuild, the agent is both executor and auditor. **Fix:** Add a lightweight post-step check (even a bash one-liner comparing `git diff --name-only` against the plan's file list) that runs after each build step and hard-stops on violations.

4. **RISK** [ADVISORY]: **Iteration quality degradation is acknowledged but not structurally addressed.** The proposal correctly identifies that "attempt 1 is informed, attempt 2 is a reasonable fix, attempt 3 is often flailing." The 3-strike limit is necessary but not sufficient — the failure mode isn't just "too many attempts" but "attempts that make things worse." A step that passes on attempt 3 with a hack that breaks step 5 is worse than stopping at attempt 1. The proposal could benefit from a regression check: after each retry, verify that previously-passing tests still pass.

5. **ALTERNATIVE** [ADVISORY]: **Step-level approval gates for initial rollout.** Rather than going from "fully manual build" to "fully autonomous build with escalation-only pauses," consider an intermediate mode where the agent implements each step and pauses for a quick human confirmation before proceeding. This would let you validate the plan-to-implementation translation quality before trusting it end-to-end. The proposal could note this as a `--build=step` variant vs `--build=auto`.

6. **OVER-ENGINEERED** [ADVISORY]: **Parallel agent spawning via worktree isolation is premature.** The proposal mentions "For parallel tracks (identified by the decompose gate), spawn worktree-isolated agents." This is the hardest part of the entire proposal — coordinating parallel autonomous agents with merge conflict resolution — buried in a single sentence. Either scope it out of v1 (sequential only) or acknowledge it as a separate design problem. The decompose gate exists for human-coordinated parallelism; autonomous parallel builds are a different beast.

## Concessions

1. **The "no new infrastructure" approach is exactly right.** Adding ~60-80 lines to an existing SKILL.md, reusing plan artifacts, escalation protocols, and existing review/ship skills is the correct level of investment for a first version. This is a capability that should be proven before it gets its own subsystem.

2. **The self-learning dependency analysis is well-calibrated.** Correctly identifying that `lessons.md` + human oversight is sufficient for now, rather than blocking on structured learning infrastructure, avoids the trap of making the perfect the enemy of the good. The "if recurring mistakes emerge, invest then" framing is sound.

3. **The approval gate placement is correct.** Keeping the human gate between plan and build — rather than making the entire pipeline zero-touch — preserves the most important review point (is this the right plan?) while automating the most time-consuming phase (executing the plan).

## Verdict

**REVISE** — The proposal is architecturally sound in its "no new infrastructure" approach and correctly identifies the gap, but has two material gaps: (1) the escalation trigger system it depends on for safety needs to be verified/formalized rather than referenced by assumed numbering, and (2) context window exhaustion on non-trivial builds needs a concrete mitigation strategy, not just an acknowledgment. The `surfaces_affected` soft guardrail (challenge #3) is a cheap fix that would meaningfully improve safety. All three material issues are SMALL-to-MEDIUM cost and don't change the fundamental design — they harden it.

---

## Challenger B — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal assumes the plan artifact can be parsed into reliable, bounded build instructions and file scopes, but no verified evidence was provided that the current `plan` skill emits a consistently machine-actionable structure for sequential execution. If the plan text is semi-structured or varies by author/model output, the build agent may misread steps, run the wrong verification commands, or edit outside intended scope. From a trust-boundary perspective, you're treating model-authored markdown as executable control input; that needs stricter structure or validation before it drives autonomous edits and shell commands.

2. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: “Run verification commands from the plan” creates a command-injection trust issue unless those commands are constrained to an allowlist or validated. The plan file is untrusted model output, and promoting it directly into shell execution crosses a critical boundary. Even if the model generated the plan earlier in the same pipeline, prompt injection or accidental dangerous command generation could lead to destructive local execution, credential exposure, or data exfiltration via shell/network tools.

3. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: Scope containment via `surfaces_affected` plus “escalate if scope grows” is weaker than enforcement. As written, the agent may already have modified out-of-scope files before detecting the violation. For privilege/scope control, you want a pre-edit guardrail or at least a deterministic check before write/apply actions, not just a protocol reminder in markdown. Otherwise lower-trust generated instructions can still cause higher-impact changes before a human is consulted.

4. [ASSUMPTION] [ADVISORY]: The claim that this is “zero-risk — the human reviews every PR” understates the risk of autonomous local execution before PR review. Human review mitigates merge-time defects, but not build-time side effects: secret leakage into logs, destructive filesystem commands, unintended migrations, external API calls, or poisoned test fixtures can all happen before review.

5. [UNDER-ENGINEERED] [ADVISORY]: The proposal says the 7 escalation triggers apply during build, including “security-sensitive changes,” but does not define how those are detected. Without concrete detection criteria, the system may fail open on auth, secret, network, deserialization, shell, or permission-related changes—the exact places an autonomous builder deserves the most scrutiny.

6. [ESTIMATED] [ADVISORY]: “Estimated scope: ~60-80 lines added to plan/SKILL.md” is ESTIMATED: assumes existing plan instructions are already structured enough, execution controls can be expressed purely in prompt text, and no validation/helpers are needed. Given the trust-boundary and execution-safety concerns above, that estimate likely excludes safeguards required for safe autonomous shell execution.

## Concessions
- Reusing the existing approval gate and escalation model is directionally sound and reduces uncontrolled autonomy.
- Calling out repeated-failure stopping behavior is a good containment measure against blind retry loops.
- Restricting edits to declared surfaces is the right security/control objective, even if the current proposal needs stronger enforcement.

## Verdict
REVISE — the feature is promising, but autonomous execution currently treats model-generated plan content as trusted instructions for file edits and shell commands without enough validation or enforcement.

---

## Challenger C — Challenges
[ERROR: Challenger C (gemini-3.1-pro): LLM call failed (InternalServerError): Error code: 503 - {'error': {'message': 'litellm.ServiceUnavailableError: GeminiException - {\n  "error": {\n    "code": 503,\n    "message": "This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.",\n    "status": "UNAVAILABLE"\n  }\n}\n. Received Model Group=gemini-3.1-pro\nAvailable Model Group Fallbacks=None', 'type': None, 'param': None, 'code': '503'}}]

---

---
debate_id: autobuild-tools-on
created: 2026-04-17T14:51:02-0700
mapping:
  A: gpt-5.4
personas:
  A: security
---
# autobuild-tools-on — Challenger Reviews

## Challenger A (security) — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposal turns a documentation-only skill change into an execution feature without adding any enforcement for trust boundaries during autonomous writes. You state “agent edits are checked against the plan's file list” and “no new hook needed,” but the existing read-before-edit hook only protects configured sensitive paths and explicitly exempts `tasks/`, `docs/`, `tests/`, `config/`, and `stores/` (`hooks/hook-read-before-edit.py` lines 59-83; `config/protected-paths.json`). I did not see evidence of a hook or script that blocks writes outside `surfaces_affected`. That means the new mode would rely on the model to self-police scope, which is weak precisely when the system is autonomously iterating after failures. Add an actual pre-write scope gate tied to the active plan artifact, or narrow the recommendation to “assisted autobuild” rather than autonomous build.

2. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal assumes the plan artifact can be safely and deterministically parsed into executable build steps and `verification_commands`, then executed. From the repo evidence provided, plans are markdown artifacts and the enforcement config only requires those frontmatter fields exist (`config/protected-paths.json` lines 17-23); I did not see evidence here of a hardened parser or command allowlist for plan-derived commands. That creates a shell-injection and prompt-injection boundary problem: untrusted natural-language plan content becomes executable behavior. Before approving autonomous execution, define a strict schema for executable fields and constrain command execution to vetted patterns or an explicit allowlist.

3. [RISK] [MATERIAL] [COST:MEDIUM]: Parallel-track execution increases the chance of bypassing isolation through prompt content and path handling. The existing agent-isolation hook enforces `isolation: "worktree"` for write-capable agents, but its own header notes it only “warns (non-blocking) when worktree agents receive absolute repo paths in their prompts, which bypasses isolation entirely” (`hooks/hook-agent-isolation.py` lines 4-15). Your proposal explicitly wants to spawn parallel agents during build, so this known weakness becomes part of the critical path. For autonomous mode, warning-only is insufficient; absolute-path leakage to subagents should be blocked or scrubbed.

4. [RISK] [ADVISORY]: “Zero-risk — the human reviews every PR” understates the risk of not changing the design. Human review is a mitigation for bad code landing, but it does not prevent local destructive side effects during the build loop: arbitrary verification commands, repeated test fixtures, external API calls, or unintended file churn can happen before review. This doesn’t by itself force rejection, but the proposal should separate “merge risk” from “execution risk.”

5. [UNDER-ENGINEERED] [ADVISORY]: The proposal adds a long-running autonomous loop without addressing data exfiltration to external services already present in the repo. Build OS has outbound LLM/research clients (`scripts/llm_client.py`, `scripts/research.py`, `scripts/managed_agent.py`). If autobuild feeds plan content, code, test output, or secrets-containing logs into those systems during review/escalation, sensitive repository data may leave the trust boundary. Existing code shows some care around secret leakage in logs for managed agents (`scripts/managed_agent.py` lines 86-89), which is good, but autobuild should explicitly define what artifacts may be sent to third-party APIs and what must be redacted.

## Concessions
- Reusing existing review and escalation concepts is directionally sound and avoids inventing a second governance system.
- The proposal correctly identifies that iteration quality degrades and that autonomous retries need a hard stop.
- Existing worktree-isolation infrastructure provides a useful foundation for parallel execution, even if it is not yet sufficient for this use case.

## Verdict
REVISE — the idea is plausible, but autonomous execution crosses from advisory workflow into untrusted command/file mutation, and the current proposal lacks concrete enforcement for plan scope, executable command safety, and strong isolation in parallel builds.

---

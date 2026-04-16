---
description: Runtime rules for multi-agent execution — isolation, sensitivity, reconciliation
---
<!-- Enforced-By: hooks/hook-decompose-gate.py, hooks/hook-agent-isolation.py -->

# Orchestration — Runtime Rules

These rules apply whenever agents are spawned, whether or not `/plan` was run.
Planning-time heuristics (decomposition, patterns, synthesis) live in `/plan` Step 3b.

## Policy

Agent Teams + subagents is the default orchestration model (D103). Do not use a full Conductor-style prompt overlay.

**Runtime layer cap:** No more than 2 orchestration layers active simultaneously: (1) this global rule file and (2) one task-specific skill. Do not stack additional orchestration personas or playbook injections.

## Decomposition Gate (Hook-Enforced, Advisory)

`hooks/hook-decompose-gate.py` nudges toward worktree fan-out when a session starts editing multiple distinct files. The gate is **advisory, not blocking** — it returns `permissionDecision: "allow"` with `additionalContext` carrying a prompt hint, not a user-visible deny. The agent reads the nudge and decides.

**Trigger:** fires once per session on the 2nd distinct-file Write|Edit in the main session (worktree agents are never nudged). A second firing occurs only if a `plan_submitted: true` flag exists but the main session keeps writing — that contradicts the declared intent and is worth surfacing once.

**Threshold:** ≥2 independent components. Historical data showed the "exactly 2 truly independent" case is rare but real; with advisory posture, the cost of a false positive is a single prompt-hint the agent reads and ignores. The cost of a false negative — sequentializing genuinely parallel work — is a long session that should have been two short ones.

**What the nudge says:** "Decomposition nudge: this session has now edited a second distinct file. If the work breaks into 2+ independent components, consider dispatching worktree agents. If components share state, proceed and note the reason in the current plan artifact."

**Maximize fan-out, not minimize it.** The default failure mode is under-parallelization (grouping by "theme" into one large agent instead of 2-3 focused ones). Ask: "how many independent components exist?" Trivial multi-file edits (rename, import change) that share no logical coupling can stay in one agent; edits requiring different reasoning should split.

**Read-only agents (Explore, research) can go wider** — 5-10 parallel with no worktree needed. Default to parallel Explore agents for any research with 3+ independent questions.

**Optional flags** (kept for backward compatibility; agents rarely need them now):
- `echo '{"bypass": true, "reason": "<why>"}' > /tmp/claude-decompose-{SESSION_ID}.json` → suppress the nudge for this session
- `echo '{"plan_submitted": true}' > /tmp/claude-decompose-{SESSION_ID}.json` → declare parallel plan; subsequent main-session writes trigger the "plan_declared" nudge

**Session ID:** Uses `$CLAUDE_SESSION_ID` if set, otherwise parent PID.

## Isolation Default

Parallel agents MUST use `isolation: "worktree"` unless read-only. Eliminates file collisions and index.lock contention. Read-only agents (searching, analyzing) may skip worktree isolation.

## File References in Worktree Agent Prompts

Worktree agent prompts: relative paths only (`src/file.py`, not `/home/.../src/file.py`). Absolute paths bypass isolation — the agent writes to the main checkout instead of the worktree.

## After Parallel Agents Complete

- Check for conflicting outputs before proceeding
- If agents edited overlapping content, reconcile before committing
- Reassess: initial results may show branches should be merged, expanded, or terminated

## Model Routing

Match model cost to task complexity. Haiku for classification (tier assignment, direction tagging, category labeling). Opus or cross-model for reasoning (review, debate, planning). Regex or Python for pattern matching (sentiment, format detection). The `llm_client.py` `model` parameter is where this choice is made — don't default to the session model for cheap tasks.

## Workload Sensitivity

**Tier 1 data** (fail-closed — treat ambiguous as Tier 1):
- Production secrets, API keys, OAuth tokens
- Unredacted PII (phone numbers, email addresses, physical addresses)
- Financial/contract content (>$1,000 threshold per security.md)
- Raw message text from personal communication channels

For tasks involving Tier 1 data: use standard isolated subagents via `Agent` tool, not Agent Teams. Agent Teams context sharing across sessions is not yet characterized for sensitive workloads.

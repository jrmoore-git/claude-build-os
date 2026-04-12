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

## Decomposition Gate (Hook-Enforced)

`hooks/hook-decompose-gate.py` blocks the first `Write|Edit` call in each session until you assess decomposability. When the gate fires:

1. **Assess the task.** Count **independent logical components** — groups of 1-3 tightly coupled files that can be edited without knowing the others' changes. This is the fan-out count.
2. **If 3+ components — decompose:** One agent per component. Output a plan listing each component, its file scope, and dependencies. Then write the flag: `echo '{"plan_submitted": true}' > /tmp/claude-decompose-{SESSION_ID}.json`. Dispatch parallel agents with worktree isolation.
3. **If 1-2 components — bypass:** Write: `echo '{"bypass": true}' > /tmp/claude-decompose-{SESSION_ID}.json`. Proceed normally.
4. **User override:** If the user says "skip" or "just do it", write the bypass flag immediately.

**Maximize fan-out, not minimize it.** The default failure mode is under-parallelization (grouping by "theme" into 3 large agents instead of 6-8 focused ones). Ask: "how many independent components exist?" not "can I get to 3 subtasks?" Trivial multi-file edits (rename, import change) that share no logical coupling can stay in one agent — but edits requiring different reasoning should split.

**Read-only agents (Explore, research) can go wider** — 5-10 parallel with no worktree needed. They're cheap and fast. Default to parallel Explore agents for any research that has 3+ independent questions.

The gate fires once per session. After the flag file exists, all writes proceed normally.

**Session ID:** Uses `$CLAUDE_SESSION_ID` if set, otherwise parent PID.

## Isolation Default

All parallel agents MUST use `isolation: "worktree"` unless the task is read-only (no file writes). Worktree isolation gives each agent its own git checkout, eliminating file collisions and index.lock contention. This is not optional.

Read-only agents (searching, analyzing, summarizing) may skip worktree isolation since they don't create collision risk.

## File References in Worktree Agent Prompts

When dispatching a worktree agent, **use only relative paths** in the prompt:

- **Wrong:** "Edit `/home/user/myproject/src/synthesis.py`" — absolute path points to main checkout, bypasses worktree entirely
- **Right:** "Edit `src/synthesis.py`" — relative to cwd, which is the worktree root

Absolute paths silently defeat isolation: the agent writes to the shared main checkout instead of its isolated copy. This was discovered when multiple worktree agents all wrote to main because dispatch prompts used absolute paths. The worktrees appeared empty and were auto-cleaned.

This is convention-enforced (not hooked) because it requires correct prompt authorship.

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

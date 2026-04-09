---
description: Runtime rules for multi-agent execution — isolation, sensitivity, reconciliation
---

# Orchestration — Runtime Rules

These rules apply whenever agents are spawned, whether or not `/plan` was run.
Planning-time heuristics (decomposition, patterns, synthesis) live in `/plan` Step 3b.

## Policy

Agent Teams + subagents is the default orchestration model. Do not use a full Conductor-style prompt overlay.

**Runtime layer cap:** No more than 2 orchestration layers active simultaneously: (1) this global rule file and (2) one task-specific skill. Do not stack additional orchestration personas or playbook injections.

## Decomposition Gate (Hook-Enforced)

`hooks/hook-decompose-gate.py` blocks the first `Write|Edit` call in each session until you assess decomposability. When the gate fires:

1. **Assess the task.** Is it 3+ independent subtasks with non-overlapping files?
2. **If YES — decompose:** Output a plan listing subtasks, file ownership, and parallel/sequential classification. Then write the flag (use Bash tool, NOT Write tool): `echo '{"plan_submitted": true}' > /tmp/claude-decompose-{SESSION_ID}.json`. Dispatch parallel agents with worktree isolation.
3. **If NO — bypass:** Single file or tightly coupled work. Write (use Bash tool, NOT Write tool): `echo '{"bypass": true}' > /tmp/claude-decompose-{SESSION_ID}.json`. Proceed normally.
4. **User override:** If the user says "skip" or "just do it", write the bypass flag immediately.

The gate fires once per session. After the flag file exists, all writes proceed normally.

**Session ID:** Uses `$CLAUDE_SESSION_ID` if set, otherwise parent PID.

## Isolation Default

All parallel agents MUST use `isolation: "worktree"` unless the task is read-only (no file writes). Worktree isolation gives each agent its own git checkout, eliminating file collisions and index.lock contention. This is not optional.

Read-only agents (searching, analyzing, summarizing) may skip worktree isolation since they don't create collision risk.

## After Parallel Agents Complete

- Check for conflicting outputs before proceeding
- If agents edited overlapping content, reconcile before committing
- Reassess: initial results may show branches should be merged, expanded, or terminated

## Workload Sensitivity

**Tier 1 data** (fail-closed — treat ambiguous as Tier 1):
- Production secrets, API keys, OAuth tokens
- Unredacted PII (phone numbers, email addresses, physical addresses)
- Financial/contract content
- Raw message text from personal channels (email bodies, chat messages)

For tasks involving Tier 1 data: use standard isolated subagents via `Agent` tool, not Agent Teams. Agent Teams context sharing across sessions is not yet characterized for sensitive workloads.

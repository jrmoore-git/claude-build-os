---
description: Runtime rules for multi-agent execution — isolation, sensitivity, reconciliation
---

# Orchestration — Runtime Rules

These rules apply whenever agents are spawned, whether or not `/plan` was run.
Planning-time heuristics (decomposition, patterns, synthesis) live in `/plan` Step 3b.

## Policy

Agent Teams + subagents is the default orchestration model. Do not use a full Conductor-style prompt overlay.

**Runtime layer cap:** No more than 2 orchestration layers active simultaneously: (1) this global rule file and (2) one task-specific skill. Do not stack additional orchestration personas or playbook injections.

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

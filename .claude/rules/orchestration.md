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

`hooks/hook-decompose-gate.py` blocks the first `Write|Edit` call in each session until you assess decomposability. Count independent components. 3+: decompose (one agent per component, output plan with file scopes, write flag: `echo '{"plan_submitted": true}' > /tmp/claude-decompose-{SESSION_ID}.json`, dispatch with worktree isolation). 1-2: bypass (`echo '{"bypass": true}' > /tmp/claude-decompose-{SESSION_ID}.json`). User says "skip" or "just do it": bypass immediately.

**Maximize fan-out, not minimize it.** The default failure mode is under-parallelization (grouping by "theme" into 3 large agents instead of 6-8 focused ones). Ask: "how many independent components exist?" not "can I get to 3 subtasks?" Trivial multi-file edits (rename, import change) that share no logical coupling can stay in one agent — but edits requiring different reasoning should split.

**Read-only agents (Explore, research) can go wider** — 5-10 parallel with no worktree needed. They're cheap and fast. Default to parallel Explore agents for any research that has 3+ independent questions.

The gate fires once per session. After the flag file exists, all writes proceed normally.

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

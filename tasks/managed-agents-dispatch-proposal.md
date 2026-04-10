---
topic: managed-agents-dispatch
created: 2026-04-10
---
# Managed Agents Integration with BuildOS

## Problem
BuildOS currently runs all agent work locally via Claude Code CLI sessions. Long-running tasks (debate refinement, multi-round review, consolidation) block local sessions. Remote execution requires SSH to the Mac Mini. There's no way to offload Claude-only workloads to cloud infrastructure, and no architectural primitive for managed agent dispatch.

Jarvis's always-on aspiration (persistent email/calendar/promise monitoring) is handled via cron — fire-and-forget with no session continuity. This is a separate concern that belongs in the Jarvis repo.

### Current System Failures
- Long debate/refine runs (6 rounds x 3 models) consume 15-30 minutes of local session time
- Remote execution requires SSH + tmux; no way to dispatch from laptop and check results later
- Cron-based monitoring has no state continuity between runs (each run starts fresh)
- No existing failures per se — this is greenfield capability expansion

### Operational Context
- debate.py runs ~2-5 times/day, costs ~$1-2/day across models
- Refine legs are Claude-only (3 of 6 rounds) — these could run on MA
- Consolidation (pre-judgment dedup) is Claude-only — could run on MA
- BuildOS is a framework used across multiple projects (not just Jarvis)

### Baseline Performance
No existing system for cloud-hosted agent dispatch. Current execution is 100% local via CLI sessions and cron.

## Proposed Approach
**Approach A+C: Hybrid Orchestration Layer with Background Worker as first milestone.**

Phase 1 (C — Background Worker):
- Add `scripts/managed_agent.py` client that can dispatch any Claude-only task to Managed Agents API
- Integrate with debate.py to optionally offload refine/consolidation legs
- Validate API, cost model, and failure modes on real workloads

Phase 2 (A — Orchestration Layer):
- Add routing logic to BuildOS that decides local vs. cloud execution
- Support remote execution (dispatch from any machine, poll for results)
- Integrate Agent Teams for parallel track orchestration (when API stabilizes)

**Not building (deferred to Jarvis repo):**
- Approach B: Persistent Jarvis agent with always-on session
- Cron-to-persistent migration

## Simplest Version
A `managed_agent.py` script that can:
1. Create a Managed Agent session with a prompt
2. Stream or poll for results
3. Return structured output

First integration point: `debate.py --use-ma` flag that sends refine rounds to Managed Agents instead of running locally.

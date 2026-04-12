---
topic: learning-velocity
created: 2026-04-11
---
# Learning Velocity — Close the Measurement, Verification, and Pruning Gaps

## Problem
BuildOS has an enforcement ladder (lesson -> rule -> hook -> architecture) that catches and corrects mistakes, but no way to measure whether corrections are reducing recurrence. The system captures failures but not validated approaches. Governance accumulates (lessons, rules, hooks) but nothing measures whether it's earning its keep or actively removes what's no longer load-bearing. A manual `/investigate` run just proved 3 of 4 tested lessons had stale or wrong information — nothing triggers that automatically.

The system adds friction but never removes it. More governance isn't better governance — it's slower sessions and more context consumed.

## Proposed Approach

Add three capabilities to the existing `/healthcheck` skill:

1. **Measurement** — 4 computed learning velocity metrics derived from git log on `tasks/lessons.md`. No new infrastructure, just git log math added to `/healthcheck` full scan output.

2. **Scheduled verification** — When `/healthcheck` full scan finds stale lessons (>14d, no activity), auto-run `/investigate --claim` on the top 2-3 stalest. Not all — that's expensive. The stalest ones are the most likely to be poisoning sessions.

3. **Pruning** — Rule/hook redundancy check in `/healthcheck` full scan. For each rule: "does a hook already enforce this?" If yes, the rule is redundant governance. For each hook: "has this fired in the last 30 days?" If no, it may not be earning its keep. Flag candidates — never auto-prune.

Non-goals:
- Positive signal capture as a new governance file or system. Rules already encode "do this" when they're promoted from lessons. That's the positive capture mechanism — just not framed that way.
- Dashboards or reporting UI. The metrics surface in `/healthcheck` output, not a separate tool.
- Automated pruning. Pruning candidates are flagged; user decides.

## Simplest Version
Add the 4 velocity metrics (git log math) to `/healthcheck` Step 6 output. That's ~15 lines of bash/python. If those numbers are useful after 2-3 sessions, add verification and pruning steps.

### Current System Failures
1. 2026-04-11: Manual `/investigate --claim` on 4 active lessons found 3 with stale or wrong information (L17 wrong field names, L18 structurally fragile claim, L19 wrong decomposition numbers). Nothing triggered this check automatically.
2. 2026-04-11: L21 marked Resolved but still in active table — discovered manually during investigation, not by any automated check (before healthcheck was built).
3. Ongoing: No way to answer "are we making fewer mistakes over time?" or "are lessons getting promoted faster?" The enforcement ladder has no feedback loop on its own effectiveness.

### Operational Context
- Active lessons: ~12 in tasks/lessons.md (well under 30 target)
- Rules: 8 files in .claude/rules/ (excluding reference/)
- Hooks: 17 in hooks/
- debate-log.jsonl: ~95 entries, 5-10 debate.py runs/day
- `/investigate --claim` costs: 1 cross-model panel call per lesson (~30s each, $0.05-0.10 per call)
- `/healthcheck` full scan: runs when >7d since last scan or lessons >25 — currently low frequency

### Baseline Performance
- Current measurement: none. No metrics on learning velocity exist.
- Current verification: none. Lessons are only verified when someone manually runs `/investigate --claim`.
- Current pruning: archival exists (move Resolved/Promoted lessons to archived section). No active pruning of rules or hooks. No redundancy detection.
- Current positive capture: rules encode validated patterns when promoted from lessons. No other mechanism.

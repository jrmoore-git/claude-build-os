---
name: start
description: "Session bootstrap + workflow routing. Loads working context (uncommitted work, memory staleness, current-state, infra versions, recent sessions, lessons, decisions), shows project status, and suggests the next skill based on artifact state. Replaces /recall and /status."
user-invocable: true
---

# /start — Session Bootstrap + Workflow Routing

Orient the session and route to the next action. Combines context loading (old `/recall`) with workflow stage detection (old `/status`). Idempotent — if context is already loaded this session, skip the bootstrap and jump to Step 2.

## Procedure

### Step 0: Idempotency guard

If this skill has already run in the current session (you can see the output brief earlier in conversation), skip Step 1 entirely — go straight to Step 2 (state gathering + routing). The bootstrap is expensive; the routing is cheap.

### Step 1: Bootstrap (context loading)

Run each sub-step. If a file is missing or a script fails, skip it silently.

**1a. Uncommitted work check**
```bash
python3.11 scripts/detect-uncommitted.py
```
If `has_uncommitted` or `auto_commit_pending` is true, add at the TOP of output:
```
## Prior Session Recovery
[message from output]
ACTION: Review uncommitted files, commit with a proper message, enrich session-log if auto-captured.
```

**1b. Memory staleness check**
```bash
python3.11 scripts/verify-plan-progress.py
```
If `has_stale_memory` is true:
```
## Stale Memory Detected
[message from output]
ACTION: Update listed memory files to match actual state before recommending next steps.
```
**HARD RULE:** When this fires, do NOT recommend next steps based on stale memory. Read the plan file, determine actual progress from disk artifacts + session log, update memory files immediately.

**1c. Current-state freshness check**
```bash
python3.11 scripts/check-current-state-freshness.py
```
If `is_stale` is true:
```
## Stale Current State
[message from output]
Recent commits: [list from output]
ACTION: Do NOT trust "Next Action" from current-state.md. Determine actual state from git log + session-log, then update current-state.md.
```
**HARD RULE:** When this fires, derive the "Next" section from git log + session-log, NOT from current-state.md.

**1d. Infrastructure version check**
```bash
python3.11 scripts/check-infra-versions.py
```
If `has_drift` is true, add a **Version Drift** warning and update MEMORY.md with live versions.
If `check_failed` is true, note: "Infrastructure version check incomplete — version numbers from memory may be stale."

**1e. Read context files**

Read each file below. Skip missing files silently.

| File | What to extract |
|------|----------------|
| `docs/current-state.md` | Current phase, active work, next action |
| `tasks/handoff.md` | Handoff notes from prior session |
| `tasks/session-log.md` | Last 5 entries (separated by `---`) |
| `tasks/<topic>-plan.md` | Only the section for the current in-progress topic (if a plan artifact exists) |
| `tasks/decisions.md` | Only undecided/blocked entries |
| `tasks/lessons.md` | Last 10 rows (highest lesson numbers) |

**1f. Topic search** (optional)

If the session involves a specific domain, run:
```bash
python3.11 scripts/recall_search.py [domain keywords] --files lessons,decisions
```
Include results with score > 0.1 under **Relevant prior context**.
If BM25 returns nothing useful, try semantic fallback:
```bash
python3.11 scripts/recall_search.py [domain keywords] --semantic --files lessons,decisions
```
Include results with similarity > 0.5. Treat scores below 0.55 as low-confidence.

**1g. Governance health — backward-looking (what rotted since last session?)**

Quick staleness scan — output ONLY if something needs attention. Silence = healthy.

```bash
# Count active lessons
active_count=$(grep -c '^| L[0-9]' tasks/lessons.md 2>/dev/null) || active_count=0

# Check for Resolved lessons still in active table (stale from prior sessions)
resolved_active=$(grep -E '^\| L[0-9]+.*\[Resolved' tasks/lessons.md 2>/dev/null || true)

# Days since last full healthcheck
last_hc=$(grep -n '\[healthcheck\]' tasks/session-log.md 2>/dev/null | tail -1 || true)

# Overdue decisions (NEEDS DECISION or open status, added >7 days ago)
overdue_decisions=$(grep -E 'NEEDS DECISION|Status: open' tasks/decisions.md 2>/dev/null || true)
```

**Output only if something's wrong:**
```
## Governance Health
- Lessons: N/30 [OK|WARNING >25|OVER >30]
- Resolved lessons still active: [list or "none"]
- Last full scan: N days ago [OK <7d|OVERDUE >7d]
- Overdue decisions: [list or omit]
```

If everything is healthy (count ≤25, no Resolved in active, last scan <7d, no overdue decisions): emit nothing.

**Auto-trigger full /healthcheck:** If ANY of these conditions are true, run `/healthcheck` (full 6-step scan) after bootstrap completes but before Step 2:
1. >7 days since last `[healthcheck]` marker in session-log
2. Active lesson count >25
3. Post-investigate flag (investigation report flagged stale governance)

### Step 2: Gather workflow state

```bash
# Uncommitted changes
git diff --name-only HEAD
git diff --cached --name-only
git status --short

# Recent artifacts (newest first)
ls -t tasks/*-review.md tasks/*-plan.md tasks/*-challenge.md tasks/*-judgment.md tasks/*-debate.md tasks/*-refined.md tasks/*-proposal.md tasks/*-design.md tasks/*-think.md tasks/*-explore.md 2>/dev/null | head -15

# Recent debate activity
tail -5 stores/debate-log.jsonl 2>/dev/null | python3.11 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        print(f\"{e.get('timestamp','?')[:16]}  {e.get('phase','?')}  {e.get('debate_id','?')}\")
    except: pass
"
```

If changed files exist, classify them:
```bash
echo "<changed files>" | python3.11 scripts/tier_classify.py --stdin
```

If a recent topic is detected from artifacts, check its status:
```bash
python3.11 scripts/artifact_check.py --scope <topic>
```

### Step 3: Route to next action

Evaluate conditions **in order** — first match wins.

| # | Condition | Stage | Recommendation |
|---|-----------|-------|----------------|
| 1 | Context budget at 55%+ | Context pressure | "`/wrap` before state is lost" |
| 2 | `tasks/<topic>-proposal.md` exists, no debate/challenge artifacts | Proposal ready | "`/explore` to map the option space" |
| 3 | `tasks/<topic>-design.md` exists, no challenge artifact | Design ready | "`/challenge` before planning" |
| 4 | Changed files introduce new abstraction/dependency | Scope expansion | "`/challenge` — new abstraction detected" |
| 5 | Plan exists, touches protected paths, no plan file with valid frontmatter | Plan gate gap | "`/plan` — protected paths need a plan file" |
| 6 | Multiple files edited (3+), no review artifact for current topic | Build in progress | "`/review` on this diff" |
| 7 | Changes detected (1-2 files), no review artifact | Small build | "When ready: `/review`" |
| 8 | Review exists, status=passed | Ready to ship | "`/ship` to deploy" |
| 9 | Review exists, status=revise | Findings to address | "N open findings. Address them, then `/review` again." |
| 10 | Review exists, status=degraded | Degraded review | "`/ship` to deploy or `/review` to retry" |
| 11 | Recent deploy (deploy_all.sh ran today) | Post-ship | "`/sync` to update docs" |
| 12 | No changes, no recent artifacts | Clean slate | "What are we building?" |

### Step 4: Contextual suggestions

After the primary recommendation, append any matching suggestions:

| Condition | Suggestion |
|-----------|------------|
| No design doc for active topic | "`/think` would structure this" |
| Design doc exists, no challenge artifact | "`/challenge` before `/plan`?" |
| Plan exists, unstarted (no code changes since plan) | "Ready to build, or `/elevate` to check ambition?" |
| Code changed since last review | "`/review` to validate" |
| Diff touches protected paths | "`/review --qa` recommended" |
| Session long, context above 55% | "Consider `/wrap` soon" |
| User's last message is an open question | "`/explore` to think across models" |
| Strategy language ("should we", "thesis", "bet", "direction") | "`/pressure-test` for strategic challenge" |
| Plan exists, no challenge artifact, plan introduces new features | "No `/challenge` artifact — consider running before build" |

### Step 5: Safe to stop?

- If `git status --short` shows changes: "NOT safe to stop — commit or stash first."
- If clean: "Safe to stop."

## Output Format

Single compact brief, under 2000 tokens. Bullets only.

```
## Status
[1-3 bullets: phase, what's working, what's broken]

## Last Session
[2-4 bullets: done, decided, NOT finished]

## Workflow
Stage: <stage name>
Topic: <topic if detected, or "none">
Tier: <tier if changes detected>
Artifacts: <list existing for topic, or "none">

## Next Action
-> <primary recommendation from Step 3>
   <contextual suggestions from Step 4>

## Open Decisions
[bullets: only genuinely undecided items — skip if none]

## Lessons (recent)
[5-10 bullets: most useful recent lessons, paraphrased short]

## Safe to Stop
<yes/no + reason>
```

**Rules:**
- No essays. Bullets only. One line per bullet.
- Skip any section with nothing real to say.
- Do not quote raw message content from personal channels.
- Do not surface file contents verbatim — synthesize.
- If context is thin (files sparse), say so in one line and stop.

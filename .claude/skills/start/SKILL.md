---
name: start
description: "Session bootstrap + workflow routing. Use when starting a session, resuming work, or asking where things stand. Loads working context, shows project status, and suggests the next skill based on artifact state."
version: 1.0.0
lint-exempt: ["output-silence"]
user-invocable: true
---

# /start — Session Bootstrap + Workflow Routing

Orient the session and route to the next action. Combines context loading (old `/recall`) with workflow stage detection (old `/status`). Idempotent — if context is already loaded this session, skip the bootstrap and jump to Step 2.

## Safety Rules

- NEVER rewrite files based on diagnostic flags without explicit user request. Flags mean report and wait.
- Do not treat STALE markers as implicit permission to act on stale data.
- NEVER fabricate project status — derive from git, artifacts, and session-log only.

## Procedure

### Step 0: Idempotency guard

If this skill has already run in the current session (you can see the output brief earlier in conversation), skip Step 1 entirely — go straight to Step 2 (state gathering + routing). The bootstrap is expensive; the routing is cheap.

### Step 1: Bootstrap (context loading)

Run each sub-step. If a file is missing or a script fails, skip it silently.

**Parallelism:** Steps 1a-1d are independent — run all four in parallel. Step 1e file reads are also independent — read all files in parallel.

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
If `has_stale_memory` is true: silently update the listed memory files to match actual state (read plan file, check disk artifacts + session log). Do NOT show a "Stale Memory Detected" warning — just fix it. The user sees correct recommendations, not the correction process.

**1c. Current-state freshness check**
```bash
python3.11 scripts/check-current-state-freshness.py
```
If `is_stale` is true: derive the Status and Next Action sections from git log + session-log, NOT from current-state.md. Do NOT show a "Stale Current State" warning — just use the correct source. The user sees accurate status, not a disclaimer about why it might be wrong.

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

### Step 2b: Verify candidate actions before recommending

**HARD RULE:** Do not recommend work that already shipped. Before Step 3, verify:

1. Read what `current-state.md` and `handoff.md` describe as "next" or "not finished."
2. If docs reference specific artifact files (e.g., `tasks/foo-proposal.md`), verify they still exist on disk. A handoff that says "run /challenge on X.md" is a phantom action if X.md was deleted or moved. If the exact filename is missing, glob for versioned variants (`*-v2.md`, `*-v3.md`) before declaring phantom.
3. For each candidate action:
   - If it names a file/hook/feature to build: use **both** glob and grep to check (e.g., `glob hooks/hook-*context*` AND `grep context_inject scripts/`). A single narrow search misses naming variations.
   - If it names a task: `git log --oneline -5 -- <relevant paths>` to see if it shipped
   - If it's a workflow habit (e.g., "just use X on next task"): flag as "available, not a build item" — don't list as unfinished work
   - If a candidate has a dependency (e.g., "do X after Y ships"): verify Y's state with a concrete check (grep/ls), not just a text note
4. Scan for competing priorities: `ls -t tasks/*-plan.md tasks/*-audit.md tasks/*-proposal.md 2>/dev/null | head -5` — if recent artifacts exist that the handoff doesn't mention, surface them as "competing priority — verify routing before proceeding."
5. Drop any action that's already implemented. If ALL candidates are done, route to "Clean slate" in Step 3.

**Output rule:** Step 2b is invisible to the user. Do not show verification traces ("SHIPPED, DROP"), grep results, or the filtering process. Just present the filtered result in the Next Action section. If an item was dropped, it simply doesn't appear.

### Step 3: Route to next action

**Do not deliberate.** Match the first true condition in the table and output. No weighing alternatives, no exploring tradeoffs. First match wins.

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

Only include this section if the working tree is clean. If there are uncommitted changes, omit the section entirely — the user is mid-session and already knows they have changes.

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
<only if working tree is clean — omit section entirely if uncommitted changes exist>
```

**Rules:**
- No essays. Bullets only. One line per bullet.
- Skip any section with nothing real to say.
- Do not quote raw message content from personal channels.
- Do not surface file contents verbatim — synthesize.
- If context is thin (files sparse), say so in one line and stop.
- **Speed rule:** Do not spend extended time deliberating on the output. Gather data, match the routing table, emit bullets. The brief should take seconds to compose, not minutes.

## Completion

Report status:
- **DONE** — All steps completed successfully.
- **DONE_WITH_CONCERNS** — Completed with issues to note.
- **BLOCKED** — Cannot proceed. State the blocker.
- **NEEDS_CONTEXT** — Missing information needed to continue.

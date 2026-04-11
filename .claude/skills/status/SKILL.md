---
name: status
description: "Project status, workflow stage, context-aware next action. Reads git state, artifacts, and context budget to suggest the right skill and mode."
user-invocable: true
---

# /status — Workflow Stage + Smart Routing

Show current workflow stage, project health, and context-aware next action.

## Procedure

### Step 1: Gather state

Run these checks:

```bash
# Check for uncommitted changes
git diff --name-only HEAD
git diff --cached --name-only
git status --short

# Find recent artifacts (newest first)
ls -t tasks/*-review.md tasks/*-plan.md tasks/*-challenge.md tasks/*-judgment.md tasks/*-debate.md tasks/*-refined.md tasks/*-proposal.md tasks/*-design.md 2>/dev/null | head -15

# Check what skills have run this session (recent audit entries)
sqlite3 -json stores/audit.db "SELECT action_type, MAX(timestamp) AS last FROM audit_log WHERE timestamp > datetime('now', '-4 hours') GROUP BY action_type ORDER BY last DESC LIMIT 10;" 2>/dev/null
```

If there are changed files, classify them:
```bash
echo "<changed files>" | python3.11 scripts/tier_classify.py --stdin
```

If there's a recent topic (from artifacts), check its status:
```bash
python3.11 scripts/artifact_check.py --scope <topic>
```

### Step 2: Route to next action

Evaluate the conditions below **in order** — first match wins.

| # | Condition | Stage | Recommendation |
|---|---|---|---|
| 1 | Context budget at 55%+ | Context pressure | "`/wrap-session` before state is lost" |
| 2 | No `/recall` in recent audit AND session just started | Cold start | "`/recall` to orient" |
| 3 | `tasks/<topic>-proposal.md` exists, no debate/challenge artifacts | Proposal ready | "`/debate` to pressure-test this proposal" |
| 4 | `tasks/<topic>-design.md` exists, no challenge artifact | Design ready | "`/challenge` before planning" |
| 5 | Changed files introduce new abstraction/dependency (new import, new class, new package) | Scope expansion | "`/challenge` — new abstraction detected" |
| 6 | Plan exists, plan touches protected paths, no plan file with valid frontmatter | Plan gate gap | "`/plan` — protected paths need a plan file" |
| 7 | Multiple files edited (3+), no review artifact for current topic | Build in progress | "`/review` on this diff" |
| 8 | Changes detected (1-2 files), no review artifact | Small build in progress | "When ready: `/review`" |
| 9 | Review exists, status=passed | Ready to ship | "`/ship` to deploy" |
| 10 | Review exists, status=revise | Findings to address | "N open findings. Address them, then `/review` again." |
| 11 | Review exists, status=degraded | Degraded review | "`/ship` to deploy or `/review` to retry" |
| 12 | Recent deploy (deploy_all.sh ran today) | Post-ship | "`/doc-sync` to update docs" |
| 13 | No changes, no recent artifacts | Clean slate | "What are we building?" |

**Contextual overlays** (append to the primary recommendation if detected):

- If the user's last message is a question with no file references → also suggest: "`/debate --explore` to think across models"
- If the user's last message contains strategy language ("should we", "thesis", "bet", "direction") → also suggest: "`/debate --pressure-test` for strategic challenge"
- If `tasks/<topic>-plan.md` exists but no `tasks/<topic>-challenge.md` and plan introduces new features → also note: "No `/challenge` artifact — consider running before build"

### Step 3: Project health

Run the verification script:
```bash
python3.11 scripts/verify_state.py 2>/dev/null
```

Read the output:
```bash
cat /tmp/verify-state-output.json
```

Display a one-line summary per check (pass/fail). If the file doesn't exist or the script fails, say "Health check unavailable."

### Step 4: Safe to stop?

- If `git status --short` shows changes → "NOT safe to stop — commit or stash first."
- If clean → "Safe to stop. Resume with `/status`."

### Step 5: Output format

```
## Workflow
Stage: <stage name>
Topic: <topic if detected, or "none">
Tier: <tier if changes detected>
Artifacts: <list existing artifacts for topic, e.g. "proposal, debate" or "none">

## Next Action
→ <primary recommendation from Step 2, with skill command>
  <contextual overlay if any>

## Health
Gateway:  ✅ / ❌
LiteLLM:  ✅ / ❌
MCP:      ✅ / ❌
Auth:     ✅ / ❌
Tests:    ✅ / ❌
<other checks from verify-state>

## Safe to Stop
<yes/no + reason>
```

Keep it compact. No essays. One line per item. The "Next Action" section is the primary value — make it specific and actionable.

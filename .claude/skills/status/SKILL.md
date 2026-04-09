---
name: status
description: "Project status, workflow stage, recommended next action."
user-invocable: true
---

# /status — Workflow Stage + Next Action

Show current workflow stage, project health, and recommended next action.

## Procedure

### Step 1: Detect workflow stage

Run these checks:

```bash
# Check for uncommitted changes
git diff --name-only HEAD
git diff --cached --name-only
git status --short

# Find recent artifacts (newest first)
ls -t tasks/*-review.md tasks/*-plan.md tasks/*-challenge.md tasks/*-judgment.md 2>/dev/null | head -10
```

If there are changed files, classify them:
```bash
echo "<changed files>" | python3 scripts/tier_classify.py --stdin
```

If there's a recent topic (from artifacts), check its status:
```bash
python3 scripts/artifact_check.py --scope <topic>
```

### Step 2: Determine stage and recommendation

Based on the checks, determine which stage the user is in:

| Condition | Stage | Recommendation |
|---|---|---|
| No changes, no recent artifacts | Clean slate | "Start building." |
| Changes detected, no review artifact | Build in progress | "When ready: `/review`" |
| Review exists, status=passed | Ready to ship | "Run `/ship` to deploy." |
| Review exists, status=revise | Findings to address | "N open findings. Address them, then `/review` again." |
| Review exists, status=degraded | Degraded review | "Review completed with degraded status (debate unavailable). `/ship` to deploy or `/review` to retry." |
| Recent deploy (deploy script ran today) | Post-ship | "Last deploy succeeded. Start next task." |

### Step 3: Project health

Run the verification script if available:
```bash
bash scripts/verify-state.sh 2>/dev/null
```

Display a one-line summary per check (pass/fail). If the script doesn't exist or fails, say "Health check unavailable."

### Step 4: Safe to stop?

- If `git status --short` shows changes → "NOT safe to stop — commit or stash first."
- If clean → "Safe to stop. Resume with `/status`."

### Step 5: Output format

```
## Workflow
Stage: <stage name>
Topic: <topic if detected, or "none">
Tier: <tier if changes detected>
Action: <recommended next action>

## Health
<check results or "Health check unavailable">

## Safe to Stop
<yes/no + reason>

## Commands
/review  — Classify tier + run review for current changes
/ship    — Pre-flight dashboard + deploy (gates on tests + review)
/status  — This screen (workflow stage + next action + health)
/recall  — Load session context
/wrap-session — End-of-session docs + commit
```

Keep it compact. No essays. One line per item.

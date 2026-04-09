---
name: ship
description: "Release engineer running pre-flight checks then deploying. Gates on tests + review."
user-invocable: true
---

# /ship — Pre-flight Dashboard + Deploy

Run pre-flight checks, display a dashboard, and deploy if all hard gates pass.

## Procedure

### Step 1: Detect scope

Find the most recent review or plan artifact:
```bash
ls -t tasks/*-review.md tasks/*-plan.md tasks/*-debate.md 2>/dev/null | head -5
```
Extract the topic from the newest file (e.g., `foo-review.md` → topic is `foo`).

If no artifacts found, check recent commit messages for a topic hint. If still unclear, ask the user.

### Step 2: Run pre-flight checks

Run each gate and collect results:

**Gate 1: Tests (HARD)**
```bash
bash tests/run_all.sh
```
Pass = exit 0. Fail = exit non-zero.

**Gate 2: Review (HARD)**
```bash
python3 scripts/artifact_check.py --scope <topic>
```
Parse the JSON. Pass = review artifact exists AND not stale AND (`open_material_findings` is 0 or null). Fail = missing or stale or has open findings.

**Gate 3: Plan (HARD for protected paths only)**
```bash
python3 scripts/tier_classify.py --diff-base main
```
Check if any changed files match protected paths from `config/protected-paths.json`. If yes, check that `artifact_check.py` shows plan exists. If no protected paths touched, auto-pass.

**Gate 4: QA (SOFT)**
Check for `tasks/<topic>-qa.md`. If exists, parse frontmatter `qa_result`. If `go`, pass. If `no-go` or missing, warn (advisory only — QA is not blocking).

**Gate 5: Docs (SOFT)**
Check mtimes of `tasks/decisions.md`, `tasks/lessons.md`, `tasks/session-log.md`. If none were modified today, warn (advisory only).

**Gate 6: Git (SOFT)**
```bash
git status --short
```
If output is non-empty, warn about uncommitted changes.

### Step 3: Display dashboard

Format:
```
## Pre-flight Dashboard

Tests:   PASS  /  FAIL (N failures)
Review:  PASS (Tier N, 0 open findings)  /  FAIL (missing|stale|N open findings)
Plan:    PASS (no protected paths)  /  FAIL (plan missing for protected paths)
Docs:    updated today  /  decisions.md not updated (advisory)
Git:     clean  /  N uncommitted changes

Status: READY TO SHIP  /  BLOCKED
```

### Step 4: Handle blocked state

If any HARD gate fails, display what's missing and suggest the fix:
- Tests fail → "Fix failing tests, then `/ship` again."
- Review missing → "Run `/review` first."
- Review stale → "Changes since last review. Run `/review` again."
- Open findings → "N accepted findings unaddressed. Fix them, then `/review` again."
- Plan missing → "Protected paths modified without a plan. Create `tasks/<topic>-plan.md`."

Do NOT deploy. Stop here.

### Step 5: Handle --force

If the user says "force", "ship --force", or "ship force":
- Tests STILL hard-block. Tests are never bypassed.
- Review and plan gates can be bypassed with a waiver.
- Ask the user for a one-line reason for the bypass.
- If a review artifact exists, append a `## Waiver` section:
  ```
  ## Waiver
  Bypassed: <gate name>
  Reason: <user's reason>
  Timestamp: <ISO datetime>
  ```
  Add `waiver: true` to the frontmatter.
- If no review artifact exists, create a minimal one with `status: waived` and the waiver section.
- Proceed to deploy.

### Step 6: Deploy

```bash
bash scripts/deploy_all.sh
```

Stream the output to the user. This script handles the full deploy pipeline (build, restart services, run verification checks).

If deploy fails, show which step failed and suggest remediation.

### Step 7: Post-ship verification

After deploy completes, run any available smoke tests:

```bash
bash tests/smoke_test.sh 2>/dev/null || python3 tests/smoke_test.py 2>/dev/null || echo "No smoke test found"
```

If smoke test passes:
```
Shipped and verified. Commit: <git rev-parse --short HEAD>
Post-deploy smoke: PASS
```

If smoke test fails:
```
Shipped but verification failed. Commit: <git rev-parse --short HEAD>
Post-deploy smoke: FAIL
<failure details>
```
Warn the user and suggest investigating. Do NOT auto-rollback.

## Important Notes

- Tests are NEVER bypassed, even with --force.
- Degraded review status (from failed debate) is allowed — `/ship` will note it but not block.
- SOFT gates (docs, git) are advisory. They appear in the dashboard but never block.

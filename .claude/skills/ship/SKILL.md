---
name: ship
description: "Release engineer running pre-flight checks then deploying. Use when code is reviewed and ready to deploy. Gates on tests + review."
version: 1.0.0
user-invocable: true
---

# /ship — Pre-flight Dashboard + Deploy

Run pre-flight checks, display a dashboard, and deploy if all hard gates pass.

## Safety Rules

- NEVER deploy without passing review — the review gate is a hard requirement.
- Do not skip pre-flight checks, even under time pressure.
- NEVER bypass test failures, even with --force.
- Do not auto-rollback without user approval.
- **Output silence** — Do not emit text between tool calls. Single formatted output at the end only.

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
python3.11 scripts/artifact_check.py --scope <topic>
```
Parse the JSON. Pass = review artifact exists AND not stale AND (`open_material_findings` is 0 or null). Fail = missing or stale or has open findings.

**Gate 3: Plan (HARD for protected paths only)**
```bash
python3.11 scripts/tier_classify.py --diff-base main
```
Check if any changed files match protected paths from `config/protected-paths.json`. If yes, check that `artifact_check.py` shows plan exists. If no protected paths touched, auto-pass.

**Gate 4: Verification (HARD)**

Run execution-based verification. Reading is not verification — running is verification.

a. If `tasks/<topic>-plan.md` exists and has a `verification_commands` field, run each command. Report output.

b. Run at least one adversarial probe based on what the change touches. Pick from:
- **Data correctness:** Feed unexpected input (empty string, None, unicode). Query DB after operation — does the row exist with right values? Run twice — is it idempotent?
- **Error paths:** Kill a dependency (wrong URL, missing env var) — graceful failure or silent corruption? Pass malformed JSON.
- **Boundary conditions:** Zero items, one item, max items. Midnight timestamps, UTC vs Pacific.
- **Integration:** If it calls an external API, does a real read-only call work? Check audit log row exists after execution.

Document what you probed, what you expected, and what happened.

c. If all probes pass, update plan's `verification_evidence` field:
```bash
sed -i '' 's/verification_evidence: "PENDING"/verification_evidence: "<evidence summary>"/' tasks/<topic>-plan.md
```

Pass = all probes pass + plan commands pass. Fail = any probe or command fails. A report with zero adversarial probes is rejected.

**Gate 5: QA Dimensions (SOFT)**

Evaluate 5 dimensions. For each, note PASS or FAIL with a one-line reason.

1. **Test coverage:** For each changed file, does a corresponding test exist? New scripts without tests = FAIL.
2. **Regression risk:** Changed function signatures — are all callers updated? Changed imports — are all importers updated?
3. **Plan compliance:** If a plan exists, does the diff match `surfaces_affected`? Files changed but not in plan? Files in plan but not changed?
4. **Negative tests:** Are error paths covered? Check test files for assertions on error cases.
5. **Integration:** If imports or interfaces changed, are downstream consumers updated? New scripts referenced correctly?

Advisory only — failing dimensions warn but do not block deploy.

**Gate 6: Docs (SOFT)**
Check mtimes of `tasks/decisions.md`, `tasks/lessons.md`, `tasks/session-log.md`. If none were modified today, warn (advisory only).

**Gate 7: Git (SOFT)**
```bash
git status --short
```
If output is non-empty, warn about uncommitted changes.

**Gate 8: BuildOS Sync (HARD — pre-deploy check)**
```bash
bash scripts/buildos-sync.sh --dry-run 2>&1
```
Parse the summary line. Pass = "0 changed, 0 new, 0 missing". If any files are changed, new, or missing — repos are out of sync. Block deploy. Fix: run `bash scripts/buildos-sync.sh --push` first, then `/ship` again. Note: `deploy_all.sh` Step 6 also runs `--push` as best-effort after deploy, but THIS gate (pre-deploy dry-run) is the real enforcement point.

### Step 3: Display dashboard

Format:
```
## Pre-flight Dashboard

Tests:      ✅ PASS  /  ❌ FAIL (N failures)
Review:     ✅ PASS (Tier N, 0 open findings)  /  ❌ FAIL (missing|stale|N open findings)
Plan:       ✅ PASS (no protected paths)  /  ❌ FAIL (plan missing for protected paths)
Verify:     ✅ PASS (N probes, evidence recorded)  /  ❌ FAIL (probe failed: <detail>)
QA:         ✅ 5/5 dimensions  /  ⚠️ N/5 dimensions (advisory)
Docs:       ✅ updated today  /  ⚠️ decisions.md not updated (advisory)
Git:        ✅ clean  /  ⚠️ N uncommitted changes
BuildOS:    ✅ in sync  /  ❌ FAIL (N files diverged — run buildos-sync.sh --push)

Status: READY TO SHIP  /  BLOCKED
```

### Step 4: Handle blocked state

If any HARD gate fails, display what's missing and suggest the fix:
- Tests fail → "Fix failing tests, then `/ship` again."
- Review missing → "Run `/review` first."
- Review stale → "Changes since last review. Run `/review` again."
- Open findings → "N accepted findings unaddressed. Fix them, then `/review` again."
- Verify fail → "Adversarial probe failed: <detail>. Fix and `/ship` again."
- Plan missing → "Protected paths modified without a plan. Create `tasks/<topic>-plan.md`."
- BuildOS out of sync → "N files diverged. Run `bash scripts/buildos-sync.sh --push`."

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
  Timestamp: <ISO datetime Pacific>
  ```
  Add `waiver: true` to the frontmatter.
- If no review artifact exists, create a minimal one with `status: waived` and the waiver section.
- Proceed to deploy.

### Step 6: Deploy

```bash
bash scripts/deploy_all.sh
```

Stream the output to the user. This script:
- Restarts gateway + MCP server
- Builds frontend
- Runs 22 verification checks

If deploy fails, show which step failed and suggest remediation.

### Step 7: Post-ship verification

After deploy completes, run any available smoke tests:

```bash
python3 tests/smoke_test.py 2>/dev/null || python3 app/tests/smoke_test.py 2>/dev/null || bash tests/smoke_test.sh 2>/dev/null || echo "No smoke test found"
```

This verifies the deployed application is healthy after the deploy, not just that tests passed before it. The fallback chain checks common smoke test locations.

If smoke test passes (exit 0, no critical failures):
```
Shipped and verified. Commit: <git rev-parse --short HEAD>
Post-deploy smoke: ✅ PASS (N checks)
```

If smoke test passes with warnings (exit 0, but warnings printed):
```
Shipped and verified. Commit: <git rev-parse --short HEAD>
Post-deploy smoke: ✅ PASS with ⚠️ N warnings (non-blocking)
<warning details>
```

If smoke test fails (exit 1, critical failures):
```
Shipped but verification failed. Commit: <git rev-parse --short HEAD>
Post-deploy smoke: ❌ FAIL
<failure details>
```
Warn the user and suggest investigating. Do NOT auto-rollback.

## Output Format

The ship skill produces a pre-flight dashboard showing gate status (PASS/FAIL for each gate), an overall status (READY TO SHIP / BLOCKED), and post-deploy verification results. The review artifact may be updated with waiver information if --force is used.

## Important Notes

- Tests are NEVER bypassed, even with --force.
- Verification (adversarial probes) is NEVER bypassed, even with --force. The whole point is to catch what happy-path testing misses.
- Degraded review status (from failed debate) is allowed — `/ship` will note it but not block.
- SOFT gates (QA dimensions, docs, git) are advisory. They appear in the dashboard but never block.
- The standard pipeline is `/review` → `/ship`. Use `/review --qa` for isolated QA checks.

## Completion

Report status:
- **DONE** — All gates passed, deployed successfully, post-ship verification complete.
- **DONE_WITH_CONCERNS** — Deployed with soft gate warnings or degraded review status.
- **BLOCKED** — Cannot deploy. Hard gate(s) failed. State which gates and remediation steps.
- **NEEDS_CONTEXT** — Missing topic or unable to determine scope.

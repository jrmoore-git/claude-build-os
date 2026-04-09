---
topic: buildos-sync-enforcement
review_tier: cross-model
status: passed
git_head: 34c8a70
producer: claude-opus-4-6
created_at: 2026-04-03T21:46:00-0700
scope: scripts/deploy_all.sh, .claude/skills/ship/SKILL.md, scripts/buildos-sync.sh
findings_count: 0
spec_compliance: false
---

## PM / Acceptance
- [MATERIAL — FIXED] Exit code 1 semantics fragile and undocumented. Fixed: changed to distinctive exit code 78 in buildos-sync.sh, deploy_all.sh checks for 78 specifically.
- [MATERIAL — FIXED] HARD gate in /ship could be bypassed by deploy_all.sh continuing on non-security failures. Fixed: clarified that /ship Gate 8 (pre-deploy --dry-run) is the real enforcement point; deploy_all.sh Step 6 is best-effort push after deploy. Documented explicitly in both files.
- [ADVISORY] Bundled unrelated /ship changes (verify gate, QA dimensions) — noted, these were from a prior session's commit.

## Security
- [MATERIAL — FIXED] Non-security sync failures silently degrading HARD gate. Fixed: two-layer enforcement model — /ship --dry-run blocks pre-deploy, deploy_all.sh --push is best-effort post-deploy. Only exit 78 (banned-terms) blocks in deploy_all.sh.
- [ADVISORY] --push runs after deploy is live — acknowledged, /ship pre-deploy gate is the real check.

## Architecture
- [MATERIAL — FIXED] STEPS_COMPLETED not updated after Step 5 — fixed in this change.
- [ADVISORY] $? capture in else branch of if — works correctly in bash, added comment for clarity.
- [ADVISORY] Hardcoded step numbering — accepted trade-off for readability.

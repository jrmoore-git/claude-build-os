---
scope: "Enforce BuildOS sync on every deploy and promote /ship gate from SOFT to HARD"
surfaces_affected: "scripts/deploy_all.sh, .claude/skills/ship/SKILL.md"
verification_commands: "bash scripts/buildos-sync.sh --dry-run"
rollback: "git revert <sha>"
review_tier: "Tier 2 — Log only"
challenge_skipped: true
verification_evidence: "buildos-sync --dry-run shows 0 changed after --push; exit 78 tested in code; /ship gate clarified as pre-deploy check"
---

# Plan: BuildOS Sync Enforcement

## Build Order

1. `scripts/deploy_all.sh` — Add Step 6: BuildOS sync after contract tests. Push failure warns but doesn't block. Banned-terms failure blocks.
2. `.claude/skills/ship/SKILL.md` — Gate 8: SOFT → HARD. Update dashboard + blocked-state handler.

## Verification
- `bash scripts/buildos-sync.sh --dry-run` confirms drift detection
- After `--push`: re-run confirms 0 changed

# Resolution: Build OS Compliance Fixes

## Response to Challenges

### Challenge A1 (staff): Contract tests need execution context clarity
**Concede.** The contract tests in `tests/contracts/test_*.sh` are self-contained bash scripts that create temporary SQLite databases, run assertions, and clean up. They don't require a running system — they test the toolbelt (outbox_tool.py) directly. But this should be explicit. The deploy_all.sh addition should note that contract tests run against toolbelt code, not against running services, so they belong AFTER service restart (services are up) but they don't depend on services.

The operational concern about "partially deployed + test failure" is real but already handled: deploy_all.sh uses `set -e` + `trap ERR`, so if contract tests fail in Step 5, Steps 1–4 have completed (services are up), and the developer gets a clear "FAILED at step 5" message. This is the correct failure mode — services are running with the new code, but the developer is warned that invariants may be violated. The alternative (running contracts before service restart) would leave services down on test failure, which is worse.

### Challenge A2 (staff): Empty GRANOLA_OWNER_EMAILS and cache schema stability
**Compromise.** The challenger is right that fail-closed on empty owner_emails has UX consequences — an empty verified set means no drafts can be created, which could be confusing. But this is the correct security posture: unknown state = restrictive, not permissive.

On cache schema stability: the direct parse fallback is already fragile. See A3.

### Challenge A3 (staff): Remove fallback entirely instead of adding filter
**Concede.** This is the better fix. The direct Granola cache parse is a bootstrap path from early development. The verified_emails_cache table is now populated nightly by email-cache-refresh. Instead of adding more logic to a risky fallback, remove the direct parse entirely. If verified_emails_cache is empty, the system should:
1. Return an error: "Email verification cache is empty. Run email-cache-refresh or add address to email_allowlist manually."
2. Log to audit.db (action_type: email_verification_cache_empty)

This is simpler, more auditable, and eliminates the second source of truth.

### Challenge A4 (staff): Deploy timing not measured
**Compromise.** Fair point — "~30s" was an estimate. The contract tests are 8 bash scripts that create temp databases and run outbox_tool.py commands — they're fast (sub-5s each). But I should measure. I'll add a timing note to the implementation.

### Challenge A5 (staff): PostToolUse hook only covers Claude Code edits
**Concede.** The hook only fires for Claude Code tool use, not git operations or IDE edits. But for this project, Claude Code IS the primary edit surface — direct git/IDE edits are rare. A git pre-commit hook would be more universal but also more intrusive (blocks all commits, not just SKILL.md edits).

Given the challenger's point, I'll revise: instead of a PostToolUse echo hook, add a check to `deploy_all.sh` itself. Before Step 1 (deploy_skills.sh), compare SKILL.md mtimes against the last deploy timestamp. If any SKILL.md is newer than the last gateway restart, the deploy proceeds normally. If no SKILL.md changed, Step 1 can be skipped (optimization). This is architectural enforcement — the freshness check is in the deploy script, not in an advisory hook.

### Challenge A6 (staff): Hook has no freshness tracking
**Concede.** Per A5, dropping the PostToolUse hook approach entirely. The freshness check moves into deploy_all.sh as a pre-check, not a Claude-specific hook. This handles all edit surfaces (Claude Code, IDE, git) because the deploy script is the only path to "done."

---

## Revised Plan

| Gap | Original Fix | Revised Fix |
|---|---|---|
| 1. Contract tests in deploy | Add Step 5 to deploy_all.sh | Same — but document that contracts test toolbelt directly, don't need running services. Add timing measurement. |
| 2. Granola owner filter | Add filter to direct parse | **Remove direct parse fallback entirely.** Return error + audit log when cache is empty. |
| 3. SKILL.md change warning | PostToolUse echo hook | **Drop.** Deploy_all.sh is the enforcement point. No additional hook needed — the Build OS rule "enforce verification at the system boundary" already applies. |

**Net: 2 file changes (deploy_all.sh, outbox_tool.py), not 3.**

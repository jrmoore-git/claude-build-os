---
debate_id: build-os-compliance-fixes
created: 2026-03-15T19:43:22-0700
mapping:
  A: gpt-5.4
---
# build-os-compliance-fixes — Challenger Reviews

## Challenger A — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL]: Gap 1 assumes `tests/run_all.sh` is safe to run inside `deploy_all.sh`, but you haven’t addressed production execution context, dependency availability, or side effects. If contract tests require a running system, seeded state, network access, or mutate shared resources, then adding them blindly to deploy creates a new failure mode: deploys fail intermittently on test flake or, worse, partially deploy and then fail after making changes. “Rollback = revert one file” is not an operational rollback if the script has already applied prior steps. You need to specify whether these tests are pre-deploy, post-deploy verification, or staging-only, and what happens when they fail after stateful steps have already run.

2. [ASSUMPTION] [MATERIAL]: Gap 2 claims “fail-closed” when `GRANOLA_OWNER_EMAILS` is empty, but that is only safe if all callers correctly handle an empty verified set and do not fall back again, bypass checks, or degrade UX into manual overrides that operators start ignoring. You’re also assuming Granola cache schema stability (`creator.email`, `attendees[].email`) without versioning or parse guards. If the cache format changes, this path may silently return empty or partial results and create hard-to-debug production behavior. The safer path you did not fully evaluate is removing or feature-flagging the direct-parse fallback entirely rather than adding more logic to an already risky bypass path.

3. [ALTERNATIVE] [MATERIAL]: For Gap 2, the better operational option may be to disable draft eligibility when `verified_emails_cache` is empty/stale instead of parsing local Granola cache at all. Your proposal preserves a hidden second source of truth with separate filtering logic, which increases maintenance burden and creates divergence risk between MCP-populated cache behavior and local parse behavior. That means more on-call complexity when someone asks why an address was available in one mode but not another. If compliance is the driver, a hard failure with explicit remediation (“run email-cache-refresh”) is more auditable and easier to reason about than a fallback path.

4. [UNDER-ENGINEERED] [ADVISORY]: Gap 1’s “adds ~30s to deploy” is asserted, not demonstrated. If `tests/run_all.sh` already includes pytest plus contract tests, deploy time variance under CI load, cold caches, or degraded dependencies could be much worse. That matters operationally because slower deploys increase contention, operator retries, and timeout tuning. At minimum, you need timing data and a decision on whether deploy scripts are still acceptable for interactive use.

5. [OVER-ENGINEERED] [ADVISORY]: Gap 3 adds a Claude-specific PostToolUse hook to compensate for a stale-content workflow issue, but that only covers edits made through that toolchain. It does nothing for direct git edits, IDE changes, rebases, or automated modifications. So you’re adding configuration complexity without materially improving enforcement coverage. A git pre-commit/pre-push warning, CI check on changed `SKILL.md`, or serving skills directly from source would be more universal and operationally reliable.

6. [RISK] [MATERIAL]: The SKILL.md warning hook has no state tracking, so it won’t actually tell you whether `deploy_skills.sh` has been run after the most recent change. In practice this becomes noisy advice that can be ignored, which is exactly the failure pattern you’re trying to fix. Worse, if you later escalate to auto-deploy in a hook, you introduce race conditions, repeated deploys on incremental edits, and non-obvious local side effects. You need a real freshness check—e.g., compare SKILL.md mtimes or content hashes against deployed artifacts—before choosing reminder vs enforcement.

## Concessions
- Wiring existing contract tests into the deploy path is directionally correct; the current gap is real.
- The Granola fallback path is a legitimate compliance concern and should not remain unfiltered.
- The proposal keeps changes small and rollback conceptually simple at the code-diff level.

## Verdict
REVISE — the fixes are plausible, but the proposal underestimates deployment/test failure modes, preserves a risky fallback architecture, and offers weak enforcement for stale SKILL content without a reliable freshness signal.

---

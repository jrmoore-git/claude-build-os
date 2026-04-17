# Current State — 2026-04-16 (bundle-1 + bundle-2 + sanitizer fix; security blocker carried over)

## What Changed This Session
- **Bundle-1 shipped (4 commits):** structural review gate hook (`hooks/hook-post-build-review.py` — PostToolUse edit counter + re-fires `/review` reminder every 5 edits past threshold) + intent-router flag-read; hook-class tagging for all 23 hooks (advisory/enforcement-low/enforcement-high) + `docs/reference/hook-pruning-rubric.md` + 30-session-AND-28-day maturity gate in `scripts/session_telemetry_query.py`; `/review` dismissed-findings convention in `.claude/rules/review-protocol.md`. Closed L25.
- **Foundational fix for Opus 4.7 `temperature` deprecation (750fe9b):** replaced scattered per-site checks with `MODEL_DEPRECATED_PARAMS` table + `_sanitize_llm_kwargs()` in `scripts/llm_client.py`. All 4 dispatch paths route through it. Contract test `test_all_llm_paths_route_through_sanitizer` prevents recurrence. `/review` with Opus 4.7 challengers works again.
- **Bundle-2 shipped (4 commits):** Essential Eight line in CLAUDE.md replaced with 5 applicable invariants (no strike-throughs); anti-slop promoted from prose rule to `hooks/pre-commit-banned-terms.sh` with evidence-based list (10 words + 2 phrases, per `tasks/llm-slop-vocabulary-research.md` Perplexity research, POSIX-portable via `[[:space:]]+`); `tests/test_setup_tier_install.py` drift detector.
- **Installed `.git/hooks/pre-commit` symlink** after bundle-2 QA discovered the anti-slop hook wasn't actually firing on commits (captured as L41).
- Updated `tasks/lessons.md` (L25 + L40 promoted, added L41 + L42) and `tasks/decisions.md` (D26, D27).
- 10 commits total, 957 tests passing (was 923 pre-session), 34 new tests added.

## Current Blockers
- **SECURITY (CARRYOVER, NOT RESOLVED THIS SESSION): rotate `ANTHROPIC_API_KEY` and `LITELLM_MASTER_KEY`** — both leaked into the assistant transcript via a `cat ~/.zprofile` ssh command in an earlier parallel session today. If transcripts are logged/synced anywhere shared, treat as exposed. This session did not touch the rotation work.

## Next Action
**First:** rotate the two leaked keys (Anthropic console + macmini `~/.zprofile` + macmini `~/openclaw/config/litellm.env`), then restart `litellm-proxy` container so it picks up the new `LITELLM_MASTER_KEY`. **Then:** normal work can resume — next session should start with `/start`. If the framework is ever cloned to a new machine, `ln -sf ../../hooks/pre-commit-banned-terms.sh .git/hooks/pre-commit` must be run once (L41 captures this gap).

## Recent Commits
fde8fa3 Apply review fixes to bundle-2: POSIX portability + framing
b1a5ca4 tests: tier-install drift detection for /setup (#4)
34cdf42 Promote anti-slop from advisory rule to pre-commit hook (#6)

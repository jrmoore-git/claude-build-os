# Handoff — 2026-04-16 (buildos-improvements bundles 1+2 + sanitizer fix)

## Session Focus
Shipped the 7-item BuildOS improvements proposal as two bundles, plus a foundational fix for Opus 4.7 `temperature` deprecation that was silently failing cross-model `/review` calls through the `_sdk_tool_call` path.

## Decided
- **D26** — BuildOS improvements ships as 2 bundles. Bundle-1 closes L25 (structural review gate + hook-class rubric + review convention). Bundle-2 handles hygiene (Essential Eight cleanup + anti-slop hook promotion + tier-install test). #7 stays held as speculative.
- **D27** — LLM param deprecations centralize via `MODEL_DEPRECATED_PARAMS` capability table + `_sanitize_llm_kwargs()`. Contract test enforces all dispatch paths route through it. Supersedes ad-hoc per-site `if model == "..."` checks that left 2 of 4 paths unpatched.
- Anti-slop list was *tightened* not deleted — user pushed back on the "delete" recommendation; correct enforcement-ladder move is promote (rule → hook), not demote. Evidence-based list via Perplexity research (`tasks/llm-slop-vocabulary-research.md`).

## Implemented
- **10 commits:** 4 bundle-1 (`4ba6912`, `62e317b`, `6a3fb0b`, `e60e35b`), 1 foundational (`750fe9b`), 4 bundle-2 (`8a0130c`, `34cdf42`, `b1a5ca4`, `fde8fa3`).
- **New hook:** `hooks/hook-post-build-review.py` — advisory PostToolUse counter, re-fires `/review` reminder every 5 edits past threshold.
- **New doc:** `docs/reference/hook-pruning-rubric.md` — two-tier rubric + maturity gate (30 sessions AND 28 days).
- **New test files:** `tests/test_hook_post_build_review.py` (11 tests), `tests/test_setup_tier_install.py` (4 tests). Existing `tests/test_llm_client.py` gained 10 sanitizer unit tests + 1 contract test (grep-based regression-proof).
- **Hook enforcement installed:** `.git/hooks/pre-commit` symlinked to `hooks/pre-commit-banned-terms.sh`. Verified firing on real `git commit` with slop content.
- **Governance:** L25 + L40 promoted to rules/hooks, L41 (hook install gap) + L42 (sanitizer pattern) added, D26 + D27 recorded.
- 957 tests passing (up from 923 pre-session).

## NOT Finished
- **Security rotation (CARRYOVER from earlier parallel session today):** `ANTHROPIC_API_KEY` and `LITELLM_MASTER_KEY` leaked via `cat ~/.zprofile` over ssh. Still not rotated. This session did not touch it.
- Anti-slop hook requires manual `ln -sf ../../hooks/pre-commit-banned-terms.sh .git/hooks/pre-commit` on fresh clones (L41 captures this gap). Could wire into `setup.sh` in a future bundle.
- `#7` (model-tier-aware hook activation) still speculative and held per original plan.
- Hook-rule slop-list sync has no drift test (advisory-deferred from bundle-2 review).

## Next Session Should
1. **Rotate the two leaked API keys** (Anthropic console + macmini `~/.zprofile` + macmini `~/openclaw/config/litellm.env`) and restart the `litellm-proxy` container. Don't do other work until this is resolved.
2. Then `/start` normally — current-state is accurate, handoff is fresh.
3. Optional next bundle: wire the pre-commit symlink into `setup.sh` (would close L41) + add a hook-rule sync test (~10 lines).

## Key Files Changed
- `hooks/hook-post-build-review.py` (new), `hooks/pre-commit-banned-terms.sh` (SLOP_PATTERN + SLOP_PHRASES), `hooks/hook-intent-router.py` (flag read), 22 existing hook files (class tags)
- `scripts/llm_client.py` (MODEL_DEPRECATED_PARAMS + sanitizer + 4 dispatch paths), `scripts/session_telemetry_query.py` (class column + prune-candidates + maturity gate)
- `.claude/settings.json` (registered new hook), `.claude/rules/code-quality.md` (tightened anti-slop list), `.claude/rules/review-protocol.md` (negative-examples section), `.claude/skills/review/SKILL.md` (dismissal reminder)
- `CLAUDE.md` (Essential Eight rewrite)
- `docs/reference/hook-pruning-rubric.md` (new)
- `tests/test_hook_post_build_review.py` (new), `tests/test_setup_tier_install.py` (new), `tests/test_llm_client.py` (+ sanitizer tests)
- `tasks/lessons.md` (L25, L40 → Promoted; L41, L42 added), `tasks/decisions.md` (D26, D27)

## Doc Hygiene Warnings
- None. Lessons + decisions updated inline with the wrap. 13 untracked governance artifacts in `tasks/` (proposal/challenge/findings/judgment/enriched/plans/reviews/QA per bundle + slop-vocabulary research) committed with this wrap.

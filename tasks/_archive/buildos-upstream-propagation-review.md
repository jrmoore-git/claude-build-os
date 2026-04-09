---
topic: buildos-upstream-propagation
review_tier: cross-model
status: passed
git_head: a9e36a7
producer: claude-opus-4-6
created_at: 2026-03-30T13:38:00-0700
scope: .claude/rules/*.md, .claude/skills/*/SKILL.md, scripts/*.py, scripts/buildos-sync.sh
findings_count: 0
spec_compliance: false
---

# BuildOS Upstream Propagation — Review (v2)

## Cross-Model Panel

3 reviewers (Gemini 3.1 Pro x2, GPT-5.4) reviewed the full diff (25 framework files).

## Findings

### Fixed (from this review)

1. **[MATERIAL] `nicole_filter` leak in tier_classify.py** (Reviewers A, C) — Project-specific reference in TIER1_PATTERNS, EXEMPT_PATTERNS, and classify_file(). Removed all 3 references. Also reset CORE_SKILLS to empty placeholder.

2. **[MATERIAL] `PROJECT_ROOT` crash outside git repo** (All 3 reviewers) — `subprocess.check_output` at import time crashes in non-git contexts. Wrapped in try/except with fallback to `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` in all 5 scripts (debate.py, tier_classify.py, artifact_check.py, finding_tracker.py, enrich_context.py).

3. **[MATERIAL] Sync script no auto-revert on second scan failure** (Reviewer B) — If banned-terms found after copy, script now runs `git checkout -- $file` for each copied file before exiting.

4. **[BONUS] "Nicole" in wrap-session example text** (caught during fix verification) — Changed example from "Nicole slack skill" to "notification skill". Also added `Nicole|Meaghan|Granola|nicole_filter` to banned-terms pattern.

### Dismissed

5. **Skills removed `cd` to project root** (Reviewers A, C) — Claude Code always executes skills from the project root directory. The absolute `cd` was redundant. Not a functional regression.

6. **`python3` vs `python3.11` direction** (Reviewer B) — Skills correctly generalized from `/opt/homebrew/bin/python3.11` to bare `python3` for upstream portability. Downstream overrides via project config.

7. **design-review auth flow generalized** (Reviewer B) — Removing project-specific `#token=<token>` URL is correct for upstream. Downstream projects configure their own auth.

### Advisory (not blocking)

8. `app/` as frontend root convention — acceptable for v1, documented in README.
9. `docs/.*PRD` broader regex — acceptable, unlikely false matches.
10. Banned-terms blocklist is brittle — agree long-term, but adequate for current scope. Future: consider gitleaks/trufflehog.
11. `BUILDOS_DIR` not validated — low risk, local-only operation.

## Evidence

- Banned-terms scan: PASSED (25 files, 0 matches)
- All 4 material findings fixed and verified
- `nicole_filter` grep: 0 matches across all manifest files
- `PROJECT_ROOT` pattern: all 5 scripts have try/except fallback
- Sync script revert: implemented with `git checkout -- $file` fallback

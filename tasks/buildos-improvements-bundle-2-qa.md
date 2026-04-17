---
topic: buildos-improvements-bundle-2
qa_result: go
git_head: fde8fa3
producer: claude-opus-4-7
created_at: 2026-04-16T23:25:00-07:00
commits_scoped: [8a0130c, 34cdf42, b1a5ca4, fde8fa3]
hook_installed: true
---

# QA — buildos-improvements-bundle-2

**Result: go (1 environmental advisory)**

All 5 dimensions PASS. 957 tests green. Bundle-2 is doc/config/test-only (no new .py/.sh beyond the test) so test-coverage dimension reduces to validating the new test file itself. Hook installation gap caught during QA and resolved.

## 5-Dimension Results

- [x] **Test coverage:** No new production scripts to cover. The new test file (`tests/test_setup_tier_install.py`) has 4 drift-detection assertions, all passing. Hook smoke-tested: slop blocks, clean text passes, phrase blocks, dropped words pass.

- [x] **Regression risk:** Zero function signature changes in existing code. All new `def`s are in the new test file. CLAUDE.md edit is a single line. code-quality.md edit is an entire section rewrite (additive + reclassification, no semantic regression). Hook additions are additive patterns inside the existing scan loop.

- [x] **Plan compliance:** All 4 files touched are in `allowed_paths` (CLAUDE.md, .claude/rules/code-quality.md, hooks/pre-commit-banned-terms.sh, tests/test_setup_tier_install.py). No scope creep.

- [x] **Negative tests:** Hook blocks slop words ✓, blocks slop phrases ✓, allows dropped words (`robust`, `comprehensive`, `nuanced`, `crucial`, `leverage`, `facilitate`, `utilize`, `streamline`) ✓. Tier-install test covers structural drift in 4 scenarios; explicitly documents scope-out for tier-membership drift.

- [x] **Integration:** `.git/hooks/pre-commit` symlink installed during QA (see advisory below). Live commit with slop content blocked end-to-end — hook fires on real `git commit`. Rule file references the hook path (hook-rule linkage established). pytest discovers the new test file automatically.

## Environmental advisory (resolved during QA)

**Finding:** `.git/hooks/pre-commit` symlink was not installed at QA start. The hook file existed and ran correctly when invoked as `bash hooks/pre-commit-banned-terms.sh`, but git's pre-commit chain wasn't wired to it. All bundle-1 and bundle-2 commits this session succeeded without the hook firing — the enforcement was not active.

**Root cause:** `.git/hooks/` is not under version control (per-developer state). The hook's file header documents the install step (`ln -sf ../../hooks/pre-commit-banned-terms.sh .git/hooks/pre-commit`) but the step is manual.

**Fixed during QA:** symlink installed. Verified the hook now blocks real commits containing slop.

**Remaining gap:** fresh clones still need manual install. This is a framework-setup concern, not a bundle-2 regression. Deferred to a future bundle: either (a) add to setup.sh's install path, or (b) add a runtime check that warns when an enforcement hook's symlink is missing. Challenger B flagged this during `/review`; classified as out-of-scope-advisory in the review artifact.

## Tests

```
PASS: tests/test_setup_tier_install.py (4 passed in 0.02s)
PASS: full suite (957 passed in 15.32s)
PASS: hook smoke — slop words block, phrases block, dropped words pass, clean text passes
PASS: real git commit — hook installed and firing
```

## Session totals

- **Pre-session tests:** 923
- **Post-session tests:** 957 (+34 across bundles 1 and 2 + sanitizer contract tests)
- **Commits this session:** 10
  - Bundle 1: `4ba6912`, `62e317b`, `6a3fb0b`, `e60e35b`
  - Out-of-bundle (llm_client): `750fe9b`
  - Bundle 2: `8a0130c`, `34cdf42`, `b1a5ca4`, `fde8fa3` (review fixes)
  - QA this run: hook install (local state, not a commit)

## Next

Bundle-2 is done. Full session ready for `/wrap`.

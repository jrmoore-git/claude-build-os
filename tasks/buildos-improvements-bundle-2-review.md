---
topic: buildos-improvements-bundle-2
review_tier: cross-model
status: revise
git_head: b1a5ca4
producer: claude-opus-4-7
created_at: 2026-04-16T23:15:00-07:00
scope: "CLAUDE.md, .claude/rules/code-quality.md, hooks/pre-commit-banned-terms.sh, tests/test_setup_tier_install.py"
challengers_reached: 3
findings_count: 2
spec_compliance: true
spec_artifacts: [tasks/buildos-improvements-bundle-2-plan.md, tasks/buildos-improvements-challenge.md, tasks/llm-slop-vocabulary-research.md]
---

# Review — buildos-improvements-bundle-2

**Verdict: REVISE — 2 MATERIAL, 6 ADVISORY**

3 of 3 challengers reached (Opus 4.7 now works via the foundational sanitizer fix). Highest-signal finding: **unanimous MATERIAL** on `\s+` regex portability in the new SLOP_PHRASES pattern.

| Lens | Material | Advisory |
|---|---|---|
| PM | 1 | 3 |
| Security | 1 | 3 |
| Architecture | 0 | 2 |

## PM / Acceptance

- **[MATERIAL] Tier-install test has a documented-but-unaddressed scope gap: Tier-1↔Tier-2 moves not detected.** Challengers A and B both caught this. C disagreed (interpreted scope narrowly). The test asserts "declared files have templates" and "templates are declared in some tier" — but a file moved between tiers silently satisfies both. **Fix** (trivial, ≤5 lines): narrow the test file docstring to state the actual contract ("declared↔template existence drift; does NOT detect tier-membership changes"). Expanding scope to catch tier-moves would need an `expected_tier` manifest — rejected as over-engineering for single-developer framework.

- **[ADVISORY] "Evidence-based" framing slightly overstates research support for `seamless`.** Research classifies `seamless` as MODERATE, not STRONG. Rule text says "first 5 have direct research evidence" — accurate would be "first 4 strong + seamless moderate." 1-line text fix.

- **[ADVISORY] `docs/contract-tests.md` may conflict with Essential Eight rewrite.** Challenger B notes: that doc says "eight invariants apply regardless." Not in bundle-2 scope; flagged for a future doc-sync. Out of scope, not blocking.

- **[ADVISORY] `seamless` classification caveat.** Same finding as above from a different angle. Already covered.

## Security

- **[MATERIAL] SPEC VIOLATION: `\s+` in SLOP_PHRASES is not POSIX-portable regex.** Unanimous across all 3 challengers. On strict POSIX ERE (BSD grep without GNU extensions), `\s` matches literal `s` not whitespace. Current macOS grep happens to support it as a GNU extension (verified), but contributors on stricter environments will get silent false-negatives on the 2 banned phrases. **Fix** (trivial, ~2 lines): replace `\s+` with `[[:space:]]+` in the SLOP_PHRASES constant. `\b` has the same concern but challengers A and B note it works on all real-world grep implementations in `-E` mode — keeping as-is with a comment.

- **[ADVISORY] Hook bypass via `git commit --no-verify`.** Acceptable under single-developer threat model. Same property as every pre-commit hook. Not a regression.

- **[ADVISORY] Skip-list doesn't cover `templates/` or nested `tasks/*/` dirs.** Templates currently contain no slop; nested tasks dirs don't exist. Future-usability concern; noted for bundle-3 if tripped.

## Architecture

- **[ADVISORY] Test parser is format-sensitive to SKILL.md layout.** If setup skill ever adds a non-tier `### Something` subsection between tier headings, bullets get misattributed. Low-probability; test is a drift detector, not a parser. Documented in the test's own docstring would suffice.

- **[ADVISORY] Hook-rule sync is drift-prone.** Rule file lists 10 words, hook has them as SLOP_PATTERN — no test asserting the two match. ~10-line test could assert `set(words_in_rule) == set(words_in_hook)`. Worth adding in a follow-up; not a regression since this was never tested.

## Dismissed claims (with rationale)

- **Tier-install test does not cover Tier 0** (B). Tier 0 creates no files. An empty-list assertion tells us nothing useful. Keeping test's implicit "Tier 0 = no files" contract via the absence of a tier0 test function; documenting in docstring as part of the MATERIAL fix.
- **Real pre-commit integration not tested** (B). The hook has a documented install step (`ln -sf ...`). Adding an install test is a separate concern — would verify framework setup, not bundle-2's scope.
- **Add hook-rule sync test** (A). Fair advisory, but out of scope for a 3-commit hygiene bundle. Queued for future.
- **Verification smoke test in plan is fragile** (A, re: `/tmp` path). Plan text is inaccurate; actual smoke test used an in-repo dir and worked. Plan typo, not a code bug.

## Inline fixes to apply (before marking status: passed)

1. `hooks/pre-commit-banned-terms.sh` — `\s+` → `[[:space:]]+` in SLOP_PHRASES
2. `.claude/rules/code-quality.md` — "first 5 have direct research evidence" → "first 4 have strong research evidence; `seamless` is moderate"
3. `tests/test_setup_tier_install.py` — narrow docstring to state the actual contract (existence drift, not tier-membership drift)

All three fixes are ≤5 lines each. None require new abstractions. Meets PROCEED-WITH-FIXES criteria (MATERIAL findings with trivial inline fixes).

## Next action

Apply fixes → re-verify with `bash hooks/pre-commit-banned-terms.sh` + `pytest tests/` → `/review --qa`.

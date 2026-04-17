---
topic: debate-frontmatter
qa_result: go
git_head: 4996223
producer: claude-opus-4-7
created_at: 2026-04-16T20:50:22-0700
---

# QA: debate-frontmatter migration

5-dimension validation of the in-progress diff against
`tasks/debate-frontmatter-plan.md`. Pre-commit (HEAD = 4996223 baseline).

## Dimensions

- [x] **Test coverage:** Existing tests cover all 4 migrated functions and 4
      constants; they were retargeted from `debate.X` to `debate_common.X` in
      the same diff. `test_debate_pure.py` (5 _build_frontmatter + 8
      _redact_author + 7 _shuffle_challenger_sections), `test_debate_utils.py`
      (10 refs), `test_debate_posture_floor.py` (~32 refs across
      _apply_posture_floor + SECURITY_FLOOR_*), `test_debate_commands.py` (1
      ref). No new untested code paths added — pure verbatim move.
- [x] **Regression risk:** Function signatures unchanged (`git diff` -def/+def
      pairs identical for all 4 functions). All 9 internal call sites + 6
      `CHALLENGER_LABELS` reads in debate.py retargeted. Sole sibling caller
      (`debate_verdict.py:82`) retargeted. Negative invariant verified:
      `hasattr(debate, sym)` is False for all 8 migrated symbols.
- [x] **Plan compliance:** `git diff --stat` shows exactly the 7 files
      enumerated in `surfaces_affected`. No extras, no omissions:
      `scripts/debate.py`, `scripts/debate_common.py`, `scripts/debate_verdict.py`,
      `tests/test_debate_pure.py`, `tests/test_debate_posture_floor.py`,
      `tests/test_debate_utils.py`, `tests/test_debate_commands.py`. Two
      untracked plan files (`debate-frontmatter-plan.md`, `session-telemetry-plan.md`)
      are out of scope; only the former belongs to this commit.
- [x] **Negative tests:** Existing test files cover the well-documented edge
      cases for each migrated function:
      `test_debate_pure.py` covers `_redact_author` no-frontmatter / mid-document /
      author-absent cases; `_build_frontmatter` empty mapping / extras / formatting
      cases; `_shuffle_challenger_sections` single-section / determinism cases.
      `test_debate_posture_floor.py` covers all 16 SECURITY_FLOOR_PATTERNS plus
      above-floor / no-match / case-sensitivity edge cases. No new error paths
      introduced by this commit.
- [x] **Integration:** `python3.11 scripts/debate.py challenge --help` loads
      successfully. `import debate` clean. `debate_common` reachable from all
      sibling modules and tests; `tests/test_debate_posture_floor.py` had
      `import debate_common` added (was missing). No new shebangs or path
      additions required.

Tests: PASS (932 passed in 11.42s)

## Plan-compliance deviations
None. Single-purpose verbatim migration matches plan exactly.

## Verification artifacts (commands run)
```
bash tests/run_all.sh                                                 # 932 passed
grep -n 'def _apply_posture_floor|def _shuffle_challenger_sections|
        def _build_frontmatter|def _redact_author|^SECURITY_FLOOR_PATTERNS|
        ^SECURITY_FLOOR_MIN|^_SECURITY_FLOOR_RE|^CHALLENGER_LABELS' \
   scripts/debate.py                                                   # 0
grep -rn '\bdebate\.<each-symbol>\b' scripts/ tests/ hooks/            # 0
python3.11 -c "...hasattr negative invariant..."                       # OK
python3.11 scripts/debate.py challenge --help                          # CLI loads
```

## Net LOC delta
- `scripts/debate.py`: 3815 → 3684 (−131)
- `scripts/debate_common.py`: 338 → 471 (+133)
- Net: +2 LOC across both files (extra blank lines in `debate_common.py`'s
  section dividers — same pattern as prior 3 migrations)

## Verdict
**GO.** Single-purpose verbatim move with full test retargeting. Same pattern
as F4 (12a865b), `_load_config` (50a7fbd), `_log_debate_event` (170a3e6).
Per D25, `/challenge` skipped — parent `tasks/debate-common-challenge.md`
gates the architecture; this is mechanical execution of an F-list item.

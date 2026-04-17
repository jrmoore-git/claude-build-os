---
scope: "Migrate frontmatter helpers (_build_frontmatter, _redact_author, _apply_posture_floor, _shuffle_challenger_sections) + 4 supporting constants (SECURITY_FLOOR_PATTERNS, SECURITY_FLOOR_MIN, _SECURITY_FLOOR_RE, CHALLENGER_LABELS) from debate.py to debate_common.py. 9 internal function-call sites + 6 CHALLENGER_LABELS retargets in debate.py + 1 sibling (debate_verdict) + 4 test files (test_debate_pure ~20 refs, test_debate_posture_floor ~20 refs incl SECURITY_FLOOR_*, test_debate_utils 10 refs, test_debate_commands 1 ref)."
surfaces_affected: "scripts/debate_common.py, scripts/debate.py, scripts/debate_verdict.py, tests/test_debate_pure.py, tests/test_debate_posture_floor.py, tests/test_debate_utils.py, tests/test_debate_commands.py"
verification_commands: "bash tests/run_all.sh && grep -n 'def _apply_posture_floor\\|def _shuffle_challenger_sections\\|def _build_frontmatter\\|def _redact_author\\|^SECURITY_FLOOR_PATTERNS\\|^SECURITY_FLOOR_MIN\\|^_SECURITY_FLOOR_RE\\|^CHALLENGER_LABELS' scripts/debate.py && grep -rn '\\bdebate\\._build_frontmatter\\b\\|\\bdebate\\._redact_author\\b\\|\\bdebate\\._apply_posture_floor\\b\\|\\bdebate\\._shuffle_challenger_sections\\b\\|\\bdebate\\.SECURITY_FLOOR_MIN\\b\\|\\bdebate\\.SECURITY_FLOOR_PATTERNS\\b\\|\\bdebate\\._SECURITY_FLOOR_RE\\b\\|\\bdebate\\.CHALLENGER_LABELS\\b' scripts/ tests/ hooks/"
rollback: "git revert <sha> — single atomic commit, no schema/infra/data state changes"
review_tier: "Tier 1.5"
verification_evidence: "PENDING"
challenge_artifact: "tasks/debate-common-challenge.md (parent: per F-list under D25 architectural pattern)"
challenge_recommendation: "PROCEED (mechanical move per established F4/load-config/log-event pattern; no new abstractions)"
---
# Plan: Frontmatter Helpers + Posture-Floor Migration

Per D25 + parent `tasks/debate-common-challenge.md` F-list. Same pattern as F4
(commit 12a865b), `_load_config` (50a7fbd), and `_log_debate_event` (170a3e6).

## What moves

The 4 named functions pull 4 supporting constants with them. CHALLENGER_LABELS
must move because keeping it in `debate.py` while `_shuffle_challenger_sections`
moves to `debate_common.py` would create a backward `debate_common → debate`
layering edge.

| Symbol | Type | debate.py line | Why |
|---|---|---|---|
| `SECURITY_FLOOR_PATTERNS` | list | 461 | Used only by `_SECURITY_FLOOR_RE` + `test_debate_posture_floor.py:150` |
| `SECURITY_FLOOR_MIN` | int=3 | 469 | Used by `_apply_posture_floor` + 18 test refs |
| `_SECURITY_FLOOR_RE` | compiled regex | 472 | Used by `_apply_posture_floor` + `test_debate_posture_floor.py:153` |
| `_apply_posture_floor` | function | 477 | named symbol |
| `CHALLENGER_LABELS` | list (`string.ascii_uppercase`) | 494 | Used by `_shuffle_challenger_sections` (line 537) **and** 6 cmd_* callers in debate.py |
| `_shuffle_challenger_sections` | function | 497 | named symbol |
| `_build_frontmatter` | function | 826 | named symbol — already calls `debate_common.PROJECT_TZ` (becomes intra-module after move) |
| `_redact_author` | function | 844 | named symbol |

## Lessons applied (this session's L40-candidate work)

- **Whole-identifier patterns:** Pre-flight grep used `\bdebate\.<sym>\b` for all
  8 symbols across `scripts/`, `tests/`, `hooks/`. Result: 1 sibling
  (`debate_verdict.py:82`) + 50+ test refs across 4 files. No surprises.
- **Substring-prefix trap (L40 candidate):** Verified no `CHALLENGER_LABELS_*`
  variants exist. `SECURITY_FLOOR_MIN` and `SECURITY_FLOOR_PATTERNS` similarly
  have no suffix-extension variants. Word-boundary defeat (the `170a3e6`
  near-miss with `DEFAULT_LOG_PATH` followed by `_`) is not in scope here.
- **Monkeypatch form:** Searched
  `monkeypatch\.setattr.*debate.*<sym>` and `setattr\(debate.*<sym>` for all 8
  symbols across `tests/`. **0 hits.** All test references are pure attribute
  reads.
- **`sys.modules` hygiene (L39 boundary):** Confirmed none of the 4 target test
  files manipulates `sys.modules`. The previously-removed cargo-cult globs
  (commit c993edf) covered the only at-risk files.

## Build Order

| # | Step | Files | Verification |
|---|---|---|---|
| 0 | Pre-flight: clean tree, baseline test pass | — | `git status --short` clean; `bash tests/run_all.sh` 932/932 |
| 1 | Add `SECURITY_FLOOR_PATTERNS`, `SECURITY_FLOOR_MIN`, `_SECURITY_FLOOR_RE`, `CHALLENGER_LABELS` + the 4 functions to `debate_common.py`. Add top-level imports `re`, `string`. Inside `_build_frontmatter`, the body becomes bare `PROJECT_TZ` (intra-module — drop the `debate_common.` prefix). Inside `_apply_posture_floor`, collapse `import re as _re` and use the top-level `re`. Keep `_shuffle_challenger_sections`'s lazy `import random` as-is. | `scripts/debate_common.py` | Module loads; `python3.11 -c "import sys; sys.path.insert(0,'scripts'); import debate_common as dc; assert callable(dc._build_frontmatter); assert callable(dc._redact_author); assert callable(dc._apply_posture_floor); assert callable(dc._shuffle_challenger_sections); assert dc.SECURITY_FLOOR_MIN == 3; assert dc.CHALLENGER_LABELS[0] == 'A'; print('OK')"` |
| 2 | In `debate.py`: delete the 8 symbols. Retarget 9 internal function-call sites (lines 937, 956, 1147, 1361, 1368, 1568, 1585, 1638, 3022) to `debate_common.X`. Retarget 6 `CHALLENGER_LABELS` reads (lines 1030, 1034, 1121, 3211, 3225, 3452) to `debate_common.CHALLENGER_LABELS`. Drop the `import re as _re` line if no longer used. | `scripts/debate.py` | Suite passes; `grep -n 'def _apply_posture_floor\|def _shuffle_challenger_sections\|def _build_frontmatter\|def _redact_author\|^SECURITY_FLOOR_PATTERNS\|^SECURITY_FLOOR_MIN\|^_SECURITY_FLOOR_RE\|^CHALLENGER_LABELS' scripts/debate.py` returns 0 |
| 3 | In `debate_verdict.py`: rename `debate._build_frontmatter` → `debate_common._build_frontmatter` at line 82. Add `import debate_common` if absent. | `scripts/debate_verdict.py` | `grep -n 'debate\._build_frontmatter' scripts/` returns 0 |
| 4 | In each of 4 test files: add `import debate_common` if absent. Retarget `debate.X` → `debate_common.X` for all 8 symbols. Counts: `test_debate_pure.py` ~20 refs (5 `_build_frontmatter`, 8 `_redact_author`, 7 `_shuffle_challenger_sections`); `test_debate_posture_floor.py` ~20 refs (`_apply_posture_floor` + `SECURITY_FLOOR_*` + `_SECURITY_FLOOR_RE`); `test_debate_utils.py` 10 refs (2+5+3); `test_debate_commands.py` 1 ref (line 365 `SECURITY_FLOOR_MIN`). | `tests/test_debate_pure.py`, `tests/test_debate_posture_floor.py`, `tests/test_debate_utils.py`, `tests/test_debate_commands.py` | Suite passes |
| 5 | Verification battery: full grep + hasattr negative invariant + CLI smoke | (all above) | All commands clean |
| 6 | Commit (plan + QA artifact + edits) | tasks/debate-frontmatter-{plan,qa}.md | `git status --short` clean save audit log |

## Files

| File | Op | Scope |
|---|---|---|
| `scripts/debate_common.py` | MODIFY | +8 symbols + 2 imports (`re`, `string`). +~80 LOC. ~338 → ~418. |
| `scripts/debate.py` | MODIFY | −8 symbols + 15 retargets (9 function calls + 6 CHALLENGER_LABELS). Net ~−65 LOC. ~3815 → ~3750. |
| `scripts/debate_verdict.py` | MODIFY | 1 retarget + import (if absent) |
| `tests/test_debate_pure.py` | MODIFY | ~20 retargets + import |
| `tests/test_debate_posture_floor.py` | MODIFY | ~20 retargets + import |
| `tests/test_debate_utils.py` | MODIFY | 10 retargets + import |
| `tests/test_debate_commands.py` | MODIFY | 1 retarget |

## Execution Strategy

**Decision:** sequential
**Pattern:** pipeline
**Reason:** Each step depends on the previous: cannot retarget `debate.py`
internals (Step 2) before `debate_common.py` exposes the symbols (Step 1);
cannot retarget siblings (Step 3) or tests (Step 4) before deletion completes.
Single component, no fan-out — files share too much state for parallel agents
to be net-positive (same reasoning as the prior 3 migrations).

## Verification

```bash
# 1. Full suite
bash tests/run_all.sh
# expect: 932 passed

# 2. Symbols deleted from debate.py
grep -n 'def _apply_posture_floor\|def _shuffle_challenger_sections\|def _build_frontmatter\|def _redact_author\|^SECURITY_FLOOR_PATTERNS\|^SECURITY_FLOOR_MIN\|^_SECURITY_FLOOR_RE\|^CHALLENGER_LABELS' scripts/debate.py
# expect: 0 matches

# 3. No dangling debate.X references to migrated symbols
grep -rn '\bdebate\._build_frontmatter\b\|\bdebate\._redact_author\b\|\bdebate\._apply_posture_floor\b\|\bdebate\._shuffle_challenger_sections\b\|\bdebate\.SECURITY_FLOOR_MIN\b\|\bdebate\.SECURITY_FLOOR_PATTERNS\b\|\bdebate\._SECURITY_FLOOR_RE\b\|\bdebate\.CHALLENGER_LABELS\b' scripts/ tests/ hooks/
# expect: 0 matches

# 4. Negative invariant — debate has no shadow symbols
python3.11 -c "
import sys; sys.path.insert(0,'scripts')
import debate
for sym in ['_build_frontmatter','_redact_author','_apply_posture_floor','_shuffle_challenger_sections','SECURITY_FLOOR_MIN','SECURITY_FLOOR_PATTERNS','_SECURITY_FLOOR_RE','CHALLENGER_LABELS']:
    assert not hasattr(debate, sym), f'FAIL: debate.{sym} still exists'
print('OK')
"

# 5. debate_common loads cleanly
python3.11 -c "
import sys; sys.path.insert(0,'scripts')
import debate_common as dc
assert callable(dc._build_frontmatter)
assert callable(dc._redact_author)
assert callable(dc._apply_posture_floor)
assert callable(dc._shuffle_challenger_sections)
assert dc.SECURITY_FLOOR_MIN == 3
assert len(dc.SECURITY_FLOOR_PATTERNS) > 0
assert dc._SECURITY_FLOOR_RE is not None
assert dc.CHALLENGER_LABELS[0] == 'A'
print('OK')
"

# 6. CLI smoke
python3.11 scripts/debate.py challenge --help > /dev/null && echo "CLI loads"
```

## Rollback

`git revert HEAD` — single atomic commit, file content only, no schema/infra/data state changes.

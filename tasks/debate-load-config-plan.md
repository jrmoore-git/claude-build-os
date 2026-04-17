---
scope: "Migrate config loader from debate.py to debate_common.py. Moves _load_config + 4 supporting constants (_DEFAULT_PERSONA_MODEL_MAP, _DEFAULT_JUDGE, _DEFAULT_REFINE_ROTATION, VALID_PERSONAS). Deletes vestigial PERSONA_MODEL_MAP alias (dead code — only its own definition + a help-string comment reference). Updates 9 internal debate.py call sites + 4 sibling modules + 9 test sites in 2 files."
surfaces_affected: "scripts/debate.py, scripts/debate_common.py, scripts/debate_explore.py, scripts/debate_compare.py, scripts/debate_verdict.py, scripts/debate_check_models.py, tests/test_debate_pure.py, tests/test_debate_smoke.py"
verification_commands: "bash tests/run_all.sh && grep -n 'def _load_config\\|^_DEFAULT_PERSONA_MODEL_MAP\\|^_DEFAULT_JUDGE\\|^_DEFAULT_REFINE_ROTATION\\|^VALID_PERSONAS\\|^PERSONA_MODEL_MAP' scripts/debate.py && grep -rn 'debate\\._load_config\\|debate\\._DEFAULT_PERSONA\\|debate\\._DEFAULT_JUDGE\\|debate\\._DEFAULT_REFINE_ROTATION\\|debate\\.VALID_PERSONAS' scripts/ tests/"
rollback: "git revert <sha> — single atomic commit, no schema/infra/data changes"
review_tier: "Tier 1.5"
verification_evidence: "932/932 tests pass; 0 defs in debate.py; 0 debate.X refs to migrated symbols across scripts/+tests/+hooks/; debate has no shadow symbols (hasattr check); _load_config end-to-end smoke pass; CLI loads; debate.py 3897→3834 (−63 LOC), debate_common.py 239→311 (+72 LOC); 1 missed test fixture caught + fixed mid-build (test_debate_commands.py:170 monkeypatch.setattr(debate, '_load_config'))"
challenge_artifact: "tasks/debate-common-challenge.md (parent: F4-style migration accepted under D25 architectural pattern)"
challenge_recommendation: "PROCEED (architectural decision in D25 + parent challenge already gates this work; no new abstractions, no new dependencies, mechanical move per established pattern)"
---
# Plan: `_load_config` Migration

Per D25 (debate.py refactor → package style with shared `debate_common.py`) and the
parent debate-common-challenge.md F-list. Same pattern as the F4 cost-tracking commit
(12a865b): mechanical move to `debate_common.py`, retarget all call sites in one commit.

## What moves

| Symbol | Type | Lines |
|---|---|---|
| `_DEFAULT_PERSONA_MODEL_MAP` | dict | 568-573 (approx) |
| `_DEFAULT_JUDGE` | str | 575 |
| `_DEFAULT_REFINE_ROTATION` | list | 576 |
| `VALID_PERSONAS` | set | 578 |
| `_load_config(config_path=None)` | function | 581-633 |

**Also deleted:** `PERSONA_MODEL_MAP = _DEFAULT_PERSONA_MODEL_MAP` (line 637) — dead-code
alias. Only references are its own definition and a help-string comment in argparse
description (line 3653 — that text reference stays, it's user-facing prose).

**Import style commitment** (per F3 of parent challenge): all call sites use
`debate_common.X` qualified, never `from debate_common import …`.

**Re-export prohibition** (per F3 of parent challenge): debate.py does NOT re-export
any of these symbols. All access goes through `debate_common.X`.

## Build Order

| # | Step | Files | Verification |
|---|---|---|---|
| 0 | Pre-flight: clean tree, baseline test pass | — | `git status --short` clean (only artifacts); `bash tests/run_all.sh` → 932 passed |
| 1 | Add 4 constants + `_load_config` to `debate_common.py`. Add `import json` if missing. Reuse existing `PROJECT_ROOT`. | `scripts/debate_common.py` | `python3.11 -c "import sys; sys.path.insert(0,'scripts'); import debate_common; assert callable(debate_common._load_config); assert isinstance(debate_common.VALID_PERSONAS, set); print('OK')"` |
| 2 | In `debate.py`: delete the 4 constants + function (lines 568-633) + dead alias (line 637). Replace 9 internal call sites of `_load_config()` with `debate_common._load_config()`. Lines: 1045, 1326, 1395, 1462, 1564, 1633, 2638, 3080, 3373. | `scripts/debate.py` | Suite passes; `grep -n 'def _load_config\|^_DEFAULT_PERSONA_MODEL_MAP\|^_DEFAULT_JUDGE\|^_DEFAULT_REFINE_ROTATION\|^VALID_PERSONAS\|^PERSONA_MODEL_MAP' scripts/debate.py` returns 0 |
| 3 | In each of 4 sibling modules: replace `debate._load_config()` with `debate_common._load_config()`. (`import debate_common` already present in all 4 from prior commits.) | `scripts/debate_explore.py:26`, `debate_compare.py:37`, `debate_verdict.py:44`, `debate_check_models.py:20` | Suite passes; `grep -n 'debate\._load_config' scripts/` returns 0 |
| 4 | In `tests/test_debate_pure.py`: rename 1 `debate._load_config` site (line 501-563 area, 7 invocations across multiple tests) and 8 `debate._DEFAULT_*` references. In `tests/test_debate_smoke.py`: rename 1 `debate._load_config()` site (line 79). `import debate_common` already present in test_debate_pure.py. Add it to test_debate_smoke.py. | `tests/test_debate_pure.py`, `tests/test_debate_smoke.py` | Suite passes; `grep -n 'debate\._load_config\|debate\._DEFAULT_' tests/` returns 0 |
| 5 | Final verification: full suite + all greps from frontmatter | (all above) | All clean |
| 6 | Commit | (above + plan artifact) | `git status --short` clean |

## Files

| File | Op | Scope |
|---|---|---|
| `scripts/debate_common.py` | MODIFY | Add 4 constants + `_load_config`. Add `import json` if missing. ~70 LOC added. |
| `scripts/debate.py` | MODIFY | Delete 4 constants + function + dead alias (lines 568-637). Update 9 internal call sites. Net ~−70 LOC. Will go ~3897 → ~3830 lines. |
| `scripts/debate_explore.py` | MODIFY | Update line 26: `debate._load_config()` → `debate_common._load_config()` |
| `scripts/debate_compare.py` | MODIFY | Update line 37 |
| `scripts/debate_verdict.py` | MODIFY | Update line 44 |
| `scripts/debate_check_models.py` | MODIFY | Update line 20 |
| `tests/test_debate_pure.py` | MODIFY | Rename 9 references (1 `_load_config` × 7 tests + 8 `_DEFAULT_*` references). Existing `import debate_common` works. |
| `tests/test_debate_smoke.py` | MODIFY | Add `import debate_common`; rename 1 `_load_config` site (line 79). |

## Execution Strategy

**Decision:** sequential
**Pattern:** pipeline
**Reason:** Same as F4 — Step 1 must add full implementation to debate_common before Step 2 deletes from debate.py (else 9 internal sites break). Step 3 sibling updates after Step 2. Step 4 test updates after Step 3. Single agent, no worktree. (No `components` field — 1 logical component.)

## Verification

```bash
# 1. Suite
bash tests/run_all.sh    # expect: 932 passed

# 2. Defs gone from debate.py
grep -n 'def _load_config\|^_DEFAULT_PERSONA_MODEL_MAP\|^_DEFAULT_JUDGE\|^_DEFAULT_REFINE_ROTATION\|^VALID_PERSONAS\|^PERSONA_MODEL_MAP' scripts/debate.py
# expect: 0

# 3. No call site uses debate.X for migrated symbols
grep -rn 'debate\._load_config\|debate\._DEFAULT_PERSONA\|debate\._DEFAULT_JUDGE\|debate\._DEFAULT_REFINE_ROTATION\|debate\.VALID_PERSONAS' scripts/ tests/
# expect: 0

# 4. debate_common loads cleanly
python3.11 -c "
import sys; sys.path.insert(0, 'scripts')
import debate_common
assert callable(debate_common._load_config)
assert isinstance(debate_common._DEFAULT_PERSONA_MODEL_MAP, dict)
assert isinstance(debate_common.VALID_PERSONAS, set)
cfg = debate_common._load_config()
assert 'persona_model_map' in cfg
assert 'judge_default' in cfg
print('OK')
"

# 5. debate has no shadow symbols
python3.11 -c "
import sys; sys.path.insert(0, 'scripts')
import debate
for sym in ['_load_config', '_DEFAULT_PERSONA_MODEL_MAP', '_DEFAULT_JUDGE', '_DEFAULT_REFINE_ROTATION', 'VALID_PERSONAS', 'PERSONA_MODEL_MAP']:
    assert not hasattr(debate, sym), f'FAIL: debate.{sym} still exists'
print('OK')
"

# 6. CLI loads
python3.11 scripts/debate.py challenge --help > /dev/null && echo OK
```

## Rollback

`git revert HEAD` — file content only, no schema/infra/data changes.

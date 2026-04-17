---
topic: debate-load-config
qa_result: go
git_head: cc7271d (will be updated post-commit)
producer: claude-opus-4-7
created_at: 2026-04-16T20:30:00-0700
---
# QA — `_load_config` Migration

## 5-Dimension Check

- [x] **Test coverage:** `test_debate_pure.py` exercises `_load_config` across 7 test cases (nonexistent file, malformed JSON, valid config, unknown persona filter, all-defaults fallback, partial config). `test_debate_smoke.py:test_load_config_includes_compare_default` smoke-tests the full path. `test_debate_commands.py` fixtures monkeypatch `_load_config` across many `cmd_*` test scenarios. All 22 invocations now point at `debate_common._load_config` and pass.
- [x] **Regression risk:** Zero signature changes (`_load_config(config_path=None)` unchanged). 9 internal debate.py call sites + 4 sibling sites + 8 test sites + 1 monkeypatch fixture all retargeted. Whole-repo grep for stale `debate.X` refs returns 0 across `scripts/`, `tests/`, and `hooks/`. The vestigial `PERSONA_MODEL_MAP` alias (only its own definition + a help-string comment referenced it) was removed safely.
- [x] **Plan compliance:** **One advisory deviation** — `tests/test_debate_commands.py` was added to scope mid-build (8 → 9 files). Reason: `monkeypatch.setattr(debate, "_load_config", ...)` at line 170 was not surfaced during plan-time scouting (I only grepped for `debate._load_config(` call form, missed the `setattr(debate, "_load_config", ...)` form). Caught immediately at test-run time (34 errors, all `AttributeError: ... has no attribute '_load_config'`), fixed in one Edit. Mechanical clarification, not scope creep — it's the same surface area, just a different grep pattern.
- [x] **Negative tests:** `test_debate_pure.py:501-565` covers: file not found (returns defaults), malformed JSON (returns defaults), valid config, unknown persona (filtered out), partial config keys (defaults filled). All exercise `debate_common._load_config` post-migration. 7 tests, all pass.
- [x] **Integration:** All access paths updated:
  1. Internal debate.py (9 sites — verified via grep)
  2. Sibling modules (4 — debate_explore:26, debate_compare:37, debate_verdict:44, debate_check_models:20)
  3. Test files (3 — test_debate_pure.py, test_debate_smoke.py, test_debate_commands.py)
  Hooks directory clean. CLI `debate.py challenge --help` loads cleanly. End-to-end smoke (`debate_common._load_config()` returns dict with all expected keys) passes.

## Tests

PASS — 932 passed in 11.48s. Smoke + run_all.sh + clean-scan all green.

## Verification Battery (from plan)

- `bash tests/run_all.sh` → 932 passed ✓
- `grep -n 'def _load_config|^_DEFAULT_*|^VALID_PERSONAS|^PERSONA_MODEL_MAP' scripts/debate.py` → 0 ✓
- `grep -rn 'debate\._load_config|debate\._DEFAULT_*|debate\.VALID_PERSONAS' scripts/ tests/ hooks/` → 0 ✓
- `hasattr(debate, <migrated symbol>)` → all False ✓
- `debate_common._load_config()` smoke → returns valid config dict ✓
- `debate.py challenge --help` → exit 0 ✓
- LOC: debate.py 3897→3834 (−63), debate_common.py 239→311 (+72) ✓

## Lesson Surfaced

**New lesson candidate (not yet logged):** Plan-time scouting must grep for BOTH the call form (`debate.X(`) AND the monkeypatch form (`setattr(debate, "X", ...)`, `monkeypatch.setattr(debate, "X", ...)`) when migrating a symbol that test fixtures may patch. Today's miss was caught by the test suite (correct guard), but pre-flight grep would have caught it without a re-run.

This refines L39 (sys.modules splits) with another boundary case: monkeypatch-by-string-name lookups don't show up in normal grep. Could be added as L40 if recurring; otherwise document inline in the next migration plan.

## Verdict: GO

- 932/932 passing
- Zero MATERIAL issues
- Plan compliance OK (one mid-build scope clarification, non-substantive)
- All verification commands clean
- Migration is mechanically identical to F4 (12a865b) — same pattern, same risk profile, same outcome

## Next

- `/ship` ready
- Or: continue to `_log_debate_event` migration (next single-purpose commit per the parent plan)

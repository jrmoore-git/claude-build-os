---
topic: debate-log-event
qa_result: go
producer: claude-opus-4-7
created_at: 2026-04-16T20:50:00-0700
---
# QA — `_log_debate_event` + `PROJECT_TZ` + `DEFAULT_LOG_PATH` Migration

## 5-Dimension Check

- [x] **Test coverage:** No dedicated unit tests for `_log_debate_event` (it's a side-effect function — append to JSONL). Coverage is via integration through every cmd_* test in `test_debate_commands.py` (each calls a `cmd_*` which logs an event; the `suppress_debate_log` fixture monkeypatches it to a no-op). All such fixtures retargeted to `debate_common._log_debate_event` and pass. PROJECT_TZ exercised via every cmd that timestamps output. DEFAULT_LOG_PATH exercised via `debate_stats.py` integration.
- [x] **Regression risk:** Zero signature changes (`_log_debate_event(event, log_path=None, cost_snapshot=None)` unchanged; PROJECT_TZ + DEFAULT_LOG_PATH are passive constants). 7 internal `_log_debate_event` + 4 internal `PROJECT_TZ` debate.py call sites + 5 sibling files + 1 test fixture all retargeted. Whole-repo grep clean post-fix.
- [x] **Plan compliance:** **One advisory deviation** — `scripts/debate_stats.py` was added to scope mid-build (7 → 8 files). Reason: original scout grep used `\bdebate\.DEFAULT_LOG\b` which doesn't match `DEFAULT_LOG_PATH` (the `_` after LOG defeats `\b`). Caught by post-build verification grep (using whole identifier `debate\.DEFAULT_LOG_PATH`), fixed in one Edit. Same class of miss as the prior commit's monkeypatch oversight — see "Lesson Surfaced" below.
- [x] **Negative tests:** `_log_debate_event` is wrapped by `os.makedirs(..., exist_ok=True)` — handles missing dir. `cost_snapshot=None` branch handled (uses cumulative get_session_costs). Both paths exercised by integration tests.
- [x] **Integration:** All 5 access surfaces updated:
  1. Internal debate.py (7 _log + 4 PROJECT_TZ sites)
  2. Sibling modules (5 — debate_explore, debate_compare, debate_verdict, debate_outcome, debate_stats)
  3. Test fixture (1 — test_debate_commands.py:208 monkeypatch)
  Hooks clean. CLI loads. Cleanup of obsolete lazy `import debate` in debate_outcome.py (no other debate.X reference remained).

## Tests

PASS — 932 passed in 11.52s.

## Verification Battery

- `bash tests/run_all.sh` → 932 passed ✓
- `grep -n 'def _log_debate_event|^DEFAULT_LOG_PATH|^PROJECT_TZ' scripts/debate.py` → 0 ✓
- `grep -rn 'debate\._log_debate_event|debate\.PROJECT_TZ|debate\.DEFAULT_LOG_PATH' scripts/ tests/ hooks/` → 0 ✓
- `hasattr(debate, <migrated symbol>)` → all False ✓
- `debate.py challenge --help` → exit 0 ✓
- LOC: debate.py 3834→3815 (−19), debate_common.py 311→338 (+27)

## Lesson Surfaced (2nd time today — promotion candidate)

**Pre-flight grep must use whole-identifier patterns, not prefix + word-boundary.** Today's miss was `\bdebate\.DEFAULT_LOG\b` (matches "DEFAULT_LOG" with end-of-word, but `_` after LOG is a word char so the pattern requires the literal substring "DEFAULT_LOG" with non-word char following — never matches `DEFAULT_LOG_PATH`).

Combined with yesterday's miss (monkeypatch.setattr form not in `debate.X(` grep), this is becoming a pattern: scouting greps systematically miss certain access forms. Two recurrences in two commits suggests a checklist or generated grep rather than ad-hoc patterns.

**Promotion candidate (L40 if recurring again):** Migration plan template should include a generated grep that covers:
- Call form: `\bdebate\.<symbol>\b` for each migrated symbol
- Attribute access: `\bdebate\.<symbol>(?![\w])` — same but explicit negative lookahead
- Monkeypatch form: `setattr\(\s*debate\s*,\s*["\']<symbol>["\']`
- Single source of truth: enumerate the symbol list once, generate all 3 patterns from it.

For now: caught by post-build verification battery (correct guard). Document in next migration plan.

## Verdict: GO

- 932/932 passing
- Zero MATERIAL issues
- Plan compliance OK (one mid-build scope clarification, mechanical)
- Same pattern as F4 (12a865b) and `_load_config` (50a7fbd) — risk profile identical
- 3 incremental migrations now complete: cost-tracking → load_config → log_event

## Next

- `/ship` ready
- Or: continue to frontmatter helpers migration (`_build_frontmatter`, `_redact_author`, `_apply_posture_floor`, `_shuffle_challenger_sections`) — last helper-group commit before the cmd_* extractions

---
topic: debate-common
qa_result: go-with-warnings
git_head: e2dd116
producer: claude-opus-4-7
created_at: 2026-04-16T19:30:00-07:00
plan: tasks/debate-common-plan.md
challenge: tasks/debate-common-challenge.md
review_mode: --qa
posture: 3
---
# QA: debate-common (commit e2dd116)

## 5-Dimension Results

- [x] **Test coverage** — PASS (with note). No dedicated `tests/test_debate_common.py`; the 4 moved functions are exercised via existing tests: `_load_credentials` via 8 monkeypatch sites in test_debate_commands.py + cmd_* execution paths; `_get_fallback_model` and `_get_model_family` via 24 direct call sites in test_debate_fallback.py; `_load_dotenv` via every test import. Adequate coverage; a dedicated unit test file would be cleaner but is not blocking for a pure-move refactor.
- [x] **Regression risk** — PASS. All 4 function signatures preserved verbatim (`_load_dotenv()`, `_load_credentials()`, `_get_model_family(model_name)`, `_get_fallback_model(primary, config)`). No callers needed signature updates — only the qualified-name prefix (`debate.X` → `debate_common.X`) changed.
- [ ] **Plan compliance** — PASS-WITH-WARNINGS. 4 planned files unchanged + 1 unplanned file changed:
  - `scripts/debate_outcome.py` (planned, unchanged): justified — doesn't reference any of the 4 migrated symbols.
  - `scripts/debate_stats.py` (planned, unchanged): justified — same reason.
  - `tests/test_debate_smoke.py` (planned, unchanged): scope narrowed mid-execution. Its `del sys.modules["debate"]` is exact-match and cannot capture `debate_common`. F2 strict requirement satisfied without touching this file.
  - `tests/test_debate_tools.py` (planned, unchanged): scope narrowed. Its glob is `startswith("debate_tools")` — won't capture `debate_common`. F2 satisfied.
  - `stores/debate-log.jsonl` (changed, unplanned): runtime audit log appended by this session's `/challenge` and `/review` runs. Automatic side effect; not in plan but expected.
  
  All 5 deltas have legitimate justifications. None violate the F2 cleanup intent.
- [x] **Negative tests** — PASS. No new error paths added. Both error returns in `_load_credentials` (`return None, None, False`) and the `FileNotFoundError` handler in PROJECT_ROOT computation are moved verbatim from debate.py. No regression in error semantics.
- [x] **Integration** — PASS. Grep for migrated symbols accessed via `debate.X` in `scripts/` and `tests/` returns zero matches. Sibling modules correctly carry BOTH lazy `import debate` (for non-migrated helpers like `debate.get_session_costs`, `debate._load_config`, `debate.LLM_SAFE_EXCEPTIONS`, `debate._parse_frontmatter`) AND lazy `import debate_common` (for the 4 migrated helpers). Dual-import is the correct transition state.

## Tests

```
bash tests/run_all.sh
932 passed in 11.31s
```

PASS. (Already verified at end of build, before commit; no re-run needed per skill rule.)

## User-Specified Concerns (from invocation)

### (a) L39-class latent issue
**Verified clean.** The L39 mechanism requires `sys.modules` manipulation that captures the lazy-imported module's identity. After this commit:
- `test_debate_commands.py:22-23` glob removed (was `startswith("debate")`, would have captured `debate_common`).
- `test_debate_smoke.py:35,77` use exact-match `"debate"` — cannot capture `debate_common`.
- `test_debate_tools.py:18-19` uses `startswith("debate_tools")` — cannot capture `debate_common`.

No remaining test code can shuffle `debate_common` out of `sys.modules` mid-suite. F3 import style (`import debate_common; debate_common.foo()`, never `from debate_common import foo`) is enforced everywhere — verified by grep returning zero `from debate_common` matches.

### (b) Patch-target staleness
**Verified clean.** All `_load_credentials` patches updated to target `debate_common`:
- 2 fixtures (`fake_credentials`, `fake_credentials_fallback`) in test_debate_commands.py — multi-line `setattr` form, both updated.
- 6 inline patches at test_debate_commands.py lines 960, 973, 989, 1008, 1021, 1035 — all updated via single-line `setattr` replace_all.
- Direct calls in test_debate_fallback.py (8× `_get_fallback_model`, 16× `_get_model_family`) — all updated.

Test outcome (932 pass) confirms patches land on the right module — silent no-ops would manifest as `_load_credentials` returning real `None` and tests asserting against fake values failing.

### (c) Leftover debate.X references compiling silently
**Verified clean.** Python's tolerance for setting attributes on modules means `setattr(debate, "_load_credentials", ...)` would succeed even after `_load_credentials` is gone from debate.py — but the cmd_* code's call to `debate_common._load_credentials()` would still resolve to the real function in debate_common, ignoring the patched-but-detached attribute on debate. Consequence: tests would see real credential lookup behavior instead of fakes.

The grep `debate\._load_credentials|debate\._load_dotenv|debate\._get_fallback_model|debate\._get_model_family|debate\.DEFAULT_LITELLM_URL` against scripts/ and tests/ returns ZERO matches. Combined with the 932-pass test result, no silent patch ghosts.

### (d) Breaks next planned commit (cost tracking atomic migration)
**No blocker.** Next commit will:
1. Move `_session_costs`, `_session_costs_lock`, `_estimate_cost`, `_track_cost`, `get_session_costs`, `_cost_delta_since`, `_track_tool_loop_cost`, cost rate tables → `debate_common.py` atomically.
2. Update `_call_litellm` (still in debate.py for now) to call `debate_common._track_cost` (currently calls local `_track_cost`).
3. Update 4 sibling modules: `_cost_snapshot = debate.get_session_costs()` → `debate_common.get_session_costs()`.
4. Update test_debate_pure.py and test_debate_utils.py: many `debate._estimate_cost(...)` direct calls → `debate_common._estimate_cost(...)` + add `import debate_common`.

This commit's pattern (lazy `import debate_common` next to lazy `import debate` in siblings) directly enables that cleanup. No conflicts; no rework needed.

## Verdict: GO-WITH-WARNINGS

The warning is the plan-compliance delta. All 5 deviations are documented and justified — they tighten scope (don't touch files that don't need touching) rather than expand it. The `stores/debate-log.jsonl` modification is a runtime audit-log side effect, not a code change.

No MATERIAL findings. No regressions. F1, F2, F3, F5 from the challenge fully implemented; F4 explicitly deferred per its own atomicity constraint.

## Suggested Next Action

`/wrap` the session — significant work shipped (challenge gate, plan, implementation, QA, 2 commits). The followup commits (cost tracking, prompt loader, remaining cmd_* extractions) should each get their own session with fresh `/start` and `/plan`.

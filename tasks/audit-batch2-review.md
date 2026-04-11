---
topic: audit-batch2
review_tier: cross-model
status: passed
git_head: 9dec8f4
producer: claude-opus-4-6
created_at: 2026-04-10T21:45:00-0700
scope: "scripts/debate_tools.py, .claude/rules/reference/operational-context.md, .claude/skills/status/SKILL.md, .claude/skills/challenge/SKILL.md, CLAUDE.md, setup.sh, tests/contracts/*, tests/test_llm_client.py"
findings_count: 0
spec_compliance: false
review_backend: cross-model (2/3 responders — GPT-5.4 had request format error)
---
# Review: audit-batch2

## Review Summary

Cross-model review with 2 of 3 models responding (claude-opus-4-6, gemini-3.1-pro). GPT-5.4 failed with a LiteLLM request format error (not a code issue).

Two material findings were identified and fixed in this review pass:

1. **`mode` vs `phase` field mismatch** — operational-context.md and /status skill referenced `mode` but debate-log.jsonl uses `phase`. Fixed: all references now use `phase` and `debate_id`.
2. **`test_rollback.sh` isolation** — test used unused temp dir setup/teardown while running against real project root. Fixed: removed misleading temp dir code, added clear comment about why real project root is needed.

## PM / Acceptance
- [ADVISORY] Test quality is uneven — `test_idempotency.sh` tests tautologies (--help determinism), `test_rollback.sh` runs against real tree. Acceptable as first-generation replacements for 100%-broken outbox tests.
- [ADVISORY] `debate.py` smoke tests (`test_debate_smoke.py`) already existed but weren't in the Batch 2 diff — not a gap.
- [ADVISORY] Good process: challenge artifact with 3 challengers, all 4 revisions applied.

## Security
- [ADVISORY] `test_no_credential_leakage_in_error` tests that LLMError doesn't inject real keys, but doesn't exercise actual HTTP error paths. At posture 2 (speed-with-guardrails), this is acceptable.
- [ADVISORY] `_load_api_key` .env fallback path is untested. Low risk at posture 2.
- [ADVISORY] `setup.sh` hook change from `cp` to `ln -sf` is a security improvement (symlink stays in sync with repo version).

## Architecture
- [ADVISORY] Contract tests use inline Python via bash — effective for removing SQLite dependency, but harder to debug/lint long-term. Migration to pytest would be a future improvement.
- [ADVISORY] `test_idempotency.sh` tests tautological determinism (--help output, json.load of static file). Low signal but not harmful.
- [ADVISORY] Residual `sqlite3` string match in scripts is a string reference, not an import. No action needed.

## Findings Fixed During Review
| Finding | Source | Fix |
|---------|--------|-----|
| `mode` vs `phase` field mismatch in docs + /status skill | Challenger A (claude-opus-4-6) | Updated operational-context.md and status SKILL.md to use `phase`/`debate_id` |
| `test_rollback.sh` misleading temp dir | Challenger A (claude-opus-4-6) | Removed unused setup_test_dir/teardown_test_dir, clarified test purpose |
| `helpers.sh` dead SQLITE declaration | Challenger A (claude-opus-4-6) | Removed unused SQLITE variable and temp dir helpers |

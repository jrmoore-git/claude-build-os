---
topic: audit-batch2
created: 2026-04-10
---
# Audit Batch 2: Contract Tests, Audit DB, Test Coverage

## Problem
The 2026-04-10 audit (tasks/audit-2026-04-10.md) found three structural gaps in BuildOS:

1. **F2 (Critical): Contract tests all fail.** All 7 tests in tests/contracts/ depend on `scripts/outbox_tool.py` which doesn't exist — it's a downstream Jarvis artifact. The Essential Eight invariants (idempotency, approval gating, audit completeness, degraded mode, state machine validation, rollback, version pinning, exactly-once scheduling) are listed as hard rules in CLAUDE.md but have zero passing verification. Result: 5/56 tests pass across all contract test files.

2. **F1 (Critical): audit.db is empty (0 bytes) but docs and code assume 18,500+ rows.** `operational-context.md` provides 3 SQL queries against `audit_log`. `debate_tools.py:134` reads from it. `/status` and `/challenge` skills reference it. No code in BuildOS writes to it — the audit_log table was populated by the downstream Jarvis project. The system silently returns empty results, which `/status` interprets as "clear day."

3. **F5 (Warning): 69% of Python scripts have no tests.** Most critically: `debate.py` (1,800+ lines, orchestrates all cross-model work) and `llm_client.py` (all external API calls route through it) have zero test coverage.

## Proposed Approach

### Item 1: Rewrite contract tests for BuildOS
Replace the outbox_tool.py-dependent tests with tests that exercise BuildOS's own code paths:
- **Idempotency:** debate.py produces same output for same input (deterministic seed)
- **Audit completeness:** debate.py writes to debate-log.jsonl for every run
- **Degraded mode:** llm_client.py returns structured errors when LiteLLM is down
- **Version pinning:** debate-models.json pins model versions
- **State machine:** artifact_check.py validates artifact state transitions (proposal → challenge → plan → review)
- **Rollback:** setup.sh is idempotent (run twice, same result)
- Drop approval gating and exactly-once scheduling tests (these are downstream-only concepts — BuildOS has no outbox or scheduled sends)

Non-goals: Testing downstream project behavior. Testing hook execution (hooks run in Claude Code's harness, not testable in isolation).

### Item 2: Decide on audit.db
Two options:
- **Option A: Implement writes.** Add audit logging to debate.py (it already writes to debate-log.jsonl — dual-write to audit.db). Update `/status` to read from it. Cost: ~50 lines in debate.py + schema init.
- **Option B: Strip claims.** Remove the 18,500+ row reference from operational-context.md. Update `/status` and `/challenge` to use debate-log.jsonl instead. Remove the `_get_recent_costs` function from debate_tools.py. Cost: doc edits + ~20 lines removed.

### Item 3: Add tests for debate.py and llm_client.py
- **debate.py:** Smoke tests for CLI argument parsing, output format validation, model config loading. Not full integration tests (those require LiteLLM running).
- **llm_client.py:** Unit tests for error categorization, retry logic, response parsing. Mock the HTTP layer.

### Simplest Version
Start with Item 2 (smallest, unblocks Item 1), then Item 1 (contract tests), then Item 3 (additive, no dependencies).

### Current System Failures
- Contract test run: 5/56 pass (run on 2026-04-10)
- `/status` silently returns no operational data (audit.db empty)
- `debate_tools.py _get_recent_costs()` returns $0.00 for all queries
- No test caught the dead code removed in Batch 1 (pipeline_manifest.py, verify_state.py had zero callers)

### Operational Context
- debate-log.jsonl: 95 entries, 2026-03-15 to 2026-04-10, all valid JSON
- debate.py: runs ~5-10 times per day across /challenge, /debate, /review, /refine
- LiteLLM proxy: running locally, 3 models configured (claude-opus-4-6, gemini-3.1-pro, gpt-5.4)
- No cron jobs in BuildOS — all execution is interactive via Claude Code sessions

### Baseline Performance
- Contract tests: 5/56 passing (9% pass rate)
- Test coverage: 5/16 scripts have tests (31%)
- audit.db: 0 bytes, 0 rows (should have operational history)
- debate-log.jsonl: healthy, 95 entries, functional as an alternative data source

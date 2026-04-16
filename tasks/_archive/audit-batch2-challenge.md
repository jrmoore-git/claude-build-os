---
topic: audit-batch2
created: 2026-04-10
review_backend: cross-model
challengers: 3
recommendation: PROCEED
complexity: medium
security_posture: 2
---
# Challenge: Audit Batch 2 Remediation

## Recommendation: PROCEED with revisions

All 3 challengers agree the work is necessary and well-scoped. No objections to the direction. Four revisions required before planning:

### Required Revisions

1. **Commit to Option B for audit.db** (unanimous). Strip the 18,500+ row claims, remove `_get_recent_costs`, point `/status` and `/challenge` at `debate-log.jsonl`. Option A (dual-write) adds complexity for a system that runs 5-10 times/day interactively — unjustified at this scale. debate-log.jsonl is already the source of truth.

2. **Update CLAUDE.md when dropping 2 invariants** (unanimous). If BuildOS can only verify 6 of 8 Essential Eight invariants (no outbox = no approval gating, no exactly-once scheduling), the docs must say so explicitly. Otherwise the next audit re-flags the same gap.

3. **Verify artifact_check.py before promising a state machine test** (2 of 3 challengers). The proposal assumes it implements enforced state transitions (proposal -> challenge -> plan -> review). Challengers found only 1 "state machine" match across all scripts. Test what actually exists, not what the workflow diagram implies.

4. **Don't assume debate.py idempotency via seed** (1 challenger, valid). External LLM calls are inherently nondeterministic. The idempotency contract test should test something actually deterministic — config loading, argument parsing, file output format — not cross-model output equality.

### Advisory Notes

- debate.py is 3,564 lines, not 1,800+ as stated. Smoke tests are an acceptable first step but the proposal should acknowledge this leaves most of the file untested.
- llm_client.py tests should verify no credential leakage in error output (security, advisory at posture 2).
- Consider whether "contract tests" is the right framing — there's no service boundary. These are really property tests for framework invariants. Naming matters for future contributors.
- Challenger C suggests integration tests against the live local LiteLLM proxy instead of HTTP mocks for llm_client.py. Worth considering for simplicity.

### Concessions (all challengers agreed)

- Diagnosis is thorough and evidence-based. Every major claim verified.
- Dropping downstream-only tests is correct.
- Sequencing (Item 2 -> Item 1 -> Item 3) is right.
- debate-log.jsonl is healthy and sufficient as the operational data source.

## Complexity: Medium

- 6 new/rewritten test files
- 1 doc update (CLAUDE.md Essential Eight annotation)
- ~3 files modified (debate_tools.py, operational-context.md, status skill)
- ~4 files deleted (old contract tests that can't be salvaged)
- No new abstractions, no new dependencies

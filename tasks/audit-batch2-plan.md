---
scope: "Fix 3 structural gaps from 2026-04-10 audit: strip audit.db claims, rewrite contract tests for BuildOS, add test coverage for debate.py and llm_client.py"
surfaces_affected: "scripts/debate_tools.py, .claude/rules/reference/operational-context.md, .claude/skills/status/SKILL.md, .claude/skills/challenge/SKILL.md, CLAUDE.md, tests/contracts/*, tests/test_debate_smoke.py, tests/test_llm_client.py"
verification_commands: "bash tests/run_all.sh"
rollback: "git revert <sha>"
review_tier: "Tier 1.5"
verification_evidence: "96 pytest pass, 5/5 rollback contract, 3/3 audit completeness, sqlite removal verified, mode→phase fix verified — 4 probes all pass"
challenge_artifact: "tasks/audit-batch2-challenge.md"
challenge_recommendation: "PROCEED"
challenge_revisions_applied: true
---
# Plan: Audit Batch 2 — Contract Tests, Audit DB, Test Coverage

## Challenge Revisions Applied

Per `tasks/audit-batch2-challenge.md` (3 challengers, unanimous PROCEED with revisions):

1. **Committed to Option B for audit.db** — strip claims, use debate-log.jsonl only
2. **CLAUDE.md will annotate 6-of-8 invariants** — no approval gating or exactly-once scheduling in BuildOS
3. **Dropped state machine contract test** — artifact_check.py only checks existence/staleness, not enforced transitions
4. **Dropped idempotency-via-seed test** — external LLM calls are nondeterministic; test deterministic properties instead

## Build Order

### Step 1: Strip audit.db claims (sequential, main)

Unblocks Steps 2 and 3 by establishing debate-log.jsonl as the sole data source.

1. Remove `_get_recent_costs()` from `scripts/debate_tools.py` (~lines 124-152)
2. Rewrite `.claude/rules/reference/operational-context.md`:
   - Remove audit.db schema section and all 3 SQL queries
   - Replace with debate-log.jsonl usage patterns (jq queries)
   - Keep metrics.db section unchanged
3. Update `/status` skill — replace audit.db references with debate-log.jsonl
4. Update `/challenge` skill — remove audit.db operational context references
5. Delete `stores/audit.db` (0 bytes, placeholder)

### Step 2: Rewrite contract tests (parallel agent, worktree)

Replace outbox_tool.py-dependent tests with BuildOS-native tests.

1. Rewrite `tests/contracts/helpers.sh` — remove outbox_tool.py dependency, add BuildOS helpers
2. Rewrite 6 contract tests:
   - `test_audit_completeness.sh` — debate.py writes to debate-log.jsonl for every run
   - `test_degraded_mode.sh` — llm_client.py returns structured errors when LiteLLM is down
   - `test_version_pinning.sh` — debate-models.json pins model versions, no "latest" tags
   - `test_rollback.sh` — setup.sh is idempotent (run twice, same result)
   - `test_idempotency.sh` — config loading and argument parsing produce consistent results
   - `test_artifact_validation.sh` — artifact_check.py validates existence and staleness (not state machine)
3. Delete 2 downstream-only tests:
   - `test_approval_gating.sh` (no outbox)
   - `test_exactly_once.sh` (no scheduled sends)
4. Update `CLAUDE.md` Essential Eight annotation: "6 of 8 apply to BuildOS (no approval gating, no exactly-once scheduling — these require a downstream outbox)"

### Step 3: Add unit tests (parallel agent, worktree)

1. Expand `tests/test_debate_smoke.py`:
   - CLI argument parsing for all subcommands
   - Model config loading from debate-models.json
   - Output format validation (YAML frontmatter in artifacts)
   - Acknowledge: 3,564-line file, smoke tests are a first step
2. Create `tests/test_llm_client.py`:
   - Error categorization (connection, auth, rate limit, model errors)
   - Response parsing
   - No credential leakage in error output (security, per challenger advisory)

## Execution Strategy

**Decision:** hybrid
**Pattern:** pipeline (Step 1) then fan-out (Steps 2+3)
**Reason:** Steps 2 and 3 have non-overlapping file scopes and independent deliverables, but both depend on Step 1 completing (debate-log.jsonl as sole data source)

| Subtask | Files | Depends On | Isolation |
|---------|-------|------------|-----------|
| Step 1 | debate_tools.py, operational-context.md, status SKILL.md, challenge SKILL.md, stores/audit.db | — | main |
| Step 2 | tests/contracts/*, CLAUDE.md | Step 1 | worktree |
| Step 3 | tests/test_debate_smoke.py, tests/test_llm_client.py | Step 1 | worktree |

**Synthesis:** Main agent runs full test suite after both worktree agents complete, reconciles any conflicts.

## Files

| File | Action | Scope |
|------|--------|-------|
| `scripts/debate_tools.py` | modify | Remove `_get_recent_costs()` |
| `.claude/rules/reference/operational-context.md` | modify | Replace audit.db with debate-log.jsonl |
| `.claude/skills/status/SKILL.md` | modify | Point at debate-log.jsonl |
| `.claude/skills/challenge/SKILL.md` | modify | Remove audit.db references |
| `stores/audit.db` | delete | Empty placeholder |
| `tests/contracts/helpers.sh` | modify | Remove outbox_tool.py, add BuildOS helpers |
| `tests/contracts/test_audit_completeness.sh` | rewrite | debate-log.jsonl verification |
| `tests/contracts/test_degraded_mode.sh` | rewrite | llm_client.py error handling |
| `tests/contracts/test_version_pinning.sh` | rewrite | debate-models.json validation |
| `tests/contracts/test_rollback.sh` | rewrite | setup.sh idempotency |
| `tests/contracts/test_idempotency.sh` | rewrite | Config/arg determinism |
| `tests/contracts/test_artifact_validation.sh` | rewrite | artifact_check.py existence/staleness |
| `tests/contracts/test_approval_gating.sh` | delete | Downstream-only |
| `tests/contracts/test_exactly_once.sh` | delete | Downstream-only |
| `CLAUDE.md` | modify | Annotate 6-of-8 invariants |
| `tests/test_debate_smoke.py` | modify | Expand CLI smoke tests |
| `tests/test_llm_client.py` | create | Error handling, no credential leakage |

## Verification

```bash
bash tests/run_all.sh
# Expect: all contract tests pass, all unit tests pass
# Target: >50% pass rate (up from 9%)
```

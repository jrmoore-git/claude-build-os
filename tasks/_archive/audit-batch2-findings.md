---
debate_id: audit-batch2-findings
created: 2026-04-10T21:20:00-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# audit-batch2-findings — Challenger Reviews

## Challenger A — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL]:** The proposal claims `artifact_check.py` validates artifact state transitions and proposes testing it for state machine validation. Tool results show `artifact_check` exists as a script with a test file (`tests/test_artifact_check.py`), but `check_function_exists("artifact_check", "scripts")` returns false — meaning there's no function by that name, just a script. More importantly, `check_code_presence("state machine", "scripts")` returns only 1 match across all scripts. The proposal assumes artifact_check.py implements a full state machine (proposal → challenge → plan → review), but this needs verification. If the state transitions are just comments or partial, the contract test for "state machine validation" would be testing something that doesn't actually exist as enforced logic — repeating the same pattern as the outbox_tool dependency (tests for phantom capabilities).

2. **RISK [MATERIAL]:** The proposal's Item 2 presents Option A (dual-write to audit.db) and Option B (strip claims, use debate-log.jsonl) as equivalent choices but doesn't make a recommendation. Tool verification confirms: `audit_log` table doesn't exist (`count_records` and `get_recent_costs` both return "no such table: audit_log"), `audit.db` is referenced in skills (2 matches), and `debate_tools.py:_get_recent_costs` exists and queries it. This is a **live silent failure** — `_get_recent_costs` is callable right now and returns errors or empty results. The proposal should commit to Option B. Option A introduces a dual-write pattern (jsonl + sqlite) for a system that runs 5-10 times/day interactively — that's unjustified complexity. debate-log.jsonl already has 95 entries and is the actual source of truth. Dual-write creates a consistency problem for zero benefit at this scale.

3. **UNDER-ENGINEERED [ADVISORY]:** The proposal says "Drop approval gating and exactly-once scheduling tests (these are downstream-only concepts)" but doesn't address updating CLAUDE.md to remove or annotate these as downstream-only invariants. If CLAUDE.md lists 8 Essential Eight invariants and BuildOS can only verify 6, the doc should say so explicitly. Otherwise the next audit will re-flag the same gap.

4. **RISK [ADVISORY]:** debate.py is 3,564 lines (EVIDENCED: tool shows `total_lines: 3564`, not the 1,800+ claimed in the proposal). The proposal scopes Item 3 as "smoke tests for CLI argument parsing, output format validation, model config loading." For a 3,564-line file with at least 7 subcommands (challenge, judge, refine, review, review-panel, check-models, and more visible at line 3540+), smoke tests alone leave enormous surface area untested. This is acceptable as a first step but the proposal should acknowledge the gap explicitly and set a target for what "adequate" looks like for this file.

5. **ASSUMPTION [ADVISORY]:** The proposal claims "5/56 tests pass (9% pass rate)" for contract tests. This is SPECULATIVE from the reviewer's perspective — no tool was used to run the test suite, and the number comes from the audit document. The claim is plausible given that `outbox_tool` has zero matches anywhere in the codebase, but the exact numbers should be verified before being used as a baseline metric.

6. **ALTERNATIVE [ADVISORY]:** For Item 1, rather than writing new contract tests that test BuildOS internals (idempotency via deterministic seed, etc.), consider whether the "contract test" abstraction is even the right one. What's being proposed is really just unit/integration tests for specific properties. Calling them "contract tests" when there's no contract boundary (no service interface, no API schema) imports terminology that doesn't match the architecture. This is cosmetic but could cause confusion — future contributors may expect contract tests to test inter-service contracts.

## Concessions

1. **The sequencing is correct.** Item 2 → Item 1 → Item 3 is the right order. Fixing the data source unblocks contract tests, and contract tests are higher value than unit test coverage for debate.py given the current 5/56 failure rate.

2. **The diagnosis is thorough and verified.** Every major claim checks out: `outbox_tool` doesn't exist anywhere (EVIDENCED), `audit_log` table doesn't exist (EVIDENCED), `_get_recent_costs` is live dead code (EVIDENCED), debate.py and llm_client.py have zero test coverage (EVIDENCED).

3. **Dropping downstream-only tests is the right call.** No outbox, no cron jobs (`get_job_schedule` confirms no jobs config exists), no scheduled sends — testing approval gating and exactly-once scheduling would be testing phantom capabilities.

## Verdict

**REVISE**: The proposal is well-diagnosed but needs to (1) commit to Option B for audit.db rather than leaving it as an open question, (2) verify that artifact_check.py actually implements enforceable state transitions before promising a contract test for it, and (3) note that debate.py is 3,564 lines not 1,800+, which affects the scoping of Item 3. The core approach is sound; these are refinements, not directional changes.

---

## Challenger B — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL]: The proposed “idempotency” contract test assumes `debate.py` can be made deterministic via a seed, but I could not verify any deterministic-seeding mechanism in the codebase; only a generic `seed` substring exists somewhere in scripts, and `debate.py` currently routes cross-model calls through `llm_client.py` to external models, which are inherently nondeterministic. If this assumption is wrong, that test will be flaky and will recreate the same false-signal problem as the current broken contract suite.

2. [RISK] [MATERIAL]: Option A (dual-write from `debate.py` into `stores/audit.db`) introduces a new trusted-data boundary without a migration/locking plan. I verified `_get_recent_costs()` opens `stores/audit.db` directly with `sqlite3.connect(...)` and queries `audit_log`; adding writes from the hot orchestration path risks database lock contention, partial-write behavior, and silent divergence between `debate-log.jsonl` and SQLite unless atomicity/reconciliation is specified. That is a production-behavior change, not just a test fix.

3. [ALTERNATIVE] [MATERIAL]: Option B is the safer default because the verified code already has a working local log path (`debate-log.jsonl` appears in scripts) while the only verified DB consumer shown is `_get_recent_costs()` in `scripts/debate_tools.py`, which queries a DB the proposal says is empty. Given “speed-with-guardrails,” stripping stale audit.db claims and moving readers to the JSONL log reduces false operational confidence without introducing new persistence code.

4. [UNDER-ENGINEERED] [ADVISORY]: The proposal drops approval-gating and exactly-once scheduling tests as “downstream-only,” which may be correct functionally, but it should also remove or clearly scope any BuildOS documentation claims that still present those as hard local invariants. Otherwise you preserve a trust mismatch: docs imply guarantees the repo does not enforce.

5. [RISK] [ADVISORY]: The suggested `llm_client.py` tests should explicitly verify that structured errors and mocked failures do not leak `LITELLM_MASTER_KEY` or raw request payloads into test output/logs. I verified `llm_client.py` uses an environment API key and is the shared path for all external calls, so this is the highest-value place to lock down credential-handling regressions.

6. [ASSUMPTION] [ADVISORY]: The proposal cites a state machine of `proposal → challenge → plan → review`, but I could not verify that exact transition model in `artifact_check.py`; the file header mentions plan, challenge, judgment, and review artifacts, but not the proposed sequence. The contract test should be derived from actual artifact rules in code, not from an inferred workflow description.

## Concessions
- The proposal correctly identifies a real integrity issue: `_get_recent_costs()` in `scripts/debate_tools.py` reads `stores/audit.db`, so an empty DB can produce misleading “all clear / $0.00” results.
- The proposal is grounded on verified test gaps: `scripts/debate.py` and `scripts/llm_client.py` currently have no discovered test files.
- The config does pin concrete model identifiers in `config/debate-models.json`, so a version/config validation test is a good fit for this repo.

## Verdict
REVISE with one key change: prefer Option B first, and redefine contract tests around behaviors the repo can actually enforce locally rather than nondeterministic cross-model outputs or unverified workflow assumptions.

---

## Challenger C — Challenges
## Challenges
1. [RISK] [MATERIAL]: The proposal presents options for Item 2 (`audit.db`) instead of making a recommendation. Option B (strip claims, use `debate-log.jsonl`) is the only viable path for our SPEED-WITH-GUARDRAILS posture. `debate-log.jsonl` already contains historical data [EVIDENCED: 95 entries, 2026-03-15 to 2026-04-10], whereas implementing dual-writes to a fake downstream database adds complexity for zero user value. 
2. [UNDER-ENGINEERED] [MATERIAL]: Item 1 correctly removes tests for "approval gating" and "exactly-once scheduling" because BuildOS does not have an outbox. However, these are defined as hard rules in the "Essential Eight invariants" within `CLAUDE.md`. Dropping the tests without amending `CLAUDE.md` to reflect that BuildOS only supports 6/8 invariants will create immediate documentation/policy conflicts.
3. [OVER-ENGINEERED] [ADVISORY]: Item 3 proposes mocking the HTTP layer to unit test `llm_client.py`. Given that the LiteLLM proxy is running locally and the system is executed interactively [EVIDENCED: runs ~5-10 times per day], spending time building HTTP mocks for LiteLLM may be unnecessary overhead compared to just adding simple integration tests that ping the actual local proxy.

## Concessions
1. Correctly identifying that `outbox_tool.py` is a downstream dependency and stripping it out will finally allow the BuildOS pipeline to have a passing test suite.
2. Right-sizing the testing for `debate.py` [EVIDENCED: 1,800+ lines, verified via tool as 3564 lines] to CLI smoke tests rather than attempting deep unit testing of a massive legacy script.
3. The "Simplest Version" execution order correctly sequences unblocking the data source (Item 2) before fixing the tests that might depend on it (Item 1).

## Verdict
REVISE to commit explicitly to Option B for the audit DB, and explicitly include the `CLAUDE.md` documentation update to formally reduce the "Essential Eight" to the "Supported Six" for BuildOS.

---

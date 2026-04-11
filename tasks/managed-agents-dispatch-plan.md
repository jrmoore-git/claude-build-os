---
scope: "Add managed-agent dispatch for debate.py consolidation via new managed_agent.py module"
surfaces_affected: "scripts/managed_agent.py, scripts/debate.py, tests/test_managed_agent.py"
verification_commands: "python3.11 -m pytest tests/test_managed_agent.py -v && python3.11 scripts/debate.py judge --help | grep use-ma"
rollback: "git revert <sha>"
review_tier: "Tier 1.5"
verification_evidence: "PENDING"
challenge_recommendation: "PROCEED"
challenge_artifact: "tasks/managed-agents-dispatch-challenge.md"
---

# Managed Agents Dispatch — Build Plan

## Build Order

1. **Create `scripts/managed_agent.py`** — MA client module (new, ~150 lines)
   - `dispatch_task(payload, metadata, api_key) -> session_id` — creates MA agent + session via Anthropic SDK beta, sends materialized prompt
   - `poll_task(session_id, timeout_s, api_key) -> raw_result` — polls/streams SSE events with configurable timeout, retry with backoff on transient failures
   - `validate_result(raw_result, expected_max_len) -> (text_body, stats_or_none)` — validates schema, size (2x input), required fields; matches `_consolidate_challenges` return shape
   - `MA_SAFE_EXCEPTIONS` tuple mirroring `LLM_SAFE_EXCEPTIONS` pattern
   - Credential: load `MA_API_KEY` from env, no logging, no broad subprocess inheritance
   - Logging: structured events compatible with `_log_debate_event` / `debate-log.jsonl`

2. **Integrate into `scripts/debate.py`** — modify `cmd_judge` (~30 lines around line 1484)
   - Add `--use-ma-consolidation` argparse flag to judge subcommand
   - Before existing `_consolidate_challenges` call, check flag + credential availability
   - If set + credential present: build payload from `challenge_body`, call `dispatch_task` -> `poll_task` -> `validate_result`
   - On success: use MA result as `consolidated_body`, log MA source
   - On failure: log fallback reason, run local `_consolidate_challenges`
   - If set + credential missing: log warning, fall back to local (not hard-fail)

3. **Create `tests/test_managed_agent.py`** — unit tests (new)
   - Dispatch: success path, network error, auth error
   - Poll: success, timeout, transient retry
   - Validate: valid result, oversized result, missing body, empty body
   - Fallback: verify each failure mode triggers local fallback
   - Mock MA API responses — no live calls

## Files

| File | Action | Scope |
|------|--------|-------|
| `scripts/managed_agent.py` | Create | ~150 lines — MA client: dispatch/poll/validate |
| `scripts/debate.py` | Modify | ~30 lines in `cmd_judge` — add `--use-ma-consolidation` flag and integration |
| `tests/test_managed_agent.py` | Create | Unit tests for MA client module |

## Key Constraints (from refined proposal)

- **Observability**: Log cost/tokens/model/job-status via `_log_debate_event`. Waived: LiteLLM dashboard. Reimplemented: retries, per-call logging, session cost accumulation.
- **Security**: Explicit payload only. No ambient context. Sensitive-content default deny. Provider assumptions documented before production rollout.
- **Credentials**: `MA_API_KEY` env var. No logging. No broad subprocess inheritance. Missing -> fallback to local (not hard-fail).
- **Validation**: Match `(text_body, stats_dict_or_none)` return shape. Size limit: 2x input length. Result treated as data only — never auto-executed.
- **Error handling**: Retry transient failures with bounded backoff (3 attempts). Strict polling timeout (configurable, default ~5min). Fallback to local on any failure.

## Execution Strategy

**Decision:** sequential
**Pattern:** pipeline
**Reason:** 2 logical components with dependency (integration requires client module). Below 3-component threshold for parallel decomposition.

| Subtask | Files | Depends On | Isolation |
|---------|-------|------------|-----------|
| A: MA client module | `scripts/managed_agent.py` | — | — |
| B: debate.py integration | `scripts/debate.py` | A | — |
| C: Tests | `tests/test_managed_agent.py` | A | — |

**Synthesis:** Sequential build, then run tests to verify all paths.

## Verification

- `python3.11 -m pytest tests/test_managed_agent.py -v` — all tests pass
- `python3.11 scripts/debate.py judge --help` — shows `--use-ma-consolidation` flag
- `python3.11 -c "from scripts.managed_agent import dispatch_task, poll_task, validate_result"` — imports succeed
- Manual: run `debate.py judge --use-ma-consolidation` on real workload with `MA_API_KEY` set
- Manual: run without `MA_API_KEY`, verify graceful fallback to local

## Reference Artifacts

- `tasks/managed-agents-dispatch-refined.md` — definitive design (6-round cross-model refined)
- `tasks/managed-agents-dispatch-challenge.md` — challenge gate artifact (PROCEED)
- `tasks/managed-agents-dispatch-proposal.md` — original proposal
- `tasks/managed-agents-dispatch-judgment.md` — judge ruling (5 accepted, 3 dismissed, 1 escalated)

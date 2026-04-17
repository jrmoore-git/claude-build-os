---
topic: debate-cost-tracking
created: 2026-04-16
---
# F4 Atomic Cost-Tracking Migration

## Project Context
BuildOS is a self-improving AI development framework. `scripts/debate.py` (~3991 lines after the simplest-version split shipped today as e2dd116) is a cross-model debate engine that powers `/challenge`, `/judge`, `/refine`, `/review`, `/explore`, and other governance skills. The active refactor splits debate.py into a package-style layout: a shared `scripts/debate_common.py` plus per-command sibling modules (`debate_explore.py`, `debate_compare.py`, `debate_verdict.py`, `debate_outcome.py`, etc.), with debate.py shrinking as functions migrate.

## Recent Context
- **2026-04-16 (today, earlier session):** Shipped split 6/N (cmd_explore extraction, commit 6bbde96). Surfaced L39 (sys.modules-driven module-identity split in test files).
- **2026-04-16 (today, mid-session):** Course-corrected refactor architecture from sibling-leaf with lazy `import debate` to package style with shared `debate_common.py` (D25). Ran cross-model `/challenge` on the new architecture (3 challengers + claude-sonnet-4-6 judge): recommendation PROCEED-WITH-FIXES, 5 material findings accepted, 0 blockers.
- **2026-04-16 (today, late session):** Implemented "simplest version" of `debate_common.py` (commit e2dd116) — 4 helpers (`_load_credentials`, `_load_dotenv`, `_get_model_family`, `_get_fallback_model`) + 2 constants. debate.py shrank 4090 → 3991 lines. F4 (cost tracking) was explicitly **deferred** to this followup commit because it requires atomic migration to avoid double-counting.
- **2026-04-16 (today, this session):** Resumed for the F4 commit per handoff guidance.

## Problem
The cost-tracking subsystem (7 functions + 1 mutable dict + 1 lock + 1 pricing table, debate.py:780-911) is the next migration unit per F4 of the parent challenge artifact. Unlike the simplest-version helpers (which are stateless), `_session_costs` is a **module-level mutable accumulator**. If only some symbols move (writers in `debate_common`, readers in `debate`, or vice versa), the accumulator becomes two distinct dicts and writes silently land in the wrong copy. The result is silent cost loss in the audit log — invisible at test time, only detectable by reading `stores/debate-log.jsonl` and noticing missing `costs` deltas.

This blocks the next 6 `cmd_*` extractions (cmd_pressure_test, cmd_review, cmd_challenge, cmd_refine, cmd_premortem, cmd_judge), which all call cost helpers and need a stable migration target.

## Proposed Approach
Single atomic commit moving all 8 cost-tracking symbols + 1 table:

| Symbol | Type | Lines |
|---|---|---|
| `_TOKEN_PRICING` | constant dict | 782-791 |
| `_estimate_cost(model, usage)` | pure function | 794-811 |
| `_session_costs` | mutable dict | 817 |
| `_session_costs_lock` | threading.Lock | 818 |
| `_track_cost(model, usage, cost_usd)` | locked write | 821-832 |
| `get_session_costs()` | locked read (public) | 835-845 |
| `_cost_delta_since(snapshot)` | pure compute | 848-874 |
| `_track_tool_loop_cost(model, tool_result)` | wrapper | 905-910 |

In the same commit:
- Replace 11 internal call sites in debate.py with `debate_common.X` qualified references
- Update 4 sibling modules (`debate_explore`, `debate_compare`, `debate_verdict`, `debate_outcome`) — change `debate.get_session_costs()` → `debate_common.get_session_costs()`, add `import debate_common` where missing
- Update 2 heavy test files (`test_debate_pure.py` ×12 sites, `test_debate_utils.py` ×8 sites) — change `debate._estimate_cost` → `debate_common._estimate_cost`
- Verify `tests/test_debate_tools.py:120,157` still passes (substring searches against `scripts/` directory should still find `_estimate_cost` in its new location)

**Non-goals:**
- Prompt loader migration (separate followup commit)
- `_load_config` migration (separate followup commit)
- `_log_debate_event` migration (separate followup commit)
- Frontmatter helpers, posture floor, shuffle (separate followup commits)
- Any of the 6 remaining `cmd_*` extractions

## Simplest Version
This **is** the simplest version — atomicity is a hard constraint. Cannot split without introducing the double-accumulator bug. The smallest valid commit is "all 8 symbols + 1 table together."

A naive simpler approach ("move the pure functions first, dict later") fails because `_track_cost` writes to `_session_costs` and `get_session_costs` reads it; if `_track_cost` lives in `debate_common` and `_session_costs` lives in `debate`, every call mutates a `debate_common._session_costs` shadow that no one reads.

### Current System Failures
1. **F4 in parent challenge** (`tasks/debate-common-challenge.md`, today): explicitly flagged the cost subsystem as requiring atomic migration. Marked OUT OF SCOPE for the simplest-version commit (e2dd116). Plan recommendation was PROCEED-WITH-FIXES contingent on F4 being addressed in its own commit.
2. **Sibling modules carry stale `import debate` for cost reads** (debate_compare.py:21, debate_verdict.py:20, debate_outcome.py:17): each module has a lazy `import debate  # ... get_session_costs ...` comment indicating the dependency, blocking the eventual deletion of `debate` from sibling import lists.
3. **debate.py:1095, 1097, 1107, 1268, 1532, 1636-37, 1704-05, 2728, 2910, 3170, 3332, 3463**: 11+ unqualified internal calls to cost helpers. After migration, these become `debate_common.X` references; not migrating leaves them as dangling unqualified references that confuse readers about ownership.

### Operational Context
- `debate.py` runs ~5-15×/day across the framework (cross-model challenges, judge calls, refine loops, audit reviews)
- Per-call cost accumulation is logged to `stores/debate-log.jsonl` (one entry per phase: challenge, judge, refine, review)
- 932 tests in suite; full run ~7-10s
- Cost data is consumed by `/healthcheck` for budget reports and `cmd_verdict` for per-debate cost summaries
- Simplest-version commit (e2dd116) shipped with 932/932 passing; QA artifact 0467c78 marked go-with-warnings (5 documented plan-compliance deviations, all justified)

### Operational Evidence
The parent commit (e2dd116) is the strongest evidence: it migrated 4 stateless helpers + 2 constants using identical pattern (add to debate_common, delete from debate, replace call sites in 4 siblings + 2 tests). Same-day shipped, 932/932 passing, /review --qa go-with-warnings. The cost migration follows the identical pattern with one added constraint: the 8-symbol unit must be atomic. No new techniques required.

### Baseline Performance
- debate.py: 3991 lines (post-e2dd116). Will go to ~3861 (~−130 LOC) after this commit.
- debate_common.py: 126 lines (post-e2dd116). Will go to ~265 (~+140 LOC).
- Test suite: 932/932 passing. Migration target: 932/932 (zero behavior change).
- Cost-tracking call sites unchanged in count: every `_track_cost` call still happens, every `get_session_costs` still returns the same shape; only the qualified module reference changes.

---
topic_slug: debate-cost-tracking
date: 2026-04-16
judge: claude-sonnet-4-6
review_backend: cross-model
challengers: [claude-opus-4-6, gpt-5.4, gemini-3.1-pro]
recommendation: PROCEED-WITH-FIXES
complexity: low
challenger_verdicts: [APPROVE, APPROVE, APPROVE]
---
# Challenge: F4 Atomic Cost-Tracking Migration

## Proposal Summary

Atomic migration of the 8 cost-tracking symbols + `_TOKEN_PRICING` table from `debate.py` to `debate_common.py` in ONE commit. Updates 11 internal call sites + 4 sibling modules + 2 heavy test files. Follows the identical pattern as the simplest-version commit (e2dd116) with one added constraint: the 8-symbol unit must move together to prevent split-accumulator bug (double `_session_costs` dict).

See `tasks/debate-cost-tracking-proposal.md` and `tasks/debate-cost-tracking-plan.md`.

## Challenger Findings

All three challengers returned APPROVE verdicts. The judge (claude-sonnet-4-6) consolidated 14 raw → 8 unique findings. Two MATERIAL findings accepted (both specification clarifications, zero new code required). Two ADVISORY findings dismissed (standard due-diligence, not flaws).

Raw findings: `tasks/debate-cost-tracking-findings.md`
Judge output: `tasks/debate-cost-tracking-judgment.md`

### Accepted (MATERIAL)

**F1: Import style for debate.py call sites must be explicit** (Challenger A, judge confidence 0.75)

The proposal cites "qualified references" as a benefit but doesn't explicitly name the import style. If `from debate_common import _track_cost` is used, call sites remain unqualified and the ownership-clarity benefit evaporates.

**Resolution (verified):** `scripts/debate.py:68` already uses `import debate_common` from the prior e2dd116 commit. F3 from the parent `debate-common-challenge.md` (today) mandates this style. Plan Step 2 explicitly says "Replace internal call sites with `debate_common.X`." Fix: update proposal + plan text to state the commitment explicitly. Zero code change. **~1 LOC (plan text).**

**F3: Module-level mutable state vulnerable to reassignment-based reset** (Challenger A, judge confidence 0.80)

If any code does `debate._session_costs = {}` (reassignment vs `.clear()`) AND debate.py re-exports via `from debate_common import _session_costs`, the migration reintroduces the double-accumulator bug through a re-export path.

**Resolution (verified):**
- `grep -rn '_session_costs\s*=' scripts/ tests/` → only the definition at `debate.py:817`. Zero reassignment sites.
- `grep -rn 'debate\._session_costs' scripts/ tests/` → zero external references.
- No backward-compat re-export is needed; `import debate_common` qualified access is the only path.

Fix: add an explicit non-goal to the plan: "debate.py will NOT re-export `_session_costs` or `_session_costs_lock`; all access goes through `debate_common.X`." **~2 LOC (plan text).**

### Dismissed (ADVISORY)

**F2: Enumeration of access paths is unverified** (2/3 challengers, judge confidence 0.70)

Standard due-diligence advice. The proposal already names `test_debate_tools.py:120,157` as a specific verification step and enumerates line numbers for all known sites. 932 tests would catch any missed path at runtime. Dismissed as good practice, not blocking.

**F4: No regression test proves single-accumulator invariant** (2/3 challengers, judge confidence 0.65)

Both challengers correctly note the 932-test suite would not catch a structural split-state bug. However, the atomicity constraint (move all 8 symbols in one commit) is the architectural guard — a regression test is belt-and-suspenders. Dismissed as follow-up opportunity, not blocking.

## Recommendation

**PROCEED-WITH-FIXES**

Both accepted findings are trivial specification clarifications (totaling ~3 LOC of plan text, zero production code beyond what the plan already mandates). The three challenger APPROVE verdicts plus the judge's "overall: REVISE with accepted changes" (where accepted = specification clarifications) converge on PROCEED.

### Inline Fixes for Build

1. **F1 resolution:** Update plan + proposal text to explicitly commit to `import debate_common` + `debate_common.X` qualified call sites (matches F3 from parent `debate-common-challenge.md`). ~1 LOC.

2. **F3 resolution:** Add explicit non-goal to plan: "debate.py will NOT re-export `_session_costs` or `_session_costs_lock` via `from debate_common import`. All access is `import debate_common` + qualified references. Pre-merge verification: `grep -rn '_session_costs\s*=' scripts/ tests/` returns only the single definition in `debate_common.py` (moved from `debate.py:817`)." ~2 LOC.

## Simpler Alternative

None identified by challengers. Challenger A noted a `CostTracker` class wrapper as an "ALTERNATIVE [ADVISORY]" but explicitly marked it a future refactor, not this commit. The atomic migration IS the simplest version (splitting further reintroduces the bug).

## Override

No override needed — all three challengers and the judge recommend proceeding with specification clarifications. The plan's atomicity rationale, scope, and verification steps are sound.

## Complexity: low

Same pattern as e2dd116 (shipped today, 932/932). One new constraint (atomicity) already addressed in plan. No new abstractions, no new dependencies, no new infrastructure.

## Next Steps

1. Update `tasks/debate-cost-tracking-plan.md` with the two inline fixes (F1 + F3 text clarifications).
2. Proceed to build per plan Step 0 → 7.
3. Run `/review --qa` per Tier 1.5 classification.

---
debate_id: debate-cost-tracking-findings
created: 2026-04-16T19:42:05-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# debate-cost-tracking-findings — Challenger Reviews

## Challenger A — Challenges
## Challenges

1. **RISK** [MATERIAL] [COST:TRIVIAL]: The proposal states 11 internal call sites in `debate.py` will change to `debate_common.X` qualified references, but does not address whether `debate.py` already has `import debate_common` at the top or whether it will use `from debate_common import ...` style. The simplest-version commit (e2dd116) established a pattern for this — but the proposal doesn't explicitly state which import style will be used in `debate.py` itself. If `debate.py` uses `from debate_common import _track_cost, get_session_costs, ...`, the call sites remain unqualified and the "dangling unqualified references that confuse readers about ownership" problem the proposal claims to fix is not actually fixed. If it uses qualified `debate_common._track_cost(...)`, that's 11 sites of churn that adds visual noise. This is a style decision that should be stated, not a blocker — but since the proposal explicitly cites "qualified references" as a benefit, it should commit to the pattern.

2. **ASSUMPTION** [ADVISORY]: The proposal assumes `tests/test_debate_tools.py:120,157` uses substring searches against the `scripts/` directory to find `_estimate_cost`. If those tests actually import `debate._estimate_cost` by name (rather than grepping files), they would break and need updating. The proposal says "should still find" — this needs verification, not assumption. Given the test suite is fast (7-10s), a single run confirms or denies this.

3. **RISK** [MATERIAL] [COST:SMALL]: The `_session_costs` dict and `_session_costs_lock` are module-level mutable state. After migration to `debate_common`, any code that does `import debate; debate._session_costs` (e.g., test fixtures that directly inspect or reset the accumulator between tests) will get an `AttributeError` or, worse, if `debate.py` re-exports the symbol via `from debate_common import _session_costs`, will get a **snapshot binding** — a new name bound to the same object at import time, which works for mutable dicts (same object reference) but would silently break if anyone ever reassigns `_session_costs = {}` to reset it rather than calling `.clear()`. The proposal should verify: (a) no test or production code does `debate._session_costs = {}` (reassignment), and (b) if `debate.py` re-exports for backward compat, it's documented as transitional. The `_session_costs_lock` has the same concern but locks are never reassigned so it's safe.

4. **ALTERNATIVE** [ADVISORY]: Rather than moving the mutable dict and lock as bare module-level state, this could be wrapped in a tiny `CostTracker` class with `track`, `snapshot`, `delta`, `reset` methods. This would make the "single accumulator" invariant structurally enforced (you pass around one object) rather than relying on import discipline. However — this introduces a new abstraction not present in the current code, violates the "same pattern as e2dd116" principle, and is better suited for a future refactor pass. Noting it as a future option, not a blocker.

5. **UNDER-ENGINEERED** [ADVISORY]: The proposal doesn't mention a smoke test or assertion that verifies the single-accumulator invariant post-migration. Something like `assert debate_common._session_costs is debate_common._session_costs` is trivially true, but a test that calls `debate_common._track_cost(...)` and then verifies `debate_common.get_session_costs()` reflects it — while also verifying `debate` module has no shadow `_session_costs` — would be a cheap regression guard. This is a nice-to-have, not a blocker, given the existing 932 tests cover the functional behavior.

## Concessions

1. **Atomicity constraint is correctly identified and well-argued.** The double-accumulator failure mode is real, silent, and would only manifest in production logs — not in tests. The "move pure functions first" naive alternative is correctly rejected with a clear explanation of the shadow-dict failure.

2. **Scope is appropriately narrow.** The non-goals list is explicit and reasonable. Moving exactly the cost-tracking unit and nothing else is the right granularity for a single commit.

3. **Operational evidence from e2dd116 is strong.** Same pattern, same team, same day, same test suite. The only new variable is mutable state, and the proposal correctly identifies that as the key risk and addresses it via atomicity.

## Verdict

**APPROVE** — The proposal correctly identifies the core risk (split accumulator), enforces the right constraint (atomic migration), follows an established pattern (e2dd116), and has appropriately narrow scope. The two MATERIAL findings are both low-cost fixes (state the import style explicitly; verify no reassignment of `_session_costs` in tests) that should be addressed during implementation but do not change the approach.

---

## Challenger B — Challenges
## Challenges
1. [ASSUMPTION] [ADVISORY]: The proposal assumes all cost-tracking access paths are enumerated by the listed 11 internal call sites, 4 sibling modules, and 2 test files. If any dynamic import, monkeypatch, or external script reaches `debate._session_costs`, `debate._track_cost`, or `debate.get_session_costs` directly, the migration could break observability or tests silently. This is primarily a compatibility assumption, not a clear blocker, but it should be verified with a repo-wide grep before merge.

2. [UNDER-ENGINEERED] [ADVISORY]: The plan preserves a module-level mutable accumulator in `debate_common`, which is acceptable for an atomic refactor, but it does not add a regression test specifically proving there is only one accumulator after migration. Given the stated failure mode is “silent cost loss in the audit log,” a focused test that writes via one import path and reads via another would materially improve confidence against future reintroduction of the split-state bug.

3. [RISK] [ADVISORY]: Cost data is consumed by `/healthcheck` and `cmd_verdict`, so the risk of not changing is continued blockage of the next 6 command extractions and persistence of stale `import debate` dependencies in sibling modules. The proposal addresses that risk directly; however, if any logging path still serializes cost state by referencing old symbols in `debate`, audit visibility could regress. This is a check-to-make, not evidence of a flaw in the approach.

## Concessions
- Correctly identifies the trust/integrity boundary: the mutable accumulator and its lock must move together to avoid split state.
- The atomic migration minimizes silent audit-log corruption risk better than a staged move would.
- Scope control is strong: no unnecessary unrelated migrations are bundled.

## Verdict
APPROVE — the proposal is sound for a refactor-only change, with the main follow-up being verification that no residual callers or tests still depend on old `debate` cost symbols.

---

## Challenger C — Challenges
## Challenges
None. The proposal correctly identifies the Python module-level state split-brain hazard and right-sizes the atomic commit to prevent it.

## Concessions
1. Correctly recognizing that module-level mutable state (`_session_costs`) dictates the atomic migration boundary, preventing silent audit logging failures.
2. Excellent discipline on scope management, explicitly listing the 5 specific subsystems (prompts, config, logging, etc.) that will *not* be in this commit.
3. Proactive updates to the lazy `import debate` comments in sibling modules, paying down the technical debt created during the initial sibling extractions.

## Verdict
APPROVE. The plan is technically sound, strictly bounded to unblock the remaining command extractions, and correctly mitigates the module-level state split-brain risk.

---

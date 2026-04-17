---
debate_id: debate-cost-tracking-findings
created: 2026-04-16T19:43:05-0700
mapping:
  Judge: claude-sonnet-4-6
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# debate-cost-tracking-findings — Independent Judgment

Judge model: claude-sonnet-4-6 (non-author)
Challenger mapping: {'A': 'claude-opus-4-6', 'B': 'gpt-5.4', 'C': 'gemini-3.1-pro'}
Consolidation: 14 raw → 8 unique findings (from 3 challengers, via claude-sonnet-4-6 via local)

## Judgment

### Challenge 1: Import style for debate.py call sites is unspecified
- Challenger: 1/3 challengers
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.75
- Rationale: The proposal explicitly cites "qualified references" as a benefit of the migration for 11 call sites in debate.py, but does not specify whether `import debate_common` (qualified) or `from debate_common import _track_cost` (unqualified) will be used. This is a real ambiguity — if unqualified imports are used, the stated ownership-clarity benefit evaporates. The fix is cheap: the proposal should commit to a specific import style before implementation.
- Evidence Grade: C (plausible reasoning from proposal text; no tool verification of current import patterns)
- Required change: Proposal must explicitly state the import pattern to be used in debate.py for the 11 call sites (e.g., "debate.py will use `import debate_common` and call sites will be `debate_common._track_cost(...)` qualified references"). The chosen pattern should be consistent with the import style already established in e2dd116 for the stateless helpers.

---

### Challenge 2: Enumeration of access paths is unverified
- Challenger: 2/3 challengers
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.70
- Rationale: The proposal already calls out `tests/test_debate_tools.py:120,157` as a specific verification step ("Verify ... still passes"), demonstrating awareness of non-obvious access paths. A repo-wide grep is standard due diligence and is a reasonable pre-merge step, but it doesn't rise to a blocking concern given: (a) the proposal enumerates specific line numbers for all known sites, (b) the 932-test suite would catch most broken imports at runtime, and (c) the challengers provide no evidence of actual missed sites — only the theoretical possibility. This is good practice advice, not a flaw requiring proposal revision.
- Evidence Grade: C (speculative concern without tool verification of actual missed paths)

---

### Challenge 3: Module-level mutable state vulnerable to reassignment-based reset
- Challenger: 1/3 challenger (A)
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.80
- Rationale: The concern is technically sound and specific. If debate.py re-exports `_session_costs` via `from debate_common import _session_costs` for backward compatibility, any code doing `debate._session_costs = {}` (reassignment) silently creates a new dict in debate's namespace while debate_common still holds the original accumulator. This is exactly the double-accumulator bug the atomicity constraint is designed to prevent, reintroduced through a re-export path. The proposal does not address whether backward-compat re-exports will be used or whether any existing code reassigns rather than `.clear()`s. The fix is a verification step, not a redesign.
- Evidence Grade: C (sound technical reasoning about Python name binding semantics; no tool verification of whether reassignment exists in practice)
- Required change: Proposal must specify: (a) debate.py will NOT re-export `_session_costs` or `_session_costs_lock` via `from debate_common import` (only `import debate_common` qualified access), OR if re-export is used for backward compat, it must be explicitly marked transitional with a comment; (b) a pre-merge grep confirms no production or test code does `debate._session_costs = {}` (reassignment vs `.clear()`).

---

### Challenge 4: No regression test proves single-accumulator invariant
- Challenger: 2/3 challengers
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.65
- Rationale: Both challengers correctly identify that the 932-test suite is functional and would not catch the structural split-state bug. Adding a focused invariant test is genuinely good practice. However, this is advisory — the proposal's atomicity constraint (migrating all 8 symbols together) is the architectural guard against the split-state bug. The test would be a belt-and-suspenders addition, not a required fix. The proposal already demonstrates the pattern works (e2dd116, 932/932). Recommending this as a follow-up is appropriate but not blocking.
- Evidence Grade: C (reasonable inference about test suite coverage; no tool verification)

---

## Spike Recommendations
None. All material challenges are resolvable through specification clarifications, not empirical tests.

---

## Evidence Quality Summary
- Grade A: 0
- Grade B: 0
- Grade C: 4
- Grade D: 0

**Note:** All material challenges are based on plausible reasoning from the proposal text and Python semantics, without tool-verified evidence from the actual codebase. This means the challenges are theoretically sound but may or may not reflect actual conditions in the repo. The accepted changes are low-cost clarifications that address real ambiguities regardless.

---

## Summary
- Accepted: 2 (Challenge 1: import style specification; Challenge 3: reassignment vulnerability verification)
- Dismissed: 2 (Challenge 2: unverified enumeration — advisory; Challenge 4: missing invariant test — advisory)
- Escalated: 0
- Spiked: 0

**Overall: REVISE with accepted changes**

The proposal is structurally sound — the atomicity constraint is correctly identified, the scope is appropriately narrow, and the operational evidence from e2dd116 is strong. The two accepted changes are both lightweight clarifications that can be resolved in the proposal text before implementation:

1. Commit to a specific import style for the 11 debate.py call sites (use `import debate_common` + qualified references to preserve the stated ownership-clarity benefit).
2. Confirm no reassignment-based reset exists for `_session_costs` and specify that backward-compat re-exports (if any) are explicitly marked transitional.

Neither accepted change requires redesign or additional commits. The proposal can proceed once these two points are specified.

---
decision: D14
original: "/check renamed to /review because the name should match the action"
verdict: HOLDS
audit_date: 2026-04-15
models_consulted: claude-opus-4-6, gemini-3.1-pro, gpt-5.4
---

# D14 Audit

## Original Decision

Rename `/check` to `/review` across the entire codebase (directory, SKILL.md, 193 cross-references in 39 files). The skill is a cross-model code review — "check" undersells it and sounds like a lint check.

## Original Rationale

Users reach for "review my code" not "check my code." The modes (`--qa`, `--governance`, `--second-opinion`) are all review sub-modes. The old name was `/review` before D12 consolidation — D14 restored it.

## Audit Findings

**3/3 models returned HOLDS with strong agreement.**

**Rationale holds:** The skill is a deliberative, multi-persona evaluation engine (PM + Security + Architecture). "Check" has standard developer meaning — lint check, CI check, status check — which is precisely what this skill is not. D15 (auto-detection: code → personas, documents → --models) was built on the renamed skill, confirming the name fits the evolved capability set.

**Alternatives adequately evaluated:** `/code-review` is doubly wrong — ergonomic friction (11 chars, hyphen) plus wrong semantics since the skill also reviews documents. Keeping `/check` was the only real alternative; it was correctly rejected for semantic collision with automated tooling conventions. One unexplored option (`/assess`) was noted by one reviewer but offers no improvement over `/review` on any axis.

**D14 corrected a D12 consolidation artifact:** D12's focus was merging (25 → 15 skills); naming was secondary. `/check` was a consolidation placeholder. D14 restored the name that was accurate before D12 changed it.

**Blast radius already sunk:** 193 cross-references across 39 files updated once. Reverting would require equal or larger churn with zero semantic gain.

## Verdict

**HOLDS**

The rename is semantically accurate, ergonomically correct, pipeline-coherent (think → plan → review → ship), and already load-bearing (D15 depends on it). No action needed.

## Risk Assessment

- **Risk of keeping (status quo):** Near zero. Name matches usage, pipeline narrative is coherent, D15 depends on it.
- **Risk of reverting:** Moderate-to-high. Would require another 193+ reference updates, reintroduce semantic ambiguity between qualitative AI review and deterministic lint checks, and contradict the D12 rip-and-replace philosophy. Zero functional gain.
- **Evidence basis:** EVIDENCED — pipeline structure, D15 dependency, cross-reference count, and 3-model unanimous verdict.

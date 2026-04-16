---
decision: D13
original: "Cross-model evaluation must use review-panel (parallel) not serial review calls"
verdict: HOLDS
audit_date: 2026-04-15
reviewers: [claude-opus-4-6, gemini-3.1-pro, gpt-5.4]
judge: gpt-5.4
accepted_findings: 0
dismissed_findings: 4
---

# D13 Audit

## Original Decision

Three rules for cross-model evaluation workflows: (1) use `review-panel` (parallel 3 models) instead of 3× `review` (serial) for independent evaluations; (2) run all persona simulations as parallel Agent calls, not serial; (3) stop iterating when consensus hits target.

## Original Rationale

Explore intake eval took ~75 min wall-clock. Root cause: 18 serial API calls (6 rounds × 3 models) when each round's 3 calls are independent. `review-panel` already parallelizes via ThreadPoolExecutor. Estimated savings: ~55 min (75→20 min) from orchestration changes alone, zero code changes.

## Audit Findings

All three independent reviewers (claude-opus-4-6, gemini-3.1-pro, gpt-5.4) returned **HOLDS**. Judge dismissed all 4 raised concerns:

1. **Terminology drift** (`review-panel` now a deprecated alias for `review`) — DISMISSED. The behavioral principle is correct; the naming evolved to match D14/D15 renaming. Current `orchestration.md` already references `review --personas` / `review --models`.

2. **Combining register+flow eval into one prompt per model** — DISMISSED. Framed as secondary optimization, not an outcome-changing flaw. Primary waste was serial→parallel, not prompt count per model.

3. **"Stop on consensus" could prematurely halt on biased agreement** — DISMISSED. Conservative-bias problem was separately addressed in D21 (orthogonal concern). D21 adds judge step for quality; D13 controls execution efficiency. These compose correctly.

4. **75→20 min savings estimate may be overstated** — DISMISSED. Estimate is labeled as such. Decision correctness does not depend on the precise magnitude — the structural inefficiency (18 serial independent calls) is evidenced.

## Verdict

**HOLDS**

D13 is an execution efficiency decision that leverages existing ThreadPoolExecutor parallelism in `debate.py`. It required zero code changes. Post-D13 developments (D14/D15 renaming, D21 judge step) are orthogonal and compose correctly.

The one wording note from reviewers: the rule should be read as "use the parallel multi-model path (`review --models` / `review --personas`)" rather than literally "use `review-panel`", since that command name is now a deprecated alias. The current `orchestration.md` text already reflects this correctly.

## Risk Assessment

- **Risk of keeping D13:** Minimal. Potential for terminology confusion since `review-panel` is deprecated, but the live rule text in `orchestration.md` uses current command names.
- **Risk of reversing D13:** High. Reverts to ~75-minute serial evaluation cycles with no quality benefit. No scenario where serial execution of independent evaluations produces better results than parallel execution.

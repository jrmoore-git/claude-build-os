---
decision: D6
original: "Explore flow presents 3 bets with fork-first format, not 1 committed direction"
verdict: REVERSE
audit_date: 2026-04-15
superseded_by: D11
---

# D6 Audit

## Original Decision

Explore generates 8-10 brainstorm options, clusters into exactly 3 bets that differ on 2+ dimensions (customer, product form, business model, distribution), presents the fork statement first, then 150-word descriptions and a comparison table. Human picks or redirects.

## Original Rationale

Previous flow picked "the most interesting" direction and developed it fully — skipping obvious answers for novelty. Fork-first with 3 bets lets the human see the trade-off before the AI commits. Tested across 15 personas, 4.6/5 average.

## Audit Findings

**Panel verdict: 2× REVERSE, 1× REVIEW.** No HOLDS votes.

**What holds:** The core principle — expose multiple divergent directions before committing — is correct, validated by testing, and carried forward by D11. Alternatives were rejected appropriately: 1 direction (no steering), 2 directions (false binary), 8-10 raw items (too many half-baked options). No conservative bias. D6 was an expansion from 1 to 3, not a descoping.

**What does not hold:** Every specific implementation element prescribed by D6 was replaced by D11 one day later (2026-04-11):

| D6 prescribed | D11 replaced with |
|---|---|
| Hardcoded dimensions (customer, product form, business model, distribution) | Domain-derived dimensions from pre-flight |
| Fork-first statement | Convergence/Divergence synthesis map |
| Comparison table | Qualitative synthesis with Strongest Ideas |
| 150-word descriptions | 800-word structured arguments |
| "3 bets" framing | "3+ divergent directions" |

D11's simulation evidence showed D6's product-market dimensions produced 3.4–3.8/5 on non-product questions vs 4.4+ after the domain-agnostic redesign. D6 assumed — without examining — that explore = product exploration. The shipped `/explore` SKILL.md and `debate.py` prompts reflect D11 entirely, not D6.

**Governance risk of keeping D6 active:** Any future model or developer reading D6 as a live decision would implement the fork-first format, comparison table, and hardcoded dimensions — all of which have been replaced. L13 is listed as "Subsumed by D6" but should map to D11.

## Verdict

**REVERSE — D6 is superseded by D11.**

This is a records-hygiene reversal, not a design change. The codebase already reflects D11. D6's core principle (multi-direction over single-direction) survived into D11 and remains valid. The specific prescription does not. Marking D6 as superseded closes the gap between the decision log and shipped reality.

## Risk Assessment

**Risk of reversal:** None. No code changes required. D11 already carries the principle.

**Risk of leaving D6 active:** Governance confusion. Future sessions referencing D6 as live would implement the wrong output format and wrong divergence dimensions. L13's reference chain is also broken until corrected.

## Required Follow-On Actions

1. Mark D6 in decisions.md as superseded by D11 (add note to D6 entry).
2. Update L13 reference from "Subsumed by D6" to "Subsumed by D11 (D6 was the intermediate step)".

---
decision: D11
original: "Explore mode is domain-agnostic with adaptive dimensions, not product-market-specific"
verdict: HOLDS
audit_date: 2026-04-15
models_used: claude-opus-4-6, gemini-3.1-pro, gpt-5.4
judge: gpt-5.4
---

# D11 Audit

## Original Decision

Redesign explore mode to derive divergence dimensions from the problem domain instead of hardcoding product-market dimensions (customer, revenue, distribution, product form, wedge). Pre-flight becomes a thread-and-steer adaptive protocol that infers domain on the fly. Old preflight files demoted to reference. Direction 3 forced to challenge the question's premise.

## Original Rationale

Explore was hardcoded for product-market strategy; engineering, organizational, research, and career questions got asked "who pays?" and "what's the adoption barrier?" Tested across 8 domains with 5 rounds of iteration: non-product questions improved from 3.4-3.8 avg to 4.4+ avg, domain appropriateness hit 5.0 with zero product-language leakage. Premise-challenge on Direction 3 was the single highest-leverage change (+1.0 on career and organizational questions).

## Audit Findings

**Rationale holds. [EVIDENCED]** BuildOS is a general-purpose solo-dev thinking framework with 22 skills spanning product, engineering, career, organizational, and process decisions. Hardcoding product-market dimensions was a scope mismatch. Implementation is confirmed: `config/prompts/preflight-adaptive.md` v7 exists with domain inference, SKILL.md routes to it exclusively, Direction 3 premise-challenge is implemented via the ASSUMPTIONS TO CHALLENGE section, old files retained as reference only.

**Conservative bias did not corrupt this decision.** D11 was an expansion, not a simplification. The pre-D21 pipeline's conservative bias pressed toward descoping; D11 went the other direction, suggesting the evidence was strong enough to overcome that pressure.

**Alternatives rejected soundly.** (a) More bucket types: recreates same rigidity. (b) No dimensions: causes direction convergence, violating D6's 2+ dimensional difference requirement. (c) Self-derive without pre-flight: contradicts D7's validated finding that pre-flight context quality drives output quality. No model challenged these rejections.

**Minor gaps identified (all advisory, non-blocking):**
- Product-domain quality under the adaptive system was not explicitly benchmarked. Gap worth monitoring.
- Dimension variance possible on exotic/niche domains — graceful degradation, not failure.
- Old preflight files could drift and mislead future maintenance.

## Verdict

**HOLDS**

3/3 models and independent judge concur. Operational evidence is specific and substantial. Risk of reversal is HIGH (reintroduces known failure mode); risk of keeping is LOW (bounded monitoring gaps). No evidence of bias corruption, context gaps, or flawed alternatives analysis.

## Risk Assessment

| Direction | Risk | Level |
|---|---|---|
| Keep D11 | Occasional dimension variance on exotic domains; product-quality gap not benchmarked | LOW |
| Reverse D11 | Immediate regression on non-product explore use cases; contradicts measured gains | HIGH |

**Recommended action:** Benchmark product-domain explore quality under the adaptive system in a future simulation run. No architectural change warranted.

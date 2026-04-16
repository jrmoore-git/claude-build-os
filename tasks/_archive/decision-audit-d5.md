---
decision: D5
original: "Thinking modes are single-model, not multi-model — prompt design drives quality"
verdict: REVIEW
audit_date: 2026-04-15
audit_models: claude-opus-4-6, gemini-3.1-pro, gpt-5.4
judge_model: gpt-5.4
judge_accepted: 4
judge_dismissed: 1
---
# D5 Audit

## Original Decision

explore, pressure-test, and pre-mortem use single-model calls. Multi-model reserved for validate and refine only. Rationale: "Tested 3 different models vs 1 model prompted 3 times with forced divergence. Single-model with divergence prompts produced more diverse output."

## Original Rationale

Cost (3x spend rejected), quality claim (tested diversity, not independence), and structural distinction (review/refine benefit from cross-family diversity, thinking modes don't). Decision treats explore and pressure-test as a unified category.

## Audit Findings

**F1: ACCEPTED (0.94) — Core test has no linked artifact.** The empirical comparison ("3 models vs 1 model prompted 3 times") cannot be verified. No file, no session log, no setup documented. [EVIDENCED]

**F2: ACCEPTED (0.84) — Multi-model baseline was likely corrupted.** D5 was made 2026-04-10. The context-injection bug (external models evaluated in a vacuum) was active at that time. If multi-model was context-starved vs. a context-rich session model, the comparison was invalid. [ESTIMATED]

**F3: ACCEPTED (0.86) — D5 measures the wrong quality dimension for pressure-test.** D5 measured output diversity (easy to achieve with prompting). Pressure-test quality requires reasoning independence (cannot be achieved by prompting a single model's distribution). D5's own rationale accepts cross-family diversity for validate/refine because correlated blind spots matter there — but pressure-test is the same type of adversarial/evaluative mode. The logic doesn't explain the asymmetry. [ESTIMATED]

**F4: ACCEPTED (0.88) — Missing middle alternative.** D5 evaluated all-multi-model vs. all-single-model. A selective approach — single-model for explore (generative, surface diversity sufficient), multi-model for pressure-test (adversarial, independence required) — was never considered. [EVIDENCED]

**F5: DISMISSED (0.79) — Explore mode likely holds.** D6 (4.6/5 across 15 personas) provides solid operational evidence that single-model explore works. Not a flaw; a finding in favor of keeping explore single-model as-is.

## Verdict: REVIEW

D5 holds for explore. D5 does not hold as a blanket rule covering pressure-test.

The explore/pressure-test split reveals a category error in the original framing. Explore is generative (surface diversity is sufficient). Pressure-test is adversarial (independence is the quality dimension that matters). D5's own rationale accepts multi-model for other adversarial modes (validate, refine) but treats pressure-test as equivalent to ideation without justification.

## Risk Assessment

**Risk of keeping D5 as-is:** Pressure-test runs with correlated blind spots. A plan built by Claude, pressure-tested by Claude, may miss the exact failure modes Claude systematically underweights. This is the correlated failure problem D5 itself identifies for validate/refine — but then ignores for pressure-test. [ESTIMATED, high-confidence by analogy]

**Risk of changing D5:** Cost increase (~2x for pressure-test subcommand if multi-model). No risk to explore. Implementation complexity is low — debate.py already supports multi-model via `--models` flag. [EVIDENCED]

## Required Changes

1. Amend D5 to split by mode: explore stays single-model (D6 evidence holds), pressure-test is reopened.
2. Run a controlled comparison for pressure-test: single-model adversarial vs. multi-model adversarial on 3-5 real plans. Measure whether multi-model catches risks single-model systematically misses (correlated-failure test).
3. Link or re-run the original benchmark under current context-complete conditions before using it as justification.
4. If multi-model wins for pressure-test: update D5 to "single-model for generative modes (explore), multi-model for adversarial/evaluative modes (pressure-test, validate, refine, review)."

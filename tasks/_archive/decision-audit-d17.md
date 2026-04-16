---
decision: D17
original: "Refine critique mode — document-type-aware refinement prevents consulting-deliverable drift"
verdict: HOLDS
audit_date: 2026-04-15
audited_by: claude-opus-4-6,gemini-3.1-pro,gpt-5.4
bias_bugs_applicable: false
---

# D17 Audit

## Original Decision

Added `--mode critique` to `debate.py refine` with three-layer auto-detection (frontmatter → content heuristic → default). Critique mode strips `REFINE_RECOMMENDATION_PRESERVATION_RULE` and `REFINE_STRATEGIC_POSTURE_RULE`, uses dedicated sharpening prompts, defaults to 2 rounds, and emits drift detection warnings on stderr. Track 2 (model routing) parked — no outcome data.

## Original Rationale

Refine rounds on the Brady VP sales memo turned a sharp pressure-test into a 120-day pilot plan with fabricated success criteria. Root cause: two prompt rules assume all documents are proposals. On critiques, "more specific" means "more actionable" which means consulting deliverable. A/B test: proposal mode +127% size, critique mode -21%. Audit of 10 prior refined docs: proposals refine correctly (7/10 sharpened, 3/10 same).

## Audit Findings

**3-model review: unanimous HOLDS (claude-opus-4-6, gemini-3.1-pro, gpt-5.4)**

**Bias bug applicability:** Neither structural bug applies here. D17 adds capability rather than descoping, and the core evidence (Brady A/B test, 10-doc audit) is quantitative data that context-vacuum evaluation could not corrupt. The prompt-rule mismatch is valid regardless of whether models had project context.

**Rationale integrity:** Holds. The root cause diagnosis is precise (two named prompt rules), the A/B test is concrete and directional, and the fix matches the diagnosis exactly. EVIDENCED.

**Alternative rejections:** Hold on all three. (a) Prompt-only without detection — users forget flags, same failure recurs. (b) Universal change — 10-doc audit proves proposal mode works; regressing the working case is wrong. (c) Post-processing filter — cannot distinguish legitimate proposal specificity from critique drift.

**Track 2 parking:** Appropriate. No outcome quality data exists to justify model routing per document type. Prompt differentiation already captures the behavioral difference. EVIDENCED.

**Implementation verified:** `--mode {proposal,critique}` exists; three-layer auto-detection implemented; prompt rules conditionally excluded; rounds default 2/6; drift detection on stderr; subtype routing (challenge vs pressure-test). EVIDENCED.

## Verdict

**HOLDS**

The decision is well-evidenced, correctly scoped, and not influenced by the conservative bias or context-vacuum bugs. Risk of reverting is high (re-enables consulting-deliverable drift on all critique refinements). Risk of keeping is low (detection edge cases mitigated by manual `--mode` override and drift observability).

## Risk Assessment

| Direction | Risk level | Basis |
|---|---|---|
| Keep D17 | Low | Detection errors possible; mitigated by --mode override and drift detection on stderr |
| Revert D17 | High | Immediately re-enables the failure mode on all challenge/pressure-test refinements |
| Activate Track 2 now | Medium | No outcome data; adds routing complexity without evidence of payoff |

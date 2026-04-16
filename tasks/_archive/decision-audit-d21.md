---
decision: D21
original: "Standard /challenge includes judge step — adversarial challengers no longer get the last voice"
verdict: HOLDS
audit_date: 2026-04-15
reviewers: claude-opus-4-6, gemini-3.1-pro, gpt-5.4 (review panel) + gpt-5.4 (judge)
judge_verdict: APPROVE (0 accepted, 3 dismissed, 0 spiked)
---

# D21 Audit

## Original Decision

Standard `/challenge` pipeline changed from challengers → synthesis to challengers → independent judge → synthesis. Judge sees both proposal evidence and challenger findings simultaneously. Judge model must not overlap with any challenger model. Judge prompt checks for conservative bias, cost-of-inaction, and whether challengers engaged with operational evidence.

## Original Rationale

A/B test on context-packet-anchors proposal (session 13): without judge, session model synthesized adversarial findings into maximal descoping — skipping extraction entirely. With independent judge (GPT-5.4), the extraction approach was preserved and robustness improvements were requested instead. Root cause: adversarial challengers get the last voice, and the session synthesizer has recency bias toward that voice. L28 and L29 both document this failure pattern with operational evidence.

## Audit Findings

**3-model review panel (claude-opus-4-6, gemini-3.1-pro, gpt-5.4): all three returned HOLDS.**

The rationale holds. The root cause analysis is structurally precise — adversarial last-voice plus recency-biased synthesis equals systematic conservatism. This is documented pipeline behavior (L28, L29), not a hypothetical failure mode.

Alternatives were rejected correctly:
- Rebuttal step: still filtered through the biased session synthesizer, doesn't break the structural loop
- Judge in --deep only: preserves the bug on every standard challenge run (the most common path)
- Weaken challenger prompts: removes the adversarial signal that makes challenge valuable; fixes the wrong thing

The one alternative not explicitly considered — prompt instructions to the synthesizer to resist recency bias — would be a weaker intervention because prompt instructions don't hold against structural incentives. The judge is a structural fix for a structural problem.

**Common risk flags from all three reviewers (rated ADVISORY, all dismissed by independent judge):**

1. **Judge overcorrection**: Anti-conservative-bias framing could cause the judge to dismiss valid challenges. *Mitigation already in place*: evidence grading (A/B/C/D) with enforcement rules means a well-evidenced challenge survives regardless of bias-checking instructions.
2. **Session over-deference to judge**: Synthesis may anchor too strongly on judge verdict. *Speculative, not demonstrated*. Changing the anchor from adversarial-last-voice to balanced-judge is the intended behavior.
3. **Partial model independence**: Model non-overlap helps but doesn't eliminate correlated failure. *Known limitation, explicitly accepted in design*.

Independent judge (GPT-5.4, no challenger overlap): APPROVE as-is. All three challenges dismissed as advisory.

## Verdict

**HOLDS.**

D21 fixes a real, documented structural bug. The solution is appropriate (structural fix for structural cause). The implementation is sound — evidence grading, model non-overlap, cost-of-inaction analysis, and conservative bias checks all target observed failure modes. The risks introduced are manageable and smaller than the risk of the original failure mode.

## Risk Assessment

**Residual risk to monitor:** Judge permissiveness rate. If the judge consistently overrides challenger recommendations, track whether dismissed challenges were genuinely generic or had Grade A/B evidence. Evidence grading provides the instrument; the threshold for recalibration is a pattern of Grade A challenges being dismissed.

**Risk of reverting:** Returns the system to the documented failure mode — systematic conservative descoping on every standard challenge, with no mechanism to weigh proposal evidence against adversarial findings.

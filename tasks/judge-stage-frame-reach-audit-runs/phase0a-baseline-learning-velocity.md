---
debate_id: learning-velocity-findings-v2
created: 2026-04-17T18:14:45-0700
mapping:
  Judge: gpt-5.4
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# learning-velocity-findings-v2 — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {'A': 'claude-opus-4-6', 'B': 'gpt-5.4', 'C': 'gemini-3.1-pro'}
Consolidation: 12 raw → 9 unique findings (from 3 challengers, via claude-sonnet-4-6 via local)

## Judgment

### Challenge 1: Hook “fired in last 30 days” pruning criterion lacks a data source
- Challenger: A/B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.95
- Evidence Grade: A (tool-verified via reported symbol/file searches showing no hook execution logging system)
- Rationale: This is a concrete implementation gap, not generic skepticism. The proposal presents hook fire recency as a specific pruning signal while also claiming “no new infrastructure,” but the challenge provides repo-grounded evidence that no such runtime hook telemetry exists. The proposal’s evidence about stale lessons supports measurement/verification, but it does not address this pruning mechanism at all.
- Required change: Remove or rewrite the “has this hook fired in the last 30 days?” criterion unless hook execution logging is first added explicitly as new infrastructure. If pruning remains in scope now, replace this sub-signal with something implementable without telemetry, such as static checks or manual review candidates.

### Challenge 2: Rule-hook redundancy detection has no specified mechanism
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.86
- Evidence Grade: C (plausible reasoning from transcript; absence-of-search-result supports lack of existing implementation, but not impossibility)
- Rationale: The challenge is valid insofar as the proposal states a concrete capability without specifying how it would be done. The absence of existing comparison logic does not by itself prove it cannot be added, but the proposal as written under-specifies whether this is manual annotation, heuristic matching, or LLM semantic comparison. Since the proposal’s own “simplest version” omits pruning, this looks more like future-scope than implementation-ready scope.
- Required change: Narrow the proposal to specify an implementable redundancy mechanism, or move rule-hook redundancy detection to a later phase. If retained now, define the method, cost, and failure modes explicitly.

### Challenge 3: Auto-triggered `/investigate --claim` creates prompt-injection/data-exfiltration risk
- Challenger: B
- Materiality: MATERIAL
- Decision: SPIKE
- Confidence: 0.63
- Evidence Grade: C (proposal text supports the automatic trigger claim, but repo-specific risk and exploitability are not verified)
- Rationale: The concern is substantively real: automatically passing lesson content into an external LLM is a security-relevant change, and the proposal does not mention field scoping or sanitization. However, the challenge does not provide tool-verified evidence about what `/investigate --claim` already scopes, strips, or sends, so under the stated rules this is not strong enough for outright acceptance in a high-risk domain. A targeted verification of the actual invocation path would resolve this.
- Spike recommendation: Inspect the exact payload construction for `/investigate --claim` when called from `/healthcheck`; test with 10 crafted lesson entries containing irrelevant context and prompt-injection strings. Success criteria: only intended claim fields are transmitted, surrounding lesson text is excluded or sanitized, and the model cannot alter execution behavior beyond claim evaluation. BLOCKING: YES

### Challenge 4: Coupling `/healthcheck` to `/investigate` makes cost less predictable
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.82
- Evidence Grade: B (supported by proposal’s own cost/frequency figures, but challenge is explicitly advisory)
- Rationale: Not judged as material per instructions. As an advisory note, it is reasonable, but the proposal already caps investigations to 2–3 and states full scans are low-frequency, so this does not presently undermine the proposal.

### Challenge 5: `git log` metrics are noisy proxies at current scale
- Challenger: A/B
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.88
- Evidence Grade: B (supported by proposal data plus observed low-N/bulk-edit pattern)
- Rationale: Not judged as material per instructions. As an advisory point, it is fair, but the proposal’s “simplest version” explicitly frames these as lightweight initial metrics to evaluate after a few sessions, which appropriately acknowledges uncertainty rather than overclaiming precision.

## Spike Recommendations
- **Security/input-scoping spike for auto-triggered `/investigate --claim`**
  - What to measure: Actual payload sent from `/healthcheck` into `/investigate --claim`; whether only claim-relevant fields are included; whether adversarial lesson text can influence prompt behavior or cause unrelated context disclosure.
  - Sample size: 10 crafted lessons, including benign stale entries and adversarial entries with injection strings, unrelated secrets-like text, and malformed claim content.
  - Success criteria: Payload is field-scoped; non-claim content is excluded or sanitized; no leakage of unrelated lesson/context data; investigation behavior remains bounded to claim verification.
  - BLOCKING: YES

## Evidence Quality Summary
- Grade A: 1
- Grade B: 2
- Grade C: 2
- Grade D: 0

## Summary
- Accepted: 2
- Dismissed: 2
- Escalated: 0
- Spiked: 1
- Overall: SPIKE (test first) if any blocking spikes

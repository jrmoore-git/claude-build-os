---
type: experiment
created: 2026-04-15
status: complete
---
# D4+D5 A/B Analysis: Single vs Multi-Model Pressure-Test

## Experiment Design

**Input:** `tasks/context-packet-anchors-design.md` (305-line design doc)
**Condition A (single):** `pressure-test --model claude-sonnet-4-6`
**Condition B (multi):** `pressure-test --models claude-sonnet-4-6,gemini-2.5-flash,gpt-5.4`
**Synthesis model:** gpt-5.4 (auto-selected, different family from inputs)

## Raw Results

| Metric | Single | Multi |
|--------|--------|-------|
| Output lines | 52 | 174 |
| Models that produced output | 1/1 | 2/3 (gemini timed out) |
| Distinct counter-theses | 1 | 2 + synthesis |
| Synthesis section | N/A | Yes (5 structured sections) |
| Unique insights not in single | N/A | 3 (see below) |

## What Multi-Model Added

### Unique findings only in multi-model output:
1. **Post-output classifier alternative** (Analyst A): Score outputs for specificity *after* generation and only re-prompt when generic. Avoids adding prompt complexity upfront.
2. **Relevance compression alternative** (Analyst B): Compress decision-relevant evidence into a "critical facts" brief before judging. Addresses the actual evidence from the user's own A/B tests.
3. **Disagreement surfacing** (Synthesis): Where analysts disagreed on "how much to build now," synthesis identified that B's position (limited experiment) was better-evidenced than A's (total delay).

### Overlapping findings (confirmed by both):
1. Wrong bottleneck risk (anchors vs context/evidence selection)
2. Slot extraction fragility
3. Shared anchors reducing useful diversity
4. Insufficient evidence for broad rollout

### What single-model found that multi also found:
All core findings from single-model appeared in multi-model. Multi-model added **breadth** (unique alternatives) and **adjudication** (synthesis resolved disagreements).

## Synthesis Quality

The synthesis section followed the 5-part contract (agreements, disagreements, unique findings, false positives, overall assessment). It correctly:
- Identified that one analyst's claim was speculative ("12-18 month models will absorb this")
- Resolved a real disagreement with evidence-based reasoning
- Flagged 3 top risks in priority order

## Failure Mode: Model Timeout

Gemini-2.5-flash timed out. The system degraded gracefully:
- Minimum 2 successful analyses met (2/3)
- Synthesis ran on the 2 successful outputs
- Mapping correctly showed only the 2 models that completed

## Conclusion

Multi-model pressure-test adds value through:
1. **Unique alternatives** that a single model misses (2 distinct counter-approaches)
2. **Disagreement adjudication** — synthesis identifies which position has stronger evidence
3. **False positive detection** — synthesis flags weak claims from individual analysts

Cost: ~3x tokens, ~2x wall-clock (parallel execution). Worth it for high-stakes proposals.
Not needed for routine pressure-tests on small changes.

## Recommendation

D5 multi-model mode validated. Recommend as default for:
- Pre-plan gates on T1+ features
- Strategic direction decisions
- Any proposal where the single-model output "feels too agreeable"

Keep single-model as default for routine use (speed, cost).

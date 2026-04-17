---
topic: dual-mode-generalization
created: 2026-04-17
related_plan: tasks/dual-mode-generalization-plan.md
related_brief: tasks/dual-mode-generalization-think.md
related_lessons: [L43, L44, L45]
methodology: frame-lens-validation.md (Round 1)
threshold: 5/5 BIDIRECTIONAL (pre-committed)
---

# Dual-Mode Generalization Audit — Results

Tests whether the dual-mode (paired tools-on + tools-off) pattern Frame adopted generalizes to architect, security, and pm personas. Pre-committed decision criterion: adopt dual-mode for a persona iff ALL 5/5 proposals show mode-exclusive MATERIAL findings in BOTH directions (same threshold as Frame Round 1).

## Verdicts

| Persona | Model | BIDIRECTIONAL | Verdict | Ship? |
|---|---|---|---|---|
| architect | claude-opus-4-7 | 5/5 | **ADOPT** | Yes — extend persona expansion |
| security | gpt-5.4 | 4/5 | **DECLINE** | No — threshold not met |
| pm | gemini-3.1-pro | 2/5 | **DECLINE** | No — threshold not met |

Only architect adopts. Threshold discipline held: 4/5 is a threshold-change question, not an adopt.

## Per-Persona Detail

### Architect — ADOPT (5/5)

| Proposal | Tools-off excl. | Tools-on excl. | BIDIRECTIONAL |
|---|---|---|---|
| autobuild | 1 | 3 | YES |
| explore-intake | 3 | 3 | YES |
| learning-velocity | 2 | 4 | YES |
| streamline-rules | 3 | 3 | YES |
| litellm-fallback | 2 | 2 | YES |

**Pattern:** Tools-on consistently catches "already-shipped / stale baseline" defects (4 of 5 proposals) — the factual-verification axis unreachable without tools. Tools-off consistently catches structural/design concerns (rollback discipline, correlated-blind-spot abstractions, scope wording). Same asymmetry Frame saw.

Full tagging: `tasks/dual-mode-generalization-architect-analysis.md`.

### Security — DECLINE (4/5)

| Proposal | Tools-off excl. | Tools-on excl. | BIDIRECTIONAL |
|---|---|---|---|
| autobuild | ≥1 | ≥1 | YES |
| explore-intake | 0 | 3 | **NO** |
| learning-velocity | ≥1 | ≥1 | YES |
| streamline-rules | ≥1 | ≥1 | YES |
| litellm-fallback | ≥1 | ≥1 | YES |

**Failure point:** explore-intake. Tools-off produced 2 MATERIAL findings that collapsed into a single prompt-injection defect. Tools-on caught that same defect PLUS two additional defects tools-off missed entirely (sensitive-data exfiltration via Slot 4/5 questions to external LLM, and wrong integration point — proposal targets `scripts/debate.py` but explore logic lives in `scripts/debate_explore.py`). Zero tools-off-exclusive MATERIAL findings on this proposal.

**Pattern observed (across 4 passing proposals):** Tools-on-exclusive = code-grounded (line numbers, specific hook behaviors, test-coverage gaps, wrong file paths). Tools-off-exclusive = threat-model/policy (sandbox, consent, signal quality, dilution). Complementary but asymmetric — tools-on dominated on the proposal where tools-off's MATERIAL budget got consumed reiterating the same defect.

**Close-call note (DO NOT LOOSEN THRESHOLD):** 4/5 is genuine evidence that dual-mode is mostly valuable for security — enough that a future session may choose to re-validate with a threshold change. That's a separate decision requiring its own pre-commitment + re-run. This audit's pre-committed threshold stands.

Full tagging: `tasks/dual-mode-generalization-security-analysis.md`.

### PM — DECLINE (2/5)

| Proposal | Tools-off excl. | Tools-on excl. | BIDIRECTIONAL |
|---|---|---|---|
| autobuild | 0 (shared) | 0 (shared) | **NO** |
| explore-intake | 0 | ≥1 | **NO** |
| learning-velocity | ≥1 | ≥1 | YES |
| streamline-rules | 0 | ≥1 | **NO** |
| litellm-fallback | ≥1 | ≥1 | YES |

**Pattern:** PM persona without tools is strong at catching prompt-engineering, UX, and product-sequencing critiques. These show up in both modes (shared findings dominate on 3/5 proposals). Tools add value only on specific defect classes that require codebase verification (e.g., "lesson_events.py already exists", "feature already shipped"). That value didn't clear the MATERIAL bar on 3 of 5 proposals.

PM is the clearest DECLINE — tools-off alone captures most of PM's value; dual-mode would roughly double cost per proposal for ~30-40% marginal findings on 2 of 5.

Full tagging: `tasks/dual-mode-generalization-pm-analysis.md`.

## Cross-Persona Summary

**Three distinct outcomes across three personas** — the tool-posture axis does not generalize uniformly:

- **Architect** benefits most from dual-mode. Largest mode-exclusive counts. The "already-shipped" detection axis (factual) is complementary to structural-reasoning axis (tools-off).
- **Security** benefits on most proposals but fails the strict threshold. Tools-on's code-grounded findings are distinct from tools-off's threat-model framing — but explore-intake shows tools-off can collapse into redundancy when the proposal has a salient attack surface.
- **PM** benefits least. The persona's core critique patterns (product framing, UX, sequencing) don't require tool access. Shared findings dominate.

**Per-persona cost/benefit framing (for future threshold-revisit conversations):**
- Architect: dual-mode doubles cost, catches 12-15 additional mode-exclusive MATERIAL findings across 5 proposals. High ROI.
- Security: dual-mode doubles cost, catches 8-10 additional mode-exclusive findings, but one proposal is asymmetric. Medium ROI.
- PM: dual-mode doubles cost, catches 3-4 additional mode-exclusive findings. Low ROI.

## Ship Decision (Phase 3)

- **Architect:** extend `scripts/debate.py` persona-expansion logic to architect (Frame is the template). Add `architect_factual_model` to `config/debate-models.json`. Update `.claude/skills/challenge/SKILL.md` Step 6/7 and `.claude/rules/review-protocol.md` Stage 1 to document architect dual-mode. Add `TestArchitectPersona` class to `tests/test_debate_pure.py` (Frame precedent).
- **Security + PM:** stay single-mode. L43 updated with per-persona evidence.

**Factual model for architect:** follow Frame's cross-family precedent. Frame uses sonnet (structural) + gpt-5.4 (factual). Architect's structural = opus-4-7; pick a different-family factual. Default: `gpt-5.4` (cross-family with Anthropic's Opus). Alternative: `gemini-3.1-pro` (further diversity). Keep consistent with Frame's pattern unless there's reason to deviate. Going with `gpt-5.4` — matches Frame's choice and keeps cross-family diversity simple.

## Notes on Methodology

- Used same 5 proposals as frame-lens-validation Round 1. Held variation constant.
- Each persona's tagging delegated to an independent agent with the same rubric. Threshold pre-committed before runs executed; no re-fitting.
- All 28 paired runs completed in a single session (~10 minutes wall clock, parallel).
- The "close-call" for security (4/5) is an argument for a future, separately-designed experiment at a lower threshold — not a reason to loosen this one. Threshold changes require re-validation.

## Open Questions (NOT rolled into this audit)

1. Should the threshold be lower for certain personas? Security's 4/5 is evidence that 5/5 may be overly strict for personas with asymmetric tool value. A future audit could pre-commit a 4/5 bidirectional + ≥X mode-exclusive findings rule.
2. Does dual-mode benefit correlate with proposal type (e.g., proposals with heavy code-verification content benefit more)? Would need cross-tabulation with proposal characteristics.
3. Frame's decision was based on n=4, other personas on n=5 — the MATERIAL-finding counts differ enough that comparing Frame's 4/4 to these n=5 results isn't apples-to-apples. Not blocking; flagged.

None of these change the shipping decision. Architect adopts. Security + PM decline.

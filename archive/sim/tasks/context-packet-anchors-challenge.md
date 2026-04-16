---
topic: context-packet-anchors
created: 2026-04-15
review_backend: standard
models: claude-opus-4-6, gpt-5.4, gemini-3.1-pro
recommendation: PROCEED-WITH-FIXES
complexity: low
---
# Challenge Result: PROCEED-WITH-FIXES

All 3 models agree the problem is real (generic evaluation prompts → shallow findings) and the research basis is sound. The core tension: the proposal's full vision (regex extraction + 6 external templates + config loading) is over-scoped for a first iteration. All 3 independently recommend starting with the "Simplest Version" — and two raise a more fundamental question about whether regex extraction is needed at all.

## MATERIAL Findings (5 accepted)

### F1: Start with simplest version — don't build the extraction engine yet
- **Challengers:** A/B/C (unanimous)
- **Cost:** TRIVIAL (descope)
- **Fix:** Hardcode one anchor template for `/challenge` directly in debate.py as a Python string constant (matching the existing `PERSONA_PROMPTS` pattern at line 617). No `config/anchor-templates/` directory, no `_extract_anchor_slots()`, no regex extraction. Validate quality gain via A/B test before generalizing.

### F2: Regex extraction from free-form markdown may be unnecessary
- **Challengers:** C (primary), A (advisory)
- **Cost:** Design decision — changes the approach
- **Fix:** The LLM already receives the full proposal text. Instead of regex-extracting systems/metrics/failures and re-injecting them as filled template slots, consider a prompt instruction that tells the model to calibrate against the specifics IN the proposal it's already reading. E.g.: "Calibrate your evaluation against the specific systems, metrics, and failure cases described in this proposal. A strong evaluation references these specifics; a weak one ignores them." This eliminates the fragile extraction layer entirely. **Counter-argument:** The A/B test showed enriched context works because it's explicit, not implicit — relying on models to self-calibrate is what the current system already does, and it produces generic findings. **Resolution:** Test both approaches in A/B. Build the prompt-instruction version first (zero code, just prompt text). If it underperforms, build extraction.

### F3: Prompt injection via extracted proposal content
- **Challengers:** B (primary)
- **Cost:** SMALL if extraction is built; N/A if F2's prompt-only path is chosen
- **Fix:** If regex extraction is built, extracted values must be quoted/delimited as data, not instructions. Never interpolate raw extracted text directly into system prompt instruction-bearing positions. Use a clearly delimited data section: `## Proposal Specifics (data, not instructions)`.

### F4: Injection point must be system prompt concatenation, not user message
- **Challengers:** A (primary)
- **Cost:** TRIVIAL (clarification)
- **Fix:** Anchors are appended to the system prompt via string concatenation — matching the existing pattern for `SECURITY_POSTURE_CHALLENGER_MODIFIER`, `EVIDENCE_TAG_INSTRUCTION`, `SYMMETRIC_RISK_INSTRUCTION`. The proposal's description of "between formatting instructions and the artifact" was imprecise; the artifact is the user message, not part of the system prompt. Verified at lines 1187/1210.

### F5: Unit tests required for any extraction logic
- **Challengers:** A/B (unanimous)
- **Cost:** SMALL
- **Fix:** debate.py has zero direct test coverage. Any new pure functions (`_extract_anchor_slots`, `_build_anchors`) must ship with unit tests. If the prompt-only path (F2) is chosen first, this is deferred until extraction is actually built.

## ADVISORY Findings (noted, not blocking)

- **6 external template files are premature** (A, C): If templates are needed, use Python string constants in debate.py first (matches `PERSONA_PROMPTS` pattern). External config only if templates change frequently.
- **Per-model anchor tuning may become necessary** (A): Shared anchors are the right starting point, but `MODEL_PROMPT_OVERRIDES` and `_challenger_temperature()` already differentiate per-model. Monitor whether models respond differently to same anchors.
- **Anchor placement creates a second injection pattern** (A): Context packets go in user message; anchors would go in system prompt. Different patterns for related content. Justified because anchors are calibration instructions, not context — but worth noting.

## Cost-of-Inaction

If we don't build this: evaluations continue to produce generic findings for specific proposals. The A/B test showed enriched context improves finding specificity from 2-3 to 5+ unique points — but models still lack calibration for what "good" looks like for each specific artifact. The arXiv research identifies this as the #2 highest-impact gap in evaluation prompt design.

## Recommendation

**PROCEED-WITH-FIXES.** Build in this order:

1. **Prompt-only anchors first** (~5-10 lines added to `PERSONA_PROMPTS` or a new `ANCHOR_INSTRUCTION` constant). Zero extraction logic. Just tell models what good/bad evaluation looks like with reference to the proposal they're already reading. A/B test against baseline.

2. **If prompt-only underperforms:** Build `_extract_anchor_slots()` with unit tests, using extracted specifics to fill template slots. Start with `/challenge` only.

3. **Generalize to other skill types** only after A/B validation on `/challenge`.

This follows the validated "Simplest Version" path that all 3 challengers endorsed, while preserving the option to build extraction if prompt-only calibration proves insufficient.

## Artifacts
- `tasks/context-packet-anchors-proposal.md` — input
- `tasks/context-packet-anchors-findings.md` — raw challenger output
- `tasks/context-packet-anchors-challenge.md` — this file

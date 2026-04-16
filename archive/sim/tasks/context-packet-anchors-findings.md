---
debate_id: context-packet-anchors-findings
created: 2026-04-15T17:51:17-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# context-packet-anchors-findings — Challenger Reviews

## Challenger A — Challenges
Now I have a complete picture. Let me formulate my review.

## Challenges

1. **ASSUMPTION** [MATERIAL] [COST:SMALL]: **The proposal says anchors go "into the system prompt between formatting instructions and the artifact," but the artifact (proposal) is the user message, not part of the system prompt.** Verified at line 1187/1210: `user=proposal` is separate from `sys_prompt`. The injection point description is imprecise. The actual injection would need to be either (a) appended to the system prompt before `TOOL_INJECTION_DEFENSE`, or (b) prepended to the user message before the proposal text. This matters because anchor placement relative to the proposal text affects whether models treat anchors as instructions vs. content to evaluate. The fix is straightforward — clarify that anchors are appended to `sys_prompt` (the existing pattern for `SECURITY_POSTURE_CHALLENGER_MODIFIER`, `EVIDENCE_TAG_INSTRUCTION`, etc.) — but the proposal should be explicit about this.

2. **UNDER-ENGINEERED** [MATERIAL] [COST:SMALL]: **No test coverage exists for debate.py, and the proposal adds regex-based extraction (`_extract_anchor_slots`) without any testing plan.** Verified: `check_test_coverage` returned `has_test: false` for `scripts/debate.py`. Regex-based slot extraction from free-form proposal text is exactly the kind of function that breaks silently on edge cases (empty proposals, proposals without metrics sections, proposals with unusual markdown formatting). The two proposed functions are pure and testable — the proposal should commit to unit tests for `_extract_anchor_slots` at minimum. This is especially important because a regex that extracts wrong slots produces subtly wrong anchors that degrade evaluation quality without any visible error.

3. **RISK** [MATERIAL] [COST:TRIVIAL]: **The proposal adds 6 template files in `config/anchor-templates/` but debate.py's `_load_config()` only reads `config/debate-models.json`.** Verified at lines 560-607: config loading is hardcoded to a single JSON file. The anchor templates would need their own loading mechanism. This is trivial to implement (just `open()` and `read()` the template file), but it introduces a new config loading pattern that diverges from the existing centralized config approach. The proposal should acknowledge this and decide whether templates are loaded at import time (like `PERSONA_PROMPTS`) or at call time (like `_load_config()`).

4. **RISK** [ADVISORY]: **Regex extraction from free-form markdown is inherently fragile.** The proposal says `_extract_anchor_slots` uses "regex-based extraction of systems, metrics, failures, requirements, evidence, decisions, constraints, and project goals." That's 8 slot types extracted via regex from arbitrary proposal text. When extraction fails (and it will for some proposals), the anchor template gets empty slots. The proposal should specify fallback behavior — does an empty slot produce a generic anchor, or does the anchor section get omitted entirely? The "simplest version" (hardcoded template for `/challenge`) wisely sidesteps this for the first iteration.

5. **OVER-ENGINEERED** [ADVISORY]: **Six template files for six skill types may be premature.** The proposal correctly identifies the "simplest version" as hardcoding one template for `/challenge`. The jump from 1 hardcoded template to 6 external template files is a significant complexity increase. The intermediate step — 6 templates as Python string constants in debate.py (matching the existing `PERSONA_PROMPTS` pattern at line 617) — would be more consistent with the codebase's current patterns and avoid the new config loading mechanism entirely.

6. **ALTERNATIVE** [ADVISORY]: **Anchors could be injected into the user message (proposal text) rather than the system prompt.** The existing pattern for context enrichment is that "context packets are passed as part of the proposal text, not as separate system prompt sections" (per the proposal itself). Injecting anchors into the system prompt creates a second injection pattern. Consistency with the context-packet approach would mean prepending anchors to the proposal text. This is a design choice, not a flaw — system prompt placement may actually be better for calibration instructions — but the proposal should justify the divergence from the established context-packet pattern.

7. **ASSUMPTION** [ADVISORY]: **The proposal assumes shared anchors across all 3 models "to preserve convergence," but the existing architecture already has per-model differentiation.** Verified: `MODEL_PROMPT_OVERRIDES` (line 1183) and `_challenger_temperature()` (line 1178) already customize behavior per model. Shared anchors are a reasonable starting point, but the proposal should acknowledge that per-model anchor tuning may become necessary if models respond differently to the same anchor framing (which the Databricks research on model-family-specific saturation points suggests is plausible).

## Concessions

1. **The incremental approach is sound.** The "simplest version" — hardcode one template for `/challenge`, test, then generalize — is exactly the right development strategy for a 4,136-line file with no test coverage. It limits blast radius.

2. **The injection point in the prompt assembly pipeline is well-chosen.** The existing pattern of string concatenation for prompt modifiers (`EVIDENCE_TAG_INSTRUCTION`, `SYMMETRIC_RISK_INSTRUCTION`, `SECURITY_POSTURE_CHALLENGER_MODIFIER`) is already established. Adding anchors as another concatenated segment is architecturally consistent.

3. **The research backing is credible and the problem is real.** The A/B test data from session 12 (thin vs. enriched context) provides concrete evidence that prompt enrichment improves evaluation quality. Anchors are a logical next step in that validated direction, and the non-goals (no per-model anchors, no full rubrics, no CoT instructions) show disciplined scoping.

## Verdict

**APPROVE** with the condition that the two MATERIAL items are addressed: (1) clarify the injection point as system prompt concatenation (matching existing modifier pattern), and (2) commit to unit tests for `_extract_anchor_slots` given the regex-on-freeform-text fragility and zero existing test coverage. Both are SMALL fixes that don't change the design.

---

## Challenger B — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposal introduces six new template files under `config/anchor-templates/`, but the existing config loader in `scripts/debate.py` only loads `config/debate-models.json` via `json.load` and there is no verified support for reading or validating anchor template files. That creates a trust-boundary risk: external file content would begin influencing system prompts without any described validation, fallback behavior, or path restrictions. At minimum, define how template selection is constrained to an allowlist of skill types, how missing/malformed templates fail closed, and how arbitrary filesystem paths are prevented.

2. [RISK] [MATERIAL] [COST:SMALL]: Injecting anchor text into the **system prompt** based on regex extraction from `proposal_text` moves untrusted proposal content across a privilege boundary from user content into higher-trust instructions. Even if the extracted fields are “just facts,” a malicious or malformed proposal can plant instruction-like strings (“ignore previous instructions”, XML/markdown delimiters, fake headers) into extracted slots, which then gain system-level authority when interpolated into anchors. The proposal should require escaping/quoting extracted values, delimiting them as data, and forbidding direct instruction-bearing content in slots.

3. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The design assumes regex extraction of “systems, metrics, failures, requirements, evidence, decisions, constraints, and project goals” is reliable enough to drive evaluation calibration, but no validation plan is provided for mis-extraction or adversarial formatting. If extraction is wrong, the system prompt can confidently bias reviewers toward fabricated priorities or omit real risks. The recommendation should include explicit fallback behavior when confidence is low: omit anchors, use a minimal generic anchor, or only populate slots with clearly delimited headings actually found.

4. [UNDER-ENGINEERED] [ADVISORY]: `scripts/debate.py` currently has no verified direct test coverage (`check_test_coverage` returned none). Adding prompt-construction logic that changes reviewer behavior across `cmd_challenge()` and likely `cmd_review()`/other paths without parser tests, golden prompt tests, and failure-mode tests raises regression risk. This doesn't by itself block the direction, but it should change next steps.

5. [ALTERNATIVE] [ADVISORY]: The proposal jumps to six per-skill template files, but its own “Simplest Version” suggests hardcoding one `/challenge` anchor first. Given `cmd_challenge()` is a verified insertion point and the repo shows no current anchor-template infrastructure, a one-skill rollout is the safer path to validate quality gains before adding more prompt-bearing config surface.

## Concessions
- The proposal correctly identifies a real gap: verified current persona prompts are generic and do not provide artifact-specific calibration.
- It keeps the change conceptually bounded to pure prompt-construction helpers rather than adding new networked or privileged subsystems.
- It explicitly avoids per-model divergence and chain-of-thought requirements, which reduces unnecessary prompt complexity.

## Verdict
REVISE with one-sentence rationale: the direction is promising, but before approval it needs explicit protections for prompt-injection via extracted proposal text and a concrete, validated template-loading/fallback design for the new config surface.

---

## Challenger C — Challenges
## Challenges

1. [RISK] [MATERIAL] [COST: MEDIUM]: Relying on regex to extract semantic concepts like "project goals", "failures", and "constraints" from unstructured proposal text is inherently brittle. Unless every proposal follows a rigid, machine-readable syntax for these elements, a 50-line regex function will either miss critical context or capture garbled text, corrupting the anchors injected into the prompt. 

2. [OVER-ENGINEERED] [MATERIAL] [COST: TRIVIAL]: The proposed solution extracts text from the proposal using regex, formats it into an external template, and feeds it back to the LLM in the system prompt. This is redundant because the LLM *already receives the full proposal text* in its context window. You are building an intermediate extraction layer for a model that natively excels at reading the source material. Instead of extracting, simply add an instruction to the persona prompts directing the model to extract and calibrate its own anchors based on the provided artifact.

3. [ALTERNATIVE] [ADVISORY]: The "Simplest Version" identified in the proposal (hardcoding one anchor instruction directly into `debate.py` for `/challenge`) is the correct starting point, yet the primary proposal jumps straight to building a multi-template system with a custom extraction engine. Validating the concept with a single inline prompt addition avoids building 6 external templates prematurely.

## Concessions
1. Accurately identifies a known failure mode: generic "be specific" instructions yield shallow, generic critiques. 
2. Grounded in validated A/B testing from Session 12, recognizing that more context requires better calibration to prevent model convergence on surface-level reasoning.
3. Proposes an excellent "Simplest Version" fallback plan that right-sizes the experiment.

## Verdict
REVISE to implement the "Simplest Version" (a single hardcoded prompt instruction in `/challenge`) instead of building a brittle regex-based semantic extraction engine.

---
*Quantitative Claims Audit:*
- "Context budgets doubled (1-8K to 8-16K tokens)": [EVIDENCED]
- "Databricks research (2,000+ experiments) confirms quality improves": [EVIDENCED]
- "debate.py runs ~5-10 times/day": [ESTIMATED] (Assumes current daily pipeline execution rates)
- "95+ entries in debate-log.jsonl": [SPECULATIVE] (Plausible based on runs, but unverified)
- "Tool calls went UP... Claude 34→40, GPT 13→19, Gemini 1→5": [EVIDENCED]

---

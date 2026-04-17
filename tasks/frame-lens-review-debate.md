---
debate_id: frame-lens-review-debate
created: 2026-04-17T12:46:44-0700
mapping:
  A: claude-opus-4-7
  B: gpt-5.4
  C: gemini-3.1-pro
personas:
  A: architect
  B: security
  C: pm
---
# frame-lens-review-debate — Challenger Reviews

## Challenger A (architect) — Challenges
The shuffle only affects what the judge sees (per the docstring line 392–393: "The original mapping is preserved in the output file; shuffling only affects what the judge sees"). So the output file `personas` frontmatter stays consistent with body headers. ✅ No issue.

### `_auto_generate_mapping` and verdict round [ADVISORY]
`debate_verdict.py` calls `debate._auto_generate_mapping(meta, challenge_body)` to reconstruct mapping from challenge output. The new persona-label frontmatter block could confuse this if it's parsing the YAML loosely. Worth confirming downstream `verdict` flow still produces sane output against a dual-mode frame challenge file — not verified in this diff, not in verification_commands. [ADVISORY] — add a verdict-round smoke test against a frame-dual challenge file, or verify manually.

### Dedup logic [ADVISORY]
Line 976 (`seen`) dedups on `(model, p)` before the frame expansion branch. If a user passes `--personas frame,frame` (unlikely but possible), the second `frame` is skipped correctly. If a user passes `--personas frame` with `enable_tools=True`, and the frame_factual_model happens to equal the frame model (e.g., both sonnet because `frame_factual_model` was removed from config), the dedup isn't re-checked against the factual half — you'd get two challengers on the same model. Defensive but minor. [ADVISORY].

### Test coverage [ADVISORY]
- Two new validator tests added. No test added for:
  - Frame dual-mode expansion (frame + `--enable-tools` → 2 challengers with correct `use_tools` flags).
  - Fallback interaction (the MATERIAL bug above would be caught by a fallback-mode test).
  - Dict-expansion in `_build_frontmatter`.
  - SKILL.md Step 1 code block consistency (it now says `architect,security,pm,frame`, and Step 7 also updated — both verified in diff).

Plan Change 7 explicitly listed four unit tests; only the validator-scope pair landed. The plan specified: "`frame` is in VALID_PERSONAS", "`frame` resolves to a model", "`PERSONA_PROMPTS["frame"]` exists and contains 'missing', 'candidate set', 'compositional'", "`cmd_challenge` accepts --personas frame without error". **None of these four plan-specified tests are in the diff.** [ADVISORY] — shipped tests (validator scope) address orthogonal fixes, not the core feature. The verification_commands run the full pytest suite which passes (959), but the feature itself lacks targeted tests.

---

## Summary

**[MATERIAL] findings: 1**
- **Security/Architecture — fallback mode interaction:** `args.enable_tools = False` flip (line 1046) happens *after* challenger construction (line 986 reads the pre-flip value). In a fallback episode, `--personas frame --enable-tools` will still create a `use_tools=True` frame-factual challenger and hit `llm_tool_loop` via the OpenAI SDK, which the guard explicitly says "can't call Anthropic tool API." Move the guard earlier, or have it post-process the challenger list.

**[ADVISORY] findings: 5**
- Scope drift (dual-mode added post-plan without re-gate).
- `_build_frontmatter` dict fix is one-level-deep only.
- `_auto_generate_mapping` in `verdict` round not verified against new frontmatter shape.
- Dedup doesn't re-check after frame expansion if `frame_factual_model` collides.
- Plan-specified feature tests (4 listed in Change 7) absent; only orthogonal validator tests shipped.

**No SPEC VIOLATIONS** on MUST-NOT / EXCLUDED clauses. The diff honors all five Non-Goals.

**Recommendation:** Fix the fallback bug (MATERIAL) before declaring shipped. The advisories are worth addressing but not blocking — most can land in a followup. The feature itself is architecturally sound; the validation evidence (n=5 paired + L44 methodology) is more rigorous than typical for this repo, and the rollback story is clean.

---

## Challenger B (security) — Challenges
## PM/Acceptance

- [ADVISORY] The implementation matches the refined plan’s core behavior: `frame` is added to persona config and validation (`scripts/debate_common.py:252-320`, `config/debate-models.json:2-16`), `/challenge` expands it into `frame-structural` + `frame-factual` when `--enable-tools` is set (`scripts/debate.py:979-1000`), and the skill/rule docs now instruct users to include `frame`. This is in-scope and right-sized for the stated problem.

- [ADVISORY] The validator-scope fix and frontmatter YAML fix are called out as orthogonal refinements in the updated plan, and the diff implements both (`scripts/debate.py:_validate_challenge`, `scripts/debate_common.py:_build_frontmatter`) with tests added for the validator path (`tests/test_debate_pure.py:321-369`). That is consistent with the refinement section, but there is no visible test coverage in this diff for the new dual-mode `frame` orchestration itself. Given the original plan required persona acceptance tests, I’d strongly recommend adding a focused unit test for `cmd_challenge` expanding `frame` into two challengers under `--enable-tools` to reduce regression risk.

## Security

- [ADVISORY] No new obvious trust-boundary violation is introduced by the frame lens itself. The factual half only enables the same existing tool loop path already used by other challengers, and the structural half explicitly disables tools (`scripts/debate.py:989-999`, `1110-1137`). From a security posture standpoint, that is a net improvement over making all frame analysis tool-enabled.

- [ADVISORY] The new `_build_frontmatter` nested-dict serialization writes raw keys/values into YAML without quoting (`scripts/debate_common.py:453-460`). In this diff the only new nested payload is an internally generated `personas` map with fixed keys/values, so there is no immediate injection issue. Still, the helper is generic now; if future callers pass user-derived strings containing `:`, `#`, or newlines, frontmatter parsing could break. Worth hardening before broader reuse.

## Architecture

- [MATERIAL] The dual-mode expansion adds a 5th challenger slot when the usual `architect,security,pm,frame` set is run with tools, but the code still indexes challengers purely by `debate_common.CHALLENGER_LABELS[i]` (`scripts/debate.py:1051-1054`, `1152-1155`). I did not verify the size of `CHALLENGER_LABELS` in this diff, and there is no guard here for “more challengers than labels.” If that label list is still sized for the prior panel, this will fail at runtime as soon as frame dual-mode is exercised. Even if it currently happens to be long enough, the architecture is brittle: challenger identity is now dynamic, but labeling remains fixed-position. This should be made length-safe before ship.

- [ADVISORY] The change is structurally coherent: persona selection now carries `{model, prompt, use_tools, persona_name}` rather than a loose tuple (`scripts/debate.py:958-1008`), which is a healthier boundary for mixed tool/no-tool challengers. That said, the duplicate-model warning logic still operates on the pre-expansion `persona_models` map (`scripts/debate.py:1009-1017`), so it will not warn if `frame_factual_model` collapses back onto an already-used model. That is not a correctness bug, but it weakens the intended “cross-family diversity” safeguard.

- [ADVISORY] The output/frontmatter shape has evolved from a simple label→model mapping to also include label→persona metadata (`scripts/debate.py:1177-1187`, `scripts/debate_common.py:453-460`). That’s a reasonable additive design, but it introduces a new informal output contract for downstream consumers. I don’t see verification in this diff that any consumers of debate artifacts tolerate the new nested `personas:` block. Risk of changing: downstream parsers may be YAML-fragile. Risk of not changing: dual-mode results would be ambiguous and harder to judge/dedup. The chosen direction is sensible, but it would benefit from at least one parser/consumer compatibility test.

---

## Plan clause extraction and verification

### EXCEPTION clauses
- None explicitly labeled as EXCEPTION in the plan.

### MUST NOT clauses
- “You do NOT critique the candidates in the proposal.”  
  - Verified implemented in `PERSONA_PROMPTS["frame"]` and `["frame-factual"]`. No contradiction seen.

- “Do NOT manufacture missing options just to produce findings.”  
  - Verified implemented in `PERSONA_PROMPTS["frame"]`. No contradiction seen.

- “Do NOT re-enumerate what exists in the codebase as ‘findings.’”  
  - Verified implemented in `PERSONA_PROMPTS["frame-factual"]`. No contradiction seen.

### EXPLICITLY EXCLUDED clauses
- Not changing the judge or refine phases.  
  - Verified: diff changes `cmd_challenge`, config, docs, lessons, tests; no visible judge/refine behavioral changes in reviewed snippets.

- Not gating `/plan` on frame findings differently from other findings.  
  - Verified: no special gating logic added in reviewed code.

- Not implementing a “frame quality score” or pre-flight check.  
  - Verified: no such scoring/check added.

- Not back-fixing the gbrain-adoption-refined.md spec.  
  - Verified: no such file touched.

- Not building a separate `cmd_frame_review` subcommand.  
  - Verified: frame is implemented as persona expansion inside `cmd_challenge`, not a new subcommand.

### Additional scope/allowed-path verification
- Allowed-path compliance: all changed files shown in the diff are within the plan’s allowed paths. No contradiction seen.
- Refined scope compliance: dual-mode expansion, cross-family `frame_factual_model`, validator scope fix, and frontmatter dict serialization fix are all implemented and match the refinement section.

### Quantitative claims in plan/docs touched by diff
- “n=5 paired validation…” / “~30 novel MATERIAL findings” / “BETTER on 4/5” / “TIED on 1/5” / “flipped 1 verdict” / “959 tests pass” / “2 existing validator tests updated; 2 new tests added” / “~30s vs ~75s” / “~25 tool calls” / “2.4x faster” / “~3x faster” / “~17 calls vs Sonnet’s ~56”  
  - All of these are **SPECULATIVE** within this review because the supporting artifact `tasks/frame-lens-validation.md` and test execution results were not provided in the diff snippets I verified. I therefore did not use them to drive any material verdict.

---

## Challenger C (pm) — Challenges
### Plan Exceptions & Exclusions Verification

*   **EXPLICITLY EXCLUDED:** "Not changing the judge or refine phases."
    *   **Status:** Verified. No changes to `cmd_judge` or `cmd_refine`.
*   **EXPLICITLY EXCLUDED:** "Not gating `/plan` on frame findings differently from other findings."
    *   **Status:** Verified. Findings are output as standard type tags (ALTERNATIVE, ASSUMPTION) and processed natively.
*   **EXPLICITLY EXCLUDED:** "Not implementing a 'frame quality score' or pre-flight check."
    *   **Status:** Verified. Implemented strictly as a standard adversarial persona.
*   **EXPLICITLY EXCLUDED:** "Not back-fixing the gbrain-adoption-refined.md spec"
    *   **Status:** Verified. No changes to Jarvis-repo specs.
*   **EXPLICITLY EXCLUDED:** "Not building a separate `cmd_frame_review` subcommand."
    *   **Status:** Verified. Handled directly inside `cmd_challenge`.

### Quantitative Claims

*   "caught ~30 novel MATERIAL findings" -> **[EVIDENCED]** via `tasks/frame-lens-validation.md`
*   "flipped 1 verdict (litellm-fallback REVISE → REJECT)" -> **[EVIDENCED]** via `tasks/frame-lens-validation.md`
*   "BETTER on 4/5 proposals and TIED on 1/5" -> **[EVIDENCED]** via `tasks/frame-lens-validation.md`
*   "~3x faster (GPT terminates tool loops in ~17 calls vs Sonnet's ~56)" -> **[EVIDENCED]** (based on L43 lesson records)

---

### PM / Acceptance

*   **[MATERIAL] Scope Right-Sized:** The diff elegantly implements the dual-mode frame expansion entirely within the existing parallel execution loop inside `cmd_challenge`. It fulfills all refined requirements (tool disabling for structural, config-driven model selection for factual) without expanding the CLI contract.
*   **[MATERIAL] Validator Scope Fixed:** The `_validate_challenge` patch correctly constrains the tag checks to the `## Challenges` section. This resolves the false-positive friction explicitly identified during validation.
*   **[ADVISORY] Prompt Guardrails:** The `frame` prompt includes an explicit "Do NOT manufacture missing options just to produce findings" and "APPROVE is valid" which protects against the common failure mode of forced adversarial output on perfectly good proposals.

### Architecture

*   **[MATERIAL] Concurrency Safety:** `cmd_challenge` dynamically adds challenger dictionaries to the array before distributing them to the `ThreadPoolExecutor`. The array size bounds the number of workers. Adding a 5th (or 6th via dual-mode) challenger scales cleanly. The `CHALLENGER_LABELS` list handles the labeling symmetrically up to index limits.
*   **[MATERIAL] Dict Serialization Fix:** The patch to `_build_frontmatter` expanding nested dicts ensures valid YAML generation for the new `extras` containing `{"personas": ...}`. This is structurally sound and safely prevents serialization crashes or parse failures downstream.
*   **[ADVISORY] Config Fallback Layering:** `debate_common.py` safely injects `frame_factual_model` into `defaults`, meaning old or unmigrated local `debate-models.json` files will cleanly fall back without throwing `KeyError`s.

### Security

*   **[MATERIAL] Tool Isolation Boundary:** The prompt injection risk of passing `--enable-tools` to the negative-space `frame` persona is mitigated structurally inside Python (forcing `use_tools=False` in the dict), rather than relying on LLM prompt instructions ("Do not use tools") which models routinely ignore. This ensures true operational isolation for the structural review.
*   **[ADVISORY] Data Paths:** The dual-mode execution passes unchanged through the existing `_run_challenger` and `_call_litellm` pathways, inheriting all existing API key management, retry logic, and sanitization boundaries without introducing new external network calls.

---

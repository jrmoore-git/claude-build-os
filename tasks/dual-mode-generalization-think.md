---
generated_by: /think refine
generated_on: 2026-04-17
branch: main
status: DRAFT
related: tasks/frame-lens-validation.md, tasks/lessons.md (L43, L44)
---

# Brief: Dual-Mode Generalization Audit (architect / security / pm)

## Problem Statement
The Frame persona adopted dual-mode (paired tools-on + tools-off halves) because n=5 validation showed every proposal had mode-exclusive MATERIAL findings in both directions (L43). It is an open question whether the same verification-vs-reasoning tool-posture axis generalizes to the other debate personas — architect, security, pm — or whether Frame's structural-vs-factual split is uniquely tied to "critique the candidate set" work.

Until this is answered per-persona, we either under-ship (leaving mode-exclusive findings on the table for 3 of 4 personas) or over-ship (expanding all personas into dual-mode without evidence the split earns its cost).

## Proposed Approach
Apply the frame-lens-validation Round 1 methodology, unchanged, to each of the other three personas:

- **Personas + models:** architect (claude-opus-4-7), security (gpt-5.4), pm (gemini-3.1-pro) — same assignments already used in `config/debate-models.json`.
- **Proposals:** same 5 used in frame-lens-validation Round 1 — autobuild, explore-intake, learning-velocity, streamline-rules, litellm-fallback. Re-using holds the axis of variation to "persona" only.
- **Runs:** for each persona, run each proposal twice — once tools-on (`--enable-tools`), once tools-off. 3 personas × 5 proposals × 2 modes = 30 single-persona runs (~15 paired comparisons).
- **Comparison:** for each proposal+persona, tag MATERIAL findings as mode-exclusive-to-tools-on, mode-exclusive-to-tools-off, or present-in-both. Same rubric as frame Round 1.

### Decision criterion (pre-committed)
**Adopt dual-mode for a persona iff every one of 5 proposals shows mode-exclusive MATERIAL findings in BOTH directions** (same threshold as Frame, L43). A persona failing this bar (e.g., 4/5 bidirectional, or 5/5 only one direction, or tools-on consistently dominates) does not adopt — document the asymmetry in L43.

This threshold is locked before any runs execute. No re-fitting after seeing data.

### Shipping pattern (per outcome)
- **All 3 generalize:** extend the Frame persona-expansion logic in `scripts/debate.py` to architect/security/pm. Frame implementation is the template. Ship with paired-validation evidence doc.
- **Some generalize:** ship only those; leave others single-mode; update L43 with per-persona evidence + reasoning for the non-adopters.
- **None generalize:** document in L43 that Frame's dual-mode structure is unique to candidate-set critique work; close the question.

## Key Assumptions
1. Frame-lens-validation Round 1 methodology is sound and portable — same 5 proposals carry enough variation across domains to stress-test a persona. (Evidence: Round 1 passed peer review; zero regressions across Rounds 1–3.)
2. Each persona's current model assignment is the "right" model — we are testing dual-mode at the assigned model, not re-opening model choice. (Evidence: `config/debate-models.json` is current production config.)
3. MATERIAL-finding tagging is reproducible enough that two humans agree on mode-exclusive classification. (Evidence: Round 1 produced clean tags; frame-lens-review passed.)
4. 30 single-persona runs is within cost/latency budget — no need to batch across sessions. (Evidence: Round 1 completed same-session; Sonnet outlier known but not blocking.)

## Risks
1. **Re-fit temptation after data lands.** Strong threshold pre-commit (5/5 bidirectional) mitigates. If we see a 4/5 result and are tempted to adopt anyway, that is a threshold change — document it as such and re-validate, don't silently loosen.
2. **Latency outlier reproduction.** Sonnet hit 324s on litellm-fallback structural in Round 3 (per prior session-log). Architect is Opus, not Sonnet — different model — but the same proposal may still be a latency risk across personas. Budget time; don't block shipping on a single outlier.
3. **Cross-proposal noise.** A persona may look mode-exclusive on noisy proposals but not on well-specified ones. Mitigated by using the exact 5 proposals Frame used — variation is held constant.
4. **Premature generalization ("Frame worked, so all must").** The decision criterion is per-persona, not global. Explicitly allow for "generalizes to architect, not to pm" outcome.
5. **Infrastructure drift since Round 1.** `scripts/debate.py` has had edits since Frame shipped. Verify the persona-expansion logic still works as documented before first paired run (one smoke-test paired run on a single proposal + persona before the full 30).

## Simplest Testable Version
**Phase 0 (smoke test, 1 paired run):** run architect persona, tools-on + tools-off, on one proposal (e.g., autobuild). Confirm: (a) both modes return structured findings, (b) MATERIAL tagging works on the output, (c) no debate.py crash, (d) latency acceptable. If Phase 0 passes, proceed to full 30-run matrix. If Phase 0 surfaces a bug, fix-forward before scaling.

**Phase 1 (full matrix):** 30 runs as described above. Output: `tasks/dual-mode-generalization-results.md` with per-persona per-proposal MATERIAL-finding tables + the pre-committed 5/5-bidirectional decision per persona.

**Phase 2 (ship):** extend persona expansion to the personas that passed the threshold, following Frame as template. Update L43 with per-persona evidence regardless of adopt/decline.

## Next Action
`/plan` on this brief to produce the 30-run matrix + Phase 0 smoke test + ship checklist. Plan should include: exact `debate.py` invocations per run, output file naming convention, MATERIAL-finding rubric reference (point to frame-lens-validation), and the decision table template.

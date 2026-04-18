# Source data inventory

Audit of which real refined specs can seed which benchmark failure modes. Compiled 2026-04-18 from `tasks/refine-frame-directive-validation/`.

## Real specs with unfixed Frame Check concerns (DRIFT / RESURRECT candidates)

Eight specs. For DRIFT, we copy the spec into a fixture and author a fail-diff that implements the flagged concern. For RESURRECT, the same specs can be repurposed with the fail-diff implementing an alternative the judge stage rejected (reconstructed from the proposal's alternative space).

| Source file | Unfixed concern(s) | Category keywords (for scorer) | Suited to |
|---|---|---|---|
| `autobuild-v3.md` | Inherited frame (external-source validation) | `inherited-frame` | DRIFT |
| `learning-velocity-v3.md` | Load-bearing assumption (lesson structure), Inflated problem (one sample) | `load-bearing-assumption`, `inflated-problem` | DRIFT |
| `litellm-fallback-v3.md` | Inflated problem (onboarding cliff), Load-bearing assumption (Anthropic as fallback) | `inflated-problem`, `load-bearing-assumption` | DRIFT |
| `streamline-rules-v3.md` | Load-bearing assumption (file list completeness), Inflated problem (effectiveness claim) | `load-bearing-assumption`, `inflated-problem` | DRIFT |
| `streamline-rules-v4.md` | Load-bearing assumption (runtime files + token savings) | `load-bearing-assumption` | RESURRECT (alternative compression approach) |
| `streamline-rules-v5.md` | Load-bearing assumption (enumerated files still exist) | `load-bearing-assumption` | RESURRECT |
| `autobuild-v4.md` | Inherited frame, Inflated problem | `inherited-frame`, `inflated-problem` | DRIFT |
| `autobuild-refined-new.md` | Load-bearing assumption (plan artifact completeness) | `load-bearing-assumption` | DRIFT |

Real data covers DRIFT (5 pairs from `autobuild-v3`, `learning-velocity-v3`, `litellm-fallback-v3`, `streamline-rules-v3`, `autobuild-v4`) with concerns that vary across three categories (`load-bearing-assumption`, `inflated-problem`, `inherited-frame`). Mode coverage is good — not all concerns are one category.

For RESURRECT, real data gives ≥2 pairs (`streamline-rules-v4` / `-v5`, `autobuild-refined-new`). Remaining 3 pairs need synthetic or semi-synthetic construction: pick a sound spec and author a synthetic Frame Check section listing a "rejected alternative" that the judge supposedly considered, then author fail-diff implementing that alternative.

## Real specs with frame-sound verdict (negative-control + NEW_DEFECT / SCOPE seeds)

Four specs. Direct use for negative controls. Also used as the "clean spec" that seeds synthetic NEW_DEFECT and SCOPE fail-diffs (the defect is introduced at implementation time against a frame-sound spec).

| Source file | Notes |
|---|---|
| `autobuild-v5.md` | Autobuild v5 — frame sound. Good candidate for NEW_DEFECT (hardcoded threshold introduced in diff). |
| `learning-velocity-v5.md` | Learning velocity v5 — frame sound. Good for SCOPE (diff adds out-of-scope lesson archiver). |
| `litellm-fallback-v5.md` | LiteLLM fallback v5 — frame sound. Good for NEW_DEFECT (flag name embedding deprecated-provider premise). |
| `negative-control-v5.md` | Explicit negative-control spec (verbose-flag proposal) — frame sound. Use as first negative control fixture. |

## Mode-by-mode plan

- **DRIFT (5 pairs):** all from real unfixed-concern specs above.
- **RESURRECT (5 pairs):** 2 from real data (`streamline-rules-v4`, `autobuild-refined-new`), 3 synthetic (author synthetic Frame Check section pointing to a rejected alternative on top of a real proposal).
- **NEW_DEFECT (5 pairs):** synthetic against 3 frame-sound specs (reuse specs; vary defect type: hardcoded threshold, shipped-premise flag, rare-case-as-common).
- **SCOPE (5 pairs):** synthetic against 3 frame-sound specs (reuse specs; vary scope-expansion type: extra feature, unrelated refactor, speculative helper).
- **Negative controls (2):** `autobuild-v5` and `negative-control-v5`, each with a matched-scope pass-diff that implements only what the spec allows.

## Open caveats

- The 4 modes are not equally populated by real data. DRIFT is best-covered; NEW_DEFECT and SCOPE are almost fully synthetic. Synthetic fixtures risk confirmation bias if the fail-diff is authored by the same hand that writes the scoring rules. Mitigation: for synthetic fixtures, the concern_keyword list comes from the spec's category set, not from the fail-diff author's intent.
- We are reusing some specs across fixtures (e.g., `autobuild-v5` for both negative control and NEW_DEFECT). Fixture IDs must be distinct; scoring must treat each invocation independently to avoid cross-contamination.
- Real-data specs were produced by the refine prompts across 5 iterations. The Frame Check wording varies between iterations. For the scorer's "explicitly names" test, we use the verbatim phrase from the *specific file copied into the fixture*, not a generalized form.

---
topic: review-lens-linkage
generated_by: /think discover
date: 2026-04-18
branch: main
status: DONE
mode: Builder
---

# Design: Review-lens Linkage — Frame Check Enforcement

## Problem Statement

The Frame pattern shipped in `/challenge` (D28, 4th persona) and extended to judge (D30) and refine (D31) stages produces a structured `### Frame Check` subsection inside `tasks/<topic>-refined.md`. That subsection is a status list: (a) unfixed concerns, (b) "covered at section X" pointers, or (c) "frame is sound."

`/review` (code review) already reads the refined spec into the PM lens prompt for spec compliance. But nothing specifically targets the `### Frame Check` subsection or its status-list semantics. The unknown: **does existing PM-lens compliance already catch Frame defects that leak into code, or is there a gap?**

Unlike judge and refine — which **generate** Frame findings against a proposal or document — review's role is **enforcement**: verify that the diff against the ultimate spec does not implement what the spec said was a frame defect, does not resurrect rejected alternatives, does not introduce new defects, and does not expand scope silently.

Per L47: we cannot iterate on a review-stage Frame directive without a baseline benchmark. Qualitative "looks cleaner" is pattern-matching, not evidence.

## What Makes This Cool

The symmetric move — adding a 4th Frame-enforcement lens to `/review` — is the aesthetically satisfying answer. But the user's feedback (2026-04-18, saved as `feedback_debate_ground_in_impact.md`) explicitly rejects that frame: debate modifications must be justified by measured impact on outcome quality, never by shape. The cool version of this work is the one that **refuses to build a directive until the benchmark proves one is needed**. It inverts the prompt-engineering-treadmill default mode and installs a measurement discipline that future pipeline extensions can reuse.

## Premises (agreed)

1. All four review-stage failure modes are in scope: spec drift during implementation, resurrection of rejected alternatives, new frame defects introduced at implementation, silent scope expansion.
2. Current `/review` has partial coverage — PM lens reads the refined spec and does generic compliance, but nothing specifically targets the `### Frame Check` subsection's status-list semantics.
3. Benchmark must exist before iterating on any directive (L47).
4. Linkage shape (directive location, lens count) is chosen by measured detection rate on the benchmark, not by symmetry with `/challenge`'s 4th Frame persona (new feedback memory).
5. `refined.md` may not exist for every `/review` invocation. Frame Check linkage applies only when it does; the rest of `/review` proceeds unchanged.

## Independent Perspective

Not run — decision was to move directly from premises to alternatives once the user re-grounded the question as impact-first. A post-benchmark second opinion may be useful before committing to any directive in phase 2.

## Approaches Considered

### Approach A: Extended PM lens + Frame Check parser

Add a parser to `/review` Step 4 that extracts the `### Frame Check` subsection from `tasks/<topic>-refined.md`. Augment the Step 5 PM-lens system prompt with an explicit "Frame Enforcement" sub-directive that takes parsed unfixed concerns as structured input and checks each against the diff. Single skill edit plus a parser function.

- **Pros:** Smallest diff that can still target Frame Check's status-list format. PM lens already has compliance framing; Frame Enforcement sub-directive calibrates on benchmark per L47.
- **Cons:** Co-mingles Frame signal with PM compliance signal; harder to measure the directive in isolation. Requires careful calibration (refine v2 cautionary tale).

### Approach B: Dedicated Frame-enforcement lens

New 4th persona `frame-enforcement` in `scripts/debate.py`. Added to the `/review` Step 5 persona list. Dedicated prompt reads only the Frame Check section and evaluates each unfixed concern against the diff.

- **Pros:** Maximum separation of concerns. Lens can be measured in isolation. Symmetric with `/challenge`'s 4th Frame persona.
- **Cons:** Larger change (debate.py persona + skill edit + new prompt). Symmetry is not a justification per the impact-first principle. Adds another LLM call per review. Over-correction risk (L47 refine v2): a dedicated lens with a narrow brief is easier to mistune into silent failure.

### Approach C: Benchmark-only, no code change yet (RECOMMENDED)

Build the benchmark first. No change to `/review` or `debate.py`. Measure baseline detection rate of Frame-defective diffs by the current PM-lens compliance path. Only add an enforcement directive if the benchmark shows a gap.

- **Pros:** Honest about the possibility that existing spec-compliance already handles Frame Check. Inverts the default prompt-engineering treadmill. The benchmark itself is reusable scaffolding for any future review-stage directive work. If gap is found, the benchmark is already built to calibrate A or B.
- **Cons:** Delays any enforcement directive by one benchmark-build cycle. Requires constructing paired diffs across 4 failure modes, which is the actual research work.

## Recommended Approach

**Approach C.** L47 is load-bearing. The previous "iterate refine v1 → v5 without a baseline" episode is exactly the pattern we're supposed to have learned from. Build the benchmark, measure current detection, then decide.

If the benchmark shows PM-lens compliance already catches ≥80% of Frame Check defects at zero or near-zero FP rate, declare done and document the linkage. If it shows a gap, the next iteration is A (smaller change, easier to calibrate). B is reserved for the case where A hits a calibration ceiling.

## Open Questions

- **Benchmark construction:** how do we source paired (fail/pass) diffs for each of the 4 failure modes? Can we synthesize from existing judge-frame-directive-validation and refine-frame-directive-validation artifacts, or does this need fresh data? Likely some of each — the refined spec and its Frame Check exist for shipped work; we may need to author diffs that deliberately violate or respect them.
- **Negative controls:** how many frame-sound specs do we need to validate that we're not flagging compliant diffs? Minimum 2, probably more.
- **Detection threshold:** what counts as "detected"? A finding tagged [MATERIAL] that names the specific Frame Check concern, or any finding that touches the affected lines? Strict vs. permissive scoring matters for interpretation.
- **Benchmark reusability:** can this benchmark scaffold later work on premortem / explore-synthesis / think-discover frame directives, or does each pipeline stage need its own test set?

## Success Criteria

**Phase 1 (benchmark):**
- Benchmark harness exists at `scripts/review_frame_benchmark.py` (or equivalent) and can run end-to-end against a fixed benchmark directory.
- ≥5 paired fail/pass diffs per failure mode × 4 modes = ≥40 evaluation cases + ≥2 negative controls.
- Baseline detection rate measured for current `/review` against each failure mode.
- Results documented in `tasks/review-lens-linkage-benchmark.md` with per-mode breakdown and overall Pareto plot.

**Phase 2 (only if Phase 1 shows a gap):**
- Directive (A) calibrated against benchmark with paired-A/B comparison to baseline.
- New directive is Pareto-dominant: ≥ baseline detection AND ≤ baseline FP rate.
- Zero silent-failure modes (per refine v2 lesson).

## Next Steps

1. **Build the benchmark** before any `/review` or `debate.py` edits.
2. **Draft the benchmark spec** — failure-mode taxonomy, scoring rules, paired-diff generation plan. Write to `tasks/review-lens-linkage-benchmark-plan.md` before writing any code.
3. **Source test data** — inventory existing refined specs on disk; identify which can support paired-diff construction vs. which need synthetic data.
4. **Run baseline** — current `/review` against full benchmark, no changes. Capture detection matrix.
5. **Decide from evidence** — if gap, proceed to Approach A with benchmark as calibration target. If no gap, document the linkage in `/review` SKILL.md and close.

First concrete action: write `tasks/review-lens-linkage-benchmark-plan.md` that specifies failure-mode taxonomy, paired-diff construction methodology, and scoring rules. This is the `/plan` artifact for the benchmark itself.

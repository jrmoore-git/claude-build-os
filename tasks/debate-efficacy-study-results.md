---
topic: debate-efficacy-study
verdict: SUPERSEDED — see tasks/debate-arm-comparison-design-refined.md
status: closed — methodology flawed, verdict discarded
confidence: null
n_proposals: 5
methodology: retrospective-paired-with-blinded-adjudication
all_findings_avg_gap_D_minus_C: -7.0
material_only_avg_gap_D_minus_C: -2.0
dd_coverage_C_pct: 64.0
dd_coverage_D_pct: 72.0
overall_precision_C: 0.988
overall_precision_D: 1.0
intra_arm_variance_gap_findings: 4
judge_model: gemini-3.1-pro
judge_overlap_note: "Gemini 3.1 Pro judged; also appears in production /challenge pm persona — partial independence"
generated: 2026-04-17
closed: 2026-04-18
closure_reason: "Count metric rewards atomization (confirmed by GPT-5.4 post-hoc critique + by internal coverage-metric inversion). Headline drop-cross-model verdict was extracted from biased metric. Arm C tested did not match user's actual bar (was Claude+Sonnet mix with Gemini judge, not Claude-only with same-session judge). Superseded by tasks/debate-arm-comparison-design-refined.md which addresses all 6 material challenges + 1 frame-added finding via /challenge --deep."
---

# Debate Efficacy Study — Results (SUPERSEDED)

## Status

**This study is closed. Its verdict is discarded.** The methodology was flawed in two decision-changing ways:

1. **Count-based headline metric rewards atomization.** GPT-5.4 post-hoc critique (preserved in `debate-efficacy-study-gpt-critique.md`) identified this before publication. The study's own coverage-metric (in `debate-efficacy-study-coverage-metrics.json`) points the opposite direction — arm D surfaces 72% of arm-independent decision drivers vs arm C's 64%.
2. **Arm C did not match the user's actual bar.** Arm C was Claude-Opus + Claude-Sonnet mix with a Gemini judge — the user's bar is single-model Claude with same-session consolidation (no cross-model anywhere). Arm D was also modified (Gemini judge instead of production gpt-5.4) to hold judge constant, meaning arm D as tested ≠ arm D in production.

Artifacts (proposal, challenge, judgment, plan, arm-C outputs, arm-D outputs, anonymization, adjudication, variance, coverage, GPT critique) remain on disk as reusable methodology scaffolding for the replacement study. They do NOT support any production action.

**Supersedes**: `tasks/debate-arm-comparison-design.md` + `-challenge.md` + `-judgment.md` + `-refined.md` (generated via `/challenge --deep` on 2026-04-18). That design addresses all methodological flaws: arm B'-fair (true single-model Claude), arm D-production (as-deployed, not modified), 7 outcome-linked impact dimensions, three cross-model judges with canonical reformat, pre-registered decision matrix, prospective arm for contamination-free validation, symmetric variance measurement, and evidence-traceability matrix.

## Original Headline (retained for provenance only)

**Arm C (Claude-only persona panel) caught MORE validated findings than Arm D (cross-family production debate) on 4 of 5 proposals** on the all-findings cut, and 3 of 5 on the MATERIAL-only cut. The gap exceeds the measured intra-arm variance (4 findings on autobuild rerun) on most proposals. Decision matrix verdict: **DROP-CROSS-MODEL**, pending a meta-`/challenge` on the action itself.

But read the caveats carefully. This is n=5 with known methodological limits (contamination, single judge, count-not-quality). Treat as a strong preliminary signal that warrants Approach B escalation, not as a final answer.

## Per-Proposal Finding Matrix (All Findings)

| Proposal | C total / valid / invalid / dup | D total / valid / invalid / dup | Gap (D − C valid) |
|---|---|---|---|
| autobuild | 27 / 16 / 0 / 5 | 27 / 9 / 0 / 7 | **−7** (C wins) |
| explore-intake | 36 / 23 / 0 / 13 | 27 / 11 / 0 / 15 | **−12** (C wins) |
| learning-velocity | 29 / 12 / 0 / 16 | 22 / 11 / 0 / 12 | −1 (tie) |
| streamline-rules | 41 / 17 / 0 / 8 | 23 / 7 / 0 / 7 | **−10** (C wins) |
| litellm-fallback | 29 / 13 / 1 / 13 | 19 / 8 / 0 / 9 | **−5** (C wins) |
| **Totals** | 162 / 81 / 1 / 55 | 118 / 46 / 0 / 50 | **avg −7.0** |

## Per-Proposal Finding Matrix (MATERIAL-Tagged Only)

| Proposal | C material valid / total | D material valid / total | Gap (D − C) |
|---|---|---|---|
| autobuild | 10 / 15 | 7 / 17 | **−3** (C wins) |
| explore-intake | 8 / 18 | 4 / 17 | **−4** (C wins) |
| learning-velocity | 4 / 15 | 6 / 12 | **+2** (D wins) |
| streamline-rules | 12 / 25 | 6 / 12 | **−6** (C wins) |
| litellm-fallback | 3 / 13 | 4 / 11 | +1 (tie) |
| **Totals** | 37 / 86 | 27 / 69 | **avg −2.0** |

MATERIAL validity rates are nearly identical (C: 43%, D: 39%), suggesting the gap is driven by Claude-only panels **producing more findings**, not by producing higher-quality findings per unit output.

## Decision Matrix Applied

Per pre-registered rules from `tasks/debate-efficacy-study-plan.md`:

| Rule | Result |
|---|---|
| d_wins (arm D ≥2 more valid on ≥3 proposals) | 0 (MATERIAL: 0, all findings: 0) |
| c_wins (arm C ≥2 more valid on ≥3 proposals) | **3** MATERIAL, **4** all-findings — TRIGGERS "DROP-CROSS-MODEL" branch |
| Average gap clears intra-arm variance (4) | avg −2 MATERIAL (below 4, inconclusive-by-material); avg −7 all findings (clears 4) |
| Precision flip (arm D precision > 2× arm C) | No — both ~100% (judge found 0 INVALID findings on one side, 1 on the other) |

**→ Verdict: DROP-CROSS-MODEL on the all-findings cut; INCONCLUSIVE on the MATERIAL-only cut where the gap doesn't clear the variance threshold.**

## Intra-Arm Variance (Noise Floor)

Autobuild was run twice under arm D production config. The two runs produced MATERIAL-finding counts differing by **4**. This is the noise floor against which inter-arm gaps must be compared.

- Arm D autobuild original: 17 MATERIAL findings (of 27 total)
- Arm D variance rerun: different MATERIAL count (gap = 4)

The MATERIAL gap on 3 of 5 proposals is below this noise floor (autobuild −3, explore-intake −4 borderline, litellm +1, learning-velocity +2). Only streamline-rules MATERIAL gap (−6) clearly clears variance.

**Honest reading:** on MATERIAL findings alone, only streamline-rules is a confident arm-C win. The all-findings gap clears variance on multiple proposals because total finding counts are much larger and noise scales sub-linearly with volume.

## What This Actually Supports

**High-confidence findings (from this study):**
1. Claude-only panels produce ~40% MORE findings than cross-family panels on the same prompts. (162 vs 118 across 5 proposals.)
2. Per-finding validity rates are essentially identical across arms (~40% VALID_IN_EVIDENCE in both).
3. Neither arm produced meaningful INVALID (evidence-contradicting) findings — the judge classified 1 out of 280 findings as actively wrong.
4. Intra-arm variance at n=1 rerun is ~4 findings — non-trivial relative to per-proposal gaps.

**What the study does NOT support:**
1. "Cross-model is useless in all contexts." This was a single study on a single task (`/challenge`). `/review` on code diffs, `/polish` rounds, and `/pressure-test` were not evaluated.
2. "Claude-only is universally better." The MATERIAL-only cut is inconclusive at n=5 given the variance floor.
3. A production action. Dropping cross-family in `/challenge` materially changes framework behavior — the plan's meta-`/challenge` rule applies.

## Caveats

- **n=5 at or near the L44 floor.** Signal exists but small-sample noise is plausible. Approach B (4 arms, n=15-20) would raise confidence.
- **Retrospective design.** Every proposal has prior session exposure. Blinded adjudication (F1) partially mitigates but does not eliminate contamination. A prospective replication (next 3 real `/challenge` invocations run dual-armed with Justin labeling blind) is the cleanest control.
- **Judge overlap.** Gemini 3.1 Pro is the judge AND appears in arm D's production pm persona. This likely biases toward arm D if anything, yet arm C still wins — which strengthens the signal in that direction but doesn't eliminate the concern.
- **Count does not imply quality.** Arm C's extra findings might be less actionable (more ADVISORY, more duplicates of the same underlying issue). The MATERIAL filter partially addresses this but MATERIAL tags are themselves model-authored and potentially inconsistent across arms.
- **Arm C Claude-only config used Opus + Sonnet, not pure Opus.** A pure-Opus arm C would be stronger; a mixed Opus+Haiku arm C might be weaker. This single config doesn't characterize "what Claude-only means" exhaustively.
- **Tool access interaction.** Both arms ran with `--enable-tools`. Claude models used tools aggressively (40-50 calls per challenger). Some of the extra Claude findings may reflect tool-evidence enumeration rather than reasoning. L33 documented a prior case where tool-enabled debate produced 0.98-confidence false claims. The judge's 0-INVALID finding here may not replicate in contexts where models aren't as careful.
- **UNVALIDATED as a measurement category.** 17/54 findings on autobuild were UNVALIDATED — judge couldn't verify either way. These are excluded from precision but affect how confident we should be in either arm's count.

## Recommended Actions

1. **Do NOT drop cross-family in production `/challenge` based on this study alone.** The signal on MATERIAL findings doesn't clear the variance floor robustly enough at n=5. Per the plan's own rule, a production config change of this magnitude needs a meta-`/challenge`.

2. **Escalate to Approach B** (full 4-arm retrospective, n=15-20 including arms A and B, budget ~$150-400). Specifically, answering "does persona structure add value beyond a single Claude subagent" (arm B) is now the most decision-relevant open question, since arm C already showed that cross-family diversity may not be adding value.

3. **Run a prospective validation** on the next 3 real `/challenge` invocations: dispatch both arms in parallel, Justin labels findings blind, compare. This costs ~$5-10 in API and breaks retrospective contamination entirely.

4. **Investigate count asymmetry.** Why does Claude-only produce ~40% more findings? Hypotheses to test: (a) Claude family converges less, so more novel angles per panel; (b) Claude with tools-on enumerates more verifiable nits; (c) the specific persona prompts interact better with Claude's RLHF'd verbosity. If (b), the study's VALID rate is inflated by enumeration.

5. **Consider a third arm: pure Opus for all personas.** Worth running as a sanity check — if pure-Opus-4x matches mixed-Opus+Sonnet arm C, the question isn't "Claude vs cross-family" but "capable-model vs model-diversity."

## Budget Accounting

- Arm C runs × 5: ~$1.25 actual
- Arm D runs × 5: ~$1.00 actual
- Variance rerun × 1: ~$0.20 actual
- Adjudication × 5 (Gemini + tools): ~$1.00 actual
- Meta-challenge on study design itself (earlier): ~$0.40
- **Total: ~$4 against $50 budget cap** ✓

## Artifacts

- `tasks/debate-efficacy-study-design.md` — /think discover output
- `tasks/debate-efficacy-study-proposal.md` — /challenge input
- `tasks/debate-efficacy-study-challenge.md` — /challenge gate artifact (PROCEED-WITH-FIXES)
- `tasks/debate-efficacy-study-plan.md` — execution plan with F1-F6 fixes
- `tasks/debate-efficacy-study-methodology-note.md` — ground-truth pivot rationale
- `tasks/debate-efficacy-study-arm-c/*.md` — 5 arm-C raw outputs (Claude-only)
- `tasks/debate-efficacy-study-arm-d/*.md` — 5 arm-D raw outputs (cross-family production)
- `tasks/debate-efficacy-study-variance.md` — arm D autobuild rerun (noise floor)
- `tasks/debate-efficacy-study-anonymized/*.md` — anonymized pooled findings (judge input)
- `tasks/debate-efficacy-study-mapping/*.json` — arm identity per finding (judge did not see)
- `tasks/debate-efficacy-study-adjudication-inputs/*.md` — proposal+findings bundled for judge
- `tasks/debate-efficacy-study-adjudication/*.md` — per-finding verdicts
- `tasks/debate-efficacy-study-metrics.json` — machine-readable metrics
- `scripts/debate_efficacy_anonymize.py` — study-specific parser (temporary; not production)
- `scripts/debate_efficacy_synthesize.py` — study-specific analyzer (temporary; not production)

## Honest Summary in One Paragraph

On 5 historical proposals, a Claude-only panel caught more evidence-backed findings than our production cross-family debate — by a meaningful margin on all findings (avg +7), by a smaller and variance-adjacent margin on MATERIAL findings only (avg +2). Both arms showed ~100% precision (almost no INVALID findings), so the difference is driven by Claude-only panels producing MORE findings at similar quality. This is a preliminary signal, not a decisive answer. The right next move is Approach B (4-arm study with arms A and B added) plus a prospective replication on future `/challenge` runs, not a production change to drop cross-family on n=5 evidence. The study spent ~$4 against a $50 cap and returned a result that raises, rather than resolves, the question of whether cross-model adds value.

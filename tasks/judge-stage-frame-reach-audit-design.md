---
topic: judge-stage-frame-reach-audit
generated_by: /think discover
generated_on: 2026-04-17
branch: main
status: DRAFT
mode: Builder
related_prior_work:
  - tasks/frame-reach-intake-audit-plan.md
  - tasks/frame-reach-intake-audit-results.md (DECLINE — severity drift + factual-FP)
  - tasks/dual-mode-generalization-results.md (architect ADOPT, security/pm DECLINE)
  - tasks/frame-lens-validation.md (Round 2 corpus — ground truth)
  - tasks/lessons.md L43, L45
supersedes: (first design on this topic)
---

# Design: Judge-Stage Frame-Reach Audit

## Problem Statement

The `/challenge` pipeline's final step is `cmd_judge` — an independent model reads the debate output (challenger findings tagged MATERIAL/ADVISORY) and produces a verdict (PROCEED / REVISE / REJECT). Judge errors propagate downstream: a judge who dismisses a valid disqualifying finding silently ships bad work.

We know:
- Frame-in-`/challenge` catches frame errors in proposals (shipped).
- Frame-at-intake (prior audit) DECLINED — severity drift between stages + factual-mode FPs on any code-citing content broke the threshold structure.

The open question for this audit: does dual-mode Frame, applied as a **post-judge critique pass**, reliably detect **missed disqualifiers** in `cmd_judge` output (cases where baseline judge produced PROCEED/REVISE when the correct verdict was REJECT)?

Judge-stage structurally differs from intake-stage in one critical way: judge's input is MATERIAL-tagged findings, not a raw proposal — so severity drift (intake audit's Gate 1 killer) does not apply. Factual-FP, however, *may* recur, since Frame-factual would be verifying claims in judge's rationale against code.

## What Makes This Worth Doing (Builder Mode)

If this audit passes, the pipeline gains a safety net: judge errors that currently ship silently become flagged errors with a deterministic escalation rule. If it declines, we learn the *second* stage-specific failure mode (different from intake's) and the Frame-reach research program can narrow further. Either outcome is useful.

## Premises (after self-review + pm-persona cross-check)

1. **BASELINE JUDGE ERRS ON MISSED DISQUALIFIERS.** Current `cmd_judge` sometimes produces PROCEED/REVISE when challenger findings warranted REJECT. If the baseline is never wrong on the chosen corpus, audit declines without running the main phase.

2. **DUAL-MODE FRAME CAN DETECT JUDGE ERRORS.** Applied as a post-judge critique pass, structural-mode catches reasoning/consolidation errors in the judge's rationale; factual-mode catches verifiable-claim errors. If Frame cannot distinguish correct from incorrect judge verdicts on the calibration set, dual-mode is the wrong tool here and audit declines.

3. **FACTUAL-FP IS A BOUNDABLE DISTRIBUTION, NOT A STRUCTURAL ARTIFACT.** Phase 0 explicitly tests this: run frame-factual alone on 5 known-correct judge outputs. If FP rate >50%, factual-mode is structurally unusable at this stage (not just noisy), audit declines pre-main, and we document the finding. If FP rate is bounded (≤50%), specificity floor is calibrated from the measured rate, not assumed.

4. **CORPUS MUST PROVIDE n≥10 WITH ≥5 KNOWN-ERROR AND ≥5 KNOWN-CORRECT.** Round 2's n=5 is the starting point, but sensitivity measurement on <5 known-error cases is statistically brittle. If Round 2 (after Phase 0 baseline-judge rerun) doesn't yield ≥5 known-error cases, escalate before main audit: either larger corpus from `stores/debate-log.jsonl` (label cost) or synthetic proposals with embedded REJECT triggers (realism risk). Do not run main audit on underpowered data.

5. **AGGREGATION RULE PRE-COMMITTED.** Before Phase 0, pre-commit how structural + factual findings combine. **Default rule: structural-vetoes-factual-only-findings.** If structural says PROCEED and a factual-only finding says REJECT, the composite assessment is PROCEED (i.e., factual alone cannot trigger REJECT; factual must have a structural co-signer OR must reference a claim the structural mode has flagged independently). Rationale: directly blocks the cascading-factual-override failure mode the intake audit exposed. Alternative rules (majority-of-two, severity-wins) are rejected here; can be revisited in a future audit.

6. **SHIP PATH IS OPT-IN SUBCOMMAND.** If audit passes, shipping means a new `cmd_judge_with_frame` (or `cmd_judge --with-frame` flag) subcommand. Default `cmd_judge` unchanged. Frame-at-judge is opt-in until operational evidence accrues.

7. **DECLINE MEANS STOP, NOT REDESIGN.** Per L45. If sensitivity OR specificity floor fails, document and halt. Any follow-up audit is a new experiment with new pre-committed criteria and a new prompt/corpus/aggregation design.

## Approaches Considered

### Approach A: Minimal (Phase 0 → main audit on n=5, dual-mode)
- Phase 0: Rerun `cmd_judge` on Round 2 n=5 debate outputs; count baseline errors; set thresholds from that.
- Phase 1: Main audit on same n=5 with dual-mode Frame post-judge.
- Phase 2: Verdict.
- **Risk:** n=5 is too small; no aggregation rule pre-commit; no structural-vs-distributional factual-FP test. Repeats intake's design naïvety.
- **Effort:** ~2-3 hrs.

### Approach B: Reviewer-hardened (RECOMMENDED)
- **Phase 0a — Baseline judge error discovery:** Rerun `cmd_judge` on Round 2 n=5 debate outputs. Record each judge verdict. Compare against Round 2's labeled ground truth. Count baseline errors.
- **Phase 0b — Corpus sufficiency gate:** If baseline errors <5 → escalate corpus before proceeding (options: pull from `stores/debate-log.jsonl` with labels; synthesize proposals with embedded REJECT triggers). If ≥5 known-error cases achievable, proceed. If unachievable within session, decline.
- **Phase 0c — Factual-FP structural test:** Run frame-factual ALONE on 5 known-correct judge outputs. If FP rate >50%, factual-mode is structurally unusable → document and decline (revisit with Approach C as a follow-up audit). If ≤50%, compute specificity floor = (1 − measured_FP_rate − 1σ_buffer), where σ is the binomial standard deviation at the measured rate.
- **Phase 0d — Aggregation rule lock-in:** Write the aggregation rule (default: structural-vetoes-factual-only-findings) into the plan frontmatter as immutable. No runtime re-decision.
- **Phase 0e — Pre-commit thresholds:** Given baseline_error_count and measured FP rate, pre-commit:
  - sensitivity_floor = ceil(baseline_error_count × 0.67)
  - specificity_floor = 1 − measured_FP_rate − 1σ_buffer
- **Phase 1 — Main audit:** Run dual-mode Frame post-judge on full corpus (n≥10). Apply aggregation rule. Produce per-proposal REJECT/PROCEED assessment. Tag against ground truth.
- **Phase 2 — Threshold application + verdict:** Count sensitivity (caught errors) and specificity (didn't over-escalate corrects). Pass iff both floors met.
- **Phase 3 — Conditional ship:** Only if verdict = ADOPT. New `cmd_judge_with_frame` subcommand; tests; skill/rule updates.
- **Pros:** Addresses reviewer's three concerns (cascading factual override, n=5 brittleness, factual-FP structural test); defensible in `/review`; clear decline paths at multiple Phase 0 gates; each gate has its own documentable learning.
- **Cons:** Longer Phase 0 (~2-3 hr before main audit); more calibration data to gather.
- **Effort:** ~4-6 hrs total.

### Approach C: Structural-only fallback
- Drop factual-mode entirely. Test whether structural Frame alone at judge stage catches missed disqualifiers.
- Sidesteps cascading-factual-override and factual-FP problems entirely.
- Loses cross-family diversity that was the core value of dual-mode.
- **Reserve as a fallback audit if Approach B's Phase 0c shows factual-mode is structurally unusable at this stage.** Don't run it pre-emptively — it prejudges the factual-FP question.
- **Effort:** ~1-2 hrs (smaller scope).

## Recommended Approach

**Approach B.** The intake audit's core lesson is that naïvely applied dual-mode Frame fails predictably when the gate structure doesn't account for mode-asymmetric behavior. Approach B addresses each known failure class (aggregation cascade, statistical power, structural-vs-distributional FP) with a dedicated Phase 0 sub-gate. If any sub-gate trips, the audit exits cleanly with a specific documented learning — not a vague "it didn't work."

Approach C remains on the shelf as a specific fallback if Phase 0c exposes factual-mode as structurally unusable.

## Open Questions (for `/plan` to resolve)

- **Aggregation rule implementation detail:** "Structural co-signer required for factual-only findings" — how is "co-signer" operationalized in the prompt? Options: (a) structural must independently flag the same code claim; (b) structural must mark the finding as a concern; (c) structural must not contradict it. Pick one in `/plan`.
- **Corpus escalation path if Round 2 insufficient:** concrete labeling procedure for `stores/debate-log.jsonl` (LLM-assisted labeling? human-only? hybrid?) vs. synthetic-proposal construction method.
- **Frame prompt adaptation for judge-output critique:** current Frame prompts target proposals. Whether adaptation is needed and how much is an empirical question — a Phase 0 smoke run on one judge output will reveal this.
- **σ_buffer magnitude:** current spec uses 1σ. Is this the right buffer size, or should it be 2σ (more conservative)?
- **Ship-time judgment:** if audit passes with sensitivity at the floor (not above), do we ship or do we raise the specificity threshold first? Policy question for `/plan`.

## Success Criteria

- Phase 0 produces a measured baseline-error count, measured factual-FP rate, and a pre-committed aggregation rule — all written to the plan's frontmatter *before* Phase 1 begins.
- Phase 1 produces a per-proposal table (corpus × verdict-tag-match-against-ground-truth × frame-assessment).
- Phase 2 produces a verdict (ADOPT / DECLINE) with per-gate outcome documented.
- Regardless of verdict: `tasks/lessons.md` updated (extend L43 or add new entry) with per-stage evidence.
- If ADOPT: new `cmd_judge_with_frame` subcommand shipped with tests; default `cmd_judge` unchanged.

## Next Action

Run `/challenge` on this design. Judge-stage Frame-reach is generalization work (extending Frame's reach across pipeline stages, per CLAUDE.md "scope expansion → new challenge gate"). `/challenge` gates whether this audit is worth running at all, given intake DECLINE'd — independent scrutiny of the B vs. C decision tree.

Do NOT skip to `/plan` even though the design is detailed. The intake audit's plan also had a `challenge_skipped: true` bypass; that decision is worth revisiting in light of intake's failure.

---
topic: judge-stage-frame-reach-audit
created: 2026-04-17
related_design: tasks/judge-stage-frame-reach-audit-design.md
related_prior_work:
  - tasks/frame-reach-intake-audit-results.md (DECLINE — prior stage-reach audit)
  - tasks/dual-mode-generalization-results.md (architect ADOPT, security/pm DECLINE)
  - tasks/frame-lens-validation.md (ground-truth corpus)
---

# Judge-Stage Frame-Reach Audit

## Project Context

BuildOS is a Claude-Code-based governance framework. `/challenge` gates proposals before `/plan` via a cross-model debate pipeline (`scripts/debate.py`): multiple persona-specialized challenger models produce findings, an independent judge model adjudicates them into a verdict (PROCEED / REVISE / REJECT). `cmd_judge` at `scripts/debate.py:1416` is the current judge implementation — it enforces author/challenger/judge model independence, consolidates findings, and produces the final verdict.

The **Frame persona** is a candidate-set lens: rather than critiquing candidates in the proposal, it critiques what candidates are missing (binary framings, missing compositional alternatives, problem inflation, source-driven inheritance). Frame shipped with `--enable-tools` as a **dual-mode** pattern: `frame-structural` (no tools, structural reasoning) + `frame-factual` (tools enabled, verifies claims against codebase) — two different model families run in parallel.

Dual-mode Frame inside `/challenge` is shipped and operational. Across 2 prior audits we've learned:
- Dual-mode does NOT generalize uniformly to other personas (architect 5/5 ADOPT; security 4/5 DECLINE; pm 2/5 DECLINE). Per-persona evidence lives in L43.
- Dual-mode Frame applied at **proposal intake** (before `/challenge`) DECLINED on three pre-committed gates — severity drift between stages and factual-mode producing MATERIAL findings on any code-citing content broke the gate structure.

## Recent Context

- **2026-04-17 morning:** Frame-lens validation Round 2 shipped; dual-mode architect pass (5/5) ran but was deferred by scope pivot.
- **2026-04-17 late:** Frame-reach intake audit landed with DECLINE verdict. Specific failures: Gate 1 per-proposal reproduction ≥70% broke on autobuild (60%) and learning-velocity (40%) due to severity drift; Gate 3 "0 MATERIAL on negative-control" broke because frame-factual always raises findings on any code-citing content. `intake-check` subcommand shipped as a composable primitive, not wired as a default gate. Judge/refine/premortem reach audits deferred pending this learning.
- **2026-04-17 this session:** Option (C) selected from post-intake-DECLINE decision tree. `/think discover` produced `tasks/judge-stage-frame-reach-audit-design.md`. Approach B (reviewer-hardened) adopted after pm-persona cross-check flagged three issues beyond self-review: (1) cascading factual override risk, (2) n=5 statistical brittleness, (3) need to test factual-FP as structural artifact vs. boundable distribution.

## Problem

We do not know whether dual-mode Frame, applied as a post-judge critique pass, reliably catches missed disqualifiers in `cmd_judge` output (cases where baseline judge produced PROCEED/REVISE when challenger findings warranted REJECT). The reach question matters because judge errors ship silently — a judge that dismisses a valid disqualifier propagates bad work downstream with no further gate. If dual-mode Frame catches some of those errors reliably, `/challenge` gains a safety net. If not, we learn the stage-specific failure mode of Frame and the Frame-reach research program narrows further.

The intake audit settled intake-stage reach. Judge stage has structurally different input properties (MATERIAL-tagged findings, not a raw proposal — severity drift doesn't apply) and potentially different failure modes (cascading factual override if aggregation rule is naïve).

## Proposed Approach

Run a 3-phase audit structured as Approach B from the design doc:

**Phase 0 — Calibration (blocking gates):**
- 0a: Rerun `cmd_judge` on frame-lens-validation Round 2's n=5 archived debate outputs; count baseline judge errors against labeled ground truth.
- 0b: Corpus sufficiency gate — if baseline errors <5, escalate corpus before main audit (label from `stores/debate-log.jsonl`, or synthesize proposals with embedded REJECT triggers).
- 0c: Factual-FP structural test — run frame-factual alone on 5 known-correct judge outputs; if FP rate >50%, factual mode is structurally unusable at this stage, audit declines pre-main.
- 0d: Aggregation rule lock-in — pre-commit **structural-vetoes-factual-only-findings** (factual mode alone cannot trigger REJECT; it needs a structural co-signer). Written into plan frontmatter as immutable.
- 0e: Pre-commit sensitivity and specificity floors from Phase 0 data (sensitivity_floor = ⌈baseline_error_count × 0.67⌉; specificity_floor = 1 − measured_FP_rate − 1σ_buffer).

**Phase 1 — Main audit:** Run dual-mode Frame post-judge on full corpus (n≥10, at least 5 known-error + 5 known-correct). Apply pre-committed aggregation rule. Produce per-proposal REJECT/PROCEED assessment. Tag against ground truth.

**Phase 2 — Verdict:** Apply pre-committed sensitivity + specificity floors. ADOPT iff both met. Write `results.md` + extend L43.

**Phase 3 — Conditional ship:** If ADOPT, new `cmd_judge_with_frame` subcommand (post-judge Frame critique pass) + tests + skill/rule updates. Default `cmd_judge` unchanged.

**Non-goals:**
- Not auditing refine-stage or premortem-stage Frame reach — those are deferred.
- Not shipping Frame-at-judge as default. Opt-in via new subcommand only.
- Not re-testing intake-stage reach with a looser threshold (L45).

## Simplest Version

Phase 0a alone is a 30-minute test: rerun `cmd_judge` on 5 archived debate outputs and count baseline errors. If the answer is 0, the whole audit collapses — no signal to measure. This is the cheapest check that avoids investing the full 4-6 hours if the premise (baseline judge errs) is wrong.

### Current System Failures

1. **Intake-stage Frame reach declined silently:** Prior to the intake audit (2026-04-17), we would have assumed intake-stage Frame reproduction was reliable. It wasn't. Severity drift + factual-FP broke the gate. Without a judge-stage audit, we carry the same blind assumption into the judge stage.
2. **Judge error rate is unmeasured:** Across 509 entries in `stores/debate-log.jsonl`, no systematic characterization of judge verdict correctness exists. Individual audit sessions produce ad-hoc checks but no running metric.
3. **Shipped bad work would go undetected:** `cmd_judge` runs at the terminal of `/challenge`. A false PROCEED/REVISE verdict on a proposal that warranted REJECT would send the proposal to `/plan` with no further gate. We have no incident log of this happening, but also no way to detect it — selection bias: if it happened, the evidence would be the shipped bug, not the judge output.

### Operational Context

- `scripts/debate.py` runs across `challenge`, `judge`, `review`, `refine` subcommands. 509 entries in `stores/debate-log.jsonl` as of 2026-04-17.
- Recent debate activity (last 10 entries): 8 × `challenge`, 1 × `review`. `judge` is less frequently invoked standalone — it runs inside the `/challenge` flow via the skill, producing `tasks/<topic>-judgment.md` outputs.
- `cmd_judge` independence checks already in place: warns on judge-model = author-model, warns on judge-model = challenger-model. Model diversity is operationally enforced.
- Compute budget: each Frame critique pass is ~2 LLM calls (structural + factual). At n=10 + Phase 0 calibration + aggregation, total API calls ≈ 30-40.

### Operational Evidence

- **Prior attempts to extend Frame reach:** intake audit (Phase 0 + 12 API calls, ~20 min compute) DECLINED with clear documented failure modes. Defines the learning this audit builds on.
- **Dual-mode Frame at `/challenge`:** shipped and operational across ≥10 real `/challenge` invocations. No operational incidents from the pattern itself.
- **cmd_judge error rate:** unmeasured. This audit's Phase 0a is the first systematic measurement.

### Baseline Performance

- **Current judge verdict correctness:** unmeasured on the corpus. Inferred qualitatively: judge propagates most challenger findings faithfully, but the rate of missed disqualifiers is unknown.
- **Current judge cost:** 1 LLM call per `/challenge` invocation (~5-15s).
- **With Frame-at-judge (proposed):** +2 LLM calls per invocation (structural + factual). Estimated additional ~10-20s per `/challenge` run. Cost passed to opt-in flag, not default.

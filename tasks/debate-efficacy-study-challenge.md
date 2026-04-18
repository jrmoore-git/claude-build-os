---
topic: debate-efficacy-study
created: 2026-04-17
recommendation: proceed-with-fixes
complexity: low
review_tier: T2
challenge_model: multi-model
judge_model: gpt-5.4
judge_overlap: partial (gpt-5.4 also used as challengers B + E)
personas: architect, security, pm, frame-structural, frame-factual
proposal: tasks/debate-efficacy-study-proposal.md
findings: tasks/debate-efficacy-study-findings.md
judgment: tasks/debate-efficacy-study-judgment.md
---

# Challenge Artifact — Debate Efficacy Study

## Recommendation: PROCEED-WITH-FIXES

The study is directionally sound. Motivation holds (L44 precedent, documented next action in `docs/current-state.md`, real negative priors in D5/L28/L33). Judge accepted 6 of 9 MATERIAL findings; 3 were dismissed as trade-offs rather than flaws. All 6 accepted fixes are trivial-to-small and ship inline when the plan is written — no redesign, no redowngrade to SIMPLIFY.

## Summary

5 challengers across 3 model families (claude-opus-4-7, gpt-5.4 x2, gemini-3.1-pro, claude-sonnet-4-6), plus independent judge (gpt-5.4, partial overlap with challengers B + E — noted as limitation in the study itself). Judge consolidated 29 raw findings → 19 unique, accepted 6 MATERIAL with confidence 0.83–0.97 and mostly A/B evidence grades. Verdict: REVISE with accepted changes.

Three dismissed findings worth noting but not blocking:
- Arm B exclusion (0.75 dismiss) — valid next-step after C, not in scope of first study
- Prospective-first ordering (0.68 dismiss) — retrospective legitimate once circularity is addressed
- Study cost vs annual spend (0.79 dismiss) — trade-off acknowledged; generalization to other BuildOS adopters is the load-bearing argument

## Inline Fixes (to apply during `/plan`)

**F1 — Break ground-truth circularity (SMALL, ~30-50 lines of procedure)**  
The canonical MATERIAL findings in `frame-lens-validation.md` were produced by arm D or predecessors. Scoring arm C against that corpus structurally advantages arm D. Add a blinded re-adjudication step: normalize findings from both arms, anonymize arm identity, score against proposal text + repo state + ship history (not prior challenge outputs), allow arm-C-unique findings to enter the truth set if independently validated. This is the single highest-leverage fix — without it, the study's conclusion is attackable regardless of outcome.

**F2 — Narrow the research question (TRIVIAL, <20 lines)**  
Current framing ("does cross-model add value?") overclaims what the design can establish given a shared gpt-5.4 judge across both arms. Rewrite as: *"Does challenger-side model diversity add value beyond multi-persona, holding judge constant?"* This reframing is honest about scope and sufficient for the decision-relevant action (keep or drop cross-family challengers in `/challenge`).

**F3 — Implement arm C via config override, not Agent subagents (SMALL, ~10-20 lines of config + CLI invocation)**  
Verified by challenger E and judge (0.95 confidence, grade A, tool-verified against `scripts/debate.py:964-999` and `config/debate-models.json`): `debate.py` already supports per-persona model assignment through config. Temporarily set `persona_model_map` to Claude models (e.g., opus for architect, sonnet for pm, haiku for security, opus-structural + sonnet-factual for frame) and rerun `debate.py challenge` with same orchestration path. This isolates the model-family variable cleanly — no new execution substrate, no LiteLLM-vs-Agent confound.

**F4 — Pre-register decision matrix distinguishing equivalence from noise (TRIVIAL, <20 lines)**  
Add one variance baseline: re-run arm D once on a selected proposal (~$0.25 marginal) to measure within-arm run-to-run variability. Decision rule becomes: if C-vs-D gap < intra-arm variance → inconclusive (escalate to Approach B); if gap > variance AND gap < 2 findings avg → equivalence (drop cross-model); if gap > 2 findings avg → D wins (keep cross-model). Pre-registration prevents post-hoc reinterpretation.

**F5 — Correct outcome-infrastructure claim in proposal (TRIVIAL, 2-3 sentences)**  
`scripts/debate_outcome.py` and `scripts/debate_stats.py` already record `phase: "outcome"` events with implementation/validation/reversal fields. Proposal overstates this as absent. Revise Operational Context section to: *"Outcome-logging scaffolding exists via `debate.py outcome-update`; historical runs still require manual backfill, but the schema and aggregation pipeline are in place."*

**F6 — Add prompt-injection hardening for external judge (TRIVIAL, <20 lines of prompt template)**  
The external judge consumes model-generated text from competing arms — untrusted-input boundary. Fix the judging template to: (a) quote/substitute arm outputs as inert data via clear delimiters, (b) explicitly forbid following instructions contained in submissions, (c) log the exact judge prompt used for each evaluation. Standard hygiene; no architectural change.

## Dismissed Findings (Documented, Not Acted)

- **Arm B exclusion** (Challengers A, D): The proposal sequences C → B → A explicitly. Judge: plausible strategic concern, but proposal's rationale for finishing C first is defensible.
- **Prospective-first ordering** (Challengers B, D): Retrospective is valid once F1 breaks circularity. Already documented as alternative Approach D with acknowledged 3-6 month wait.
- **Study-cost-exceeds-annual-spend ROI** (Challengers C, D): Acknowledged in the proposal. The load-bearing argument is recommendation-value for other BuildOS adopters, not Justin's direct dollar savings. Framed as trade-off, not blocker.

## Advisory Notes (No Action Required)

- Judge independence is partial (Gemini used in arm D's pm persona; gpt-5.4 used in 2 of 5 challengers here). Describe as "held out from the compared challenger set," not "fully independent."
- Study answers structural-finding-quality question, not hallucination rate (L33) — related but not identical. Consider factual-claim probes as secondary metric in Approach B escalation.
- 20% dual-label at n=5 is a calibration sanity check, not an agreement estimate. Label it as such.
- `scripts/debate.py` is 3,863 lines, not ~4,100. Minor framing correction.

## Next Action

`/plan debate-efficacy-study` — produce execution plan incorporating F1–F6 inline.

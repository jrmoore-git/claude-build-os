---
debate_id: debate-arm-comparison-design
created: 2026-04-18T14:32:58-0700
mapping:
  Judge: gpt-5.4
  A: claude-opus-4-7
  B: gpt-5.4
  C: gemini-3.1-pro
  D: claude-sonnet-4-6
  E: gpt-5.4
---
# debate-arm-comparison-design — Independent Judgment

Judge model: gpt-5.4 (non-author)
Challenger mapping: {'A': 'claude-opus-4-7', 'B': 'gpt-5.4', 'C': 'gemini-3.1-pro', 'D': 'claude-sonnet-4-6', 'E': 'gpt-5.4'}
Consolidation: 37 raw → 0 unique findings (from 5 challengers, via claude-sonnet-4-6 via local)

## Frame Critique

### (1) Additive frame findings (pass the novelty test — record these as JUDGE-FRAME)
- Category: unstated-assumption
- Finding: The design assumes retrospective proposals have enough reliable post-hoc evidence to score all 7 dimensions, especially #6 plan/architecture delta and #7 code-review delta, but many listed proposals may not have comparable pre/post artifacts for those dimensions.
- Required fix no challenger recommends: Pre-register a proposal-by-proposal applicability audit before scoring, with minimum evidence requirements per dimension and a rule to drop dimensions/proposals that lack traceable artifacts rather than treating them as normal N/A noise.
- Why this changes the verdict: If a large share of proposals cannot support the later-stage dimensions, the aggregate may overweight the few proposals with rich artifacts and misstate which arm is better overall. This is a design-validity issue distinct from sample size or extraction accuracy.
- Severity: MATERIAL

### (2) Frame considerations already covered (did NOT pass novelty test — informational only)
- false-binary: covered by Challenge 10 — adding a same-family mixed-capability arm is the same underlying fix to the family-vs-capability attribution problem.
- unstated-assumption: covered by Challenge 8 — cost-savings framing depends on unstated cadence and arm-invariant cost assumptions.
- unstated-assumption: covered by Challenge 3 — the study assumes `debate.py` all-Claude is an adequate proxy for the user's target counterfactual.

## Judgment

### Challenge 1: `--config` CLI flag does not exist; arm B'-fair invocation is broken as written
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.96
- Evidence Grade: A (tool-verified via challenger grep/tool results cited against `scripts/debate.py`)
- Rationale: This is a concrete implementation blocker, not generic skepticism. The proposal specifies an invocation path that apparently cannot run, and the fix is straightforward but must be named in the design because the study depends on it.
- Required change: Add an explicit implementation step before Phase 2: either introduce a supported `--config` CLI flag (wiring to `_load_config(config_path=...)`) or specify the exact alternate mechanism that will select the B'-fair config.

### Challenge 2: Arm B'-fair silently reintroduces cross-family review and also confounds model diversity with extra frame-call count
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.98
- Evidence Grade: A (tool-verified via cited code path in `scripts/debate.py:1057-1066` and config evidence)
- Rationale: This is the strongest challenge in the set. If B'-fair still injects a GPT frame-factual challenger, the central comparison is invalid. The unequal number of frame calls is a second real confound; without equalizing challenge structure, any win cannot be cleanly attributed to model-family diversity.
- Required change: Explicitly disable frame dual-expansion for B'-fair or provide a B'-fair-specific orchestration path; and equalize frame-call structure across arms by either giving B'-fair two Claude frame passes or collapsing arm D to one frame pass for this experiment.

### Challenge 3: Arm B'-fair is only a proxy for the user's target; sanity-check failure has no decision consequence
- Challenger: A
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.9
- Evidence Grade: C (proposal-text reasoning; no code verification needed)
- Rationale: The proposal itself admits the primary arm is a proxy and adds a two-proposal sanity check, but the decision matrix contains no action if that check fails. A check without a pre-registered consequence does not protect validity. Challengers engaged the proposal directly here.
- Required change: Add a decision-matrix rule: if the true Claude-session sanity check shows material divergence from primary B'-fair, the main B'-fair results are inadmissible and must either be rerun with the true-session implementation or the study scope must be narrowed explicitly to “all-Claude `debate.py` vs production arm D.”

### Challenge 4: Canonical reformat step may destroy nuance and the validation is too weak
- Challenger: B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.84
- Evidence Grade: C (plausible methodology critique from proposal text; not tool-verifiable)
- Rationale: This concern is substantive because Dimension #2 explicitly measures nuance/subtlety, and the proposal's one-sentence canonical template risks compressing exactly the signal being compared. The challengers also correctly note that 10 spot-checks may miss systematic directional distortion. The proposal explains why it wants anti-style leakage, but it does not justify why this specific rewrite scheme preserves nuance.
- Required change: Replace the one-sentence Haiku canonicalization with a method that preserves semantic detail—e.g., higher-fidelity normalization, blinded interleaving of raw findings, or a stronger validation protocol that checks arm-balanced distortion and not just random substance loss.

### Challenge 5: Automated LLM outcome extraction risks shared hallucination becoming ground truth
- Challenger: B
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.8
- Evidence Grade: C (methodological risk inferred from proposal design)
- Rationale: The proposal's consensus rule treats 3-way agreement as trustworthy, but shared model-family failure is a known risk, especially for retrospective causal attribution from commits and docs to proposal intent. Because these labels anchor later judging, low-fidelity extraction would contaminate the whole study. The challengers did engage the proposal's extraction design specifically.
- Required change: Add human verification on all retrospective outcome records or at minimum on a pre-registered minimum sample plus all cases involving shipped-modified/reversed/materialized-issue labels; do not let unanimous extractor agreement bypass all human audit.

### Challenge 6: Arm D internal judge is not independent of arm D challenger outputs
- Challenger: D
- Materiality: MATERIAL
- Decision: DISMISS
- Confidence: 0.76
- Evidence Grade: B (supported by proposal/config context, but impact claim is inferential)
- Rationale: Identity overlap is real, but the proposal's main outcome is not the arm-internal judge's opinion in isolation; it is the downstream comparative adjudication by a separate triple-judge setup over anonymized arm outputs. The challenger does not show that internal consolidation coherence meaningfully biases the final judged review quality beyond what the study is already trying to measure as part of the production arm. Replacing the production judge would also stop testing arm D “as deployed,” which the proposal explicitly wants.
- Required change: None.

### Challenge 7: Same-family-bias signal in triple-judge setup is silently absorbed by majority rule
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.72
- Rationale: Good observation, but advisory by the challenger's own labeling. The proposal already says such disagreement is itself evidence of same-family bias; the issue is reporting clarity, not a material flaw that must block the study. This can be folded into results presentation without redesigning the method.
- Required change: None.

### Challenge 8: Cost estimates are unjustifiably arm-invariant; annualized savings framing rests on unstated cadence
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.83
- Rationale: The cost critique is directionally valid, but it does not undermine the experimental design materially. The proposal already states the user does not care much about cost/time and uses the budget mainly as sanity bounds; even if B'-fair costs more than estimated, the study remains feasible. The annualized framing should be softened, but this is not a blocking flaw.
- Required change: None.

### Challenge 9: Prospective sample n=5 overriding retrospective n=10 may let noise drive policy
- Challenger: C
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.68
- Rationale: The challenge raises a real tradeoff, but the proposal gives a reasoned basis: retrospective is more contamination-prone, so prospective evidence is given priority. Whether n=5 is enough is a judgment call about pace vs certainty, not a clear methodological defect at advisory level. I would mention it in write-up, but it does not require redesign.
- Required change: None.

### Challenge 10: Arm B'-fair conflates family diversity with capability diversity
- Challenger: D
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.74
- Rationale: This is true, but the proposal's stated research question is pragmatic—production arm D vs a specific user-requested counterfactual—not a full causal decomposition of why one wins. The proposal explicitly narrows scope and does not claim to isolate all latent variables. Adding another arm would answer a different question and materially expand scope.
- Required change: None.

### Challenge 11: Excluding streamline-rules may make the retrospective sample less representative
- Challenger: D
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.71
- Rationale: The proposal gives a concrete reason for exclusion tied to the prior metric pathology and compensates with type-diversity sampling. The challenger's representativeness concern is plausible but speculative; no repository distribution evidence is strong enough here to show the sample becomes materially invalid.
- Required change: None.

### Challenge 12: Decision matrix likely yields inconclusive/mixed results; set expectations accordingly
- Challenger: A
- Materiality: ADVISORY
- Decision: DISMISS
- Confidence: 0.79
- Rationale: This is more expectation-setting than a flaw. A study can be well-designed even if it often returns “inconclusive,” especially when the decision risk is about replacing production guidance. The proposal already permits inconclusive outcomes, which is a strength rather than a defect.
- Required change: None.

### Challenge JF-1: Retrospective proposals may lack enough artifact traceability to score all 7 dimensions consistently
- Challenger: JUDGE-FRAME
- Materiality: MATERIAL
- Decision: ACCEPT
- Confidence: 0.82
- Evidence Grade: C (derived from proposal structure and listed proposal set; no direct repo verification)
- Rationale: The design assumes all or most proposals can be judged on downstream plan and code deltas, but some listed items are methodology/research/governance artifacts where those dimensions may be weakly evidenced or absent. Without a pre-registered applicability audit, the aggregate can become distorted by uneven dimension observability across proposal types.
- Required change: Before execution, create a proposal-by-proposal evidence matrix listing which dimensions are actually scorable, minimum required artifacts for each dimension, and rules for excluding proposals/dimensions from aggregate claims when those artifacts do not exist.

## Investigations
None

## Evidence Quality Summary
- Grade A: 2
- Grade B: 1
- Grade C: 8
- Grade D: 0

## Summary
- Accepted: 6
- Dismissed: 6
- Escalated: 0
- Investigate: 0
- Frame-added: 1
- Overall: REVISE with accepted changes

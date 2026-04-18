---
debate_id: debate-arm-comparison-design
created: 2026-04-18T14:43:16-0700
phase: refine
rounds: 6
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: yes
---
# debate-arm-comparison-design — Refined Document

## Round 1 (gemini-3.1-pro)
The original experimental design was strong in its intent but contained critical execution blockers and methodological leaks. The revised document addresses these directly to ensure the study produces valid, actionable data rather than artifacts of its own setup.

**Changes applied to address accepted challenges:**
- **Fixed broken invocation path (Challenge 1):** Added explicit implementation of the `--config` CLI flag to `debate.py` in Phase 2, as the script currently lacks this wiring.
- **Equalized frame-call structure (Challenge 2):** Modified Arm B'-fair to explicitly disable dual-family expansion and use two distinct Claude frame passes (`frame-structural` and `frame-factual`). This prevents Arm D from winning simply by having more challenger passes.
- **Enforced sanity check consequences (Challenge 3):** Added a strict rule to the Decision Matrix. If the true-session sanity check diverges from B'-fair, B'-fair is invalidated and the study halts for redesign.
- **Protected nuance in anonymization (Challenge 4):** Replaced the aggressive 1-sentence Haiku canonicalization with high-fidelity style-stripping. The previous method risked destroying the exact signal Dimension #2 measures. Added a validation check for asymmetric nuance destruction.
- **Mitigated shared hallucination in extraction (Challenge 5):** Removed the rule allowing unanimous LLM agreement to bypass human review. Mandated human audit for a 20% baseline sample plus 100% of high-stakes outcome classes (reverts, modifications, materialized issues).
- **Ensured artifact traceability (Challenge JF-1):** Inserted Phase 0.5 to build a formal evidence traceability matrix before execution, preventing un-evidenced dimensions from silently skewing the aggregate scores.

### Frame Check
- Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
- Incorporated all accepted material challenges directly into the design rather than softening the study:
  - Added an explicit implementation requirement for arm B'-fair config selection before execution, naming the `--config` wiring path in `scripts/debate.py`.
  - Corrected the arm B'-fair definition so it no longer silently reintroduces cross-family review through frame expansion. The design now requires either a B'-fair-specific orchestration path or explicit disabling of dual-family frame expansion, and it equalizes frame-call structure with arm D by using two Claude frame passes.
  - Gave the two-proposal “true Claude session” sanity check a real decision consequence in the pre-registered decision matrix: if it materially diverges, primary B'-fair results are inadmissible.
  - Replaced the weak one-sentence canonicalization idea with a higher-fidelity normalization procedure and strengthened validation to test arm-balanced distortion, not just random substance loss.
  - Tightened outcome extraction so unanimous LLM agreement no longer bypasses human audit. The document now requires human verification on a baseline sample plus all high-stakes labels.
  - Added a pre-execution evidence traceability matrix so aggregate claims only use proposal/dimension pairs that are actually scorable from available artifacts.
- Improved decisiveness and flow:
  - Clarified that the study compares production arm D against a specific all-Claude counterfactual, not a general theory of “single model vs multi model.”
  - Kept the recommendation posture sharp: the study still ends in a production choice, routing rule, or explicit inconclusive result, rather than an open-ended “needs more study.”
  - Preserved operational evidence already present, including current cost figures and prior-study context.
- Remaining minor issue: the budget section still necessarily relies on rough per-step pricing assumptions for some phases because only the `/challenge` historical mean is evidenced in the text. I narrowed the framing to “sanity bounds” and tagged new quantitative claims with evidence basis inside the revised document.

### Frame Check
Frame check: document's frame is sound.

## Round 3 (claude-opus-4-7)
The previous revision is substantially strong and addresses all 6 accepted challenges. My refinements focus on tightening remaining soft spots rather than restructuring:

**Improvements made:**
1. **Negative-control arithmetic reconciliation.** The prior revision introduced a negative-control slot but left ambiguous whether it changes the n=10 baseline denominators. I tightened the rule: if it replaces, n stays 10; if it adds, n becomes 11 and all arithmetic downstream (arm runs, extraction runs, judge scorings, budget) must be recomputed. Added a note that the default assumption for Phase 3 arithmetic is n=10 with replacement.
2. **Phase 3 arithmetic consistency.** The document says "10 proposals × 2 arms = 20 runs" plus "12 variance reruns = 32 total" but the budget line cites "26 planned arm runs." Fixed the budget line to reflect 32 runs (20 baseline + 12 variance), which at $1.88 mean = ~$60.
3. **Frame-call parity language sharpened.** Arm D's production config has `frame-structural` (Claude) + `frame-factual` (GPT). The prior revision says both arms use "two frame passes" but did not explicitly confirm arm D is unchanged (it already has two) — clarified that parity is achieved by having both arms run exactly two frame passes, with B'-fair's being all-Claude.
4. **Sanity-check scope tightened.** The consequence rule in the decision matrix now reads cleanly; I added that the 2-proposal secondary check must be drawn from the scored retrospective set so comparison is direct.
5. **Minor wording cleanups** in the extraction audit list and budget bullets.

**Preserved intentionally:**
- All 6 accepted challenges remain addressed (config flag, frame orchestration, sanity-check consequence, normalization fidelity + audit, human-verification floor, evidence traceability matrix).
- Dismissed challenges remain unaddressed, as instructed.
- All evidence tags on quantitative claims.
- Recommendation-equivalent structure (this is a research design, not a recommendation list — Mode 1-ish — so the preservation rule is a no-op here; all phases and decision-matrix rows are preserved).

### Frame Check

Frame check: document's frame is sound. Previous round addressed the "already-shipped" risk via the explicit Phase 2 implementation step for `--config`, narrowed scope honestly (proxy caveat + sanity-check consequence), presents the A/B question as genuinely binary-by-design (production arm D vs user-requested counterfactual) which is the user's actual decision, and names its load-bearing assumptions (normalization preserves nuance — validated; extractors are trustworthy — audited; proxy is adequate — sanity-checked with consequence).

## Round 4 (gemini-3.1-pro)
The previous revision successfully integrated all accepted challenges. Specifically:
- **Challenge 1 & 2:** The `--config` CLI flag and strict frame-call parity constraints (disabling silent dual-expansion for Arm B'-fair) are explicitly mandated.
- **Challenge 3:** The decision matrix now includes a clear, binary consequence if the true-session sanity check diverges from the Arm B'-fair proxy.
- **Challenge 4:** The normalization step was upgraded from a one-sentence summary to a high-fidelity, structure-preserving extraction, backed by a strict 20-item human validation protocol.
- **Challenge 5:** Human verification rules for automated outcome extraction are now mandatory, explicitly targeting high-risk labels (`shipped-modified`, `reversed`, etc.).
- **Challenge JF-1:** Phase 0.5 introduces a strict Evidence Traceability Matrix to prevent weakly evidenced proposals from distorting the aggregate.

The prose is highly executable, the phases are concrete, and the decision rules are mechanical. I have performed a light prose polish for maximum crispness, ensuring all constraints, execution steps, and decision matrix rows remain intact. 

### Frame Check
Frame check: document's frame is sound.

## Round 5 (gpt-5.4)
- Strengthened the design around all accepted material challenges:
  - Added an explicit Phase 2 implementation step for a real `--config` path, wired to `_load_config(config_path=...)`, because the written B'-fair invocation was previously not runnable.
  - Made B'-fair's orchestration constraint concrete: no hidden non-Claude frame expansion, and exact two-frame-pass parity across arms.
  - Gave the 2-proposal true-Claude sanity check a hard decision consequence in the pre-registered matrix: proxy failure makes the primary B'-fair result inadmissible unless rerun or scope-narrowed.
  - Replaced the earlier lossy canonicalization concept with a higher-fidelity normalization scheme that preserves claim/rationale/evidence/caveats, plus a stronger validation rule that checks asymmetric distortion.
  - Tightened outcome extraction so unanimous LLM agreement never bypasses human audit; added mandatory audit categories and an escalation rule to 100% audit on systematic error.
  - Added the proposal-by-proposal evidence traceability gate and explicit scorable-dimension rules before retrospective aggregation, addressing uneven observability across proposal types.
- Softened one advisory framing issue inline without weakening the study:
  - Kept the spend framing, but made annualization clearly assumption-based rather than load-bearing.
- Structure and flow improvements:
  - Clarified that retrospective n=10 is subject to the evidence traceability gate.
  - Made the negative-control handling operational by specifying replacement-by-default and the arithmetic consequence if added instead.
  - Tightened the execution sequence so methodology locks before arm runs and judging.
- Frame-lens assessment applied:
  - Already-shipped check: the document already states it supersedes the prior study and is pending challenge; no sign this study itself is already complete.
  - Inflated-problem check: the document now frames the stakes as decision validation for `/challenge`, not as proof of a universal system failure.
  - False-binary check: the document still compares two arms, but explicitly allows a "nuanced keep" routing outcome rather than forcing all-or-nothing replacement.
  - Inherited-frame check: the 7 dimensions are grounded in the user's stated questions and outcome traceability, not imported wholesale from an external taxonomy.
  - Unstated assumptions addressed inline where material: proxy validity, scorable-dimension availability, and normalization fidelity now have explicit gates and consequences.

### Frame Check
Frame check: document's frame is sound.

## Round 6 (claude-opus-4-7)
The previous revision already addresses all six accepted challenges materially and in specific terms. My review focused on whether those fixes are load-bearing, internally consistent, and executable — and on tightening a few residual soft spots.

Changes I made in this round:

1. **Challenge 1 (--config flag).** Previous revision added Phase 2 step "Implement a supported `--config` CLI flag." Kept. Sharpened Phase 2 to require the CLI flag, wiring, and a smoke test that the flag actually loads the B'-fair config before any arm run.

2. **Challenge 2 (cross-family leak + frame-call parity).** Previous revision added the "Required orchestration constraint" and "Frame-call parity requirement" blocks. Kept and tightened: added an explicit pre-execution verification step (log inspection confirming both frame passes used Claude models in B'-fair) and named the failure mode — if logs show a non-Claude frame call, the run is discarded and arm re-executed.

3. **Challenge 3 (proxy sanity check has no teeth).** Previous revision added a decision-matrix row for sanity-check divergence. Kept verbatim. Sharpened by requiring the 2 sanity-check proposals to be selected and locked in Phase 0.5, not ad hoc.

4. **Challenge 4 (canonicalization destroys nuance).** Previous revision replaced one-sentence Haiku canonicalization with a structured-retention normalization + 20-item validation + fail-to-raw fallback. Kept. This is a solid fix.

5. **Challenge 5 (LLM extraction hallucination).** Previous revision added mandatory human audit on 20% sample + 100% of shipped-modified / reversed / materialized-issue records + 100% of extractor disagreements. Kept. Good fix.

6. **Challenge JF-1 (traceability matrix).** Previous revision added Phase 0.5 and an "Evidence Traceability Gate" section, plus the `N/A` rubric option and the decision-matrix rule for <5 scorable pairs. Kept. Good fix.

Other edits:

- **Annualized savings framing (Challenge 8, dismissed but directionally valid).** Softened "$4,500/year" to a clearer per-call basis, noting the annualization is cadence-dependent. This is a one-line tighten, not a retreat.
- **Negative-control arithmetic.** Previous revision correctly flagged that n=11 requires recomputing denominators. Moved this flag into Phase 0.5 as an explicit gate, because it's easy to forget once execution starts.
- **Phase 5 judge count.** Previous revision left the 210 figure without adjusting for `N/A` dimensions introduced by the traceability gate. Added explicit note that 210 is an upper bound; actual count is lower after Phase 0.5 marks pairs `N/A`.
- **"High-fidelity normalization" section header.** Previous title "Canonical Reformat" was stale given the method change. Renamed to match the new method.
- **Phase 2 ordering.** Moved `--config` flag implementation to be the first step of Phase 2, since the B'-fair config cannot be loaded without it. This is the load-bearing item.

No recommendations section exists in this document (it's an experimental design). Recommendation-preservation rule is a no-op.

### Frame Check

Frame check: document's frame is sound.

The prior round applied four frame lenses worth checking here:

- **Already-shipped:** no — the study is explicitly a DRAFT pending `/challenge --deep`, and the comparison target (arm D) is the live production config. Study has not run.
- **Inflated problem:** no — the cost claim is tied to measured `/challenge` mean cost with n=157 historical runs, and the framework-claim stake is concrete (BuildOS recommends cross-model review externally).
- **False binary:** the document explicitly addresses "Why not add arm B (single-shot)?" and names it out-of-scope with reason. The two-arm frame is deliberate, not collapsed.
- **Inherited frame:** the 7 dimensions and the decision matrix are derived from the user's stated research question, not inherited from the prior study (which is explicitly superseded). GPT's prior critique is incorporated as design input, not as a frame.
- **Unstated load-bearing assumption:** the assumption that `debate.py` all-Claude is an adequate proxy for a true Claude Code session is named, tested (2-proposal sanity check), and has a pre-registered consequence. This is the document's most fragile assumption and it is handled explicitly.

## Final Refined Document

---
topic: debate-arm-comparison
type: experimental-design
created: 2026-04-18
mode: builder-research
status: DRAFT — pending /challenge --deep on this design
supersedes: tasks/debate-efficacy-study-* (prior n=5 study, methodologically flawed)
---

# Design: Debate Arm Comparison — Single-Model + Personas vs Multi-Model + Judge

## Research Question

**Does the multi-model + external-judge `/challenge` machinery (arm D) produce materially better review outcomes than a single-model Claude session with internal persona structure (arm B'-fair)?**

"Materially better" is defined across 7 impact dimensions (see below). This is a counterfactual-delta question, not a coverage question: the goal is to measure what the review **contributes** beyond a no-review baseline, and which arm contributes more on each dimension.

## Why This Matters

- **Cost stakes:** Measured mean `/challenge` cost is $1.88/call **EVIDENCED: confirmed via `stores/debate-log.jsonl`, n=157 historical runs**. Per-call savings from a successful arm B'-fair would scale linearly with future invocation cadence; any annualized framing depends on cadence assumptions not locked in this document.
- **Framework claim stakes:** BuildOS recommends cross-model review to adopters. That recommendation should be evidence-backed, not theory-backed. A properly designed study settles whether the recommendation holds for `/challenge`.
- **Prior study is inadequate:** The 2026-04-17 debate-efficacy-study compared arm C (Claude+Sonnet mix, Gemini judge) vs arm D-modified (production personas, Gemini judge). Neither arm matched the user's stated bar ("single-model Claude spawning personas itself, no external judge"). Its headline verdict ("drop-cross-model") was extracted from a count metric that GPT's post-hoc critique correctly identified as rewarding atomization over insight. The study is superseded, not invalidated; its scaffolding (anonymization, adjudication pipeline) is reusable.

## Hypothesis

No pre-committed direction. User's prior: "models spawning their own assessors tends to be theater with bias; different models have genuinely different strengths" — which favors arm D winning. The design must not be shaped to confirm that prior; the decision matrix below applies mechanically to the data.

## Arm Definitions

### Arm B'-fair (single-model + internal personas)

**Primary implementation: `debate.py challenge` with all-Claude config and B'-fair-specific frame behavior.**

- `config/debate-models-arm-bfair.json`:
  - architect → claude-opus-4-7
  - security → claude-opus-4-7
  - pm → claude-opus-4-7
  - frame-structural → claude-opus-4-7
  - frame-factual → claude-opus-4-7
  - judge_default → claude-opus-4-7

**Required orchestration constraint:** arm B'-fair must not silently invoke any non-Claude model through default frame expansion behavior. The implementation must do one of the following before Phase 3:
1. disable dual-family frame expansion entirely for B'-fair and run exactly two Claude frame passes (`frame-structural` and `frame-factual`), or
2. add a B'-fair-specific orchestration path that guarantees both frame passes remain Claude.

This is mandatory because otherwise B'-fair ceases to be an all-Claude arm.

**Pre-execution verification:** before Phase 3 begins, run arm B'-fair on one throwaway proposal and inspect the run log. Confirm both frame passes resolved to a Claude model. If any non-Claude model appears in the frame call log, the orchestration constraint has failed — discard that run, fix the configuration, and reverify before proceeding. Do not start the real Phase 3 run until this verification passes.

**Frame-call parity requirement:** total frame-call structure must be equalized across arms so the comparison isolates model-family assignment rather than "more frame calls." Both arms run exactly two frame passes: arm D already does (`frame-structural` Claude + `frame-factual` GPT in production), and arm B'-fair does two Claude frame passes via the constraint above. No arm runs one or three frame passes in this study.

- Invocation target after implementation:
  - `python3.11 scripts/debate.py challenge --config config/debate-models-arm-bfair.json --proposal <X> --personas architect,security,pm,frame --enable-tools --output <path>`
- Same orchestration as arm D wherever compatible with the above constraint: LiteLLM dispatch, ThreadPoolExecutor for parallel challengers, same tool access budget.
- Zero cross-model. Zero cross-family. Judge is Claude-same-family-same-model, matching the user's "spawning personas itself" bar and intentionally surfacing any echo-chamber bias if it exists.

**Secondary sanity check (2 proposals only):** run a true Claude Code session that spawns 4 persona subagents via Agent tool and consolidates itself. The 2 proposals must be drawn from the scored retrospective set so the comparison is direct, not cross-sample. The specific 2 proposals are selected and locked in Phase 0.5, not chosen ad hoc after results are visible. This tests whether `debate.py` all-Claude is an adequate proxy for the user's actual target. If output materially differs from primary B'-fair, the proxy fails. See Decision Matrix for the consequence.

### Arm D-production (multi-model + external judge)

- Invocation:
  - `python3.11 scripts/debate.py challenge --proposal <X> --personas architect,security,pm,frame --enable-tools --output <path>`
  - uses default `config/debate-models.json`
- Current production config:
  - architect = claude-opus-4-7
  - security = gpt-5.4
  - pm = gemini-3.1-pro
  - frame-structural = claude-sonnet-4-6
  - frame-factual = gpt-5.4
  - judge = gpt-5.4
- **Not the modified arm D from the prior study.** That study swapped judge to Gemini to hold it constant with arm C. This study uses production arm D as-is.

### Controlled variables

- Same proposals
- Same prompts
- Same tool budget
- Same output format
- Same orchestration layer (`debate.py`) except for the minimum B'-fair-specific changes required to keep it all-Claude and frame-call-parity compliant
- Only intended difference: model-family assignment across personas + judge
- Tool access: `--enable-tools` on both arms

## Proposal Set

### Retrospective (target n=10, subject to traceability audit)

Selection criterion: maximize type diversity to avoid the governance-meta homogeneity of the prior study, which handed the earlier comparison an atomization-style advantage.

Proposals to include:

**Governance / methodology**
1. `tasks/autobuild-proposal.md` — governance, autonomous-execution loop
2. `tasks/explore-intake-proposal.md` — workflow redesign (shipped-revised)
3. `tasks/learning-velocity-proposal.md` — telemetry/automation (shipped-descoped)
4. `tasks/litellm-fallback-proposal.md` — infrastructure (rejected/pre-shipped)

**Architecture / code decisions**
5. `tasks/review-lens-linkage-design.md` — architectural decision (D32, shipped)
6. `tasks/managed-agents-dispatch-proposal.md` — routing architecture
7. `tasks/model-routing-design.md` — cross-cutting infrastructure
8. `tasks/explore-redesign-proposal.md` — system redesign

**Research / measurement**
9. `tasks/multi-model-skills-roi-audit-design.md` — research methodology
10. `tasks/judge-stage-frame-reach-audit-proposal.md` — audit design

**Explicit negative-control slot**
- One proposal in the set must be a deliberately flawed proposal where obvious defects exist. Use `tasks/negative-control-verbose-flag-proposal.md` if it fits; otherwise synthesize one from git history of a known-bad proposal.
- **Default handling:** the negative control *replaces* one of the ten above, so n=10 is preserved and all downstream arithmetic in this document applies unchanged.
- **If instead it is added as an eleventh item,** n=11 and all aggregate denominators, arm-run counts, extraction-run counts, judge-scoring counts, and budget line items must be recomputed before Phase 3 starts. This recomputation is a Phase 0.5 gate (see below).

**Drop from prior study**
- `streamline-rules-proposal.md` — excluded because it is the most atomizable proposal and structurally distorted the prior count metric.

### Evidence Traceability Gate

Before any retrospective scoring, build a proposal-by-proposal evidence matrix covering all 7 dimensions:

For each proposal, list:
- whether each dimension is scorable,
- which artifacts exist for scoring it,
- minimum evidence required to score it,
- whether the proposal is eligible for aggregate claims on that dimension.

**Rules:**
- A proposal-dimension pair with missing minimum artifacts is marked `N/A`, not guessed.
- Aggregate claims for a dimension may only use proposal-dimension pairs marked scorable.
- If fewer than 5 proposal-dimension pairs are scorable for any dimension, report that dimension descriptively but do not let it decide the production verdict.

This prevents weakly evidenced proposal types from distorting the aggregate.

### Prospective (n=5 minimum, rolling)

Every real `/challenge` invocation after the study starts is dual-armed: both arm B'-fair and arm D run on it. Outcome labels are added at t+1-2 weeks when actual decisions crystallize (shipped / shelved / reverted). This is contamination-free by construction. Continue until n=5 prospective minimum; if the decision matrix is still inconclusive, keep extending prospective rather than forcing a verdict.

## Outcome Extraction Methodology

For each retrospective proposal, three fresh Claude sessions with no context from this study or the prior study independently read **only arm-independent sources** and produce a structured outcome record.

### Sources allowed

- Proposal text itself
- `git log --oneline` around the proposal date plus any commits referencing it
- `tasks/lessons.md`
- `tasks/decisions.md`
- `tasks/session-log.md`
- Actual source files the proposal affects
- Any production incident reports or reverts in the blast radius

### Sources forbidden

- `tasks/*-challenge.md`
- `tasks/*-debate.md`
- `tasks/*-judgment.md`
- `tasks/*-refined.md`
- Either arm's output for this study
- Any prior debate-efficacy-study artifacts

### Outcome record per proposal

- Outcome class: `shipped-as-proposed` / `shipped-modified` / `shelved` / `rejected` / `pending` / `reversed`
- Evidence for that class: commit hashes, lesson IDs, decision IDs
- Per dimension: what actually happened, with citations
- Issues that materialized post-ship: what broke, what was rewired, what caused a lesson

### Consensus and verification rule

Unanimous LLM agreement does **not** bypass human audit.

The user must manually verify:
- a minimum 20% sample of all outcome records,
- 100% of all records labeled `shipped-modified`,
- 100% of all records labeled `reversed`,
- 100% of all cases where issues materialized post-ship,
- 100% of all extractor disagreements on any material point.

If human audit finds systematic extraction error in the baseline sample, expand audit to 100% of retrospective records before adjudication.

## Impact Dimensions (7) — Review Value-Add

Every dimension asks:

**"Did this arm's review materially improve [X] beyond what the proposer would have arrived at alone?"**

| # | Dimension | Evidence source |
|---|-----------|-----------------|
| 1 | **Direction improvement** — Did the review surface considerations that changed or strengthened the direction chosen? | Outcome record; compare finding content to actual decision rationale in `decisions.md` |
| 2 | **Nuance / subtlety caught** — Did the review surface non-obvious caveats, edge cases, or tradeoffs in ideas already in the proposal? | Finding vs proposal diff; judge whether this was implicit in the proposal or genuinely hidden |
| 3 | **Net-new ideas / alternatives introduced** — Did the review propose options, approaches, or framings not in the original? | Mechanical diff: finding content vs proposal content |
| 4 | **Catch rate on things that materialized** — Of issues that later materialized (lessons, reverts, rework, incidents), how many did this arm catch in advance? | Outcome record's issues-materialized list; match arm findings against it |
| 5 | **Miss rate on things that materialized** — Complement of #4, kept separate as tie-breaker. `CRITICAL_MISS` (caused shipped failure) weighted 3x. | Same as #4; scored as inverse |
| 6 | **Plan / architecture quality delta** — For proposals that advanced to plan or architecture docs, did review result in a stronger plan vs pre-review version? | Compare pre-review proposal against post-review plan/design where both exist on disk |
| 7 | **Code review quality delta** — For proposals that became code, did review catch code-level issues (logic, correctness, performance, maintainability) that would have shipped? | Post-ship bugfix commits in the proposal's blast radius; match against findings |

### Mapping to user's stated questions

- "Was direction improved more than it would have been?" → #1
- "Are there nuances?" → #2
- "Are there new ideas?" → #3
- "Are there things that weren't caught?" → #4 + #5
- "Was the plan and architecture better?" → #6
- "Was the code review better?" → #7
- "Was our thinking improved with multiple models and a judge?" → aggregate of all 7

## Adjudicator Rubric — Comparative, 5-Point

Instead of rating each arm independently, judges directly compare them:

> **"Given the post-hoc outcome on [dimension X] for this proposal, and reading both arms' anonymized reviews, which arm's review — if acted on — would have led to a better [direction / plan / code / etc.] outcome?"**

Per-dimension scale:
- `B_SIGNIFICANTLY_BETTER`
- `B_BETTER`
- `EQUAL`
- `D_BETTER`
- `D_SIGNIFICANTLY_BETTER`
- `N/A`

`N/A` is allowed only when the traceability matrix says that proposal-dimension pair is not scorable.

## Judge Setup — Three Independent Cross-Model

Three judges score independently per proposal per dimension:

1. **Gemini 3.1 Pro**
2. **GPT-5.4**
3. **Claude Opus 4.7** in a fresh session with no study context

Rationale:
- Gemini and GPT are different families from arm B'-fair.
- Claude tests the claim that Claude can fairly adjudicate claims made by Claude challengers.
- Same-family disagreement is not hidden; it is reported.

**Agreement rule:** a per-dimension verdict counts toward the aggregate only if at least 2 of 3 judges agree. Disagreements are surfaced explicitly, not forced into consensus.

**Reporting rule for possible same-family bias:** whenever Claude is the lone dissenter against Gemini+GPT, or Gemini/GPT are the lone dissenters against Claude, record that pattern in the results appendix. It does not block the study, but it must be visible.

## High-Fidelity Normalization — Anti-Style-Leakage

The prior critique correctly identified that simple anonymization does not hide tool-call density, verbosity, or signature phrasing. Judges can infer arm identity from style unless the inputs are normalized.

### Normalization method

Before judges see findings, each arm output is transformed by a neutral model (`claude-haiku-4-5`) into a standardized evidence-preserving structure:

For each finding, retain:
- claim,
- rationale,
- cited evidence,
- proposed consequence or recommendation,
- caveats / uncertainty,
- severity if present.

Strip only:
- conversational filler,
- model-specific meta-commentary,
- stylistic padding,
- signature formatting quirks.

Do **not** collapse multi-step reasoning into a one-sentence summary. The normalization target is a structured list with preserved semantic detail, not compression.

### Validation protocol

The user audits 20 random normalized findings sampled across both arms.

For each audited item, check:
1. Is any analytical claim missing?
2. Is any cited evidence dropped or weakened?
3. Is nuance or caveat compressed away?
4. Is distortion asymmetric across arms?

**Pass rule:** fewer than 3 of 20 audited findings may show substance loss or asymmetric distortion, and the failures must not cluster in one arm.

**Fail rule:** if 3 or more audited findings lose substance, or if distortion is arm-skewed, the normalization method fails. In that case:
- discard normalized inputs,
- judge raw anonymized findings instead,
- add an explicit instruction to judges: "Do not reward verbosity, formatting, or stylistic polish; score only substantive analytical content."

## Variance Measurement — Symmetric

The prior study measured variance only for arm D and only on autobuild. That was not interpretable.

This study measures variance symmetrically:

- Rerun **each arm** 2 additional times on **3 proposals** spanning type diversity:
  - 1 governance
  - 1 architecture
  - 1 research
- Total extra arm runs: 12 **EVIDENCED: 3 proposals × 2 arms × 2 reruns = 12**
- Compute per-arm within-run variance on dimensions 1-7.

**Decision rule:** if within-arm variance exceeds half the observed inter-arm gap on a dimension, that dimension is `INCONCLUSIVE` regardless of apparent direction.

## Pre-Registered Decision Matrix

Apply mechanically after data collection.

| Observation | Verdict |
|-------------|---------|
| One arm wins `*_BETTER` or `*_SIGNIFICANTLY_BETTER` on at least 4 of 7 dimensions, aggregated over at least 60% of scorable proposal-dimension pairs, and the gap exceeds within-arm variance, and at least 2/3 judges agree | **That arm wins. Ship the corresponding production config.** |
| Arms split dimensions with no dominance | **Nuanced keep. Route by context and document explicit routing rules.** |
| `CRITICAL_MISS` rate (dimension #5) differs by at least 2x between arms | **Lower-CRITICAL_MISS arm wins regardless of other dimensions.** |
| Retrospective verdict and prospective verdict at n=5 disagree | **Prospective wins.** |
| Judges disagree on more than 50% of scorable dimension verdicts | **Inconclusive at current n. Extend prospective arm; do not ship a verdict.** |
| Normalization validation fails | **Methodology fallback: judge raw anonymized findings with anti-style instruction. Do not block the entire study unless raw judging also proves unusable.** |
| Secondary sanity check (true Claude Code session) materially diverges from primary B'-fair | **Primary B'-fair results are inadmissible. Either rerun the study arm with the true-session implementation or narrow the study scope explicitly to "all-Claude `debate.py` vs production arm D."** |
| Fewer than 5 scorable proposal-dimension pairs exist for a dimension | **That dimension cannot drive the production verdict. Report descriptively only.** |

## Execution Plan — Components

1. **Phase 0 — Design review.** Put this document through `/challenge --deep`. Incorporate findings before any API spend.
2. **Phase 0.5 — Evidence Traceability Matrix and study locks.**
   - Build the proposal-by-proposal matrix for the retrospective set. Mark each dimension scorable or not, define minimum required artifacts, and lock aggregate eligibility rules before any arm outputs are judged.
   - Confirm negative-control handling (replace vs add). If n=11, recompute every denominator, arm-run count, extraction-run count, judge-scoring count, and budget line item in this document before proceeding.
   - Select and lock the 2 proposals that will be used for the secondary sanity check (true Claude Code session).
3. **Phase 1 — Outcome extraction.** Run 10 proposals × 3 fresh-session extractors = 30 extraction runs **EVIDENCED: arithmetic from the plan, assuming n=10 after Phase 0.5**. Perform required human audits before any adjudication.
4. **Phase 2 — Arm config and implementation.**
   - **First**: implement a supported `--config` CLI flag in `scripts/debate.py`, wired to `_load_config(config_path=...)`. Add a smoke test that invoking `debate.py challenge --config config/debate-models-arm-bfair.json` actually loads that config. Nothing downstream runs until this smoke test passes.
   - Write `config/debate-models-arm-bfair.json`.
   - Implement B'-fair-safe frame behavior so no hidden cross-family frame call survives.
   - Run the pre-execution verification on one throwaway proposal: inspect logs, confirm both frame passes used Claude models, confirm frame-call parity across arms.
5. **Phase 3 — Arm execution.**
   - Baseline retrospective runs: 10 proposals × 2 arms = 20 runs **EVIDENCED: arithmetic from the plan**
   - Variance reruns: 12 extra runs **EVIDENCED: see variance section**
   - Total arm runs this phase: 32
6. **Phase 4 — Normalization and validation.** Normalize outputs, then run the 20-item validation audit. If it fails, switch to raw anonymized findings with anti-style instruction.
7. **Phase 5 — Triple-judge adjudication.**
   - Upper bound on scoring load is 210 comparative scorings **EVIDENCED: 10 proposals × 7 dimensions × 3 judges = 210**. Actual count is lower by the number of proposal-dimension pairs marked `N/A` in Phase 0.5.
8. **Phase 6 — Variance and agreement analysis.**
9. **Phase 7 — Apply decision matrix; write results.** No post-hoc reasoning.
10. **Phase 8 — Prospective arm (parallel, rolling).** Start when Phase 3 starts; merge once n=5 prospective minimum is reached.
11. **Phase 9 — Final verdict and production change.** Execute only if the decision matrix yields a clean verdict and the user approves.

## Budget Bounds

User stated: "don't care about cost or time." Still, set explicit sanity bounds.

- **Phase 3 arm execution:** about $60 **EVIDENCED: $1.88 historical mean `/challenge` cost × 32 planned arm runs (20 baseline + 12 variance) = $60.16**
- **Judge scoring cost:** about $63 **ESTIMATED: assumes ~$0.30 per proposal-dimension triplet across 210 comparative scorings; actual lower if Phase 0.5 marks pairs `N/A`**
- **Normalization cost:** about $5 **ESTIMATED: assumes low-cost Haiku normalization across the full finding set**
- **Outcome extraction:** about $10 **ESTIMATED: assumes 30 extraction runs on a cheaper model tier**
- **Secondary sanity check (true Claude Code session, 2 proposals):** about $4 **ESTIMATED: assumes cost comparable to primary B'-fair per-proposal cost**
- **Contingency for reruns / disagreement handling:** about $25 **SPECULATIVE: no direct data in the document**

**Total study budget:** about $170 **ESTIMATED: sum of the above line items**

- **Hard stop:** if cumulative spend exceeds $300, pause and reassess.
- **User attention cost:** validate the normalization sample, resolve extraction disagreements, approve any proposal swaps, approve the final production verdict.

## What I Need From You

Two decisions after `/challenge --deep` produces its findings:

1. Do the 10 retrospective proposals look right, or should any be swapped? Confirm negative-control handling (replace vs add).
2. Approve the final verdict before any production change.

Everything else is model-driven.

## Out of Scope / Methodology Decisions Made Explicitly

- **Why not add arm B (single-shot, no personas)?** Different research question.
- **Why judge = Claude Opus in arm B'-fair, not no judge?** User's bar is "Claude spawning personas itself." A no-judge version returns raw persona findings, not a consolidated review, so it is not comparable to arm D.
- **Why not use `/explore` for direction-generation comparison?** `/challenge` is the skill under evaluation.
- **Why not evaluate on prospective outcomes only?** Prospective n=5 takes weeks; retrospective gives faster provisional signal. The decision matrix explicitly lets prospective override retrospective.

## Connection to Prior Work

- Supersedes `tasks/debate-efficacy-study-*`.
- Reuses prior scaffolding where valid: anonymization pipeline, adjudication template, and operational mechanics.
- Discards the prior verdict.
- `decision-drivers.md` may be used only as a pointer to artifacts; extractor sessions must independently derive outcome records from arm-independent sources.
- GPT critique (`tasks/debate-efficacy-study-gpt-critique.md`) is incorporated prospectively into this design rather than used as a post-hoc patch.

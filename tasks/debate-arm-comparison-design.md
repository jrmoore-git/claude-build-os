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

"Materially better" is defined across 7 impact dimensions (see below). This is a counterfactual-delta question, not a coverage question — the goal is measuring what the review **contributes** beyond a no-review baseline, and which arm contributes more on each dimension.

## Why This Matters

- **Cost stakes:** Measured mean `/challenge` cost is $1.88/call (confirmed via `stores/debate-log.jsonl`, n=157 historical runs). Annualized spend at current cadence: ~$4,500. If arm B'-fair ≈ arm D on impact, we recover ~90% of that spend.
- **Framework claim stakes:** BuildOS recommends cross-model review to adopters. That recommendation should be evidence-backed, not theory-backed. A properly designed study settles whether the recommendation holds.
- **Prior study is inadequate:** The 2026-04-17 debate-efficacy-study compared arm C (Claude+Sonnet mix, Gemini judge) vs arm D-modified (production personas, Gemini judge). Neither arm matched the user's stated bar ("single-model Claude spawning personas itself, no external judge"). Headline verdict ("drop-cross-model") extracted from a count metric that GPT's post-hoc critique correctly identified as rewarding atomization over insight. Study is superseded, not invalidated — its scaffolding (anonymization, adjudication pipeline) is reusable.

## Hypothesis

No pre-committed direction. User's prior: "models spawning their own assessors tends to be theater with bias; different models have genuinely different strengths" — which favors arm D winning. Design must not be shaped to confirm this prior; explicit decision matrix below applies mechanically to the data.

## Arm Definitions

### Arm B'-fair (single-model + internal personas)

**Primary implementation: `debate.py challenge` with all-Claude config.**
- `config/debate-models-arm-bfair.json`:
  - architect → claude-opus-4-7
  - security → claude-opus-4-7
  - pm → claude-opus-4-7
  - frame → claude-opus-4-7 (single mode, no dual-family expansion — that's cross-family)
  - judge_default → claude-opus-4-7 (same-session consolidation, matching user's "spawning personas itself" bar)
- Invocation: `python3.11 scripts/debate.py challenge --config config/debate-models-arm-bfair.json --proposal <X> --personas architect,security,pm,frame --enable-tools --output <path>`
- Same orchestration as arm D (LiteLLM dispatch, ThreadPoolExecutor for parallel challengers, same tool access budget).
- Zero cross-model. Zero cross-family. Judge is Claude-same-family-same-model (worst-case echo-chamber condition — surfaces bias if it exists).

**Secondary sanity check (on 2 proposals only):** A true Claude Code session spawns 4 persona subagents via Agent tool and consolidates itself. If output materially differs from primary B'-fair, flag as orchestration confound. If outputs converge, primary B'-fair is trusted.

### Arm D-production (multi-model + external judge)

- Invocation: `python3.11 scripts/debate.py challenge --proposal <X> --personas architect,security,pm,frame --enable-tools --output <path>` (uses default `config/debate-models.json`)
- Current production config: architect=claude-opus-4-7, security=gpt-5.4, pm=gemini-3.1-pro, frame-structural=claude-sonnet-4-6, frame-factual=gpt-5.4, judge=gpt-5.4
- **Not the modified arm D from the prior study.** That study swapped judge to Gemini to hold it constant with arm C. This study uses production arm D as-is.

### Controlled variables

- Same proposals, same prompts, same tool budget, same output format, same orchestration layer (`debate.py`).
- Only difference: model-family assignment across personas + judge.
- Tool access: `--enable-tools` on both arms (mirrors production default).

## Proposal Set

### Retrospective (n=10)

Selection criterion: maximize type diversity to avoid the governance-meta homogeneity of the prior study (which handed arm C an atomization-style advantage).

Proposals to include:

**Governance / methodology (reuse from prior study, drop streamline-rules):**
1. `tasks/autobuild-proposal.md` — governance, autonomous-execution loop
2. `tasks/explore-intake-proposal.md` — workflow redesign (shipped-revised)
3. `tasks/learning-velocity-proposal.md` — telemetry/automation (shipped-descoped)
4. `tasks/litellm-fallback-proposal.md` — infrastructure (rejected/pre-shipped)

**Architecture / code decisions (new to study):**
5. `tasks/review-lens-linkage-design.md` — architectural decision (D32, shipped)
6. `tasks/managed-agents-dispatch-proposal.md` — routing architecture
7. `tasks/model-routing-design.md` — cross-cutting infrastructure
8. `tasks/explore-redesign-proposal.md` — system redesign

**Research / measurement (new to study):**
9. `tasks/multi-model-skills-roi-audit-design.md` — research methodology
10. `tasks/judge-stage-frame-reach-audit-proposal.md` — audit design

**Explicit negative-control slot:** One proposal in the set must be a deliberately-flawed proposal where obvious defects exist. `tasks/negative-control-verbose-flag-proposal.md` if it fits; otherwise synthesize one from git history of a known-bad proposal.

**Drop from prior study:** `streamline-rules-proposal.md` — most atomizable, structurally distorts the count metric and by extension any metric that correlates with decomposition.

### Prospective (n=5 minimum, rolling)

Every real `/challenge` invocation after the study starts is dual-armed: both arm B'-fair and arm D run on it. Outcome labels added at t+1-2 weeks when actual decisions crystallize (shipped/shelved/reverted). Contamination-free by construction. Continues until n=5 prospective; more is better.

## Outcome Extraction Methodology

For each retrospective proposal, three fresh Claude sessions (no context from this study or prior study) independently read **only arm-independent sources** and produce a structured outcome record:

**Sources (allowed):**
- Proposal text itself
- `git log --oneline` around the proposal date + any commits referencing it
- `tasks/lessons.md`, `tasks/decisions.md`, `tasks/session-log.md`
- Actual source files the proposal affects
- Any production incident reports / reverts in the blast radius

**Sources (forbidden):**
- `tasks/*-challenge.md`, `tasks/*-debate.md`, `tasks/*-judgment.md`, `tasks/*-refined.md` for this or any proposal
- Either arm's output for this study (obviously, not yet produced)
- Any prior debate-efficacy-study artifacts

**Outcome record per proposal:**
- Outcome class: shipped-as-proposed / shipped-modified / shelved / rejected / pending / reversed
- Evidence per class: commit hashes, lesson IDs, decision IDs
- Per dimension (see 7 dimensions below): what actually happened? Cite evidence.
- Issues that materialized post-ship (if any): what broke, what got rewired, what caused a lesson?

**Consensus rule:** If all 3 fresh-session extracts agree on outcome class + evidence, trust it. If they diverge on any material point, surface the divergence — user adjudicates those specific cases (NOT the whole set). Expected disagreement rate: <15%.

## Impact Dimensions (7) — Review Value-Add

Every dimension asks: **"Did THIS arm's review materially improve [X] beyond what the proposer would have arrived at alone?"**

| # | Dimension | Evidence source |
|---|-----------|-----------------|
| 1 | **Direction improvement** — Did the review surface considerations that changed/strengthened the direction chosen? | Outcome record; compare finding content to actual decision rationale in decisions.md |
| 2 | **Nuance / subtlety caught** — Did the review surface non-obvious caveats, edge cases, tradeoffs in ideas already in the proposal? | Finding vs. proposal diff; judgment on "was this implicit in proposal or genuinely hidden?" |
| 3 | **Net-new ideas / alternatives introduced** — Did the review propose options/approaches/framings not in the original? | Mechanical diff: finding content vs. proposal content. Flag findings that introduce net-new candidates. |
| 4 | **Catch rate on things that materialized** — Of issues that later materialized (lessons, reverts, rework, incidents), how many did this arm catch in advance? | Outcome record's "issues materialized" list; match arm findings against it. |
| 5 | **Miss rate on things that materialized** — Complement of #4, kept separate as tie-breaker. CRITICAL_MISS (caused shipped failure) weighted 3x. | Same as #4; scored as inverse. |
| 6 | **Plan / architecture quality delta** — For proposals that advanced to plan/architecture docs, did review result in a stronger plan vs. pre-review version? | Compare pre-review proposal against post-review plan/design where both exist on disk. |
| 7 | **Code review quality delta** — For proposals that became code, did review catch code-level issues (logic, correctness, performance, maintainability) that would have shipped? | Post-ship bugfix commits in proposal's blast radius; match against findings. |

**Mapping to user's stated questions:**
- "Was direction improved more than it would have been?" → #1
- "Are there nuances?" → #2
- "Are there new ideas?" → #3
- "Are there things that weren't caught?" → #4 + #5 (catch AND miss, complementary)
- "Was the plan and architecture better?" → #6
- "Was the code review better?" → #7
- "Was our thinking improved with multiple models and a judge?" → aggregate of all 7

## Adjudicator Rubric — Comparative, 5-Point

Instead of rating each arm independently (the prior study's flaw), judges directly compare:

> **"Given the post-hoc outcome on [dimension X] for this proposal, and reading both arms' anonymized reviews, which arm's review — if acted on — would have led to a better [direction / plan / code / etc.] outcome?"**

Per-dimension 5-point scale:
- `B_SIGNIFICANTLY_BETTER` — B' would have prevented a major failure / surfaced a major missed insight / shifted direction materially
- `B_BETTER` — B' would have modestly improved the outcome
- `EQUAL` — no meaningful difference
- `D_BETTER` — D would have modestly improved
- `D_SIGNIFICANTLY_BETTER` — D would have prevented a major failure etc.
- `N/A` — dimension doesn't apply to this proposal

## Judge Setup — Three Independent Cross-Model

Three judges score independently per proposal per dimension:
1. **Gemini 3.1 Pro** (different family from arm B'-fair; shares one persona slot with arm D, partial independence)
2. **GPT-5.4** (different family from arm B'-fair; shares multiple slots with arm D, partial independence)
3. **Claude Opus 4.7 (fresh session, no study context)** — controls for claim: "Claude can adjudicate claims made by Claude challengers accurately." If judges 1+2 favor one arm and judge 3 disagrees, the disagreement itself is evidence of same-family bias.

**Agreement rule:** A per-dimension verdict counts toward the aggregate only if ≥2 of 3 judges agree. Disagreements surfaced as a list, not forced.

## Canonical Reformat — Anti-Style-Leakage

GPT-critique finding #7 on the prior study: "anonymization doesn't hide tool-call density, verbosity, or 'SPECULATIVE'/'EVIDENCED' language. Judge can infer arm from style." Fix:

Before judge sees findings, each finding is rewritten by a neutral LLM (claude-haiku-4-5 to minimize cost) to a canonical template:

```
FINDING #N:
CLAIM: [one sentence, neutral voice]
EVIDENCE: [one sentence naming source — file, commit, prior artifact]
TAG: [MATERIAL | ADVISORY] + [one of: ASSUMPTION, RISK, ALTERNATIVE, OVER_ENGINEERED, UNDER_ENGINEERED]
```

**Validation:** After reformat, user spot-checks 10 random findings (NOT 40% dual-labeling) to confirm reformat preserves substance. If substance is lost in ≥2 of 10, reformat methodology fails — fall back to raw findings + explicit "don't reward style" instruction to judges.

## Variance Measurement — Symmetric

**The prior study's biggest methodological gap:** variance was measured only for arm D, only on autobuild. Can't interpret inter-arm gaps without symmetric variance.

- Rerun **each arm** 2× on **3 proposals** (6 extra runs, 12 total). Proposals chosen to span type diversity (1 governance, 1 architecture, 1 research).
- Compute per-arm within-run variance on dimensions 1-7.
- If within-arm variance exceeds half the inter-arm gap on a dimension, that dimension's verdict is INCONCLUSIVE regardless of direction.

## Pre-Registered Decision Matrix

Applied mechanically after data collection. No post-hoc reasoning.

| Observation | Verdict |
|-------------|---------|
| Arm wins `*_BETTER` or `*_SIGNIFICANTLY_BETTER` on ≥4 of 7 dimensions, aggregated over ≥60% of proposals-where-dimension-applies, AND gap exceeds within-arm variance, AND ≥2/3 judges agree | **That arm wins.** Ship corresponding production config. |
| Arms split dimensions (each wins 2-3) with no dominance | **Nuanced keep.** Route to arm whose dimensions matter per context — document routing rules. |
| `CRITICAL_MISS` rate (dim #5) differs by ≥2x between arms | **Lower-CRITICAL_MISS arm wins** regardless of other dimensions. Preventing shipped failures dominates. |
| Retrospective verdict and prospective verdict (at n=5) disagree | **Prospective wins.** Retrospective is the more contaminated methodology. |
| Judges disagree on >50% of dimension scorings | **Inconclusive at current n.** Extend prospective arm; do not ship a verdict. |
| Canonical reformat validation fails (≥2/10 substance loss) | **Methodology failure; rework before any verdict.** |

## What This Study Does NOT Answer

Scope containment — honest non-goals:
- Does the **persona structure itself** add value over a single-shot single-model review? (That's arm B, skipped; separate study.)
- Does **cross-family diversity beyond 2 families** matter? (Would require arm with 4+ distinct families.)
- Is any **specific model swap** (e.g., dropping gpt-5.4 judge) worth doing independently?
- Does the study result generalize to `/review` (code diffs), `/polish` (6-round refinement), `/pressure-test`? (Those are separate skills with different task structure.)
- Does adding frame directives to `/explore` / `/pressure-test` / `/think discover` help? (The original question (b) from this session; deferred pending this study's outcome and evidence of real miss at those stages.)

## Execution Plan — Components

1. **Phase 0 — Design review** (this document through `/challenge --deep`). Incorporate findings before any API spend.
2. **Phase 1 — Outcome extraction.** 10 proposals × 3 fresh-session extractors = 30 extraction runs. User spot-audits divergences only.
3. **Phase 2 — Arm config.** Write `config/debate-models-arm-bfair.json`.
4. **Phase 3 — Arm execution.** 10 proposals × 2 arms = 20 runs. Plus 6 variance reruns (3 proposals × 2 arms × 2 reps).
5. **Phase 4 — Canonical reformat + user validation.** Reformat all findings; user spot-checks 10.
6. **Phase 5 — Triple-judge adjudication.** ~200 findings × 3 judges × 7 dimensions = ~4200 scorings (but judges score per-proposal-per-dimension, not per-finding → closer to 10 proposals × 7 dimensions × 3 judges = 210 comparative scorings).
7. **Phase 6 — Variance + agreement analysis.**
8. **Phase 7 — Apply decision matrix; write results.** Honest reading; if inconclusive, say so.
9. **Phase 8 — Prospective arm** (parallel, rolling). Starts Phase 3; synthesized when n=5+.
10. **Phase 9 — Final verdict + production change** (only if decision matrix produces clean verdict AND user approves).

## Budget Bounds

User stated: "don't care about cost or time." Still, explicit bounds for sanity:
- **API cost estimate:** Phase 3 at $1.88/call × 26 runs ≈ $50. Phase 5 at ~$0.10/scoring × 210 × 3 ≈ $60. Canonical reformat via haiku ≈ $5. Outcome extraction × 30 × cheap model ≈ $10. Variance + disagreement-resolution contingency: $25. **Total: ~$150.** 30x the prior study's actual $100 study day. Worth it for rigor.
- **Hard stop:** If cumulative spend exceeds $300, pause and reassess.
- **User attention cost:** Pick 2 extra proposals if desired (or delegate to me); validate reformat sample (10 findings); resolve outcome-extraction disagreements (expected <15%); approve final verdict.

## What I Need From You

Two decisions after /challenge --deep produces its findings:
1. Do the 10 retrospective proposals look right, or swap any?
2. Approve final verdict before production change.

Everything else is model-driven.

## Out of Scope / Methodology Decisions Made Explicitly

- **Why not add arm B (single-shot, no personas)?** Different research question ("does persona structure add value"). Bundling dilutes both answers.
- **Why judge = Claude-opus in arm B'-fair, not no-judge?** User's bar says "Claude spawning personas itself" — the "itself" implies the same Claude also consolidates. A no-judge version returns raw persona findings, not a verdict. Apples-to-oranges with arm D output.
- **Why not use `/explore` for direction-generation comparison?** `/challenge` is the skill under evaluation; `/explore` generates divergent options, different task. Separate study if useful.
- **Why not evaluate on real-world outcomes only (no retrospective)?** Prospective n=5 takes weeks; retrospective gives faster provisional signal. Decision matrix explicitly prefers prospective when they disagree.

## Connection to Prior Work

- Supersedes `tasks/debate-efficacy-study-*`. Prior study's scaffolding (anonymization pipeline, adjudication template) is reused; prior verdict is discarded.
- Prior study's `decision-drivers.md` content is reusable as seed data for outcome extraction, but extractor sessions must re-derive independently to avoid contamination.
- GPT critique (`tasks/debate-efficacy-study-gpt-critique.md`) methodology points baked into this design, not retrofitted.

---

**End of design. Pending `/challenge --deep` before any execution.**

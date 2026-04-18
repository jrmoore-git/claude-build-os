---
topic: debate-efficacy-study
created: 2026-04-17
---
# Debate Efficacy Study — Does Cross-Model Debate Beat Cheaper Alternatives?

## Project Context

BuildOS is a governance framework for Claude Code that hardens LLM-driven software engineering via skills, hooks, and cross-model review gates. The load-bearing component under scrutiny here is **the debate system** — `scripts/debate.py` (~4,100 lines) plus the `/challenge`, `/review`, and `/polish` skills that invoke it via a LiteLLM proxy to route across Claude, GPT, and Gemini families. `/challenge` runs 4 adversarial personas (architect, security, pm, frame) as cross-model challengers plus an independent judge; `/review` runs 3 cross-model reviewers on code diffs.

## Recent Context

- **2026-04-17:** Frame lens shipped as 4th `/challenge` persona after n=5 paired validation (`tasks/frame-lens-validation.md`). Dual-mode frame-structural (claude-sonnet-4-6, no tools) + frame-factual (gpt-5.4, tools on) added ~30 novel MATERIAL findings beyond the prior 3-persona panel across 5 historical proposals; flipped one verdict from REVISE → REJECT (litellm-fallback feature already shipped). L44 codified the evidence bar: **n≥3 (ideally 5+) paired comparisons on output quality before shipping LLM tuning decisions**.
- **`docs/current-state.md` names the next action:** "Run paired output-quality audit (n=5, paired comparisons, quality first per L44) across other personas and other multi-model systems. Determine where the verification-vs-reasoning tool-posture axis from L43 generalizes." This study formalizes that work.
- **Negative priors already on record:** D5 (single model + divergence prompts produced more diverse output than multi-model for thinking modes — multi-model NOT always better); L28 (3 independent models unanimous-and-wrong when operational evidence missing); L33 (debate.py --enable-tools produced 0.98-confidence false claim a `ls hooks/` would have refuted in 0.1s).

## Problem

The debate system is load-bearing governance infrastructure (Stage 1 gate `/challenge`, Stage 2 `/challenge --deep`, Stage 3 review `/review`). Its design is grounded in theory + localized paired validation (frame-lens n=5 within the debate framework), but we have **no direct comparison against cheaper alternatives**.

The decision-relevant question: **does multi-model add value beyond multi-persona?** If a Claude-only persona panel (4 parallel Claude Opus subagents with the same persona prompts) produces findings of equivalent quality to the full cross-model debate, the model diversity is decoration and dropping it cuts ~10x of debate API spend on `/challenge` and `/review` with no quality loss. If cross-model produces substantially more novel MATERIAL findings, the current spend is validated.

Who this affects: Justin (primary user), any future BuildOS adopter. What it costs today: debate.py runs ~5-10 times/day across `/challenge` + `/review` + `/polish`. Each `/challenge` is ~$0.15-0.25 under the current 4-persona + judge config. Over a year that's several hundred dollars of potentially unnecessary spend — small in absolute terms, but the *framework* recommends this system to others, and that recommendation should be load-bearing on evidence, not theory.

## Proposed Approach

**Approach C (minimal isolation):** Run arm C (Claude-only persona panel via `Agent` tool — 4 parallel Claude Opus subagents with architect/security/pm/frame prompts) against arm D (current multi-model debate) on the 5 frame-lens-validation proposals (autobuild, explore-intake, learning-velocity, streamline-rules, litellm-fallback). Use the canonical MATERIAL findings documented in `tasks/frame-lens-validation.md` plus git-history review as ground truth. Measure per-arm precision, recall, unique-catches, and cost/finding. External judge: Gemini 3.1 Pro (not part of arm C, independent of arm D's persona models). 20% dual-label (1 of 5 proposals) by Justin to measure judge agreement.

**Non-goals:**
- NOT comparing to "no review at all" (arm A)
- NOT comparing to "single Claude subagent" (arm B)
- NOT running prospective arm on held-out future proposals
- NOT studying `/review` code review, `/polish` rounds, or `/pressure-test`

**Escalation rule:** If the C-vs-D distinction is smaller than paired-comparison noise floor (no arm catches ≥2 more unique MATERIAL findings than the other on 3+ of 5 proposals), escalate to Approach B (retrospective 4-arm, ~$150-400). If B still inconclusive, run Approach A (full 4-arm retro + prospective, $300-800 + 2-4 weeks).

## Simplest Version

Approach C IS the simplest version. A smaller version would be n=1 which violates L44. A sanity-check variant: run only 2 of the 5 proposals first (autobuild + explore-intake), see if the arms separate cleanly before investing in all 5.

### Current System Failures

This is not a bugfix — there are no "failures" in the debate system to point at. The failure mode being addressed is **absence of evidence**: the system works well enough to ship findings, but we can't distinguish "this finding came from cross-model insight" from "this finding came from persona structure alone." Three indirect signals:

1. **L28 (2026-04-15):** 3 independent models via `/challenge` unanimously recommended killing sim-compiler as "commodity" — wrong, and dangerous enough that the decision was reversed in D20. The failure mode was correlated error, which the 4-persona panel is supposed to catch. Whether it actually does remains untested against the cheaper alternative.
2. **L33 (2026-04-15):** `/challenge --enable-tools` produced 0.98-confidence false claim ("BuildOS hooks don't exist") across 2 of 3 models. Judge accepted. A Claude subagent with `ls hooks/` tool access would have found the answer in one call. This is evidence that multi-model doesn't reliably beat a single deterministic check for verifiable claims.
3. **D5 (2026-04-10):** Tested 3 different models vs 1 model prompted 3 times with forced divergence on a strategic decision. **Single-model with divergence prompts produced more diverse output than multi-model.** This is direct evidence that cross-model ≠ cross-viewpoint for some task classes; we just haven't tested whether `/challenge`'s persona task is one of them.

### Operational Context

- `stores/debate-log.jsonl`: 447 entries. Each entry records phase (challenge/judge/review/refine/polish), debate_id, challengers count, accepted/dismissed counts. **Does not record outcome labels** (was the debate right? did the proposal ship? did findings materialize?). Outcome labeling is net-new manual work required for this study.
- Debate runs per day: ~5-10 based on commit cadence and `/challenge` invocation patterns.
- Per-`/challenge` cost estimate (from frame-lens-validation cost summary): ~$0.15-0.25 API spend, ~95-120s wall time with 4 personas + judge + `--enable-tools`.
- Frame-lens-validation outputs on disk: `/tmp/frame-pairs/*.md` (n=4 paired), `/tmp/frame-historical/*-dual.md` (n=5 same-family), `/tmp/frame-crossfamily/*.md` (n=5 cross-family). Ground truth material for this study lives in these files plus the proposals' commit histories.

### Operational Evidence

**Paired-comparison methodology has direct prior art in this codebase:**
- **Frame-lens-validation** (n=5 across 3 rounds) is the nearest methodological analogue. It compared tools-on vs tools-off (Round 1, n=4), dual-frame vs 3-persona historical (Round 2, n=5), and cross-family vs same-family (Round 3, n=5). Outcome: 4th persona adopted; cross-family routing adopted; L44 promoted the methodology to a durable rule.
- **D5's n=1-per-condition test** (single model with divergence vs multi-model) showed the core premise of cross-model is *not universally true* across skill types — creates the priority motivation for this study.

**What has NOT been tested:**
- Multi-model (arm D) vs multi-persona-single-model (arm C) head-to-head on `/challenge`'s specific task.
- Whether debate's cost per MATERIAL finding is competitive with simpler review structures.
- Whether cross-family diversity in arm D is the active ingredient, or whether cross-persona prompting alone suffices.

### Baseline Performance

Current production `/challenge` (arm D, default config): ~$0.15-0.25 per run, ~95-120s wall, ~4-8 MATERIAL findings per proposal (from frame-lens-validation cost summary). Before frame lens shipped, 3-persona panel caught 0/5 "already shipped" proposals; after, 5/5. Baseline quality is non-zero but not saturated — still measurable headroom for the next comparison. This study doesn't replace or modify the existing system; it measures its marginal value against a cheaper alternative.

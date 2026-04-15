---
topic: challenge-pipeline-fixes
created: 2026-04-15
---
# Challenge Pipeline Structural Fixes

## Project Context
Build OS is a governance framework for building with Claude Code — 22 skills, a cross-model debate engine (`scripts/debate.py`, 4,136 lines, 9 subcommands), 17 hooks, and rules in `.claude/rules/`. The debate engine powers 5+ skills by sending proposals and documents to 3 LLM models (claude-opus-4-6, gpt-5.4, gemini-3.1-pro) for independent evaluation.

The `/challenge` skill is the primary go/no-go gate. It assembles a proposal, sends it to 3 cross-model challengers, synthesizes findings, and recommends proceed/simplify/pause/reject. Every non-trivial feature passes through this gate.

## Recent Context

**Session 11 (current):** A/B tested proposal quality passed to cross-model challengers. Thin proposals (52 lines, no project context) caused model divergence, wasted tool calls, and less specific findings. Enriched proposals (150 lines, full project context) caused convergence, fewer tool calls, and more specific findings. Audited all 22 skills: 6 of 10 debate-calling skills have thin context. Web research validated findings (Google ICLR 2025: insufficient context raises hallucination from 10.2% to 66.1%). Built context packet spec and refined it through 6 cross-model rounds.

**Concurrent session (separate conversation):** Found that `/challenge` produced a systematically wrong verdict on the sim-compiler proposal. All 3 models converged on "don't build, it's commodity" — but they lacked operational evidence that a bespoke version had already proved its value across 17 rounds of iteration. The pipeline fed reviewers the proposal and structural audit findings, but NOT the eval_intake.py iteration history, eval results, or persona cards proving the approach worked.

**Sessions 7-10:** Built linter (246 lines, 9 checks), fixed all 22 skills, wired PostToolUse hook. Wrote 76 linter tests + 106 debate.py pure-function tests.

## Problem

The `/challenge` pipeline has four structural bugs that cause systematically wrong evaluations when the input is incomplete. These were discovered independently in two separate sessions and produce the same root cause: models evaluate in a vacuum and converge on plausible-but-wrong answers.

**Bug 1: Proposals don't include operational evidence.** When a proposal generalizes an approach that already delivered results, challengers don't know. They evaluate "should we build X?" without knowing "a bespoke version of X already saved us days of work." The proposal template has no section for prior results or track record.

**Bug 2: "Commodity" claims aren't verified before influencing judgment.** Challengers say "DeepEval/LangSmith/MLflow already do this" and the judge accepts it. Nobody checks whether those tools actually meet the specific requirements. The `--verify-claims` flag exists on `debate.py judge` but isn't wired for build-vs-buy claim verification.

**Bug 3: Unanimous convergence amplifies correlated error.** Three models with the same blind spot produce three copies of the same wrong answer, which looks like strong consensus. The pipeline treats unanimity as high confidence. No advocate role exists — everyone defaults to skepticism because that's what `/challenge` is designed for.

**Bug 4: Thin context packets across 6 skills.** Six of ten debate-calling skills (pressure-test, elevate, polish, explore, healthcheck, simulate) pass thin or no project context to `debate.py`, forcing models to waste tool calls reconstructing basics. Validated by A/B test: enriched context reduced Claude's tool calls from 29→22, GPT's from 14→9, and caused all 3 models to converge on the same finding.

## Proposed Approach

Four layers, ordered by cost and impact:

### Layer 1: Operational Evidence section in proposal template (TRIVIAL)
Add `## Operational Evidence` to the `/challenge` proposal template (Step 3 in SKILL.md). Three questions:
- Has any version of this approach been tried? What happened?
- What data exists (eval results, metrics, session log entries)?
- What's the before/after on the dimension it's trying to improve?

If empty — fine, it's greenfield. But if there IS a track record and it's not included, the challenge evaluates in a vacuum.

### Layer 2: Context packet standard for all debate.py calls (SMALL)
Apply the context packet spec (`tasks/context-packet-spec-refined.md`) to the 6 thin-context skills. Each debate.py call gets: Project Context (30-50 lines), Recent Context (20-30 lines), the artifact, and optional evaluation-specific context via `enrich_context.py`.

Partially started in this session — edits in progress to all 6 skills.

### Layer 3: Build-vs-buy claim verification (MEDIUM)
When a challenger says "tool X already does this," flag the claim for verification before the judge rules. The verification asks: "Does tool X meet these specific requirements?" — not just "does tool X exist?" Wire into `debate.py judge --verify-claims` for this specific claim type.

Implementation: Extract "commodity" or "already exists" claims from challenge findings. For each, run a focused Perplexity query matching the proposal's specific requirements against the named tool. Inject verification results into judge context.

### Layer 4: Dissent requirement on unanimous kill (MEDIUM)
If all challengers converge on "don't build" / "reject," force a second round where one model switches to advocate. Their job: "Make the strongest possible case FOR this proposal. What evidence would change the verdict? What is the panel missing?"

This doesn't guarantee correctness, but breaks correlated error. If the advocate can't find a compelling case, the kill is strengthened. If they can, it surfaces the blind spot.

### Not proposed (deferred): Value/build-buy phase split
Splitting `/challenge` into two phases (value assessment then build-vs-buy) is architecturally sound but changes how the skill fundamentally works. Layers 1-4 address the immediate bugs. If Layers 3-4 prove insufficient, the phase split becomes Layer 5.

## Simplest Version

Layer 1 alone: add `## Operational Evidence` to the proposal template. One edit to `/challenge` SKILL.md. Zero code changes. Addresses the single highest-impact bug (proposals missing track records that would change the verdict).

### Current System Failures

1. **Sim-compiler false kill (session 7-8):** All 3 models converged on "don't build, it's commodity." Verdict was wrong — a bespoke version had already proved its value across 17 iterations. Root cause: proposal lacked operational evidence. The "commodity" label was accepted without specific requirement matching.

2. **Next-build-priorities thin proposal (session 11, Run 1):** Thin proposal (52 lines) caused Gemini to barely engage (3 tool calls), models to diverge (one said "scrap tests," another said "add tests"), and findings lacked specificity. Enriched version (150 lines) caused convergence and specific findings.

3. **Six thin-context skills (session 11 audit):** pressure-test, elevate, polish, explore, healthcheck, and simulate all pass thin or no project context to debate.py. Models waste initial tool calls reconstructing what the project is. Research confirms: insufficient context increases hallucination from 10.2% to 66.1% (Google/ICLR 2025).

### Operational Context

- debate.py runs ~5-10 times/day across challenge, review, explore, polish, pressure-test
- `/challenge` is the primary gate — every non-trivial feature passes through it
- 10 skills call debate.py; 4 have rich context, 6 have thin/no context
- `--verify-claims` flag exists on `debate.py judge` but is not wired for build-vs-buy verification
- `enrich_context.py` (146 lines) exists with `--scope` flag but only 4 skills use it
- debate-log.jsonl tracks all runs

### Baseline Performance

- **Context quality:** 4 skills pass rich context, 6 pass thin/no context
- **Tool call overhead:** Run 1 (thin): Claude 29, GPT 14, Gemini 3. Run 2 (enriched): Claude 22, GPT 9, Gemini 6.
- **Cross-model convergence:** Run 1 diverged. Run 2 converged. No dissent mechanism exists.
- **Claim verification:** `--verify-claims` exists but is never invoked automatically for build-vs-buy claims
- **False kill rate:** At least 1 confirmed (sim-compiler), unknown total — no tracking exists

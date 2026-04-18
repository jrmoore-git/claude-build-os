---
debate_id: debate-efficacy-study-findings
created: 2026-04-17T13:05:17-0700
mapping:
  A: claude-opus-4-7
  B: gpt-5.4
  C: gemini-3.1-pro
  D: claude-sonnet-4-6
  E: gpt-5.4
personas:
  A: architect
  B: security
  C: pm
  D: frame-structural
  E: frame-factual
---
# debate-efficacy-study-findings — Challenger Reviews

## Challenger A (architect) — Challenges
Key structural facts verified:
- Arm D personas span 3 model families: claude-opus (architect), gpt-5.4 (security), gemini-3.1-pro (pm), claude-sonnet (frame). Judge is gpt-5.4.
- `debate_outcome.py` / `cmd_outcome_update` exists, so outcome labeling has tooling scaffolding.
- `persona_model_map` includes a `staff` persona NOT used in `/challenge` (4 personas) — possibly used elsewhere.

Now the architectural critique.

## Challenges

1. **[ASSUMPTION] [MATERIAL] [COST:TRIVIAL]**: The proposal treats arm C as "4 parallel Claude Opus subagents with the same persona prompts" but the production arm D mixes *three* model families where the **judge is gpt-5.4** (EVIDENCED: `judge_default=gpt-5.4`, persona map spans claude-opus, gpt-5.4, gemini-3.1-pro, claude-sonnet). If arm C also uses gpt-5.4 as judge, you're not testing "Claude-only" — you're testing "Claude challengers + GPT judge" vs "multi-family challengers + GPT judge." That isolates challenger diversity but the headline framing ("cross-model add value?") is broader than what the experiment measures. Fix: either state the scope precisely ("challenger-side model diversity only, judge held constant") or add an arm C' with a Claude judge. Trivial to fix in the write-up; material because it changes what conclusion the study can support.

2. **[RISK] [MATERIAL] [COST:SMALL]**: Ground-truth contamination. The "canonical MATERIAL findings" in `tasks/frame-lens-validation.md` were *produced by arm D itself* (or its predecessors). Using arm-D-derived findings as ground truth to score arm C is a rigged comparison: any finding arm D alone surfaced enters the truth set; any finding arm C alone surfaces has no ratification path and looks like a false positive. The frame-lens-validation study had the same structure but was testing tools-on vs tools-off within the same family of outputs — here you're comparing a system to its own historical output. Mitigation: add a blind re-adjudication pass where Justin + the external Gemini judge score findings from both arms *without knowing which arm produced them*, and allow arm-C-unique findings to enter the truth set if independently validated against git history. This is SMALL work but decision-changing — without it, arm D almost certainly "wins" by construction.

3. **[UNDER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]**: n=5 with a pre-committed escalation rule is fine, but the escalation trigger ("no arm catches ≥2 more unique MATERIAL findings than the other on 3+ of 5 proposals") conflates two different null results: (a) arms are equivalent (drop cross-model, save money), (b) measurement noise drowns the signal (inconclusive, need more n). These have opposite action implications. Pre-register a decision matrix: if arms tie AND within-arm run-to-run variance (measured by re-running arm D once on 1 proposal) is smaller than the C-vs-D gap, call equivalence; if variance dominates, escalate. One extra arm-D rerun, ~$0.25.

4. **[ALTERNATIVE] [ADVISORY]**: The proposal skips arm B (single Claude subagent, no persona structure) as a non-goal, but B is the *cheapest* intervention and would answer a different load-bearing question: does the persona structure itself add value, or is it the model capability? If C ≈ D, you've shown model diversity is decoration but still don't know whether persona decomposition is doing the work. Deferring B is defensible given budget, but note that C vs D alone cannot support a recommendation to simplify `/challenge` — only to change its model routing.

5. **[RISK] [ADVISORY]**: L33 (the 0.98-confidence false claim) is cited as motivation but isn't in the study design. The study measures *finding quality on historical proposals where ground truth is mostly structural*, not *hallucination rate on verifiable factual claims*. If cross-model's real failure mode is correlated factual hallucination (L33) and its real value is correlated structural reasoning (unmeasured here), this study will cleanly answer the wrong question. Consider adding one factual-claim probe per proposal as a secondary metric.

6. **[OVER-ENGINEERED] [ADVISORY]**: 20% dual-label (1 of 5) gives essentially no statistical power on judge agreement — it's a single data point. Either accept this as a sanity check (say so) or dual-label everything; there's no middle ground at n=5.

## Concessions

1. Scope discipline is strong: explicitly excluding `/review`, `/polish`, `/pressure-test`, prospective arms, and arms A/B keeps the study finishable. The pre-committed escalation ladder (C → B → A) is exactly the right shape.
2. Reusing the n=5 frame-lens-validation corpus is pragmatic — ground-truth work is partially amortized, and it aligns with L44's n≥3 (ideally 5+) bar.
3. Picking Gemini 3.1 Pro as external judge (not a member of arm C, independent of arm D's challenger set though same family as two arm D personas) is a sensible independence choice given what's available.

## Verdict

**REVISE** — the study is well-scoped and proportionate, but two material issues (ground-truth contamination from arm-D-derived findings, and imprecise framing about which diversity axis is actually being tested given the shared gpt-5.4 judge) will let the conclusion be attacked regardless of outcome. Both fixes are trivial-to-small; this is a build condition, not a redesign.

---

## Challenger B (security) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal treats `tasks/frame-lens-validation.md` plus git-history review as “ground truth,” but that is not an independently validated truth source; it is prior model output plus retrospective interpretation. That creates a circularity risk where arm D is judged against labels partly derived from the same debate framework it is meant to justify, which can over-credit the incumbent and under-measure false negatives/false positives from both arms. Fix by defining a blinded adjudication protocol per finding with explicit evidence requirements from proposal text, repo state, and ship/outcome history rather than reusing prior challenge artifacts as canonical truth.

2. [RISK] [MATERIAL] [COST:SMALL]: The Claude-only arm C introduces a trust-boundary change that is security-relevant: the proposal says it will run “via `Agent` tool — 4 parallel Claude Opus subagents,” while the current debate path routes through LiteLLM and existing cost/event plumbing. Managed-agent/provider paths in this repo explicitly rely on Anthropic-hosted isolation and retention assumptions, not BuildOS-local proxy controls, and cost logging parity is already documented as a gap in the managed-agent client comments. If study prompts contain internal proposals or sensitive roadmap material, arm C may send them to a different external service path with different retention/observability guarantees, confounding both security posture and cost measurement. Fix by pinning the exact transport for arm C, documenting data handling differences, and redacting or excluding sensitive proposals if the provider path differs from arm D.

3. [UNDER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: The proposal names an “external judge: Gemini 3.1 Pro” but gives no prompt-injection or contamination controls for judging model outputs that may include embedded instructions from either arm. Since the artifacts being judged are model-generated text, the trust boundary is untrusted output → judge prompt. Without a fixed wrapper that quotes outputs as data and forbids instruction-following from submissions, the judge can be steered by arm-produced prompt injections or formatting tricks, biasing results. Add a strict judging template that treats arm outputs as inert evidence, strips tool directives, and records the raw prompts used.

4. [UNDER-ENGINEERED] [ADVISORY]: Cost comparisons are likely to be noisy unless you normalize for transport differences and existing logging limitations. The repo logs debate events to `stores/debate-log.jsonl` with per-event costs, but the proposal already notes outcome labels are absent, and managed-agent comments note weaker centralized cost visibility. If arm C uses a non-LiteLLM path, “cost/finding” may not be directly comparable without a separate ledger.

5. [ALTERNATIVE] [ADVISORY]: Consider a small blinded within-proposal crossover before the full study: anonymize arm outputs and randomize ordering for the external judge and Justin dual-label pass. This does not change the core recommendation but would reduce anchoring bias toward the incumbent multi-model format.

## Concessions
- The proposal correctly identifies the main failure being addressed as absence of evidence, not a fabricated bug, and it names the risk of not changing: continued spend and governance recommendations without direct comparative validation.
- It explicitly uses paired comparisons and an escalation rule rather than overcommitting to a large study upfront.
- It keeps production unchanged while measuring marginal value, which limits operational blast radius.

## Verdict
REVISE — the study is directionally sound, but it needs an independent labeling protocol and clearer controls around provider/data-handling differences and judge contamination before its results should drive governance decisions.

---

## Challenger C (pm) — Challenges
## Challenges
1. [RISK] [MATERIAL] [COST:SMALL]: Negative ROI on optimization effort. The proposal aims to optimize an API spend of ~$1.50-$2.50 per day (5-10 runs at $0.15-$0.25) [EVIDENCED]. The engineering time required to manually label outcomes, run paired comparisons, and analyze results will immediately exceed years of potential API savings. Unless BuildOS is about to be deployed to thousands of users, this is premature optimization.
2. [OVER-ENGINEERED] [ADVISORY]: Solving for a non-problem. The proposal explicitly admits "there are no 'failures' in the debate system to point at" [EVIDENCED]. Validating the theoretical purity of multi-model vs multi-persona is an academic exercise that distracts from fixing actual user-facing failures. 

## Concessions
- Grounding the experiment design in established, previously successful patterns (L44 paired comparisons).
- Recognizing the need to separate tooling/posture from underlying model diversity.
- Clearly defining the escalation paths and non-goals.

## Verdict
REJECT because the engineering effort to conduct the study vastly outweighs the negligible daily API cost savings of an already-functional system.

---

## Challenger D (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL] [COST:SMALL]:** The study treats "MATERIAL findings" as a stable, objective ground truth, but the canonical findings in `tasks/frame-lens-validation.md` were themselves produced by the debate system (arm D). Using arm D's prior outputs as ground truth to evaluate arm D vs arm C introduces circular validation — arm D is structurally advantaged because the ground truth was shaped by its own output patterns, persona framing, and judge. A truly independent ground truth (e.g., retrospective outcome labeling from what actually broke in production, or a separate human audit of the proposals) is absent from the candidate set. The proposal acknowledges "outcome labeling is net-new manual work" but doesn't include it as a candidate approach, treating the existing debate-derived labels as sufficient.

2. **ALTERNATIVE [MATERIAL] [COST:SMALL]:** The candidate set skips **arm B (single Claude subagent, no persona structure)** as a non-goal, but D5 and L33 together make this the most decision-relevant comparison. D5 showed single-model-with-divergence-prompts beat multi-model on diversity. L33 showed multi-model accepted a false claim a single deterministic tool call would have caught. The question "does persona structure add value beyond a single capable model?" is arguably more load-bearing than "does cross-model add value beyond multi-persona?" — because if arm B ≈ arm C ≈ arm D, the entire debate architecture is decoration. Excluding arm B as a non-goal is an unstated assumption that persona structure is already validated, which it isn't.

3. **ASSUMPTION [MATERIAL] [COST:TRIVIAL]:** The cost framing ("several hundred dollars/year, small in absolute terms") is ESTIMATED and then immediately discounted, but the proposal's own escalation path (Approach B: $150-400, Approach A: $300-800) means the study itself may cost more than a year of the system it's evaluating. The proposal doesn't acknowledge this inversion. If the study costs $300-800 to reach a conclusion, and the annual spend being evaluated is "several hundred dollars," the ROI of the study is negative unless the recommendation generalizes to other BuildOS adopters. That generalization claim is asserted but not examined.

4. **ASSUMPTION [ADVISORY]:** The proposal assumes Gemini 3.1 Pro is a genuinely independent judge because it's "not part of arm C, independent of arm D's persona models." But Gemini was already used in arm D's cross-model panel. If Gemini's evaluation style is correlated with its challenger style (same model family, same training), it may systematically favor findings that resemble its own challenger outputs. A judge from a completely orthogonal family (e.g., a human, or a model not used in either arm) would be cleaner. This is advisory because 20% dual-label by Justin partially mitigates it.

5. **OVER-ENGINEERED [ADVISORY]:** The escalation ladder (C → B → A) is pre-built before knowing whether the C-vs-D signal is even measurable on n=5 retrospective proposals. The "sanity-check variant" (run 2 of 5 first) is mentioned but framed as optional. Given that the ground-truth circularity problem (finding #1 above) could invalidate the entire retrospective methodology, the sanity check should be the *first* gate, not an optional shortcut — and it should include a check on whether the ground truth labels are arm-D-independent before investing in all 5.

6. **ALTERNATIVE [ADVISORY]:** A missing candidate is **prospective-only, n=3**: run the next 3 real `/challenge` invocations in production simultaneously under both arms (arm C and arm D), with Justin labeling findings blind before seeing which arm produced them. This avoids the ground-truth circularity entirely, costs ~$5-10 in API spend, and produces outcome-labeled data. The proposal explicitly excludes prospective comparison as a non-goal without explaining why — the stated reason ("held-out future proposals") doesn't address the circularity problem that retrospective comparison creates.

---

## Concessions

1. **The escalation structure is sound in principle.** Starting with the cheapest arm (C-only vs D) before committing to a full 4-arm study is correct sequencing, and the explicit noise-floor criterion for escalation is more rigorous than most such proposals.

2. **The negative priors (D5, L28, L33) are genuinely load-bearing.** The proposal doesn't cherry-pick evidence for the system — it leads with the strongest cases against it. This is methodologically honest and correctly motivates the study.

3. **The 20% dual-label by Justin is a real calibration mechanism.** Including human agreement measurement on judge labels is the right instinct, even if the judge-independence concern above partially undermines it.

---

## Verdict

**REVISE** — The candidate set has one material structural flaw: using arm D's prior outputs as ground truth to compare arm C vs arm D is circular, and the exclusion of arm B (single-model baseline) removes the comparison most directly motivated by the codebase's own negative priors (D5, L33). Both issues are fixable without redesigning the study — either by adding independent outcome labeling as a prerequisite gate, or by substituting a small prospective arm for the retrospective ground truth. The study as framed risks producing a result that validates arm D by construction.

---

## Challenger E (frame-factual) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal claims `stores/debate-log.jsonl` “does not record outcome labels,” but the repo already ships outcome logging via `scripts/debate.py outcome-update` and `scripts/debate_stats.py` explicitly aggregates `outcomes`. `scripts/debate_outcome.py:13-32` appends `phase: "outcome"` records with implementation/validation/reversal fields, and `scripts/debate_stats.py:33-50`/header notes say stats include outcomes. The manual labeling burden may still be real for historical runs, but the premise that outcome labeling is net-new infrastructure is falsified by shipped code.

2. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The proposal says `scripts/debate.py` is “~4,100 lines,” but the current file is 3,863 lines (`read_file_snippet` metadata for `scripts/debate.py`). This matters because the writeup uses file size as part of its framing for “load-bearing complexity”; that framing should be updated to current state.

3. [ALTERNATIVE] [MATERIAL] [COST:SMALL]: The proposal treats “Claude-only persona panel via Agent tool” as the minimal way to isolate model-family effects, but `debate.py` already supports direct model override paths (`--models` generic prompt and persona resolution through config), so you can likely run a same-engine same-output-format experiment by temporarily swapping `persona_model_map` to Claude models rather than introducing Agent-tool subagents as a different execution substrate. `scripts/debate.py:964-999` shows challenger construction is driven by config/personas, and `config/debate-models.json` already centralizes persona→model assignment. Changing both model family and orchestration mechanism at once risks confounding the result.

4. [UNDER-ENGINEERED] [ADVISORY]: The proposal’s external-judge plan says “Gemini 3.1 Pro (not part of arm C, independent of arm D's persona models),” but arm D already uses Gemini for PM by default (`config/debate-models.json:2-11`). So the judge is not independent of arm D’s model family; it is only independent of a specific arm instance. That doesn’t invalidate the study, but the writeup overstates independence and should describe this as partial independence.

## Concessions
- The proposal accurately reflects the newly shipped frame persona and dual-mode cross-family expansion (`docs/current-state.md:4-10`, `config/debate-models.json:13-16`).
- The cited “next action” in `docs/current-state.md` does in fact call for paired output-quality audits across other personas and multi-model systems (`docs/current-state.md:16-18`).
- The concern about testing cross-model value against cheaper alternatives is directionally consistent with current code/config, which still route `/challenge` across multiple model families by default (`config/debate-models.json:2-11`).

## Verdict
REVISE — the study direction is sound, but it overstates missing outcome infrastructure and proposes a confounded Arm C design when the existing debate config surface already supports a cleaner same-engine comparison.

### Quantitative claims
- “~5-10 times/day” debate usage — **SPECULATIVE**: no repo data verified here supports this frequency.
- “Each `/challenge` is ~$0.15-0.25” — **SPECULATIVE**: pricing exists in `scripts/debate_common.py:139-169`, but no measured run data was provided/verified here.
- “10x of debate API spend” reduction — **ESTIMATED**: plausible only if replacing cross-family panel + judge with Claude-only subagents materially reduces calls/tokens; proposal does not supply token accounting.
- “447 entries” in `stores/debate-log.jsonl` — **SPECULATIVE**: not verified from repo contents in this review.
- “~30 novel MATERIAL findings” and “flipped one verdict” — **EVIDENCED** by `docs/current-state.md:4-10`, though that is a repo doc claim rather than direct derivation from raw study artifacts.

---

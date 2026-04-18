---
debate_id: debate-arm-comparison-design
created: 2026-04-18T14:30:44-0700
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
# debate-arm-comparison-design — Challenger Reviews

## Challenger A (architect) — Challenges
Sufficient evidence. Key findings:

1. `--config` flag does not exist in debate.py CLI (0 matches for `--config` or `add_argument('--config'`), though `_load_config(config_path=None)` *does* accept a path parameter. So the proposed invocation line is wrong as written — needs a code change or env var to select config.
2. Production config actually uses `claude-sonnet-4-6` for architect/frame per `_DEFAULT_PERSONA_MODEL_MAP`, while the loaded JSON map per `read_config_value` shows `architect=claude-opus-4-7, frame=claude-sonnet-4-6`. The proposal describes production arm D as `architect=claude-opus-4-7` — that matches the JSON ✓. Good.
3. Proposal lists personas `architect,security,pm,frame` — missing `staff`. `VALID_PERSONAS` includes staff. Whether `/challenge` in production actually uses 4 or 5 personas is relevant to cost baseline.
4. The proposal's arm D description includes `frame-structural` and `frame-factual` as separate slots (dual-mode), but arm B'-fair collapses frame to single mode. This is a *real* confound the design half-acknowledges ("no dual-family expansion — that's cross-family") but doesn't address: arm D runs **5 challenger calls** (architect, security, pm, frame-structural, frame-factual) while arm B'-fair runs **4**. That's not just model-family difference — it's one extra persona-call. Cost comparison and finding-count comparison are both distorted.
5. Cost claim `$1.88/call, n=157` — cannot verify `stores/debate-log.jsonl` contents (stores/ not in allowed read set). SPECULATIVE on my end but plausible given architecture.

## Challenges

1. **RISK** [MATERIAL] [COST:TRIVIAL]: The invocation `python3.11 scripts/debate.py challenge --config config/debate-models-arm-bfair.json ...` will not work. Verified: `_load_config` accepts a `config_path` argument, but `scripts/debate.py` exposes no `--config` CLI flag (0 matches for `--config` or `"--config"` in scripts; 0 matches for `add_argument('--config'`). Phase 2 must either add a `--config` argparse flag (trivial) or use `DEBATE_CONFIG` env var (doesn't exist either — 0 matches for `DEBATE_CONFIG`). Design should name the mechanism it's adding rather than assume it exists. Build condition, not a reject.

2. **ASSUMPTION** [MATERIAL] [COST:SMALL]: Arm B'-fair is described as running personas `architect,security,pm,frame` (4 challengers), while production arm D runs `frame-structural` + `frame-factual` as two separate cross-family calls (per `debate_common.py` line 287: `frame_factual_model` is a distinct slot). So arm D fires **5 challenger calls + judge**, arm B'-fair fires **4 + judge**. This confounds three things the study claims to isolate: (a) cost comparison ($1.88 isn't the right baseline for a 4-call arm — it's lower), (b) finding-volume (more calls → more findings mechanically), (c) "frame coverage" (D gets two framings, B' gets one). Either add frame-factual as a second Claude-Opus frame call in arm B'-fair, OR collapse arm D to single-frame mode for the comparison. As currently designed, a finding that "arm D wins on dimension 2 (nuance)" is unattributable between model-family-diversity and one-extra-frame-call.

3. **RISK** [MATERIAL] [COST:TRIVIAL]: The "primary B'-fair = `debate.py` with all-Claude config" is *not* what the user's stated bar describes ("single-model Claude spawning personas itself, no external judge"). The primary implementation still routes through LiteLLM/ThreadPoolExecutor — it's all-Claude-via-API, not a Claude Code session spawning Task subagents. The design handles this by making the "true session" version a secondary n=2 sanity check. That's a reasonable compromise, but if the two diverge the study has no budget/plan for what happens — the design says "flag as orchestration confound" but doesn't say whether that voids the verdict. Add a row to the decision matrix: "if sanity-check divergence is material, primary B'-fair result is inadmissible and you re-run B'-fair at n=10 via the true-session path." Otherwise the sanity check has no teeth.

4. **UNDER-ENGINEERED** [ADVISORY]: The triple-judge setup uses judge #3 = Claude Opus (same family as arm B'-fair's challengers and judge). This is deliberately a same-family bias probe, good. But the agreement rule `≥2 of 3 judges agree` means that when judges 1+2 (Gemini+GPT) both favor arm D and judge 3 (Claude) favors arm B', the verdict is "arm D wins" — which is exactly the same-family-bias signal you wanted to detect, now silently absorbed into the majority. Surface this case explicitly: "if judge 3 is the outlier and the direction-of-disagreement correlates with arm family, flag as bias-contaminated and report both with and without judge 3."

5. **ASSUMPTION** [ADVISORY]: Cost bound `$150 total, hard stop $300`. Phase 3 is 26 runs × $1.88 ≈ $50 — but $1.88 is the mean for arm D (5 challengers + judge + tools). Arm B'-fair with all-Opus challengers may cost *more per call* than arm D (Opus is pricier than Sonnet/Gemini; arm D only has one Opus slot). If arm B'-fair averages $3-4/call, total moves to ~$200-250. Doesn't break the study but the $150 figure is ESTIMATED on an unjustified assumption that per-call cost is arm-invariant. Tag it honestly.

6. **OVER-ENGINEERED** [ADVISORY]: 210 comparative scorings × 3 judges + 30 extraction runs + 12 variance runs + reformat validation + prospective arm. This is rigorous, but the decision matrix has six rows, some of which route to "inconclusive" or "rework methodology." Probability that the study produces a clean actionable verdict (not "inconclusive," not "methodology failure," not "nuanced keep — route by context") is maybe 40-50% given realistic noise. Worth acknowledging upfront: there's a plausible path where $150-300 yields "results were mixed, keep current config." That's still informative, but set the expectation.

## Concessions

1. The symmetric-variance fix (both arms, multiple proposals) and the negative-control proposal slot directly address the two sharpest methodological flaws the GPT critique raised on the prior study. This is evidence-driven iteration, not hand-waving.
2. Pre-registered decision matrix with CRITICAL_MISS as dominant tie-breaker is the right structure — it prevents post-hoc narrative fitting, which is the failure mode the prior study hit.
3. The explicit non-goals section (arm B skipped, cross-family-beyond-2 skipped, `/review`/`/polish` skipped) correctly contains scope. Each of those is a separate study and bundling would dilute this one.

## Verdict

**REVISE** — the research design is methodologically sound and the decision matrix is well-constructed, but challenges 1–3 are must-fix before Phase 2: the `--config` CLI mechanism doesn't exist, the frame-persona asymmetry (4 vs 5 challenger calls) silently confounds the key comparison, and the sanity-check failure mode has no pre-registered consequence. All three are trivial-to-small fixes; fix them and execute.

---

## Challenger B (security) — Challenges
## Challenges
1. [UNDER-ENGINEERED] [ADVISORY]: The cost claims are too weakly grounded for planning confidence. **EVIDENCED:** the design cites `$1.88/call` from `stores/debate-log.jsonl, n=157 historical runs`. **SPECULATIVE:** the total `~$150`, `~$60` for scoring, `~$5` for reformat, `~$10` for extraction, and `~$25` contingency are not tied to token counts, prompt sizes, or verified model pricing in the proposal text. This does not block a move-fast experimental study, but those numbers should not drive scope decisions without a quick token-based sanity check.

2. [ASSUMPTION] [ADVISORY]: The proposal assumes arm B'-fair is a valid proxy for the user's stated target ("single-model Claude session with internal persona structure"), but your own design admits the primary implementation is still `debate.py challenge` with parallel persona orchestration and only a 2-proposal sanity check against a "true Claude Code session." If those differ materially, the main comparison answers "all-Claude debate.py orchestration vs production multi-model debate.py," not necessarily the user's actual counterfactual.

3. [UNDER-ENGINEERED] [ADVISORY]: The retrospective outcome-extraction pipeline risks contamination and inconsistency because it relies on "three fresh Claude sessions" reading repo history and documents, but the design does not specify a locked extraction prompt/schema beyond the outcome record fields. In practice, small prompt drift can swamp the claimed `<15%` disagreement expectation. This is a methodology robustness issue, not a security blocker.

4. [ASSUMPTION] [ADVISORY]: The canonical reformat step is a plausible anti-style-leakage control, but the validation threshold is somewhat thin: 10 random findings with failure at `≥2/10` substance-loss may miss systematic distortion of certain finding types (for example, nuanced tradeoff findings vs concrete factual findings). Given the study goal, this is acceptable, but the proposal is assuming that random spot checks will catch meaning loss reliably.

## Concessions
- The design explicitly evaluates both directions of risk: the risk of the multi-model system underperforming and the risk of not changing a costly production recommendation.
- It correctly identifies and addresses the prior study's major methodological flaws: non-comparable arms, count-metric distortion, style leakage, and asymmetric variance measurement.
- The repo already shows real debate/judge infrastructure and credential-loading paths in `scripts/debate.py`, `scripts/debate_common.py`, and `scripts/judge_frame_orchestrator.py`, so this is not proposing a fantasy workflow detached from implementation reality.

## Verdict
APPROVE with minor methodological tightening: the study is directionally sound and worth running, but treat budget and proxy-validity claims as provisional rather than settled.

---

## Challenger C (pm) — Challenges
## Challenges

1. **[OVER-ENGINEERED] [MATERIAL] [COST: SMALL]: The canonical reformat step destroys the signal it is trying to measure.**
Using a cheaper model (`claude-haiku-4-5`) to rewrite findings into a neutral, one-sentence template actively destroys the "nuance/subtlety" that Dimension #2 is explicitly trying to measure. If a complex architectural tradeoff is flattened into "CLAIM: The routing architecture has a flaw", the judges cannot evaluate depth of thought. 
*Fix:* Drop the intermediate rewrite. Present the raw text to the judges, but wrap it in an explicit `<ignore_style_and_verbosity>` system prompt instruction. If anonymization is strictly required, use the same tier of model (Opus/GPT-5.4) to do the rewrite, not Haiku.

2. **[ASSUMPTION] [MATERIAL] [COST: MEDIUM]: Fully automated outcome extraction will hallucinate false causal links.**
Relying on three "fresh Claude sessions" to read `git log`, source code, and `lessons.md` to establish the ground truth of what *actually* happened (Phase 1) assumes LLMs can accurately attribute post-hoc code changes to specific abstract proposal intents. LLMs routinely make plausible-but-false associative leaps here. Because you only review *divergences*, a shared hallucination across the three models becomes unverified "ground truth." 
*Fix:* For a sample size of only 10 retrospective proposals, human extraction (the user) of the actual outcomes is feasible, ensures high fidelity, and establishes an unimpeachable ground truth for the judges to evaluate against. 

3. **[RISK] [ADVISORY]: Prospective sample size (n=5) is too small to overrule retrospective data.**
The pre-registered decision matrix states that if retrospective (n=10) and prospective (n=5) verdicts disagree, prospective wins. However, n=5 is an extremely small sample size for a process with high variance (different topics, different authors, different complexity). Letting an n=5 sample cleanly override an n=10 sample risks making a policy decision on statistical noise.

## Concessions
1. The pivot to evaluating the *counterfactual delta* (what review caught vs. what happened) rather than just counting finding volume is a massive methodological upgrade.
2. The symmetric variance measurement natively addresses the biggest flaw in the prior study.
3. The pre-registered decision matrix mechanically binds the outcome to data, preventing post-hoc justification of user priors.

## Verdict
**REVISE** to either remove the Haiku-based reformat step or upgrade the model tier to preserve nuance, and replace the automated LLM outcome extraction with human ground-truth generation.

*(Quantitative Claims Note: $1.88/call and n=157 are [EVIDENCED]; ~$4,500 annualized and ~$150 study budget are [ESTIMATED].)*

---

## Challenger D (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL] [COST:MEDIUM]:** The candidate set assumes the only meaningful comparison axis is *model-family diversity* (single-family vs. multi-family). But the proposal's own "What This Study Does NOT Answer" section acknowledges that persona structure itself is a separate variable. This means arm B'-fair conflates two things: (a) single-family and (b) same-model-for-all-personas. A missing arm — call it B''-diverse-single-family — would use Claude Opus for some personas and Claude Sonnet/Haiku for others within the same family. This would isolate whether the benefit of arm D comes from *cross-family diversity* or merely *model-capability diversity*. Without this arm, a finding that "arm D wins" cannot be attributed to cross-family diversity specifically — it could be that any model mix beats a monoculture. The proposal's core claim ("different models have genuinely different strengths") is about families, but the design can't confirm that's the operative variable.

2. **ASSUMPTION [MATERIAL] [COST:SMALL]:** The proposal treats the judge as a passive scorer, but in arm D the judge is GPT-5.4 — the same model that plays two challenger roles (security, frame-factual). The judge in arm D is therefore not independent of the arm D challenger outputs. The proposal acknowledges partial independence for judges 1 and 2 in the adjudication phase, but does not acknowledge that the *internal* arm D judge (GPT-5.4) is scoring findings it partially generated. This is a within-arm conflict that could systematically inflate arm D's coherence scores (the judge will find its own framing familiar and well-structured). The proposal has no control for this. A missing candidate: arm D-clean-judge, where the arm D judge is replaced with a model that has no challenger role in either arm (e.g., Gemini for internal consolidation). Without this, the inter-arm comparison is partially confounded by judge-challenger identity overlap in arm D.

3. **ALTERNATIVE [MATERIAL] [COST:SMALL]:** The proposal's canonical reformat step (haiku rewrites all findings to a neutral template) is doing double duty: it's both an anti-style-leakage control and a substance-preservation step. But the validation rule (spot-check 10 of ~200 findings) is too weak to catch systematic reformat failures — haiku may consistently flatten nuance in a direction that favors one arm's finding style. A missing candidate: instead of reformat-then-validate, use a *blind interleaving* approach where the judge sees findings from both arms in a single shuffled list and scores them without knowing arm assignment, with arm identity revealed only after scoring. This is cheaper (no reformat LLM cost), more robust to systematic reformat bias, and is the standard approach in blinded comparative studies. The proposal chose reformat over interleaving without explaining why interleaving was rejected.

4. **ASSUMPTION [ADVISORY]:** The $1.88/call cost figure is tagged EVIDENCED (n=157, `stores/debate-log.jsonl`), but the annualized spend projection of ~$4,500 is SPECULATIVE — it requires an assumed call cadence that isn't stated. The proposal says "current cadence" without quantifying it. This doesn't affect the study design, but the cost-justification framing ("recover ~90% of that spend") is load-bearing for the "why this matters" section and rests on an unverified rate assumption.

5. **OVER-ENGINEERED [ADVISORY]:** The secondary sanity check (2 proposals run through a true Claude Code Agent-tool subagent setup) is described as a confound detector but has no decision rule attached to it. If outputs "materially differ," the proposal says "flag as orchestration confound" — but then what? There's no branch in the decision matrix for "orchestration confound detected." This check adds execution complexity and cost without a defined consequence path. It should either have a decision rule or be dropped.

6. **ALTERNATIVE [ADVISORY]:** The proposal uses retrospective proposals where the actual outcome is known, then asks judges to score which arm's review *would have* led to a better outcome. This is a counterfactual judgment, not an empirical one — judges are being asked to imagine an alternate history. A missing candidate: for the prospective arm, run both arms *before* any decision is made and have the actual decision-maker (the user) rate which arm's review was more useful *at decision time*, not retrospectively. This is a direct utility measure rather than a counterfactual one. The proposal does have a prospective arm but doesn't include this real-time utility rating — it still relies on post-hoc outcome labeling at t+1-2 weeks.

7. **ASSUMPTION [ADVISORY]:** The proposal assumes that the 10 retrospective proposals are representative of the proposal types that will be reviewed in production going forward. But the selection criteria explicitly exclude the most "atomizable" proposal type (streamline-rules) to avoid distorting count metrics. If production use skews toward governance/process proposals (which the repo manifest suggests — 21 docs files, heavy process infrastructure), the exclusion may make the sample *less* representative of actual use, not more. The proposal doesn't address this tension.

---

## Concessions

1. **The decision matrix is genuinely pre-registered and mechanical.** Specifying tie-breaking rules (CRITICAL_MISS 3x weight, prospective beats retrospective) before data collection is methodologically sound and directly addresses the prior study's post-hoc interpretation flaw.

2. **Symmetric variance measurement is a real improvement.** Requiring both arms to be rerun 2× on 3 proposals, and making INCONCLUSIVE the verdict when within-arm variance exceeds half the inter-arm gap, is the right call and was the prior study's most significant gap.

3. **The "What This Study Does NOT Answer" section is honest and well-scoped.** Explicitly deferring the persona-structure question, the cross-family-beyond-2 question, and the generalization-to-other-skills question prevents scope creep and keeps the research question answerable.

---

## Verdict

**REVISE** — Two material issues require design changes before execution: (1) the conflation of model-family diversity with model-capability diversity in arm B'-fair means a finding either way cannot be attributed to the operative variable, and (2) the arm D internal judge (GPT-5.4) is not independent of arm D's challenger outputs, creating a within-arm coherence bias that the current adjudication setup doesn't control for. Both are fixable with bounded scope changes before any API spend.

---

## Challenger E (frame-factual) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal’s “arm B'-fair” is not actually comparable to “Claude spawning personas itself” under current `debate.py challenge` behavior, because selecting `frame` with `--enable-tools` automatically expands into **two challengers** (`frame-structural` on Claude Sonnet with tools off, plus `frame-factual` on GPT-5.4 with tools on). In code, `if p == "frame" and ... args.enable_tools ... challengers.append(... model ... use_tools=False)` then adds a second challenger using `config["frame_factual_model"]` (`scripts/debate.py:1057-1066`), and production config sets `frame_factual_model` to `gpt-5.4` (`config/debate-models.json:14`). So the proposed invocation for B'-fair would silently reintroduce cross-family review unless the study also changes code or disables the frame expansion path; a config-only arm file is insufficient.

2. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The stated production arm-D config is inaccurate for the frame persona. The proposal says “frame-structural=claude-sonnet-4-6, frame-factual=gpt-5.4,” which is true, but it presents this as if both are explicit persona assignments in the config. In reality, `persona_model_map.frame` is only `claude-sonnet-4-6`; `frame-factual` is an implementation-specific expansion driven by `frame_factual_model` in config plus special logic in `debate.py` (`config/debate-models.json:2-15`, `scripts/debate.py:1057-1064`). That matters because the study design assumes arm definitions are controlled purely by config, but one arm difference is encoded in orchestration behavior, not just model mapping.

3. [ALTERNATIVE] [ADVISORY]: The proposal frames triple-judge adjudication as new study machinery, but the repo already has dedicated infrastructure for exactly this style of “structural + factual + aggregate verdict” frame review in `scripts/judge_frame_orchestrator.py` and benchmarking harness support in `scripts/review_frame_benchmark.py` (`scripts/judge_frame_orchestrator.py:1-16`, `scripts/review_frame_benchmark.py:1-10`). This doesn’t falsify the design, but it suggests the proposal may be overlooking existing adjudication/orchestration surfaces that could reduce bespoke study code.

## Concessions
- The proposal is correct that current production defaults are `architect=claude-opus-4-7`, `security=gpt-5.4`, `pm=gemini-3.1-pro`, `frame=claude-sonnet-4-6`, and `judge_default=gpt-5.4` (`config/debate-models.json:2-15`).
- It is correct that `/challenge` currently runs challengers in parallel with tool access available per challenger (`scripts/debate.py:1131-1167`).
- It is fair to say the repo has recent frame-stage work; recent commits show active additions around judge-stage/frame-reach auditing rather than a stale untouched pipeline (`get_recent_commits` on `scripts/debate.py`, `scripts/judge_frame_orchestrator.py`, `config/debate-models.json`).

## Verdict
REVISE — the core arm-B definition is factually broken against current code, so the study would not test the claimed single-model/no-cross-family condition without implementation changes beyond a new config file.

---

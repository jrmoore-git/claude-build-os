---
debate_id: judge-stage-frame-reach-audit-findings
created: 2026-04-17T17:35:35-0700
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
# judge-stage-frame-reach-audit-findings — Challenger Reviews

## Challenger A (architect) — Challenges
Structural claims verified: `cmd_judge` exists at line 1416 (matches proposal), `cmd_intake_check` shipped, frame dual-mode (structural+factual) exists in scripts, frame persona maps to `claude-sonnet-4-6` and judge default is `gpt-5.4` (model independence claim holds). `cmd_judge_with_frame` does not yet exist (correctly described as the Phase 3 deliverable).

One thing worth checking — the judge and frame persona model families relative to author:

Author is `claude-opus-4-7`, judge is `gpt-5.4`, frame is `claude-sonnet-4-6`. Frame shares Anthropic family with author — relevant to the independence story.

## Challenges

1. **ASSUMPTION [MATERIAL] [COST:SMALL]**: The audit treats dual-mode Frame as a judge-independent critic, but the frame persona is mapped to `claude-sonnet-4-6` (Anthropic) while the author is `claude-opus-4-7` (also Anthropic). EVIDENCED: `persona_model_map` shows `frame: claude-sonnet-4-6`, `author_models = {"claude-opus-4-7", "litellm/claude-opus-4-7"}` at `scripts/debate.py:1450`. The existing `cmd_judge` explicitly treats same-family as degraded independence (`degraded_single_model`). A post-judge Frame pass run with an Anthropic model critiquing an Anthropic-authored proposal re-introduces exactly the correlated-blind-spot risk the judge stage was designed to remove. Phase 0 must either (a) remap frame to a non-Anthropic model at this stage, or (b) add an independence check mirroring the one in `cmd_judge`. Without this, a "reach" measurement will conflate Frame-specific reach with within-family agreement bias. Fix is small: add a `judge_family != frame_family` precondition to Phase 0 and pin the frame model used for the audit.

2. **RISK [MATERIAL] [COST:TRIVIAL]**: The pre-committed aggregation rule ("structural-vetoes-factual-only-findings") collapses dual-mode Frame into essentially structural-only when factual stands alone, but says nothing about the inverse — factual-FP pollution of a structural-signed finding. At intake, factual-FP was the gate-breaker. Judge stage input (MATERIAL-tagged findings that already cite code) is *more* code-dense than raw proposals, so factual mode's "always finds something" failure mode likely gets worse, not better. The rule needs a second clause: a finding whose only substantive content is a factual claim unsupported by the structural pass is discarded even if structural "co-signs" a different aspect. Otherwise "co-signer" becomes a rubber stamp. TRIVIAL to add as a frontmatter-locked rule before Phase 1.

3. **UNDER-ENGINEERED [MATERIAL] [COST:SMALL]**: Phase 0c sets the factual-FP gate at >50% but Phase 0e sets `specificity_floor = 1 − measured_FP_rate − 1σ_buffer`. With n=5 known-correct outputs, the 1σ binomial buffer on a proportion is ≈ √(p(1-p)/5) — roughly ±0.22 at p=0.5. That means the specificity floor is effectively set by sampling noise, not by frame behavior. Either (a) raise the known-correct arm to n≥10 before computing the floor, or (b) pre-commit a fixed specificity floor (e.g., 0.80) independent of Phase 0 measurement, so the audit can't self-adjust its pass bar downward. The current formulation lets a high-FP-rate Phase 0 produce a permissively low floor that Phase 1 then "meets."

4. **RISK [ADVISORY]**: The corpus-escalation path in 0b ("synthesize proposals with embedded REJECT triggers") is a known distribution-shift hazard. Synthesized REJECT-triggered proposals will have different surface features than organic judge errors — embedded triggers tend to be more detectable than the drift-shaped errors that actually occur in production. If Phase 0a yields <5 baseline errors and you fall through to synthesis, the Phase 1 sensitivity measurement is measuring Frame's ability to catch synthetic tells, not real judge misses. Labeling from `stores/debate-log.jsonl` (509 entries available — EVIDENCED in proposal) should be exhausted before synthesis, and synthesis results should be reported separately from organic results rather than pooled.

5. **ALTERNATIVE [ADVISORY]**: An n=5→n=10 audit run against a judge whose error rate is unmeasured is a large investment to answer one subquestion ("does Frame catch judge errors at this stage"). The cheaper prior question — "what is the `cmd_judge` error rate, and what shape are the errors?" — is Phase 0a alone and is a prerequisite for *any* judge-side intervention, not just Frame. If Phase 0a shows baseline errors are dominated by a specific pattern (e.g., severity under-weighting of security findings), a targeted judge-prompt fix or a `cmd_judge --strict-on-security` flag may be a better instrument than a second dual-mode pass. Worth gating Phase 1 on a qualitative review of Phase 0a error shape, not just error count. The proposal implicitly assumes Frame is the right tool; Phase 0a hands you the data to check that assumption at zero extra cost.

6. **OVER-ENGINEERED [ADVISORY]**: Shipping Phase 3 as a new `cmd_judge_with_frame` subcommand risks command-surface proliferation (`debate.py` already has challenge/judge/review/refine/pressure_test/premortem/intake-check/compare/explore/outcome/stats/verdict). If ADOPT survives Phase 2, an opt-in `--post-frame` flag on `cmd_judge` keeps the primitive composable with the existing model-independence checks in one place and avoids duplicating the author/challenger/judge independence logic at lines 1450-1465. Not material to the audit itself.

## Concessions

1. Phase 0a as a 30-minute go/no-go is exactly the right shape — learning from the intake DECLINE has produced a cheaper-failure-first structure.
2. Pre-committing sensitivity/specificity floors and the aggregation rule in frontmatter before Phase 1 (rather than after seeing data) is a real methodological improvement over the intake audit.
3. The distinction drawn between intake stage (raw proposal, severity drift applies) and judge stage (MATERIAL-tagged findings, severity drift doesn't apply) is structurally correct and justifies why the intake DECLINE doesn't foreclose the judge audit.

## Verdict

**REVISE** — the audit structure is sound, but findings 1-3 are build conditions that must be resolved before Phase 0 runs: pin a non-Anthropic model for the frame-at-judge pass (or add an explicit independence check), tighten the aggregation rule to cover factual-FP-within-cosigned-findings, and either enlarge the Phase 0 known-correct arm to n≥10 or pre-commit a fixed specificity floor. All three are trivial-to-small fixes that protect the Phase 2 verdict from being driven by methodology artifacts rather than Frame reach.

---

## Challenger B (security) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal assumes archived judge/challenge artifacts are safe to resend through additional LLM calls, but `cmd_judge` reads full proposal and challenge bodies and the codebase loads credentials from `.env`/environment for external model calls (`scripts/debate.py:1423,1433`; `scripts/debate_common.py:_load_credentials`). A post-judge Frame audit increases data egress to external model providers and possibly fallback paths without stating a data-classification boundary, redaction policy, or whether archived corpus items may contain sensitive code/proposal content. This is material because the recommendation to audit/ship depends on whether the corpus is allowed to leave the repo boundary; add an explicit corpus eligibility rule and redaction step before Phase 0/1.

2. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The pre-committed aggregation rule only blocks one direction of cascading override (“structural-vetoes-factual-only-findings”), but it does not constrain prompt-injection or tool-result poisoning from the factual mode if it is allowed to inspect code and then co-sign structural conclusions. The trust boundary here is untrusted repository content/tool output → factual Frame prompt → final reject recommendation. If archived proposals or referenced files contain adversarial instructions, the factual pass could still shape the structural pass or the final adjudication unless you specify strict one-way aggregation, tool-output quoting, and “tool data is evidence, not instruction” handling. This matters because the design explicitly cites cascading factual override risk but only partially addresses it.

3. [UNDER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: There is no stated logging/sanitization plan for audit outputs even though the system already tracks debate events/costs and the proposal would create `results.md` plus likely additional logs. If per-proposal false-positive/false-negative examples include raw proposal text or challenge findings, private design details could be copied into durable artifacts or telemetry. This is a build-condition issue: require result artifacts to store IDs/labels and minimal excerpts, not full prompts or provider responses, unless the corpus is explicitly public/safe.

4. [ASSUMPTION] [ADVISORY]: The quantitative claim “509 entries in `stores/debate-log.jsonl`” is not tool-verified in this review, so treat it as SPECULATIVE unless separately measured before using it to justify corpus sufficiency or sampling convenience.

5. [ASSUMPTION] [ADVISORY]: The compute estimate “≈30–40 API calls” is ESTIMATED: assumes Phase 0 plus Phase 1 at n=10 with ~2 calls per dual-mode pass and limited reruns. Reasonable, but it should not drive approval criteria without recording actual retries/fallback invocations because `llm_client` retries transient failures and fallback can alter call counts.

## Concessions
- The proposal correctly evaluates both change risk and no-change risk, especially the silent-propagation risk from judge false PROCEED/REVISE outcomes.
- Pre-committing the aggregation rule before looking at results is a strong control against outcome-shopping.
- Making any eventual feature opt-in via a new subcommand rather than changing default `cmd_judge` materially limits blast radius.

## Verdict
REVISE with one-sentence rationale: the audit design is promising, but it needs explicit controls for data egress/redaction and stronger trust-boundary handling around factual-mode/tool-fed inputs before it is safe to run on archived judge artifacts.

---

## Challenger C (pm) — Challenges
## Challenges
1. [OVER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: Proposing a complex 4-phase audit (Phases 0b through 3) before establishing if the baseline judge actually fails is premature optimization. The proposal admits the current `cmd_judge` error rate is entirely unmeasured [EVIDENCED]. If the 30-minute Phase 0a test yields 0 missed disqualifiers, the design and planning effort for the rest of the audit is wasted. The immediate scope should be constrained strictly to Phase 0a to prove the problem exists before approving the heavy evaluation machinery to solve it.
2. [RISK] [MATERIAL] [COST:SMALL]: The pre-committed aggregation rule ("structural-vetoes-factual-only-findings" in Phase 0d) logically neuters the factual mode. If factual findings cannot independently trigger a REJECT and always require a structural co-signer, you are paying a ~10-20s latency penalty [ESTIMATED] and extra token costs for a mode that has zero independent gating authority. If factual mode is so noisy that it cannot be trusted to veto on its own, it should be excluded from the judge-stage experiment entirely rather than running it just to ignore its solo findings.
3. [ASSUMPTION] [ADVISORY]: Setting rigid sensitivity and specificity floors (Phase 0e) based on a calibration sample of n=5 [EVIDENCED] is highly vulnerable to statistical noise. A single anomalous proposal in that small batch will radically skew the mathematical gating criteria for Phase 2, making the final ADOPT/DECLINE decision brittle.

## Concessions
1. Explicitly defining a 30-minute Phase 0a kill-switch is a great defensive practice to prevent wasting hours of compute and analysis if the baseline problem doesn't exist.
2. Properly internalizes the negative lessons from the intake-stage failure by actively designing a structural test (Phase 0c) for the known factual-FP vulnerability.
3. Keeping the proposed integration strictly opt-in via a new subcommand (`cmd_judge_with_frame`) safely isolates experimental risk from the mainline `/challenge` operation.

## Verdict
REVISE to constrain the immediate scope to just Phase 0a, proving that the baseline judge actually misses disqualifiers before authorizing the full multi-phase audit design.

---

## Challenger D (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL] [COST:SMALL]:** The proposal assumes the judge stage has "structurally different input properties" that make severity drift inapplicable — but this is asserted, not demonstrated. The intake audit's severity drift failure occurred because Frame-factual raised MATERIAL findings on any code-citing content. Judge outputs (`tasks/<topic>-judgment.md`) almost certainly cite code paths, hook names, and script references when adjudicating findings. The structural difference claimed (MATERIAL-tagged findings vs. raw proposal) doesn't eliminate the factual-FP problem; it may just relocate it. Phase 0c tests this, but the proposal treats the structural difference as load-bearing justification for running the audit at all, before that test confirms it.

2. **ASSUMPTION [MATERIAL] [COST:MEDIUM]:** The corpus sufficiency gate (Phase 0b) assumes that if n=5 archived outputs yield <5 baseline errors, the corpus can be extended by labeling from `stores/debate-log.jsonl` or synthesizing proposals with embedded REJECT triggers. Synthesized proposals are not the same distribution as real proposals — a Frame pass that catches synthetic REJECT triggers may not generalize to organic judge errors. The proposal doesn't distinguish between "corpus extended via real labeled data" and "corpus extended via synthetic data," treating them as equivalent fallbacks. If the real corpus is insufficient (likely, given judge is "less frequently invoked standalone"), the audit may proceed on a synthetic corpus that proves nothing about production behavior.

3. **ALTERNATIVE [MATERIAL] [COST:SMALL]:** A missing candidate is **passive corpus accumulation before auditing**. Given that judge is invoked less frequently than challenge (1 judge entry vs. 8 challenge entries in the last 10 log entries), the natural corpus growth rate may produce a sufficient real-labeled corpus within 2-4 weeks without any synthesis. The proposal doesn't consider "wait for corpus" as an option, defaulting instead to synthesis when real data is sparse. This is a timing question, not a technical one, and the proposal doesn't justify urgency that would rule out waiting.

4. **ALTERNATIVE [ADVISORY] [COST:TRIVIAL]:** The proposal's "simplest version" (Phase 0a alone, 30 minutes) is identified but then immediately embedded inside a 4-phase structure. A missing candidate is **Phase 0a as a standalone decision gate with an explicit stop condition**: run Phase 0a, publish the baseline error count, and only commission the full audit design if errors ≥5. The current structure nominally includes this (Phase 0b escalation), but the full audit design — including aggregation rule lock-in (Phase 0d), pre-committed floors (Phase 0e), and the `cmd_judge_with_frame` subcommand design — is already written before Phase 0a runs. This is pre-building the abstraction layer before confirming the premise.

5. **OVER-ENGINEERED [ADVISORY] [COST:SMALL]:** The aggregation rule "structural-vetoes-factual-only-findings" is locked in Phase 0d as immutable before the main audit runs. This is a reasonable safeguard, but locking it as immutable before seeing the factual-FP distribution (measured in Phase 0c) means the rule can't be tuned if Phase 0c reveals a different FP profile than expected. A factual-FP rate of 20% might warrant a different aggregation rule than a rate of 45%. Pre-committing the rule before measuring the distribution it's designed to handle is backwards.

6. **ASSUMPTION [ADVISORY]:** The proposal states "judge errors ship silently" and "a false PROCEED/REVISE verdict would send the proposal to /plan with no further gate." This is presented as a current system failure, but the proposal also notes "we have no incident log of this happening." The severity framing ("shipped bad work would go undetected") is speculative — SPECULATIVE, no data — and the proposal acknowledges selection bias. The problem statement is sound in principle but the urgency framing slightly inflates a theoretical risk into a demonstrated failure mode.

---

## Concessions

1. **Phase 0 blocking gates are well-structured.** The proposal correctly identifies that the intake audit's failure modes (severity drift, factual-FP) need to be tested before committing to the main audit, and it operationalizes those tests as explicit go/no-go gates rather than assumptions.

2. **The aggregation rule addresses the cascading factual override risk.** The pm-persona cross-check finding (cascading factual override) is directly addressed by the structural-vetoes-factual-only rule. The proposal shows genuine learning from prior audit failures rather than repeating them.

3. **Non-goals are correctly scoped.** Deferring refine-stage and premortem-stage audits, keeping `cmd_judge` default unchanged, and explicitly declining to re-test intake with looser thresholds are all appropriate scope constraints that prevent scope creep.

---

## Verdict

**REVISE** — The candidate set is missing one material option (passive corpus accumulation vs. synthesis), and the proposal's most load-bearing assumption (that judge-stage inputs are structurally immune to the factual-FP failure mode that killed the intake audit) is asserted rather than tested before the full audit machinery is designed. The aggregation rule lock-in before Phase 0c data is also backwards. These are fixable with a clearer decision tree: Phase 0a → stop if <5 errors; Phase 0c → stop if FP >50% *and* revise aggregation rule if FP is in the 20-45% range; only then lock the rule and proceed. The core audit structure is sound; the sequencing and corpus-sourcing assumptions need tightening.

---

## Challenger E (frame-factual) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST: SMALL]: The proposal says “`cmd_judge` independence checks already in place: … Model diversity is operationally enforced,” but the code only emits warnings and continues. In `scripts/debate.py:1451-1471`, author/judge overlap and challenger/judge overlap both print `WARNING:` messages; there is no block or enforcement path. This matters because the audit framing treats judge independence as a guardrail already assured by the system when it is only advisory.

2. [ASSUMPTION] [MATERIAL] [COST: TRIVIAL]: The proposal claims dual-mode Frame uses “two different model families run in parallel.” That is true for the shipped `/challenge` path, but the proposed Phase 0d aggregation rule (“structural-vetoes-factual-only-findings”) assumes the two halves are independently available at judge stage. There is no `cmd_judge_with_frame` or judge-stage Frame integration today; `scripts/debate.py` exposes `cmd_intake_check` as a wrapper for challenge-stage Frame (`scripts/debate.py:1402-1413`), but `cmd_judge` has no analogous hook or post-judge dual-mode pass in the inspected implementation around `cmd_judge` (`scripts/debate.py:1416+`). The proposal should present Phase 0/1 as research requiring new orchestration, not as a near-existing path.

3. [ASSUMPTION] [ADVISORY]: The proposal cites “509 entries in `stores/debate-log.jsonl` as of 2026-04-17” and bases operational context on that count, but no repo tool here can verify `stores/` contents, and the only code we can inspect (`scripts/debate_stats.py`) shows the log is append-only and multi-phase (`phase` aggregation at `scripts/debate_stats.py:33-49`), not necessarily one-entry-per-debate. Treat the 509 figure as **SPECULATIVE** unless backed by a checked artifact outside this review. It should not drive corpus-size or frequency claims by itself.

4. [UNDER-ENGINEERED] [ADVISORY]: The proposed specificity floor formula is statistically thin for the stated sample size. The proposal explicitly says Phase 1 can run at “n≥10, at least 5 known-error + 5 known-correct,” while Phase 0c estimates factual FP from only 5 known-correct outputs. With that denominator, “specificity_floor = 1 − measured_FP_rate − 1σ_buffer” is highly unstable. This does not contradict code, but it does make the pass/fail gate brittle relative to the claimed rigor.

## Concessions
- The proposal is accurate that `cmd_judge` exists at `scripts/debate.py:1416` and does perform overlap checks against author and challenger models.
- It is accurate that dual-mode Frame shipped for `/challenge`; `config/debate-models.json:13-16` documents `frame_factual_model` and the notes describe structural Claude + factual GPT cross-family operation.
- It is accurate that `intake-check` shipped as a composable primitive rather than a default gate; `scripts/debate.py:1402-1413` is exactly that wrapper.

## Verdict
REVISE — the core audit idea is plausible, but it overstates current judge-stage enforcement/integration and should tighten its claims about what already exists versus what must be built.

---

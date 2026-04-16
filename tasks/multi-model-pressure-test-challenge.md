---
debate_id: multi-model-pressure-test
created: 2026-04-15T20:45:04-0700
mapping:
  A: claude-opus-4-6
  B: gemini-3.1-pro
  C: gpt-5.4
---
# multi-model-pressure-test — Challenger Reviews

## Challenger A — Challenges
## Challenges

1. **ASSUMPTION** [MATERIAL] [COST:SMALL]: The brief states "synthesis model defaults to config `judge_default` (gpt-5.4) — different family from typical pressure-test models" but doesn't enforce the cross-family constraint. If a user passes `--models gpt-5.4,gpt-5.4-mini`, the synthesis model (also gpt-5.4) is from the same family, defeating the reasoning independence goal. There should be a validation check or at least a warning when the synthesis model shares a family with any input model. Without this, the core thesis of the change — cross-family diversity — is silently violated in common configurations.

2. **RISK** [MATERIAL] [COST:SMALL]: The synthesis prompt design is load-bearing for the entire feature's value proposition. "Where do the analyses DISAGREE?" is mentioned as mitigation but not specified as a concrete artifact. If the synthesis prompt is weak, multi-model mode degrades to expensive concatenation. The brief should include the synthesis system prompt (or at least its structure) as a deliverable, not leave it implicit. This is a small cost to fix — it's one prompt — but it's the difference between the feature working and not working.

3. **RISK** [ADVISORY]: Mutual exclusivity of `--model` and `--models` is clean, but what happens when neither is specified? The brief doesn't state whether multi-model mode can be set as a default via config (e.g., `pressure_test_models` in project config). If the feature proves valuable, users will want it as default without typing `--models` every time. Not blocking, but worth noting for the config story.

4. **OVER-ENGINEERED** [ADVISORY]: Position-randomized anonymous labeling (Zheng et al.) is principled for the review panel where a judge scores competing outputs. In pressure-test synthesis, the synthesis model isn't ranking the analyses — it's reconciling them. Anonymization still has mild value (prevents name-brand bias in synthesis), but position randomization is less critical here than in head-to-head evaluation. Not worth removing, but don't let it drive complexity.

5. **ASSUMPTION** [ADVISORY]: "The pressure-test system prompt works across model families without modification." This is plausible for the adversarial critique format but worth a quick manual check. Claude-family models and Gemini-family models sometimes interpret structured output instructions differently. A single test run across target families before shipping would validate this cheaply.

6. **RISK** [ADVISORY]: 3x cost claim is ESTIMATED (assumes 3 models). Actual cost depends on user configuration. For the stated use case (pre-plan gate, infrequent), this is fine. But if someone wires this into a CI loop, costs scale. The brief correctly scopes this as infrequent — just ensure the documentation reinforces that framing.

## Concessions

1. **Reusing the ThreadPoolExecutor pattern from 4 existing sites** is the right call — proven infrastructure, no new concurrency abstractions, minimal risk of novel bugs.
2. **Keeping single-model `--model` behavior completely unchanged** is clean backward compatibility. No migration, no breakage, no flag day.
3. **Scoping out multi-model premortem** is disciplined. Ship the simpler, higher-value case first and let evidence drive expansion.

## Verdict

**APPROVE** with two small build conditions: (1) add cross-family validation/warning for synthesis model vs. input models, and (2) include the synthesis prompt as an explicit deliverable rather than leaving it to implementation-time improvisation. Both are SMALL cost and directly protect the feature's core value proposition.

---

## Challenger B — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: Exception handling in parallel execution. While D18 provides fallback, if a model completely fails or times out after all fallbacks, it will likely raise an exception. If `ThreadPoolExecutor.map` or `.result()` is used without catching exceptions per thread, one model's failure will crash the entire pressure test. You must wrap the thread execution to return an error string (e.g., "Model X failed to return a response") instead of throwing, allowing the synthesis step to proceed with partial data.
2. [ASSUMPTION] [ADVISORY]: The proposal states the synthesis model (`judge_default`, gpt-5.4) will be from a "different family than typical pressure-test models." If a user specifies `--models gpt-5.4 claude-3-opus`, the synthesis model will overlap with an input model, violating the cross-family synthesis premise. This is operationally fine, but breaks the theoretical assumption of the feature.
3. [OVER-ENGINEERED] [ADVISORY]: Maintaining both `--model` and `--models` as mutually exclusive flags creates unnecessary CLI parsing logic. Consider just making `--model` accept a list of strings (e.g., `nargs='+'`). If length is 1, bypass synthesis. If length > 1, trigger the multi-model flow. 

## Concessions
1. Reusing the proven `ThreadPoolExecutor` and position-randomization patterns from the review panel drastically reduces implementation risk and net-new code.
2. The operational cost increase [ESTIMATED: 3x cost based on 3 input models] is properly contextualized and accepted given the infrequent execution of the command.
3. Rollback path is excellent: if the multi-model synthesis fails or performs poorly, users can simply revert to passing the single `--model` flag.

## Verdict
APPROVE because the design heavily leverages proven existing patterns, and the minor missing exception-handling logic can be easily addressed during implementation.

---

## Challenger C — Challenges
## Challenges
1. [ASSUMPTION] [ADVISORY]: “Reasoning independence” is asserted but not verified for the actual model set you expect users to pass via `--models`. If users choose closely related variants, the proposal may add cost without meaningful diversity. This doesn’t block the experiment, but the A/B test should measure disagreement quality, not just number of findings.

2. [UNDER-ENGINEERED] [ADVISORY]: The proposal says the synthesis model should be from a different family than any input models, but the only concrete mechanism described is a default to `judge_default` (`gpt-5.4`). That works only if the selected inputs are indeed from other families; if a user includes the same family in `--models`, the stated property may silently fail. Since this is a speed-focused experiment, this is acceptable if documented, but the implementation should not claim guaranteed cross-family synthesis unless it actually checks.

3. [ASSUMPTION] [ADVISORY]: “ThreadPoolExecutor parallel pattern is proven” is supported only by reuse elsewhere, not by evidence that pressure-test calls have the same latency, timeout, or rate-limit behavior. Reusing the pattern is reasonable, but success in other commands is not proof that this specific path will behave well under concurrent multi-model API calls.

4. [ASSUMPTION] [ADVISORY]: Quantitative claim — “3x cost for multi-model runs” is **ESTIMATED**: assumes a typical 3-model run plus 1 synthesis call offset by pressure-test’s current single-model baseline; exact multiplier depends on number of selected models, token lengths of returned analyses, and synthesis prompt size. This is directionally plausible but should not be treated as precise.

5. [ALTERNATIVE] [ADVISORY]: For the experiment’s goal, you may want to preserve raw per-model outputs in a machine-readable structure in addition to the synthesized text. Without that, evaluating whether multi-model actually improved adversarial critique quality versus single-model may be harder, because synthesis can hide disagreement rather than expose it.

## Concessions
- Reusing an existing parallel execution pattern lowers implementation risk and is a sensible fast path.
- Mutual exclusivity between `--model` and `--models`, plus requiring at least 2 models, keeps the CLI behavior understandable.
- Anonymization and position randomization are good choices for reducing synthesis bias and are aligned with the stated objective.

## Verdict
APPROVE — the proposal is a reasonable, testable experiment, and the main gaps are evidence/validation details rather than flaws that should block implementation.

---

---
debate_id: evaluation-routing-findings
created: 2026-04-11T20:52:14-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# evaluation-routing-findings — Challenger Reviews

## Challenger A — Challenges
Now I have all the data I need. Let me compile the review.

## Challenges

1. **ASSUMPTION [ADVISORY]**: The proposal states "Personas only route to models — they don't inject PERSONA_PROMPTS in review-panel (only in `challenge`)." I verified this is correct — `cmd_review_panel` at line 2790 uses only the `--prompt`/`--prompt-file` as the system prompt (line 2863: `system=prompt + TOOL_INJECTION_DEFENSE`), and `PERSONA_PROMPTS` has only 1 match in the codebase, not in the review-panel path. This validates the core premise: personas in review-panel are *already* just model selectors with misleading names. The proposal correctly identifies this.

2. **UNDER-ENGINEERED [MATERIAL]**: The `_run_reviewer` inner function (line 2854) takes `persona` as its parameter and uses it as a key into `pmap` (line 2855: `model = pmap[persona]`), as a label in stderr output (line 2856), in the return tuple (line 2892), and in the audit log (lines 2931, 2941-2948). When `--models` is used, there is no persona string. The proposal doesn't specify what replaces the persona in these four roles. The simplest approach (use the model name as the persona key) works for model lookup and stderr, but changes the audit log schema — `"personas"` would contain model strings instead of persona names. Downstream consumers of the audit log (the `stats` command at line 3647, any external tooling) may break or produce confusing output. The implementation needs to either: (a) use synthetic labels like "model-1", "model-2", "model-3" as the persona key, or (b) explicitly document that the `personas` field in the log will contain model names when `--models` is used. This is a small design decision but it needs to be made explicitly.

3. **RISK [ADVISORY]**: The `--personas` arg is currently `required=True` (line 3515). Making it mutually exclusive with `--models` means neither can be individually `required`. Argparse's `mutually_exclusive_group` doesn't support `required` on individual members, but the group itself can be `required=True`. This is a known argparse pattern but easy to get wrong — if implemented as two optional args with manual validation, the error messages will be worse than using `add_mutually_exclusive_group(required=True)`.

4. **ALTERNATIVE [ADVISORY]**: Instead of `--models`, consider `--personas` accepting model names directly when they don't match any key in `persona_model_map`. This would be a single-arg approach: if the value is a known persona, look it up; if it looks like a model string (contains `/` or `-` with digits), pass it through. This avoids the mutual-exclusion complexity entirely. However, this is arguably more magical and less explicit than the proposal's approach. The proposal's two-flag design is cleaner for documentation and error messages.

5. **RISK [ADVISORY]**: The proposal mentions updating "D15" skill content-type routing, but `D15` doesn't appear in the skills files (verified: 0 matches). Either this is a planned skill that doesn't exist yet, or the identifier is wrong. This doesn't block the `--models` implementation but the second half of the proposal (moving routing logic into the skill) can't be evaluated against existing code.

## Concessions

1. **The problem diagnosis is precise and verified.** Personas in `review-panel` are pure model selectors — no persona-specific prompts are injected. The naming creates a false affordance that causes the caller to think in code-review terms. This is a real UX/cognitive bug, not a hypothetical one.

2. **The layering decision is correct.** Content-type awareness belongs in the skill (the caller), not in `debate.py`. The script should be a dumb multi-model dispatcher. Adding document-type personas to the config would be the wrong abstraction — it conflates "which model" with "what framing."

3. **The scope is appropriately minimal.** One new arg, mutual exclusion with the existing arg, skip the persona lookup. The non-goals are well-chosen — not adding content detection to debate.py, not changing challenge personas, not creating document-type personas.

## Verdict

**APPROVE** — The proposal correctly identifies that personas in review-panel are already just model aliases, and adding `--models` as a direct bypass is the minimal correct fix. The one material gap (audit log schema when using `--models` instead of persona names) needs a design decision during implementation but doesn't change the approach.

---

## Challenger B — Challenges
## Challenges
1. [UNDER-ENGINEERED] [ADVISORY]: The proposal says `--models` should be “mutually exclusive with `--personas`,” but the current CLI defines `review-panel --personas` as required and has no mutual-exclusion group yet, so this is not just a small flag add; it requires parser and handler changes together or the UX will be broken/inconsistent. EVIDENCED: `review-panel` currently has `rp.add_argument("--personas", required=True, ...)` at `scripts/debate.py:3513-3516`, and `cmd_review_panel` unconditionally parses `args.personas` at `scripts/debate.py:2803-2806`.

2. [UNDER-ENGINEERED] [ADVISORY]: Logging/output semantics need an explicit decision for model-direct mode. Today the audit log records `"personas": personas` plus an anonymized label→model `"mapping"`. If `--models` is added without adjusting log schema, downstream tooling may see missing or misleading persona data. This won’t block the change, but it should be specified. EVIDENCED: `cmd_review_panel` currently logs `"phase": "review-panel", "personas": personas, "mapping": mapping` at `scripts/debate.py:2929-2936`.

3. [UNDER-ENGINEERED] [ADVISORY]: There is no existing test coverage for `scripts/debate.py`, so even a simple routing/arg-parsing change has elevated regression risk. Given the move-fast posture this is still advisory, but the proposal should at least include one parser/behavior smoke test for the new exclusivity rule. EVIDENCED: `check_test_coverage` reports `has_test: false` for `scripts/debate.py`.

## Concessions
- The core premise is supported by the code: `review-panel` passes the caller’s prompt directly as system prompt and does not inject persona-specific framing in the non-tool path. EVIDENCED: `_call_litellm(model, prompt, input_text, ...)` at `scripts/debate.py:2888-2890`.
- The proposal chooses the right layer for content routing: the skill can decide code vs non-code before invoking `review-panel`, avoiding unnecessary complexity inside `debate.py`.
- Adding direct model selection is consistent with existing patterns elsewhere in the CLI, since `challenge` and `refine` already support `--models`. EVIDENCED: `challenge --models` at `scripts/debate.py:3435-3439`; `refine --models` at `scripts/debate.py:3486-3487`.

## Verdict
APPROVE — the change is small, evidence-backed, and likely to reduce a real recurring workflow failure with minimal implementation risk.

---

## Challenger C — Challenges
## Challenges
None. The proposal is tightly scoped, directly addresses a verified behavioral failure (lesson violation under pressure), and smartly avoids the trap of building more persona infrastructure. 

## Concessions
1. **Right-sizing**: Correctly identifies that adding new "document reviewer" persona types is over-engineering when the `--prompt` already acts as the evaluation framing.
2. **Structural Fix**: Moving the routing logic into the `/review` skill removes the cognitive burden from the user/agent and replaces a failed behavioral instruction (L21) with a systemic guardrail.
3. **Accurate Diagnosis**: Accurately traces the root cause of the evaluation mismatch to `review-panel`'s forced reliance on code-review aliases.

## Verdict
APPROVE. The change is minimal, structurally prevents a recurring failure mode, and properly delegates model-selection routing to the skill layer.

---

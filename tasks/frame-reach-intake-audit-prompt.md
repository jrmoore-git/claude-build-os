---
topic: frame-reach-intake-audit
created: 2026-04-17
related_plan: tasks/frame-reach-intake-audit-plan.md
---

# Intake Prompt Spec

## Prompt design decision: reuse Frame prompts verbatim

The intake-check subcommand calls the existing Frame persona dual-mode expansion path — same `frame-structural` + `frame-factual` prompts used inside `/challenge` today. No adaptation. Evidence for the decision:

1. **The question is the same at both stages.** Frame asks: is this proposal's candidate set right? Are problem framings right? Are cited claims stale? Those questions don't change based on pipeline position.
2. **The prompts are stage-agnostic.** Frame prompts (`PERSONA_PROMPTS["frame"]` + `PERSONA_PROMPTS["frame-factual"]`) reason from the proposal text alone (structural) or verify claims against the codebase (factual). Neither requires knowledge of "what stage of the pipeline this is running at."
3. **Clean comparison to Round 2.** Since Round 2 used the same prompts, intake findings can be compared directly to Round 2 findings without confounding variables. If intake catches the same frame errors Round 2 caught, the ONLY axis of variation is stage — not prompt.
4. **Adaptation is a scope expansion.** Adapting the prompts for "pre-challenge" context (e.g., adding "you are running before downstream personas") would be a change to intake AND Frame (since they'd use different prompts). Scope creep. Defer.

If Phase 0 smoke test shows the verbatim reuse doesn't work (e.g., output format breaks because the prompts expect challenge context somewhere), the first remediation is minimal adaptation — NOT rewriting the prompts.

## Implementation mechanic

`cmd_intake_check` is a thin wrapper over `cmd_challenge`:
- Forces `args.personas = "frame"`
- Forces `args.enable_tools = True`
- Forces `args.system_prompt = None`
- Delegates to `cmd_challenge(args)`

Net code size: ~15 LOC plus argparse subparser (~10 LOC) plus main dispatch (~2 LOC). Same persona-expansion path at `debate.py:995` handles the dual-mode split into frame-structural + frame-factual.

## Negative-control proposal choice

**Selected:** `tasks/negative-control-verbose-flag-proposal.md` — synthetic minimal proposal written specifically for this audit.

**Rationale:**
- Most existing tasks/*-proposal.md files carry REVISE verdicts from Round 2, so are unsuitable as clean controls.
- A purpose-written minimal proposal has unambiguously clean framing: one candidate, explicit evidence, narrow scope, clear rollback.
- If Frame raises MATERIAL frame findings on it, the prompts or model are the problem — the audit's FP gate is the right place to catch that.

**Proposal content (summary):** adds a `--verbose` CLI flag to `debate.py` that prints LLM response text and tool-call trace to stderr. Clear problem, well-scoped solution, cited evidence (recent debugging git log), explicit rollback. No binary framing, no source-driven candidates, no problem inflation.

## Expected outputs (per plan)

- Intake runs: `tasks/frame-reach-intake-audit-runs/{proposal}-intake.md` (one file per proposal, dual-mode output in single file)
  - 5 audit proposals: autobuild, explore-intake, learning-velocity, streamline-rules, litellm-fallback
  - 1 negative control: negative-control-verbose-flag
  - Total: 6 files, 12 API calls

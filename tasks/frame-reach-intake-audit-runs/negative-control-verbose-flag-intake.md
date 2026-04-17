---
debate_id: negative-control-verbose-flag-intake
created: 2026-04-17T16:17:27-0700
mapping:
  A: claude-sonnet-4-6
  B: gpt-5.4
personas:
  A: frame-structural
  B: frame-factual
---
# negative-control-verbose-flag-intake — Challenger Reviews

## Challenger A (frame-structural) — Challenges
## Challenges

1. ASSUMPTION [ADVISORY]: The proposal assumes `debate.py` owns the LLM call path end-to-end, but the manifest shows `scripts/llm_client.py` exports `llm_call`, `llm_call_json`, `llm_call_raw`, and `llm_tool_loop` — the actual LLM invocation and tool-call dispatch almost certainly lives there, not in `debate.py`'s `_call_llm`. Threading `args.verbose` through `debate.py` alone may not reach the tool-call trace or token counts without also touching `llm_client.py` or `debate_tools.py`. The "no changes to other modules" constraint in scope may be self-defeating. [COST: SMALL]

2. ALTERNATIVE [ADVISORY]: `llm_client.py` already exists as the centralized LLM dispatch layer. A `DEBUG_LLM=1` environment variable (or a `verbose` parameter on `llm_call`) placed there would instrument *all* callers (`debate.py`, `managed_agent.py`, `research.py`, etc.) with one change, rather than wiring a flag through one script's argument parser. This is not necessarily better — the proposal's scope is intentionally narrow — but the candidate set doesn't acknowledge this option, and it would be cheaper to implement and more broadly useful.

3. ASSUMPTION [ADVISORY]: The proposal scopes to ~20 LOC and "one file," but `debate.py` has at least a dozen exported functions (`cmd_challenge`, `cmd_judge`, `cmd_refine`, `cmd_review`, `cmd_pressure_test`, `cmd_premortem`, `_run_claim_verifier`, `_consolidate_challenges`, etc.). Threading a `verbose` flag through all call sites that invoke `_call_llm` and tool calls may require more plumbing than 20 LOC suggests, especially if `verbose` needs to reach nested helpers. This is a scope estimate risk, not a design flaw. [COST: TRIVIAL to SMALL]

4. OVER-ENGINEERED [ADVISORY]: The proposal includes "Running token counts" as a verbose output item. Token counting typically requires either a tokenizer library or an API response field — it's not free. If this requires a new dependency or non-trivial extraction logic, it inflates scope beyond the stated ~20 LOC. The prompt/response printing and tool-call trace are the high-value items; token counts are separable and could be deferred. [COST: TRIVIAL if already in API response, SMALL if requires tokenizer]

## Concessions

1. The problem is real and well-evidenced: 4 commits in one month adding/removing debug prints is a concrete, low-noise signal that the workaround is recurring. The severity framing is accurate, not inflated.
2. Default-off flag is the right design choice — zero regression risk for existing callers, tests, and CI workflows.
3. The rollback story is genuinely trivial, which is appropriate for a purely additive change.

## Verdict

APPROVE — the frame is sound. The problem is real, the solution is proportionate, and the candidate set (add a flag vs. keep editing) is the right level of granularity for this scope. The one material-adjacent concern (whether `debate.py` actually owns the call path or delegates to `llm_client.py`) is worth a quick code read before writing the implementation, but it doesn't change the recommendation — it only affects which file(s) get the conditional prints.

---

## Challenger B (frame-factual) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal’s implementation sketch is stale/wrong about where to add logging. `scripts/debate.py` does have `_run_challenger` (lines 1062+), but there is no `_call_llm` function in that file anymore (`check_code_presence("_call_llm", "scripts") -> exists=false`). Non-tool model calls now flow through `_call_with_model_fallback(...)` from `cmd_challenge` (lines 1136-1139), while tool-enabled calls go through `llm_tool_loop(...)` with an `on_tool_call` callback (lines 1083-1097). So “thread `args.verbose` through to `_run_challenger` and `_call_llm`” is not implementable as written; the real surface spans both `_call_with_model_fallback` and tool-loop integration.

2. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposed “no changes to `debate_common.py`, `debate_tools.py`, or other modules” misses that `scripts/llm_client.py` already captures richer tool-loop data than `debate.py` keeps. `llm_tool_loop` returns full `tool_calls` records including `name`, parsed `args`, `result`, and aggregated `usage` token counts (llm_client.py lines 725, 799-802, 841-845), but `debate.py` currently discards that detail and only appends `{"turn": turn, "tool": name}` via `on_tool_call` (lines 1095-1097, 1123-1125). If the goal is to print tool name + arguments + return value + running token counts, the simplest accurate implementation likely needs to consume `tool_result["tool_calls"]` and `tool_result["usage"]` or add hooks in `llm_client.py`; restricting scope to `debate.py` alone underestimates the work and may yield incomplete verbose output.

3. [ASSUMPTION] [ADVISORY]: The proposal’s motivation cites a current workaround of editing `_run_challenger` and `_call_llm`, plus “4 commits adding/removing temporary debug prints.” I could not verify that history from recent `scripts/debate.py` commits: the last 8 commits touching the file are refactors/model updates, not obvious debug-print churn (`get_recent_commits(["scripts/debate.py"])`). This doesn’t prove the anecdote is false, but as stated it is unverified and should not be treated as evidenced justification.

4. [UNDER-ENGINEERED] [ADVISORY]: “Near-zero risk” is overstated because the verbose payload proposed includes full responses and tool return values, which can be large and may expose proposal contents or repo snippets on stderr. Current behavior is intentionally high-level (`Calling {label}...`, elapsed seconds, tool-call counts at lines 1070 and 1142-1144). A shipped `--verbose` flag is still reasonable, but the proposal should acknowledge output-volume/sensitivity tradeoffs and probably cap/truncate fields consistently.

## Concessions
- The repo already emits only coarse progress for challengers today: `Calling ...`, fallback notices, elapsed time, and tool-call counts in `scripts/debate.py` lines 1070 and 1142-1144.
- A default-off CLI flag is a sensible compatibility shape; I found no existing `--verbose` parser flag in `scripts/debate.py`’s CLI setup.
- The codebase already has test coverage around `scripts/debate.py`, so adding a flag and assertions is feasible without new infrastructure (`check_test_coverage("scripts/debate.py")` shows multiple tests).

## Verdict
REVISE — the feature idea is sound, but the proposal misstates the current call structure and under-scopes the implementation needed to expose full tool traces and token usage correctly.

---

# Proposal: Add `--verbose` flag to `scripts/debate.py`

## Problem

`debate.py` prints only high-level progress to stderr (model name, latency, tool call count). When a debate run produces unexpected output — empty response, off-format findings, premature termination — developers need the intermediate LLM response text and tool-call trace to diagnose. The current workaround is editing `_run_challenger` and `_call_llm` in `debate.py` to add temporary `print()` statements, then reverting the edits after debugging. Three developers on the team have done this in the last month (git log shows 4 commits adding/removing temporary debug prints to these functions).

## Proposed Change

Add a `--verbose` CLI flag that, when set, prints to stderr:
- Each LLM call's full prompt (first 500 chars) and full response
- Each tool call's name + arguments + return value
- Running token counts

When `--verbose` is not set, existing behavior is unchanged. Default is off.

## Scope

- `scripts/debate.py`: add argparse flag on top-level parser; thread `args.verbose` through to `_run_challenger` and `_call_llm`; add conditional print statements guarded by `args.verbose`.
- No changes to `debate_common.py`, `debate_tools.py`, or other modules.
- No new dependencies, no config changes.
- ~20 LOC.

## Rollback

Revert the commit. Default-off flag means zero behavior change for non-verbose invocations; existing tests and workflows unaffected.

## Why This Is Worth Shipping

Each debug session currently costs ~5-10 minutes of edit/revert churn. A persistent flag removes that cost. The flag is purely additive (no behavior change unless invoked) so the risk of regression is near-zero.

## Effort

Small: one file, one new arg, conditional prints. Reviewable in one sitting.

---
debate_id: negative-control-refined-new
created: 2026-04-18T09:43:46-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# negative-control-refined-new — Refined Document

## Round 1 (gemini-3.1-pro)
This is a strong, tightly scoped proposal. The problem statement is particularly effective because it cites specific evidence (4 commits in a month) and quantifies the cost (5-10 minutes per debug session). 

The primary area for improvement is an architectural assumption in the proposed implementation. Threading a boolean `args.verbose` flag through multiple function signatures (`_run_challenger`, `_call_llm`) is a known anti-pattern in Python. Using Python's built-in `logging` module allows you to set the log level once at the top level and emit debug statements anywhere without changing function signatures. I have flagged this in the Frame Check for downstream reviewers to consider, but left the document's proposed scope intact per refinement rules.

### Frame Check
- [Unstated load-bearing assumption]: Assumes threading a boolean `args.verbose` flag through function signatures is the optimal implementation — using Python's built-in `logging` module (setting level to `DEBUG` when `--verbose` is passed) would achieve the same result without polluting function signatures across the call stack.

## Round 2 (gpt-5.4)
The proposal is already concise and well-scoped. I made the document more executable by tightening the implementation details, clarifying what should and should not be logged, and making the success case more concrete without changing the core recommendation.

Key improvements:
- Preserved the document’s narrow scope and additive nature.
- Tightened the proposed behavior so “verbose” output is clearly diagnostic stderr output only.
- Clarified that truncation applies to prompts but not responses, matching the original intent.
- Added a minimal implementation outline so the change is straightforward to review and land.
- Kept rollback simple and preserved the low-risk framing.

Remaining issue addressed:
- The original proposal’s “running token counts” item was slightly underspecified. The revision makes it clear this means per-call and cumulative counts if those values are already available in `debate.py`; otherwise the flag should print whatever token accounting the script currently exposes rather than inventing new estimation logic.

### Frame Check
Frame check: document's frame is sound.

## Final Refined Document

# Proposal: Add `--verbose` flag to `scripts/debate.py`

## Problem

`debate.py` currently prints only high-level progress to stderr, such as model name, latency, and tool-call count. When a debate run produces unexpected output — for example, an empty response, off-format findings, or premature termination — developers cannot see the intermediate LLM response text or tool-call trace needed to diagnose the failure.

The current workaround is to manually edit `_run_challenger` and `_call_llm` in `debate.py` to inject temporary `print()` statements, then revert those edits after debugging. This is a recurring friction point: git log shows 4 commits in the last month where team members accidentally committed and then removed temporary debug prints in these functions. EVIDENCED: proposal text cites 4 commits in the last month.

## Proposed Change

Add a `--verbose` CLI flag to `scripts/debate.py`. When the flag is set, print diagnostic data to stderr for the current run:

- Each LLM call’s prompt, truncated to the first 500 characters.
- Each LLM call’s full response text.
- Each tool call’s name, arguments, and return value.
- Token accounting visible during the run: per-call and cumulative counts if `debate.py` already has those values available; otherwise print the token counts the script currently exposes rather than introducing new estimation logic.

When `--verbose` is not passed, existing output behavior remains unchanged. The default state is off.

## Scope

- **`scripts/debate.py`**
  - Add a `--verbose` flag to the top-level `argparse` parser.
  - Thread `args.verbose` through to `_run_challenger` and `_call_llm`.
  - Add conditional stderr logging guarded by `args.verbose`.
  - Keep all verbose output in `stderr` so normal stdout behavior and downstream piping remain unchanged.

- **Out of scope**
  - No changes to `debate_common.py`, `debate_tools.py`, or other modules.
  - No new dependencies.
  - No configuration file changes.
  - No changes to default non-verbose behavior.

Estimated footprint: ~20 LOC. ESTIMATED: assumes adding one argparse flag, plumbing one boolean through two functions, and a small number of guarded print statements in a single file.

## Implementation Sketch

1. Add `parser.add_argument("--verbose", action="store_true", help="Print LLM and tool-call diagnostics to stderr")`.
2. Pass `args.verbose` into `_run_challenger(...)`.
3. Pass the same boolean into `_call_llm(...)`.
4. In verbose mode, emit:
   - a prompt preview before each LLM call,
   - the full response after the call returns,
   - each tool invocation and result,
   - token counts alongside existing progress output where available.
5. Keep all prints behind the flag so the default path stays byte-for-byte equivalent in practice except for the presence of the new CLI option.

## Rollback

Revert the commit.

Because the flag is default-off, standard non-verbose invocations keep the current behavior. Existing tests and CI workflows should therefore remain unaffected unless they assert on the exact CLI help text.

## Why This Is Worth Shipping

Each manual debug session currently costs an estimated 5–10 minutes of edit/revert churn. A persistent flag removes that repeated overhead for a common failure-analysis task. ESTIMATED: assumes current workflow includes editing, rerunning, and reverting temporary debug prints per session.

The change is purely additive, isolated to one script, and hidden behind a default-off flag. That keeps regression risk low while making failures materially easier to inspect.

It also eliminates a specific source of avoidable repository noise: temporary debug-print commits in `_run_challenger` and `_call_llm`.

## Effort

Small.

The change touches one file, introduces one CLI argument, and adds a handful of conditional stderr print statements. It should be easy to review and ship in a single pass.

---
debate_id: negative-control-tightened
created: 2026-04-18T09:54:32-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# negative-control-tightened — Refined Document

## Round 1 (gemini-3.1-pro)
This is an excellent, tightly scoped proposal. The problem is clearly quantified (3 devs, 4 commits, 5-10 minutes per session), the solution is direct, and the blast radius is explicitly bounded. 

One minor implementation note: threading `args.verbose` through multiple function signatures (`_run_challenger`, `_call_llm`) can add boilerplate. You might consider configuring Python's standard `logging` module at the top level (`logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)`) to avoid modifying function signatures, though conditional prints are perfectly fine for a ~20 LOC change. The revised text slightly generalizes the implementation step to allow either approach.

### Frame Check
Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The revision is already concise and well-scoped. It clearly states the user pain, keeps the change additive, and avoids overreaching beyond `scripts/debate.py`.

Remaining issues:
- The proposal lacks a recommendations section. That is acceptable here because this is a short proposal rather than a recommendation matrix.
- “Running token counts” is under-specified: if token accounting is not already available in `debate.py`, adding it may exceed the claimed ~20 LOC. This is best fixed inline by narrowing the output to token counts when already exposed by the existing response object or client wrapper.
- “Full response” conflicts slightly with “prompt truncated to the first 500 chars for readability.” The proposal should be explicit that verbose mode prints the full model response but only a truncated prompt preview.
- “Zero behavior change” is too absolute. Default-off means no intended behavior change for standard invocations, but the new code path still adds maintenance surface. Tightening that wording makes the claim more defensible.
- The implementation guidance should choose one mechanism. For a small script-scoped change, guarded stderr prints are simpler than introducing logging configuration unless logging already exists.

### Frame Check
Frame check: document's frame is sound.

## Final Refined Document

# Proposal: Add `--verbose` flag to `scripts/debate.py`

## Problem

`debate.py` currently prints only high-level progress to stderr, such as model name, latency, and tool-call count. When a debate run produces unexpected output — for example, an empty response, off-format findings, or premature termination — developers need the intermediate LLM response text and tool-call trace to diagnose the issue.

The current workaround is to manually edit `_run_challenger` and `_call_llm` in `debate.py` to add temporary `print()` statements, then revert those edits after debugging. Three developers on the team have done this in the last month; the git log shows 4 commits adding and removing temporary debug prints in these functions. This creates recurring edit/revert churn of roughly 5–10 minutes per debug session.

## Proposed Change

Add a `--verbose` CLI flag that, when set, outputs the following debug information to stderr:

- For each LLM call:
  - a prompt preview truncated to the first 500 characters for readability
  - the full model response
- For each tool call:
  - tool name
  - arguments
  - return value
- Running token counts, if token usage is already exposed by the existing response object or client path in `debate.py`

When `--verbose` is not set, standard invocations keep the current output behavior. The default remains off.

## Scope

- **Target:** `scripts/debate.py` only.
- **Implementation:** Add an `argparse` flag to the top-level parser and guard the new stderr outputs behind this flag. Use direct guarded stderr prints unless `debate.py` already has an established logging setup.
- **Exclusions:** No changes to `debate_common.py`, `debate_tools.py`, or other modules. No new dependencies or config file changes.
- **Size:** ~20 LOC ESTIMATED: assumes prompt/response and tool-call data are already available at the current call sites and token counts are only printed when already exposed, not newly computed.

## Rollback

Revert the commit. Because the flag is default-off, standard invocations should continue to produce the same output as before, and existing tests and CI workflows should not require changes.

## Why This Is Worth Shipping

A persistent flag removes the recurring 5–10 minute friction of manual edit/revert cycles during debugging. The change is additive, isolated to one script, and disabled by default, so regression risk is low.

## Effort

Small. This requires modifying one file, adding one argument, and inserting guarded outputs at existing LLM and tool-call sites. It should be reviewable in a single sitting.

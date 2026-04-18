---
debate_id: negative-control-v5
created: 2026-04-18T11:30:05-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# negative-control-v5 — Refined Document

## Round 1 (gemini-3.1-pro)
This is an excellent, tightly scoped proposal. The problem statement is particularly strong because it cites specific, verifiable evidence (git logs showing 4 commits adding/removing debug prints) rather than relying on vague complaints. The scope, rollback plan, and ROI are all perfectly scaled to the size of the change. 

Minor prose tightening was applied to improve flow, but the core structure and technical details remain exactly as proposed.

### Frame Check
- Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The proposal is already crisp and narrowly scoped. I kept that posture, but tightened a few areas to make the recommendation more executable and slightly safer:

- Strengthened the implementation section from “add print statements” to a concrete logging contract: write only to stderr, preserve default behavior, and avoid changing control flow.
- Added a small but important safety caveat: verbose output may include prompt/response content and tool payloads, so it should be treated as diagnostic output, not routine logging.
- Narrowed one absolute claim. “Zero behavior change” is too strong because enabling verbose mode does intentionally change stderr output and could expose sensitive content; the revised document states no behavior change for default invocations.
- Preserved the existing evidence and did not inflate the problem beyond the cited developer churn.

### Frame Check
Frame check: document's frame is sound.

## Final Refined Document

# Proposal: Add `--verbose` flag to `scripts/debate.py`

## Problem

`debate.py` currently prints only high-level progress to stderr (model name, latency, tool call count). When a debate run produces unexpected output—such as an empty response, off-format findings, or premature termination—developers need the intermediate LLM response text and tool-call trace to diagnose the issue.

The current workaround is manual: developers edit `_run_challenger` and `_call_llm` in `debate.py` to add temporary `print()` statements, then revert the edits after debugging. This is a recurring tax; three developers on the team have done this in the last month alone (git log shows 4 commits adding and removing temporary debug prints in these functions).

## Proposed Change

Add a `--verbose` CLI flag that, when set, prints the following diagnostic data to stderr:

- Each LLM call's full prompt, truncated to the first 500 characters
- Each LLM call's full response
- Each tool call's name, arguments, and return value
- Running token counts

When `--verbose` is not set, existing behavior remains unchanged. The default state is off.

## Scope

- **Target:** `scripts/debate.py`
- **Implementation:**
  - Add a `--verbose` boolean flag to the top-level argparse parser
  - Thread `args.verbose` through to `_run_challenger` and `_call_llm`
  - Add conditional stderr logging guarded by `args.verbose`
  - Keep the change observational only: no changes to execution order, retry behavior, tool behavior, or return values
- **Exclusions:** No changes to `debate_common.py`, `debate_tools.py`, or other modules. No new dependencies or configuration changes.
- **Footprint:** ~20 LOC.

## Rollback

Revert the commit. Because the flag is default-off, standard non-verbose invocations will behave as they do today. Existing tests and CI workflows should be unaffected unless they explicitly depend on exact stderr contents under verbose mode.

## Why This Is Worth Shipping

Each debug session currently costs ~5–10 minutes of edit/revert churn. A persistent flag eliminates this friction permanently.

The change is additive and operationally low-risk for normal usage because the default path is unchanged. The implementation is also easy to review because it is confined to one script and does not alter shared modules.

## Risks and Constraints

- Verbose mode will emit prompt text, model responses, and tool payloads to stderr. That output should be treated as diagnostic data and used only in contexts where that content is acceptable to expose.
- Truncating prompts to 500 characters keeps output readable while still surfacing enough context to debug most formatting and control-flow issues.

## Effort

Small. The change touches a single file, introduces one new argument, and adds guarded diagnostic printing. It is easily reviewable in one sitting.

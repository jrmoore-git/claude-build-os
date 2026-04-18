---
debate_id: negative-control-v3
created: 2026-04-18T09:59:57-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# negative-control-v3 — Refined Document

## Round 1 (gemini-3.1-pro)
This is an exceptionally well-scoped and grounded proposal. It identifies a specific pain point, backs it up with version control evidence (4 commits, 3 developers), quantifies the cost (5-10 minutes per session), and proposes a minimal, low-risk solution. 

The refinement focuses only on minor formatting improvements to make the specifications even easier to read during implementation and code review.

### Frame Check
Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The proposal is already strong: scoped to one file, explicit about default-off behavior, and supported by concrete evidence from recent developer activity. The prior revision does not appear to have introduced regressions because there is no sign of overreach beyond `scripts/debate.py`, and the recommendation remains executable.

Remaining issues are mostly completeness and precision:
- The proposal has no explicit recommendations section. That is acceptable here because the whole document is itself a single concrete proposal, but the implementation details can be made more operational.
- “Running token counts” is slightly under-specified; the document should say whether this means per-call, cumulative, or both.
- “Complete LLM response” and “tool returned value” may produce very large stderr output or expose sensitive content from prompts/tool payloads. That is not a frame defect, but it should be handled inline with a bounded logging rule.
- “Near-zero” regression risk is directionally right but too absolute without naming the actual risks. Better to state the concrete risks and the guardrails.

### Frame Check
- Frame check: document's frame is sound.

## Final Refined Document

# Proposal: Add `--verbose` flag to `scripts/debate.py`

## Problem

`debate.py` currently prints only high-level progress to stderr: model name, latency, and tool-call count. When a debate run produces unexpected output — such as an empty response, off-format findings, or premature termination — developers need the intermediate LLM response text and tool-call trace to diagnose the issue.

The current workaround is manually editing `_run_challenger` and `_call_llm` in `debate.py` to add temporary `print()` statements, then reverting the edits after debugging.

- **Impact:** Three developers on the team have done this in the last month.
- **Evidence:** Git log shows 4 separate commits adding and removing temporary debug prints to these specific functions.
- **Cost:** Each debug session currently costs ~5–10 minutes of edit/revert churn.

This is a recurring local debugging task, not a one-off incident, and the current workflow creates avoidable churn in both working trees and commit history.

## Proposed Change

Add a `--verbose` CLI flag to `debate.py`.

When set, the script will print diagnostic data to stderr for each debate run:

- **LLM calls:** the prompt, truncated to the first 500 characters, and the complete LLM response.
- **Tool calls:** the tool name, provided arguments, and returned value.
- **Metrics:** token counts for each LLM call and a running cumulative total for the process.

When `--verbose` is not set, existing behavior remains unchanged. The default is off.

## Scope

- **Modified files:** `scripts/debate.py` only.
- **Implementation:**
  - Add a `--verbose` boolean flag to the top-level argparse parser.
  - Thread `args.verbose` into `_run_challenger` and `_call_llm`, or initialize a module-level logger from the parsed flag.
  - Guard all additional diagnostic output behind the verbose check.
  - Keep all verbose output on stderr so stdout behavior remains unchanged.
- **Constraints:**
  - No changes to `debate_common.py`, `debate_tools.py`, or other modules.
  - No new dependencies.
  - No configuration file changes.
- **Size:** ~20 lines of code.

## Output Contract

Verbose mode should emit enough detail to debug execution without changing the script's normal interfaces:

- **Default mode:** preserve current stdout and stderr behavior exactly.
- **Verbose mode:** add diagnostic stderr lines only.
- **Prompt logging:** truncate prompts to 500 characters to keep logs readable.
- **Response logging:** print the full LLM response as returned.
- **Tool logging:** print tool name, arguments, and return value for each tool invocation.
- **Metric logging:** print per-call token counts and the cumulative total seen so far in the run.

This keeps the feature additive: users opt in when debugging, and non-verbose callers see no output-format change.

## Risks and Mitigations

- **Risk: excessively noisy logs during long runs.**  
  **Mitigation:** keep verbose mode default-off and send diagnostics only to stderr.
- **Risk: very large prompt payloads reduce log readability.**  
  **Mitigation:** truncate prompts to the first 500 characters.
- **Risk: accidental dependence on verbose output format.**  
  **Mitigation:** preserve existing default behavior exactly and treat verbose output as debugging-only diagnostics.

These are bounded risks because the flag is opt-in and isolated to one script.

## Rollback

Revert the commit.

Because the flag is default-off, standard non-verbose invocations keep the current behavior. Existing tests and CI workflows should remain unaffected.

## Why This Is Worth Shipping

A persistent flag removes recurring edit/revert churn from a common debugging workflow.

Based on the proposal's evidence, the current cost is:
- 5–10 minutes per debug session
- observed across 4 recent debug-print commit cycles in the git log

That is enough to justify a small, localized quality-of-life improvement, especially because the change is isolated to one file and does not alter the default execution path.

## Effort

Small.

This requires modifying one file, adding one CLI argument, and inserting conditional diagnostic output. It should fit in a single implementation and review pass.

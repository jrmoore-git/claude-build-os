---
scope: "Add --critique flag to sim_pipeline.py for iterative developer-in-the-loop annotation"
surfaces_affected: "scripts/sim_driver.py, scripts/sim_pipeline.py"
verification_commands: "python3.11 -m pytest tests/test_sim_driver.py tests/test_sim_pipeline.py -v"
rollback: "git revert <sha>"
review_tier: "Tier 2"
verification_evidence: "PENDING"
challenge_skipped: true
---

# Plan: Iterative Critique Loop (D22)

## Build Order

### Step 1: sim_driver.py — `format_transcript_markdown(result)`
Takes a result dict, returns readable markdown.
- Score summary header (per-dimension scores, overall average, termination reason)
- `### Turn N (role)` sections with content
- Developer annotates inline with `> ` blockquotes between turns
- No new dependencies

### Step 2: sim_driver.py — `critique_hook(directives)`
Hook factory. Returns a callable matching the turn_hook signature `(turn, max_turns, executor_history, transcript) -> str|None`.
- Injects all directives as a single system reminder at turn 1 only
- Directives are session-level context, not per-turn nudges
- Format: `[CRITIQUE DIRECTIVES: ...]\n1. directive\n2. directive\n...`

### Step 3: sim_pipeline.py — `extract_directives(annotated_path, model)`
Reads annotated markdown, calls LLM to extract structured directives.
- Returns `list[str]` — 3-7 specific behavioral directives
- Prompt instructs LLM to find developer annotations (blockquotes/comments) and convert to actionable executor instructions
- Default model: haiku (cheap, classification-grade task per orchestration.md model routing)
- On LLM failure: print error, return empty list (pipeline continues without critique)

### Step 4: sim_pipeline.py — `--critique` flag + wiring
New argparse argument in main().
- Read annotated file
- Call extract_directives()
- Print extracted directives to stderr for developer review
- Create critique_hook(directives), append to active_hooks
- Compatible with other hooks (e.g., --hooks sufficiency --critique annotated.md)

### Step 5: sim_pipeline.py — score comparison
When --critique is used and --output-dir contains a prior pipeline_report.json:
- Load prior scores
- After run completes, print before/after diff table to stderr
- Format: `dimension: old → new (delta)`

## Files

| File | Action | Scope |
|------|--------|-------|
| scripts/sim_driver.py | Modify | +format_transcript_markdown() (~25 lines), +critique_hook() (~15 lines) |
| scripts/sim_pipeline.py | Modify | +extract_directives() (~35 lines), +--critique flag + wiring (~25 lines), +score comparison (~20 lines) |

Estimated total: ~120 lines new code.

## Verification

```bash
# Existing tests still pass
python3.11 -m pytest tests/test_sim_driver.py tests/test_sim_pipeline.py -v

# Full suite
python3.11 -m pytest tests/ -v
```

## Execution Strategy

**Decision:** sequential
**Reason:** 2 files, ~6 edits, step 3-5 depend on step 1-2 exports. Below parallel threshold.

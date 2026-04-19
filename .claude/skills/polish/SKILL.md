---
name: polish
description: "Cross-model iterative refinement (6 rounds, 3 models). Use when you have a draft document, plan, or answer that needs iterative improvement across model families."
version: 1.0.0
user-invocable: true
---

# /polish — Cross-Model Iterative Refinement

6-round collaborative refinement across 3 model families. Each model reads the previous version and produces a better one. No personas, no adversarial framing — just iterative improvement.

Use standalone on any input, or as the final phase of `/challenge --deep`.

Defers to `/pressure-test` when you need adversarial pressure-testing. Defers to `/review` for post-implementation code review.

## Safety Rules

- NEVER discard the original document structure without user approval.
- Do not add content beyond what exists in the source document — refinement improves, not expands.
- NEVER send proprietary content to external models without the user's awareness.
- **Output silence** — Do not emit text between tool calls. Single formatted output at the end only.

## Procedure

### Step 1: Get topic and input

If the user provided a topic as an argument, use it. Otherwise ask: "What's the topic name? (e.g., `auth-redesign`)"

Identify the input document. Accept any of:
- Explicit file path from the user
- `tasks/<topic>-proposal.md` (if coming from debate pipeline)
- `tasks/<topic>-plan.md`
- `tasks/<topic>-design.md`
- Any other file the user points to

If no document found: "Which file should I refine? Provide the path." Stop.

### Step 2: Optional focus areas

Ask: "Any specific areas to focus on? (enter to skip)"

If the user provides focus areas, write them to a temp file:

```bash
cat > /tmp/refine-focus-<topic>.md << 'FOCUS'
The following areas were flagged for special attention during refinement:

<user's focus areas>

Address these specifically while also improving the document generally.
FOCUS
```

### Step 2b: Build project context file

Write project context to a separate file that will be passed via `--system-context`. The document itself stays unwrapped so the refine truncation check (ratio of revised/input) stays calibrated.

1. Read `docs/current-state.md` fresh — extract current phase, active work, and relevant subsystem (ceiling ~80 lines).
2. Read `tasks/session-log.md` (last 2–3 relevant entries) — summarize recent work relevant to this document, including decisions and pivots (ceiling ~50 lines).
3. Optionally run `python3.11 scripts/enrich_context.py --proposal <input-file> --scope define` if the input file exists on disk (ceiling ~20 lines).
4. Write the context file:

```bash
CONTEXT_FILE=$(mktemp /tmp/polish-context-XXXXXX.md)
cat > "$CONTEXT_FILE" << 'CTX_EOF'
## Project Context
<project description from CLAUDE.md + current-state.md summary>

## Recent Context
<session-log summary>

## Prior Decisions
<enrich_context.py output, if any>
CTX_EOF
```

Pass `$CONTEXT_FILE` as `--system-context` in Step 3. Clean up after Step 3 completes.

Do NOT use `--judgment` for project context. `--judgment` filters for `### Challenge ... Decision: ACCEPT` blocks and silently drops anything else — plain context prose never reaches the model through that slot.

### Step 3: Run refinement

```bash
python3.11 scripts/debate.py refine \
  --document <input-file> \
  --system-context $CONTEXT_FILE \
  --rounds 6 \
  --output tasks/<topic>-refined.md \
  --enable-tools
```

If focus areas were provided in Step 2, append them to `$CONTEXT_FILE` after the project context, separated by `\n\n## Focus Areas\n\n`, then pass the combined file via `--system-context`. Do not use `--judgment` for focus areas — see Step 2b note.

If debate.py fails or is unavailable, fall back to single-model analysis using the session model. Perform 3 manual refinement passes on the document, writing each intermediate version to the output file.

Parse JSON stdout. Four fields matter:
- `rounds_completed` — total rounds that ran (includes errored and discarded rounds).
- `rounds_failed` — LLM/network errors. If > 2, warn but don't block.
- `rounds_discarded` — rounds where the revised doc was truncated or dropped recommendation slots. Revision was NOT promoted.
- `rounds_successful` — rounds that produced a promoted revision (= `rounds_completed - rounds_failed - rounds_discarded`).

**Sanity check (HARD):** if `rounds_successful == 0` and `rounds_completed > 0`, the refined document is identical to the input — every round either errored or was discarded. Report DONE_WITH_CONCERNS and warn the user that the output is NOT improved. Point them at the round notes in the output file header to diagnose (most likely cause: truncation against an oversized input, dropped recommendation slots in a critique-mode doc, or all models timing out). Check `rounds_successful`, not `rounds_discarded == rounds_completed` — the latter is false when any round also errored, which would silently bypass the sanity check.

### Step 4: Summary

Display:

```
## Refinement Complete

Input:  <input-file>
Output: tasks/<topic>-refined.md
Rounds: <rounds_successful>/<rounds_completed> successful (<models used>)
        <rounds_failed> failed, <rounds_discarded> discarded

Round-by-round notes are in the output file header.
```

Clean up temp context and focus files if created. If the skill exits via an error path before reaching this point, the temp files in `/tmp/polish-context-*` will persist (no guaranteed cleanup on failure); not a secret risk since they only contain `docs/current-state.md` + session-log summaries, but review and delete if needed.

## Output Format

The refined document is written to `tasks/<topic>-refined.md`. It preserves the original structure with improvements applied across 6 rounds (or fewer if early-stopped). The output file header contains round-by-round notes showing what each model changed.

## Important Notes

- Cost: ~$0.10-0.30 per run depending on document size.
- 6 rounds across 3 models means each model refines twice (gemini -> gpt -> claude -> gemini -> gpt -> claude).
- Model rotation configured in `config/debate-models.json` under `refine_rotation`.
- The `--enable-tools` flag gives refiners read-only access to verify claims against the codebase.
- When called as part of `/challenge --deep`, the judgment file seeds accepted challenges as focus areas. When standalone, the focus areas slot serves the same purpose.
- Each round preserves verified data, measurements, and operational context — models are instructed not to collapse evidence into summaries.

## Completion

Report status:
- **DONE** — All steps completed successfully. Refined document written.
- **DONE_WITH_CONCERNS** — Completed with partial rounds (some rounds failed).
- **BLOCKED** — Cannot proceed. State the blocker.
- **NEEDS_CONTEXT** — Missing input document or topic name.

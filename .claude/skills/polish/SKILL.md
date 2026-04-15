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

### Step 3: Run refinement

If focus file exists, use `--judgment` to seed it (reuses the judgment_context slot):

```bash
python3.11 scripts/debate.py refine \
  --document <input-file> \
  --rounds 6 \
  --output tasks/<topic>-refined.md \
  --enable-tools
```

If focus areas were provided, add: `--judgment /tmp/refine-focus-<topic>.md`

If debate.py fails or is unavailable, fall back to single-model analysis using the session model. Perform 3 manual refinement passes on the document, writing each intermediate version to the output file.

Parse JSON stdout. If rounds_failed > 2, warn but don't block — partial refinement is still useful.

### Step 4: Summary

Display:

```
## Refinement Complete

Input:  <input-file>
Output: tasks/<topic>-refined.md
Rounds: <completed>/<total> (<models used>)

Round-by-round notes are in the output file header.
```

Clean up temp focus file if created.

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

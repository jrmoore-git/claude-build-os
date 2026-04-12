---
name: polish
description: "Cross-model iterative refinement (6 rounds, 3 models). Standalone or as final phase of /challenge --deep. For improving any document, plan, or answer."
user-invocable: true
---

# /polish — Cross-Model Iterative Refinement

6-round collaborative refinement across 3 model families. Each model reads the previous version and produces a better one. No personas, no adversarial framing — just iterative improvement.

Use standalone on any input, or as the final phase of `/challenge --deep`.

Defers to `/pressure-test` when you need adversarial pressure-testing. Defers to `/review` for post-implementation code review.

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

## Important Notes

- Cost: ~$0.10-0.30 per run depending on document size.
- 6 rounds across 3 models means each model refines twice (gemini -> gpt -> claude -> gemini -> gpt -> claude).
- Model rotation configured in `config/debate-models.json` under `refine_rotation`.
- The `--enable-tools` flag gives refiners read-only access to verify claims against the codebase.
- When called as part of `/challenge --deep`, the judgment file seeds accepted challenges as focus areas. When standalone, the focus areas slot serves the same purpose.
- Each round preserves verified data, measurements, and operational context — models are instructed not to collapse evidence into summaries.

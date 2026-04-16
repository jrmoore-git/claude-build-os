---
name: pressure-test
description: "Counter-thesis or pre-mortem failure analysis. Use when you need adversarial analysis of a direction, strategy, or plan. Default frame: challenge. With --premortem: assume the plan failed and write the post-mortem."
version: 1.0.0
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, AskUserQuestion
---

# /pressure-test — Strategic Counter-Thesis or Pre-Mortem

Single-model adversarial analysis. Two frames: challenge (strategic counter-thesis, default) and premortem (assume the plan failed, write the post-mortem from the future).

## Frames

| Frame | What it does | When to use |
|-------|-------------|-------------|
| **challenge** (default) | Strategic counter-thesis — attacks the core premise | Direction, strategy, product bets |
| **premortem** (`--premortem`) | Assumes the plan failed, writes post-mortem from the future | Concrete plans before execution |

## Safety Rules

- NEVER suppress findings to avoid conflict — report all identified risks.
- Do not soften critical risks or downplay failure scenarios.
- NEVER fabricate evidence or cite non-existent data to support a finding.
- **Output silence** — Do not emit text between tool calls. Single formatted output at the end only.

## Procedure

### Step 1: Determine frame and topic

Parse the user's input:

- Default frame is **challenge** (strategic counter-thesis).
- If the user passed `--premortem`, or said "pre-mortem", "why will this fail", or "failure analysis": frame is **premortem**.

Store as `FRAME`.

If the user provided a topic as an argument or a file path, derive `TOPIC` from the filename stem (e.g., `tasks/auth-proposal.md` -> `auth`). Otherwise ask:

```
What topic or proposal should I pressure-test? Provide a topic name or path to the proposal file.
```

Store as `TOPIC`.

### Step 2: Pre-flight discovery (optional)

Pre-flight is optional for pressure-test. The proposal is usually concrete enough to skip.

**Skip if:** The user says "skip", "just run it", or the proposal file is concrete and specific.

**Auto-run if:** The user says "answer the questions yourself" and you have enough context from memory, prior conversation, or the proposal file. State your assumed answers briefly, let the user correct, then proceed.

**If running pre-flight:**

Read `config/prompts/preflight-adaptive.md` for the full protocol.

1. Infer the domain from the proposal (product, engineering, organizational, research, strategy, process).
2. Select 2-3 forcing questions adaptively. Draw from reference pre-flight files when the domain matches:
   - Product domain: reference `config/prompts/preflight-product.md`
   - Solo builder domain: reference `config/prompts/preflight-solo-builder.md`
   - Architecture domain: reference `config/prompts/preflight-architecture.md`
   - Other domains: generate questions using templates in `preflight-adaptive.md`
3. Ask questions ONE AT A TIME (hard cap at 3 for pressure-test).
4. Compose context from answers. Store as `PREFLIGHT_CONTEXT`.

If pre-flight was skipped, set `PREFLIGHT_CONTEXT` to empty string.

### Step 3: Require proposal

**Challenge frame:** `tasks/<TOPIC>-proposal.md` must exist. If missing, tell the user:

```
Missing: tasks/<TOPIC>-proposal.md
Write your proposal there first, then re-run /pressure-test.
```

**Premortem frame:** Accept either `tasks/<TOPIC>-proposal.md` or `tasks/<TOPIC>-plan.md`. Check both, prefer plan if both exist. If neither exists, tell the user:

```
Missing: tasks/<TOPIC>-proposal.md or tasks/<TOPIC>-plan.md
Write your proposal or plan there first, then re-run /pressure-test --premortem.
```

Store the resolved path as `PROPOSAL_PATH`.

### Step 3b: Assemble context packet

Build a self-contained context packet so `debate.py` receives enough project context to evaluate without wasting tool calls on reconstruction.

1. **Project Context (50–100 lines):** Read `docs/current-state.md` fresh. Extract current phase, active work, and the subsystem relevant to this proposal. Include a project description from `CLAUDE.md` covering what Build OS is, key components, and the specific subsystem under evaluation.

2. **Recent Context (40–80 lines):** Read `tasks/session-log.md` (last 3–5 entries). Summarize the recent work arc — what was built, decided, pivoted, and what remains unresolved. Include relevant decision IDs from `tasks/decisions.md`.

3. **Evaluation-Specific Context (optional):** If `scripts/enrich_context.py` exists:
   ```bash
   python3.11 scripts/enrich_context.py --proposal $PROPOSAL_PATH --scope challenge
   ```
   Include relevant decisions and lessons from the output. If it fails or returns empty, proceed without it.

4. **Compose:** Assemble into a single text block with `## Project Context`, `## Recent Context`, and `## Prior Decisions` sections.

5. **Merge:** If PREFLIGHT_CONTEXT exists from Step 2, prepend the context packet before it. The combined text becomes the `--context` value in Step 4. If PREFLIGHT_CONTEXT was empty, the context packet alone becomes the `--context` value.

### Step 4: Run pressure-test

If debate.py fails or is unavailable, fall back to single-model analysis using the session model. Perform the counter-thesis or pre-mortem analysis directly and write the output file.

#### Challenge frame (default)

```bash
python3.11 scripts/debate.py pressure-test \
  --proposal tasks/<TOPIC>-proposal.md \
  --context "$PREFLIGHT_CONTEXT" \
  --output tasks/<TOPIC>-pressure-test.md
```

#### Premortem frame

```bash
python3.11 scripts/debate.py pressure-test \
  --proposal $PROPOSAL_PATH \
  --frame premortem \
  --context "$PREFLIGHT_CONTEXT" \
  --output tasks/<TOPIC>-premortem.md
```

If `--context` is empty, omit the flag.

### Step 5: Display output

Read the output file and display its contents directly in the conversation.

### Step 6: Summary

```
## /pressure-test complete — [FRAME] frame

| Artifact | Path | Status |
|----------|------|--------|
| [output artifact] | tasks/<TOPIC>-pressure-test.md or tasks/<TOPIC>-premortem.md | done/failed |
```

For **challenge** frame, suggest:
> Revise the proposal based on the counter-thesis, or proceed if the thesis holds.

For **premortem** frame, suggest:
> Address the top failure scenarios in your plan before proceeding.

## Output Format

The pressure-test artifact is written to `tasks/<TOPIC>-pressure-test.md` (challenge frame) or `tasks/<TOPIC>-premortem.md` (premortem frame). Contains the adversarial analysis findings, risk assessments, and recommended mitigations.

## Degraded Mode

Single call, no partial state. If the call fails, report the error and stop.

## Internal Notes (SILENT -- never narrate these to the user)

- Always display output directly in the conversation, not just to a file.
- Never narrate internal mechanics, cost estimates, model choices, or pipeline plumbing.
- Each step checks for existing artifacts and skips if found.
- If pre-flight context exists, pass it via `--context`. If not, omit the flag entirely.

## Completion

Report status:
- **DONE** — All steps completed successfully. Pressure-test artifact written.
- **DONE_WITH_CONCERNS** — Completed but with degraded analysis (fallback mode).
- **BLOCKED** — Cannot proceed. State the blocker (e.g., missing proposal).
- **NEEDS_CONTEXT** — Missing topic or proposal file.

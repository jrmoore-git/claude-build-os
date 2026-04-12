---
name: pressure-test
description: "Counter-thesis or pre-mortem failure analysis. Use for adversarial analysis of a direction, strategy, or plan. Default frame: challenge (strategic counter-thesis). With --premortem: assume the plan failed and write the post-mortem from the future. Defers to: /challenge (should we build this at all), /explore (divergent options), /plan (implementation spec)."
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

### Step 4: Run pressure-test

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

## Degraded Mode

Single call, no partial state. If the call fails, report the error and stop.

## Internal Notes (SILENT -- never narrate these to the user)

- Always display output directly in the conversation, not just to a file.
- Never narrate internal mechanics, cost estimates, model choices, or pipeline plumbing.
- Each step checks for existing artifacts and skips if found.
- If pre-flight context exists, pass it via `--context`. If not, omit the flag entirely.

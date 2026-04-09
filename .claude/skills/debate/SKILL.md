---
name: debate
description: "Full cross-model debate pipeline: challenge → judge → refine. For architectural decisions and design uncertainty."
user-invocable: true
---

# /debate — Cross-Model Debate Pipeline

Run the full adversarial pipeline on a proposal: challenge → judge → refine. Produces a refined spec that `/review` can validate against.

## Procedure

### Step 1: Get topic

If the user provided a topic as an argument, use it. Otherwise ask: "What's the topic name? (e.g., `review-skill-restructure`)"

### Step 2: Require proposal

```bash
test -f tasks/<topic>-proposal.md && echo "found" || echo "none"
```

If missing: "Write your proposal to `tasks/<topic>-proposal.md`, then run `/debate` again." Stop.

### Step 3: Enrich context

```bash
python3 scripts/enrich_context.py --proposal tasks/<topic>-proposal.md
```

If enrichment returns results, create a temp file with the proposal + `## Prior Context` section appended.

### Step 4: Challenge (skip if artifact exists)

Check for existing challenge:
```bash
test -f tasks/<topic>-debate.md && echo "found" || echo "none"
```

If missing, run:
```bash
python3 scripts/debate.py challenge \
  --proposal <enriched or original proposal> \
  --personas architect,security,pm \
  --output tasks/<topic>-debate.md
```

Parse JSON stdout. If all challengers failed, display warning and stop: "Challenge phase failed (model routing may be down). Partial artifact at `tasks/<topic>-debate.md`. Retry later or proceed with what exists."

Note: output is `-debate.md`, NOT `-challenge.md` — avoids collision with `/challenge` artifacts.

### Step 5: Judge (skip if artifact exists)

```bash
test -f tasks/<topic>-judgment.md && echo "found" || echo "none"
```

If missing, run:
```bash
python3 scripts/debate.py judge \
  --proposal tasks/<topic>-proposal.md \
  --challenge tasks/<topic>-debate.md \
  --model gpt-5.4 \
  --output tasks/<topic>-judgment.md
```

If judge fails, display warning: "Judge phase failed. Challenge artifact exists at `tasks/<topic>-debate.md`. Partial pipeline is still useful." Stop.

### Step 6: Refine (skip if artifact exists)

```bash
test -f tasks/<topic>-refined.md && echo "found" || echo "none"
```

If missing, run:
```bash
python3 scripts/debate.py refine \
  --document tasks/<topic>-proposal.md \
  --judgment tasks/<topic>-judgment.md \
  --rounds 3 \
  --output tasks/<topic>-refined.md
```

If refine fails, display warning but don't block — judgment + challenge are still useful.

### Step 7: Summary

Display:
```
## Debate Complete

| Stage     | Artifact                        | Status |
|-----------|---------------------------------|--------|
| Challenge | tasks/<topic>-debate.md         | pass/fail |
| Judgment  | tasks/<topic>-judgment.md       | pass/fail |
| Refined   | tasks/<topic>-refined.md        | pass/fail |

Next: Build the implementation, then run /review <topic>
```

The refined document becomes the spec. `/review` will automatically check implementation against it when `tasks/<topic>-refined.md` exists.

## Degraded Mode

Each stage is independently valuable. If a later stage fails:
- Challenge only → useful for understanding objections
- Challenge + judgment → useful for knowing which objections hold
- All three → full refined spec

Stop at the step that fails. Partial artifacts are valid. Do not delete them.

## Important Notes

- This skill costs ~$0.20-0.75 per run (measured: $0.24 on a small proposal, scales with input size). Reserve for architectural decisions, PRD changes, schema changes, and design uncertainty.
- Each step checks for existing artifacts and skips if found. Re-running `/debate` after a partial failure resumes where it left off.
- The judgment uses a different model family from the author to avoid self-preference bias.

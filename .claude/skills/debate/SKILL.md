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

If found, check for fat template sections (`### Current System Failures`, `### Operational Context`, `### Baseline Performance`). If any are missing, tell the user which sections are absent and offer to enrich the proposal before proceeding. Fat context prevents challengers from fabricating numbers and was proven to flip debate conclusions in A/B testing.

### Step 3: Enrich context

```bash
python3.11 scripts/enrich_context.py --proposal tasks/<topic>-proposal.md --scope debate
```

If enrichment returns results, create a temp file with the proposal + `## Prior Context` section appended.

### Step 4: Challenge (skip if artifact exists)

Check for existing challenge:
```bash
test -f tasks/<topic>-debate.md && echo "found" || echo "none"
```

If missing, run:
```bash
python3.11 scripts/debate.py challenge \
  --proposal <enriched or original proposal> \
  --personas architect,security,pm \
  --enable-tools \
  --output tasks/<topic>-debate.md
```

Parse JSON stdout. If all challengers failed, display warning and stop: "Challenge phase failed (LiteLLM may be down). Partial artifact at `tasks/<topic>-debate.md`. Retry later or proceed with what exists."

Note: output is `-debate.md`, NOT `-challenge.md` — avoids collision with `/challenge` artifacts.

### Step 5: Judge (skip if artifact exists)

```bash
test -f tasks/<topic>-judgment.md && echo "found" || echo "none"
```

If missing, run:
```bash
python3.11 scripts/debate.py judge \
  --proposal tasks/<topic>-proposal.md \
  --challenge tasks/<topic>-debate.md \
  --model gpt-5.4 \
  --verify-claims \
  --output tasks/<topic>-judgment.md
```

`--verify-claims` runs an independent Claude Sonnet pass that uses verification tools to check factual claims in the challenger transcript before the judge sees them. Catches the case where 1–3 challengers reviewed blind (made 0 tool calls). Adds ~$0.01–0.05 + ~30s to the judge stage. The judgment artifact will contain an `## INDEPENDENT CLAIM VERIFICATION` section.

If judge fails, display warning: "Judge phase failed. Challenge artifact exists at `tasks/<topic>-debate.md`. Partial pipeline is still useful." Stop.

### Step 6: Refine (skip if artifact exists)

```bash
test -f tasks/<topic>-refined.md && echo "found" || echo "none"
```

If missing, run:
```bash
python3.11 scripts/debate.py refine \
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
| Challenge | tasks/<topic>-debate.md         | ✅/❌   |
| Judgment  | tasks/<topic>-judgment.md       | ✅/❌   |
| Refined   | tasks/<topic>-refined.md        | ✅/❌   |

Next: Build the implementation, then run /review <topic>
```

The refined document becomes the spec. `/review` will automatically check implementation against it when `tasks/<topic>-refined.md` exists.

After displaying the summary, update the pipeline manifest with all completed stages:

```bash
python3.11 scripts/pipeline_manifest.py add <topic> --skill debate-challenge --artifact tasks/<topic>-debate.md --status complete
python3.11 scripts/pipeline_manifest.py add <topic> --skill debate-judge --artifact tasks/<topic>-judgment.md --status complete
python3.11 scripts/pipeline_manifest.py add <topic> --skill debate-refine --artifact tasks/<topic>-refined.md --status complete
```

Only add stages that completed successfully (check the status table above).

## Degraded Mode

Each stage is independently valuable. If a later stage fails:
- Challenge only → useful for understanding objections
- Challenge + judgment → useful for knowing which objections hold
- All three → full refined spec

Stop at the step that fails. Partial artifacts are valid. Do not delete them.

## Important Notes

- This skill costs ~$0.20-0.75 per run (measured: $0.24 on a small proposal, scales with input size). Reserve for architectural decisions, PRD changes, schema changes, and design uncertainty.
- Each step checks for existing artifacts and skips if found. Re-running `/debate` after a partial failure resumes where it left off.
- The judgment uses GPT-5.4 as judge (different model family from Claude to avoid self-preference bias).

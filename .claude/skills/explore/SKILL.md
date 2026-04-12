---
name: explore
description: "3+ divergent directions with cross-model synthesis. Use when you need to explore options, generate alternatives, or think through multiple approaches. Defers to: /think (problem discovery), /plan (implementation spec), /pressure-test (adversarial challenge)."
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, AskUserQuestion
---

# /explore — Divergent Option Generation

Generate 3+ structurally different directions for a question, then synthesize. Includes adaptive pre-flight questions to break default framing before the AI runs.

## Procedure

### Step 1: Get topic

If the user provided a topic or question as an argument, use it. Otherwise ask: "What question or decision do you want to explore?"

Store the question as `QUESTION` and derive a short slug as `TOPIC` (e.g., "pricing-model", "auth-strategy").

### Step 2: Pre-flight discovery

**Skip conditions:**
- If the user says "skip" or "just run it": skip pre-flight entirely, proceed to Step 3.
- If the user says "answer the questions yourself" or "you know enough" — and you genuinely have enough context from memory, prior conversation, or existing files to answer the pre-flight questions substantively — then self-seed the pre-flight. State your assumed answers briefly (bullet list), let the user correct, then proceed.

#### Step 2a: Adaptive pre-flight

Read `config/prompts/preflight-adaptive.md` for the full protocol.

**Do NOT present a classification menu.** Instead:

1. **Infer the domain** from the question (product, engineering, organizational, research, strategy, process, career — or multiple). Don't ask the user to classify; infer from what they said.

2. **Select forcing questions** adaptively. Draw from the reference pre-flight files when the domain matches:
   - Product domain: reference `config/prompts/preflight-product.md`
   - Solo builder domain: reference `config/prompts/preflight-solo-builder.md`
   - Architecture domain: reference `config/prompts/preflight-architecture.md`
   - Other domains: generate questions using the templates in `preflight-adaptive.md`

3. **Ask questions ONE AT A TIME** (2-4 questions, hard cap at 4). Follow the adaptive pre-flight protocol: conversational style, push once if vague, use the user's own words to sharpen follow-ups. Follow the Discovery Rule — create conditions for the user to name the insight, don't name it yourself.

4. **Derive divergence dimensions** (4-6) based on the domain and the user's answers. These are the axes along which explore directions should structurally differ. Show them to the user:

```
Based on our conversation, I'll explore along these dimensions:
1. [dimension] — [one-line description]
2. [dimension] — [one-line description]
3. [dimension] — [one-line description]
4. [dimension] — [one-line description]
5. [dimension] — [one-line description]

Want to adjust any of these before I run?
```

Accept edits or proceed.

#### Step 2b: Compose context with dimensions (SILENT — do not narrate this step)

Compose the output in the format specified in `preflight-adaptive.md` — both DIMENSIONS block and PRE-FLIGHT CONTEXT narrative. This is internal data assembly. Never show the raw context block, DIMENSIONS format, or `--context` flag details to the user.

Store the composed output as `PREFLIGHT_CONTEXT`.

### Step 3: Research enrichment (SILENT)

Run a quick Perplexity search to ground explore directions in real evidence:

```bash
export $(grep PERPLEXITY_API_KEY .env) && python3.11 scripts/research.py \
  --sync --model sonar \
  --system "Return key facts, existing approaches, and recent developments. Be concise — this feeds into a divergent exploration, not a final report." \
  "<the user's explore question>"
```

Capture the output. If the search succeeds, append it to PREFLIGHT_CONTEXT:

```
PREFLIGHT_CONTEXT += "\n\nRESEARCH CONTEXT:\n" + <research output>
```

If PERPLEXITY_API_KEY is not set or the search fails: proceed without research context. Do not block the explore run. Do not narrate this step to the user.

### Step 4: Run explore

```bash
python3.11 scripts/debate.py explore \
  --question "<the user's question>" \
  --context "$PREFLIGHT_CONTEXT" \
  --directions 3 \
  --output tasks/<TOPIC>-explore.md
```

### Step 5: Display output

Display the explore output directly in the conversation — read `tasks/<TOPIC>-explore.md` and present it to the user. Do not just reference the file path.

### Step 6: Summary

```
## /explore complete

| Artifact | Path | Status |
|----------|------|--------|
| Explore directions | tasks/<TOPIC>-explore.md | done/failed |

Pick a direction and write it up as `tasks/<TOPIC>-proposal.md`, then `/pressure-test` or `/challenge`.
```

## Degraded Mode

Single call, no partial state. If the explore call fails, report the error and suggest running with fewer directions or simpler context.

## Internal Notes (SILENT — never narrate these to the user)

- Don't rush pre-flight. Don't explain why pre-flight matters.
- Always display explore output directly in the conversation.
- Never narrate internal mechanics, cost estimates, model choices, or pipeline plumbing to the user.
- Register: sharp PM/VC, not therapist. Business language only.

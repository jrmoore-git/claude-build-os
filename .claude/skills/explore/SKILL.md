---
name: explore
description: "3+ divergent directions with cross-model synthesis. Use when you need to explore options, generate alternatives, or think through multiple approaches. Defers to: /think (problem discovery), /plan (implementation spec), /pressure-test (adversarial challenge)."
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, AskUserQuestion
---

# /explore — Divergent Option Generation

Generate 3+ structurally different directions for a question, then synthesize. Includes adaptive pre-flight questions to break default framing before the AI runs.

## Phase 0: Context Assessment

Before starting pre-flight, scan the conversation for context already established.

**Check each:**

| Signal | Look for | If found |
|--------|----------|----------|
| Question/decision | User stated what they're exploring or deciding | Use as QUESTION — skip Step 1. |
| Strategy context | Business model, user type, constraints discussed | Pre-seeds pre-flight — reduces questions needed in Step 2. |
| Implementation context | Technical approach, stack, architecture discussed | Pre-seeds pre-flight — strategy + implementation may both be covered. |
| Dimensions | User named specific tradeoffs or axes to explore | Pre-seed divergence dimensions in Step 2b. |

**Routing:**
- Question + both strategy and implementation context present → self-seed the pre-flight (same as "answer the questions yourself" skip condition). State assumed answers, let user correct, proceed to Step 3.
- Question + partial context → run Step 2 pre-flight but smart-skip questions already answered by conversation.
- No context → full sequence as normal.

## Procedure

### Step 1: Get topic

If the user provided a topic or question as an argument, use it. Otherwise ask: "What question or decision do you want to explore?"

Store the question as `QUESTION` and derive a short slug as `TOPIC` (e.g., "pricing-model", "auth-strategy").

### Step 2: Pre-flight discovery

**Skip conditions:**
- If the user says "skip" or "just run it": skip pre-flight entirely, proceed to Step 3.
- If the user says "answer the questions yourself" or "you know enough" — and you genuinely have enough context from memory, prior conversation, or existing files to answer the pre-flight questions substantively — then self-seed the pre-flight. State your assumed answers briefly (bullet list), let the user correct, then proceed.

#### Step 2a: Thread-and-steer intake

Read `config/prompts/preflight-adaptive.md` for the full protocol (v7).

**Do NOT present a classification menu or question bank.** Instead:

1. **Thread-and-steer.** Each question picks up the strongest unresolved thread from the user's last answer. Use their exact phrases. Q1 IS the opening move — no preamble.

2. **Register matching.** Mirror their case, length, and density. If they write fragments, you write fragments. If your response is more than 2x their word count, it's too long.

3. **Terse-user trigger.** If answers are short/vague (1-2 sentences, no elaboration), switch to options format for ALL remaining questions: "(a) X, (b) Y, (c) Z — which fits?"

4. **Three-gate sufficiency (internal).** After each answer from Q3+, check: (a) strategy covered? (b) implementation mentioned? If strategy passes but implementation missing → meta-question. When both pass → stop. Never expose this logic to the user.

5. **Reframe (optional, once).** If their answers reveal a root cause at a different level than their proposed solution, reframe with a one-sentence thesis + one question (~25 words, their vocabulary). If rejected, accept immediately.

6. **Meta-question follow-up.** After "what should I have asked you that I didn't?" is answered, ask one follow-up threading from what they revealed before stopping.

7. **Compose context block** with mandatory CONFIDENCE field (HIGH/MEDIUM/LOW) and derive 4 divergence dimensions. Show dimensions to the user:

```
Based on our conversation, I'll explore along these dimensions:
1. [dimension] — [one-line description]
2. [dimension] — [one-line description]
3. [dimension] — [one-line description]
4. [dimension] — [one-line description]

Want to adjust any before I run?
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

If PERPLEXITY_API_KEY is not set or the search fails: fall back to Claude's built-in WebSearch tool. Run 1-2 targeted web searches on the user's question, capture key facts, and append them to PREFLIGHT_CONTEXT as `RESEARCH CONTEXT`. If WebSearch is also unavailable, proceed without research context. Do not block the explore run. Do not narrate this step to the user.

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

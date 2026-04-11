---
name: debate
description: "Multi-model thinking: smart-routes to validate (adversarial review), pressure-test (strategic challenge or pre-mortem), or explore (divergent options). Includes pre-flight questions to break default framing. Use for decisions, strategy, and design uncertainty."
user-invocable: true
---

# /debate — Multi-Model Thinking

Smart-routed multi-model thinking. One entry point, three modes. Includes a pre-flight step that asks the right questions before running the AI — because the framing matters more than the model.

## Modes

| Mode | What it does | Models | Cost |
|------|-------------|--------|------|
| **validate** | Adversarial review: challenge → judge → refine | Multi-model (3 families) | ~$0.20-0.75 |
| **pressure-test** | Strategic counter-thesis (default) or pre-mortem failure analysis (`--frame premortem`) | Single-model | ~$0.03-0.08 |
| **explore** | 3 divergent directions + synthesis | Single-model (3 rounds + synth) | ~$0.10-0.20 |

## Procedure

### Step 1: Determine mode

Parse the user's input:

- If the user provided an explicit mode (`/debate --validate`, `/debate --pressure-test`, `/debate --explore`), use it. For pre-mortem, use `/debate --pressure-test --frame premortem`.
- If the input is a **question** (string, not a file path): → **explore**
- If the input is a **file** with code diffs or implementation details: → **validate**
- If the input is a **file** with thesis, strategy, or product recommendations: → **pressure-test**
- If the user says "pre-mortem", "why will this fail", or "failure analysis": → **pressure-test** with `--frame premortem`
- If ambiguous, show the user the options and ask:

```
This could go several ways:
1. **validate** — adversarial review (find flaws in the proposal)
2. **pressure-test** — strategic challenge (is this the right thing to build?)
3. **pressure-test --frame premortem** — failure analysis (why will this fail?)
4. **explore** — divergent thinking (what are the options?)

Which mode?
```

Store the answer as `MODE`.

### Step 2: Get topic

If the user provided a topic as an argument, use it. Otherwise derive from the input (filename stem, or ask).

Store as `TOPIC`.

### Step 3: Pre-flight discovery (explore and pressure-test only)

**Skip this step for validate mode.** Validate works on concrete artifacts. For pressure-test with `--frame premortem`, pre-flight is optional (the plan is usually concrete enough).

**If the user says "skip" or "just run it":** skip pre-flight and proceed.

**Auto-run pre-flight:** If the user says "just run it" or "you know enough" or "answer the questions yourself" — and you genuinely have enough context from memory, prior conversation, or the proposal file to answer the pre-flight questions substantively — then self-seed the pre-flight. State your assumed answers briefly (bullet list), let the user correct, then proceed. This avoids interrogating the user when you already know the situation.

#### Step 3a: Adaptive pre-flight (no classification menu)

Read `config/prompts/preflight-adaptive.md` for the full protocol.

**Do NOT present a classification menu.** Instead, read the user's question and adapt:

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

#### Step 3b: Compose context with dimensions (SILENT — do not narrate this step)

Compose the output in the format specified in `preflight-adaptive.md`. This is internal data assembly — never show the raw context block, DIMENSIONS format, or `--context` flag details to the user.

#### Step 3c: Research enrichment (explore mode only — SILENT)

**Skip this step** for validate and pressure-test modes. Also skip if the user opted out of search during pre-flight.

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

If PERPLEXITY_API_KEY is not set or the search fails: proceed without research context. Do not block the explore run.

This step is silent — do not narrate it to the user. The research context flows into debate.py via the existing --context flag.

### Step 4: Route to mode

#### Mode: validate

Full adversarial pipeline. Ask for security posture (1-5, default 3).

**Require proposal:** `tasks/<topic>-proposal.md` must exist. If missing, tell the user.

**Enrich context:**
```bash
python3.11 scripts/enrich_context.py --proposal tasks/<topic>-proposal.md --scope debate
```

**Challenge** (skip if `tasks/<topic>-debate.md` exists):
```bash
python3.11 scripts/debate.py --security-posture $POSTURE challenge \
  --proposal <enriched or original proposal> \
  --personas architect,security,pm \
  --enable-tools \
  --output tasks/<topic>-debate.md
```

**Judge** (skip if `tasks/<topic>-judgment.md` exists):
```bash
python3.11 scripts/debate.py --security-posture $POSTURE judge \
  --proposal tasks/<topic>-proposal.md \
  --challenge tasks/<topic>-debate.md \
  --model gpt-5.4 \
  --verify-claims \
  --output tasks/<topic>-judgment.md
```

**Refine** (skip if `tasks/<topic>-refined.md` exists):
```bash
python3.11 scripts/debate.py refine \
  --document tasks/<topic>-proposal.md \
  --judgment tasks/<topic>-judgment.md \
  --rounds 3 \
  --output tasks/<topic>-refined.md
```

Display summary table with artifact status.

#### Mode: pressure-test

Single-model strategic challenge. No judge, no refine — the response IS the value.

**Require proposal:** `tasks/<topic>-proposal.md` must exist.

```bash
python3.11 scripts/debate.py pressure-test \
  --proposal tasks/<topic>-proposal.md \
  --context "$PREFLIGHT_CONTEXT" \
  --output tasks/<topic>-pressure-test.md
```

Display the output to the user directly in the conversation (not just to a file).

#### Mode: explore

Single-model divergent exploration. No proposal needed — takes a question.

```bash
python3.11 scripts/debate.py explore \
  --question "<the user's question>" \
  --context "$PREFLIGHT_CONTEXT" \
  --directions 3 \
  --output tasks/<topic>-explore.md
```

Display the output to the user directly in the conversation (not just to a file).

#### Mode: pressure-test --frame premortem

Same as pressure-test but with a pre-mortem prompt: assumes the plan failed and writes the post-mortem from the future.

**Require plan:** `tasks/<topic>-proposal.md` or `tasks/<topic>-plan.md` must exist.

```bash
python3.11 scripts/debate.py pressure-test \
  --proposal tasks/<topic>-proposal.md \
  --frame premortem \
  --output tasks/<topic>-premortem.md
```

Display the output to the user directly in the conversation (not just to a file).

### Step 5: Summary

Display:
```
## /debate complete — [MODE] mode

| Artifact | Path | Status |
|----------|------|--------|
| [artifacts for this mode] | tasks/<topic>-*.md | done/failed |

[Mode-specific next step suggestion]
```

For validate mode, suggest: "Build the implementation, then run `/review <topic>`"
For pressure-test (challenge frame), suggest: "Revise the proposal based on the counter-thesis, or proceed if the thesis holds"
For pressure-test (premortem frame), suggest: "Address the top failure scenarios in your plan before proceeding"
For explore, suggest: "Pick a direction and write it up as `tasks/<topic>-proposal.md`, then `/debate --pressure-test` or `/debate --validate`"

## Degraded Mode

Each mode fails gracefully:
- **validate**: each stage is independently valuable (challenge only, challenge + judgment, all three)
- **pressure-test / explore**: single call, no partial state

Stop at the step that fails. Partial artifacts are valid.

## Internal Notes (SILENT — never narrate these to the user)

- Don't rush pre-flight. Don't explain why pre-flight matters.
- Each step checks for existing artifacts and skips if found.
- Always display thinking-mode output (explore, pressure-test, pre-mortem) directly in the conversation.
- Never narrate internal mechanics, cost estimates, model choices, or pipeline plumbing to the user.

---
name: debate
description: "Multi-model thinking: smart-routes to validate (adversarial review), pressure-test (strategic challenge), explore (divergent options), or pre-mortem (failure analysis). Includes pre-flight questions to break default framing. Use for decisions, strategy, and design uncertainty."
user-invocable: true
---

# /debate — Multi-Model Thinking

Smart-routed multi-model thinking. One entry point, multiple modes. Includes a pre-flight step that asks the right questions before running the AI — because the framing matters more than the model.

## Modes

| Mode | What it does | Models | Cost |
|------|-------------|--------|------|
| **validate** | Adversarial review: challenge → judge → refine | Multi-model (3 families) | ~$0.20-0.75 |
| **pressure-test** | Strategic counter-thesis and honest take | Single-model | ~$0.03-0.08 |
| **explore** | 3 divergent directions + synthesis | Single-model (3 rounds + synth) | ~$0.10-0.20 |
| **pre-mortem** | Assume it failed, write the post-mortem | Single-model | ~$0.03-0.08 |

## Procedure

### Step 1: Determine mode

Parse the user's input:

- If the user provided an explicit mode (`/debate --validate`, `/debate --pressure-test`, `/debate --explore`, `/debate --pre-mortem`), use it.
- If the input is a **question** (string, not a file path): → **explore**
- If the input is a **file** with code diffs or implementation details: → **validate**
- If the input is a **file** with thesis, strategy, or product recommendations: → **pressure-test**
- If ambiguous, show the user the options and ask:

```
This could go several ways:
1. **validate** — adversarial review (find flaws in the proposal)
2. **pressure-test** — strategic challenge (is this the right thing to build?)
3. **explore** — divergent thinking (what are the options?)
4. **pre-mortem** — failure analysis (why will this fail?)

Which mode?
```

Store the answer as `MODE`.

### Step 2: Get topic

If the user provided a topic as an argument, use it. Otherwise derive from the input (filename stem, or ask).

Store as `TOPIC`.

### Step 3: Pre-flight discovery (explore and pressure-test only)

**Skip this step for validate and pre-mortem modes.** Validate works on concrete artifacts. Pre-mortem takes a plan as-is.

For explore and pressure-test, the framing determines the output quality. Bad framing produces sophisticated variations on the wrong answer. 2-5 minutes of upfront discovery is worth it.

**If the user says "skip" or "just run it":** skip pre-flight and proceed. But note that the output quality will be lower.

#### Step 3a: Classify the thinking type

Ask the user:

```
Before we run, I need to understand the problem. What kind of thinking is this?

(A) **Product opportunity** — evaluating whether/how to build something for a market
(B) **Solo builder** — figuring out what to build for yourself or your workflow
(C) **Architectural decision** — deciding how something should work technically
```

Based on the answer, read the corresponding pre-flight file:

- **(A):** Read `config/prompts/preflight-product.md`
- **(B):** Read `config/prompts/preflight-solo-builder.md`
- **(C):** Read `config/prompts/preflight-architecture.md`

#### Step 3b: Route to the right question subset

Each pre-flight file has a **Routing** section that selects which 3 of 5 questions to ask based on the user's stage. Read the user's input and prior answers to determine the route. Skip questions already answered by what the user has said.

#### Step 3c: Ask questions ONE AT A TIME

**Do not dump all questions at once.** Ask one. Wait for the answer. Evaluate specificity.

For each question:
1. Ask the question conversationally (not as a formal numbered item)
2. Read the user's answer
3. Check against the **push-until** criteria in the pre-flight file
4. If the answer is vague or matches a **red flag**, push once with the suggested reframe
5. When the answer is specific enough, move to the next question

**Push style:** Conversational, not interrogative. "You said 'developers would find it useful' — but who specifically? Is there someone who'd be upset if this disappeared tomorrow?" Not "Your answer is too vague. Please be more specific."

**Maximum pushes per question:** 1. If the answer is still vague after one push, accept it and move on. Don't interrogate.

#### Step 3d: Compose context

After the questions, compose the answers into the context format specified at the bottom of the pre-flight file. This context becomes the `--context` flag on the `debate.py` command.

The pre-flight context REPLACES the category-anchored description as the primary input to the AI. This is the point — the user's specific, pushed-to-specific answers are better framing than whatever label they started with.

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

Display summary table with artifact status. Update pipeline manifest.

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

Update pipeline manifest.

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

Update pipeline manifest.

#### Mode: pre-mortem

Single-model prospective failure analysis.

**Require plan:** `tasks/<topic>-proposal.md` or `tasks/<topic>-plan.md` must exist.

```bash
python3.11 scripts/debate.py pre-mortem \
  --plan tasks/<topic>-proposal.md \
  --output tasks/<topic>-premortem.md
```

Display the output to the user directly in the conversation (not just to a file).

Update pipeline manifest.

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
For pressure-test, suggest: "Revise the proposal based on the counter-thesis, or proceed if the thesis holds"
For explore, suggest: "Pick a direction and write it up as `tasks/<topic>-proposal.md`, then `/debate --pressure-test` or `/debate --validate`"
For pre-mortem, suggest: "Address the top failure scenarios in your plan before proceeding"

## Degraded Mode

Each mode fails gracefully:
- **validate**: each stage is independently valuable (challenge only, challenge + judgment, all three)
- **pressure-test / explore / pre-mortem**: single call, no partial state

Stop at the step that fails. Partial artifacts are valid.

## Important Notes

- **Pre-flight is the highest-leverage step.** The user's answers to 5 questions determine whether the AI explores the right solution space or produces sophisticated variations on the wrong frame. Don't rush it.
- validate mode costs ~$0.20-0.75 per run (multi-model). Reserve for implementation review, code review, schema changes.
- pressure-test, explore, and pre-mortem cost ~$0.03-0.20 per run (single-model). Cheap enough to run casually on strategic questions.
- Each step checks for existing artifacts and skips if found. Re-running `/debate` after a partial failure resumes where it left off.
- validate uses GPT-5.4 as judge (different model family from Claude to avoid self-preference bias).
- explore uses forced sequential divergence — same model, explicitly different each round. This produces more diverse output than 3 different models (tested and verified).
- **Always display thinking-mode output (explore, pressure-test, pre-mortem) directly in the conversation.** The user should see results without opening a file.

---
name: investigate
description: |
  Structured root-cause analysis using cross-model debate, governance memory,
  and finding lifecycle tracking. Three modes: symptom (something broke),
  drift (behavior changed), claim (verify a claim). Embodies diagnostic-before-fix.
  Defers to: /audit (broad codebase archaeology), /pressure-test (adversarial pre-mortem),
  /think (problem discovery for new work).
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Agent
  - AskUserQuestion
---

# /investigate -- Structured Root-Cause Analysis

Six-phase investigation protocol: scope, gather evidence, pull context, form hypotheses,
test hypotheses with cross-model panel, route findings to governance docs.

## When to use

- Something is broken right now and you need to find why
- Behavior changed unexpectedly — find what diverged
- Verify a claim about the system ("does X actually work?")
- Post-incident analysis when the fix is unknown

## When NOT to use

- Broad codebase survey with no specific symptom → `/audit`
- Pre-mortem on a plan that hasn't shipped → `/pressure-test --premortem`
- Defining a new problem space → `/think discover`
- Code review of a diff → `/review`

## OUTPUT SILENCE -- HARD RULE

Between tool calls, emit ZERO text to the chat. No progress updates, no "checking...",
no intermediate results. The ONLY user-visible output is:
- The final investigation report presented at the end
- Questions asked via AskUserQuestion during Phase 1

**Exception:** Text immediately preceding an AskUserQuestion call is permitted.

## Interactive Question Protocol

1. **Text-before-ask:** Before every AskUserQuestion, output the question and options
   as regular markdown. Then call AskUserQuestion.
2. **Empty-answer guard:** If AskUserQuestion returns empty: re-prompt once. If still
   empty: pause — "Pausing — let me know when you're ready."
3. **Vague answer recovery:** If "whatever you think" / "up to you": state assumption
   and proceed.

## Procedure

### Phase 1: Scope

Parse the user's input to determine:

**Mode** (store as `MODE`):
- `/investigate` or `/investigate <topic>` → **symptom** (default)
- `/investigate --drift <topic>` or user says "changed", "used to work", "different now" → **drift**
- `/investigate --claim <topic>` or user says "verify", "does X work", "is it true" → **claim**

**Topic** (store as `TOPIC`):
- If the user provided a topic slug or file path, derive from it (lowercase, hyphens, max 40 chars).
- If no topic provided, ask:

  > **What are we investigating?**
  >
  > Describe the symptom, drift, or claim in one sentence. Include the area of the
  > codebase if you know it.

  Then call AskUserQuestion. Derive `TOPIC` from the response.

**Sanitize TOPIC:** lowercase alphanumeric + hyphens only. Strip `/`, `..`, spaces, special chars.

### Phase 2: Gather Evidence (Blind)

Collect evidence WITHOUT forming hypotheses. Like audit Phase 1 — observe, don't interpret.

Run these in parallel where possible:

**2a. Code inspection:**
- Grep/Glob for files related to `TOPIC` keywords
- Read the most relevant files (max 5 — the investigation target, its tests, its callers)
- `git log --oneline -15 -- <relevant-paths>` — what changed recently in this area?
- `git diff HEAD~5 -- <relevant-paths>` — recent diffs (if small enough)

**2b. Artifact freshness** (if `TOPIC` maps to an existing scope):
```bash
/opt/homebrew/bin/python3.11 scripts/artifact_check.py --scope <TOPIC> 2>/dev/null
```
If exit 0: parse JSON. Note stale artifacts, open material findings, missing artifacts.
If exit non-zero or no matching scope: skip silently.

**2c. Health checks** (run if MODE is `symptom`):
```bash
/opt/homebrew/bin/python3.11 scripts/check-current-state-freshness.py 2>/dev/null
/opt/homebrew/bin/python3.11 scripts/check-infra-versions.py 2>/dev/null
```
Note any staleness or version drift — these may be contributing factors.

**2d. Mode-specific gathering:**

- **symptom**: Look for error messages, stack traces, failing tests, broken state.
  Run relevant test commands if they exist. Check recent git commits for suspicious changes.
- **drift**: Compare current behavior to expected. `git log --all --oneline -20` to find
  when behavior diverged. Check for config changes, dependency updates, env changes.
- **claim**: Identify what evidence would confirm or refute the claim. Read the relevant
  code path end-to-end. Check if tests exist that exercise the claimed behavior.

**Write evidence to disk** as you gather it:
```
tasks/<TOPIC>-evidence.md
```
Append each piece of evidence with its source (file path, command, git ref). This preserves
progress if the session is interrupted.

### Phase 3: Context (Governance Memory)

Pull prior decisions, lessons, and findings related to this investigation area.

**3a. Recall search** — find related governance entries:
```bash
/opt/homebrew/bin/python3.11 scripts/recall_search.py <keyword1> <keyword2> <keyword3> \
  --files all --json --top-k 5
```
Extract 3-5 keywords from the symptom/topic. Parse JSON results.

**3b. Enrich context** — pull structured governance context:

Write a temp summary of the investigation to a scratch file:
```
# Investigation: <symptom description>
## Area
<relevant codebase areas from Phase 2a>
## Symptom
<what's broken/changed/claimed>
```

```bash
/opt/homebrew/bin/python3.11 scripts/enrich_context.py \
  --proposal <scratch-file> --scope all --top-k 5
```
Parse JSON. Retain relevant decisions and lessons for Phase 4.

**3c. Finding history** — check if this area has prior tracked findings:
```bash
/opt/homebrew/bin/python3.11 scripts/finding_tracker.py list --debate-id <TOPIC> 2>/dev/null
```
If findings exist, note their states. An "open" finding in the same area may be the root cause.

**Quality gate:** If Phase 3 surfaces a prior decision or lesson that directly explains
the symptom, flag it immediately — the investigation may already be answered.

### Phase 4: Hypothesize

Form **3 or more competing hypotheses** from the evidence gathered in Phases 2-3.

Each hypothesis MUST:
- State a specific cause ("X is broken because Y")
- Cite at least one piece of evidence from Phase 2 or 3
- Predict what additional evidence would confirm or refute it

Structure:
```
HYPOTHESIS A: <assertion>
  Evidence for: <what supports this>
  Evidence against: <what weakens this>
  Test: <what command/check would confirm or refute>

HYPOTHESIS B: <assertion>
  Evidence for: ...
  Evidence against: ...
  Test: ...

HYPOTHESIS C: <assertion>
  ...
```

**Mode-specific hypothesis framing:**

- **symptom**: "The root cause is [X] because [evidence]"
- **drift**: "The behavior changed because [X] happened at [time/commit]"
- **claim**: "[Claim] is [true/false] because [evidence shows X]"

**Minimum 3 hypotheses.** If you can only think of 2, the third should be "none of the
above — the cause is something not yet in evidence" with a note on where to look next.

Append hypotheses to `tasks/<TOPIC>-evidence.md`.

### Phase 5: Test Hypotheses

For each hypothesis, run the predicted test from Phase 4.

**5a. Targeted testing** — execute the specific check for each hypothesis:
- Read specific files, run specific commands, check specific state
- For each test, record: hypothesis, test performed, result, verdict (confirmed/weakened/refuted)

**5b. Cross-model evaluation** (run on the 1-2 strongest hypotheses):

Write the evidence file + strongest hypothesis to a temp investigation summary, then:

```bash
/opt/homebrew/bin/python3.11 scripts/debate.py review-panel \
  --models claude-opus-4-6,gemini-3.1-pro,gpt-5.4 \
  --prompt "You are reviewing a root-cause investigation. The investigator has gathered evidence and formed hypotheses. For each hypothesis presented: (1) Rate confidence 1-5 based on the evidence cited. (2) Identify any evidence that was missed or misinterpreted. (3) Suggest one additional test that would increase confidence. (4) State whether the root cause diagnosis is CONFIRMED, LIKELY, POSSIBLE, or UNSUPPORTED. Be terse. Disagree with each other if the evidence warrants it." \
  --input tasks/<TOPIC>-evidence.md
```

If exit 0: parse the panel's independent evaluations. If 2/3 models confirm the same
hypothesis → high confidence. If all 3 disagree → flag ambiguity, recommend further investigation.

If exit non-zero: note "Cross-model panel unavailable" and proceed with single-model assessment.

**5c. Score each hypothesis:**
- **Confirmed** — evidence + panel agree, no contradicting evidence
- **Likely** — evidence supports, panel mostly agrees, minor gaps
- **Possible** — some supporting evidence, significant gaps remain
- **Refuted** — evidence contradicts, or panel unanimously rejects

### Phase 6: Route Findings

**6a. Write the investigation report** to `tasks/<TOPIC>-investigation.md`:

```markdown
# Investigation: <title>

Generated by /investigate on <date>
Mode: <symptom|drift|claim>
Status: <RESOLVED|LIKELY|OPEN>

## Symptom
<what was reported>

## Evidence Collected
<bulleted list with sources — file:line, command output, git ref>

## Governance Context
<relevant prior decisions, lessons, findings — with IDs>

## Hypotheses Tested

### Hypothesis A: <assertion> — <CONFIRMED|LIKELY|POSSIBLE|REFUTED>
- Evidence: <cited>
- Test: <what was run>
- Result: <what happened>
- Panel: <consensus if run>

### Hypothesis B: ...

### Hypothesis C: ...

## Root Cause
<the confirmed/likely hypothesis, stated clearly>
<or: "Inconclusive — remaining unknowns listed below">

## Recommended Next Steps
<what to do — fix approach, further investigation, or escalation>
<DO NOT implement the fix — this skill diagnoses, it does not treat>

## Routed Findings
<what was persisted where — finding tracker entries, lessons, decisions>
```

**6b. Persist findings** — if the investigation produced actionable findings:

For surprises or gotchas discovered during investigation:
- If it's a recurring pattern → note for `tasks/lessons.md` (user decides whether to add)
- If it reveals a decision that should be documented → note for `tasks/decisions.md`

**6c. Clean up** — remove scratch files:
```bash
rm -f tasks/<TOPIC>-evidence.md /tmp/investigate-*.md
```

### Phase 7: Present Results

Display the investigation report in the conversation. Then:

> **Investigation complete.**
>
> | Artifact | Path | Status |
> |----------|------|--------|
> | Investigation report | `tasks/<TOPIC>-investigation.md` | <RESOLVED/LIKELY/OPEN> |
> | Panel evaluation | <ran/skipped> | <consensus if ran> |
> | Governance hits | <count> decisions, <count> lessons | <relevant/none> |
>
> **Root cause:** <one-line summary>
>
> **Next steps:**
> - A) Fix it — proceed to `/plan` with the root cause as input
> - B) Investigate further — dig deeper into <weakest area>
> - C) Done — the report is sufficient

Then call AskUserQuestion with the same options.

Report status: **DONE** (resolved), **DONE_WITH_CONCERNS** (likely but gaps remain),
or **NEEDS_CONTEXT** (inconclusive, needs more information).

## Degraded Modes

- **debate.py unavailable:** Skip Phase 5b cross-model panel. Proceed with single-model
  assessment. Note in report: "Cross-model panel: unavailable."
- **recall_search.py / enrich_context.py unavailable:** Skip Phase 3. Note in report:
  "Governance context: unavailable."
- **finding_tracker.py unavailable:** Skip Phase 6b tracking. Document findings in
  report only.
- **All tools available but inconclusive:** Report status OPEN with specific unknowns
  and what tests remain. Do not guess.

## Rules

- **Evidence before diagnosis.** Phase 2 (gather) MUST complete before Phase 4 (hypothesize).
  Do not form hypotheses from memory or conversation history alone.
- **Cite everything.** Every hypothesis must cite specific evidence. Every evidence item
  must have a source (file path, command, git ref, governance doc ID).
- **Minimum 3 hypotheses.** Premature convergence on one cause is the #1 investigation failure mode.
- **Do not fix.** This skill diagnoses. It recommends a fix approach but does not
  implement it. The user decides whether to proceed to `/plan` or fix directly.
- **Governance context is advisory.** Prior decisions and lessons inform the investigation
  but do not override current evidence. If current evidence contradicts a prior decision,
  flag the contradiction — don't suppress it.
- **Clean scratch files.** Evidence files are working state, not deliverables.
  The investigation report is the deliverable.

---
name: think
description: "Problem definition in two modes. Use when structuring a problem before planning or challenging. 'discover' runs full problem discovery with forcing questions, premise challenges, alternatives, and writes a design doc. 'refine' runs 5 forcing questions for features or pass-through for bugfixes. Defers to: /challenge (scope gate), /plan (implementation spec), /elevate (ambition review)."
version: 1.0.0
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Write
  - Edit
  - Agent
  - AskUserQuestion
---

## Safety Rules

- NEVER skip forcing questions to reach a conclusion faster. The questions are the value.
- Do not commit to a direction — present options and let the user choose.
- NEVER fabricate demand evidence or user quotes.

## Procedure

## Interactive Question Protocol

These rules apply to EVERY AskUserQuestion call in this skill:

1. **Text-before-ask:** Before every AskUserQuestion, output the question, all options,
   and context as regular markdown. Then call AskUserQuestion. Options persist if the
   user discusses rather than picks immediately.

2. **Recommended-first:** Mark the recommended option with "(Recommended)" and list it
   as option A. If no option is clearly better (depends on user intent), omit the marker.

3. **Empty-answer guard:** If AskUserQuestion returns empty/blank: re-prompt once with
   "I didn't catch a response — here are the options again:" and the same options.
   If still empty: pause the skill — "Pausing — let me know when you're ready."
   Do NOT auto-select any option.

4. **Vague answer recovery:** If the user says "whatever you think" / "either is fine" /
   "up to you": state "Going with [recommended] since no strong preference. Noted as
   assumption." Proceed with recommended.

5. **Topic sanitization:** Before constructing any file path with `<topic>`, sanitize to
   lowercase alphanumeric + hyphens only (`[a-z0-9-]`). Strip `/`, `..`, spaces, and
   special characters. This prevents path traversal in scratch/landscape file writes.

## OUTPUT SILENCE -- HARD RULE

Between tool calls, emit ZERO text to the chat. No progress updates, no "checking...",
no intermediate results. The ONLY user-visible output is the single formatted block
at the end of each phase and the final design doc or brief presentation.

**Exception:** Text-before-ask output immediately preceding an AskUserQuestion call is permitted (see Interactive Question Protocol above).

## Mode Selection

Parse the invocation argument:

- `/think discover` -- full problem discovery (Phase 0-6)
- `/think refine` -- lightweight sanity check (Phase R0-R)
- `/think` (no argument) -- output the modes as markdown text before asking:

  Output:
  > **What kind of thinking do you need?**
  >
  > If the task is a new feature, big idea, or unclear scope, recommend discover.
  > If it's a bugfix, small feature, or well-understood change, recommend refine.
  > Mark the contextually appropriate option "(Recommended)".
  >
  > - **A) Full problem discovery** -- reframe what we're building, surface real pain, explore approaches (10-15 min)
  > - **B) Quick sanity check** -- forcing questions to sharpen a feature before planning (3-5 min)

  Then call AskUserQuestion with the same options. A routes to discover. B routes to refine.

---

# DISCOVER MODE

## Phase 0: Context Assessment

Before running intake, scan the conversation for context already established.

**Check each:**

| Signal | Look for | If found |
|--------|----------|----------|
| Problem statement | User described what they're building/solving | State in one line. Satisfies Phase 2A Q1-Q2 or Phase 2B openers. |
| Mode | Customers/revenue/users → Product. Hack/side-project/infra → Builder. | Skip mode question (Phase 1 step 5). |
| Evidence | Specific data, user behaviors, failure modes, examples | Reference them. Satisfies diagnostic questions. |
| Approach | Solution direction proposed or discussed | Include as candidate in Phase 4. |

**Output before proceeding:**

```
Context from conversation:
- Problem: {one-line summary, or "not yet clear"}
- Mode: {Product / Builder / unclear}
- Evidence: {what's established, or "none yet"}
- Approach: {direction discussed, or "open"}
- Gaps: {unanswered intake questions, or "none — all covered"}
```

**Routing:**
- All intake questions answered → skip Phase 2A/2B entirely. Run Phase 1 → 1.5 → 3 → 4 → 5 (synthesis).
- Some answered → ask ONLY unanswered questions in Phase 2A/2B. Smart-skip the rest.
- No conversation context → full sequence as normal.

Phase 1 (codebase context) and Phase 1.5 (governance context) always run — they pull from disk, not conversation.

---

## Phase 1: Context Gathering

1. Read `docs/current-state.md` and `tasks/session-log.md` (last entry) if they exist.
2. Run `git log --oneline -20` and `git diff --stat` to understand recent context.
3. Use Grep/Glob to map codebase areas relevant to the user's request.
4. Check for existing design docs:
   ```bash
   ls -t tasks/*-design.md 2>/dev/null | head -5
   ```
   If design docs exist, list them: "Prior designs: [titles + dates]"

5. Output the following as markdown text before asking. If context suggests one mode
   (e.g., mentions customers/revenue → Product; mentions "fun"/"hack" → Builder),
   mark that option "(Recommended)". If ambiguous, omit the marker.

   > **Before we dig in -- what's your goal with this?**
   >
   > - **A) Building a product** -- startup, internal tool, something with real users
   > - **B) Side project** -- hackathon, open source, learning, having fun

   Then call AskUserQuestion with the same options.
   A routes to **Product mode** (Phase 2A). B routes to **Builder mode** (Phase 2B).

6. For product mode only, assess stage:
   - Pre-product (idea, no users)
   - Has users (not yet paying)
   - Has paying customers

---

## Phase 1.5: Governance Context (discover mode only)

Pull relevant prior decisions and lessons so problem framing doesn't rediscover solved problems or propose rejected approaches.

1. Write a temp file summarizing the user's request from Phase 1:
   ```
   # Problem: <user's stated problem/goal>
   ## Area
   <relevant codebase areas identified in Phase 1 step 3>
   ```

2. Run enrichment:
   ```bash
   python3.11 scripts/enrich_context.py --proposal <temp summary file> --scope define
   ```

3. **Quality gate:** Parse the JSON output. If both `lessons` and `decisions` arrays are empty, skip — no governance context to surface.

4. If enrichment returned results, retain as governance context for use in later phases. **Scoping:** Prefer decisions over lessons. Focus on strategic/high-level items (rejected approaches, architectural choices, scope decisions) rather than implementation-level details.

5. **How to use during later phases:**
   - During Phase 2A/2B forcing questions: if a question touches an area where a prior decision exists, surface it: "Note: Prior decision D{N} addressed {topic} — {one-line summary}."
   - During Phase 3 (Premise Challenge): include relevant decisions as evidence for or against premises being challenged.
   - Do NOT dump all governance context at once — surface items when they are relevant to the specific question or premise under discussion.

6. If `enrich_context.py` does not exist or errors, continue without governance context. This step is additive.

---

## Phase 2A: Product Mode -- Diagnostic

### Posture

Be direct to the point of discomfort. Take a position on every answer and state what
evidence would change your mind. The first answer is usually the polished version --
the real answer comes after the second push.

Never say during the diagnostic:
- "That's an interesting approach" -- take a position instead
- "There are many ways to think about this" -- pick one
- "You might want to consider..." -- say "This is wrong because..." or "This works because..."
- "That could work" -- say whether it WILL work and what evidence is missing
- "I can see why you'd think that" -- if they're wrong, say they're wrong and why

**Always do:**
- Take a position on every answer. State your position AND what evidence would change it. This is rigor -- not hedging, not fake certainty.
- Challenge the strongest version of the user's claim, not a strawman.

### Pushback Patterns -- How to Push

These examples show the difference between soft exploration and rigorous diagnosis:

**Pattern 1: Vague market -> force specificity**
- User: "I'm building an AI tool for developers"
- BAD: "That's a big market! Let's explore what kind of tool."
- GOOD: "There are 10,000 AI developer tools right now. What specific task does a specific developer currently waste 2+ hours on per week that your tool eliminates? Name the person."

**Pattern 2: Social proof -> demand test**
- User: "Everyone I've talked to loves the idea"
- BAD: "That's encouraging! Who specifically have you talked to?"
- GOOD: "Loving an idea is free. Has anyone offered to pay? Has anyone asked when it ships? Has anyone gotten angry when your prototype broke? Love is not demand."

**Pattern 3: Platform vision -> wedge challenge**
- User: "We need to build the full platform before anyone can really use it"
- BAD: "What would a stripped-down version look like?"
- GOOD: "That's a red flag. If no one can get value from a smaller version, it usually means the value proposition isn't clear yet -- not that the product needs to be bigger. What's the one thing a user would pay for this week?"

**Pattern 4: Growth stats -> vision test**
- User: "The market is growing 20% year over year"
- BAD: "That's a strong tailwind. How do you plan to capture that growth?"
- GOOD: "Growth rate is not a vision. Every competitor in your space can cite the same stat. What's YOUR thesis about how this market changes in a way that makes YOUR product more essential?"

**Pattern 5: Undefined terms -> precision demand**
- User: "We want to make onboarding more seamless"
- BAD: "What does your current onboarding flow look like?"
- GOOD: "'Seamless' is not a product feature -- it's a feeling. What specific step in onboarding causes users to drop off? What's the drop-off rate? Have you watched someone go through it?"

### The Six Forcing Questions

Ask ONE AT A TIME via AskUserQuestion. Prefix each question with `[Q N/M]` where N is
the current question number and M is the total questions for this stage (from the
smart-route table below). Push on each until the answer is specific and evidence-based.
Smart-route based on product stage:

- Pre-product: Q1, Q2, Q3
- Has users: Q2, Q4, Q5
- Has paying customers: Q4, Q5, Q6
- Pure engineering/infra: Q2, Q4 only

#### Q1: Demand Reality
"What's the strongest evidence you have that someone actually wants this -- not
'is interested,' not 'signed up for a waitlist,' but would be genuinely upset if
it disappeared tomorrow?"

Push until you hear: specific behavior, someone paying, someone building their
workflow around it. Red flags: "People say it's interesting." "We got waitlist signups."

After Q1, check framing: are key terms defined? What assumptions does the answer
take for granted? Is there evidence of actual pain or is this hypothetical?
If imprecise, reframe: "Let me try restating what I think you're building: [reframe].
Does that capture it?"

#### Q2: Status Quo
"What are your users doing right now to solve this problem -- even badly? What does
that workaround cost them?"

Push until you hear: a specific workflow, hours spent, dollars wasted, tools
duct-taped together. Red flag: "Nothing -- there's no solution." If nothing exists,
the problem probably isn't painful enough.

#### Q3: Desperate Specificity
"Name the actual human who needs this most. What's their title? What gets them
promoted? What gets them fired?"

Push until you hear: a name, a role, a specific consequence. Red flags: category-level
answers like "Healthcare enterprises" or "Marketing teams." You can't email a category.

#### Q3.5: Pre-Mortem
"Imagine we built this and it failed. Not a little -- spectacularly. What went wrong?"

Push until you hear: specific failure modes (market miss, wrong user, adoption cliff,
technical dead-end), not vague "people didn't adopt it." Red flags: only technical
failures listed -- market and behavioral failures are usually deadlier.

**Scope:** Product mode, pre-product and has-users stages only. Skip for paying-customers
stage (they already have real failure data). Skip for Builder mode (pre-mortem kills
creative energy at the wrong moment).

#### Q4: Narrowest Wedge
"What's the smallest possible version of this that someone would pay real money
for -- this week, not after you build the platform?"

Push until you hear: one feature, one workflow, something shippable in days.
Red flag: "We need to build the full platform first."

Bonus push: "What if the user didn't have to do anything at all to get value?
No login, no integration, no setup."

**Intrapreneurship adaptation:** For internal projects, reframe as: "What's the
smallest demo that gets your VP/sponsor to greenlight the project?"

#### Q5: Observation & Surprise
"Have you actually sat down and watched someone use this without helping them?
What did they do that surprised you?"

Push until you hear: a specific surprise that contradicted assumptions. Red flags:
"We sent out a survey." "Nothing surprising." The gold: users doing something
the product wasn't designed for.

#### Q6: Future-Fit
"If the world looks meaningfully different in 3 years -- and it will -- does your
product become more essential or less?"

Push until you hear: a specific claim about how their users' world changes.
Red flag: "The market is growing 20% per year." Growth rate is not a vision.

**Intrapreneurship adaptation:** Reframe as: "Does this survive a reorg -- or does
it die when your champion leaves?"

**Smart-skip:** If earlier answers already cover a later question, skip it.

**Incremental saves:** After each answered question, append the Q&A pair to
`tasks/<topic>-design-scratch.md` (create if needed). This preserves progress if the
session is interrupted.

**Escape hatch:** If the user says "just do it" or expresses impatience:
- First time: "The hard questions are the value. Let me ask two more." Consult
  the stage routing table, ask the 2 most critical remaining questions.
- Second time: respect it, proceed to Phase 3 immediately.
- If user provides a fully formed plan with real evidence, skip to Phase 3.

---

## Phase 2B: Builder Mode -- Design Partner

### Posture

Enthusiastic, opinionated collaborator. Help them find the most exciting version
of their idea. Suggest things they might not have thought of.

### Questions (generative, not interrogative)

Ask ONE AT A TIME via AskUserQuestion. Prefix each question with `[Q N/5]` where N is
the current question number (adjust M downward if smart-skipping):

- "What's the coolest version of this? What would make it genuinely delightful?"
- "Who would you show this to? What would make them say 'whoa'?"
- "What's the fastest path to something you can actually use or share?"
- "What existing thing is closest to this, and how is yours different?"
- "What would you add if you had unlimited time? What's the 10x version?"

Smart-skip if the initial prompt already answers a question.

**Escape hatch:** If user says "just do it" or provides a full plan, fast-track
to Phase 4 (Alternatives). Still run Phase 3 and Phase 4.

**Mode upgrade:** If the user starts in builder mode but mentions customers, revenue,
or fundraising, switch to Product mode naturally: "Okay, now we're talking -- let me
ask you some harder questions."

---

## Phase 2.5: Related Design Discovery

After the user states the problem (first question in Phase 2A or 2B), search existing
design docs for keyword overlap.

Extract 3-5 significant keywords from the user's problem statement and grep across
existing design docs:
```bash
grep -li "keyword1\|keyword2\|keyword3" tasks/*-design.md 2>/dev/null
```

If matches found, read the matching design docs and surface them:
- "FYI: Related design found -- '{title}' on {date}. Key overlap: {1-line summary of relevant section}."
- Ask via AskUserQuestion: "Should we build on this prior design or start fresh?"

If no matches found, proceed silently.

---

## Phase 2.75: Landscape Awareness

After understanding the problem through questioning, search for what the world thinks.
This is NOT competitive research (that's /design consult's job). This is
understanding conventional wisdom so you can evaluate where it's wrong.

**Privacy gate:** Before searching, use AskUserQuestion:
> I'd like to search for what the world thinks about this space to inform our
> discussion. This sends generalized category terms (not your specific idea) to
> a search provider (Perplexity). OK to proceed?
> A) Yes, search away
> B) Skip -- keep this session private

If B: skip this phase entirely and proceed to Phase 3. Use only in-distribution knowledge.

When searching, use **generalized category terms** -- never the user's specific product
name, proprietary concept, or stealth idea. For example, search "task management app
landscape" not "SuperTodo AI-powered task killer."

**Product mode:** Run via Bash:
```bash
export $(grep -m1 '^PERPLEXITY_API_KEY=' .env) && python3.11 scripts/research.py \
  --sync --model sonar \
  --system "Return a concise landscape overview: key players, common approaches, known failure modes, and recent trends. No marketing language." \
  -o tasks/<topic>-landscape.md \
  "[problem space] landscape: existing approaches, common mistakes, why incumbents fail or succeed"
```

**Builder mode:** Run via Bash:
```bash
export $(grep -m1 '^PERPLEXITY_API_KEY=' .env) && python3.11 scripts/research.py \
  --sync --model sonar \
  --system "Return a concise landscape overview: existing solutions, open source alternatives, and best current approaches. No marketing language." \
  -o tasks/<topic>-landscape.md \
  "[thing being built] existing solutions and open source alternatives"
```

Replace `<topic>` with the actual topic slug. Replace bracketed query terms with
generalized category terms derived from the user's problem statement.

**Fallback:** If `PERPLEXITY_API_KEY` is not set in `.env` or `research.py` fails,
note: "Research unavailable -- proceeding with in-distribution knowledge only." and
continue to Phase 3.

Read the research output from `tasks/<topic>-landscape.md` and run the three-layer synthesis:
- **[Layer 1]** What does everyone already know about this space?
- **[Layer 2]** What did the research surface about current discourse, key players, and approaches?
- **[Layer 3]** Given what WE learned in Phase 2A/2B -- is there a reason the conventional approach is wrong?

**Eureka check:** If Layer 3 reasoning reveals a genuine insight, name it: "EUREKA:
Everyone does X because they assume [assumption]. But [evidence from our conversation]
suggests that's wrong here. This means [implication]."

If no eureka moment exists, say: "The conventional wisdom seems sound here. Let's build
on it." Proceed to Phase 3.

**Important:** This search feeds Phase 3 (Premise Challenge). If you found reasons the
conventional approach fails, those become premises to challenge. If conventional wisdom
is solid, that raises the bar for any premise that contradicts it.

**Landscape write:** `research.py -o` writes findings directly to `tasks/<topic>-landscape.md`.
Downstream skills (/elevate, /design consult) can reuse without repeating research.

---

## Phase 3: Premise Challenge

Before proposing solutions, challenge the premises:

1. Is this the right problem? Could a different framing yield a simpler or more impactful solution?
2. What happens if we do nothing? Real pain point or hypothetical?
3. What existing code already partially solves this? Map reusable patterns and flows.
4. If the deliverable is a new artifact (CLI, library, container, app): how will users get it?
   Distribution is part of the design.
5. Product mode only: synthesize the diagnostic evidence from Phase 2A. Does it support
   this direction? Where are the gaps?

Output premises as clear statements:
```
PREMISES:
1. [statement] -- agree/disagree?
2. [statement] -- agree/disagree?
3. [statement] -- agree/disagree?
```

Use AskUserQuestion to confirm. If the user disagrees, revise and loop back.

---

## Phase 3.5: Independent Second Opinion (optional)

Use AskUserQuestion:

> Want a second opinion from an independent perspective? A separate reviewer evaluates
> your problem statement, answers, and premises from a fresh angle.
> Takes 1-2 minutes.
> A) Yes, get a second opinion
> B) No, proceed to alternatives

If B: skip. Remember that the second opinion did NOT run (affects design doc).

If A: assemble project context from disk, then write a structured summary to a temp file.

**Project context assembly (SILENT — do not narrate):**
1. Read `docs/current-state.md` fresh — extract current phase, active work, and relevant subsystem. Stop when sufficient to identify the project and subsystem (ceiling ~80 lines).
2. Read `tasks/session-log.md` (last 2–3 relevant entries) — summarize the recent work arc including decisions and pivots (ceiling ~50 lines).
3. Optionally run `python3.11 scripts/enrich_context.py --proposal tasks/<topic>-design-scratch.md --scope define` if the scratch file exists. Include relevant decisions and lessons (ceiling ~20 lines).

**Temp file contents:**
- `## Project Context` — from current-state.md summary
- `## Recent Context` — from session-log summary
- `## Prior Decisions` — from enrich_context.py output, if any
- Mode (Product or Builder)
- Problem statement
- Key Q&A answers (1-2 sentences each, with verbatim user quotes)
- Agreed premises
- Codebase context from Phase 1

**Product mode prompt:** "You are an independent technical advisor reviewing a product
discovery conversation. Your job: 1) Steelman what they're building in 2-3 sentences.
2) What ONE thing from their answers reveals the most about what they should actually
build? Quote it. 3) Name ONE premise you think is wrong and what evidence would prove
you right. 4) If you had 48 hours and one engineer to build a prototype, what would
you build? Be direct. Be terse."

**Builder mode prompt:** "You are an independent technical advisor reviewing a builder
discovery conversation. Your job: 1) What's the COOLEST version they haven't considered?
2) What ONE thing reveals what excites them most? Quote it. 3) What existing project
gets them 50% there? 4) If you had a weekend, what would you build first? Be direct."

Run via Bash:
```bash
TMPFILE=$(mktemp /tmp/define-summary-XXXXXX.md)
# Write the structured summary to $TMPFILE
/opt/homebrew/bin/python3.11 scripts/debate.py review \
  --persona pm \
  --prompt "<mode-specific prompt above>" \
  --input "$TMPFILE"
rm -f "$TMPFILE"
```

**If exit 0:** Present review findings verbatim. Then synthesize: where you agree,
where you disagree, whether any challenged premise changes the recommendation.

**If exit non-zero:** "Independent second opinion unavailable. Proceeding without it."
Note in design doc that second opinion did not run.

If a premise was challenged, ask the user whether to revise it.

---

## Phase 4: Alternatives Generation (MANDATORY)

Produce 2-3 distinct implementation approaches:

```
APPROACH A: [Name]
  Summary: [1-2 sentences]
  Effort:  [S/M/L/XL]
  Risk:    [Low/Med/High]
  Pros:    [2-3 bullets]
  Cons:    [2-3 bullets]
  Reuses:  [existing code/patterns leveraged]
```

Rules:
- At least 2 approaches required. 3 preferred for non-trivial designs.
- One must be **"minimal viable"** (fewest files, smallest diff, ships fastest).
- One must be **"ideal architecture"** (best long-term trajectory).
- If the second opinion proposed a prototype, consider it as a starting point
  for a creative/lateral approach.

**RECOMMENDATION:** Choose [X] because [one-line reason].

Output approaches as a markdown table before asking. Mark the recommended approach
with "(Recommended)". Example format:

| | Approach A (Recommended) | Approach B | Approach C |
|---|---|---|---|
| Summary | ... | ... | ... |
| Effort | S | M | L |
| Risk | Low | Med | High |
| Pros | ... | ... | ... |
| Cons | ... | ... | ... |
| Reuses | ... | ... | ... |

Then call AskUserQuestion with the approach options. Do NOT proceed without user approval.

---

## Phase 5: Design Doc

Determine the topic slug from the user's problem statement (lowercase, hyphens, max 40 chars).

Check for existing design docs on this topic:
```bash
ls -t tasks/*-design.md 2>/dev/null | head -5
```

If a prior design doc exists for the same topic, note it in a `Supersedes:` field.

Write to `tasks/<topic>-design.md`:

### Product mode template:

```markdown
# Design: {title}

Generated by /think discover on {date}
Branch: {branch}
Status: DRAFT
Mode: Product
Supersedes: {prior filename -- omit if first design}

## Problem Statement
{from Phase 2A}

## Demand Evidence
{from Q1 -- specific quotes, numbers, behaviors}

## Status Quo
{from Q2 -- concrete current workflow}

## Target User & Narrowest Wedge
{from Q3 + Q4 -- specific human and smallest payable version}

## Premises
{from Phase 3}

## Independent Perspective
{from Phase 3.5 -- omit section entirely if second opinion did not run}

## Approaches Considered
### Approach A: {name}
{from Phase 4}
### Approach B: {name}
{from Phase 4}

## Recommended Approach
{chosen approach with rationale}

## Open Questions
{unresolved questions}

## Success Criteria
{measurable criteria}

## Distribution Plan
{how users get it -- omit if web service with existing pipeline}

## Dependencies
{blockers, prerequisites}

## Next Action
{one concrete thing to do next -- not "go build it"}
```

### Builder mode template:

```markdown
# Design: {title}

Generated by /think discover on {date}
Branch: {branch}
Status: DRAFT
Mode: Builder
Supersedes: {prior filename -- omit if first design}

## Problem Statement
{from Phase 2B}

## What Makes This Cool
{core delight or "whoa" factor}

## Premises
{from Phase 3}

## Independent Perspective
{from Phase 3.5 -- omit section entirely if second opinion did not run}

## Approaches Considered
### Approach A: {name}
{from Phase 4}
### Approach B: {name}
{from Phase 4}

## Recommended Approach
{chosen approach with rationale}

## Open Questions
{unresolved questions}

## Success Criteria
{what "done" looks like}

## Next Steps
{concrete build tasks -- first, second, third}
```

---

## Phase 5.5: Spec Review

Run a multi-persona review panel on the design doc. The panel provides independent
perspectives from different reviewer archetypes — anonymized and position-randomized.

**Context wrapping (SILENT — do not narrate):** Before sending the design doc to external
models, wrap it with project context so reviewers can evaluate feasibility and completeness
against the actual project state — not in a vacuum.

1. Read `docs/current-state.md` fresh — extract current phase, active work, and relevant subsystem. Stop when sufficient to identify the project and subsystem (ceiling ~80 lines).
2. Read `tasks/session-log.md` (last 2–3 relevant entries) — summarize the recent work arc including decisions and pivots (ceiling ~50 lines).
3. Optionally run `python3.11 scripts/enrich_context.py --proposal <design-doc-path> --scope define` if the design doc exists on disk. Include relevant decisions and lessons (ceiling ~20 lines).
4. Create a wrapped temp copy:

```bash
WRAPPED_DOC=$(mktemp /tmp/think-spec-review-XXXXXX.md)
# Write project context header
cat > "$WRAPPED_DOC" << 'CTX_EOF'
## Project Context
<project description from CLAUDE.md + current-state.md summary>

## Recent Context
<session-log summary>

## Prior Decisions
<enrich_context.py output, if any>

---
CTX_EOF
# Append the original design doc
cat <design-doc-path> >> "$WRAPPED_DOC"
```

Use `$WRAPPED_DOC` as the `--input` argument below. Clean up after review completes.

```bash
/opt/homebrew/bin/python3.11 scripts/debate.py review \
  --models claude-opus-4-6,gemini-3.1-pro,gpt-5.4 \
  --enable-tools \
  --allowed-tools check_code_presence,read_config_value \
  --prompt "Read this design document and review on 5 dimensions: Completeness, Consistency, Clarity, Scope (YAGNI?), Feasibility. For each dimension: PASS or list specific issues with fixes. Return a quality score (1-10). You have access to read-only verifier tools (check_code_presence, read_config_value) to fact-check claims about the current system. The document begins with project context so you can evaluate against the actual project state." \
  --input "$WRAPPED_DOC"
rm -f "$WRAPPED_DOC"
```

If debate.py fails or is unavailable, fall back to single-model analysis using the session model.

**If exit 0:** Parse the anonymous reviews (Reviewer A/B/C). If any reviewer flags
issues, fix each in the document. Re-run panel (max 3 iterations). If same issues
recur across iterations, persist as "## Reviewer Concerns" in the document.

**If exit non-zero (all failed):** "Spec review unavailable." Note in design doc.

**If partial (some reviewers responded — check stderr JSON):** Use available reviews,
note partial coverage in design doc.

Report: "Doc survived N rounds of review. M issues caught and fixed. Quality: X/10."

---

## Phase 6: Handoff

Output the following as markdown text, then call AskUserQuestion with the same options:

> **Design doc ready for review.**
>
> - **A) Approve** -- mark Status: APPROVED, proceed
> - **B) Revise** -- specify sections to change (loop back)
> - **C) Start over** -- return to Phase 2

Once approved, proceed to Phase 6.5 (PRD Generation).

---

## Phase 6.5: PRD Handoff

After the design doc is approved, suggest PRD generation:

> **Design doc complete. Want to generate a PRD?**
>
> - **A) Yes** (Recommended) — run `/prd` to generate requirements from the design doc
> - **B) Skip** — I'll handle the PRD separately

Then call AskUserQuestion. If A: invoke `/prd`. If B: proceed to Phase 6.6.

**Note:** The full PRD generation procedure lives in `/prd` (standalone skill). This
keeps /think discover focused on problem discovery and prevents context-budget dropout
that caused 100% Phase 6.5 skip rate when the procedure was inlined here.

---

## Phase 6.6: Handoff

Output the next-step options as markdown text. Mark the contextually
appropriate option "(Recommended)" -- if the design has scope uncertainty, recommend
/challenge; if scope is clear and ambitious, recommend /elevate; if straightforward,
recommend /plan. Then call AskUserQuestion:

> **Design doc written to `tasks/<topic>-design.md`.{prd_note} What's next?**
>
> - **A) `/elevate`** -- stress-test scope and ambition
> - **B) `/challenge`** -- gate whether to build this
> - **C) `/plan`** -- go straight to planning

Where `{prd_note}` is ` PRD generated at docs/project-prd.md.` if the PRD was
written in Phase 6.5, or empty string if skipped.

Report status: **DONE** with evidence (file path, quality score).

---

# REFINE MODE

## Phase R0: Context Assessment

Before running forcing questions, scan the conversation for context already established.

**Check each forcing question against conversation:**

| Question | Signal that it's answered |
|----------|--------------------------|
| Q1: What outcome? | User stated the goal or desired behavior |
| Q2: Current workaround? | Existing workflow or cost discussed |
| Q3: Smallest version? | MVP or testable scope defined |
| Q4: How does this serve the user? | Workflow impact described |
| Q5: What does the product become? | Alignment with direction discussed |

**Output before proceeding (only if conversation has relevant context):**

```
From conversation: {one-line problem summary}
Already answered: {list of Qs with one-line answers}
Still need: {remaining Qs, or "none — writing brief directly"}
```

**Routing:**
- All answered → skip to Phase R step 5 (synthesis). Write the brief directly.
- Some answered → ask only unanswered questions. Smart-skip the rest.
- No context → full sequence as normal.

---

## Phase R: Lightweight Sanity Check

1. Read `docs/current-state.md` and `tasks/session-log.md` (last entry) if they exist.
2. Classify the task:
   - **Bugfix with obvious root cause** -- skip questions, write brief immediately:
     "This is a bugfix. Root cause: [X]. Fix: [Y]. Writing brief."
     Write `tasks/<topic>-think.md` and proceed to handoff.
   - **Docs, config, trivial refactor** -- same: skip questions, write brief.
   - **New feature or non-trivial change** -- proceed to forcing questions.

3. Ask forcing questions ONE AT A TIME via AskUserQuestion. Prefix each question with
   `[Q N/M]` where N is the current question number and M is the total (adjust M
   downward if smart-skipping):

   - "What outcome are you after?" (the goal, not the solution)
   - "What's the current workaround? What does it cost?" (tests urgency)
   - "What's the smallest version that tests whether this works?" (MVP)
   - "How does this serve the user?" (workflow impact)
   - "What does the product become with this?" (new features only -- tests alignment)

   Smart-skip if the user's initial prompt already answers a question.

4. **Escape hatch:** If the user declines to answer twice, ask the single most
   critical remaining question, then proceed to synthesis.

5. Synthesize and write `tasks/<topic>-think.md`:

```markdown
# Brief: {title}

Generated by /think refine on {date}

## Problem Statement
{what we're solving}

## Proposed Approach
{direction from the conversation}

## Key Assumptions
{what must be true for this to work}

## Risks
{what could go wrong}

## Simplest Testable Version
{the MVP -- smallest thing that validates the approach}
```

6. Output the next-step options as markdown text. If the task introduces new
   abstractions or scope expansion, mark /challenge "(Recommended)". If
   straightforward, mark /plan "(Recommended)". Then call AskUserQuestion:

> **Brief written to `tasks/<topic>-think.md`. What's next?**
>
> - **A) `/challenge`** -- gate scope (recommended if new abstractions)
> - **B) `/plan`** -- go straight to planning

Report status: **DONE** with evidence (file path).

---

## Output Format

Discover mode produces `tasks/<topic>-design.md` (design doc with problem statement, approaches, recommendation, success criteria). Refine mode produces `tasks/<topic>-think.md` (brief with problem statement, proposed approach, assumptions, risks, simplest testable version).

## Completion Status Protocol

Report status using one of:
- **DONE** -- All steps completed. Evidence: file path written, quality score if reviewed.
- **DONE_WITH_CONCERNS** -- Completed with issues. List each concern.
- **BLOCKED** -- Cannot proceed. State blocker and what was tried.
- **NEEDS_CONTEXT** -- Missing information. State exactly what you need.

If attempted 3 times without success, STOP and escalate.

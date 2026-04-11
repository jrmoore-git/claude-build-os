---
name: design-shotgun
description: |
  Generate multiple AI design variants, open a comparison board, collect
  structured feedback, and iterate. Use when: "explore designs", "show me
  options", "design variants", "visual brainstorm", or "I don't like how
  this looks". Defers to /design-consultation for design system changes and
  /design-review for visual QA of existing UI.
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# /design-shotgun: Visual Design Exploration

Generate multiple AI design variants, open them side-by-side in the user's
browser, and iterate until they approve a direction. This is visual brainstorming,
not a review process.

## Prerequisites Check

Run before anything else:

```bash
# Design CLI binary (set DESIGN_CLI in shell profile)
D="${DESIGN_CLI:-}"
if [ -n "$D" ] && [ -x "$D" ]; then
  echo "DESIGN_READY: $D"
else
  echo "DESIGN_NOT_AVAILABLE"
fi

# Browse daemon (set BROWSE_CLI in shell profile)
B="${BROWSE_CLI:-}"
if [ -n "$B" ] && [ -x "$B" ]; then
  echo "BROWSE_READY: $B"
else
  echo "BROWSE_NOT_AVAILABLE (will use 'open' to view comparison boards)"
fi

# OpenAI API key (needed for DALL-E image generation)
if [ -n "$OPENAI_API_KEY" ]; then
  echo "OPENAI_KEY: available"
else
  echo "OPENAI_KEY: MISSING"
fi
```

If `DESIGN_NOT_AVAILABLE`: STOP. Tell the user: "Design tools aren't installed.
Run `./scripts/setup-design-tools.sh` then restart your shell."

If `OPENAI_KEY: MISSING`: STOP. Tell the user: "OPENAI_API_KEY is not set.
The design CLI needs it for DALL-E image generation. Export it in your shell
or add it to your .env file."

If `BROWSE_NOT_AVAILABLE`: use `open file://...` instead of `$B goto` to open
comparison boards.

## Step 0: Read Design System

**This step is mandatory. Do not skip.**

Look for a project design system file (common locations: `DESIGN.md`,
`docs/DESIGN.md`, `<app-dir>/DESIGN.md`):

```bash
find . -maxdepth 3 -name "DESIGN.md" -not -path "*/node_modules/*" 2>/dev/null
```

If found, read it and extract constraints (fonts, colors, spacing, borders,
layout patterns). These constraints MUST be included in every `$D generate`
and `$D variants` brief as a design system prefix.

If no DESIGN.md exists, ask the user for key design constraints or proceed
with sensible defaults. Also check `.claude/rules/design.md` for anti-slop
rules if it exists.

## Step 1: Session Detection

Check for prior design sessions:

```bash
_DESIGN_BASE=designs
mkdir -p "$_DESIGN_BASE"
_PREV=$(find "$_DESIGN_BASE" -name "approved.json" -maxdepth 2 2>/dev/null | sort -r | head -5)
[ -n "$_PREV" ] && echo "PREVIOUS_SESSIONS_FOUND" || echo "NO_PREVIOUS_SESSIONS"
echo "$_PREV"
```

**If `PREVIOUS_SESSIONS_FOUND`:** Read each `approved.json`, display a summary,
then AskUserQuestion:

> "Previous design explorations:
> - [date]: [screen] -- chose variant [X], feedback: '[summary]'
>
> A) Revisit -- reopen the comparison board to adjust choices
> B) New exploration -- start fresh
> C) Something else"

**If `NO_PREVIOUS_SESSIONS`:** Proceed to Step 2.

## Step 2: Context Gathering

If invoked from another skill with `$_DESIGN_BRIEF` set, skip to Step 3.

Gather context for the design brief:

1. **What exists** -- check for running local site and existing components:

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "NO_LOCAL_SITE"
```

2. If the user said "I don't like THIS" and localhost is running, screenshot
   the current page with `$B screenshot` for the evolve path.

3. AskUserQuestion with pre-filled context:

> "Here's what I know: [pre-filled context]. I'm missing [gaps].
> Tell me: [specific questions].
> How many variants? (default 3, up to 8)"

Two rounds max of context gathering, then proceed with assumptions.

## Step 3: Taste Memory

Read prior approved designs to bias generation:

```bash
_TASTE=$(find designs/ -name "approved.json" -maxdepth 2 2>/dev/null | sort -r | head -10)
```

If prior sessions exist, read each `approved.json` and extract patterns.
Include a taste summary in the brief: "The user previously approved designs
with these characteristics: [patterns]. Bias toward this aesthetic unless
the user explicitly requests a different direction."

## Step 4: Generate Variants

Set up output directory:

```bash
_SCREEN_NAME="<screen-name>"  # kebab-case from context
_DESIGN_DIR=designs/$_SCREEN_NAME-$(date +%Y%m%d)
mkdir -p "$_DESIGN_DIR"
echo "DESIGN_DIR: $_DESIGN_DIR"
```

### Step 4a: Concept Generation

Generate N text concepts (distinct creative directions, not minor variations).
Present as a lettered list. Every concept brief MUST include the design system
constraints from Step 0.

### Step 4b: Concept Confirmation

AskUserQuestion to confirm before spending API credits:

> "These are the {N} directions I'll generate. Each takes ~60s, run in parallel."

Options: A) Generate all, B) Change some, C) Add more, D) Fewer

### Step 4c: Parallel Generation

Launch N Agent subagents in a single message (parallel execution).

**Agent prompt template** (substitute all `{...}` values):

```
Generate a design variant and save it.

Design binary: {absolute path to $D binary}
Brief: {full variant brief INCLUDING design system constraints}
Output: /tmp/variant-{letter}.png
Final location: {_DESIGN_DIR absolute path}/variant-{letter}.png
OpenAI API key: export OPENAI_API_KEY before running the design binary.

Steps:
1. Export OPENAI_API_KEY if not in environment
2. Run: {$D path} generate --brief "{brief}" --output /tmp/variant-{letter}.png
3. If rate limited (429), wait 5s and retry (up to 3 retries)
4. Copy: cp /tmp/variant-{letter}.png {_DESIGN_DIR}/variant-{letter}.png
5. Quality check: {$D path} check --image {_DESIGN_DIR}/variant-{letter}.png --brief "{brief}"
6. Verify: ls -lh {_DESIGN_DIR}/variant-{letter}.png
7. Report: VARIANT_{letter}_DONE or VARIANT_{letter}_FAILED
```

For the evolve path (redesigning existing UI), use `$D evolve --screenshot`
instead of `$D generate`.

### Step 4d: Results

After all agents complete:
1. Read each generated PNG inline so the user sees all variants
2. Report status: "{successes} succeeded, {failures} failed"
3. If zero succeeded: fall back to sequential generation
4. Build dynamic image list for comparison board:

```bash
_IMAGES=$(ls "$_DESIGN_DIR"/variant-*.png 2>/dev/null | tr '\n' ',' | sed 's/,$//')
```

## Step 5: Comparison Board + Feedback Loop

Create and serve the comparison board:

```bash
$D compare --images "$_IMAGES" --output "$_DESIGN_DIR/design-board.html" --serve &
```

Parse the port from stderr: `SERVE_STARTED: port=XXXXX`.

If `$B` is available, use it. Otherwise `open file://...` or the HTTP URL.

**AskUserQuestion with board URL:**

> "Comparison board open at http://127.0.0.1:<PORT>/
> Rate variants, leave comments, and click Submit. Let me know when done."

After user responds, check for feedback files:

```bash
if [ -f "$_DESIGN_DIR/feedback.json" ]; then
  echo "SUBMIT_RECEIVED"
  cat "$_DESIGN_DIR/feedback.json"
elif [ -f "$_DESIGN_DIR/feedback-pending.json" ]; then
  echo "REGENERATE_RECEIVED"
  cat "$_DESIGN_DIR/feedback-pending.json"
  rm "$_DESIGN_DIR/feedback-pending.json"
else
  echo "NO_FEEDBACK_FILE"
fi
```

**If `feedback.json`:** User submitted final choice. Proceed.
**If `feedback-pending.json`:** User wants regeneration. Generate new variants
with updated brief, reload board via `curl -s -X POST http://127.0.0.1:PORT/api/reload`,
AskUserQuestion again. Repeat until `feedback.json` appears.
**If `NO_FEEDBACK_FILE`:** Use user's text response as feedback.

## Step 6: Confirm + Save

Summarize understood feedback:

```
PREFERRED: Variant [X]
RATINGS: [list]
YOUR NOTES: [comments]
DIRECTION: [overall]
```

AskUserQuestion to verify before saving.

Save approved choice:

```bash
echo '{"approved_variant":"<V>","feedback":"<FB>","date":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","screen":"<SCREEN>","branch":"'$(git branch --show-current 2>/dev/null)'"}' > "$_DESIGN_DIR/approved.json"
```

## Step 7: Next Steps

AskUserQuestion:

> "Design direction locked in. What's next?
> A) Iterate more -- refine the approved variant
> B) Implement -- start building the approved design into the app
> C) Save to plan -- add as approved mockup reference
> D) Done -- save for later"

## Rules

1. **Design system is mandatory context.** Read DESIGN.md (or equivalent) before
   generating any variant. Include design system constraints in every generation brief.
2. **Anti-slop enforcement.** No purple gradients, no centered-everything, no bubbly
   uniform radius, no generic hero copy.
3. **Artifacts go to `designs/`.** Not `/tmp/`. Design artifacts
   are project files.
4. **Show variants inline before opening the board.** User sees designs in terminal first.
5. **Confirm feedback before saving.** Always summarize and verify.
6. **Taste memory is automatic.** Prior approved designs inform new generations.
7. **Two rounds max on context gathering.** Proceed with assumptions after that.
8. **OpenAI API key required.** The design CLI uses DALL-E. Check availability early.

---
name: research
description: "Deep web research via Perplexity Sonar. Returns sourced markdown with citations. Two modes: deep (async, multi-source synthesis) and quick (sync, spot lookup). Use when a task needs evidence, landscape awareness, or multi-source synthesis. Defers to: /think (problem discovery), /explore (divergent options)."
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# /research -- Deep Web Research

Two modes: **deep** (default, async Perplexity Sonar Deep Research, ~2-5 min, $0.40-0.80) and **quick** (sync Perplexity Sonar, instant, ~$0.01).

## When to use

- Need sourced evidence on a topic before making decisions
- Landscape/competitive awareness for /think or /explore
- Multi-source synthesis that would take 15+ minutes with WebSearch agents
- Academic research (use --academic flag)

## Procedure

### Step 1: Parse input

- Extract the research question from the user's message.
- Determine mode: if user said "quick" or question is simple factual lookup, use quick mode. Otherwise use deep mode.
- Sanitize topic for filename: lowercase alphanumeric + hyphens only, matching `^[a-z0-9]+(-[a-z0-9]+)*$`. Strip `/`, `\`, `..`, spaces, and special characters.

### Step 2: Privacy gate

Before sending anything to Perplexity, output the following as markdown text, then call AskUserQuestion with the same options:

> This will send your research question to Perplexity's API for web research. The question is sent as-is.
>
> - **A) Proceed**
> - **B) Skip -- I'll research manually**

If B: output "Research skipped by user." and stop.

If the research question contains what looks like internal/proprietary terms (project names, internal codenames, company-specific jargon), warn the user before proceeding:

> Your question contains terms that may be proprietary: [list terms]. These will be sent to Perplexity as-is. Proceed?

### Step 3: Compose research request

- If the user provided a system prompt or output structure guidance, pass it via `--system`.
- Determine effort level: default medium for deep mode. Effort is not applicable for quick mode.

### Step 4: Run research

Check that `PERPLEXITY_API_KEY` is available before running. Read it from `.env`:

```bash
grep -q PERPLEXITY_API_KEY .env 2>/dev/null
```

If missing, fall back to WebSearch:

> Perplexity API key not configured — falling back to Claude's built-in WebSearch. Results will be less comprehensive (no multi-source synthesis or citations), but still grounded in live web data.

Use Claude's built-in WebSearch tool to research the question. Make 2-3 targeted searches, synthesize results, and write to `tasks/<topic>-research.md` in the same format as Perplexity output. Then skip to Step 5.

**Deep mode (default):**

```bash
export $(grep -m1 '^PERPLEXITY_API_KEY=' .env) && /opt/homebrew/bin/python3.11 scripts/research.py \
  --effort medium \
  -o tasks/<topic>-research.md \
  "<research question>"
```

**Quick mode:**

```bash
export $(grep -m1 '^PERPLEXITY_API_KEY=' .env) && /opt/homebrew/bin/python3.11 scripts/research.py \
  --sync --model sonar \
  -o tasks/<topic>-research.md \
  "<research question>"
```

**Academic mode** (if user requested scholarly sources): add `--academic` flag to either command.

**Custom output structure** (if user specified): add `--system "<structure guidance>"` to either command.

**Shell safety:** Never interpolate the user's research question directly into shell strings. Pass it as a properly quoted positional argument. Never include the API key in displayed commands or conversation output.

### Step 5: Display results

- Read `tasks/<topic>-research.md`.
- Display the research output to the user in the conversation.
- Report: mode used, output file path, and token usage from stderr.

## Output Contract

- Deep mode: sourced markdown document with `## Sources` section, written to `tasks/<topic>-research.md`.
- Quick mode: shorter response with inline citations, written to `tasks/<topic>-research.md`.
- Both modes: if `PERPLEXITY_API_KEY` is missing, error immediately with clear message.
- Zero output between tool calls. The only user-visible output is the privacy gate question (Step 2) and the final results display (Step 5).

## Safety Rules

- NEVER send the user's proprietary product names, internal project names, or specific business details to Perplexity without the privacy gate approval.
- NEVER output the API key or include it in any displayed command.
- NEVER interpolate untrusted text into shell command strings. Pass the research question as a quoted argument.
- If the research question contains what looks like internal/proprietary terms, warn the user before proceeding.

## Completion Status Protocol

- **DONE**: Research complete, file written to `tasks/<topic>-research.md`, results displayed.
- **BLOCKED**: API key missing or API error after retries.
- **NEEDS_CONTEXT**: Research question unclear, need clarification from user.

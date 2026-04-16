# Canonical SKILL.md Sections Spec

## Context

BuildOS has 22 skills defined as Markdown files with YAML frontmatter. An audit found 18/22 missing Safety Rules, 17/22 missing Output Silence, 13/22 missing escalation codes. This spec defines what a well-formed skill looks like, tiered by complexity, so a lint can enforce it.

**Informed by:**
- gstack's skill validation system (1,573 lines of structural tests, preamble-tier 1-4, required sections by tier)
- Structured authoring best practices (separate content from presentation, component-based, schema-enforced)
- Consumer-driven contract testing (Pact pattern: schema as contract, validate on every change)
- Perplexity research confirming no prompt linters exist in the ecosystem

## Tier Definitions

Skills are classified into two tiers based on what they do, not how long they are.

### Tier 1 — Utility

Skills that classify, route, capture, or look up information. They don't call external APIs, don't modify production state, and don't run multi-step procedures with branching logic.

**Current Tier 1 skills:** `/guide`, `/log`, `/triage`, `/setup`, `/audit`

### Tier 2 — Workflow

Skills that run multi-step procedures, call debate.py or external tools, modify files, produce structured artifacts, or have branching logic (modes, conditional paths). This includes skills that spawn subagents.

**Current Tier 2 skills:** `/explore`, `/polish`, `/pressure-test`, `/research`, `/plan`, `/ship`, `/start`, `/sync`, `/wrap`, `/challenge`, `/healthcheck`, `/investigate`, `/simulate`, `/elevate`, `/review`, `/think`, `/design`

## Required Sections

### All skills (Tier 1 + Tier 2)

#### 1. Frontmatter (YAML)

```yaml
---
name: skill-name
description: "Single-line quoted string. Includes 'Use when...' trigger phrase."
version: 1.0.0
---
```

**Validation rules:**
- `name` must match directory name
- `description` must be a quoted string (not YAML block scalar `|` or `>`)
- `description` must contain "Use when" trigger phrase (borrowed from gstack)
- `version` follows semver

**Rationale:** gstack validates trigger phrases in frontmatter for all skills. Our `hook-intent-router.py` and `natural-language-routing.md` maintain routing tables separately — co-locating triggers in the skill itself is simpler and keeps routing close to the skill. The `description` field is what Claude Code shows in the `/` menu, so trigger phrases there serve double duty (discovery + routing).

#### 2. Procedure

The skill must have a section describing what it does, using one of these heading patterns:
- `## Procedure`
- `## Steps`
- Numbered `### Step N` headings

**Validation:** At least one of these patterns must be present.

**Rationale:** A skill without a procedure is just a description. The procedure is the executable part.

#### 3. Completion Status

Every skill must declare how it reports completion, using one of these codes:
- `DONE` — all steps completed successfully
- `DONE_WITH_CONCERNS` — completed with issues
- `BLOCKED` — cannot proceed
- `NEEDS_CONTEXT` — missing information

**Validation:** The string `DONE` must appear in the skill body (not frontmatter). At least one of `DONE_WITH_CONCERNS`, `BLOCKED`, or `NEEDS_CONTEXT` must also appear.

**Rationale:** Borrowed from gstack (all preamble-tier 2+ skills require escalation codes) and already in our `skill-authoring.md` as the Completion Status Protocol. Currently only 9/22 skills have these.

### Tier 2 only (workflow skills)

#### 4. Safety Rules

A section headed `## Safety Rules` containing explicit prohibitions relevant to the skill.

**Validation:** The heading `## Safety Rules` must be present. The section must contain at least one `NEVER` or `Do not` statement.

**Rationale:** From our `skill-authoring.md`: "For skills that face external non-privileged users, use a standalone `## OUTPUT SILENCE -- HARD RULE` section... For internal-only skills, a bold bullet inside Safety Rules is sufficient." Currently only 4/22 skills have this. The smoke-test found this is the #1 structural gap.

**What goes here (minimum):**
- What the skill must NEVER do (e.g., "NEVER commit without review", "NEVER call send/deliver tools")
- What external state it must not modify
- What data it must not expose in output

Skills that call debate.py must include a fallback rule for when the debate engine is unavailable.

#### 5. Output Silence (interactive workflow skills)

**Applies to:** Skills that run multi-tool procedures and produce a single formatted output at the end.

**Validation:** Must contain the string "Output Silence" or "OUTPUT SILENCE" (case-insensitive match on the phrase).

**Rationale:** From `skill-authoring.md`: "Between tool calls, a skill MUST NOT emit text to the chat." This prevents double-renders when the agent stream and delivery inject collide. Currently only 5/22 skills have this.

**Exempt:** Skills where intermediate output IS the interface (e.g., `/guide` shows options, `/start` shows status brief, `/log` confirms capture). The lint should have an exemption list.

#### 6. Output Format

A section describing the shape of the skill's output: what it produces, where it's written, and what format it uses.

**Validation:** Must contain one of: `## Output Format`, `## Output`, or `## Deliverable`.

**Rationale:** From structured authoring: "separate content from presentation." A skill that doesn't declare its output format can't be validated downstream. Currently only 3/22 have this explicitly. Many skills describe output inline in the procedure, but an explicit section makes it lintable and parseable by the IR extractor.

#### 7. Debate Fallback (skills that call debate.py)

**Applies to:** Skills that invoke `scripts/debate.py`.

**Validation:** Must contain one of: "fallback", "unavailable", "fails", "error" in proximity to "debate" (within 5 lines).

**Rationale:** debate.py calls external LLM APIs. When Gemini times out or a model is down, the skill needs a defined fallback behavior (retry with different model, degrade gracefully, proceed without). Currently only 2/22 skills with debate.py usage declare a fallback.

## Optional Sections (recommended but not lint-enforced)

### Defers-to Declaration

A statement of what the skill does NOT handle and which skill to use instead.

**Example:** "Defers to: `/investigate` for root-cause analysis, `/review` for code review."

**Rationale:** From `skill-authoring.md`: "each skill description must declare what it handles AND what it defers to other skills." Prevents double-processing and helps routing. Recommended in the description field or a separate section.

### Cron Contract (cron-invoked skills only)

**Applies to:** Skills that run on a schedule.

**Validation (if present):** Must contain the 5 rules: empty result → zero output, auth failure → zero output + audit log, external API error → zero output + audit log, no narration, output contract section.

**Rationale:** From `skill-authoring.md` Cron Output Contract. Not enforced by lint because not all skills run in cron.

## Tier Classification Rules

A skill is Tier 2 if ANY of:
- It has more than 3 `### Step` or `## Phase` headings
- It calls `debate.py` or `scripts/*.py`
- It writes files (mentions `Write`, `Edit`, or file output paths)
- It spawns agents (`Agent(` or `subagent`)
- It has multiple modes (`--mode`, conditional branches)
- It produces artifacts (`tasks/*`, `docs/*` output files)

Otherwise Tier 1.

## Validation Implementation

The lint should be implementable as a Python script that:
1. Reads each `SKILL.md` file
2. Parses frontmatter (regex, not PyYAML — not installed)
3. Classifies tier based on content heuristics
4. Checks required sections for that tier
5. Reports missing sections with specific guidance

**Hook integration:** Wire as a PreToolUse hook on Write/Edit targeting `.claude/skills/*/SKILL.md` paths, or as a test in the test suite, or both.

**Exemption mechanism:** A `lint-exempt` field in frontmatter can suppress specific checks:
```yaml
lint-exempt: ["output-silence"]  # This skill uses intermediate output by design
```

## Schema as Contract

The tier + required sections define a **contract** for each skill. This contract serves three purposes:

1. **Lint layer:** Does the skill have the sections it needs? (Structural validation)
2. **IR layer:** Does the skill's behavior match its declared structure? (Semantic validation via `sim_compiler.py extract_ir`)
3. **Drift layer:** Did an edit change the skill's behavioral contract? (Change detection via `sim_compiler.py compare_ir`)

The lint validates layer 1. The IR extractor (already built) validates layers 2 and 3. This spec defines what layer 1 checks for.

## Current State vs. Target

| Section | Current (have/22) | Target Tier 1 | Target Tier 2 |
|---|---|---|---|
| Valid frontmatter | 22 | required | required |
| Trigger phrases in description | 8 | required | required |
| Semver version | 0 | required | required |
| Procedure section | 20 | required | required |
| Completion status codes | 9 | required | required |
| Safety Rules | 4 | — | required |
| Output Silence | 5 | — | required (with exemptions) |
| Output Format | 3 | — | required |
| Debate fallback | 2 | — | required (if uses debate.py) |

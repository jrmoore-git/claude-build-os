---
debate_id: canonical-skill-sections
created: 2026-04-15T13:09:15-0700
phase: refine
rounds: 3
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: no
---
# canonical-skill-sections — Refined Document

## Round 1 (gemini-3.1-pro)
*   **Strong Points:** The document provides an excellent, data-backed baseline (the 22-skill audit) and clearly delineates between Utility (Tier 1) and Workflow (Tier 2) skills. The "Schema as Contract" conceptual model is highly effective.
*   **Areas for Improvement:** The language around the linter implementation was slightly suggestive ("should be implementable as") rather than prescriptive. Validation rules relied on some loose phrasing.
*   **Changes Made:** 
    *   Upgraded descriptive language to prescriptive specification language (e.g., "must implement" instead of "should be implementable").
    *   Tightened the validation rules to specify exact string or regex requirements, making the spec immediately actionable for the developer writing the linter.
    *   Formalized the exemption mechanism and hook integration requirements.

## Round 2 (gpt-5.4)
The current revision is already strong: it defines tiers clearly, preserves the audit data, and gives concrete validation rules that are enforceable by a linter.

Remaining issues and improvements:
- **Potential ambiguity in Procedure validation:** “exactly one of the following heading patterns” can be read as forbidding a skill from having both `## Procedure` and `### Step N` subheadings under it. I tightened this so the linter checks for one valid procedure structure, not a mutually exclusive literal pattern match that would reject reasonable documents.
- **Tier 2 Output Silence scope needed sharpening:** the original says it applies to “interactive workflow skills” and gives examples of exemptions, but the validation target is still broad. I preserved the rule while making the exemption path and applicability clearer.
- **Tier classification heuristics needed precedence language:** “Otherwise Tier 1” was fine, but I made clear these are deterministic heuristics and that a single match upgrades to Tier 2.
- **Validation implementation was slightly under-specified:** I preserved the strict requirements and made the failure output expectation more actionable.
- **A few sections were slightly over-explained or repeated rationale:** I tightened wording while preserving operational context and measurements.
- **No recommendations section existed**, so the recommendation-preservation rule is a no-op here.

## Round 3 (claude-opus-4-6)
The current revision is well-structured, precise, and largely production-ready. It reads as a genuine specification rather than a discussion document. Key strengths:

1. **Tier definitions are clean and actionable.** The heuristic classification rules are deterministic and linter-implementable.
2. **Validation rules are concrete.** Each section has specific string-match or structural requirements, not vague guidance.
3. **The current-state table provides clear gap visibility.**
4. **Rationale blocks are well-sourced** to existing system artifacts (gstack, skill-authoring.md, smoke test findings).

**Issues identified for this revision:**

1. **Tier classification list inconsistency.** The Tier 1 list has 5 skills and Tier 2 has 17, totaling 22. Good — matches the audit denominator. However, `/guide`, `/start`, and `/log` are listed as Tier 1 but later cited as Output Silence exemptions for Tier 2. Since Output Silence is a Tier 2-only requirement, listing exemptions for Tier 1 skills is logically incoherent — Tier 1 skills don't need exemptions because the rule doesn't apply to them. This needs to be cleaned up: either these skills are Tier 1 (and the exemption note is unnecessary) or some of them are actually Tier 2 (and the tier lists need correction).

2. **Output Silence applicability is muddled.** The section says "Applies to: Tier 2 skills that run multi-tool procedures and emit a single formatted output at the end." This is a subset of Tier 2, but the validation rule applies to all Tier 2 skills (with exemptions). The "applies to" qualifier creates ambiguity about whether non-matching Tier 2 skills fail validation or are implicitly exempt. The exemption mechanism should be the only escape valve, and the "applies to" line should be removed or reframed.

3. **Debate Fallback "5-line radius" is underspecified for a linter.** Does this mean 5 lines above and 5 below the word "debate"? 5 lines total? Lines of raw markdown or rendered lines? This needs a precise definition for implementation.

4. **Safety Rules validation vs. required content mismatch.** The validation rules say the section body must contain `NEVER` or `Do not`. The "Required content" block lists specific prohibitions and a debate.py fallback rule. It's unclear whether the "Required content" items are linter-enforced or authoring guidance. This ambiguity will cause implementer confusion.

5. **Cron Contract section lacks tier assignment.** It's listed under "Optional Sections" but has specific validation rules ("MUST contain these 5 rules"). An optional section with MUST requirements is contradictory. Either it's optional (and the rules are guidance) or it's conditionally required (like Debate Fallback) and belongs in the required sections with a clear trigger condition.

6. **Minor: "Schema as Contract" section references `sim_compiler.py` for Layers 2-3 but this spec is explicitly "the absolute specification for Layer 1."** The Layer 2-3 references are useful context but could mislead readers into thinking this spec governs those layers.

## Final Refined Document

# Canonical SKILL.md Sections Spec

## Context

BuildOS has 22 skills defined as Markdown files with YAML frontmatter. An audit found 18/22 missing Safety Rules, 17/22 missing Output Silence, and 13/22 missing escalation codes. This spec defines what a well-formed skill looks like, tiered by complexity, to enable strict linter enforcement.

**Informed by:**
- gstack's skill validation system (1,573 lines of structural tests, preamble-tier 1–4, required sections by tier)
- Structured authoring best practices (separate content from presentation, component-based, schema-enforced)
- Consumer-driven contract testing (Pact pattern: schema as contract, validate on every change)
- Perplexity research confirming no prompt linters exist in the ecosystem

## Tier Definitions

Skills are classified into two tiers based on operational capability and blast radius.

### Tier 1 — Utility

Skills that classify, route, capture, or look up information. They do not call external APIs, do not modify production state, and do not execute multi-step procedures with branching logic.

**Current Tier 1 skills:** `/guide`, `/log`, `/triage`, `/setup`, `/audit`

### Tier 2 — Workflow

Skills that execute multi-step procedures, invoke `debate.py` or external tools, modify files, produce structured artifacts, or contain branching logic such as modes or conditional paths. This includes any skill that spawns subagents.

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
- `name` MUST match the parent directory name exactly.
- `description` MUST be a quoted string. YAML block scalars (`|` or `>`) are rejected.
- `description` MUST contain the exact substring `Use when`.
- `version` MUST follow semantic versioning (`MAJOR.MINOR.PATCH`).

**Rationale:** gstack validates trigger phrases in frontmatter for all skills. Our `hook-intent-router.py` and `natural-language-routing.md` maintain routing tables separately; co-locating triggers in the skill itself is simpler and keeps routing close to the skill. The `description` field is what Claude Code shows in the `/` menu, so trigger phrases there serve double duty for discovery and routing.

#### 2. Procedure

The skill must contain an executable procedure, not just a description.

**Validation rules:**
A skill MUST satisfy at least one of these structures:
- A `## Procedure` heading, or
- A `## Steps` heading, or
- Numbered `### Step N` headings where `N` is an integer.

The linter treats these as valid procedure patterns. They are not mutually exclusive; a skill satisfying any one pattern passes this check.

**Rationale:** A skill without a procedure is a description, not an executable asset.

#### 3. Completion Status

Every skill must declare how it reports completion to the agent loop.

**Validation rules:**
- The exact string `DONE` MUST appear in the skill body, excluding frontmatter.
- At least one of the following strings MUST also appear in the body: `DONE_WITH_CONCERNS`, `BLOCKED`, or `NEEDS_CONTEXT`.

**Rationale:** Borrowed from gstack, where all preamble-tier 2+ skills require escalation codes, and codified in our `skill-authoring.md` as the Completion Status Protocol. Currently, only 9/22 skills implement this.

### Tier 2 only (workflow skills)

#### 4. Safety Rules

A section explicitly defining operational prohibitions and constraints.

**Validation rules (linter-enforced):**
- The heading `## Safety Rules` MUST be present.
- The section body MUST contain at least one `NEVER` or `Do not` statement.

**Authoring guidance (not linter-enforced):**
Authors should include the following where applicable. These are reviewed during skill review, not by the linter:
- Explicit prohibitions such as `NEVER commit without review` or `NEVER call send/deliver tools`.
- External state modification constraints.
- Data exposure constraints.
- If the skill calls `debate.py`, a defined fallback rule for engine unavailability.

**Rationale:** From `skill-authoring.md`: "For skills that face external non-privileged users, use a standalone `## OUTPUT SILENCE -- HARD RULE` section. For internal-only skills, a bold bullet inside Safety Rules is sufficient." Currently, only 4/22 skills have this. The smoke test found this is the #1 structural gap.

#### 5. Output Silence

**Validation rules:**
- Every Tier 2 skill MUST either:
  - (a) Contain the string `Output Silence` (case-insensitive match), or
  - (b) Declare `lint-exempt: ["output-silence"]` in frontmatter.
- There is no implicit exemption. Skills where intermediate output is the interface (e.g., `/start`) MUST use option (b) explicitly.

**Rationale:** From `skill-authoring.md`: "Between tool calls, a skill MUST NOT emit text to the chat." This prevents double-renders when the agent stream and delivery inject collide. Currently, only 5/22 skills have this.

**Note on Tier 1 skills:** Tier 1 skills are not subject to this check. Tier 1 skills such as `/guide` and `/log` that emit intermediate output by design require no exemption declaration because the rule does not apply to them.

#### 6. Output Format

A section defining the exact shape, location, and format of the skill's deliverables.

**Validation rules:** The skill MUST contain one of the following headings:
- `## Output Format`
- `## Output`
- `## Deliverable`

**Rationale:** This enforces separation of content from presentation. A skill missing an output declaration cannot be validated downstream. Currently, only 3/22 have this explicitly.

#### 7. Debate Fallback (skills that call debate.py)

**Applies to:** Any Tier 2 skill whose body contains the string `debate.py`.

**Validation rules:** Within a window of 5 lines above or 5 lines below any line containing the string `debate` (10-line window centered on the match, raw Markdown lines as written in the file), at least one of the following keywords MUST appear:
- `fallback`
- `unavailable`
- `fails`
- `error`

**Rationale:** `debate.py` calls external LLM APIs. When Gemini times out or a model is down, the skill requires deterministic fallback behavior such as retry, degrade, or bypass. Currently, only 2 of the skills using `debate.py` declare a fallback.

## Optional Sections

### Defers-to Declaration

A statement defining skill boundaries and routing alternatives.

**Example:** `Defers to: /investigate for root-cause analysis, /review for code review.`

**Rationale:** Prevents double-processing. Recommended either in the description field or in a dedicated section. Not linter-enforced.

### Cron Contract (cron-invoked skills only)

**Applies to:** Skills executed on a schedule. Not currently linter-enforced; included here as an authoring standard for cron-invoked skills.

**Authoring rules:** If a skill includes a Cron Contract section, it MUST contain all 5 of the following rules:
1. Empty result → zero output.
2. Auth failure → zero output + audit log.
3. External API error → zero output + audit log.
4. No narration.
5. Output contract section.

**Future enforcement:** When a cron-invoked skill is identified by a `cron: true` frontmatter field or equivalent trigger, these rules will be promoted to linter-enforced validation. Until that trigger mechanism exists, this section is an authoring contract enforced during review.

## Tier Classification Rules

The linter MUST classify a skill as Tier 2 if any of the following heuristics match:
- Contains more than 3 `### Step` or `## Phase` headings.
- Mentions `debate.py` or `scripts/*.py`.
- Contains file modification keywords such as `Write` or `Edit`, or contains file output paths.
- Contains agent-spawning keywords such as `Agent(` or `subagent`.
- Contains branching logic keywords such as `--mode` or explicit conditional branches.
- Specifies artifact generation such as `tasks/*` or `docs/*` output files.

If none of these heuristics match, the linter classifies the skill as Tier 1.

These heuristics are deterministic. A single Tier 2 match is sufficient to classify the skill as Tier 2.

**Override mechanism:** If a skill is misclassified by heuristics, the frontmatter field `tier: 1` or `tier: 2` overrides heuristic classification. When present, the linter uses the declared tier and skips heuristic evaluation.

## Validation Implementation

The linter is a Python script with the following strict execution requirements:
1. Read each `SKILL.md` file.
2. Parse frontmatter using standard regex. PyYAML is not required or installed.
3. Check for a `tier` frontmatter override. If absent, classify tier from the heuristics defined above.
4. Execute validation rules for the assigned tier.
5. Exit with code `1` and emit specific missing-section guidance if any validation rule fails.

**Hook Integration:** The linter MUST execute as a `PreToolUse` hook on `Write` and `Edit` actions targeting `.claude/skills/*/SKILL.md` paths.

**Exemption Mechanism:** Specific checks are bypassed via a `lint-exempt` array in frontmatter:

```yaml
lint-exempt: ["output-silence"]
```

A linter exemption only disables the named check. It does not downgrade a Tier 2 skill to Tier 1 and does not bypass unrelated required sections.

## Schema as Contract

The tier classification and required sections define a structural contract for each skill. This contract operates across three layers:

1. **Lint layer (this spec):** Does the skill possess the required structural sections? This document is the absolute specification for this layer.
2. **IR layer:** Does the skill's behavior match its declared structure? Validated by `sim_compiler.py extract_ir`.
3. **Drift layer:** Did an edit alter the skill's behavioral contract? Validated by `sim_compiler.py compare_ir`.

Layers 2 and 3 are governed by their own specifications. They are referenced here to show where structural validation fits in the broader validation pipeline.

## Current State vs. Target

| Section | Current (have/22) | Target Tier 1 | Target Tier 2 |
|---|---|---|---|
| Valid frontmatter | 22 | required | required |
| Trigger phrases in description | 8 | required | required |
| Semver version | 0 | required | required |
| Procedure section | 20 | required | required |
| Completion status codes | 9 | required | required |
| Safety Rules | 4 | — | required |
| Output Silence | 5 | — | required (or lint-exempt) |
| Output Format | 3 | — | required |
| Debate fallback | 2 | — | required (if uses debate.py) |

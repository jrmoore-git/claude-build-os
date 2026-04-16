---
debate_id: context-packet-spec
created: 2026-04-15T14:54:39-0700
phase: refine
rounds: 6
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: no
---
# context-packet-spec — Refined Document

## Round 1 (gemini-3.1-pro)
- **Strengths**: The A/B test data and the identified gap (6 skills lacking context) provide a very clear empirical baseline. The distinction between "thin" and "enriched" context is well-supported by runtimes and tool-call counts.
- **Improvement Areas**: The "Implementation Priority" section is formatted as a list of targets rather than an executable plan. It states the skills but does not specify the exact changes required for each. The "Assembly Pattern" is slightly abstract and can be tightened into concrete execution steps.
- **Changes Made**: 
  - Sharpened the "Assembly Pattern" to be a strict procedural checklist.
  - Converted the "Implementation Priority" into concrete, actionable steps for each skill, removing subjective qualifiers like "could benefit" and replacing them with specific directives.
  - Retained all verified operational metrics, A/B test results, and token/line size targets.

## Round 2 (gpt-5.4)
The revision is already strong: it states the problem clearly, ties the spec to observed A/B results, and gives an implementation list instead of abstract guidance. The biggest improvement opportunity is precision.

Key issues in the current revision:

1. **Some operational claims are not yet grounded in verified repository behavior.**
   - Verified: `scripts/debate.py` exists and is 4,136 lines.
   - Verified: 10 skills reference `debate.py`.
   - Verified: `scripts/enrich_context.py` exists, but the current draft describes it as if it directly provides a generic “governance/decisions” summary. The file header says it extracts keywords from a proposal and searches governance files, returning structured JSON. The revised document should describe that more accurately and treat it as a proposal-linked enrichment source, not a universal context builder.

2. **The “exact sequence” is too rigid for the different invocation modes.**
   - The document later acknowledges disk-based, temp-file, and inline patterns, so the main assembly procedure should distinguish between a canonical section order and multiple delivery mechanisms. Otherwise it reads as one assembly path when the skills actually differ.

3. **A few requirements are too absolute without a fallback path.**
   - “Every document must be self-contained” is directionally right, but some modes may pass context via `--context` rather than physically prepending it to the artifact. The revised version should preserve the self-contained requirement at the evaluation input level, while clarifying that the self-contained packet may be delivered as one compiled file or as artifact + explicit context flag.

4. **Size guidance is useful but should be framed as budgets, not guarantees.**
   - The current wording implies the specified size “guarantees optimal” performance. The evidence supports “materially better grounding” and “better cross-model convergence,” not a universal guarantee.

5. **Implementation recommendations can be sharper.**
   - The original 6 recommendations are good and must be preserved. They can be improved by defining what each skill must include, how much context, and the immediate success condition for completion.

## Round 3 (claude-opus-4-6)
**Improvements made by previous reviewer:**
- Good structure with clear section ordering (Project Context → Recent Context → Artifact → Evaluation-Specific Context)
- Source Rules table is well-organized
- Size budgets are reasonable and tied to skill types
- Anti-patterns section is useful
- Assembly procedure is concrete
- All 6 recommendations are preserved with execution detail and done-when criteria

**Remaining issues I'll address:**

1. **Model names slightly imprecise.** The document says "Claude Opus, GPT-5.4, Gemini 3.1 Pro" — the actual config uses `claude-opus-4-6`, `gpt-5.4`, `gemini-3.1-pro`. The document's shorthand is fine for readability but should match what operators see in config.

2. **`enrich_context.py` description is accurate but could be sharper.** The Source Rules table says it does "keyword extraction and governance search" — verified correct. But the table entry is long. The `--scope` parameter (review, define, challenge, debate, all) is operationally important and not mentioned — it controls what gets returned.

3. **The "13 subcommands in dispatch block" claim in Recent Context is presented as a finding from the A/B test.** The docstring lists 9 subcommands. This is fine as-is since it's reporting what the models found (they may have counted internal dispatch branches), but it should be clearly attributed as a model finding, not a document assertion.

4. **Missing: `enrich_context.py` has a `--scope` flag** that filters results by skill context. This is directly relevant to the spec — different skill types should use different scopes. The document doesn't mention this.

5. **Delivery Patterns section is somewhat abstract.** The three patterns (disk-based, temp-file, inline) are described generically. They could be tied to specific skills for clarity.

6. **The Source Rules table lists `scripts/research.py`** but the document doesn't explain what it does or when it's used in the assembly procedure. It's mentioned once and then dropped.

7. **Success Criteria are qualitative only.** Given the A/B test already established quantitative baselines (tool call counts, timing, convergence), the success criteria should reference those baselines.

8. **Recommendations lack priority ordering signal.** They're numbered but the priority rationale (high/medium/low frequency) is buried in the text rather than being a clear field.

## Round 4 (gemini-3.1-pro)
The previous revision did an excellent job organizing the document, establishing clear size budgets, and linking specific skills to specific enrichment scopes. The evidence, metrics, and new facts are well-integrated and properly preserved. 

To make this document even sharper and more executable (per the strategic posture), I have:
1. **Explicitly targeted files**: Updated all 6 recommendations to point directly to the `.claude/skills/<name>/SKILL.md` files that need to be modified, rather than using the generic "Update the skill" phrasing. 
2. **Hardened constraints**: Changed the "Anti-Patterns" section from a weak "Do not include" to a normative "MUST NOT include" to enforce strict boundaries on packet assembly. 
3. **Tightened phrasing**: Removed passive voice in a few execution details to ensure they read as direct engineering instructions.

## Round 5 (gpt-5.4)
The current revision is strong: it is specific, preserves the A/B evidence, defines a concrete packet structure, and gives executable recommendations per skill. It also improves credibility by adding a verification-backed “New Facts Introduced” section.

A few issues remain:

1. There is one mild internal inconsistency in size guidance:
   - The global “Standard Context Packet” says Project Context is required at 30–50 lines.
   - The healthcheck recommendation later specifies a minimal 10–20 line project state summary.
   This can be reconciled by making Healthcheck/Simulate an explicit compact-mode exception rather than leaving it implicit.

2. The success criteria rely on A/B tool-call baselines but do not define how to measure improvement operationally. The document should specify that success is judged over repeated runs by skill type, not a single run.

3. The “Recent Context” requirement says “last 2–3 relevant sessions,” while the Source Rules and Assembly Procedure say “last 3 relevant entries.” This should be normalized to “up to 3 relevant entries” to avoid forcing irrelevant material.

4. The document is generally decisive, but some implementation language can be sharpened further:
   - distinguish “required packet sections” from “allowed delivery mechanisms”
   - make clear that the standard applies to the effective input seen by `debate.py`, not necessarily one physical file

5. The “New Facts Introduced” section is useful and should be preserved. It also helps correct an ambiguity around the “13 subcommands” finding by clarifying it was a model observation, not a repository fact.

## Round 6 (claude-opus-4-6)
**Improvements made by previous reviewer:**
- Good structure: clear separation of evidence (A/B test, external validation), specification, and recommendations
- Verified facts section is valuable and mostly accurate
- Source Rules table and Size Budgets table are well-organized
- Delivery Patterns by Skill section adds useful implementation guidance
- Scope section correctly clarifies compiled vs. split delivery

**Issues found:**

1. **Minor factual imprecision in New Facts:** The document says `session-log.md` is "referenced in 6 skills" but `session-log.md` (exact) matches 5 times; `session-log` (bare) matches 6. Similarly, `current-state.md` matches 5, but the document says "5 skills" for that — which is correct. The `session-log` count should say "6 references across skills (5 as `session-log.md`, 1 as bare `session-log`)" or just "5–6 skills" to be precise. Minor issue.

2. **"investigate" listed as rich-context skill but not in Size Budgets correctly:** The A/B test evidence section says 4 skills have rich context: "challenge, review, think, investigate." But the Size Budgets table groups `investigate` under "Explore" alongside `explore`. The Skill-Specific Overrides table doesn't mention `investigate` at all. Meanwhile, `think` is listed as a rich-context skill but appears nowhere in the Size Budgets or Overrides tables. This is a gap — if `think` and `investigate` already have rich context, they should still appear in the tables for completeness, and the document should clarify they need no remediation.

3. **Redundancy between Source Rules and Skill-Specific Overrides:** Both tables specify `enrich_context.py --scope` mappings. The Overrides table repeats the scope values already in the Source Rules table. This could be tightened.

4. **Anti-Patterns section could be more actionable:** "Stale project context copied forward without checking whether it still reflects current state" is good but doesn't say how to prevent it. The assembly procedure should address this.

5. **Success Criteria tool-call numbers need context:** The document frames Run 2 tool-call counts as targets, but these numbers include legitimate artifact-analysis tool calls, not just reconstruction. The criteria should distinguish between reconstruction tool calls and analysis tool calls, or acknowledge this limitation.

6. **Missing: what happens when `enrich_context.py` returns empty results.** The script exits with empty arrays when no keywords are found. The spec should address this edge case — the packet is still valid without enrichment output, but skills should not skip the other required sections.

7. **The "compact-mode exception" under Project Context is vague.** It says "may be compressed below 30 lines" but doesn't give a floor. Given the healthcheck/simulate budget is 50–100 lines total, 10–20 lines for Project Context (as recommendation 5 specifies) is the right floor. This should be stated in the exception.

## Final Refined Document

# Context Packet Specification for Cross-Model Evaluation

## Project Context

Build OS is a governance framework for building with Claude Code. It treats Claude as a governed subsystem inside a real engineering workflow. The framework has 22 skills (composable procedures in `.claude/skills/*/SKILL.md`), a cross-model debate engine (`scripts/debate.py`, 4,136 lines, 9 subcommands), 17 hooks for runtime enforcement, and rules in `.claude/rules/`. This is a solo developer project.

The debate engine powers 5+ skills by sending proposals, documents, and code to 3 LLM models (claude-opus-4-6, gpt-5.4, gemini-3.1-pro) for independent evaluation — adversarial challenge, code review, iterative refinement, divergent exploration, and pressure-testing.

## A/B Test Evidence

We ran an A/B test on proposal quality passed to cross-model challengers:

- **Run 1 (thin, 52 lines, no project context):** Claude made 29 tool calls in 100s, GPT made 14 in 50s, Gemini made 3 in 21s. Findings were less specific. Gemini barely engaged. Models diverged — one said "scrap tests, ship to product work," another said "revise to add debate.py tests."
- **Run 2 (enriched, 150 lines, full project context):** Claude made 22 tool calls in 89s, GPT made 9 in 66s, Gemini made 6 in 27s. All 3 converged on the same finding (debate.py test coverage underweighted). Gemini completely flipped its position. Findings were more specific (models counted 13 subcommands in the dispatch block, identified tier classification as highest-risk area).

We then audited all 22 skills. 10 call `debate.py`. Of those, 4 have rich context (challenge, review, think, investigate) and 6 have thin or no project context (pressure-test, polish, elevate, explore, healthcheck, simulate).

## External Validation

Web research across 6 questions validated the A/B findings with 4 independent research streams:

1. **Google/ICLR 2025 "Sufficient Context"**: Insufficient context increases hallucination from 10.2% to 66.1%. Models don't abstain — they reconstruct badly.
2. **Databricks long-context RAG** (2,000+ experiments): Performance improves monotonically up to model-specific saturation. At 3–6K tokens we're far below saturation.
3. **Evaluation prompt design** (arXiv 2506.13639): Criteria + reference answers are the two highest-impact components. Chain-of-thought adds zero benefit when criteria are clear. High/low anchors beat full rubrics.
4. **Cross-model agreement**: Shared sufficient context eliminates degrees of freedom causing divergence.

## Problem

Every skill assembles context for `debate.py` ad hoc — some rich, some thin. The 6 thin-context skills (pressure-test, polish, elevate, explore, healthcheck, simulate) force models to waste tool calls reconstructing project basics, produce less specific findings, and diverge on recommendations.

## Objective

Standardize every `debate.py` invocation around the same minimum information set:

- what this project is,
- what changed recently,
- what artifact is being evaluated,
- what constraints or prior decisions matter now.

A model receiving the evaluation input must not need exploratory tool calls to reconstruct basic project context.

## Scope

This specification applies to any content passed into `debate.py` through proposal, document, input, question, or explicit context channels. It covers both:

- **compiled packets** where context is physically prepended to the artifact, and
- **split delivery** where the artifact is passed separately but the full context packet is supplied through a flag such as `--context`.

The requirement is **self-contained evaluation input**, not necessarily a single physical file. Compliance is judged on the combined effective input seen by `debate.py`.

---

## Standard Context Packet

Every debate input must be structured in this order at the logical-input level, whether delivered as one file or split across artifact + `--context`.

### 1. Project Context (required, default 30–50 lines)

State what the project is, what problem it solves, and the subsystem(s) relevant to this evaluation.

Include:
- one-sentence description of Build OS,
- the relevant operational domain,
- the specific components involved in this evaluation,
- current phase or active work when it changes how the artifact should be judged.

Do **not** paste a full architecture document. Include only the context needed to evaluate this artifact correctly.

**Primary sources:**
- `docs/current-state.md`
- project description from `CLAUDE.md` or `docs/the-build-os.md`

**Compact-mode exception:** For narrow healthcheck or simulation tasks, Project Context may be compressed to 10–20 lines if it still identifies the project, subsystem, and current operating state without forcing reconstruction. It must never be omitted entirely.

### 2. Recent Context (required, 20–30 lines)

Summarize the recent work arc that led to this evaluation.

Include:
- up to the last 3 relevant sessions,
- decisions already made,
- pivots or reversals,
- unresolved questions that affect evaluation criteria.

This section exists to stop the model from judging the artifact as if it appeared in a vacuum.

**Primary sources:**
- `tasks/session-log.md` — summarize up to the last 3 relevant entries
- `tasks/decisions.md` — include recent or still-active decisions when they constrain the artifact

### 3. Artifact (required, variable length)

The actual proposal, design doc, diff, prompt, question, or document being evaluated.

This remains the center of the packet. Context should frame the artifact, not bury it.

### 4. Evaluation-Specific Context (optional, 10–20 lines)

Add only when prior decisions, governance lessons, or domain constraints materially affect the judgment.

Examples:
- prior rejected approaches,
- governance constraints,
- security or reliability lessons from similar work,
- decision records that narrow acceptable options.

**Primary sources:**
- `scripts/enrich_context.py` output (use `--scope` to match skill type — see Skill-Specific Overrides below)
- `tasks/decisions.md`
- targeted governance docs or prior research

**Empty enrichment:** If `enrich_context.py` returns no results (no keywords extracted or no governance matches), the packet is still valid. Do not skip Project Context or Recent Context because enrichment returned nothing — those sections are independently required.

---

## Source Rules

| Source | Provides | Usage Rule |
|---|---|---|
| `docs/current-state.md` | Current phase, active work, blockers | **Always** — Extract 1–2 sentences relevant to the artifact. Verify content is current before each use; do not copy stale summaries forward. |
| `tasks/session-log.md` | Recent work arc, decisions, pivots | **Always** — Summarize up to the last 3 relevant entries |
| `scripts/enrich_context.py` | Proposal-linked lessons and decisions via keyword extraction and governance search. Accepts `--scope` (review, define, challenge, debate, all) and `--top-k` to control volume. Requires `--proposal`. | **When applicable** — Use when the evaluation starts from a proposal or document. See Skill-Specific Overrides for `--scope` mapping. |
| `tasks/decisions.md` | Decided and undecided architectural choices | **When the artifact touches decided areas** |
| `scripts/research.py` | External research grounding for tools, models, or techniques | **When the artifact depends on external tools, models, or techniques** — pass research output as Evaluation-Specific Context |

## Size Budgets

Target budgets define the operating range. The Databricks research (2,000+ experiments) confirms performance improves monotonically up to model-specific saturation. All three models (claude-opus-4-6, gpt-5.4, gemini-3.1-pro) have 128K-200K context windows. Previous budgets (1-8K tokens) were far too conservative — leaving significant quality on the table. Revised budgets push toward richer context while staying well below saturation.

| Skill type | Skills | Target total | Rationale |
|---|---|---|---|
| Challenge / pressure-test | challenge, pressure-test | 250–500 lines (8–16K tokens) | Deep evaluation is the highest-stakes use. Full project grounding, decision context, operational evidence, and evaluation anchors. |
| Review (code) | review | 200–400 lines (6–12K tokens) | Diff + system context + governance constraints. Reviewers need enough context to judge whether code fits the system, not just whether it compiles. |
| Explore / investigate | explore, investigate | 150–300 lines (4–10K tokens) | Research questions need project framing, constraint context, and enough background to avoid generic answers. |
| Polish / refine | polish, elevate | 150–250 lines (4–8K tokens) | Editing must stay aligned to project goals. Richer context prevents drift toward generic prose improvements. |
| Healthcheck / simulate | healthcheck, simulate | 100–200 lines (3–6K tokens) | Narrower tasks still benefit from real project context. Previous 50-100 floor was too lean. |
| Think (already rich) | think | 150–300 lines (4–10K tokens) | Already has rich context; budget revised upward for consistency. |

## Required Quality Bar

A valid context packet must satisfy all five criteria:

1. **Project-identifying** — A reviewer can tell what Build OS is and what subsystem is under evaluation.
2. **Time-anchored** — A reviewer can tell what has happened recently that affects judgment.
3. **Artifact-centered** — The artifact remains easy to find and is not drowned in prefatory text.
4. **Constraint-aware** — Known relevant decisions or governance constraints are included when they materially narrow valid recommendations.
5. **Minimal reconstruction burden** — A reviewer does not need to spend initial tool calls rediscovering project basics.

## Anti-Patterns

Context packets **MUST NOT** include:
- Full conversation history.
- Repeated framing that paraphrases the artifact.
- Chain-of-thought instructions in evaluation prompts (research shows zero benefit when criteria are clear).
- Full rubric dumps when a few explicit criteria or high/low anchors will do.
- Raw file dumps without summarization.
- Stale project context copied forward without checking `docs/current-state.md` for the current state. The assembly procedure requires reading this file fresh each time — not reusing a cached summary from a prior session.

---

## Assembly Procedure

### Canonical section order

1. Project Context
2. Recent Context
3. Artifact
4. Evaluation-Specific Context

Exception: if Evaluation-Specific Context is essential for interpreting the artifact (e.g., a prior rejected approach that the artifact responds to), it may appear immediately before the artifact. It must never precede Project Context.

### Canonical build steps

1. **Extract project context** — Read `docs/current-state.md` fresh (not from cache). Pull the current project description and the relevant current-state summary. Verify the content reflects the actual current phase.
2. **Summarize recent work** — Reduce up to the last 3 relevant `tasks/session-log.md` entries to a concise work arc (20–30 lines).
3. **Add artifact** — Insert the proposal, document, diff, or question being evaluated.
4. **Attach constrained prior context** — Run `scripts/enrich_context.py --proposal <artifact> --scope <skill-type>` when the artifact is a proposal or document. If enrichment returns empty results, proceed without it — the packet is still valid. Add decision or governance context only when it changes what counts as a good answer.
5. **Send to `debate.py` in self-contained form** — Either compile everything into one document or pass the artifact as the main argument + context packet through `--context`.

## Delivery Patterns by Skill

### Disk-based proposals (challenge, pressure-test, review)
For skills that operate on proposal files on disk, write the packet directly into the proposal or generated review document before invoking `debate.py`.

### Temp-file evaluations (elevate, polish)
For skills that construct temporary evaluation documents, prepend Project Context and Recent Context to the temp file, then add any evaluation-specific constraints.

### Inline evaluations (explore, healthcheck, simulate)
For skills that invoke `debate.py` with direct prompt text, place the artifact in the main argument and pass the rest of the packet through `--context`. The combined input must satisfy the self-contained requirement.

## Skill-Specific Overrides

| Skill type | Override |
|---|---|
| **Challenge / pressure-test** | Fullest project and recent context. Run `enrich_context.py --scope challenge`. These modes are most sensitive to under-specification. |
| **Review** | Architecture and governance context sufficient to judge the diff. Run `enrich_context.py --scope review` (decisions only, no lessons). Avoid unrelated history. |
| **Explore / investigate** | Project framing and known constraints so exploration stays relevant. Run `enrich_context.py --scope define`. Include `research.py` output when the question involves external tools or techniques. |
| **Polish / elevate** | Project purpose and active work so improvements do not drift toward generic prose edits. Run `enrich_context.py --scope define`. |
| **Healthcheck / simulate** | Compact context (10–20 line Project Context). Never omit current system framing. Run `enrich_context.py --scope all --top-k 3` to keep results tight. |
| **Think** | Already has rich context. No changes required. Included here so the table covers all 10 debate-calling skills. |

---

## Success Criteria

This specification is successful when debate inputs consistently produce:

1. **Tighter cross-model convergence** — All 3 models converge on core findings, as observed in Run 2 of the A/B test (vs. divergent recommendations in Run 1).
2. **Fewer reconstruction tool calls** — Reduction from Run 1 baselines (Claude 29, GPT 14, Gemini 3) toward Run 2 levels (Claude 22, GPT 9, Gemini 6) or better. Note: these counts include both reconstruction and legitimate analysis calls; the signal is directional reduction, not elimination.
3. **More artifact-specific recommendations** — Findings reference concrete project elements (specific files, line counts, subsystem names) rather than generic advice.
4. **Fewer contradictory recommendations** — Models do not produce opposing recommendations caused by missing context (e.g., "scrap tests" vs. "add tests").

Measure these outcomes across repeated runs of the affected skills, grouped by skill type. Do not declare success from a single favorable run.

It is **not** successful if packets become large but generic, or if skills satisfy the format mechanically while still omitting the decisions that actually constrain the artifact.

---

## Recommendations

### 1. pressure-test — Priority: HIGH

**Frequency:** High. **Current state:** Thin or no project context.

Modify `.claude/skills/pressure-test/SKILL.md` to read `docs/current-state.md` and `tasks/session-log.md`, injecting them directly into the input document. Execute `scripts/enrich_context.py --scope challenge` to append proposal-linked governance context.

**Execution detail:** Build the standard packet with 30–50 lines of Project Context, 20–30 lines of Recent Context, the target artifact, and the enrichment output. Use disk-based delivery (write packet into the proposal file before invoking `debate.py`).
**Done when:** Every `pressure-test` run sends a self-contained evaluation packet to `debate.py` instead of a thin standalone prompt.

### 2. elevate — Priority: MEDIUM

**Frequency:** Medium. **Current state:** Thin or no project context.

Modify `.claude/skills/elevate/SKILL.md` to prepend project context and recent session logs to the design document temp file before passing it to the debate engine.

**Execution detail:** Enforce the canonical order: Project Context → Recent Context → design document → relevant decisions (only if they constrain the design). Run `enrich_context.py --scope define`. Use temp-file delivery pattern.
**Done when:** The temp file given to `debate.py` contains enough project framing that an external reviewer can judge the design without reconstructing Build OS first.

### 3. polish — Priority: MEDIUM

**Frequency:** Medium. **Current state:** Thin or no project context.

Modify `.claude/skills/polish/SKILL.md` to wrap the target document with standard Project Context to prevent ungrounded stylistic edits.

**Execution detail:** Keep this lighter than challenge mode: inject compact Project Context and only the Recent Context needed to explain the document's purpose. Run `enrich_context.py --scope define`. Use temp-file delivery pattern.
**Done when:** `polish` outputs remain aligned to project intent rather than diverging into generic writing advice.

### 4. explore — Priority: MEDIUM

**Frequency:** Medium. **Current state:** Thin or no project context.

Modify `.claude/skills/explore/SKILL.md` to inject 30–50 lines of project context into the `--context` flag alongside the existing research data.

**Execution detail:** Inject Recent Context when the question is tied to an ongoing decision. Attach `research.py` output as Evaluation-Specific Context when the question involves external tools or techniques. Subordinate external research to the project framing. Use inline delivery pattern.
**Done when:** Exploration outputs explicitly answer the project's precise question rather than an abstract version of it.

### 5. healthcheck — Priority: LOW

**Frequency:** Low. **Current state:** Thin or no project context.

Modify `.claude/skills/healthcheck/SKILL.md` to prepend a minimal project state summary to the health evaluation input.

**Execution detail:** Use compact mode: extract current phase, active work, and the specific subsystem being health-checked; strictly omit unrelated history. Keep the Project Context block to 10–20 lines, and run `enrich_context.py --scope all --top-k 3`. Use inline delivery pattern.
**Done when:** The healthcheck evaluates the current, real-world operating state of Build OS, not an abstract software project.

### 6. simulate — Priority: LOW

**Frequency:** Low. **Current state:** Thin or no project context.

Modify `.claude/skills/simulate/SKILL.md` to inject recent structural decisions directly into the simulation prompt, grounding the simulation in current architecture.

**Execution detail:** Construct the input with a 10–20 line compact Project Context block, the recent decisions that define current system shape, and the simulation scenario. Run `enrich_context.py --scope all`. Use inline delivery pattern.
**Done when:** Simulation outputs operate entirely within present architecture and constraints instead of inventing a different system.

---

## New Facts Introduced

- Verified: `scripts/debate.py` exists and is 4,136 lines (confirmed via `read_file_snippet`).
- Verified: 10 skills reference `debate.py` (confirmed via `check_code_presence` on skills file set — 10 matches).
- Verified: `scripts/enrich_context.py` exists (146 lines), is a proposal-linked enrichment script that extracts keywords, searches governance files via `recall_search.py`, and returns structured JSON. It accepts a `--scope` flag with values `review`, `define`, `challenge`, `debate`, `all` that controls which governance sources are searched. The `review` scope returns decisions only; `define` returns decisions + limited lessons (top-k capped at 2); `challenge`, `debate`, and `all` return both with full top-k. It requires a `--proposal` argument.
- Verified: `config/debate-models.json` is present with version `2026-04-09`.
- Verified: The persona model map assigns `claude-opus-4-6` (architect), `gpt-5.4` (security), `gemini-3.1-pro` (staff, pm).
- Verified: `debate.py` docstring lists 9 subcommands (challenge, judge, refine, review, check-models, compare, verdict, outcome-update, stats). The "13 subcommands in dispatch block" was a model finding from the A/B test, not a document assertion.
- Verified: `debate.py` accepts a `--context` flag (1 match in scripts via `check_code_presence`).
- Verified: `scripts/enrich_context.py` has test coverage (`tests/test_enrich_context.py`). `scripts/debate.py` does not have test coverage.
- Verified: `docs/current-state.md` is referenced in 5 skills (exact match on `current-state.md`). `tasks/session-log.md` is referenced in 5 skills (exact match on `session-log.md`; 6 matches for bare `session-log`). The gap is that these references don't consistently flow into `debate.py` input packets.
- Verified: `enrich_context.py` is already referenced in 4 skills (the rich-context skills). The 6 thin-context skills do not use it.
- Verified: `scripts/research.py` exists (1 match in scripts) and is referenced in 5 skills.

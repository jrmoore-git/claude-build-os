---
debate_id: explore-redesign
created: 2026-04-10T23:23:02-0700
phase: refine
rounds: 6
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: no
---
# explore-redesign — Refined Document

## Round 1 (gemini-3.1-pro)
This is a highly structured, well-reasoned proposal. The problem statement is clear, the current failure modes are well-documented, and the proposed changes directly address the limitations. 

**Improvements made:**
- **Technical Completeness:** Added a minor technical specification under "Key Design Decisions" (Decision 2) to clarify *how* the derived dimensions are passed from the pre-flight model to the explore engine (e.g., via structured output/JSON) to ensure the prompt injection works reliably.
- **Clarity & Formatting:** Lightly polished headings and bullet points for maximum readability while preserving all operational context, proposed flows, and specific file recommendations.

## Round 2 (gpt-5.4)
The draft is already strong: it clearly identifies the mismatch between the current product-specific explore flow and the broader set of problem types users bring to `/debate`, and it preserves useful operational context.

Improvements made in this revision:
- Tightened structure so the problem, current behavior, proposed design, implementation scope, and risks flow more cleanly.
- Clarified where behavior changes are conceptual versus implementation-specific.
- Preserved all existing recommendations under **Proposed Changes / Files to Change** and kept the same 7 entries.
- Lightly refined wording to reduce repetition and make the proposal easier to review by engineering.
- Kept all evidence-bearing sections, especially **Current System Failures** and **Operational Context**, intact in substance.

Remaining issues addressed:
- The original draft mixed product goals, prompt-design details, and code-change list somewhat abruptly; this revision separates those concerns more clearly.
- “Adaptive tree” was slightly underspecified as a tree versus an inferred question loop; this revision clarifies that the “tree” is adaptive branching, not a fixed menu tree.
- Added a short implementation note on the structured handoff from pre-flight to divergence/synthesis, because that is central to making the design reliable.

## Round 3 (claude-opus-4-6)
This is a well-structured proposal. The previous revision (or original) is clear, logically organized, and preserves operational detail well. My review identifies the following areas for improvement:

1. **Redundancy between Problem and Current Flow sections.** The "Problem" section repeats much of what "Current Flow" demonstrates with evidence. These can be tightened without losing content.

2. **The "Proposed Changes / Files to Change" section is a hybrid.** It mixes being a recommendations list (numbered, actionable) and a file manifest. The section title uses both names ("Proposed Changes / Files to Change"), which is slightly ambiguous. I'll clarify this as the canonical recommendations section and ensure all 7 items are preserved.

3. **Missing detail on the structured handoff format.** Key Design Decision #6 says pre-flight should produce structured output, and #2 has a technical note about JSON, but there's no indication of what that schema might look like — even a sketch would help reviewers evaluate feasibility.

4. **The Risks section could be slightly more honest about risk #1.** "The model needs to be good at inferring domains" is understated — this is the central bet of the proposal. I'll flag this more clearly without overstating it.

5. **Open Questions are good but missing one obvious one:** What happens when a question spans multiple domains (e.g., "Should we build or buy an identity resolution system?" is simultaneously product, engineering, and strategy)?

6. **Minor structural issue:** "Acceptance Criteria" reads as a mix of acceptance criteria and success metrics. It's fine but could use a small framing adjustment.

7. **The Recommendation section is a single recommendation.** I'll preserve it fully per the hard rule.

No errors or regressions detected — this is an improvement pass, not a correction pass.

## Round 4 (gemini-3.1-pro)
The previous revision is very strong, logically structured, and clearly articulates the problem and solution. The technical details (JSON schema, file paths, line numbers) are well-integrated. 

For this revision, I focused on light polish:
- Tightened the phrasing in the Summary and Problem sections to make the core argument punchier.
- Improved the formatting of the "Risks & Mitigations" section to make the mitigations stand out more clearly.
- Ensured absolute preservation of the "Current System Failures", "Operational Context", "Proposed Changes", and final "Recommendation" sections as required by the system constraints. 
- Maintained all technical specifics and file references without alteration.

## Round 5 (gpt-5.4)
The revision is strong: it clearly identifies the core failure mode, preserves the working orchestration, and translates the redesign into concrete file-level changes. The structure is logical and the operational context is appropriately preserved.

Remaining improvements:
- The document used both “single inferred domain” and “multi-domain” framing. I clarified that domain inference may yield one or more domains so the design is internally consistent.
- The structured handoff was identified as critical, but the proposal did not clearly state what should happen when validation fails. I added explicit fallback behavior and validation expectations without changing the core recommendation.
- A few implementation details were under-explained, especially around schema stability and prompt compatibility. I tightened those sections so acceptance criteria better match the proposed design.
- The document had a singular “## Recommendation” section rather than “## Recommendations” or “## Proposed Changes”; the existing recommendation is preserved and slightly sharpened with caveats rather than removed.
- Some wording was repetitive around product-specific assumptions. I reduced minor redundancy while keeping all factual and operational content intact.

## Round 6 (claude-opus-4-6)
The current revision is strong. It's well-structured, clearly written, and preserves all operational evidence and recommendations. My observations:

1. **No errors or regressions introduced** — the previous reviewer did good work. Evidence sections are intact, recommendations are preserved and numbered, and the proposal logic flows well.

2. **Minor structural issue**: The "Proposed Changes" section (7 numbered items) and the "Recommendation" section (1 item) both function as recommendations. The previous revision correctly preserved all of them. I'll keep them intact.

3. **Clarity improvements available**:
   - The Summary and Problem sections overlap significantly. The Problem section essentially restates the Summary with slightly more detail. I can tighten this without losing content.
   - "Key Design Decisions" is the longest section and could benefit from a brief orienting sentence at the top so readers know what they're walking into.
   - The Open Questions section has a parenthetical "(See Risk #4 for initial thinking.)" and "(See the sketch in Decision #2 as a starting point.)" — these cross-references are helpful but the last bullet partially duplicates an earlier one. I'll consolidate.

4. **One substantive gap**: The proposal doesn't address **latency impact**. The current 3-bucket classification is essentially free (menu selection). The proposed adaptive pre-flight adds a model inference call to generate domain classification, forcing questions, and structured dimensions — all before divergence even begins. This deserves at least a mention in Risks, even if the answer is "we accept it."

5. **Minor wording issues**: A few phrases are slightly redundant ("domain or domains" appears 5 times — fine in the schema spec, but repetitive in prose). The phrase "The model reads the question" could be more precise about which model call this is.

6. **The Acceptance Criteria are solid** but could be slightly tightened — one criterion says "roughly the current behavior and quality" which is vague for an acceptance criterion.

Overall this is a well-crafted proposal. My revision focuses on: tightening the Summary/Problem overlap, adding the latency risk, sharpening a few acceptance criteria, reducing minor redundancy, and improving section transitions — while preserving every fact, measurement, recommendation, and structural element.

## Final Refined Document

---
scope: explore mode redesign
created: 2026-04-10
status: draft
---

# Proposal: Adaptive Tree-Based Explore Mode

## Summary

Explore mode in `/debate` is currently hardcoded for product-market questions. The divergence dimensions, pre-flight questions, synthesis framing, and context injection label all assume the user is exploring a commercial product opportunity. While this works well for product ideation, it degrades severely for engineering, research, organizational, or strategy questions — forcing those problems into rigid, product-specific dimensions.

This proposal redesigns explore mode into a general-purpose divergent thinking flow. Instead of routing users into one of three fixed pre-flight buckets with hardcoded product dimensions, the system will dynamically infer the problem domain, generate adaptive forcing questions, derive relevant divergence dimensions, and use those custom dimensions throughout divergence and synthesis.

The goal is to retain the existing multi-round orchestration — which works exceptionally well — while stripping out the product-anchored assumptions that make the current experience brittle for non-product exploration.

## Problem

When a user asks an engineering operations question, a research question, or an organizational question, the explore engine either forces the query into a product-market framing or outputs irrelevant dimensions. The root causes are specific and structural:

- Pre-flight classifies every question into one of three product-oriented buckets (Product / Solo Builder / Architecture).
- Divergence dimensions are hardcoded: customer, revenue, distribution, product form, wedge.
- Synthesis clusters on "the customer it targets" and "the core bet."
- The context injection label is "Market Context."

Any question that doesn't fit the 3 buckets gets shoehorned into the closest one. The explore engine should serve as the general-purpose divergent thinking tool for BuildOS — applicable to any problem where iterative, single-model exploration followed by cross-model refinement is valuable.

## Current System Failures

These are observed failure modes, not hypotheticals:

- Engineering ops questions (e.g., "How do we improve CZ velocity?") get asked "who pays?" and "what's the adoption barrier?"
- Research questions (e.g., "What's the right approach to identity resolution?") get forced into "name the first customer, first dollar"
- Organizational questions (e.g., "How should we structure the platform team?") get divergence on "revenue model" and "distribution channel"
- Any question that doesn't fit the 3 buckets gets shoehorned into the closest one

## Current Flow

```text
User input → classify into 3 buckets (Product / Solo Builder / Architecture)
  → load corresponding preflight file → ask canned questions from that file
  → compose answers into fixed context format
  → inject into product-anchored explore prompts with hardcoded dimensions
    (customer, revenue, distribution, product form, wedge)
  → 3 rounds of forced divergence on those dimensions
  → synthesis that clusters on "customer it targets" and "core bet"
```

The 3-bucket classification, canned questions, and hardcoded dimensions are the root causes of the failures above. The orchestration pattern itself — gather context, diverge in rounds, synthesize — is fundamentally sound.

## Design Goal

Explore mode must become domain-adaptive without altering its overall interaction pattern. The system should still:
- Gather just enough context up front.
- Generate multiple divergent directions.
- Force contrast across rounds.
- Synthesize the tradeoffs at the end.

The core change is *how* the system determines which dimensions matter for a given query.

## Proposed Flow: Adaptive Tree

```text
"What do you want to explore?" (open-ended, no menu)
  → User states their question/problem
  → Model reads the question and infers:
      1. The domain(s) (product, engineering, organization, research, strategy, etc.)
      2. The relevant divergence dimensions for THIS question
      3. Which forcing questions would break the user's default framing
  → Adaptive questions (2–4, one at a time, push for specificity)
  → Compose context with DERIVED dimensions
  → Inject dimensions into GENERIC explore prompts
  → 3 rounds of forced divergence on the DERIVED dimensions
  → Synthesis that compares on axes relevant to THIS question
```

The "adaptive tree" is not a fixed menu tree. It is a dynamic branching interaction where the model infers the problem type and selects the next best forcing question based on the user's initial prompt and subsequent answers.

## Key Design Decisions

This section details the six design decisions that together define the adaptive redesign. Decisions #1–#2 cover the pre-flight changes, #3–#4 cover downstream prompt changes, and #5–#6 cover integration and reliability.

### 1. Pre-flight becomes adaptive, not routed

Instead of classifying into a bucket and loading a canned questionnaire, the model reads the user's question and generates appropriate forcing questions on the fly.

The existing pre-flight files (`preflight-product.md`, `preflight-solo-builder.md`, `preflight-architecture.md`) become **reference libraries** — examples of effective forcing questions for specific domains. The model can draw from them when applicable but is not constrained by them.

A new `config/prompts/preflight-adaptive.md` provides the meta-prompt: how to read a question, infer the domain(s), select or generate forcing questions, derive divergence dimensions, and emit structured output.

### 2. Divergence dimensions are derived, not hardcoded

The current `explore-diverge.md` hardcodes 5 dimensions: customer, revenue, distribution, product form, wedge. These are meaningless outside of product questions.

The new approach: pre-flight produces a set of 4–6 divergence dimensions specific to the question. These derived dimensions must be output by the pre-flight model as structured data so they can be reliably injected into subsequent divergence and synthesis prompts.

**Sketch of the structured output:**

```json
{
  "domains": ["engineering_ops"],
  "dimensions": [
    {"name": "team_structure", "description": "How the team is organized to do this work"},
    {"name": "tooling_approach", "description": "Build vs. buy vs. integrate for key tooling"},
    {"name": "process_model", "description": "Cadence, review gates, release strategy"},
    {"name": "automation_level", "description": "What's manual vs. automated vs. AI-assisted"},
    {"name": "feedback_mechanism", "description": "How the team learns whether changes worked"}
  ],
  "context_summary": "...",
  "forcing_questions_used": ["...", "..."]
}
```

The exact schema will be finalized during implementation, but the key requirement is that `dimensions` is a list of named, described items that downstream prompts can consume programmatically.

At minimum, the structured handoff should include:
- inferred domain(s),
- normalized context,
- derived dimensions,
- forcing questions used,
- and any additional fields required by divergence and synthesis.

**Examples of derived dimensions by domain:**
- **Product question:** customer segment, revenue model, distribution, product form, wedge
- **Engineering ops question:** team structure, tooling approach, process model, automation level, feedback mechanism
- **Research question:** methodology, scope, data sources, theoretical framework, success criteria
- **Organizational question:** reporting structure, decision rights, communication model, hiring profile, success metric

These dimensions are injected into the diverge prompt as a variable (`{dimensions}`), not baked into the prompt text.

### 3. Explore prompts become dimension-agnostic

The core explore, diverge, and synthesis prompts will be stripped of product-specific language.

Examples of specific rewrites:
- "strategic thinker proposing a direction for a product" → "thinker proposing a direction for a problem"
- "Name the first customer, first use case, first dollar" → "Be specific. Name the first concrete action, who it affects, what changes."
- "the core bet it makes and the customer it targets" → "the core bet it makes and the key tradeoff"
- "no mainstream VC would fund" → "feels uncomfortable or contrarian"
- "Market Context" → "Context"

The ERRC grid stays, because eliminate / reduce / raise / create is domain-agnostic and universally applicable.

### 4. Synthesis adapts to the question domain

Instead of clustering on "customer/revenue/distribution," the synthesis prompt will receive the derived dimensions and cluster on those specific axes.

The comparison table columns — Timeline, Risk, What you learn, Strategic sacrifice — are general enough to remain unchanged.

### 5. The hardcoded fallbacks in `debate.py` update too

Lines 2118–2219 contain the v0 hardcoded prompts. These require the same domain-agnostic treatment so the fallback path functions correctly for non-product questions.

The fallback path should remain structurally aligned with the prompt-file path: same context label, same dimension injection model, and the same expectations about dimension-aware synthesis. If structured pre-flight output is unavailable or invalid, the fallback path should fail visibly or use an explicit safe fallback rather than silently reverting to product-default dimensions.

### 6. Structured handoff is part of the design, not an implementation detail

This redesign depends heavily on a reliable handoff between pre-flight and later rounds. The pre-flight step must produce:
- normalized context,
- inferred domain(s),
- derived dimensions (as structured data per Decision #2),
- and any other fields required by divergence and synthesis.

Without this structure, the system risks silently falling back to vague or product-default behavior. This is the highest-risk integration point in the proposal.

## Operational Context

### What Stays the Same
- The 3-round structure (first direction → forced divergence → synthesis) is sound.
- The two-phase brainstorm-then-commit within each round is sound.
- The ERRC grid in round 2+ is domain-agnostic and stays.
- The synthesis comparison table (Timeline, Risk, What you learn, Strategic sacrifice) is general enough.
- Temperature 1.0 for exploration rounds.
- The `debate.py explore` CLI interface stays the same — the prompts change, not the orchestration.
- Pre-flight files stay as reference material.

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| **Pre-flight routing** | 3-bucket classification menu | Open question → adaptive inference |
| **Pre-flight questions** | Canned from one of 3 files | Generated/selected based on question domain |
| **Divergence dimensions** | Hardcoded: customer, revenue, distribution, product form, wedge | Derived from pre-flight, injected as variable |
| **explore.md** | Product-specific language | Domain-agnostic with `{dimensions}` slot |
| **explore-diverge.md** | Product dimensions hardcoded | `{dimensions}` injected from context |
| **explore-synthesis.md** | Clusters on customer/revenue | Clusters on derived dimensions |
| **Context label** | "Market Context" | "Context" |
| **debate.py fallbacks** | Product-anchored | Domain-agnostic |
| **SKILL.md Step 3a** | 3-option menu | Open question + adaptive tree |

## Proposed Changes

The following are the specific file-level changes required for implementation:

1. **`config/prompts/explore.md`** — Remove product-specific language and add a `{dimensions}` slot for derived dimensions.
2. **`config/prompts/explore-diverge.md`** — Replace hardcoded dimensions (customer, revenue, distribution, product form, wedge) with a `{dimensions}` variable.
3. **`config/prompts/explore-synthesis.md`** — Replace hardcoded clustering dimensions with derived dimensions from pre-flight output.
4. **`config/prompts/preflight-adaptive.md`** — NEW file. Meta-prompt for adaptive pre-flight: domain inference, forcing question generation, dimension derivation, structured output schema, and quality rules for acceptable dimensions.
5. **`scripts/debate.py` lines 2118–2219** — Rewrite v0 hardcoded fallback prompts to be domain-agnostic, matching the updated prompt files.
6. **`scripts/debate.py` line 3112** — Change "Market Context" label to "Context".
7. **`.claude/skills/debate/SKILL.md` Step 3** — Replace the 3-option bucket menu with the adaptive tree flow (open question → model inference → adaptive forcing questions).

## Risks & Mitigations

1. **Adaptive pre-flight quality depends on the session model.** The entire adaptive behavior rests on the model's ability to infer domains and generate good forcing questions. If the session model is weak or inconsistent, everything downstream degrades.
   * **Mitigation:** The reference files (`preflight-product.md`, etc.) provide worked examples the model can pattern-match against. The `preflight-adaptive.md` meta-prompt should include explicit few-shot examples. Add a validation step that checks derived dimensions against minimum quality criteria (e.g., at least 4 dimensions, each with a non-empty description). If validation fails, do not silently proceed with product-default dimensions; instead use an explicit fallback path or surface a recoverable error.

2. **Dimension drift.** If the derived dimensions are too abstract or too specific, the divergence rounds may not produce meaningfully different directions.
   * **Mitigation:** The `preflight-adaptive.md` meta-prompt must include explicit examples of good vs. bad dimensions, with guidance on the right level of abstraction.

3. **Backwards compatibility.** Users who liked the product-focused explore mode get a different experience.
   * **Mitigation:** If the model infers the product domain, it should naturally produce the same dimensions and questions as before, using the product pre-flight file as reference material. This should be verified during acceptance testing.

4. **Multi-domain questions.** Some questions span multiple domains (e.g., "Should we build or buy an identity resolution system?" is simultaneously product, engineering, and strategy).
   * **Mitigation:** The `preflight-adaptive.md` meta-prompt should instruct the model to select dimensions from multiple domains when warranted, rather than forcing a single domain classification. The domain field in the structured output supports a list rather than a single value.

5. **Schema drift between prompt files and runtime code.** The proposal depends on prompt outputs and `debate.py` consuming the same structure. If the schema changes in one place but not the other, the system may degrade in subtle ways.
   * **Mitigation:** Define one canonical schema contract for pre-flight output and validate it at the boundary before divergence begins. Keep fallback prompts and prompt-file paths aligned to that same contract.

6. **Latency from adaptive pre-flight.** The current 3-bucket classification is a menu selection — effectively zero latency. The adaptive pre-flight adds a model inference call (domain classification, forcing question generation, dimension derivation, and structured output) before divergence begins. This adds at least one full model round-trip to the flow.
   * **Mitigation:** The adaptive pre-flight replaces the canned question loading, not the entire pre-flight interaction — the user still answers 2–4 questions sequentially, so the additional latency is concentrated in the initial inference call rather than spread across the session. If this proves noticeable, the domain inference and first forcing question can be generated in a single call to minimize round-trips. Monitor wall-clock time for the pre-flight phase during acceptance testing.

## Acceptance Criteria

A successful implementation should satisfy the following:

- Non-product questions no longer receive obviously product-specific forcing questions (e.g., "who pays?" for an engineering ops question).
- Pre-flight outputs structured dimensions that are consumed directly by divergence and synthesis prompts — no silent fallback to hardcoded dimensions.
- Product questions produce dimensions and forcing questions equivalent to the current product pre-flight (customer, revenue, distribution, product form, wedge), verified by running at least 3 representative product questions through both old and new paths and comparing output quality.
- The fallback path in `debate.py` (lines 2118–2219) remains functionally aligned with the prompt-file path.
- The CLI experience remains unchanged except for the removal of the fixed bucket menu.
- Multi-domain questions produce mixed-dimension outputs without being forced into a single-domain template.
- Invalid or low-quality structured pre-flight output is detected before divergence begins, with explicit fallback or recovery behavior rather than hidden regression.

## Open Questions

- Should the inferred domain be surfaced to the user, or remain internal?
- Should users be allowed to override or edit the inferred dimensions before divergence begins?
- How strict should the schema for derived dimensions be in the pre-flight output? (See the sketch in Decision #2 as a starting point.)
- Do we want a small set of canonical cross-domain dimension types, or fully freeform dimensions per question?
- How should multi-domain questions be handled at the dimension level — merged flat list, or grouped by domain? (See Risk #4 for initial thinking.)
- Should failed schema validation trigger a user-visible retry, an internal regeneration attempt, or a simplified fallback mode?

## Recommendation

Proceed with the adaptive redesign, but treat the structured pre-flight output as a required part of the change rather than a nice-to-have. Prompt rewrites alone will not be sufficient if the system still passes weak or inconsistent dimensions into later rounds. Specifically: implement the structured output schema (Decision #2) and the validation/fallback behavior (Risk #1 mitigation) before treating the prompt rewrites as complete.

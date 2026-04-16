---
topic: context-packet-anchors
created: 2026-04-15
type: design-handoff
---
# Dynamic Evaluation Anchors — Design Handoff for Next Session

## What This Is

This document is the complete context for implementing dynamic high/low evaluation anchors and expected-outcome framing in debate.py. It covers the research basis, the design approach, open questions, and all A/B test data from the current session.

Read this document, `tasks/context-packet-spec-refined.md`, and `tasks/challenge-pipeline-fixes-proposal.md` before starting work.

## Background: Why Anchors Matter

### The Research (arXiv 2506.13639 — Evaluation Prompt Design)

The paper studied which components of evaluation prompts have the most impact on LLM-as-judge quality. Findings:

1. **Criteria + reference answers** are the two highest-impact components. Everything else (formatting instructions, chain-of-thought, rubric detail) is noise.
2. **Chain-of-thought adds zero benefit** when criteria are already clear.
3. **High/low anchors beat full rubrics.** A simple "here's what excellent looks like / here's what poor looks like" outperforms detailed 5-point scales.

### What We're Already Doing
- Context packets (Project Context, Recent Context, Artifact, Evaluation-Specific Context) — DONE, shipped to all 6 thin-context skills
- Anti-patterns (banned CoT instructions, rubric dumps, conversation history) — DONE, in spec
- Increased size budgets (roughly 2x across all skill types) — DONE, in spec + skills

### What We're NOT Doing (the gap)
1. **No high/low anchors** — we tell models what format to use (MATERIAL/ADVISORY, TYPE tags) but not what a GOOD vs BAD evaluation looks like for THIS specific artifact.
2. **No expected outcomes / reference answers** — we give models the artifact and context but never anchor what a good evaluation should engage with.

## The Design Approach

### Core Insight: Anchors Must Be Artifact-Specific

Static anchors ("be specific, cite evidence") are generic advice. The research shows anchors work because they calibrate the evaluator's quality bar for THIS specific task. A challenge on a security proposal needs different anchors than a challenge on a UI feature.

The solution: **per-skill-type anchor templates with dynamic slot-filling from the context packet.**

### Architecture: Templates + Slots

**Templates** are constant per skill type (6 types). **Slots** are filled from the artifact being evaluated.

#### Template for `/challenge` and `/pressure-test`:

```
HIGH ANCHOR: A strong evaluation of this proposal...
- References specific evidence from: {SYSTEMS} (named components/files in the proposal)
- Quantifies risk or cost using: {METRICS} (operational numbers from the proposal)
- Weighs cost-of-building against cost-of-not-building using: {FAILURES} (from Current System Failures)
- Checks commodity or feasibility claims against: {REQUIREMENTS} (specific requirements, not category match)
- Engages with the operational evidence: {EVIDENCE} (from Operational Evidence section, if present)

LOW ANCHOR: A weak evaluation of this proposal...
- Makes generic observations about "complexity" or "risk" without citing evidence from the proposal
- Ignores the operational data and metrics provided
- Claims existing tools solve the problem without matching specific requirements
- Treats "no reported failures" as evidence of stability
- Could apply to any project — nothing is specific to this system
```

#### Template for `/review`:

```
HIGH ANCHOR: A strong review of this diff...
- Identifies logic errors referencing: {SYSTEMS} (components this code touches)
- Considers edge cases specific to: {CONSTRAINTS} (system constraints from context)
- Checks the diff against: {DECISIONS} (governance decisions that constrain the implementation)
- Verifies that the code handles: {FAILURE_MODES} (failure scenarios relevant to this subsystem)

LOW ANCHOR: A weak review of this diff...
- Comments on style, naming, or formatting without substance
- Makes vague "potential issues" claims without evidence from the codebase
- Reviews the code in isolation, ignoring the system it lives in
- Doesn't reference any project-specific constraints or decisions
```

#### Template for `/explore`:

```
HIGH ANCHOR: Strong exploration directions...
- Each direction engages with: {CONSTRAINTS} (the specific constraints and context provided)
- Directions differ on multiple dimensions, not just implementation detail
- At least one direction challenges the question's premise
- Recommendations reference: {SYSTEMS} (existing project capabilities or components)

LOW ANCHOR: Weak exploration directions...
- Directions are variations of the same approach
- Ignores project constraints and explores in the abstract
- All directions converge on the obvious answer with minor variations
- No direction questions whether the question itself is right
```

#### Template for `/polish` and `/elevate`:

```
HIGH ANCHOR: Strong refinement of this document...
- Improvements align with: {PROJECT_GOALS} (the project's current phase and objectives)
- Edits preserve and strengthen: {EVIDENCE} (operational data, metrics, and evidence in the document)
- Suggestions reference: {SYSTEMS} (specific project components and constraints)

LOW ANCHOR: Weak refinement...
- Generic writing advice that could apply to any document
- Removes or weakens operational specifics in favor of "cleaner" prose
- Edits drift toward abstract quality without grounding in project context
```

#### Template for `/healthcheck` and `/simulate`:

```
HIGH ANCHOR: Strong evaluation of this system state...
- References: {SYSTEMS} (specific components and their current operational state)
- Identifies issues using: {METRICS} (concrete measurements, not hypotheticals)
- Recommendations are actionable within: {CONSTRAINTS} (current project phase and priorities)

LOW ANCHOR: Weak evaluation...
- Generic health observations that could apply to any software project
- Recommendations ignore the current project phase and priorities
- No reference to specific operational data or system state
```

### Slot-Filling Mechanism

The slots (`{SYSTEMS}`, `{METRICS}`, `{FAILURES}`, etc.) are filled by scanning the assembled context packet. This is a ~50-line Python function in debate.py:

```python
def _extract_anchor_slots(proposal_text: str) -> dict:
    """Extract slot values from the context packet for anchor generation."""
    slots = {}
    
    # SYSTEMS: file paths and component names
    # Regex: paths matching scripts/, tasks/, .claude/, hooks/, config/, docs/
    # Plus: first nouns after ## headers in Project Context section
    
    # METRICS: numbers with units or percentages
    # Regex: \d+[\.\d]*\s*(lines|files|tests|runs|times|entries|violations|%|KB|tokens)
    
    # FAILURES: bullet points from "Current System Failures" section
    # Parse: content between "### Current System Failures" and next "###"
    
    # REQUIREMENTS: bullet points from "Proposed Approach" section
    # Parse: content between "## Proposed Approach" and next "##"
    
    # EVIDENCE: content from "Operational Evidence" section (new in Layer 1)
    # Parse: content between "### Operational Evidence" and next "###"
    
    # DECISIONS: decision IDs (D\d+) and their one-line summaries
    # Regex: D\d+ from Prior Decisions section
    
    # CONSTRAINTS: lines containing "must", "never", "always", "required"
    # From Evaluation-Specific Context section
    
    # PROJECT_GOALS: current phase and active work
    # From Project Context section, first 2-3 sentences
    
    return slots
```

Then a `_build_anchors(proposal_text: str, skill_type: str) -> str` function that:
1. Calls `_extract_anchor_slots(proposal_text)`
2. Selects the template for the skill_type
3. Fills the slots
4. Returns the formatted anchor text

### Where It Gets Injected

debate.py already constructs system prompts for challengers/reviewers. The anchors get injected into the system prompt, after the formatting instructions and before the artifact.

Current system prompt structure in debate.py (approximate):
```
You are a [persona]. Evaluate this proposal...
[formatting instructions: TYPE tags, MATERIAL/ADVISORY, etc.]
[the proposal/artifact]
```

New structure:
```
You are a [persona]. Evaluate this proposal...
[formatting instructions: TYPE tags, MATERIAL/ADVISORY, etc.]

## Evaluation Quality Anchors
[filled HIGH anchor]
[filled LOW anchor]

[the proposal/artifact]
```

### The "Expected Outcomes" Question

The arXiv paper's #1 finding is "reference answers" — what a good answer looks like. This is harder than anchors because we can't predict what the evaluation should find (if we could, we wouldn't need the models).

**What we CAN do:** tell the model which parts of the input deserve scrutiny without telling it what conclusion to reach.

Approach: generate a "focus directive" from the context packet:

```
## What This Evaluation Should Engage With
Given the operational evidence and context provided, a thorough evaluation should:
- Assess whether {FAILURES} justify the proposed approach
- Verify whether {EVIDENCE} supports the claimed need (don't take it at face value)
- Check whether the proposed approach addresses {CONSTRAINTS} or ignores them
- Consider what happens if this work is NOT done (the cost of inaction from Current System Failures)
```

This is not a reference answer — it's a reference ENGAGEMENT. It tells the model what to look at, not what to conclude. The slots come from the same `_extract_anchor_slots` function.

### Open Questions for Implementation

1. **Should anchors be visible to the user?** Current thinking: no. They're internal prompt engineering. But the user could see them in debug mode or `--verbose` output.

2. **How to handle empty slots?** If the proposal has no Operational Evidence (greenfield), the anchor template should degrade gracefully — skip the evidence-related anchor lines rather than producing "Engages with the operational evidence: (none)".

3. **Should the focus directive be per-model or shared?** Current thinking: shared. All 3 models get the same anchors. This preserves the convergence benefit from shared context (proven in A/B test). Per-model anchors would reintroduce divergence.

4. **Where do anchor templates live?** Options:
   - Hardcoded in debate.py (simplest, but another thing in a 4,136-line file)
   - In `config/anchor-templates.json` or `config/anchor-templates/` (more maintainable)
   - In each skill's SKILL.md (most explicit, but spreads logic across 10 skills)
   
   Recommendation: `config/anchor-templates/` directory with one file per skill type. debate.py reads the template, fills slots, injects.

5. **Testing strategy:** `_extract_anchor_slots` is a pure function — add to `tests/test_debate_pure.py`. Template filling is also pure. The integration (injecting into system prompts) needs a test that verifies the prompt includes anchor text when a proposal is provided.

## A/B Test Data for Validation

### Prior Session A/B (next-build-priorities topic)

| Metric | Run 1 (thin, 52 lines) | Run 2 (enriched, 150 lines) |
|--------|----------------------|---------------------------|
| Claude tool calls | 29 (100s) | 22 (89s) |
| GPT tool calls | 14 (50s) | 9 (66s) |
| Gemini tool calls | 3 (21s) | 6 (27s) |
| Convergence | Diverged ("scrap tests" vs "add tests") | Converged (all agreed on debate.py test gap) |
| Specificity | Generic | Counted 13 dispatch branches, identified tier classification risk |

### This Session A/B (challenge-pipeline-fixes topic)

| Metric | Run A (thin, 45 lines) | Run B (enriched, 89 lines) |
|--------|----------------------|---------------------------|
| Claude tool calls | 34 (95.6s, hit max) | 40 (100.1s, hit max) |
| GPT tool calls | 13 (22.3s) | 19 (25.7s) |
| Gemini tool calls | 1 (24.6s) | 5 (33.8s) |
| Convergence | All REVISE (approve L1-L2, defer L3-L4) | Same verdict but richer reasoning |
| Specificity (thin) | "enumerate the 6 skills" (doesn't know which) | N/A |
| Specificity (enriched) | N/A | Verified --verify-claims is dead code (1 match, 0 implementations); security concern about leaking context to Perplexity; greenfield bias risk for empty Operational Evidence |
| Novel findings | 2-3 unique across models | 5+ unique, including security and bias concerns |

**Key insight from this A/B:** Enriched context increased tool calls (not decreased). Models spent MORE time analyzing deeper, not LESS time reconstructing. This suggests we're in the "quality monotonically improves with context" zone from the Databricks research — adding anchors on top of richer context should compound the improvement.

### Baseline for Anchor A/B Test

The next session should run the same proposal through debate.py twice:
1. With current system (enriched context, no anchors)
2. With anchors injected into the system prompt

Compare: specificity of findings, whether findings engage with the anchor-highlighted aspects, and whether low-anchor behaviors are avoided.

## What Was Already Shipped This Session

### Layer 1: Operational Evidence section
- Added `## Operational Evidence` to `/challenge` proposal template (Step 3 in SKILL.md)
- Three questions: tried before? data exists? before/after?

### Layer 2: Context packets for 6 thin-context skills
All 6 skills edited with context assembly steps:

| Skill | Delivery | enrich_context.py --scope |
|-------|----------|--------------------------|
| pressure-test | inline (--context) | challenge |
| elevate | temp-file | define |
| polish | temp-file ($WRAPPED_DOC) | define |
| explore | inline (prepend to PREFLIGHT_CONTEXT) | define |
| healthcheck | inline | all --top-k 3 |
| simulate | inline (EVAL_INPUT heredoc) | all |

### Budget increases (per Databricks research)
All size targets roughly doubled:

| Section | Old | New |
|---------|-----|-----|
| Project Context | 30-50 lines | 50-100 lines |
| Recent Context | 20-30 lines | 40-80 lines |
| Eval-Specific Context | 10-20 lines | 20-40 lines |
| Compact mode (healthcheck/simulate) | 10-20 lines | 20-40 lines |
| Challenge/pressure-test total | 150-250 lines (4-8K) | 250-500 lines (8-16K) |
| Review total | 100-200 lines (3-6K) | 200-400 lines (6-12K) |
| Explore/investigate total | 80-150 lines (2-4K) | 150-300 lines (4-10K) |
| Polish/elevate total | 80-120 lines (2-4K) | 150-250 lines (4-8K) |
| Healthcheck/simulate total | 50-100 lines (1-3K) | 100-200 lines (3-6K) |

### Proposal for deferred work
`tasks/challenge-pipeline-fixes-proposal.md` — covers Layers 1-4. Layers 1-2 shipped. Layers 3-4 (claim verification, dissent requirement) deferred pending evidence that L1-L2 are insufficient.

## Files to Read First Next Session

1. This file (`tasks/context-packet-anchors-design.md`)
2. `tasks/context-packet-spec-refined.md` — the full spec with updated budgets
3. `tasks/challenge-pipeline-fixes-proposal.md` — the proposal covering all 4 layers
4. `tasks/challenge-pipeline-enriched-findings.md` — the latest A/B results
5. `scripts/debate.py` lines ~2390-2430 — where the challenger system prompts are constructed (this is where anchors would be injected)

## Recommended Next Steps

1. **Build `_extract_anchor_slots()` and `_build_anchors()` in debate.py** — pure functions, ~80-100 lines total. Add tests to `tests/test_debate_pure.py`.
2. **Create `config/anchor-templates/` with 6 template files** — one per skill type (challenge, review, explore, polish, healthcheck, think).
3. **Inject anchors into the system prompt construction** — modify the relevant prompt-building functions in debate.py.
4. **A/B test:** Run the same proposal with and without anchors. Compare finding quality against the baselines in this document.
5. **If anchors work:** Consider adding the "focus directive" (expected-outcomes framing) as a second iteration.

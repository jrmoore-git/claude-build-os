---
scope: explore mode redesign
created: 2026-04-10
status: draft
---

# Proposal: Adaptive Tree-Based Explore Mode

## Problem

The explore mode in `/debate` is hardcoded for product-market strategy. The divergence dimensions (customer, revenue, distribution, product form, wedge), the pre-flight questions, the synthesis framing, and even the context injection label ("Market Context") all assume the user is exploring a commercial product opportunity.

When someone asks an engineering operations question ("How do we improve CZ velocity?"), a research question ("What's the right approach to identity resolution?"), or an organizational question ("How should we structure the platform team?"), the explore engine either forces the question into product-market framing or produces irrelevant dimensions.

The explore engine should be the general-purpose divergent thinking tool for BuildOS — any problem where you want iterative single-model exploration followed by cross-model refinement.

## Current Flow

```
User input → classify into 3 buckets (Product / Solo Builder / Architecture)
  → load corresponding preflight file → ask canned questions from that file
  → compose answers into fixed context format
  → inject into product-anchored explore prompts with hardcoded dimensions
    (customer, revenue, distribution, product form, wedge)
  → 3 rounds of forced divergence on those dimensions
  → synthesis that clusters on "customer it targets" and "core bet"
```

**Failure modes:**
- Engineering ops questions get asked "who pays?" and "what's the adoption barrier?"
- Research questions get forced into "name the first customer, first dollar"
- Organizational questions get divergence on "revenue model" and "distribution channel"
- Any question that doesn't fit the 3 buckets gets shoehorned into the closest one

## Proposed Flow: Adaptive Tree

```
"What do you want to explore?" (open-ended, no menu)
  → User states their question/problem
  → Model reads the question and infers:
      1. The domain (product, engineering, organization, research, strategy, etc.)
      2. The relevant divergence dimensions for THIS question
      3. Which forcing questions would break the user's default framing
  → Adaptive questions (2-4, one at a time, push for specificity)
  → Compose context with DERIVED dimensions
  → Inject dimensions into GENERIC explore prompts
  → 3 rounds of forced divergence on the DERIVED dimensions
  → Synthesis that compares on axes relevant to THIS question
```

### Key Design Decisions

**1. Pre-flight becomes adaptive, not routed**

Instead of classifying into a bucket and loading a canned questionnaire, the model reads the user's question and generates appropriate forcing questions on the fly.

The existing pre-flight files (preflight-product.md, preflight-solo-builder.md, preflight-architecture.md) become **reference libraries** — examples of good forcing questions for different domains. The model can draw from them when the question matches, but isn't constrained to pick exactly one file.

A new `config/prompts/preflight-adaptive.md` provides the meta-prompt: how to read a question, infer the domain, select/generate forcing questions, and derive divergence dimensions.

**2. Divergence dimensions are derived, not hardcoded**

The current explore-diverge.md hardcodes 5 dimensions: customer, revenue, distribution, product form, wedge. These are great for product questions but meaningless for others.

The new approach: pre-flight produces a set of 4-6 divergence dimensions specific to the question. Examples:

- **Product question:** customer segment, revenue model, distribution, product form, wedge
- **Engineering ops question:** team structure, tooling approach, process model, automation level, feedback mechanism
- **Research question:** methodology, scope, data sources, theoretical framework, success criteria
- **Organizational question:** reporting structure, decision rights, communication model, hiring profile, success metric

These dimensions are injected into the diverge prompt as a variable, not baked into the prompt text.

**3. Explore prompts become dimension-agnostic**

The core explore, diverge, and synthesis prompts lose all product-specific language:

- "strategic thinker proposing a direction for a product" → "thinker proposing a direction for a problem"
- "Name the first customer, first use case, first dollar" → "Be specific. Name the first concrete action, who it affects, what changes."
- "the core bet it makes and the customer it targets" → "the core bet it makes and the key tradeoff"
- "no mainstream VC would fund" → "feels uncomfortable or contrarian"
- "Market Context" → "Context"
- ERRC grid stays (it's domain-agnostic — eliminate/reduce/raise/create works for anything)

**4. Synthesis adapts to the question domain**

Instead of clustering on "customer/revenue/distribution," the synthesis prompt receives the derived dimensions and clusters on those. The comparison table columns (Timeline, Risk, What you learn, Strategic sacrifice) are general enough to keep.

**5. The hardcoded fallbacks in debate.py update too**

Lines 2118-2219 contain the v0 hardcoded prompts. These need the same domain-agnostic treatment so the fallback path works for non-product questions.

### What Stays the Same

- The 3-round structure (first direction → forced divergence → synthesis) is sound
- The two-phase brainstorm-then-commit within each round is sound
- The ERRC grid in round 2+ is domain-agnostic and stays
- The synthesis comparison table (Timeline, Risk, What you learn, Strategic sacrifice) is general enough
- Temperature 1.0 for exploration rounds
- The `debate.py explore` CLI interface stays the same — the prompts change, not the orchestration
- Pre-flight files stay as reference material

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| Pre-flight routing | 3-bucket classification menu | Open question → adaptive inference |
| Pre-flight questions | Canned from one of 3 files | Generated/selected based on question domain |
| Divergence dimensions | Hardcoded: customer, revenue, distribution, product form, wedge | Derived from pre-flight, injected as variable |
| explore.md | Product-specific language | Domain-agnostic with {dimensions} slot |
| explore-diverge.md | Product dimensions hardcoded | {dimensions} injected from context |
| explore-synthesis.md | Clusters on customer/revenue | Clusters on derived dimensions |
| Context label | "Market Context" | "Context" |
| debate.py fallbacks | Product-anchored | Domain-agnostic |
| SKILL.md Step 3a | 3-option menu | Open question + adaptive tree |

### Files to Change

1. `config/prompts/explore.md` — remove product language, add {dimensions} slot
2. `config/prompts/explore-diverge.md` — replace hardcoded dimensions with {dimensions}
3. `config/prompts/explore-synthesis.md` — replace hardcoded clustering dimensions
4. `config/prompts/preflight-adaptive.md` — NEW: meta-prompt for adaptive pre-flight
5. `scripts/debate.py` lines 2118-2219 — domain-agnostic fallback prompts
6. `scripts/debate.py` line 3112 — "Market Context" → "Context"
7. `.claude/skills/debate/SKILL.md` Step 3 — adaptive tree replaces bucket menu

### Risks

1. **Adaptive pre-flight quality depends on the session model.** The model needs to be good at inferring domains and generating forcing questions. If the session model is weak, the pre-flight may produce poor dimensions. Mitigation: the reference files provide worked examples the model can pattern-match against.

2. **Dimension drift.** If the derived dimensions are too abstract or too specific, the divergence rounds may not produce meaningfully different directions. Mitigation: the preflight-adaptive meta-prompt includes examples of good vs bad dimensions.

3. **Backwards compatibility.** Users who liked the product-focused explore mode get a different experience. Mitigation: if the model infers "product" domain, it should naturally produce the same dimensions and questions as before — the product pre-flight file is still reference material.

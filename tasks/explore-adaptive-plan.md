---
scope: explore mode adaptive redesign
surfaces_affected: [debate skill, debate.py, config/prompts/explore*.md, config/prompts/preflight-adaptive.md]
verification_commands: ["python3.11 scripts/debate.py explore --help", "python3.11 scripts/debate.py explore --question 'test' --directions 3 --output /tmp/test-explore.md"]
rollback: git revert to pre-change commit; prompt files are versioned with frontmatter
review_tier: cross-model
verification_evidence: 8 experiment runs across 4+ domains with scored results
---

# Plan: Adaptive Explore Mode

## Goal

Make explore mode domain-agnostic. Currently hardcoded for product-market strategy; should work for engineering, organizational, research, and strategy questions with equal quality.

## Track 1: Prompt Rewrites (4 files)

### 1a. `config/prompts/explore.md` → v2
- Remove "product, strategy, or architectural decision" → "problem or decision"
- Remove "no mainstream VC would fund" → "feels uncomfortable or contrarian"
- Remove "Name the first customer, first use case, first dollar" → "Be specific. Name the first concrete action, who it affects, what changes."
- Add `{dimensions}` slot in Phase 2 for derived dimensions
- Keep ERRC grid (domain-agnostic)
- Keep two-phase brainstorm-then-commit structure

### 1b. `config/prompts/explore-diverge.md` → v3
- Replace hardcoded 5 dimensions (customer, revenue, distribution, product form, wedge) with `{dimensions}` variable
- Keep "at least 3 of these N dimensions must differ" structure
- Remove "who pays?" and "unlocks their wallet"
- Keep ERRC grid and 4 strategic questions (why now, workaround, 10x on which axis, adjacent analogy)
- Remove "first dollar" language

### 1c. `config/prompts/explore-synthesis.md` → v3
- Replace "the core bet it makes and the customer it targets" → "the core bet it makes and the key tradeoff"
- Replace hardcoded clustering dimensions with `{dimensions}` variable
- Keep comparison table (Timeline, Risk, What you learn, Strategic sacrifice) — already general
- Keep 3-bet fork-first format

### 1d. `config/prompts/preflight-adaptive.md` → NEW
- Meta-prompt for adaptive pre-flight
- Instructions: read the question, infer domain(s), derive 4-6 divergence dimensions, select 2-4 forcing questions
- Reference existing pre-flight files as examples (product, solo-builder, architecture)
- Output: structured JSON with domains, dimensions (name + description), context_summary
- Quality rules: dimensions must be concrete enough to force real divergence, abstract enough to allow multiple answers
- Few-shot examples for 4 domains: product, engineering, organizational, research

## Track 2: Code Changes (debate.py)

### 2a. Context label
- Line 3112: `"Market Context"` → `"Context"`

### 2b. Hardcoded fallback prompts (lines 2118-2219)
- `EXPLORE_SYSTEM_PROMPT`: remove "product or architectural decision" → "problem or decision", remove "first user", "first milestone" → domain-neutral
- `EXPLORE_DIVERGE_PROMPT`: remove "SaaS", "developers", "different buyer" → "structurally different approach"
- `EXPLORE_SYNTHESIS_PROMPT`: remove "the customer it targets" → "the key tradeoff"
- All fallbacks should be functionally aligned with the v2/v3 prompt files

### 2c. Dimension injection
- `cmd_explore`: when `--context` contains a `DIMENSIONS:` block, parse and inject into `{dimensions}` slots
- When no dimensions block present, use a generic set: "approach, scope, tradeoff, mechanism, success criteria"
- This preserves backwards compatibility: old-style string context still works

## Track 3: SKILL.md Update

### 3a. Step 3a replacement
- Remove 3-option menu (Product / Solo Builder / Architecture)
- Replace with: open-ended "What do you want to explore?" → model infers domain and derives dimensions adaptively
- Existing pre-flight files become reference material, not routes
- Show derived dimensions to user before proceeding, let them edit/override

## Track 4: Experiment Suite (8 runs)

Run each question through the NEW explore flow and score. Modeled on test 3 from `run_pipeline_quality.sh`.

### Experiment Questions (spanning 4+ domains)

| # | Domain | Question | Context |
|---|--------|----------|---------|
| 1 | Product (regression) | "Should we build analytics or integrate PostHog/Amplitude?" | "50k MAU, 3 engineers, $200/mo budget, B2B SaaS, data sovereignty matters" |
| 2 | Engineering ops | "How do we cut CI/CD pipeline time from 45 minutes to under 10?" | "Monorepo, 15 microservices, 50 deploys/week, 6 engineers, 3 prod incidents last quarter from deploy issues" |
| 3 | Organizational | "How should we structure a platform engineering team within a 40-person engineering org?" | "Currently 5 product teams, no platform team, shared infra is tribal knowledge, 3 senior engineers interested" |
| 4 | Research | "What's the right approach to evaluating LLM output quality for a production system?" | "Customer-facing summarization, 10k summaries/day, current approach is spot-checking 50/day manually" |
| 5 | Strategy | "Should we open-source our internal developer tools?" | "CLI + 3 libraries, 200 internal users, competitors have open-source alternatives, team of 4 maintains them" |
| 6 | Process | "How should we redesign our incident response process?" | "12 P1 incidents last quarter, MTTR 4 hours, 3 teams involved per incident, no unified runbooks" |
| 7 | Multi-domain | "Should we build or buy an identity resolution system?" | "Product, engineering, and data science all have opinions. 500k profiles, 15% duplicate rate, $50k/yr budget" |
| 8 | Personal/career | "How should a senior IC transition to engineering management?" | "8 years IC, strong technical reputation, team of 6 needs a manager, no management training yet" |

### Scoring Criteria (per experiment)

| Criterion | Points | How to measure |
|-----------|--------|----------------|
| 3 directions generated | 2 | grep `^## Direction` or `^## Bet` |
| Synthesis present | 2 | grep `Synthesis\|Fork\|Comparison` |
| Dimensions are domain-appropriate | 2 | Manual: no product language in non-product experiments |
| Directions genuinely diverse | 2 | Unique words in direction titles >= 8 |
| Actionable first moves | 1 | grep `first move\|next week\|start with` |
| No product-language leakage | 1 | For non-product: no "customer", "revenue", "first dollar" in forced dimensions |
| **Max per experiment** | **10** | |

**Pass threshold:** >= 7/10 per experiment, >= 56/80 total (70%)

### Experiment Execution

Run in 4 batches of 2 (parallel within batch, sequential across batches):
```bash
# Batch 1: experiments 1-2
# Batch 2: experiments 3-4
# Batch 3: experiments 5-6
# Batch 4: experiments 7-8
```

Score each output, compile results table, evaluate pass/fail.

## Execution Order

1. Track 1 (prompts) + Track 2 (code) — sequential but in one pass
2. Track 3 (SKILL.md) — after prompts land
3. Track 4 (experiments) — after all code changes
4. Evaluate results, iterate if needed
5. Update decisions.md with D## for the redesign

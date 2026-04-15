---
topic: context-packet-spec
created: 2026-04-15
type: specification
---
# Context Packet Specification for Cross-Model Evaluation

## Project Context

Build OS is a governance framework for building with Claude Code. It treats Claude as a governed subsystem inside a real engineering workflow. The framework has 22 skills (composable procedures in `.claude/skills/*/SKILL.md`), a cross-model debate engine (`scripts/debate.py`, 4,136 lines), 17 hooks for runtime enforcement, and rules in `.claude/rules/`. This is a solo developer project.

The debate engine powers 5+ skills by sending proposals, documents, and code to 3 different LLM models (Claude Opus, GPT-5.4, Gemini 3.1 Pro) for independent evaluation — adversarial challenge, code review, iterative refinement, divergent exploration, and pressure-testing.

## Recent Context

We ran an A/B test on proposal quality passed to cross-model challengers:

- **Run 1 (thin, 52 lines, no project context):** Claude made 29 tool calls in 100s, GPT made 14 in 50s, Gemini made 3 in 21s. Findings were less specific. Gemini barely engaged. Models diverged — one said "scrap tests, ship to product work," another said "revise to add debate.py tests."
- **Run 2 (enriched, 150 lines, full project context):** Claude made 22 tool calls in 89s, GPT made 9 in 66s, Gemini made 6 in 27s. All 3 converged on the same finding (debate.py test coverage underweighted). Gemini completely flipped its position. Findings were more specific (counted 13 subcommands in dispatch block, identified tier classification as highest-risk area).

We then audited all 22 skills. 10 call debate.py. Of those, 4 have rich context (challenge, review, think, investigate) and 6 have thin or no project context (pressure-test, polish, elevate, explore, healthcheck, simulate).

Web research across 6 questions validated our A/B findings with 4 independent research streams:

1. **Google/ICLR 2025 "Sufficient Context"**: Insufficient context increases hallucination from 10.2% to 66.1%. Models don't abstain — they reconstruct badly.
2. **Databricks long-context RAG** (2,000+ experiments): Performance improves monotonically up to model-specific saturation. At 3-6K tokens we're far below saturation.
3. **Evaluation prompt design** (arXiv 2506.13639): Criteria + reference answers are the two highest-impact components. Chain-of-thought adds zero benefit when criteria are clear. High/low anchors beat full rubrics.
4. **Cross-model agreement**: Shared sufficient context eliminates degrees of freedom causing divergence.

## Problem

We need a standard "context packet" structure that every skill uses when assembling input for debate.py calls. Currently each skill assembles context ad-hoc, some rich and some thin. The spec should define what sections to include, in what order, at what size, and how to assemble them.

## Proposed Context Packet Structure

Every document passed to debate.py as `--proposal`, `--input`, `--document`, or `--question` context should be self-contained. A model receiving only this document should understand: what the project is, what's being evaluated, and why it matters — without needing tool calls to reconstruct context.

### Required Sections (all debate.py calls)

#### 1. Project Context (30-50 lines)
What the project is, what problem it solves, key system components relevant to THIS evaluation. Not a full architecture doc — just what the evaluator needs.

Source: `docs/current-state.md` (phase, active work) + project description from `CLAUDE.md` or `docs/the-build-os.md`.

#### 2. Recent Context (20-30 lines)
The arc of recent work that led to this evaluation. Last 2-3 relevant sessions from `tasks/session-log.md`. Key decisions from `tasks/decisions.md`. Pivots taken.

Source: `tasks/session-log.md` (last 3 entries, summarized) + `tasks/decisions.md` (undecided/recent).

#### 3. The Artifact (variable)
The actual proposal, document, code diff, or question being evaluated. This is the core input — everything else is context for evaluating it.

#### 4. Evaluation-Specific Context (10-20 lines, optional)
Prior decisions that constrain this evaluation. Relevant lessons. Governance context.

Source: `scripts/enrich_context.py` output when available.

### Size Targets

| Skill type | Target total | Rationale |
|---|---|---|
| Challenge / pressure-test | 150-250 lines (4-8K tokens) | Deep evaluation needs full context |
| Review (code) | 100-200 lines (3-6K tokens) | Diff + spec + governance context |
| Explore | 80-150 lines (2-4K tokens) | Question + research + project framing |
| Polish / refine | 80-120 lines (2-4K tokens) | Document + project context for grounding |
| Healthcheck / simulate | 50-100 lines (1-3K tokens) | Narrow scope, minimal project context |

### What NOT to Include (Anti-Patterns from Research)

- Full conversation history (causes context rot — Chroma study)
- Redundant framing that restates the artifact (distractors reduce performance)
- Chain-of-thought instructions in evaluation prompts (no benefit when criteria are clear)
- Full 5-point rubric descriptions (high/low anchors only perform better)
- Raw file dumps without summarization (attention dilution)

### Assembly Pattern

Each skill that calls debate.py should assemble the context packet before the call:

```
1. Read project description (cached per session — doesn't change)
2. Read recent session-log entries (last 3, summarized to ~20 lines)
3. Read relevant decisions (if enrich_context.py available, use it)
4. Prepend sections 1-3 to the artifact
5. Pass assembled document to debate.py
```

For skills that write proposals to disk (challenge, pressure-test): the proposal template should include Project Context and Recent Context sections, so the document is self-contained on disk.

For skills that assemble temp files (review, elevate, healthcheck, simulate): prepend project context to the temp file before passing to debate.py.

For skills that pass inline context (explore): include project context in the `--context` flag.

### Enrichment Sources

| Source | What it provides | When to use |
|---|---|---|
| `docs/current-state.md` | Current phase, active work, blockers | Always — lightweight, 1-2 sentences |
| `tasks/session-log.md` | Recent work arc, decisions, pivots | Always — summarize last 3 entries |
| `scripts/enrich_context.py` | Relevant decisions + lessons | When available — 4 skills already use it |
| `tasks/decisions.md` | Undecided items, recent decisions | When proposal touches decided areas |
| `scripts/research.py` | Web research grounding | When proposal involves external tech/patterns |

### Implementation Priority

Skills ordered by impact (debate.py call frequency x context gap severity):

1. **pressure-test** — High frequency, no project context, no enrichment
2. **elevate** — Medium frequency, has design doc but no enrichment
3. **polish** — Medium frequency, treats input as generic document
4. **explore** — Medium frequency, has research but no project context
5. **healthcheck** — Low frequency, narrow scope but could benefit
6. **simulate** — Low frequency, narrow scope evaluation

---
topic: email-processing-pipeline
created: 2026-04-10
---
# Email Processing Pipeline Redesign

## Problem
The current email triage pipeline is a single monolithic script that fetches, classifies, drafts responses, and sends — all in one pass. When classification fails, the entire pipeline stops. When the LLM draft is poor, there's no human review gate. Processing 40 emails takes 12 minutes with no parallelism.

## Proposed Approach
Decompose into 4 independent stages with a shared queue:
1. **Fetch** — pull new emails, write to `inbox` queue
2. **Classify** — LLM classification (priority, category, requires_response)
3. **Draft** — LLM response drafting for requires_response=true emails
4. **Review** — human approval queue before send

Each stage reads from its input queue and writes to its output queue. Stages can run independently and retry individually. SQLite as the queue backend (no new infrastructure).

Non-goals: real-time processing, multi-account support, attachment handling improvements.

## Simplest Version
Keep the monolithic script but add a checkpoint after each stage. If classification fails, resume from the checkpoint instead of restarting. Add a `--draft-only` flag that stops before sending.

### Current System Failures
1. 2026-04-07: Classification API timeout killed the entire pipeline — 40 emails stuck unprocessed for 6 hours until manual re-run.
2. 2026-04-01: LLM drafted a response to a legal inquiry with fabricated case numbers. No review gate — it was sent automatically.
3. 2026-03-25: Pipeline took 18 minutes during a high-volume day (65 emails). Cron overlap caused duplicate processing.

### Operational Context
- Processes ~40 emails/day on average, peaks at 65
- Pipeline runs every 30 minutes via cron
- Classification uses Claude Haiku (fast, cheap)
- Draft generation uses Claude Sonnet (quality)
- Total pipeline cost: ~$0.12/day in API calls
- SQLite for all state (no external dependencies)

### Baseline Performance
- Current: single monolithic script, no parallelism, no review gate
- Current processing time: 12 minutes average, 18 minutes peak
- Current cost: $0.12/day API, $0 infrastructure
- Current error rate: ~1 pipeline failure/week (usually API timeout)

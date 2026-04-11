---
topic: metrics-dashboard
created: 2026-04-10
---
# Internal Metrics Dashboard

## Problem
Operational metrics are scattered across SQLite databases, JSONL logs, and ad-hoc queries. There's no single view of system health — checking costs, error rates, and pipeline status requires running 5+ different queries manually. When something breaks, diagnosis starts with "which database do I query?"

## Proposed Approach
Build a lightweight web dashboard (Flask + HTMX) that surfaces key metrics:
- **Cost panel**: daily/weekly API costs by model, with trend lines
- **Pipeline panel**: last run time, success/failure, items processed per pipeline
- **Error panel**: recent errors grouped by source, with frequency sparklines
- **Health panel**: system uptime, cron job status, disk usage

Data sources: audit.db (costs, pipeline runs), metrics.db (quality metrics), debate-log.jsonl (debate stats). Read-only — dashboard never writes to any source.

Non-goals: alerting (use existing cron + stderr), user-facing analytics, historical data beyond 30 days.

## Simplest Version
A single CLI command that prints a formatted text summary of today's metrics to stdout. No web server, no persistence, no styling.

### Current System Failures
1. 2026-04-05: Took 20 minutes to diagnose why morning briefing failed — had to check 3 databases and 2 log files manually.
2. 2026-03-30: Didn't notice API costs doubled for 3 days because no one was running the cost query.
3. 2026-04-08: Cron job silently failing for 2 days — no dashboard to show "last successful run."

### Operational Context
- audit.db: 18,500+ rows, ~5MB
- metrics.db: ~2,000 rows, <1MB
- debate-log.jsonl: ~200 entries, <500KB
- All data is local SQLite — no network dependencies
- Solo developer — dashboard is for personal use only

### Baseline Performance
- Current: manual SQL queries in terminal
- Current cost: $0 (no dashboard exists)
- Current time to check system health: 5-10 minutes of manual queries

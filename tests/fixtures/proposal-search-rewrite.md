---
topic: search-rewrite
created: 2026-04-10
---
# Search Infrastructure Rewrite

## Problem
Our search is built on PostgreSQL full-text search (tsvector). It worked at 10k documents but breaks down at 500k. Search queries now take 2-8 seconds. Users report irrelevant results. The ranking algorithm is a single `ts_rank` call with no tuning.

## Proposed Approach
Migrate to Elasticsearch. Deploy a 3-node cluster. Build a sync pipeline from PostgreSQL to ES using Change Data Capture (Debezium). Implement BM25 + custom boosting for relevance. Add search analytics to track query patterns and click-through rates.

Non-goals: semantic/vector search, cross-language search, search suggestions/autocomplete (phase 2).

## Simplest Version
Add GIN indexes to the existing tsvector columns, tune `ts_rank` weights, and add a materialized view for the most common search patterns. Estimated 3-5x improvement with 2 days of work.

### Current System Failures
1. **2026-03-20:** Customer #89 reported search for "invoice Q1" returned 0 results — the documents existed but tsvector didn't match partial terms.
2. **2026-04-01:** Search query for common term "report" timed out at 10s — full table scan on 500k documents.
3. **2026-04-05:** A/B test showed users click the first search result only 12% of the time (industry benchmark: 35-45%), indicating poor ranking.
4. **2026-04-07:** Support ticket backlog has 23 "can't find document" complaints in the last 30 days.

### Operational Context
- 500k searchable documents, growing ~5k/week
- ~8k search queries/day, P50 latency 1.2s, P95 latency 5.8s
- PostgreSQL on RDS (db.r6g.xlarge), search queries consume ~30% of DB CPU
- No existing search infrastructure beyond pg tsvector
- Elasticsearch cluster would cost ~$450/month (3x m5.large.search)

### Baseline Performance
- Current: PostgreSQL tsvector with default ts_rank
- Current cost: $0 incremental (search runs on existing RDS)
- Current error rate: 2.1% timeouts on search queries
- Click-through rate on first result: 12%
- Mean Reciprocal Rank: 0.31 (estimated from support tickets)

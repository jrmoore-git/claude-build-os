---
topic: api-caching-layer
created: 2026-04-10
---
# API Response Caching Layer

## Problem
Our API serves 50k requests/day. 40% are identical read queries hitting the database every time. P95 latency is 800ms. Users on the dashboard experience visible lag when switching between views that request the same data.

## Proposed Approach
Add a Redis-backed response cache between the API handler and the database layer.
- Cache key: hash of (endpoint, query params, user org ID)
- TTL: 5 minutes for list endpoints, 30 seconds for detail endpoints
- Invalidation: write-through on POST/PUT/DELETE to the same resource
- Cache-aside pattern: check cache first, fall through to DB on miss

Non-goals: CDN-level caching, client-side caching headers, query result deduplication.

## Simplest Version
In-process LRU dict (no Redis dependency) with 60-second TTL on the 3 highest-traffic endpoints. Measure hit rate for 1 week before committing to Redis.

### Current System Failures
1. 2026-04-01: Dashboard "Accounts" tab took 3.2s to load during peak hours — all 12 API calls were cache-miss DB queries returning identical data within a 10-second window.
2. 2026-03-28: Monitoring alert for DB connection pool exhaustion — 80% of connections were serving duplicate read queries.
3. 2026-04-05: User complaint ticket #4821 — "switching between tabs feels slow, data doesn't change that often."

### Operational Context
- API handles ~50k requests/day, 20k unique query shapes
- PostgreSQL DB on RDS (db.r6g.xlarge), connection pool max 100
- Current P50 latency: 120ms, P95: 800ms, P99: 2.1s
- No existing caching infrastructure
- Redis would add ~$45/month (cache.t3.micro)

### Baseline Performance
- Current: every read hits DB directly
- Current cost: $0 caching infra, but $380/month RDS (could downsize with caching)
- Current error rate: 0.3% (mostly connection pool timeouts under load)

---
topic: api-rate-limiter
created: 2026-04-10
---
# API Rate Limiter Redesign

## Problem
Our API has no rate limiting. A single misbehaving client caused a 20-minute outage on 2026-03-15 by sending 50k requests in 3 minutes. We've had 4 incidents in the last quarter where one tenant's traffic degraded service for all tenants.

## Proposed Approach
Replace the current "nothing" with a token-bucket rate limiter backed by Redis, with per-tenant and per-endpoint limits. Limits configurable via admin API. Real-time usage dashboard for customers.

Non-goals: DDoS protection (use Cloudflare), geographic rate differentiation, ML-based adaptive limits.

## Simplest Version
Nginx-level rate limiting using `limit_req_zone` with tenant ID extracted from API key. Fixed limits, no dashboard, no admin API. Takes 2 hours to deploy.

### Current System Failures
1. **2026-03-15:** 20-minute full outage — single client sent 50k requests in 3 minutes, exhausted API server workers.
2. **2026-03-22:** Degraded performance for 45 minutes — batch import job from tenant #47 consumed 80% of DB connections.
3. **2026-04-02:** Support ticket #5102 — customer reported 500 errors during another tenant's load test.
4. **2026-04-08:** Alert fired for sustained >90% CPU on API servers — traced to automated polling client hitting /search endpoint every 2 seconds.

### Operational Context
- API handles ~120k requests/day across 230 active tenants
- Top 10 tenants generate 60% of traffic
- Average request cost: 15ms CPU, 2 DB queries
- No existing rate limiting at any layer (Cloudflare in passthrough mode)
- Redis already deployed for sessions (cache.t3.medium, ~40% utilized)

### Baseline Performance
- Current: no rate limiting, no per-tenant isolation
- Current cost: $0 rate-limiting infra (Redis already exists)
- Current error rate: 0.8% (spikes to 5-12% during noisy-neighbor incidents)
- P95 latency: 180ms normal, 2-4s during incidents

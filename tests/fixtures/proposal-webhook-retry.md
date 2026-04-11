---
topic: webhook-retry-system
created: 2026-04-10
---
# Webhook Delivery Retry System

## Problem
Our webhook delivery has no retry logic. When a customer's endpoint is temporarily down, we silently drop the event. Customers discover missed webhooks hours later when their systems are out of sync.

## Proposed Approach
Build a persistent retry queue with exponential backoff:
- Store failed deliveries in a `webhook_retry_queue` table
- Background worker processes the queue every 30 seconds
- Retry schedule: 30s, 2m, 15m, 1h, 4h, 24h (6 attempts max)
- Dead letter queue after max retries — surface in admin dashboard
- Idempotency key in webhook payload so receivers can dedupe

Non-goals: webhook signature rotation, delivery ordering guarantees, customer-configurable retry policies.

## Simplest Version
Log failed deliveries to a file. Manual re-send script for ops team. No automatic retry.

### Current System Failures
1. 2026-04-03: Customer Acme Corp missed 47 order.created webhooks during their 2-hour maintenance window. Required manual CSV export to resync.
2. 2026-03-20: DNS propagation delay caused 15 minutes of webhook failures to customer Beta Inc. All 89 events lost permanently.
3. 2026-04-08: Customer reported "missing data" — traced to a single 504 timeout on their endpoint during a deploy.

### Operational Context
- ~8,000 webhook deliveries/day across 45 active endpoints
- Current failure rate: 2.1% (mostly transient — endpoint timeouts, DNS, TLS errors)
- Average payload size: 1.2KB JSON
- No retry infrastructure exists
- PostgreSQL for storage, Sidekiq for background jobs

### Baseline Performance
- Current: fire-and-forget HTTP POST, log failure to application log
- Current cost: $0 retry infra
- Current error rate: 2.1% permanent loss rate on webhook deliveries

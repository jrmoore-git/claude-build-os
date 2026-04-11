---
topic: auth-session-migration
created: 2026-04-10
---
# Session Token to JWT Migration

## Problem
Our session-based auth stores tokens in a PostgreSQL sessions table. At 10k concurrent users, the sessions table is the #1 source of DB write contention. Session lookups add 15-40ms to every authenticated request. Legal has flagged that session tokens stored server-side may not meet new data residency requirements for EU customers.

## Proposed Approach
Migrate from server-side sessions to stateless JWTs:
- RS256-signed JWTs with 15-minute access tokens + 7-day refresh tokens
- Refresh token rotation (one-time use, stored in DB for revocation)
- Claims: user_id, org_id, roles[], issued_at, expiry
- Gradual rollout: new sessions get JWTs, existing sessions honored until expiry
- Token revocation: maintain a deny-list (Redis set) for compromised tokens

Non-goals: OAuth2 provider functionality, SAML/SSO integration, multi-device session management.

## Simplest Version
Extend session TTL to reduce DB writes. Add a read replica for session lookups. Defer JWT migration until data residency deadline.

### Current System Failures
1. 2026-03-15: DB write contention spike — sessions table lock wait time exceeded 500ms during peak, causing 403 errors for 200+ users over 8 minutes.
2. 2026-04-02: EU customer audit flagged session token storage as non-compliant with GDPR data residency (tokens stored in us-east-1 only).
3. 2026-03-30: Session cleanup cron job took 45 minutes, causing elevated DB CPU during business hours.

### Operational Context
- 10k concurrent users during peak, 2.5k off-peak
- Sessions table: 850k rows, ~2GB with indexes
- Session cleanup runs daily at 3am PT, deletes expired rows
- Current auth latency overhead: 15-40ms per request (session lookup)
- Legal deadline for data residency: 2026-07-01

### Baseline Performance
- Current: PostgreSQL sessions table, cookie-based session ID
- Current cost: ~$50/month in DB IOPS attributable to sessions
- Current error rate: 0.8% auth failures during peak (lock contention)

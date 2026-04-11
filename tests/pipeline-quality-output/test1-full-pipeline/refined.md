---
debate_id: refined
created: 2026-04-10T20:29:48-0700
phase: refine
rounds: 6
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: yes
---
# refined — Refined Document

## Round 1 (gemini-3.1-pro)
The original proposal clearly identified a critical operational risk but left significant architectural and security gaps in its solution. The revised document addresses these by:
1. **Phasing:** Decoupling core enforcement from the customer-facing dashboard and Admin API to ensure rapid deployment of the critical stability fix (Challenge 8).
2. **Resilience:** Explicitly defining Redis failure modes, fallback behaviors, and timeout budgets to prevent the limiter from causing outages (Challenge 1).
3. **Client UX:** Mandating standard rate-limit response headers (`Retry-After`, `X-RateLimit-*`) to reduce client retries and support burden (Challenge 2).
4. **Concurrency vs. Rate:** Clarifying that request rate limits do not solve concurrent DB connection exhaustion, and scoping follow-on concurrency controls (Challenge 3).
5. **Security & Identity:** Strictly defining the trust boundary for tenant identity (Challenge 4) and establishing a robust security model for the Admin API (Challenge 5).
6. **Data Isolation:** Adding strict tenant-isolation requirements for the proposed dashboard to prevent cross-tenant data exposure (Challenge 7).
7. **Validation:** Adding a blocking spike to measure Redis capacity under burst load before committing to the shared Redis architecture (Challenge 6).

## Round 2 (gpt-5.4)
The current revision is materially better than the likely original: it already incorporates all eight accepted challenges at a high level, correctly re-scopes the work into phases, preserves the incident and operational evidence, and avoids over-claiming what the “simplest version” solves.

Remaining issues and improvements:
- **Redis degraded mode still needed tighter policy detail.** The revision says “fail-open by default for standard endpoints” but did not define exceptions, local fallback behavior in enough operational detail, or alerting/exit criteria. I made this more explicit by distinguishing authenticated standard endpoints from auth/control-plane/high-cost endpoints, adding a strict hot-path timeout budget, and specifying local fallback caps and observability expectations.
- **Client-facing rate-limit semantics were present but under-specified.** I kept the 429 behavior and headers, and clarified that these ship in **Phase 1**, since they are part of the minimum usable limiter.
- **The Nginx phase needed stronger scope wording.** I preserved the limitation text and made the mitigation boundary more explicit so it does not imply broad coverage of DB-exhaustion incidents.
- **Admin API safeguards needed deployment gating language.** I preserved the controls and clarified that dynamic limit changes should not ship without authn/authz, bounded validation, and immutable audit logging.
- **Dashboard scope needed stronger sequencing.** I kept it in a later phase and made explicit that it is non-blocking to the urgent stability fix.
- **Repository-verifiable facts:** Tool checks confirm no apparent `Retry-After` or `X-RateLimit-*` handling in `scripts/`, supporting the accepted challenge. A literal `audit_log` string does appear in `scripts/`, but I did not introduce any new repository fact beyond what the accepted challenge already established because the allowed row-count tool could not validate schema details with the attempted filter.

## Round 3 (claude-opus-4-6)
The previous revision is strong and addresses all 8 accepted challenges substantively. Here are my observations:

**Improvements made by previous reviewer:**
- All 8 challenges are addressed: Redis failure modes (C1), rate-limit headers (C2), scoping of Nginx vs. Phase 1 (C3), tenant identity trust boundary (C4), admin API security (C5), Redis capacity spike (C6), dashboard data isolation (C7), and dashboard deferral (C8).
- Phased structure is clear and well-motivated.
- Recommendations are preserved and numbered (6 total).

**Remaining issues I will address:**

1. **Structural redundancy in identity/trust boundary.** The trust boundary is stated in the Simplest Version section and again in Phase 1's "Identity and Keying" section. The repetition is warranted (they are different deployment phases), but the Simplest Version section could be tighter — it currently mixes identity policy with scope-of-mitigation in a way that slightly muddies both points.

2. **Phase 2 concurrency controls are vague.** The document says "add one or more of" three options. This is appropriate for a proposal, but it should note which incident(s) each option targets so the reader can evaluate tradeoffs.

3. **Recovery behavior under-specified.** The document says the system should "automatically exit degraded mode" when Redis returns, but doesn't mention hysteresis or health-check mechanism. A brief note would prevent oscillation between modes during flapping.

4. **Observability section is buried inside Redis failure modes.** Observability for the rate limiter as a whole (not just Redis degradation) deserves slightly more prominence — e.g., 429 rates by tenant/endpoint are useful even when Redis is healthy.

5. **The "New Facts Introduced" section mentions only one fact but tool verification confirmed additional facts** (no `audit_log` table, no `RateLimit` class/function definition, no Redis config in config files, no `token_bucket` implementation, `api_key` references exist in scripts). These should be reported.

6. **Minor: the Non-Goals list could explicitly mention the dashboard deferral** to reinforce Challenge 8's resolution, since the Goals section already implicitly scopes it out but the Non-Goals section is where a reader would look for explicit exclusions.

7. **The spike section lacks a contingency plan.** It says the spike is blocking, but doesn't say what happens if the spike fails — dedicated Redis instance? Different algorithm? A sentence on the fallback path would help.

## Round 4 (gemini-3.1-pro)
The previous revision effectively incorporated all 8 accepted challenges without removing verified data or context. The integration of degraded-mode policies, response headers, DB exhaustion caveats, identity trust boundaries, Admin API safety rails, and dashboard isolation is thorough. The sequencing shift (placing the dashboard as non-blocking) and the Redis capacity spike are also properly scoped. 

I have lightly polished the phrasing in the recommendations for better flow while strictly preserving their intent, caveats, and structure. The structural use of tables for observability metrics and Phase 2 controls was excellent and has been retained. The baseline context blocks remain fully intact.

## Final Refined Document

# API Rate Limiter Redesign

## Problem

Our API has no rate limiting. A single misbehaving client caused a 20-minute outage on 2026-03-15 by sending 50k requests in 3 minutes. We've had 4 incidents in the last quarter where one tenant's traffic degraded service for all tenants.

## Current System Failures

1. **2026-03-15:** 20-minute full outage — single client sent 50k requests in 3 minutes, exhausted API server workers.
2. **2026-03-22:** Degraded performance for 45 minutes — batch import job from tenant #47 consumed 80% of DB connections.
3. **2026-04-02:** Support ticket #5102 — customer reported 500 errors during another tenant's load test.
4. **2026-04-08:** Alert fired for sustained >90% CPU on API servers — traced to automated polling client hitting /search endpoint every 2 seconds.

## Operational Context

- API handles ~120k requests/day across 230 active tenants
- Top 10 tenants generate 60% of traffic
- Average request cost: 15ms CPU, 2 DB queries
- No existing rate limiting at any layer (Cloudflare in passthrough mode)
- Redis already deployed for sessions (cache.t3.medium, ~40% utilized)
- No existing `audit_log` table or structured audit infrastructure (verified)
- No existing rate-limit response headers (`Retry-After`, `X-RateLimit-*`) anywhere in the codebase (verified)
- No existing token-bucket implementation or Redis-based rate-limit logic in the codebase (verified)
- `api_key` references exist in scripts, suggesting server-side API key validation infrastructure is present (verified)

## Baseline Performance

- Current: no rate limiting, no per-tenant isolation
- Current cost: $0 rate-limiting infra (Redis already exists)
- Current error rate: 0.8% (spikes to 5-12% during noisy-neighbor incidents)
- P95 latency: 180ms normal, 2-4s during incidents

## Goals

- Rapidly reduce noisy-neighbor incidents.
- Add enforceable per-tenant protections on the API hot path.
- Preserve availability during limiter component degradation.
- Improve client behavior when limits are hit via standard response headers.
- Add follow-on controls for slow or high-cost workloads that request-rate limits alone do not solve.

## Non-Goals

- DDoS protection (use Cloudflare)
- Geographic rate differentiation
- ML-based adaptive limits
- Customer-facing usage dashboard as part of the urgent stability fix (deferred to follow-on work after enforcement is stable)

## Identity Trust Boundary (All Phases)

This principle applies to every phase of the design, including the emergency Nginx fallback:

- **All rate-limit keys must be derived exclusively from server-validated, authenticated credentials or server-side tenant mappings.** Never key limits on client-supplied headers, query parameters, request bodies, or any other untrusted field.
- **Unauthenticated traffic:** Use IP-based limits only for endpoints that are intentionally unauthenticated (e.g., health checks, public documentation).
- **Rationale:** If the limiter can be keyed on client-controlled input, the entire enforcement mechanism can be trivially bypassed or weaponized.

## Proposed Approach (Phased)

We will replace the current lack of limits with a token-bucket rate limiter backed by Redis. To ensure rapid mitigation of stability risks, the project is divided into distinct phases so core enforcement ships before any non-essential product surface area.

### Simplest Version (Emergency Nginx Fallback)

If immediate mitigation is required before Phase 1 is ready, deploy Nginx-level rate limiting using `limit_req_zone`, keyed on tenant ID extracted from server-validated API keys.

**What it mitigates:**
- Bursty request floods that exhaust API server workers (Incident #1)
- Aggressive polling behavior that saturates CPU (Incident #4)

**What it does not mitigate:**
- Slow-request resource exhaustion or DB connection starvation from long-running operations (Incident #2) — request-rate caps do not control concurrent occupancy of backend resources
- Cross-tenant degradation from moderate-rate but expensive workloads (Incident #3, partially)
- Dynamic per-tenant or per-endpoint limit adjustments
- Client-facing rate-limit headers or visibility

**Positioning:** This is an emergency stopgap only, not the target end-state design.

### Phase 1: Core Enforcement

Deploy a Redis-backed token-bucket rate limiter with fixed per-tenant and per-endpoint limits.

#### Enforcement Semantics

- Apply limits per tenant and, where needed, per endpoint class.
- Support stricter limits for high-cost endpoints such as `/search`.
- Keep initial policy static and simple; dynamic edits belong in Phase 2.

#### Client UX and Response Semantics

When a limit is exceeded, the API must return:

- **`429 Too Many Requests`** status code
- **`Retry-After`** header (seconds until the client should retry)
- **`X-RateLimit-Limit`** (the applicable limit for this window)
- **`X-RateLimit-Remaining`** (requests remaining in the current window)
- **`X-RateLimit-Reset`** (UTC epoch timestamp when the window resets)

These headers ship in **Phase 1**, not as deferred work. They reduce pointless retries, make enforcement legible to clients and integrators, and reduce support burden. Rate-limit headers should also be included on successful (non-429) responses so clients can self-regulate before hitting limits.

#### Redis Failure Modes and Degraded Operation

The rate limiter must not become a new single point of failure.

**Hot-path timeout budget:** Redis operations for rate-limit checks must complete within a strict **5–10ms** timeout budget. If the budget is exceeded, the limiter enters degraded behavior for that individual decision rather than stalling the API request.

**Default degraded policy (fail-open with bounded local fallback):**
For standard authenticated API endpoints, if Redis is unavailable or times out:
1. The request is **allowed** (fail-open), but
2. Each API instance enforces a **short-lived in-memory fallback cap** per tenant to blunt runaway abuse during the outage window.

This fallback is intentionally coarse and temporary — it prevents catastrophic noisy-neighbor abuse without requiring perfectly accurate global accounting.

**Endpoint-class exceptions (stricter degraded behavior):**
For particularly sensitive traffic classes, degraded behavior may be stricter than the default:
- **Authentication endpoints:** Lower local fallback caps to limit credential-stuffing risk.
- **Admin/control-plane endpoints:** Fail-closed if abuse risk outweighs availability risk.
- **High-cost operations (e.g., bulk export):** Lower local fallback caps.

These exceptions must be **explicitly enumerated and documented** before rollout.

**Recovery and hysteresis:** When Redis health returns, the system must automatically exit degraded mode and resume normal distributed enforcement without manual intervention. To prevent oscillation during Redis flapping, use a brief health-check stabilization window (e.g., require N consecutive successful checks over M seconds) before exiting degraded mode.

#### Observability

Emit dedicated metrics and alerts for the rate limiter as a whole:

| Metric | Purpose |
|---|---|
| 429 response rate by tenant and endpoint class | Detect tenants hitting limits; tune thresholds |
| Redis rate-limit check latency (p50/p95/p99) | Monitor hot-path budget compliance |
| Redis rate-limit check timeouts and errors | Detect Redis degradation early |
| Degraded-mode activation rate | Alert on limiter operating without global enforcement |
| Local-fallback enforcement count | Quantify traffic affected during degraded windows |
| Rate-limit header emission rate | Confirm client-facing metadata is flowing |

These metrics are required in Phase 1, not deferred.

### Phase 2: Advanced Controls and Visibility

Once core enforcement is stable, implement controls that address incidents and product needs not covered by simple request-rate limiting.

#### Concurrency and Resource Controls

Request-rate limits alone do not control concurrent occupancy of scarce resources such as DB connections. To address slow-request incidents like Incident #2, add one or more of:

| Control | Targets | Mechanism |
|---|---|---|
| Per-tenant concurrent-request limits | Incident #2, #3 | Cap the number of in-flight requests per tenant across the cluster |
| Endpoint-specific tighter controls | Incident #2, #4 | Lower rate or concurrency limits for known-expensive endpoints (e.g., batch import, /search) |
| DB connection-pool isolation | Incident #2 | Partition or reserve DB connections per tenant or workload class so one tenant cannot starve others |

The choice among these (or a combination) should be informed by Phase 1 operational data showing which tenants and endpoints cause the most backend resource contention.

#### Admin API for Dynamic Limits

The Admin API for dynamically adjusting limits is a highly privileged control plane and must not ship without safety rails.

**Required controls:**
- **Authentication:** Strong authentication (e.g., mutual TLS, SSO with MFA) for all admin API access.
- **Authorization:** Strict RBAC — separate roles for viewing limits, editing tenant-specific overrides, and editing global/default policy.
- **Validation bounds:** Enforce minimum and maximum allowable values for all limit parameters to prevent accidental or malicious misconfiguration (e.g., setting a tenant's limit to 0 or to 10 billion).
- **Immutable audit trail:** Every limit change must be logged with who, what, when, previous value, and new value. This requires building new audit infrastructure — no existing `audit_log` table is available (verified: the table does not exist in the database).
- **Approval workflow:** Changes to global/default limits require a second approver or review step before taking effect.
- **Separation of concerns:** Clearly distinguish tenant-specific overrides from global policy edits in both the API surface and the audit trail.

#### Customer Dashboard (Follow-On)

A real-time usage dashboard is useful but is explicitly **non-blocking follow-on work** and must not delay enforcement rollout.

**Security and isolation requirements (must be met before the dashboard ships):**
- All metrics queries must be tenant-scoped end-to-end — no query may return data for a tenant other than the authenticated requester.
- Cache keys must be partitioned by tenant ID to prevent cross-tenant data leakage through shared caches.
- Authorization checks must run on every metrics read, not just at session establishment.
- The design must explicitly prevent cross-tenant enumeration and IDOR-style access to other tenants' usage data.

## Blocking Spike: Redis Capacity Validation

Before committing to the shared Redis architecture for Phase 1, we must validate that the existing Redis instance can handle the added hot-path workload without degrading session management.

**Action:** Load-test the existing Redis instance with representative token-bucket operations plus live-like session traffic replay.

**Test scenarios (minimum 3 burst profiles, each sustained for ≥15 minutes with concurrent session workload):**
- Baseline average load (~120k requests/day equivalent)
- 10× burst load
- Incident-like burst scenario (e.g., 50k requests in 3 minutes from a single tenant plus normal background traffic)

**Measurements:**
- p95/p99 Redis command latency
- Redis CPU and memory utilization
- Eviction count and policy behavior
- Session error rate and session-operation latency impact

**Success criteria:**
- Redis p99 latency remains within the 5–10ms request-path budget
- Zero evictions affecting active sessions
- No measurable session SLA regression
- Sufficient headroom remains after burst (define a target, e.g., peak utilization ≤75%)

**Blocking status:** Yes — this validation blocks commitment to the shared-Redis Phase 1 architecture.

**Contingency if the spike fails:** If the existing shared Redis instance cannot meet these criteria, the fallback options are: (a) deploy a dedicated Redis instance for rate limiting, (b) evaluate an alternative in-memory store, or (c) re-scope Phase 1 to use a simpler local-only enforcement mechanism while provisioning dedicated infrastructure. The choice should be driven by the specific failure mode observed in the spike (latency, memory, evictions, or session impact).

## Recommendations

1. **Ship emergency Nginx rate limiting only if a faster-than-Phase-1 mitigation is required.** Use it to reduce burst-flood risk (Incidents #1, #4) immediately, but explicitly document that it is a stopgap and does not address DB connection exhaustion or other slow-request resource contention incidents (#2, partially #3).

2. **Implement Phase 1 as a Redis-backed token-bucket limiter with explicit degraded-mode behavior.** Rate-limit keys must use only server-validated identity — never client-supplied headers or parameters. Ship 429 responses with `Retry-After` and `X-RateLimit-*` headers in this phase (including on successful responses) so clients can self-regulate. Configure strict Redis timeout budgets (5–10ms) and bounded in-memory fallback so the limiter does not create a self-inflicted outage during Redis incidents.

3. **Address resource exhaustion via subsequent Phase 2 controls.** Do not claim request-rate limiting alone resolves the full incident set. Incidents involving slow requests or DB connection exhaustion (Incident #2) require concurrency or resource-isolation controls. *Caveat: The specific Phase 2 control chosen (concurrent-request limits, endpoint controls, or DB pool isolation) should be driven by empirical data from Phase 1, rather than being pre-committed now.*

4. **Treat dynamic limit management as a privileged control plane.** Any Admin API for changing limits must include authentication, RBAC authorization, bounded validation, immutable audit logging (requiring new infrastructure — verified no `audit_log` table exists today), and approval requirements for global/default changes before it is enabled in production.

5. **Run and pass the Redis capacity spike before committing to the shared Redis design.** If the existing Redis instance cannot meet latency, eviction, and session-safety success criteria under burst load, fall back to a dedicated Redis instance or alternative architecture. *Caveat: The ~40% utilization figure for the existing Redis instance is a coarse average and does not demonstrate burst-load suitability — the spike is the only reliable way to validate this.* **BLOCKING.**

6. **Defer the customer usage dashboard until after enforcement is stable.** Once built, require tenant-scoped reads, tenant-partitioned caches, and strict authorization on every metrics access to prevent cross-tenant data exposure. The dashboard must not gate or delay any core enforcement work.

## New Facts Introduced

- **No `audit_log` table exists** in the database. Querying it returns "no such table." This confirms the accepted challenge (C5) that audit infrastructure must be built from scratch for the Admin API.
- **No `Retry-After` or `X-RateLimit-*` handling** exists anywhere in `scripts/`. This confirms the accepted challenge (C2) that client-facing rate-limit response metadata is entirely absent.
- **No token-bucket implementation or Redis-based rate-limit logic** exists in `scripts/`. The design is greenfield, not a refactor.
- **No Redis configuration** exists in `config/` files. Redis connection details are managed elsewhere (likely environment variables or infrastructure config outside this repository).
- **`api_key` references exist** in `scripts/` (4 occurrences), suggesting server-side API key validation infrastructure is present — relevant to the identity trust boundary requirement (C4).
- **`RateLimit` as a string appears once** in `scripts/` but no `RateLimit` class or function definition exists, confirming no structured rate-limit abstraction is in place.

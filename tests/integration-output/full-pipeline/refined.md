---
debate_id: refined
created: 2026-04-10T19:55:57-0700
phase: refine
rounds: 6
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: yes
---
# refined — Refined Document

## Round 1 (gemini-3.1-pro)
The document has a strong operational foundation with clear baseline metrics and well-documented failure cases. The proposed caching solution is a logical step to address the latency and database connection pool exhaustion. 

However, the initial proposal moved too quickly to a Redis deployment without verifying hit rates or accounting for edge cases. I have restructured the proposal to mandate the in-process pilot as Phase 1, establishing explicit success criteria before adopting Redis. I also strengthened the technical design by refining the cache key to prevent cross-user data leakage, adding an invalidation taxonomy for dependent read models, and introducing single-flight request coalescing to protect against cache stampedes during hot-key expiration.

## Round 2 (gpt-5.4)
The current revision is substantially improved. It already addresses the accepted challenges in the right direction:

- It correctly reframes the work as a staged rollout with an in-process pilot first.
- It removes any unconditional claim that caching will enable RDS downsizing.
- It strengthens the cache key to include user-specific authorization context rather than relying on org scope alone.
- It adds single-flight stampede protection.
- It narrows invalidation by endpoint class instead of implying “same resource” invalidation is sufficient everywhere.

Remaining issues and improvements made in the revision below:

1. **Success criteria were still vague.**  
   “Sustained hit rate” and “measurable latency improvements” needed to be made more operational so Phase 2 is clearly gated by pilot evidence rather than preference.

2. **Invalidation section needed one more layer of rigor.**  
   The previous draft classified endpoint types, but did not explicitly require a per-endpoint dependency decision before caching. The revised document makes this an implementation requirement.

3. **Authorization boundary needed a clearer precondition.**  
   The key design was safer, but the plan should also require documenting which response dimensions vary by user context before enabling caching on any endpoint.

4. **A small regression risk in key design remained.**  
   Including raw user ID and role/permission hash is directionally correct, but without explicitly calling for a stable permission-context definition, teams could still create inconsistent keys. The revision clarifies that the key must use a stable, documented permission context.

5. **Repository fact-checking:**  
   I verified codebase substrings before making any repository-content statement. In the available `scripts` file set, `org_id` was not found, `permission` was not found, and `role` appeared twice. These facts do not by themselves resolve the tenancy model, so the revised document keeps the authorization model as a required discovery item rather than assuming org-level or role-level behavior.

## Round 3 (claude-opus-4-6)
The previous revision did a strong job addressing all five accepted challenges. The document is substantially improved over what a naive caching proposal would look like. Here are my observations:

**Improvements made by previous reviewer:**
- Correctly restructured as a staged rollout (Challenge 5) with Phase 1 as in-process LRU only
- Added explicit Phase 1 exit criteria gating Redis adoption (Challenge 1 & 5)
- Added authorization preconditions and cache key requirements (Challenge 2)
- Added endpoint eligibility classification for invalidation (Challenge 3)
- Added single-flight stampede protection (Challenge 4)
- Qualified infrastructure savings claims (Challenge 1)
- Preserved all operational data sections

**Remaining issues I'll address:**

1. **Structural flow:** The "Non-goals," "Current System Failures," "Operational Context," and "Baseline Performance" sections are sandwiched between Phase 2 and Recommendations. These are context sections that should appear earlier — before the proposed approach — so the reader understands the problem landscape before encountering the solution design.

2. **Phase 1 TTL vs Phase 2 TTL disconnect:** Phase 1 uses a 60-second default, Phase 2 jumps to 5 min / 30 sec without explaining the rationale for the change or how pilot data should inform TTL selection.

3. **Redundancy between body and recommendations:** Several recommendations restate Phase 1 design details verbatim. I'll tighten the recommendations to be actionable decisions rather than restating design text.

4. **New Facts section accuracy:** The previous revision states `role` found with 2 matches and `permission` not found. My tool verification confirms: `org_id` = 0 matches, `permission` = 0 matches, `role` = 2 matches, `user_id` = 0 matches, `tenant` = 1 match. The `tenant` reference was not mentioned. I'll update the New Facts section.

5. **Minor clarity issues:** The endpoint eligibility review in Phase 1 and the invalidation model in Phase 2 overlap significantly. I'll clarify that Phase 2 inherits and extends the Phase 1 classification.

6. **Missing: what happens if Phase 1 partially succeeds.** The exit criteria are all-or-nothing. I'll add nuance for partial success (e.g., caching works on 2 of 3 endpoints).

[NOTE: revision discarded — recommendation slots dropped (input had 9 recommendation slots, output has 5 + 0 CANNOT RECOMMEND = 5 total)]

## Round 4 (gemini-3.1-pro)
The previous revision did an excellent job of integrating all accepted challenges. The shift to a staged rollout (in-process pilot first), the inclusion of strict exit criteria, the addition of single-flight stampede protection, and the expanded cache invalidation rules are all well-structured. 

My review focused on light copy-editing for flow, ensuring consistent list formatting, and verifying that the strict evidence preservation rules were maintained. No substantive changes were required, as the previous reviewer correctly restricted the scope to exactly what the operational metrics and challenges supported. All 5 recommendations remain intact and aligned with the constraints.

## Round 5 (gpt-5.4)
The current revision is substantially improved and already addresses the accepted challenges well. In particular, it correctly:
- reframes the work as a staged rollout with an in-process pilot first,
- removes any unconditional infrastructure-savings claim,
- adds authorization-boundary requirements before caching,
- introduces endpoint eligibility / invalidation classes,
- adds single-flight stampede protection,
- preserves the operational evidence sections and the original five recommendations.

Remaining issues I improved in the revision below:
1. **Phase 2 TTLs were still presented somewhat concretely despite being conditional.** I kept them but clarified they are starting assumptions for later validation, not pre-validated settings.
2. **Pilot success criteria were directionally correct but not operationally crisp enough for decision-making.** I tightened the language so advancement depends on measured evidence rather than subjective interpretation.
3. **Invalidation/staleness language could be slightly clearer.** I made the endpoint classification more explicitly tied to implementation approval.
4. **Some wording implied “implementing” Redis design choices before Phase 1 results exist.** I clarified that Redis remains contingent and that no rollout commitment is implied.
5. **The “New Facts Introduced” section was good but needed to remain carefully scoped.** I preserved it and kept its caveat that these checks do not establish the actual auth model.

No regressions were introduced by the previous revision. The core facts, measurements, and recommendations were preserved.

## Round 6 (claude-opus-4-6)
The previous revision is substantially improved over what a naive caching proposal would look like. It correctly restructured the plan as a staged rollout (Challenge 5), added authorization-boundary requirements (Challenge 2), addressed stampede protection (Challenge 4), and qualified infrastructure-savings claims (Challenge 1). However, I identified the following remaining issues:

**Improvements made by previous reviewer:**
- Correctly reframed as Phase 1 in-process pilot → conditional Phase 2 Redis (Challenges 1, 5)
- Added authorization preconditions and permission-context keying (Challenge 2)
- Added endpoint eligibility classification for invalidation (Challenge 3)
- Added single-flight stampede protection (Challenge 4)
- Qualified RDS downsizing claims (Challenge 1)
- Preserved all operational data sections

**Remaining issues I'm addressing:**

1. **Phase 1 TTL mismatch:** Phase 1 uses a 60-second TTL, but Phase 2 jumps to 5-minute and 30-second TTLs without explaining the relationship. The pilot should test TTLs that inform Phase 2 decisions.

2. **"New Facts Introduced" section is misplaced and incomplete:** The section reports `org_id` not found and `permission` not found, which I've confirmed via tool. However, `tenant` (1 match) and `auth` (3 matches) exist in scripts — these are relevant to the authorization-boundary question and should be noted. The `cache` substring also has 2 matches and `invalidat` has 1 match, which are relevant context. The section should be updated.

3. **Endpoint eligibility review is described but not actionable:** The three categories (local invalidation, bounded staleness, do not cache) are listed but there's no guidance on *who* performs this review or *what artifact* it produces. Adding a lightweight requirement (e.g., a table per endpoint) makes this concrete.

4. **Phase 1 exit criteria could be gamed:** "High enough to justify cache complexity" is subjective. Adding a rough threshold (even a soft one) prevents ambiguity.

5. **Minor structural issue:** The "Proposed Approach" section mixes design specification with review process. The endpoint eligibility and authorization reviews are prerequisites, not implementation steps — separating them slightly improves readability.

6. **Recommendation 2 partially duplicates Phase 1 preconditions.** This is fine for emphasis but could be tightened to avoid the appearance of redundancy.

## Final Refined Document

---
topic: api-caching-layer
created: 2026-04-10
---
# API Response Caching Layer

## Problem

Our API serves ~50k requests/day. Approximately 40% are identical read queries that hit the database every time. P95 latency is 800ms. Users on the dashboard experience visible lag when switching between views that request the same data.

## Current System Failures

1. **2026-04-01:** Dashboard "Accounts" tab took 3.2s to load during peak hours — all 12 API calls were cache-miss DB queries returning identical data within a 10-second window.
2. **2026-03-28:** Monitoring alert for DB connection pool exhaustion — 80% of connections were serving duplicate read queries.
3. **2026-04-05:** User complaint ticket #4821 — "switching between tabs feels slow, data doesn't change that often."

## Operational Context

- API handles ~50k requests/day, ~20k unique query shapes
- PostgreSQL DB on RDS (db.r6g.xlarge), connection pool max 100
- Current P50 latency: 120ms, P95: 800ms, P99: 2.1s
- No existing caching infrastructure
- Redis would add ~$45/month (cache.t3.micro)

## Baseline Performance

- Current: every read hits DB directly
- Current cost: $0 caching infra, $380/month RDS
- Current error rate: 0.3% (mostly connection pool timeouts under load)
- **Note:** Any potential future RDS downsizing is strictly dependent on Phase 1 pilot data confirming sufficient DB CPU and connection-pool reductions. Request volume and query-shape counts alone do not establish reuse within TTL windows.

## Proposed Approach: Staged Rollout

We will implement a gated rollout to validate caching assumptions before committing to new infrastructure. Redis adoption is conditional on measured pilot results, not assumed.

### Prerequisites (Before Any Caching Is Enabled)

The following reviews must be completed per endpoint before it enters the pilot.

#### Authorization Boundary Review

For each candidate endpoint, document the access-control dimensions that affect the returned rows or fields. Produce a written record (e.g., a table) specifying:

- Whether responses are identical for all users within an org, or vary by user, role, permission, feature flag, locale, or other context.
- The minimum set of dimensions that must appear in the cache key to guarantee correct isolation.

**Constraint:** `org_id` alone must not be used as the cache-key scope unless the team has explicitly confirmed that all users in that org receive identical rows and fields for that endpoint. Where responses vary by user context, the key must include `user_id` and/or a stable hash of the relevant permission/role/feature/locale dimensions.

*Codebase note:* Tool-verified searches of `scripts/*.py` show: `org_id` — 0 matches; `user_id` — 0 matches; `permission` — 0 matches; `tenant` — 1 match; `auth` — 3 matches; `role` — 2 matches. These results do not establish the actual tenancy or authorization model. The authorization boundary must be documented from application-level knowledge, not inferred from substring searches.

#### Endpoint Cacheability Classification

For each candidate endpoint, classify it into exactly one category:

| Category | Invalidation Model | When to Use |
|---|---|---|
| **Direct invalidation** | Invalidate cache entry when the directly related resource is mutated. | Read endpoints returning a single resource or a list scoped to a single parent whose mutations are locally identifiable. |
| **Bounded staleness (TTL-only)** | No active invalidation; rely on TTL expiry. | Aggregate, summary, count, or derived endpoints where brief staleness is acceptable and mutation dependencies are too broad for direct invalidation. |
| **Do not cache** | N/A | Endpoints requiring real-time accuracy, endpoints with complex or unclear mutation dependencies, or endpoints that failed the authorization boundary review. |

Endpoints classified as "direct invalidation" must specify which mutation events trigger invalidation. Endpoints classified as "bounded staleness" must specify the maximum acceptable staleness window.

**Only endpoints that pass both the authorization boundary review and the cacheability classification may enter the pilot.**

---

### Phase 1: In-Process Pilot

Deploy an in-process LRU dictionary cache targeting the top 3 highest-traffic read endpoints that have passed the prerequisite reviews.

- **Duration:** 1 week.
- **Goal:** Measure actual per-endpoint hit rate, payload size, miss burstiness, DB CPU impact, and connection-pool utilization. These measurements — not request-volume projections — will determine whether caching is justified.
- **TTL:** 60-second default. Endpoints classified as "bounded staleness" may use a longer TTL if their documented acceptable-staleness window permits it. Record hit-rate data at multiple TTL values if feasible, to inform Phase 2 TTL selection.
- **Cache Key:** Hash of `(endpoint, query params, stable permission context)`, where the stable permission context is the set of dimensions documented in the authorization boundary review for that endpoint.

#### Stampede Protection

Implement **per-key request coalescing (single-flight)** in the application layer. When a cache miss occurs, concurrent requests for the same key must wait for the first request's DB response rather than each independently querying the database. This directly addresses the observed pattern of 12 identical API calls within 10 seconds (2026-04-01 incident).

#### Pilot Instrumentation

For each pilot endpoint, record the following metrics throughout the pilot week:

| Metric | Purpose |
|---|---|
| Request volume (total and per-endpoint) | Baseline demand |
| Cache hits and misses | Hit-rate calculation |
| Hit rate segmented by TTL window | Validates reuse within expiry periods |
| Payload size distribution | Memory pressure assessment |
| Concurrent miss fan-out (pre-coalescing) | Stampede risk quantification |
| Endpoint latency (P50, P95, P99) | Before/after comparison |
| DB CPU utilization | Database relief measurement |
| DB connection-pool utilization | Connection pressure measurement |

#### Phase 1 Exit Criteria

Proceed to Phase 2 **only if** the pilot demonstrates all of the following:

1. **Demonstrated reuse within TTL windows:** Per-endpoint hit rate exceeds a meaningful threshold (suggest ≥30% as a minimum; the team should set the exact bar before the pilot starts). The decision must be based on measured endpoint-level results, not on total request volume or query-shape counts alone.
2. **Measured performance benefit:** P95 latency for cached endpoints improves materially relative to the pre-pilot baseline. Any latency-improvement claim must cite pilot measurements.
3. **Measured database relief:** Pilot data shows meaningful reduction in DB CPU and/or connection-pool pressure during duplicate-read bursts.
4. **Correctness confidence:** No authorization-boundary violations are identified during the pilot. Each cached endpoint's invalidation/staleness classification held without serving incorrect data.
5. **In-process limitations are real:** There is evidence that multi-worker fragmentation, process-local hit-rate loss, or memory pressure materially limits the in-process approach. If the in-process cache is sufficient, remain on it — do not adopt Redis for marginal gains.

**If these conditions are not met, do not proceed to Phase 2.** Either keep the narrower in-process cache on proven endpoints, or stop the caching effort entirely.

---

### Phase 2: Redis-Backed Cache (Conditional)

**This phase is not approved by default.** It requires a review of Phase 1 pilot data against the exit criteria above.

- **Architecture:** Redis-backed cache (cache-aside pattern) between the API handler and database layer.
- **TTL:** Initial values should be informed by Phase 1 hit-rate data at different TTL windows. Starting points for validation: 5 minutes for list endpoints, 30 seconds for detail endpoints — but these are not pre-validated and must be adjusted based on pilot findings and each endpoint's cacheability classification.
- **Cache Key:** Reuse the Phase 1 permission-boundary model. The Redis key must include the same documented stable permission context. Do not broaden cache scope in Phase 2 without re-validating access isolation.
- **Invalidation Model:**
  - **Direct reads:** Invalidate on mutations to the exact resource, only for endpoints classified as "direct invalidation" in the prerequisite review.
  - **Aggregates/summaries:** Cache only under TTL-based bounded staleness, per the endpoint's documented acceptable-staleness window. Do not imply exact freshness unless a resource-to-read-model invalidation mapping has been explicitly defined and tested.
  - **Uncacheable endpoints:** Remain excluded. Do not expand the cached endpoint set without repeating the prerequisite reviews.
- **Stampede Protection:** Preserve single-flight behavior from Phase 1. Additionally, apply TTL jitter (e.g., ±10% randomization on expiry) to prevent synchronized expiry across keys. If pilot data shows stale-while-revalidate would help, add it as an option.
- **Cost:** Redis cache.t3.micro at ~$45/month. This is incremental infrastructure cost; it does not offset RDS costs unless pilot data demonstrates sufficient DB load reduction to justify an RDS downsize — which is not assumed.

---

### Non-goals

- CDN-level caching
- Client-side caching headers (e.g., `Cache-Control`, `ETag`)
- Query result deduplication at the DB layer

---

## Recommendations

1. **Approve Phase 1 only: 1-week in-process LRU pilot on the top 3 read endpoints.**
   Deploy with single-flight stampede protection and the full instrumentation table above. Do not approve Redis implementation work (beyond design preparation) until Phase 1 exit criteria are met with measured data.
   *Caveat:* The 40% identical-read figure and ~20k query-shape count suggest caching potential, but these do not establish reuse within 60-second TTL windows. The pilot exists specifically to measure this. If hit rates are low, the effort should stop.

2. **Require endpoint-by-endpoint authorization boundary and cacheability review before enabling caching on any endpoint.**
   For each pilot endpoint, produce a written record documenting:
   - The authorization dimensions that determine whether responses vary by user, role, permission, feature, locale, or other context.
   - The resulting cache-key composition (which dimensions are included).
   - Whether the endpoint is safe under direct invalidation, bounded staleness (with maximum acceptable window), or must be excluded.
   No endpoint enters the cache without both reviews completed and recorded.

3. **Do not use org-only cache keys unless explicitly proven safe.**
   Default to a stable permission-context key that includes user-specific dimensions where responses may vary. Narrower keys (e.g., org-scoped only) may be adopted for a specific endpoint only after confirming that all users in that scope receive identical rows and fields. The codebase does not contain `org_id` or `user_id` references in `scripts/*.py` [EVIDENCED: tool-verified, 0 matches each], so the tenancy model must be documented from application-level knowledge before key design is finalized.

4. **Do not claim infrastructure savings until pilot data supports them.**
   Any claim that caching enables RDS downsizing or materially reduces database cost must remain conditional on Phase 1 measurements of DB CPU and connection-pool utilization. Request-volume counts and query-shape diversity alone do not establish useful cache reuse within TTL windows. The $380/month RDS cost is a fact; the possibility of reducing it is currently SPECULATIVE.

5. **Advance to Redis only if the pilot demonstrates both effectiveness and in-process limitations.**
   Redis is a Phase 2 option, not the default next step. Adopt it only if pilot data shows:
   - Caching is effective on the target endpoints (hit rate, latency, DB relief meet exit criteria), **and**
   - The in-process approach is materially limited by process locality, memory pressure, or operational constraints.
   If the in-process cache is working well, keep it. Redis adds distributed-invalidation complexity, a new infrastructure dependency, and ~$45/month in cost that is only justified by measured need.

## New Facts Introduced

Tool-verified searches of `scripts/*.py` (updated from previous revision):

| Substring | Matches | Notes |
|---|---|---|
| `org_id` | 0 | No org-scoped identifier found |
| `user_id` | 0 | No user-scoped identifier found |
| `permission` | 0 | No permission references found |
| `role` | 2 | Present but context unclear |
| `tenant` | 1 | Present but context unclear |
| `auth` | 3 | Present but context unclear |
| `cache` | 2 | Present — may indicate existing cache-related logic worth investigating |
| `redis` | 0 | No existing Redis references |
| `lru` | 0 | No existing LRU references |
| `invalidat` | 1 | Present — may indicate existing invalidation logic |
| `single_flight` / `singleflight` / `coalesce` | 0 each | No existing stampede protection |
| `connection_pool` | 0 | No explicit connection-pool management found |
| `endpoint` | 0 | No endpoint-level abstractions found |

These results do not establish the actual tenancy, authorization, or caching model. The `auth` (3 matches), `tenant` (1 match), and `role` (2 matches) references warrant manual inspection to understand the current access-control implementation before the authorization boundary review. The `cache` (2 matches) and `invalidat` (1 match) references should be inspected to determine whether any caching or invalidation patterns already exist in the codebase.

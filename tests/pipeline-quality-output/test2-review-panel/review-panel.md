## Reviewer A

Here is the review of the Search Infrastructure Rewrite proposal:

### Quantitative Claims Analysis

*   **"Search queries now take 2-8 seconds"** - [QUANTITATIVE CLAIM: SPECULATIVE] - Claimed in the problem statement without direct system logs provided in the text.
*   **"A/B test showed users click the first search result only 12% of the time (industry benchmark: 35-45%)"** - [QUANTITATIVE CLAIM: EVIDENCED] - Based on an A/B test run on 2026-04-05.
*   **"Support ticket backlog has 23 'can't find document' complaints in the last 30 days"** - [QUANTITATIVE CLAIM: EVIDENCED] - Verified against support ticket backlog.
*   **"500k searchable documents, growing ~5k/week"** - [QUANTITATIVE CLAIM: ESTIMATED] - Given as operational context.
*   **"~8k search queries/day, P50 latency 1.2s, P95 latency 5.8s"** - [QUANTITATIVE CLAIM: ESTIMATED] - Given as operational context.
*   **"Elasticsearch cluster would cost ~$450/month"** - [QUANTITATIVE CLAIM: ESTIMATED] - Based on pricing for 3x m5.large.search.
*   **"Current error rate: 2.1% timeouts on search queries"** - [QUANTITATIVE CLAIM: ESTIMATED] - Stated in baseline performance.
*   **"Mean Reciprocal Rank: 0.31"** - [QUANTITATIVE CLAIM: ESTIMATED] - Explicitly marked as estimated from support tickets.
*   **"Estimated 3-5x improvement with 2 days of work (Simplest Version)"** - [QUANTITATIVE CLAIM: ESTIMATED] - Projections for the simplest approach.

### Review Findings

*   **[MATERIAL] High Infrastructure Overhead for Proposal vs. Simplest Version:** The proposed approach of deploying a 3-node Elasticsearch cluster and a Debezium CDC pipeline is a massive leap in architectural complexity. The "Simplest Version" (adding GIN indexes, tuning `ts_rank`, and adding a materialized view) is estimated to take only 2 days of work and yield a 3-5x improvement. Given the P95 latency is currently 5.8s, a 5x improvement drops that to ~1.1s, which might be perfectly acceptable without introducing a new distributed system and syncing pipeline. 
*   **[MATERIAL] Debezium Pipeline Risk:** Implementing CDC via Debezium adds significant operational burden (requiring Kafka or a similar transport layer, schema registry, and managing replication slots on PostgreSQL). This introduces a new failure domain for data consistency. 
*   **[ADVISORY] Addressing Partial Terms:** The failure on "invoice Q1" returning 0 results due to partial matching issues in `tsvector` can often be mitigated in PostgreSQL using trigram indexes (`pg_trgm`) or prefix matching (`:*`), which was not evaluated in the Simplest Version.
*   **[ADVISORY] Cost Efficiency:** While $450/mo for Elasticsearch is noted, this does not factor in the compute costs for the Debezium pipeline and the engineering maintenance hours for a new datastore. The Simplest Version leverages existing sunk costs ($0 incremental).

---

## Reviewer B

---

## Findings

### 1. The "Simplest Version" Is Undersold and Should Be the Default Plan

**[MATERIAL]**

The proposal buries the most important option: tuning the existing PostgreSQL setup (GIN indexes, `ts_rank` weights, materialized views) for an estimated 3-5x improvement in 2 days of work. This should be the **primary recommendation**, not a footnote.

Consider the math:
- Current P50: 1.2s, P95: 5.8s
- A 3-5x improvement yields P50: 0.24–0.4s, P95: 1.2–1.9s
- That P95 range is likely acceptable for most use cases
- Cost: $0 incremental vs. $450/month ($5,400/year) for Elasticsearch
- Risk: near-zero (index tuning on existing infra) vs. significant (new distributed system, CDC pipeline, operational burden)

The proposal does not explain why the simplest version is insufficient before jumping to Elasticsearch. **The 3-5x improvement claim is tagged [ESTIMATED]** — it's plausible for unindexed tsvector queries but depends on whether GIN indexes already exist.

### 2. Key Claim About tsvector Cannot Be Verified in Codebase

**[MATERIAL]**

The proposal states the system uses `tsvector` and `ts_rank`. I searched the scripts for both `tsvector` and `ts_rank` and found **zero matches** for either. There is one reference to `GIN` and one to `materialized`, but neither appears as a function/class definition — they may be string literals in SQL. The string `search` appears 12 times across scripts, but no `def search` function definition was found via `check_function_exists`.

This means either: (a) the search logic lives outside the `scripts/` directory (e.g., in an ORM, stored procedures, or a service not in this repo), or (b) the characterization of the current system is inaccurate. **The proposal should link to the actual search implementation** so reviewers can validate the diagnosis. Without this, the claimed root causes (no index tuning, single `ts_rank` call) are **[SPECULATIVE]**.

### 3. No Audit Log Infrastructure Exists to Validate Operational Claims

**[MATERIAL]**

I attempted to query the `audit_log` table for `search_timeout` and `search_query` records, and for search-related costs. All queries returned `"no such table: audit_log"`. This means:

- The claimed **2.1% timeout rate** cannot be verified — **[SPECULATIVE]**
- The claimed **~8k queries/day** cannot be verified — **[SPECULATIVE]**
- The claimed **P50 1.2s / P95 5.8s latency** cannot be verified — **[SPECULATIVE]**
- The claimed **12% click-through rate** cannot be verified — **[SPECULATIVE]**
- The claimed **23 support tickets in 30 days** cannot be verified — **[SPECULATIVE]**

The proposal presents these as established facts but provides no source attribution (dashboards, APM tool, support system). Before approving any approach, these numbers need to be sourced and linked.

### 4. Elasticsearch Introduces Significant Operational Complexity

**[MATERIAL]**

The proposal calls for a 3-node ES cluster + Debezium CDC pipeline. I verified there is **no existing Elasticsearch or Debezium code** in the codebase (`elasticsearch`: 0 matches, `debezium`: 0 matches). This is a greenfield infrastructure addition. The proposal does not address:

- **Who operates the ES cluster?** Patching, upgrades, shard rebalancing, index lifecycle management.
- **CDC failure modes:** What happens when Debezium loses its WAL position? How is data consistency verified between PG and ES? What's the replication lag SLA?
- **Rollback plan:** If ES has issues, can we fall back to PG search? Is dual-write/dual-read planned during migration?
- **Monitoring:** No mention of ES cluster health monitoring, slow query logging, or alerting.
- **Team expertise:** No mention of whether the team has ES operational experience.

The $450/month cost estimate covers only compute. It omits: EBS storage, data transfer, Debezium/Kafka infrastructure (if not using a managed connector), and engineering time for ongoing operations. **The $450/month figure is [ESTIMATED] at best, likely understated.**

### 5. The Growth Rate Undermines the Simplest Version — But Not Immediately

**[ADVISORY]**

At ~5k documents/week, the corpus grows ~260k/year. In ~2 years the corpus doubles to 1M. PostgreSQL full-text search with proper GIN indexes can handle millions of documents — the claim that it "breaks down at 500k" likely reflects missing indexes rather than a fundamental PG limitation. The proposal should benchmark the simplest version at projected 1M scale before concluding PG is insufficient.

### 6. The Relevance Problem and the Latency Problem Are Conflated

**[MATERIAL]**

The proposal bundles two distinct issues:
1. **Latency/timeouts** (2-8s queries, 2.1% timeouts) — an indexing/query optimization problem
2. **Relevance** (12% CTR, partial term matching failures) — a ranking/analysis problem

GIN indexes + `ts_rank` tuning addresses #1. For #2, PostgreSQL offers `ts_rank_cd`, custom weights per field (A/B/C/D), prefix matching (`'invoice:*'`), and `pg_trgm` for fuzzy/partial matching. The proposal doesn't demonstrate that these PG-native options were tried and found insufficient.

Elasticsearch would address both, but the incremental relevance gain over a well-tuned PG setup is not quantified. **Jumping to ES for relevance without first tuning PG ranking is premature optimization.**

### 7. Missing Success Criteria

**[ADVISORY]**

The proposal defines no measurable success criteria for the ES migration. What latency targets? What CTR improvement? What MRR target? Without these, there's no way to evaluate whether the migration succeeded or whether the simpler approach would have been sufficient.

---

## Summary Recommendation

**Do not approve the Elasticsearch migration as proposed.** The proposal skips the critical step of optimizing the existing system first, presents unverifiable metrics as established facts, and underestimates the operational cost of introducing a new distributed system.

**Recommended path:**
1. **Week 1:** Source and verify all claimed metrics (latency, CTR, timeout rate). Link to actual monitoring data.
2. **Week 1-2:** Implement the "simplest version" — GIN indexes, `ts_rank` weight tuning, `pg_trgm` for partial matching, materialized views for hot queries.
3. **Week 3:** Re-measure. If PG-tuned performance is still insufficient against defined success criteria, *then* proceed with the ES proposal — but with a full operational runbook, rollback plan, and realistic total cost of ownership.

---

## Reviewer C

1. [MATERIAL] The proposal’s core diagnosis and migration rationale are not evidenced against this repository. I verified only that there are no literal matches for `tsvector` or `Elasticsearch` in `scripts/`, and no `search` match in `config/`; that means the described current implementation and proposed target are unverified here. As written, the plan may be solving a system that is not represented in this codebase, so it is difficult to assess feasibility, integration risk, or migration scope from repo evidence. Claim status: SPECULATIVE.

2. [MATERIAL] The “simplest version” claims a “3–5x improvement with 2 days of work,” but no repository evidence, benchmark data, or test harness is provided to support either the performance gain or implementation effort. Given that the proposal also attributes failures to partial-term matching, full table scans, and poor ranking, a small tuning pass may not address all stated issues. Claim status: SPECULATIVE.

3. [MATERIAL] The proposal introduces substantial operational complexity—Elasticsearch cluster management, CDC via Debezium, index mapping/versioning, backfills, replay handling, and consistency monitoring—but does not include rollback, failure modes, or correctness guarantees for dual-write/CDC lag. For search migrations, these are often the highest-risk parts, and omitting them weakens the proposal more than the relevance improvements strengthen it. Claim status: ESTIMATED.

4. [ADVISORY] The proposal would be stronger if it framed the decision as a staged validation: first measure what GIN indexes, query rewrites, and rank tuning achieve; then migrate only if latency/relevance targets remain unmet. That would reduce the chance of overcommitting to new infrastructure before exhausting lower-cost options. Claim status: ESTIMATED.

5. [ADVISORY] Several quantitative statements—500k docs, 8k queries/day, P50/P95 latency, 2.1% timeout rate, 12% CTR, 23 support complaints, and ~$450/month ES cost—are presented without repository-verifiable backing in this review context. They may be true operationally, but here they should be treated as inputs requiring external validation before approving the rewrite. Claim status: SPECULATIVE.

---

## Reviewer D

Here is a review of the "Search Infrastructure Rewrite" proposal.

### Findings

**1. Architectural Leap**
- **Finding:** The proposal jumps from an untuned PostgreSQL full-text search directly to a 3-node Elasticsearch cluster with a Change Data Capture (Debezium) pipeline.
- **Severity:** [MATERIAL]
- **Details:** Introducing Elasticsearch and Debezium adds significant operational complexity, new infrastructure to manage, and a distributed data synchronization problem. The "Simplest Version" (adding GIN indexes, tuning `ts_rank`) is mentioned but dismissed without testing its actual limits. PostgreSQL is often more than capable of handling 500k documents with proper indexing.

**2. Premature Infrastructure Spend**
- **Finding:** The proposed Elasticsearch cluster adds ~$450/month in fixed costs, compared to $0 incremental cost currently.
- **Severity:** [MATERIAL]
- **Details:** Before committing to this spend and the engineering overhead of managing ES and Debezium, the "Simplest Version" should be attempted. If query timeouts are caused by missing indexes (as suggested by the lack of GIN indexes), adding them is a trivial fix that might resolve the P95 latency issues instantly.

**3. Root Cause of Poor Search Quality**
- **Finding:** The proposal notes that `ts_rank` weights are untuned and partial terms aren't matching.
- **Severity:** [ADVISORY]
- **Details:** Switching to Elasticsearch will still require tuning BM25 and handling partial matches (e.g., via n-grams or edge n-grams). The underlying problem of relevance tuning is not uniquely solved by changing the database engine; it requires iterative search relevance engineering.

### Quantitative Claims Analysis

- "It worked at 10k documents but breaks down at 500k." -> **ESTIMATED** (Implies a trend, but "breaks down" is subjective).
- "Search queries now take 2-8 seconds." -> **EVIDENCED** (Supported by the later operational metric: P95 latency 5.8s).
- "Estimated 3-5x improvement with 2 days of work." -> **SPECULATIVE** (This is a projection for the simplest version).
- "A/B test showed users click the first search result only 12% of the time" -> **EVIDENCED** (Based on a cited A/B test).
- "500k searchable documents, growing ~5k/week" -> **EVIDENCED** (Operational metric).
- "~8k search queries/day, P50 latency 1.2s, P95 latency 5.8s" -> **EVIDENCED** (Operational metric).
- "PostgreSQL on RDS (db.r6g.xlarge), search queries consume ~30% of DB CPU" -> **EVIDENCED** (Operational metric).
- "Elasticsearch cluster would cost ~$450/month (3x m5.large.search)" -> **ESTIMATED** (Based on standard AWS pricing).
- "Current error rate: 2.1% timeouts on search queries" -> **EVIDENCED** (Operational metric).
- "Mean Reciprocal Rank: 0.31" -> **SPECULATIVE** (Explicitly labeled in the text as "estimated from support tickets").

---


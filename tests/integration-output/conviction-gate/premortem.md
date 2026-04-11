---
mode: pre-mortem
created: 2026-04-10T19:51:18-0700
model: gpt-5.4
prompt_version: 1
---
# Pre-Mortem

1. **AI auto-approval merged a “low-risk” PR that broke production auth, and the team disabled the whole review triage system after one incident.**  
   - **Type:** Execution failure  
   - **Warning sign visible today:** The plan proposes auto-approving “formatting, docs, test additions,” but there is no definition of enforcement boundaries, no mention of CODEOWNERS/branch protections, and no rollback/escalation policy. Also, “AI-powered” is doing policy work without a stated precision target.  
   - **What would have prevented it:** Start with triage-only, not auto-approval. Require deterministic rules for auto-merge eligibility: file-path allowlist, no production code touched, green CI, small diff size, and sampled human audit of 20% of approved PRs for 4 weeks.  
   - **Would prevention have changed the plan?** Yes, materially. The plan should have been phased; if leadership insists on auto-approval in quarter one, the project should not start in that form.

2. **Test suite “parallelization” cut runtime only from 45 to 28 minutes because the suite is dominated by shared-state integration tests and serial setup, while flakiness increased.**  
   - **Type:** Execution failure  
   - **Warning sign visible today:** The proposal jumps to “8 parallel shards using pytest-xdist” but provides no test composition data: percentage unit vs integration, longest 20 tests, fixture startup costs, database isolation strategy, or current flake rate by test class. “Why now” is literally TBD pending infra cost, which suggests the bottleneck hasn’t been profiled.  
   - **What would have prevented it:** Run a 1-week profiling effort first: collect per-test timing, fixture/setup cost, and flake frequency; then parallelize only the isolated subset and first fix shared DB/filesystem/global-state tests. Set a success gate: if >40% of runtime is non-parallelizable setup/integration work, do not pursue xdist as the main lever.  
   - **Would prevention have changed the plan?** Possibly. It might have changed this work from “split into 8 shards” to “stabilize and isolate tests first,” delaying or replacing the current plan.

3. **One-click deploys turned a 12-step manual process into a fragile GitHub Actions pipeline that repeatedly failed on secrets, environment drift, and missing rollback logic, increasing incident duration.**  
   - **Type:** Execution failure  
   - **Warning sign visible today:** The problem statement identifies missed manual steps, but the recommendation is just “single workflow triggered by merge to main” with no mention of staged rollout, approvals for prod, idempotency, preflight checks, or rollback. Last 3 incidents were deployment-related, which means the process is already high-risk; replacing it wholesale without decomposition is dangerous.  
   - **What would have prevented it:** First codify the runbook as executable steps in a non-prod pipeline, then add pre-deploy validation, artifact immutability, environment diff checks, and one-click rollback. Launch with canary/staging gates and manual prod approval before full merge-to-main automation.  
   - **Would prevention have changed the plan?** Yes. The plan should have been “safe deploy automation” rather than “merge to main deploys prod.” Same goal, different rollout.

4. **Renovate generated a flood of dependency PRs, overwhelmed reviewers, destabilized CI, and erased any review-capacity gains from the other initiatives.**  
   - **Type:** Execution failure  
   - **Warning sign visible today:** The recommendation has no owner, no batching policy, no package grouping, no schedule, and no merge criteria beyond “auto-merge for patch versions.” The “Why now” field is not actually a rationale; it references monitoring build times after enabling, meaning activation is proposed before governance exists.  
   - **What would have prevented it:** Assign an owner, restrict scope to dev dependencies first, batch updates weekly, group by ecosystem, cap open PRs, and require a dependency dashboard review before enabling auto-merge.  
   - **Would prevention have changed the plan?** Yes, but not fatally. This should be a controlled pilot, not an always-on background stream from day one.

5. **Velocity never improved because the team optimized visible bottlenecks while the real constraint was unstable requirements and too much in-flight work.**  
   - **Type:** Strategy failure  
   - **Warning sign visible today:** The plan assumes review, CI, and deploy friction explain the velocity plateau, but provides no throughput breakdown: average cycle time by stage, WIP per engineer, rework rate, blocked-story percentage, carryover between sprints, or product churn. Team growth without velocity gains often signals coordination/product-definition limits, not tooling.  
   - **What would have prevented it:** Before committing, do a 2-sprint value-stream analysis: measure wait time in review, test, deploy, and requirement churn. If review/test/deploy consume 30% of time but rework and scope changes consume comparable or greater time, do not frame this as a tooling-first optimization project.  
   - **Would prevention have changed the plan?** Potentially yes — it could mean not starting this project as the primary bet at all.

## The Structural Pattern
These failures share one assumption: that obvious local frictions are the system constraint, and that automation will reliably convert saved minutes into higher sprint velocity. The plan repeatedly skips baseline measurement, rollout guardrails, and ownership details, replacing diagnosis with implementation. That makes this partly an execution problem, but deeper down it is a sequencing problem: the team is trying to automate before instrumenting, and trying to scale throughput before proving where the bottleneck actually is. This pattern should change the plan: add measurement first, phase risky automation behind hard eligibility rules, and delay any “auto-approve/auto-merge/deploy-on-merge” steps until audited pilots succeed.

## The One Test
Run a **2-week instrumented flow study on every PR and story** before building anything. Specifically: tag 50 recent and 50 live work items; measure time in coding, waiting for review, review iterations, CI runtime, flaky reruns, deploy prep, deployment, and post-merge rework; classify incidents and delays by cause. In parallel, do one constrained pilot: deterministic auto-merge only for docs/format-only PRs in a single repo with 100% human audit afterward. This one test would show whether review/CI/deploy are truly the dominant constraints and whether low-risk automation is safe enough to scale.
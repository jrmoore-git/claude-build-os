---
mode: explore
created: 2026-04-11T00:04:22-0700
model: gpt-5.4
directions: 3
prompt_versions: explore=3, diverge=4, synthesis=4
---
# Explore: Should we build or buy an identity resolution system?

## Direction 1

## Brainstorm
1. Buy a lightweight dedup vendor focused on CRM hygiene and accept that analytics-grade identity resolution is a separate later problem.  
2. Build a simple in-house rules engine around email, phone, company, and domain similarity, embedded in the CRM sync pipeline.  
3. Create a presentation-layer “Jane Smith collapse” in CRM views now, without changing underlying records, and defer true entity resolution.  
4. Stand up a central identity graph service with probabilistic ML matching and make every system resolve through it.  
5. Outsource the whole problem to a RevOps/data services firm that owns matching operations with human review.  
6. Stop trying to create one master truth; run two systems on purpose: real-time deterministic dedup for sales, probabilistic offline resolution for analytics.  
7. Don’t solve duplicates globally at all; only dedup the top 5% of accounts and active pipeline contacts where customer-facing embarrassment actually happens.  
8. Treat duplicates as a workflow problem, not a data problem: require merge decisions at record creation when confidence is low.  
9. Use an LLM-assisted human-in-the-loop merge queue to turn weekly cleanup into continuous operations without building matching infrastructure.  
10. Reframe the question entirely: the real issue is CRM trust in live selling moments, so solve “visible contradiction” rather than “identity resolution.”

## Direction: Split the problem in two: CRM masking now, analytics resolution separately

## The Argument
Do not build or buy a single identity resolution system right now. That is the wrong shape of solution for your actual conflict. You have two jobs with different tolerances, different latency needs, and different economics:

- **Sales needs immediate suppression of visible duplicates in CRM views**
- **Data science needs higher-fidelity entity matching for offline analytics**
- **Engineering does not want another foundational platform to maintain**

A single system forces one compromise model onto all three. That is why this debate is stuck.

The right move is a **hybrid split architecture**:

- **For CRM:** implement a **presentation-layer duplicate collapse** with deterministic rules and confidence thresholds. If three Jane Smith records likely refer to one person, sales sees one “primary” profile with a banner: “2 possible duplicates hidden.” No underlying destructive merge required.
- **For analytics:** continue a separate offline entity-resolution process, upgraded incrementally with probabilistic matching as needed, because batch analytics can tolerate ambiguity and delayed resolution.

This is the most interesting direction because it rejects the false premise that identity resolution is one product decision.

### Why now?
Two things changed that make this possible now and more urgent than 2 years ago:

1. **Modern CRMs and customer-facing tools now support view-layer customization and overlays much more easily** than they used to. You no longer need a full master data platform just to hide duplicate embarrassment in front of sales.
2. **The cost of over-solving has become clearer.** Two years ago, teams could justify building central identity systems as strategic infrastructure. Today, with a $50k/year budget and stronger pressure to show fast user-facing value, the economics favor targeted fixes over platform ambitions.

Also, customer expectations in live sales interactions are higher. The tolerance for “our data is messy” has dropped. The sales question is not asking for canonical identity science; it’s asking why the UI contradicts itself in front of customers.

### What’s the workaround?
You already have the workaround: weekly manual dedup scripts catching 60%. Sales reps probably also mentally ignore duplicates, search multiple times, or pick the “most complete” Jane Smith by instinct. Data teams likely export records, cluster them offline, and work around inconsistencies in notebooks or BI models.

These workarounds prove two things:
- Demand is real: people are spending time compensating for bad identity handling.
- The actual bottleneck is not “we lack perfect matching”; it’s “the current cleanup cadence is too slow for customer-facing moments.”

### Moment of abandonment
People abandon the current approach in the **live lookup moment**: rep searches “Jane Smith,” sees 3 records, and loses trust instantly. That is the failure point to design backward from. Weekly scripts are irrelevant at that moment. A system that is 95% perfect offline but fails in the UI still loses.

### 10x on which axis?
**Time-to-visible-improvement.** This approach is 10x better on speed to customer-facing impact. You can reduce duplicate embarrassment in weeks, not quarters, without waiting for a gold-standard identity graph.

### Adjacent analogy
This is like **email threading before mailbox deduplication**. Gmail didn’t need to rewrite the underlying storage model of every message to reduce clutter; it grouped related items in the interface first. The mechanism was simple: solve the user’s perception problem immediately, while keeping deeper normalization separate. That transfers directly here.

## First Move
Next week, product + RevOps + one engineer define the **top 5 deterministic duplicate rules** for CRM display collapse:

- exact email match  
- exact phone match  
- same full name + same company domain  
- same LinkedIn URL  
- same full name + same account owner + high field overlap  

Then implement a **read-time duplicate cluster service or CRM-side overlay** that:
- selects a primary visible record
- hides likely duplicates from default search/results
- shows a “possible duplicates” badge for manual reveal

Target only active sales views first: search results, account/contact sidebar, and opportunity linking.

## Why This Beats the Alternatives
**1. Build a full custom identity resolution platform**  
Wrong because it creates a new system engineering already doesn’t want, burns budget, and still won’t solve the immediate customer-facing Jane Smith problem fast enough.

**2. Buy a full-featured vendor**  
Wrong because $50k/year is too tight for serious cross-system identity platforms, and you’ll still spend integration effort forcing one system to satisfy both sales and analytics.

**3. Keep improving weekly scripts**  
Wrong because the core issue is latency and visibility. Weekly cleanup cannot protect live CRM moments.

## Biggest Risk
The biggest risk is that presentation-layer collapse becomes a permanent band-aid and the underlying data quality keeps degrading. If you do this without clear ownership and a separate roadmap for offline analytics resolution plus record-creation controls, you may improve the UI while making the real identity mess worse.

---

## Direction 2

## Brainstorm
1. **Do not build or buy identity resolution; replace duplicate records in CRM with a “possible same person” presentation overlay** — tags: **[2 data architecture: no shared model] [4 integration depth: presentation-layer only] [5 ownership: product/RevOps]**
2. **Outsource duplicate operations entirely to a BPO/vendor queue with humans resolving only high-visibility CRM conflicts** — tags: **[1 approach: outsourced service] [3 confidence: human-in-the-loop] [5 ownership: outsourced]**
3. **The question is wrong because CRM embarrassment is a UX problem, not an identity problem; suppress duplicates in account views and leave source systems alone** — tags: **[2 no shared model] [4 presentation-layer only] [5 ownership: product]**
4. **The question is wrong because “one true customer identity” is unnecessary at this scale; accept duplicates and add confidence labels everywhere identity is ambiguous** — tags: **[3 confidence: tolerance] [4 embedded labeling, not resolution] [5 ownership: product analytics governance]**
5. **The question is wrong because sales and data science need different truths; formalize two identities with no attempt to reconcile them centrally** — tags: **[2 federated/no single model] [5 split ownership by function] [1 don’t solve as one system]**
6. **Buy nothing and stop deduping proactively; create a concierge merge desk triggered only by executive/sales-facing records** — tags: **[1 don’t solve broadly] [3 human-in-the-loop] [4 operational workflow, not system]**
7. **Move the problem upstream by requiring stronger record creation controls and source-specific identity contracts instead of downstream resolution** — tags: **[1 don’t buy/build resolver] [4 embedded at creation points] [5 engineering + ops ownership]**

## Direction: The question is wrong: solve the demo-day CRM embarrassment, not “identity resolution”

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| “One system to satisfy everyone” | Visible duplicate embarrassment in CRM | Confidence in what sales sees live | A duplicate-suppression layer plus exception queue |
| Premature ML-resolution ambitions | Engineering scope | Speed of mitigation | A policy: unresolved identity is acceptable unless customer-facing |
| Weekly blind scripts as the main answer | Cross-team conflict over requirements | Accountability in RevOps/product | A separate later decision on analytics identity |

## The Argument
You should **neither build nor buy an identity resolution system right now**. The question is wrong because:

1. **The real urgent problem is not entity resolution; it is customer-facing CRM embarrassment.** Sales is asking why Jane Smith appears three times during a live interaction. That is a **view problem**. It does not require a canonical identity backbone.
2. **Data science and sales are asking for different products.** Sales needs fast suppression of obvious duplicates in CRM screens. Data science wants ML-grade match quality for analytics. Forcing one system to serve both is how you overspend and still disappoint both.
3. **Your budget and org constraints don’t support a general-purpose identity program.** At $50k/year and with engineering already resistant, both “build properly” and “buy properly” are mis-scoped. Even many vendors that fit the sticker price will still demand integration, tuning, stewardship, and process change you have not budgeted for.

**Why now?**  
Two things changed: first, the pain is now visible in front of customers, which makes it a revenue/credibility issue, not just data hygiene. Second, your current weekly scripts have plateaued at ~60%, which means incremental scripting will not remove the visible problem reliably enough.

**What’s the workaround today?**  
People either ignore duplicates in the moment, manually search around them, or run weekly scripts that clean up after the fact. That is acceptable for back-office hygiene, but not for live customer interactions.

**What to do instead:**  
Build a **presentation-layer duplicate suppression feature inside the CRM experience**. When a rep opens Jane Smith, the UI groups likely duplicates into one “working card” with links to underlying records. Think: “3 records likely represent the same contact — showing unified summary.” No hard merge required. No system of record changed. Add a lightweight exception queue so RevOps can confirm or separate edge cases that matter.

This is structurally different from identity resolution:
- no central customer graph,
- no canonical ID ambition,
- no broad downstream integrations,
- no ML science project,
- no claim that analytics and operations need one truth.

**10x axis:** time-to-visible-improvement for sales.

**Adjacent analogy:** Email clients solved “threading” before they solved perfect message classification. Users cared about seeing one conversation, not the ontology of every message. Do the same for CRM contacts.

## First Move
Instrument the top 20 CRM views used in live sales workflows and identify where duplicate display causes the most embarrassment. Then implement one concrete change: **on contact/account detail pages, collapse exact/near-exact duplicates into a grouped card using simple high-precision rules** (same email, same phone, or same full name + company). Owner: product + RevOps, with light engineering support. Success metric: reduction in duplicate-visible sessions in those views, not total dedup rate.

## Why This Beats the Alternatives
The obvious alternatives are wrong for this moment:

- **Build**: too much scope. A real identity system means schema design, survivorship rules, match governance, backfills, integrations, stewardship, and endless edge cases. Engineering already does not want another system.
- **Buy**: same core problem, just with license fees. Cheap tools will underperform or still require implementation effort you do not have. Expensive tools blow the budget.
- **Previous direction (“CRM masking now, analytics resolution separately”)** still accepts the premise that you eventually need a separate analytics resolution track. I would go further: **do not assume analytics identity resolution is necessary at all** until a specific model or decision is blocked by duplicate noise. Many analytics questions tolerate ambiguity better than operational CRM does.

So this wins because it attacks the only proven urgent pain, avoids a false unification project, and keeps future options open.

## Biggest Risk
The biggest risk is **organizational discomfort with not fixing the “real” data underneath**. Some stakeholders will see suppression as cosmetic. You must be explicit: yes, it is cosmetic—and that is exactly why it is the right move for a customer-facing symptom under tight budget and low engineering appetite.

---

## Direction 3

## Brainstorm
1. **Don’t build or buy identity resolution; redesign the CRM experience to show an “Account Summary” assembled at read-time from likely duplicates** — [Diff: 1 dont solve, 2 no shared model, 4 presentation-layer/real-time read, 5 product-owned]
2. **Outsource duplicate adjudication to RevOps as a queue-based operational process, backed by lightweight vendor tooling, not a system of record** — [Diff: 1 hybrid/outsource, 3 human-in-the-loop, 5 outsourced/ops-owned]
3. **The question is wrong because “identity resolution” is not the product need; the need is demo-safe seller confidence, which can be solved with a UI suppression layer and meeting-mode profiles** — [Diff: 1 dont solve, 4 presentation-layer only, 5 product-owned]
4. **The question is wrong because analytics and CRM should tolerate ambiguity differently; stop forcing one canonical identity and adopt confidence-labeled identities in each workflow** — [Diff: 2 federated/no shared canonical model, 3 tolerance model, 5 cross-functional governance]
5. **The question is wrong because duplicate profiles are partly a process-quality problem; spend the budget on prevention at capture points, not retrospective resolution** — [Diff: 1 dont solve core premise, 4 embedded at data entry, 5 ops/engineering-owned]
6. **Buy a narrow CRM-native dedup product with auto-merge disabled and route only high-confidence matches into suggested merges** — [Diff: 1 buy vendor, 3 human-review threshold, 4 embedded in CRM, 5 RevOps-owned]
7. **Use a probabilistic matching service only for analytics, and leave CRM identities untouched except for a “possible duplicate” banner** — [Diff: 2 distributed matching, 3 probabilistic ML, 4 standalone analytics service + light UI cue]
8. **The question is wrong because at 500k profiles and $50k/year, “identity resolution system” is over-scoping; define a duplicate-tolerance policy and stop trying to make Jane Smith singular everywhere** — [Diff: 1 reject/reframe, 3 tolerance, 5 executive/product policy-owned]

## Direction: The question is wrong because you do not need an identity resolution system; you need a demo-safe CRM

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| Canonical-identity ambition, auto-merge pressure, platform build scope | Customer-facing duplicate embarrassment, seller uncertainty, engineering surface area | Confidence in live CRM views, duplicate prevention at entry, explicit uncertainty handling | Read-time account summary, “possible same person” cluster cards, meeting-mode CRM view |

## The Argument
The question is wrong because it assumes the right decision is **build vs buy a system**. It isn’t. Your immediate business problem is not entity resolution; it is **public-facing CRM failure in front of customers**.

Three ways the question is wrong because:
1. **The question is wrong because it treats duplicate records as a backend data problem when the pain is a front-end trust problem.** Sales is not asking for F1 score; they are asking why Jane Smith appears three times during a call.
2. **The question is wrong because it assumes one canonical identity must serve CRM and analytics equally well.** Those workflows have different error costs. Sales needs graceful presentation; data science needs tunable confidence.
3. **The question is wrong because it assumes solving duplicates requires another permanent system.** With a $50k/year budget and an engineering team that does not want more infrastructure, a new identity platform is exactly the wrong shape of solution.

So the right move is: **build a thin presentation-layer “unified profile view” inside the CRM, not an identity resolution system.** At read-time, when a seller opens a contact or account, the UI groups likely duplicates into a single summary card: emails, last activity, owner, company, open opportunities. The original records remain untouched. No auto-merge. No canonical master. No analytics promise.

Why now? Two changes make this necessary and possible:
- **Necessary:** live customer-facing embarrassment has crossed the threshold where weekly scripts are no longer acceptable.
- **Possible:** 500k profiles is small enough for lightweight similarity scoring and precomputed candidate clusters without buying heavy MDM infrastructure.

What’s the workaround today? Weekly scripts and human memory. Reps mentally reconcile duplicates on the fly, or avoid certain CRM screens in meetings. That is expensive, brittle, and reputation-damaging.

10x axis: **time-to-trust in a live CRM view.**

Adjacent analogy: Email clients solved “conversation view” before perfect message/thread identity. They improved the user experience without first solving the entire canonical-data problem.

## First Move
Ship one concrete thing: **a “Possible Duplicates” account/contact panel in the CRM for the 50 most customer-visible reps.**

Mechanism:
- Precompute candidate duplicate clusters nightly using simple rules: exact email, normalized phone, same company + same normalized name, shared domain + high string similarity.
- In the CRM UI, collapse those records into a single summary module with a confidence label and a click-to-expand list of underlying records.
- Add a “meeting mode” toggle that hides raw duplicate rows and shows only the summary.

Who it affects: sales first.  
What changes: the embarrassing screen goes away without waiting for canonical merges.

Timeline depends on one unknown: **how customizable your CRM UI is.** If you can inject a custom panel and query precomputed clusters, this is a small product/engineering change. If your CRM is rigid, the fastest version is a browser-extension overlay or adjacent internal tool.

## Why This Beats the Alternatives
The obvious alternatives are wrong-shaped:

- **Build a full identity system:** too much scope, creates a net-new platform, and still won’t solve sales embarrassment fast enough.
- **Buy a general-purpose identity vendor:** budget is tight, implementation is still real work, and most of the value will be unused because your actual pain is CRM presentation.
- **Previous direction: “CRM masking now, analytics later.”** Too close to the original framing. It still accepts “identity resolution” as the center of gravity and treats masking as a stopgap. I’m saying the opposite: the system itself is the wrong object.
- **Previous direction: “the problem is demo-day CRM embarrassment, not identity resolution.”** This one goes further by rejecting build-vs-buy entirely and specifying a different mechanism: a read-time, no-canonical, product-owned UX layer rather than a dedup program.

Engineering should like this because it avoids a new platform. Sales should like it because it removes visible duplicates. Data science can still continue using separate matching logic for analytics later, if and when it matters.

## Biggest Risk
**The biggest risk is organizational:** stakeholders may refuse a solution that improves the visible problem without creating a canonical master record. If leadership insists that “real” solutions must merge data underneath, this direction dies even if it is the fastest, cheapest way to eliminate the actual pain.

---

## Synthesis

## The Fork

The real choice is [Bet A: CRM-Native Dedup Tool] vs [Bet B: Demo-Safe CRM Overlay] vs [Bet C: Exception-Only Human Merge Desk].

## Bet A: CRM-Native Dedup Tool
Buy a narrow CRM-native dedup product and use it for high-confidence match suggestions inside the existing sync pipeline. This is the obvious path: fastest way to reduce duplicate creation and clean obvious collisions without inventing a new platform. Keep matching deterministic at first—email, phone, domain, normalized name—and require approval for anything ambiguous. RevOps owns operations; engineering only handles integration and field mapping. This defends the premise that duplicates are a real data problem worth addressing directly, but scopes it to what your budget and team can support.
**First move:** Evaluate 3 CRM-native vendors against 500k-profile volume, approval workflow, API limits, and total annual cost under $50k.
**Sacrifice:** You give up deeper cross-system identity ambition and accept vendor constraints, limited customization, and likely weak support for analytics-grade resolution.

## Bet B: Demo-Safe CRM Overlay
Do not solve identity resolution as a system. Build a presentation-layer duplicate collapse in the CRM so reps see one working profile with a “possible duplicates” badge. No hard merges, no shared identity graph, no canonical truth. Product/RevOps own the workflow; engineering builds a thin read-time service or UI extension. Matching stays high-precision and deterministic because the goal is seller trust, not perfect entity science. This wins if the urgent pain is live embarrassment in front of customers and engineering resists new infrastructure. It changes the experience in weeks while preserving future options.
**First move:** Instrument top sales screens, define 5 high-precision grouping rules, and ship collapse behavior for search results and contact/account views.
**Sacrifice:** You leave underlying data messy, may entrench a cosmetic fix, and learn little about whether a broader identity program is ever justified.

## Bet C: Exception-Only Human Merge Desk
Don’t build software beyond basic queueing. Route only high-visibility duplicate conflicts—active pipeline, executive accounts, customer-facing contacts—into a human-reviewed merge desk run by RevOps or an outsourced service. This changes the confidence model completely: humans adjudicate ambiguity, not rules or ML. Integration is shallow; ownership is operational, not technical. It fits a low-engineering, low-budget environment and targets the top 5% of records where mistakes matter most. Choose this if duplicate pain is concentrated and you need control more than scale.
**First move:** Stand up a daily exception queue fed by simple duplicate triggers and staff one RevOps owner with SLA targets for sales-critical records.
**Sacrifice:** You give up scale, automation learning, and the chance to build a durable data asset; duplicate handling remains a service, not a capability.

## Comparison

| | Timeline | Risk | What you learn | Strategic sacrifice |
|---|----------|------|----------------|---------------------|
| **Bet A** | 4–8 weeks if a CRM-native tool fits current stack; longer if procurement/security drag | Vendor underperforms, integration friction, false positives annoy reps | Whether direct dedup in CRM materially reduces duplicate creation and cleanup load | Flexibility to design a bespoke cross-system identity layer later |
| **Bet B** | 2–6 weeks if CRM UI is customizable; unknown if overlay requires workaround | CRM customization limits, UI confusion, hidden duplicates mask deeper issues | Whether the real pain is presentation/trust rather than underlying identity quality | Canonical-data ambition and pressure to “truly” fix records now |
| **Bet C** | 1–3 weeks to launch a queue with simple triggers and staffing | Operational backlog, inconsistent human decisions, SLA misses | Where duplicate pain is actually concentrated and what ambiguity humans can resolve reliably | Scale economics and the option to treat dedup as an automated product capability |
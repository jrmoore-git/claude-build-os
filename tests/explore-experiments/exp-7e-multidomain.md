---
mode: explore
created: 2026-04-11T00:08:00-0700
model: gpt-5.4
directions: 3
prompt_versions: explore=3, diverge=4, synthesis=4
---
# Explore: Should we build or buy an identity resolution system?

## Direction 1

## Brainstorm
1. Buy a lightweight dedup vendor and sync its “golden record” back into the CRM, accepting a black-box matcher to get sales relief fast.
2. Build an internal entity-resolution service with deterministic rules first, then add probabilistic matching for analytics later.
3. Split the problem: fix CRM duplicates only in the presentation layer now, while leaving source systems untouched and postponing full identity resolution.
4. Stop trying to create one master identity system and instead add a “possible duplicate” workflow with human confirmation at the point of pain.
5. Outsource matching operations entirely to a specialist data-ops vendor and treat identity resolution as a managed service, not a product capability.
6. Create a canonical identity graph in the warehouse for analytics only, and explicitly do nothing for CRM until the graph proves value.
7. Use LLM-assisted match explanation on top of simple rules so reps see one merged customer card plus the reason records were grouped, even if backend records remain separate.
8. Embrace duplicate tolerance: redesign sales workflows so duplicate records are harmless, and stop investing in resolution except for high-value accounts.
9. Make identity resolution a product-owned trust layer with confidence bands, where only high-confidence merges are auto-hidden and everything else is surfaced as uncertainty.
10. Reframe the problem entirely: the issue is not identity resolution but live-demo credibility, so solve “customer-facing record embarrassment” rather than enterprise-wide dedup.

## Direction: Solve demo embarrassment, not identity resolution

## The Argument
Do not build or buy a full identity resolution system right now. Build a **presentation-layer duplicate suppression layer inside the CRM** that collapses obvious duplicates in real time for sales, and keep analytics matching separate in the warehouse. This is a hybrid answer: **don’t solve the whole problem yet; solve the public failure point immediately**.

The mistake is treating one question as if it were one system. It is not. Sales is asking, “Why does Jane Smith appear 3 times when a customer is watching?” That is a **trust and UX problem**, not an enterprise identity architecture problem. Data science wants something different: a durable, probabilistic entity graph for analytics. Engineering is right that building another central system under a $50k/year budget is a trap.

So the right move is:
- **Solution approach:** hybrid, with no full master system now
- **Data architecture:** no shared global model yet; lightweight duplicate groups for CRM views, warehouse-native matching for analytics later
- **Match confidence model:** deterministic + human-tolerant confidence bands for CRM
- **Integration depth:** presentation-layer only for CRM, not source-of-truth mutation
- **Ownership:** product/revops, not engineering platform

### Why now?
Two things changed versus two years ago.

First, modern CRMs and internal app layers now make it cheap to **overlay a unified customer card without rewriting underlying records**. You no longer need to physically merge records to give sales a clean view.

Second, stakeholder expectations have diverged. Sales needs **instant credibility in live workflows**; data science needs **traceable match quality**. Two years ago, teams still got pressured into one “customer 360” project. Today the smarter move is unbundling: operational views and analytical identity do not need the same system on day one.

### What’s the workaround?
You already have it: weekly manual scripts, partial merge logic, and reps mentally stitching together duplicate records on the fly. Some teams also use saved searches, account naming conventions, or revops cleanup tickets before big calls. Those are ugly workarounds, but they prove demand: people care enough to manually compensate.

They also reveal the real constraint: nobody actually needs perfect global identity to get value. They need **the duplicate to stop being visible at the wrong moment**.

### Moment of abandonment
People abandon the current approach during a live customer interaction. Not in the warehouse. Not in a data quality review. The failure point is when a rep searches “Jane Smith,” sees three near-identical profiles, and loses confidence in front of the customer. Design backward from that moment.

That means the system should optimize for:
1. very low false-positive merges in CRM views,
2. instant response,
3. visible explanation like “Showing 1 of 3 likely duplicate records.”

### 10x on which axis?
**Time-to-trust for sales.** Not match accuracy overall. Not architecture elegance. This is 10x better on the single dimension that matters now: how fast you eliminate embarrassing duplicate exposure in customer-facing workflows.

### Adjacent analogy
This is the same pattern as **email threading**. Email clients didn’t solve the full identity of every sender or canonicalize all message metadata globally. They solved the user-facing problem first: “show this conversation as one thread so the inbox feels coherent.” The mechanism transfers: **group noisy underlying records into a cleaner operational view without pretending the backend is fully resolved**.

## First Move
Next week, product + revops should define the **top 5 duplicate patterns** causing sales embarrassment: exact email match, same phone, same company + full name, plus known import-source collisions.

Then implement a CRM-side “Likely Duplicate Group” card:
- on search results and profile pages,
- auto-collapse only when confidence is high,
- show one primary record,
- display “2 similar records hidden,”
- allow reps to expand if needed,
- do not physically merge anything.

Measure one thing for 30 days: **duplicate appearances per sales session**.

## Why This Beats the Alternatives
**Buying a full vendor now** is too broad for the budget and the wrong shape for the problem. Most identity vendors are built for cross-channel CDP/MDM use cases, not “make live CRM search not embarrassing.” You’ll pay for architecture you won’t fully integrate.

**Building a full internal identity service** is classic overreach. Engineering will inherit another quasi-platform, and you still won’t satisfy sales quickly because source merging, survivorship, and downstream sync all take too long.

**Doing only warehouse matching for data science** ignores the acute pain. It may produce better analytics, but sales will still see Jane Smith three times tomorrow.

## Biggest Risk
The biggest risk is organizational drift: this “presentation-layer fix” gets mistaken for a complete identity strategy and stalls the eventual analytics-grade solution. Prevent that by naming it correctly from day one: **CRM duplicate suppression**, not enterprise identity resolution.

---

## Direction 2

## Brainstorm
- **CRM-native merge layer + analyst review queue** — buy a lightweight duplicate-management app inside the CRM, with humans approving ambiguous merges; presentation-level fix first, not a new identity platform. **[Diff: approach=buy, architecture=no shared model/CRM-local, confidence=human-in-the-loop, integration=presentation-layer, ownership=ops/product]**
- **Outsource dedup operations to a RevOps/BPO service** — pay for managed duplicate cleanup with SLAs and playbooks, using existing CRM/admin tools rather than software you own. **[Diff: approach=outsourced, architecture=no new model, confidence=human-in-the-loop, integration=embedded in business ops not pipeline, ownership=external]**
- **Tolerance-based “possible duplicate” UX instead of hard identity resolution** — don’t merge records systemically; flag likely dupes at account/contact view and before demos. **[Diff: approach=don’t fully solve, architecture=no shared model, confidence=tolerance not exact match, integration=presentation-layer, ownership=product/sales ops]**
- **Real-time enrichment API from a vendor CDP/ID service** — route record create/update events to a third-party identity API that returns canonical IDs. **[Diff: approach=buy, architecture=vendor-centralized, confidence=probabilistic ML, integration=real-time API, ownership=engineering]**
- **Federated matching only for analytics** — leave CRM alone, use warehouse-native entity resolution for data science models and reporting. **[Diff: approach=hybrid, architecture=federated/warehouse-only, confidence=probabilistic ML, integration=analytics pipeline, ownership=data science]**
- **Pre-demo concierge cleanup workflow** — create a workflow where customer-facing records get scrubbed before meetings; solve embarrassment operationally, not globally. **[Diff: approach=process not platform, architecture=no shared model, confidence=human review, integration=workflow layer, ownership=sales ops]**
- **Mastered account-only resolution, ignore contact-level duplicates** — narrow scope to company/account identity where pain is highest in CRM views and cheaper to buy tools for. **[Diff: approach=scope reduction, architecture=partial shared model, confidence=rules+review, integration=CRM embedded, ownership=RevOps]**

## Direction: Buy a CRM-native duplicate-management layer with human review

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| New platform build, cross-system “single source of truth” ambition, weekly script dependency | Live-demo embarrassment, accidental bad merges, engineering lift | CRM trust for sales, merge accuracy on high-value records, speed of cleanup | Analyst review queue, duplicate score in-record, merge SLAs by customer-facing priority |

## The Argument
Yes: **buy a narrow CRM-layer dedup solution, not an identity resolution system.**

This accepts the premise that you need duplicates gone, but uses a different mechanism: **solve the visible CRM problem where it occurs**, with a vendor tool designed for duplicate detection/merge workflow in the CRM and a small human review loop for uncertain cases.

Why this is right:

**Why now?**  
Two things changed. First, the pain is now front-stage: sales is asking why “Jane Smith” appears three times while customers are watching. That is a trust problem, not just a data-quality metric. Second, the market now has cheap, CRM-native duplicate tools that can be configured in days, not months, and fit inside a $50k/year budget. You no longer need to choose between brittle scripts and a full-blown identity graph.

**What’s the workaround today?**  
You already have it: weekly manual scripts catching ~60%. Everyone is compensating with tribal knowledge, pre-demo record searches, and awkward explanations. Data science likely does local cleanup in analysis anyway. The workaround is expensive in credibility and recurring labor.

**Mechanism**  
Buy a tool that:
- scans CRM records continuously or daily for likely duplicates,
- scores candidate pairs,
- auto-merges only exact/high-confidence cases by rule,
- routes medium-confidence cases to an analyst queue,
- surfaces “possible duplicate” warnings on contact/account pages before sales presents them.

This is **not** enterprise identity resolution. It is **duplicate management in the CRM UI and workflow**.

**10x axis:** time-to-visible-improvement.  
Sales does not need perfect entity resolution; they need Jane Smith not to embarrass them in front of customers. This direction improves that axis fastest.

**Adjacent analogy:** fraud review, not autopilot.  
Payments teams don’t auto-approve every borderline transaction with a giant custom system on day one; they combine vendor scoring with manual review for ambiguous cases. That pattern works here.

Budget-wise, this is the only option aligned with constraints:
- Software: many CRM dedup/admin tools fit in low tens of thousands annually.
- People: one RevOps/data steward can review ambiguous merges as part of ongoing hygiene.
- Engineering: minimal involvement, mostly installing package, permissions, and event/config setup.

This also creates a cleaner organizational contract:
- **Sales** gets immediate CRM improvement.
- **Engineering** avoids building another system.
- **Data science** is free to pursue stricter matching separately in the warehouse later, without blocking CRM cleanup now.

## First Move
**Within 2 weeks, run a live bake-off on your own CRM data with 2 CRM-native duplicate vendors.**

Specifically:
1. RevOps exports a representative sample: 50k contacts/accounts including known duplicate-heavy segments.
2. Two vendors run trial scans and show:
   - exact duplicates found,
   - medium-confidence candidates,
   - merge workflow,
   - in-record duplicate warnings,
   - admin controls/undo/audit trail.
3. Score them on three hard criteria:
   - reduction of duplicate-visible records in CRM,
   - false-merge risk,
   - total admin time per week.

Decision maker: **Head of RevOps/Product**, not engineering. Engineering only validates security/integration effort.

## Why This Beats the Alternatives
**Versus building:**  
Custom identity resolution is the wrong economic shape for $50k/year and the wrong speed for a sales-visible problem. You’ll spend months on matching logic, edge cases, merge semantics, undo paths, and stakeholder fights over truth definitions.

**Versus a full vendor identity graph/CDP:**  
Too broad. You’ll pay for cross-channel identity capabilities you do not need to stop CRM embarrassment.

**Versus warehouse-only matching:**  
Helpful for analytics, irrelevant when a salesperson opens the CRM in front of a customer.

**Versus doing nothing but improving scripts:**  
Still brittle, still batchy, still invisible in workflow, still no review queue or user-facing warnings.

**Versus the previous direction(s):**  
This is not a custom system and not a back-end identity model. It is a **bought, CRM-local, human-reviewed operational layer** owned by RevOps/product, optimized for customer-facing trust rather than universal identity correctness.

## Biggest Risk
**Bad merges that sales cannot easily undo.**

If the chosen tool has weak audit/rollback controls, one wrong auto-merge will destroy trust faster than three duplicate Janes. The kill criterion is simple: if you cannot inspect, approve, and reverse merges cleanly, do not buy it.

---

## Direction 3

## Brainstorm
- **The question is wrong because “identity resolution” bundles three jobs that should be separated**: treat CRM display, analytics entity linking, and operational record stewardship as different products with different tolerances; solve only the view layer now. **[Differs: 1 approach=dont solve as one system, 2 architecture=no shared model, 4 integration=presentation-layer, 5 ownership=product/ops]**
- **The question is wrong because duplicates are not the main failure; uncontrolled record creation is**: stop creating new Janes unless minimum evidence is provided, and make ambiguous creates impossible in key workflows. **[1 dont solve/build prevention, 3 deterministic tolerance, 4 embedded in workflow, 5 ownership=product/RevOps]**
- **The question is wrong because “one true customer record” is unnecessary for most work**: move to federated identities with context-specific IDs and explicit uncertainty, instead of merging records. **[1 hybrid/dont merge, 2 federated, 3 tolerance, 4 API plus UI badges, 5 engineering/platform]**
- **The question is wrong because sales is asking for confidence in front of customers, not perfect identity resolution**: create a “customer-safe presentation mode” that suppresses likely dupes, groups similar contacts, and hides ambiguity during demos. **[1 presentation workaround, 2 no shared model, 3 tolerance threshold, 4 presentation-layer only, 5 product]**
- **The question is wrong because the cheapest path is to downgrade the requirement**: declare duplicate elimination out of scope; publish duplicate-rate SLOs by funnel stage and only enforce uniqueness where it affects revenue workflows. **[1 dont solve broadly, 2 no centralized model, 3 deterministic policy, 4 embedded controls, 5 ops leadership]**
- **The question is wrong because analytics and CRM should not share an identity substrate**: let data science use warehouse-side probabilistic linkage on snapshots while CRM remains source-native and mostly untouched. **[1 hybrid split, 2 distributed matching, 3 probabilistic ML for analytics only, 4 warehouse pipeline, 5 data science]**
- **The question is wrong because this is a governance problem disguised as a tooling decision**: assign record-domain owners, define merge authority, and require human accountability for high-value accounts instead of algorithmic identity resolution. **[1 process/governance, 3 human stewardship, 4 workflow/ops, 5 product+RevOps]**
- **Contrarian: the question is wrong because showing raw CRM data to customers is the avoidable mistake**: redesign customer-facing moments so no one sees internal contact lists at all. **[1 eliminate use case, 2 no shared model, 4 presentation/process change, 5 sales enablement/product]**

## Direction: Stop Asking for “Identity Resolution”; Split the Problem and Fix Record Creation

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| The idea of one system serving sales, analytics, and ops | New duplicate creation in lead/contact workflows | Evidence required before creating a new person/account | Separate products: create-time guardrails, customer-safe CRM views, warehouse linkage |
| Customer-facing exposure to raw ambiguous CRM records | Pressure to merge everything into one canonical record | Accountability of RevOps/product owners for duplicate policy | Explicit uncertainty states instead of forced merges |

## The Argument
No: do not start with “build or buy an identity resolution system.” The question is wrong because it assumes one problem, one architecture, and one answer.

You have **three different jobs**:
1. **Sales UX**: don’t embarrass reps in front of customers.
2. **Analytics linkage**: let data science do entity-level analysis.
3. **Operational hygiene**: keep duplicate creation from accelerating.

Those jobs have different economics and different error costs. Forcing them into one identity-resolution program is how you burn $50k/year and still disappoint everyone.

The right direction is to **stop solving retrospective identity globally** and instead **prevent new duplicates at creation time**, while letting each downstream use case handle ambiguity differently.

**Why now?**  
What changed is scale and stakeholder conflict. At 500k profiles and ~15% duplicate rate, weekly cleanup is now losing to inflow. The current system catches 60% after the fact, which means the real defect is upstream: your workflows still allow low-evidence record creation. Also, modern product teams can now put lightweight search-before-create, required evidence fields, and “possible existing record” interstitials directly into CRM-adjacent workflows without launching a master-data initiative.

**What’s the workaround today?**  
People are doing two bad workarounds:
- Sales mentally ignores duplicates or gets surprised live.
- Ops runs weekly scripts that clean up after the damage.
That is equivalent to fixing typos in published books instead of changing the keyboard.

**What to do instead**
- In any workflow that creates a lead/contact/account, require minimum identity evidence before save.
- On create, show likely existing records and force the user to attach or justify a new record.
- For customer-facing CRM views, default to grouped/hidden ambiguous records rather than exposing raw duplicates.
- Let data science do warehouse-side probabilistic linkage separately for analytics. That is not the same product.

This is a **10x on operational leverage**, not matching accuracy. If you cut duplicate creation by half, the weekly scripts suddenly become good enough for legacy cleanup, and the problem decays instead of compounds.

**Adjacent analogy:** fraud teams stopped trying to “perfectly clean” all historical transactions before checkout; they moved risk controls to the moment of transaction. Same pattern here: block bad record creation where it starts.

## First Move
Instrument the top three duplicate-creating workflows in the CRM this week: lead import, manual contact creation, and account creation from sales. For each, measure:
- how many new records are created,
- what fields are present at create time,
- how often email/domain/name+company already exist.

Then pick **one workflow**—manual contact creation for sales—and change it so a rep cannot create “Jane Smith” without either linking to an existing likely match or providing a missing unique identifier and a reason code. This immediately affects the stakeholder causing the most visible pain and creates the first decision signal: whether duplicate inflow drops materially when friction is added.

## Why This Beats the Alternatives
The obvious approaches are wrong for your budget and disagreement pattern.

A full build assumes you need a shared canonical identity layer. You don’t. Engineering already does not want another system, and $50k/year is not enough to build and maintain something credible across CRM + analytics + ops.

A buy decision sounds safer, but it still accepts the false premise that one duplicate-management product should satisfy sales immediacy, analytics rigor, and operational stewardship. It won’t. You’ll either overfit to CRM cleanup or underdeliver on ML-grade linkage.

Previous directions also point the wrong way because they start downstream:
- Solving demo embarrassment alone treats the symptom, not the source.
- Buying CRM-native dedupe with human review still centers retrospective cleanup and review queues, which do not stop new duplicates from entering.

This direction changes the game: **separate the problems, attack creation, and stop pretending one identity system is the right unit of decision.**

## Biggest Risk
Sales may revolt against added friction at record creation. If reps feel slowed down, they will route around the process or push for rollback. If you cannot make create-time checks fast and narrowly targeted to high-risk cases, the policy dies.

---

## Synthesis

## The Fork

The real choice is [Bet A: Buy CRM-Native Dedup] vs [Bet B: Presentation-Layer Suppression] vs [Bet C: Prevention-First Split Model].

## Bet A: Buy CRM-Native Dedup
Buy a narrow duplicate-management tool inside the CRM, with rule-based auto-merges for obvious matches and analyst review for ambiguous cases. This is the conventional answer because it directly attacks the visible problem where sales feels it, without asking engineering to build a platform. It differs from a custom identity system by staying CRM-local, human-reviewed, and operationally owned by RevOps/product. It works if the real need is fast reduction in duplicate exposure, not enterprise-wide identity truth. Under a $50k budget, this is the highest-probability path to visible improvement in weeks, provided rollback, audit trail, and merge controls are strong.
**First move:** Run a 2-vendor bake-off on a 50k-record CRM sample; score duplicate reduction, false merges, admin hours, and undoability.
**Sacrifice:** You give up owning core matching capability and likely postpone any broader cross-system identity architecture.

## Bet B: Presentation-Layer Suppression
Don’t merge records or buy identity resolution yet. Build a CRM-side duplicate suppression layer that groups obvious duplicates in search and profile views, shows one primary card, and reveals “2 similar records hidden” with explanation. Keep source systems untouched and let analytics solve matching separately later. This works if the urgent pain is demo embarrassment, not database correctness. It differs from Bet A by being custom, presentation-only, deterministic/tolerance-based, and product-owned rather than vendor-managed. It minimizes false-merge risk because nothing is physically merged. If sales just needs trust in customer-facing moments, this is the fastest path to relief with the least architectural commitment.
**First move:** Define the top 5 duplicate patterns and ship a “Likely Duplicate Group” card in CRM search/results for high-confidence cases only.
**Sacrifice:** You intentionally leave underlying duplicate data and downstream workflow mess largely untouched.

## Bet C: Prevention-First Split Model
Reject “identity resolution” as the wrong unit of decision. Split the jobs: prevent new duplicate creation in workflows, use grouped views for sales, and let data science do separate warehouse-side probabilistic linkage. The core bet is that inflow is the real defect; retrospective cleanup will never catch up while creation remains loose. This differs from A and B on solution approach, architecture, integration depth, and ownership: no single system, no shared master model, workflow-embedded controls, owned by product/RevOps with analytics separately owned by data science. It works if duplicate volume is compounding faster than cleanup and the organization can tolerate more friction at create-time.
**First move:** Instrument lead import, manual contact creation, and account creation; then add search-before-create and required evidence to one high-volume workflow.
**Sacrifice:** You give up the fantasy of one near-term unified customer record and accept more process friction.

## Comparison

| | Timeline | Risk | What you learn | Strategic sacrifice |
|---|----------|------|----------------|---------------------|
| **Bet A** | 2–6 weeks to know, based on typical CRM app trials and config-heavy rollout | Bad merges, weak rollback, analyst queue overload | Whether a vendor can materially reduce visible dupes within budget and acceptable admin load | Dependence on vendor logic; less incentive to build internal identity capability |
| **Bet B** | 1–4 weeks for first UX impact if CRM/app layer is editable; unknown if CRM customization is constrained | Suppression misses too many cases or is mistaken for a full solution | Whether the pain is primarily customer-facing trust rather than data correctness | Underlying data quality remains; limited help for ops and downstream systems |
| **Bet C** | 2–8 weeks to see duplicate inflow change; depends on workflow control points and rep compliance | Sales pushes back on added friction; users route around controls | Whether duplicate creation is the dominant driver and which workflows cause it | No single-system narrative; slower path to a unified identity story |
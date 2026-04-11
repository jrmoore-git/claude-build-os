---
mode: explore
created: 2026-04-10T23:59:26-0700
model: gpt-5.4
directions: 3
prompt_versions: explore=3, diverge=4, synthesis=4
---
# Explore: Should we build or buy an identity resolution system?

## Direction 1

## Brainstorm
- Buy a lightweight identity-resolution vendor now and use it as the system of record for matching, because the budget and urgency favor speed over elegance.
- Build a rules-based dedup service in-house embedded in the data pipeline, with deterministic matching for visible product records and manual review for edge cases.
- Go hybrid: buy a vendor matching core for batch/entity graph creation, but build your own product-facing merge policies, review tooling, and customer-view suppression layer.
- Ignore “identity resolution” as the primary problem and instead build a customer-facing canonicalization layer that hides duplicates in sales views without fully solving backend entity resolution.
- Create a shared “duplicate risk queue” with human-in-the-loop adjudication, optimizing for the last 20% of high-cost duplicates rather than full automation.
- Build a probabilistic graph-based resolver owned by data science, but only for analytics use cases, while product keeps a separate deterministic operational identity model.
- Do the uncomfortable thing: stop trying to unify all teams on one system and run two identity systems on purpose—one operational and one analytical—with explicit translation rules.
- Use a federated approach where source systems retain identity ownership and a thin resolution service creates just-in-time links instead of a centralized golden record.
- Buy nothing and repurpose modern LLM-assisted record comparison plus existing warehouse tooling to create a low-cost, analyst-operated matching workflow.
- Reframe the question entirely: the problem is not build vs buy, it is governance—who has authority to define “same profile” for sales, support, and analytics when those definitions are legitimately different.

## Direction: Build a customer-facing suppression layer now, not a full identity system

## The Argument
The most interesting move is to **stop treating this as one identity-resolution problem**. You have two different jobs masquerading as one:

1. **Sales/product need duplicate invisibility** in customer-facing views, immediately.  
2. **Data science needs better entity matching** for analytics, eventually.

Those are not the same architecture, confidence model, integration pattern, or owner. Forcing one system to satisfy both under a $50k budget is how teams burn six months and still ship nothing.

So the right direction is: **build a narrow, product-owned duplicate suppression layer for customer-facing experiences now, and postpone full identity resolution to a later hybrid evaluation.** This is a custom layer, distributed over existing systems, deterministic-plus-review, integrated in real-time where duplicates are visible, owned by product+engineering. That differs from the obvious “buy a platform for everything” path on at least four dimensions.

### Why now?
Two things changed:

- **The cost of visible bad data has become immediate revenue loss.** This is no longer a back-office data hygiene issue; sales is losing deals because customers see duplicate records. Once the defect is customer-visible, latency matters more than theoretical matching quality.
- **Modern warehouse/app stacks make thin canonicalization layers cheap to build.** Two years ago, you were choosing between clunky weekly scripts or a large MDM project. Today you can stand up a real-time suppression service on top of your existing profile store, use deterministic match clusters for high-confidence cases, and expose one canonical profile in the UI without replatforming everything.

### What’s the workaround?
Today’s workaround is exactly what proves demand:  
- weekly dedup scripts,  
- reps manually ignoring or mentally merging duplicates,  
- downstream analysts cleaning data in notebooks.

That tells you two things. First, people absolutely need deduplication. Second, they are already accepting **use-case-specific truth**. Sales just needs the UI not to embarrass them. Analysts need cleaner aggregates. Nobody truly needs a philosophical “single identity” by next quarter.

### Moment of abandonment
People quit the current approach at the point where **duplicate cleanup is no longer upstream of the customer interaction**. Weekly scripts catch 60%, but the remaining 40% appear in live views, and that’s where trust collapses. Design backward from that moment: when a rep opens an account or contact, the system should suppress obvious siblings and present one canonical record plus “possible duplicates” behind the scenes.

### 10x on which axis?
**Time-to-visible-trust.** Not overall matching quality. Not long-term elegance. This approach is 10x better on the single axis that matters now: how fast you stop showing embarrassing duplicate records to customers and sales.

### Adjacent analogy
This is how **email spam filtering** evolved operationally: providers didn’t solve the entire abuse/identity problem before helping users—they built a high-confidence suppression layer first, hiding the worst mess while richer models matured in parallel. The mechanism transfers because both problems have asymmetric costs: a visible bad outcome hurts more than an unseen unresolved edge case.

## First Move
Next week, create a **“canonical profile service”** for the customer-facing views only.

Specifically:
1. Product + eng define the 3 views where duplicates hurt deals most.
2. Data team extracts the top duplicate patterns from the current scripts: exact email, normalized domain+name, phone, CRM external ID conflicts.
3. Engineering builds a small service/table that assigns a **display_canonical_id** for high-confidence duplicate clusters only.
4. UI changes: customer-facing screens show only the canonical record; secondary records are hidden behind “possible linked profiles.”
5. Add an internal review queue for ambiguous matches, handled by sales ops or support.

This can ship in weeks, not quarters.

## Why This Beats the Alternatives
**Buy a full vendor now:**  
Too broad for the budget and too slow for the immediate revenue problem. Most vendors will promise one graph for all use cases, but integration, policy decisions, and merge semantics will dominate the timeline—not the matching engine.

**Build a full in-house identity system:**  
Classic trap. You’ll spend months arguing about match definitions, golden records, survivorship, and ownership. Meanwhile duplicates still show up in the product.

**Hybrid vendor-core now:**  
More sensible than pure buy, but still starts at the wrong layer. If the first milestone is “vendor connected to all profile sources,” you have already lost focus. Solve the visible pain first; decide later whether the backend graph should be bought.

## Biggest Risk
The biggest risk is **organizational, not technical**: data science will see this as a partial solution and object that it doesn’t improve analytics identity quality enough. They’ll be right. This direction only works if leadership explicitly separates **operational duplicate suppression** from **analytical identity resolution** and agrees that the first one gets solved first.

---

## Direction 2

## Brainstorm
1. **Don’t solve identity resolution; redesign the product to tolerate ambiguity** — the question is wrong because perfect identity isn’t required to stop sales pain; show “possible related records” in UI and route merge decisions into workflow, not backend truth. **[Differs: data architecture=federated/no central graph, match model=human-in-the-loop, integration depth=product-embedded workflow, ownership=product+sales ops]**
2. **Buy a lightweight MDM/CRM-native dedupe app and constrain scope to sales-critical objects only** — use a vendor for account/contact dedupe in the operational system, explicitly not enterprise-wide identity resolution. **[Differs: build/buy=buy, integration depth=embedded in system of record, ownership=RevOps, match model=deterministic vendor rules]**
3. **Create a “golden record for analytics only” in the warehouse, and leave product records alone** — the question is wrong because DS and sales need different things; solve analytical identity separately in batch with probabilistic linkage. **[Differs: data architecture=centralized warehouse graph, match model=probabilistic ML, integration depth=data pipeline, ownership=data science]**
4. **Stand up a brokered identity layer using open-source entity resolution plus paid review tooling** — hybrid approach: OSS matcher, custom orchestration, human review queue for uncertain merges. **[Differs: build/buy=hybrid, match model=human-in-the-loop + probabilistic, ownership=shared product+eng+ops]**
5. **Outsource duplicate adjudication to operations, not software** — the question is wrong because 75k suspect records at this scale may be cheaper to clean operationally than to systematize under a $50k budget. **[Differs: build/buy=neither/process solution, match model=human-only, ownership=ops team, integration depth=none/minimal]**
6. **Adopt an event-time identity service only for new records, and freeze legacy cleanup** — real-time API for ingress dedupe, accept historical mess for now. **[Differs: integration depth=real-time API, data architecture=distributed matching at write-time, ownership=platform eng]**
7. **Invert the problem: enforce upstream data contracts and capture better identifiers instead of matching later** — the question is wrong because duplicates are a data creation problem first; fix lead import, form capture, CRM entry rules, and partner feeds. **[Differs: mechanism=prevention not resolution, integration depth=input systems, ownership=shared RevOps+eng, match model=deterministic validation]**

## Direction: Don’t solve identity resolution; redesign the product to tolerate ambiguity

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| the assumption that one backend identity must exist before users can act | false precision, forced merges, cross-team deadlock | salesperson confidence, transparency of uncertainty, time-to-visible-fix | “possible duplicate” UI, merge inbox, confidence labels, account-owner adjudication workflow |

## The Argument
You asked “build or buy an identity resolution system?” The better answer is: **don’t start there.** The question is wrong because:

1. **The sales problem is not identity resolution; it is duplicate visibility in customer-facing workflows.**  
2. **The data science problem is not the same problem as the product problem.** A single system won’t satisfy both well under a $50k/year budget.  
3. **A backend truth system is the most expensive way to remove UI embarrassment.** You can reduce lost deals faster by making ambiguity visible and actionable.

So the direction is: **make the product resilient to duplicate uncertainty instead of pretending you can cheaply establish universal identity now.**

What changes: in customer-facing views, when two records are likely related, the UI shows **“Possible duplicate records”** with key fields side-by-side, plus a one-click action: **merge, dismiss, or assign for review**. Keep current records intact until a human confirms. This avoids bad auto-merges, which are harder to unwind than duplicate display.

**Why now?**  
Two things changed: first, duplicates are now causing direct revenue loss, which means this is a workflow problem, not just data hygiene. Second, your current scripts already catch ~60%, so you have enough signal to generate a review queue and UI hints immediately without inventing a full identity platform.

**What’s the workaround today?**  
People are doing exactly what weak systems force them to do: manual scripts weekly, tribal knowledge from account owners, and sales reps noticing duplicates too late in front of customers. That workaround is expensive, embarrassing, and inconsistent.

**10x on which axis?**  
**Time-to-visible-improvement.** You can change what sales sees before you solve enterprise identity.

**Adjacent analogy:**  
Fraud systems often do not block every suspicious transaction automatically; they surface **risk + review workflows** because ambiguity is operational, not purely algorithmic. Same pattern here.

## First Move
Instrument the top 3 customer-facing views where duplicates cost deals, and add a non-destructive **“Possible duplicate” module** fed by your existing weekly dedup output plus 2-3 simple additional heuristics (same email domain + company name similarity + owner overlap). The first affected users are sales reps and account managers. Success metric: reduction in duplicate-related deal escalations and faster human resolution of suspect records.

## Why This Beats the Alternatives
The obvious approaches are wrong for different reasons:

- **Build a full identity system:** too much scope, too many stakeholders, and no budget room for platform work plus governance. You will spend months arguing about canonical truth while sales keeps losing deals.
- **Buy an identity platform:** $50k/year is tight, and most value will be trapped in integration and process change anyway. Vendor capability won’t fix unresolved ownership across product, DS, and sales.
- **Analytics-first identity graph:** good for DS, irrelevant to visible duplicate records in live workflows.
- **Pure prevention/upstream contracts:** useful, but it does nothing for the 75k-ish existing duplicate profiles already hurting deals.
- **Human cleanup only:** better than doing nothing, but without UI support and prioritization, ops work won’t hit the moments that matter commercially.

This direction also deliberately avoids the failure mode of prior “suppression layer” thinking: it is **not** a hidden patch to mask records. It is a **workflow redesign** that exposes uncertainty, routes ownership, and makes action possible without declaring false truth.

## Biggest Risk
The biggest risk is organizational: teams may reject a solution that admits uncertainty because they want a “real” identity answer. If leadership treats visible ambiguity as unacceptable, they will force premature auto-merging and recreate the same problem in a riskier form.

---

## Direction 3

## Brainstorm
1. **Buy a CRM-native data quality app and make the CRM the system of record** — vendor-first, centralized in existing platform, deterministic rule engine, embedded in operational workflow, owned by RevOps rather than eng/data. **[Differs: build/buy, data architecture, match model, ownership]**

2. **Use a human-in-the-loop merge queue with model-assisted triage, not automated identity resolution** — hybrid, distributed candidate generation plus reviewer decisions, human-in-the-loop confidence, embedded in back-office ops tooling, owned by a shared RevOps+support function. **[Differs: match model, integration depth, ownership]**

3. **The question is wrong because you don’t need “identity resolution”; you need customer-record governance with SLA-backed stewardship** — reframe to operating model, hybrid lightweight tools, federated ownership by domain stewards, human adjudication, process embedded in account lifecycle. **[Differs: ownership, match model, integration depth, premise]**

4. **The question is wrong because duplicates are a workflow-quality problem created upstream, so buy form enrichment/validation and block bad record creation** — vendor-first prevention, federated at data-entry points, deterministic validation, real-time API at ingest, owned by product ops / RevOps. **[Differs: build/buy, data architecture, integration depth, ownership, premise]**

5. **The question is wrong because one identity system cannot satisfy sales and data science; split operational identity from analytical identity** — hybrid: buy ops dedup tooling, keep DS probabilistic entity resolution in warehouse, dual architecture, different confidence models per use case, separate ownership. **[Differs: data architecture, match model, integration depth, ownership, premise]**

6. **Outsource dedup entirely as a managed data-ops service with contractual accuracy SLAs** — buy/service, external human review plus vendor tooling, periodic batch embedded in CRM/data pipeline, owned by business ops. **[Differs: build/buy, match model, ownership, integration depth]**

7. **Create an append-only canonical account ledger instead of merging profiles** — custom but not identity-resolution-centric, event-sourced/federated references, deterministic linkage plus manual exceptions, embedded in write path, owned by engineering platform. **[Differs: data architecture, integration depth, ownership]**

8. **The question is wrong because at 500k profiles and $50k/year, full identity resolution is economically upside-down; define duplicate tolerance bands and only intervene on revenue-critical segments** — selective governance, hybrid tooling, human review for top accounts, minimal automation elsewhere, shared product+sales ownership. **[Differs: ownership, match model, premise, target outcome]**

## Direction: Split operational identity from analytical identity

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| One-system-fits-all thinking | Cross-team conflict over “the right match” | Confidence in customer-facing records where revenue is at risk | Two identity products: operational and analytical |
| Pressure to solve perfect identity globally | Time engineers spend on bespoke weekly scripts | Clarity of ownership by use case | Explicit boundary between merge-for-UI and link-for-analysis |
| Premature custom platform build | Visible duplicate records in sales workflows | Decision speed because each team gets fit-for-purpose tooling | A contract: CRM truth for ops, warehouse entity graph for DS |

## The Argument
The question is wrong because it assumes “identity resolution” is one problem. It is at least two:

1. **Sales needs operational cleanliness**: no embarrassing duplicate records in customer-facing views.
2. **Data science needs analytical linkage**: higher-recall matching, often probabilistic, without necessarily changing source records.

Trying to satisfy both with one system is what creates deadlock. Sales wants conservative merges; data science wants aggressive linking. A single build-or-buy decision forces one confidence model, one owner, and one failure mode onto incompatible jobs.

So the right direction is **dual-track identity**:

- **Buy** a CRM-native or customer-data quality tool for operational dedup in the systems sales touches.
- **Keep/build lightweight probabilistic entity resolution in the warehouse** for analytics only, where linked identities do not automatically merge customer-facing records.

This is structurally different from both prior directions because it does not create a suppression layer and does not ask the product to tolerate ambiguity. It **separates the domains**.

**Why now?**  
What changed is not the duplicate rate; it’s the cost of mixing use cases. Sales is already losing deals, which means operational duplicate pain is now revenue-visible. At the same time, DS is asking for ML-grade matching, which is exactly the kind of requirement that makes operational systems risky. Once both are true at once, a unified identity approach becomes slower, more political, and more expensive than a split system.

**What’s the workaround today?**  
Manual scripts weekly. That is a bad compromise: too slow for sales, too brittle for DS, and owned by nobody. It catches only 60%, meaning you are paying operational and analytical costs simultaneously.

**10x on which axis?**  
**Decision velocity.** This approach gives each team a usable answer fast without waiting for consensus on a mythical perfect matcher.

**Adjacent analogy:**  
Fraud systems often separate **real-time transaction decisions** from **offline risk models**. The online system must be conservative and explainable; the offline model can be more probabilistic and exploratory. Same pattern here.

Budget-wise, this fits the $50k/year reality better than building a full identity platform. Buy the operational layer where vendor products already solve common CRM dedup workflows. Let DS use warehouse-native matching libraries/processes they likely already know, scoped to analytics outputs rather than source-of-truth merges.

## First Move
Run a **one-week decision workshop** with Sales Ops, Product, Engineering, and DS to define two explicit artifacts:

1. **Operational identity policy**: what fields and confidence are required before any customer-facing merge happens in CRM.
2. **Analytical identity policy**: what linkage recall/precision DS needs in the warehouse, independent of CRM merges.

Then evaluate 3 CRM-native dedup vendors against the operational policy using a sample of your known duplicates, while DS tests a warehouse-side matcher on the same sample. The decision signal is whether the same pair gets different treatment in ops vs analytics. If yes — and it almost certainly will — that proves the split architecture is necessary.

## Why This Beats the Alternatives
The obvious approach — “just build” — is wrong at this budget. A real identity system needs data model design, confidence tuning, review workflows, merge semantics, monitoring, and reversibility. That is not a $50k/year problem unless labor is free.

“Just buy” is also wrong if it implies one vendor will satisfy both sales-grade conservatism and DS-grade probabilistic linkage. Most tools are better at one than the other.

Previous directions fail because:
- A **suppression layer** treats the symptom in customer views but leaves the sales/DS conflict unresolved.
- **Designing the product to tolerate ambiguity** may be philosophically elegant, but sales is already losing deals because duplicates are visible now. You need direct operational correction.

This direction beats them by **matching solution type to job type**: conservative bought tooling for operations, flexible analytical matching for DS.

## Biggest Risk
Governance drift: if teams quietly re-import analytical linkages into operational systems, you recreate the same mess under a different name. You need a hard rule that warehouse identity outputs cannot auto-merge customer-facing records.

---

## Synthesis

## The Fork

The real choice is [Bet A: CRM-Native Operational Dedupe] vs [Bet B: Product Tolerates Ambiguity] vs [Bet C: Split Operational and Analytical Identity].

## Bet A: CRM-Native Operational Dedupe
Buy a lightweight CRM-native dedupe tool and make the operational system the matching source of truth for sales-critical objects now. This is the obvious path: fastest time to relief, lowest custom build burden, and best fit for a $50k budget when the pain is visible duplicate records hurting deals. Keep scope narrow: accounts/contacts in the systems reps actually use, deterministic rules first, manual review for exceptions. Own it in RevOps/engineering, not data science. This works if you resist enterprise-MDM ambition and treat it as an operational cleanup product, not universal identity.
**First move:** Pull a labeled sample of known duplicate accounts/contacts, evaluate 3 CRM-native vendors against it, and run a 2-week pilot in the sales workflow.
**Sacrifice:** You give up a unified long-term identity architecture and accept vendor constraints on match logic and extensibility.

## Bet B: Product Tolerates Ambiguity
Don’t solve identity first; redesign the product so duplicates are visible, explainable, and actionable without forced backend merges. Instead of hiding uncertainty, show “possible duplicate” modules in the highest-stakes customer-facing views, with merge/dismiss/assign actions and owner-based review workflow. Use distributed heuristics plus human adjudication. This differs materially from Bet A: custom build, federated matching, human-in-the-loop, and product/sales-ops ownership. It works when the real problem is embarrassment and workflow breakdown, not lack of a perfect golden record. You improve trust fast while avoiding bad auto-merges that are costly to unwind.
**First move:** Add a non-destructive duplicate panel to the top 3 sales views using current script outputs plus a few simple heuristics.
**Sacrifice:** You give up the simplicity of a single clean operational record and accept ongoing ambiguity in the product experience.

## Bet C: Split Operational and Analytical Identity
Accept that sales and data science need different identity systems. Buy conservative operational dedupe for CRM-facing workflows, but keep/build a separate probabilistic entity-resolution process in the warehouse for analytics. This is a hybrid architecture with different confidence models, integration depths, and owners by use case. It works because the conflict is structural: sales needs explainable, high-precision merges; DS needs higher-recall linkage that should not rewrite customer-facing records. Instead of forcing one compromise system, create explicit boundaries and policies between operational identity and analytical identity.
**First move:** Run a one-week policy workshop to define operational merge rules vs analytical linkage rules, then test vendors and warehouse matching on the same duplicate sample.
**Sacrifice:** You give up the dream of one identity system and commit to governing two truths with explicit translation rules.

## Comparison

| | Timeline | Risk | What you learn | Strategic sacrifice |
|---|----------|------|----------------|---------------------|
| **Bet A** | 2–6 weeks to know, based on typical CRM-app pilots and narrow object scope | Vendor setup, rule tuning, and workflow adoption may underperform on messy edge cases | Whether a narrow vendor tool can materially reduce visible sales duplicates within budget | Dependence on vendor model and less flexibility for broader identity strategy |
| **Bet B** | 1–4 weeks to know, since it reuses existing scripts and targets only 3 views | UI/workflow may create confusion or low adjudication follow-through | Whether sales pain is mostly a workflow/visibility problem rather than a backend matching problem | No clean canonical record; ambiguity becomes an explicit product choice |
| **Bet C** | 3–8 weeks to know; operational pilot is fast, but policy and boundary work adds coordination | Governance drift between systems; teams may leak analytical matches into ops | Whether sales and DS truly need different confidence models on the same records | Abandoning a single-system future and taking on permanent dual-system governance |
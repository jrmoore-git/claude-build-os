---
mode: explore
created: 2026-04-10T23:45:40-0700
model: gpt-5.4
directions: 3
prompt_versions: explore=2, diverge=3, synthesis=3
---
# Explore: Should we build or buy an identity resolution system?

## Direction 1

## Brainstorm
1. Buy a lightweight identity resolution vendor and integrate it into the CRM/customer-facing views first, accepting a simpler rules-based core to stop visible duplicate pain fast.
2. Build an internal deterministic dedup service around email, domain, phone, and company-name normalization, embedded in the data pipeline and owned by engineering.
3. Use a hybrid model: vendor for entity matching core, but keep a custom review queue, merge policy layer, and product-specific conflict rules in-house.
4. Don’t solve “identity resolution” broadly at all; create a customer-facing “golden record overlay” that suppresses duplicate display without merging underlying data yet.
5. Create a human-in-the-loop triage system where only high-value or customer-visible records get deduped in near real time, and analytics keeps a separate probabilistic graph.
6. Build a centralized identity graph with probabilistic ML matching owned by data science, and make every downstream system consume it as the source of truth.
7. Go contrarian: stop trying to deduplicate globally and instead define per-use-case identity—sales view identity, analytics identity, support identity—because one canonical truth is the wrong goal.
8. Buy nothing and redesign workflows so duplicate creation is prevented at entry points with aggressive blocking, autocomplete, and “possible match” prompts.
9. Use a federated approach: each system keeps its own records, but a real-time resolution API computes likely matches on demand without mass merges.
10. Outsource the messy middle: combine cheap vendor tooling with an operations-heavy review process run by revops/data stewards, not engineering or data science.

## Direction: Per-use-case identity, not one canonical system

## The Argument
The interesting move is to reject the premise that you need one identity resolution system that satisfies sales, product, engineering, and data science equally. You do not. You need **two outputs**: a **customer-facing suppression layer** for sales now, and an **analytics identity graph** for data science later. That means a **hybrid architecture** with **federated matching**, **human-in-the-loop confidence handling**, **real-time API for customer-facing surfaces**, and **shared product+engineering ownership**.

### 1. Why now?
Two things changed. First, LLM-assisted rule generation and modern matching libraries make it cheap to build the orchestration layer and review tooling without building a full ML identity platform from scratch. Second, the pain has shifted from “bad back-office hygiene” to **revenue loss in customer-facing views**. Two years ago, weekly scripts that caught 60% may have been tolerable. Today, visible duplicates are costing deals, which means latency matters more than theoretical purity. At the same time, data science’s need for probabilistic matching is real—but it’s a different requirement from sales’ need to not embarrass themselves in front of customers.

### 2. What’s the workaround?
Today’s workaround is exactly what the market always does when a problem is real but unsolved: weekly scripts, manual merges, rep tribal knowledge, and analysts building their own fuzzy matching logic in notebooks. That proves demand. It also shows the constraint: nobody trusts a black-box auto-merge enough to let it rewrite production records broadly. So the correct system is not “one engine to merge everything,” but a layered one that **resolves enough for the workflow in front of the user**, while keeping irreversible actions gated.

### 3. Moment of abandonment
People quit the current approach at the moment a sales rep opens an account, sees two or three customer records, and no longer knows which one is safe to use in front of the customer. That is the abandonment point—not batch accuracy, not graph elegance. Design backward from that failure: when a rep views a profile, the system should **collapse likely duplicates into a single display group in real time** with clear confidence and source lineage. No waiting for next week’s script. No forced hard merge. Just “here is the best customer view now.”

### 4. 10x on which axis?
This is **10x better on time-to-visible-correctness**. Not overall sophistication. Not theoretical match quality. The single winning axis is: **how quickly customer-facing duplicates disappear without risky full-data rewrites**. On other axes, it is good enough: analytics can consume a separate probabilistic identity map; engineering avoids a giant platform rewrite; product gets immediate UX improvement. The weakness is lack of one canonical golden record. That does **not** kill adoption because the organization already doesn’t have one—it just pretends it wants one.

### 5. Adjacent analogy
This is how fraud systems evolved in payments. The winning pattern was not “one perfect model decides everything globally.” It was **risk-tiered decisioning**: auto-approve some, auto-decline some, queue the ambiguous middle, and present a safer operational view immediately. The mechanism transfers directly: use deterministic rules for high-confidence suppression, probabilistic scoring for likely matches, and human review for merge-worthy ambiguity. The product surface gets cleaner fast without overcommitting to irreversible data changes.

## First Move
Next week, create a **customer-visible duplicate suppression service** for the sales-facing profile view only. Engineering and product define 5 high-signal match rules: exact email, normalized phone, same domain + similar company name, same external CRM ID, and shared billing address. Wrap them in a confidence score with 3 bands: auto-group in UI, suggest to user, send to review queue. Do **not** hard-merge records yet. Measure one thing: reduction in duplicate profiles shown to sales within 30 days.

## Why This Beats the Alternatives
**Buying a full vendor platform** is the obvious answer, but at $50k/year you’ll get either limited capability or a tool that still requires painful integration and governance. Worse, vendors optimize for canonical identity, which is not your immediate failure mode.

**Building a full internal ML identity graph** is intellectually attractive to data science and operationally wrong. It is too slow, too expensive, and too easy to stall on training data, evaluation, and ownership fights.

**Improving the weekly scripts** is insufficient because the problem is no longer recall in batch—it is customer-facing latency and trust at the moment of use.

## Biggest Risk
The biggest risk is organizational, not technical: teams may reject a split model because it feels “impure” to have sales identity and analytics identity differ. If leadership insists on one canonical truth before shipping any improvement, this dies in committee and you keep losing deals to duplicate records.

---

## Direction 2

## Brainstorm
- **Buy vendor core + embed a real-time “golden record” API in the product path** — [hybrid, centralized graph, probabilistic ML, real-time API, shared product+eng]
- **Build a lightweight deterministic merge service inside the data pipeline only** — [build, distributed matching, deterministic rules, embedded pipeline, engineering-owned]
- **Buy a CDP/MDM-lite and keep product-facing records separate from analytics identity** — [buy, federated approach, vendor probabilistic, standalone + batch sync, product ops-owned]
- **Create a human-in-the-loop review queue for only high-value account conflicts, automate the rest with simple rules** — [hybrid, federated, human-in-the-loop, embedded CRM workflow, sales ops-owned]
- **Contrarian: don’t solve universal identity; solve “customer-facing duplicate suppression” at read time** — [build, federated/read-time overlay, deterministic + confidence threshold, real-time API, product engineering-owned]
- **Contrarian: outsource matching entirely to a managed enrichment/identity vendor and treat internal systems as consumers** — [buy, externalized centralized graph, vendor ML, standalone service, rev ops-owned]
- **Build a feature store + ML matcher for analytics, but buy a separate operational dedup tool for CRM/product surfaces** — [hybrid, split architecture, probabilistic ML + deterministic ops rules, pipeline + workflow, shared DS+eng]
- **Adopt an event-driven identity broker that never hard-merges records, only emits linkage assertions with confidence** — [build, federated link graph, probabilistic + human escalation, real-time/event-driven, platform team-owned]

## Direction: Buy vendor core, keep a custom linkage layer, and stop hard-merging everything

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| Universal hard-merge as the default answer | Internal custom matching logic and weekly script maintenance | Real-time confidence-scored identity decisions in customer-facing views | A dual-speed identity system: vendor-backed entity resolution for ops, custom link-confidence layer for product and analytics consumers |
| One canonical identity model for every team | Manual record review on low-value duplicates | Team-specific consumption of identity: sales, product, DS each get fit-for-purpose outputs | “Link, don’t prematurely merge” as an operating model |
| Batch-only dedup as the control point | Scope of v1 to the 20% of duplicates causing 80% of visible pain | Observability: precision/recall, false merge tracking, and confidence thresholds | A reversible identity graph instead of irreversible cleanup scripts |

## The Argument
**Buy the matching engine, build the control plane.** That is the right answer here.

A full build is the obvious technical temptation, especially because data science wants ML. It is wrong for this company right now. At 500k profiles and a $50k/year budget, you do not need to invent entity resolution; you need duplicate pain to stop showing up in front of customers and sales. Vendor identity resolution is now cheap enough and mature enough to handle the hard part—candidate generation, fuzzy matching, survivorship options, and operational workflows—without a year-long internal platform project.

But buying an all-in-one “single customer truth” is also wrong. Product, engineering, and data science do **not** need the same identity object. Forcing one canonical merge model creates political deadlock and bad data decisions. So the winning structure is: **buy a vendor core for probabilistic matching, then build a thin internal linkage layer that exposes confidence-scored links instead of aggressively hard-merging records everywhere.**

**Why now?**  
Two things changed: first, duplicate visibility is now a revenue problem, not a data hygiene problem. Sales is losing deals. Second, modern identity tools can be stood up fast enough that the opportunity cost of building from scratch is unjustifiable. The old weekly script was acceptable when duplicates were an internal nuisance. It is no longer acceptable when they leak into customer-facing views.

**What’s the workaround?**  
What people do without this is exactly what you are doing now: weekly dedup scripts, ad hoc SQL, manual merges in CRM, and local team-specific exceptions. That catches some duplicates but creates inconsistency, lag, and irreversible bad merges. Data science then rebuilds identity logic downstream anyway.

**10x on which axis?**  
**Time-to-reliable-resolution in customer-facing workflows.** Not model elegance. Not theoretical accuracy. The win is reducing duplicate exposure from weekly correction to near-real-time suppression and linkage.

**Adjacent analogy:**  
This is how fraud/risk systems evolved. Companies stopped building every scoring primitive themselves and instead bought core detection capability, then built custom policy layers on top for their business context. Identity resolution should follow the same pattern here.

## First Move
In the next 2 weeks, run a **30-day vendor bake-off** with 2 MDM/entity-resolution vendors that fit inside budget, using a labeled sample of 10k profiles and 500 known duplicate/non-duplicate pairs from sales pain cases.

Scope the pilot narrowly:
1. Measure precision/recall on visible duplicate cases.
2. Stand up one **read-time duplicate suppression API** for the customer-facing view.
3. Do **not** allow automatic hard merges in source systems yet.
4. Expose confidence bands: auto-link, review, ignore.

This immediately affects sales and product: customer-facing duplicate records stop appearing before the broader identity debate is settled.

## Why This Beats the Alternatives
**Against build-from-scratch ML:** too slow, too political, and too expensive in hidden labor. You will spend months on training data, features, threshold fights, and ops. Meanwhile sales keeps losing deals.

**Against buying a full canonical MDM rollout:** too heavy, too rigid, and guaranteed to trigger cross-team conflict about ownership and truth definitions. It solves governance before it solves visible pain.

**Against deterministic rules only:** better than today, but it will plateau fast and fail on the fuzzy edge cases data science cares about.

**Against human-review-first systems:** useful as a safety valve, but not sufficient. The volume is too high and customer-facing lag still exists.

**Against the previous direction of per-use-case identity only:** this is structurally different because it uses a **vendor probabilistic core**, a **central link graph**, and a **real-time API layer** under **shared product+engineering ownership** rather than a fragmented identity model.

## Biggest Risk
The biggest risk is **organizational misuse of confidence scores**—teams will pressure the system into automatic hard merges too early. If that happens, a good linkage system turns into another brittle source-of-truth fight. Keep v1 reversible: link first, merge later.

---

## Direction 3

## Brainstorm
1. **Truth-at-read overlay** — build a lightweight real-time resolution API that leaves source records untouched and computes a canonical display identity on demand; **[Build, distributed overlay, probabilistic+rules, real-time API, shared product+eng]**
2. **Steward queue first** — build a human-in-the-loop adjudication service where model-generated candidate pairs are resolved daily by ops/sales owners, with product consuming only approved merges; **[Build, centralized review store, human-in-the-loop, embedded workflow tool, business ops ownership]**
3. **Feature-flagged customer-view dedup only** — do not solve enterprise identity broadly; ship a narrow UI-layer duplicate suppression system for sales-facing views and leave analytics separate for now; **[Build, presentation-layer federation, deterministic, embedded in app UI, product ownership]**
4. **Reverse ETL identity spine** — resolve identity in the warehouse only, publish golden IDs outward to apps via reverse ETL, and stop trying to dedup operational systems directly; **[Hybrid-build on warehouse stack, centralized warehouse model, probabilistic ML, embedded in data pipeline, data science ownership]**
5. **Event-sourced identity decisions ledger** — create an append-only decision log of “same/not same” assertions from systems and humans, and derive identities from those assertions instead of hard merges; **[Build, federated ledger, human+probabilistic, standalone service, platform engineering ownership]**
6. **Open-source MDM stack with services wrapper** — adopt an open-source entity resolution tool, self-host it, and wrap it with product-specific APIs and review workflows; **[Buy-ish/open source, centralized graph, probabilistic ML, standalone+batch, engineering ownership]**
7. **Contrarian: stop deduping records, dedupe experiences** — leave duplicates in CRM/db, but add account-level grouping and conflict-aware actions so sales never experiences dupes even if records persist underneath; **[Build, no central identity layer, deterministic grouping, embedded application behavior, product team ownership]**
8. **Contrarian: paid cleanup sprint, not system** — run a 90-day intensive one-time cleanup plus prevention rules at write-time, explicitly avoiding a general identity platform; **[Service/process, minimal architecture, deterministic+manual, write-path validation, rev ops ownership]**

## Direction: Reverse ETL identity spine

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| Direct record merges across every operational system | Weekly manual dedup scripting and bespoke one-off cleanup jobs | Warehouse-native matching quality, observability, and publish cadence | A single “golden ID spine” pushed into customer-facing tools without replacing those tools |

## The Argument
You should **build a warehouse-native identity spine and publish golden IDs back into downstream systems via reverse ETL**.

This is structurally different from both “one canonical identity system” and “buy vendor core plus linkage.” It does **not** create a central operational MDM, and it does **not** depend on a vendor’s identity engine as the center of gravity. Instead, identity resolution becomes a **data product in the warehouse**, where your data science team can actually iterate on matching quality, and engineering only has to consume a stable `golden_profile_id`.

Why now? Two things changed. First, the pain is now customer-visible: sales is losing deals because duplicates appear in live views. Second, the scale is finally enough to justify a formal matching pipeline: **500k profiles × 15% duplicate rate = ~75k bad records**. Weekly scripts catching 60% means tens of thousands of dupes still leak through. At this size, ad hoc fixes are more expensive than a repeatable spine.

What’s the workaround today? People are doing exactly what immature identity stacks always do: scripts, one-off SQL, manual merges, and arguing over edge cases. Product wants clean UX, engineering wants low-risk systems, and data science wants probabilistic matching. The warehouse spine is the first approach that gives each group what it needs without forcing one runtime architecture on everyone.

10x on which axis? **Time-to-visible-cleanliness in customer-facing tools.** Not theoretical identity purity. You can get from weekly cleanup to **daily or intra-day golden ID publishing** without replatforming CRM/app databases.

Adjacent analogy: This is how the modern metrics layer won over embedded reporting logic. Instead of hard-coding definitions in every app, teams centralized the logic in the warehouse/semantic layer and pushed consistent outputs everywhere. Identity can work the same way: centralize the logic, distribute the result.

How it works:
- Build matching in the warehouse using deterministic blocking + probabilistic scoring.
- Output clusters with a stable `golden_profile_id`, confidence score, and “survivorship” attributes.
- Push that ID and preferred display record into CRM/app tables through reverse ETL or direct sync.
- Customer-facing views use the golden ID grouping immediately.
- High-uncertainty pairs go to a small review queue, but only for the long tail.

This fits the budget. A vendor identity platform that solves both ops and analytics well will likely strain $50k/year. A warehouse-native pipeline with a modest review tool and reverse ETL is feasible inside that budget, especially if you already have dbt/warehouse infrastructure.

## First Move
In the next 2 weeks, **stand up a dedicated `identity_resolution` schema in the warehouse** owned by a **shared product+engineering lead with data science implementing match logic**. Start with the 3 fields most predictive for your domain—email, company/domain, and normalized name/phone—and produce a first `golden_profile_id` table for the sales-facing profile view only. Then wire one downstream surface to consume it: the customer-facing record list where duplicates are currently visible.

## Why This Beats the Alternatives
The obvious “buy an identity system” answer fails your constraints. At $50k/year, you will end up with a tool that either does analytics identity well but is weak operationally, or cleans CRM data but is opaque to data science. You’ll also inherit integration work anyway.

A fully custom canonical identity platform is too much. It creates operational blast radius, requires migration politics across teams, and solves more than you need right now.

The previous directions also miss the mark:
- **Per-use-case identity** institutionalizes disagreement. It accepts fragmentation when your immediate problem is visible inconsistency.
- **Buy vendor core + custom linkage** still makes the vendor the center and leaves you paying for a black box while building all the hard connective tissue yourself.

The warehouse spine is better because it **solves the sales visibility problem fast**, gives **data science control over match quality**, and minimizes operational risk by **publishing IDs instead of forcing hard merges**.

## Biggest Risk
The biggest risk is **downstream teams refusing to trust and adopt the golden ID in product surfaces**. If engineering keeps rendering raw source records, or sales ops keeps manually merging against different logic, the spine becomes “just another table.” The project lives or dies on one thing: making `golden_profile_id` the default join key and display grouping in the first high-value customer-facing workflow.

---

## Synthesis

## The Fork

The real choice is [Bet A: Customer-View Suppression Overlay] vs [Bet B: Vendor Core + Custom Linkage Layer] vs [Bet C: Warehouse Identity Spine].

## Bet A: Customer-View Suppression Overlay
Build the obvious fix: stop visible duplicate pain in sales first, without trying to create one canonical customer record. Use deterministic rules plus confidence bands to group likely duplicates at read time in the customer-facing view, leaving source systems untouched. This differs by being a custom build, federated/read-time architecture, deterministic-first confidence model, embedded in the app surface, and product+engineering owned. It works because your acute failure is not global identity quality; it is reps seeing duplicate profiles during live workflows. By keeping it reversible, you avoid source-of-truth fights and bad merges while improving customer-facing correctness fast.
**First move:** Ship a sales-profile duplicate suppression service using 5 high-signal match rules and 3 confidence bands; measure duplicate exposure reduction in 30 days.
**Sacrifice:** You give up a near-term canonical identity layer and accept that analytics and ops may use different identity logic for a while.

## Bet B: Vendor Core + Custom Linkage Layer
Buy the matching engine, but do not buy the operating model. Use a vendor’s probabilistic entity-resolution core for candidate generation and scoring, then build a thin internal layer that exposes confidence-scored links, review workflows, and product-specific policies. This is a hybrid path with a centralized link graph, probabilistic ML core, real-time API, and shared product+engineering ownership. It works because vendor tools can end weekly-script pain faster than an internal ML build, while your custom layer prevents premature hard merges and lets each team consume identity differently. This is the best balance if you want speed plus stronger long-term matching quality.
**First move:** Run a 30-day bake-off with two vendors on 10k records and 500 labeled pairs; wire the winner into one customer-facing suppression API.
**Sacrifice:** You give up full control of the matching core and become partially dependent on vendor economics, roadmap, and model transparency.

## Bet C: Warehouse Identity Spine
Make identity a warehouse-native data product. Build deterministic blocking plus probabilistic scoring in the warehouse, output a stable `golden_profile_id`, and publish that ID back into CRM and product surfaces via reverse ETL. This is a build-heavy approach with centralized warehouse architecture, probabilistic matching, pipeline-embedded integration, and data science-led ownership. It works if you want a reusable identity foundation that serves analytics and can still clean customer-facing views without operational hard merges. Rather than computing identity in the product path or outsourcing the core, you centralize logic where data science can iterate and downstream systems just consume the result.
**First move:** Create an `identity_resolution` schema, generate a first `golden_profile_id` table from email/domain/name-phone signals, and feed one sales-facing list view.
**Sacrifice:** You give up fastest time-to-relief and accept slower operational feedback loops than a read-time overlay or vendor-backed real-time service.

## Comparison

| | Timeline | Risk | What you learn | Strategic sacrifice |
|---|----------|------|----------------|---------------------|
| **Bet A** | 2–6 weeks to know if visible duplicate pain drops | Rule quality may plateau; UI grouping may miss fuzzy cases or confuse users | Whether customer-facing suppression alone solves the revenue pain without deeper identity infrastructure | You postpone a shared identity foundation and normalize split identities across teams |
| **Bet B** | 4–8 weeks to validate via vendor pilot and first API | Integration friction, poor vendor fit, or pressure to auto-merge too early | Whether vendor ML materially outperforms rules on your messy duplicate set at acceptable cost | You cede core matching leverage to a vendor and narrow future architectural independence |
| **Bet C** | 6–12 weeks to prove adoption in one downstream workflow | Slow stakeholder adoption; warehouse outputs may not make it into live product behavior | Whether a warehouse-owned golden ID can become the default join/display key across teams | You commit identity gravity toward data science and away from product-path real-time control |
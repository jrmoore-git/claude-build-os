---
mode: explore
created: 2026-04-10T23:52:52-0700
model: gpt-5.4
directions: 3
prompt_versions: explore=3, diverge=4, synthesis=3
---
# Explore: Should we build or buy an identity resolution system?

## Direction 1

## Brainstorm
- Buy a lightweight identity-resolution vendor and use it as the system of record for matching, with engineering only handling integrations.
- Build a rules-based dedup service in-house focused on obvious duplicates and real-time prevention at profile creation/edit time.
- Do a hybrid: vendor for offline probabilistic matching, but keep customer-facing merge decisions and UI suppression logic in your own product layer.
- Ignore “identity resolution” as a platform problem and instead solve the sales problem first by adding a customer-facing canonicalization layer that hides duplicates without fully merging them.
- Create a human-in-the-loop matching queue where uncertain cases go to sales ops, optimizing for trust rather than automation.
- Build a centralized entity graph owned by data science, then expose resolved identities downstream to product and sales systems.
- Use no dedicated system at all: redesign workflows so duplicate creation is acceptable, then reconcile only at account/opportunity milestones.
- Take a contrarian path: stop trying to maximize recall and instead aggressively optimize precision, merging far fewer records but eliminating the embarrassing visible duplicates that cost revenue.
- Buy a CDP-style tool even if it’s unfashionable for this use case, using its identity stitching engine as the core and ignoring most of the rest.
- Reframe the question entirely: the real issue is organizational ownership, so create a shared “customer identity contract” and only then choose minimal tooling.

## Direction: Hide First, Resolve Second — hybrid canonicalization layer over a vendor core

## The Argument
You should not start by building a full identity resolution system, and you should not buy a giant vendor platform either. The right move is a **hybrid**: buy a low-cost vendor or OSS-backed probabilistic matching core for batch candidate generation, then build a **thin canonicalization layer** in your own product that suppresses visible duplicates in customer-facing views and controls merges with explicit confidence thresholds.

This is the most interesting direction because it reframes the problem correctly: you do not have one duplicate problem, you have **two different jobs** pretending to be one.

1. **Sales/product job:** never show embarrassing duplicate records in front of customers.  
2. **Data science job:** improve identity stitching for analytics, where probabilistic ambiguity is acceptable.

Those jobs require different tolerances. Sales needs high precision and immediate suppression. Data science wants higher recall and can tolerate uncertainty. One system can support both, but not with one policy.

### Why now?
Two things changed versus two years ago:

- **Matching quality is now cheap enough**: vendor APIs and modern open-source/entity-resolution tooling can generate decent probabilistic match candidates without a six-figure contract or dedicated ML team.
- **The pain is now visible in-product, not just in the warehouse**: sales is losing deals because duplicates appear in customer-facing views. Once bad identity leaks into live product experiences, weekly cleanup is no longer acceptable.

The old world tolerated back-office dedup. Today the issue has moved to revenue-critical surfaces.

### What’s the workaround?
People already prove demand through ugly workarounds:
- weekly scripts catching only ~60%
- sales reps manually searching multiple profiles before calls
- internal “don’t merge unless certain” habits
- analysts building one-off stitched datasets separate from production records

Those are classic signs that the need is real but trust in full automation is low.

### Moment of abandonment
People abandon the current approach at the exact point where a probable duplicate becomes a **customer-visible contradiction**: a rep opens an account and sees two profiles for the same person/company, or a customer sees inconsistent history tied to different records.

That is the failure point to design backward from. Don’t start with “perfect entity resolution.” Start with “never embarrass us in front of the customer.”

### 10x on which axis?
This is 10x better on **time-to-visible-improvement**.

A full build takes months and still won’t settle team disagreements. A full buy creates integration debt and pushes you into someone else’s ontology. A hybrid can reduce visible duplicates in key views within weeks, while still improving analytics over time.

### Adjacent analogy
This is how fraud systems evolved: the winning pattern was not “fully automate all fraud decisions,” it was **score centrally, enforce locally**. A risk engine generates probabilities; the product applies different thresholds for approval, review, or block based on context. Identity resolution should work the same way: one matching core, different actions by use case.

### Concrete design
Make at least three dimensions meaningfully different from the obvious options:

- **Build vs buy vs hybrid:** vendor/OSS core + custom product layer
- **Data architecture:** federated/canonicalization layer, not one giant centralized graph first
- **Match confidence model:** probabilistic candidate generation plus human-reviewed merge band
- **Integration depth:** embedded in customer-facing read paths for suppression, plus batch pipeline for analytics
- **Ownership:** shared product + engineering ownership, not data science alone

Use three confidence bands:
- **High confidence:** auto-link for display suppression
- **Medium confidence:** queue for ops review
- **Low confidence:** leave separate, but expose as candidates to analytics

Crucially, **linking for display is not the same as destructive merge**. That distinction is what makes this workable on your budget and timeline.

## First Move
Next week, pick the **two customer-facing screens** where duplicate visibility costs revenue most. Engineering adds a simple canonical-profile read layer in front of those views. In parallel, run a 30-day trial with a low-cost vendor or OSS matcher on the 500k profiles to generate duplicate candidate pairs with confidence scores. Set a strict threshold for display suppression only; do not bulk-merge records yet. Product and sales ops review the top 500 medium-confidence cases to calibrate thresholds.

## Why This Beats the Alternatives
**Full in-house build:** too slow, politically contentious, and likely to collapse into endless debate over matching logic before helping sales.

**Full vendor purchase:** your budget is too small for a robust enterprise-grade solution, and vendors will optimize for generic identity graphs, not the exact customer-facing suppression logic your product needs.

**Rules-only in-house dedup:** obvious and cheap, but you already know the ceiling—your weekly scripts catch ~60%, and rules systems degrade badly on edge cases and evolving data.

## Biggest Risk
The biggest risk is **organizational ambiguity**: if you do not explicitly separate “display linking,” “true merge,” and “analytics stitching,” teams will fight over one threshold and one definition of identity. That kills momentum. The solution works only if you treat identity resolution as a multi-policy system, not a single yes/no decision.

---

## Direction 2

## Brainstorm
1. **Don’t do identity resolution; do record presentation suppression at read-time** — the question is wrong because the acute problem is duplicate *visibility*, not entity truth. Build a lightweight UI/API merge-overlay, leave source records intact. **[Differs: custom build, real-time API, engineering ownership, deterministic]**
2. **Split the problem: buy a CRM-native duplicate prevention tool, not a cross-system resolution platform** — the question is wrong because you’re treating prevention and historical cleanup as one purchase. Use vendor rules where records are created and stop new dupes first. **[Differs: buy, embedded in operational system, engineering+ops ownership, deterministic]**
3. **Create a “golden segment” only for revenue-critical accounts** — the question is wrong because resolving all 500k profiles equally is wasteful. Build a human-assisted workflow for top accounts only. **[Differs: custom, human-in-the-loop, distributed scope, product+sales ownership]**
4. **Federated stewardship model: each system keeps identity, central service only stores conflict signals** — don’t centralize entities at all; route likely-collision alerts back to system owners. **[Differs: custom, federated architecture, standalone alerting, shared ownership]**
5. **Analytics-only probabilistic identity graph in the warehouse** — the question is wrong because data science and sales need different truths. Buy/build only for analytical unification; leave operational CRM untouched. **[Differs: custom or buy-light, centralized warehouse graph, probabilistic ML, data science ownership]**
6. **Outsource duplicate operations to a BPO + review tooling** — uncomfortable option: don’t automate matching; buy labor and a queue. **[Differs: buy-service, human-in-the-loop, standalone ops workflow, ops ownership]**
7. **Delete and re-key the workflow, not the data** — uncomfortable option: redesign customer-facing views and sales process around account-level objects so profile duplication matters less. **[Differs: product redesign, no central resolution, embedded workflow change, product ownership]**

## Direction: Fix Duplicate Visibility, Not Identity Resolution

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| urgency to unify every profile everywhere | dependence on weekly manual cleanup | confidence in customer-facing views | a read-time “same customer” overlay service |
| premature ML ambitions | duplicate exposure to sales reps | speed of remediation | a queue for only ambiguous merges |

## The Argument
The question is wrong because it assumes you need an identity resolution system to solve the business problem. You don’t. Your most expensive pain is visible duplicates causing lost deals. That is a presentation-layer problem first, master-data problem second.

Three ways the question is wrong because:
1. **The question is wrong because it treats sales pain and analytics accuracy as one system decision.** They need different outputs: sales needs one clean view now; data science needs probabilistic clustering later.
2. **The question is wrong because it assumes record-level truth must be fixed before user experience improves.** A read-time suppression layer can hide obvious dupes immediately without risky source merges.
3. **The question is wrong because it frames the decision as build vs buy for a broad platform, when your budget and scale point to a narrower intervention.** $50k/yr is tight for a serious cross-system vendor and too small for a robust bespoke resolution platform with ongoing tuning.

So the right move is: **build a narrow duplicate-overlay service** that groups records for customer-facing views using high-precision rules, while leaving source systems untouched. Think “linked display identities,” not “canonical master record.”

Why now?  
Because your current weekly scripts catch only ~60%, and the cost is visible revenue loss. Also, this is now feasible because 500k profiles is small enough for a straightforward candidate-generation and rules service run by engineering without buying enterprise MDM. The business case exists because sales is already feeling the failure.

What’s the workaround today?  
Manual scripts, ad hoc rep judgment, and probably selecting “the least wrong” record in front of customers. That’s fragile and slow.

10x axis: **time-to-visible-cleanliness.** Not perfect identity accuracy.

Adjacent analogy:  
Email clients solved “conversation view” before perfect message normalization. E-commerce sites collapse duplicate listings in the UI before fixing catalog internals. Presentation unification often beats source-of-truth unification.

Concretely: compute likely duplicate clusters using strict deterministic signals only—exact email, normalized domain + company name, phone, strong account identifiers. Expose a service that customer-facing views call to show one primary record plus “3 related records hidden.” Add a small review queue only for records that hit medium-confidence rules and affect active pipeline.

This avoids the trap of overbuilding ML for an operational problem. Data science can still build a separate warehouse identity model later if needed.

## First Move
Instrument where duplicates are costing deals: pick the customer-facing sales view with the highest usage, then export 200 known duplicate examples from recent lost/opposed deals. Engineering and sales ops spend one working session defining **five high-precision suppression rules** and the UI behavior for collapsed records. Then implement the overlay on that one view.

This first move matters because it answers the only decision that counts: can you materially reduce duplicate exposure without touching source data?

## Why This Beats the Alternatives
**Buying a full identity resolution platform:** overkill, likely over budget, and still requires integration, rule tuning, and governance you don’t currently have. You’ll pay to solve a broader problem than the one hurting you.

**Building a full identity system:** wrong sequencing. You’ll disappear into schema debates, survivorship logic, and merge semantics across teams with conflicting goals.

**Previous direction (vendor core + custom canonicalization):** still accepts the premise that a central resolution layer is necessary. It adds architecture before proving that customer-visible duplication is the real leverage point.

This direction wins because it narrows scope to the business failure, uses engineering muscle you already have, and separates operational UX cleanup from analytical identity science.

## Biggest Risk
The biggest risk is **false positives collapsing records that should remain distinct**, which can erode sales trust fast. That’s why this only works if you optimize for precision over recall and start with display suppression, not destructive merges.

---

## Direction 3

## Brainstorm
1. **Don’t build or buy identity resolution; split the problem into UI record-linking + analytics entity modeling** — the question is wrong because one “system” cannot serve sales UX and DS truth simultaneously. **[Differs: build/buy = neither single system; architecture = dual-track/federated; confidence = deterministic for UI + probabilistic for analytics; ownership = split product+eng and DS]**
2. **Make source systems authoritative and push dedup upstream via workflow gates** — the question is wrong because duplicates are being created operationally, not merely detected later. **[Differs: build/buy = process/tooling, not resolution platform; architecture = federated at source; integration = embedded in operational workflows; ownership = RevOps + product ops]**
3. **Adopt “linked identities, not merged identities” as the product model** — the question is wrong because hard resolution assumes a single golden record is necessary. **[Differs: architecture = relationship graph/federated references, not canonical record; confidence = human-in-the-loop review for merge authority; integration = app-level model change; ownership = shared product+eng]**
4. **Use a BPO/manual adjudication queue with lightweight scoring, not a system purchase** — the question is wrong because at 500k profiles and 15% dupes, the binding constraint may be review capacity, not matching tech. **[Differs: build/buy = operational service; confidence = human-in-the-loop; integration = standalone queue; ownership = ops team]**
5. **Freeze merge ambitions and redesign customer-facing views to collapse likely duplicates at read time only** — the question is wrong because the urgent pain is visible duplicates, not enterprise-wide identity truth. **[Differs: build/buy = no platform; integration = real-time presentation layer; architecture = no centralized resolver; ownership = product+frontend eng]**
6. **Use warehouse-native entity resolution for analytics only, and explicitly leave product untouched** — the question is wrong because “identity resolution” is being overloaded by DS requirements. **[Differs: build/buy = buy SQL/package or build in warehouse; architecture = analytics-local; integration = data pipeline only; ownership = data science/data eng]**
7. **Kill the premise and measure duplicate cost first; maybe do nothing but targeted account cleanup** — the question is wrong because “15% duplicates” is not the same as 15% business harm. **[Differs: build/buy = neither initially; confidence = no global matcher; ownership = finance/product; integration = none]**
8. **Replace profile-centric architecture with account/contact interaction timelines where identity ambiguity is tolerated** — the question is wrong because the product may be over-dependent on precise person-level identity. **[Differs: architecture = model redesign; integration = core product; ownership = product strategy; outcome target = ambiguity-tolerant UX]**

## Direction: Split the problem: no single identity resolution system

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| Search for one “golden” solution | Scope conflict between sales and DS | Speed of visible duplicate suppression | Two fit-for-purpose identity layers |
| Premature vendor evals | Risk of bad global merges | Clarity of ownership | UI link model + warehouse entity model |
| Endless matching debates | Dependence on weekly scripts | Decision quality by use case | Explicit policy for when identities can merge |

## The Argument
You should **not** ask “build or buy an identity resolution system.” The question is wrong because:

1. **The question is wrong because sales and data science do not need the same thing.** Sales needs duplicate suppression in customer-facing views now. Data science needs stable entity modeling for analytics. One system trying to satisfy both under a $50k budget will do neither well.

2. **The question is wrong because your urgent problem is presentation, not ontology.** Sales is losing deals from visible duplicate records. That can be fixed without solving enterprise identity in full.

3. **The question is wrong because a single global resolver creates the most dangerous failure mode: bad merges.** False positives hurt sales, support, and reporting more than leaving some duplicates unmerged.

So the right direction is **two-track identity handling**:

- **Track A: product-facing linked-record suppression**
  - Deterministic rules plus lightweight review.
  - No hard merge required.
  - At read time, customer-facing views collapse obviously related records into one display group.
  - Owned by product + engineering.

- **Track B: analytics-facing entity model in the warehouse**
  - Probabilistic matching is allowed because it does not rewrite operational records.
  - DS gets confidence scores, versioned entity tables, and can tune precision/recall.
  - Owned by DS + data engineering.

**Why now?**  
Two things changed: the pain is now revenue-visible, and modern warehouse tooling makes analytics entity modeling cheap enough without buying a full MDM platform. Also, your current weekly scripts already prove there is enough signal to act; they just act too late and too globally.

**What’s the workaround today?**  
Weekly manual scripts, sales reps manually spotting duplicates, and DS compensating downstream with ad hoc joins. That is exactly why each team thinks the answer should optimize for them.

**10x axis:** **time-to-value for the sales pain.**  
You can materially reduce visible duplicates fast because UI suppression does not require fully trusted identity resolution.

**Adjacent analogy:**  
Email clients solved this with **threading before truth**. They did not first build perfect identity for every sender; they grouped what users needed to see coherently. Analytics later can use richer models.

Timeline: a UI-layer linked-record approach can often be implemented quickly if you control the read path and have basic stable identifiers like email/domain/name. The exact timeline depends on **where customer-facing views are rendered and whether search/indexing must change**. The warehouse entity model depends on **data cleanliness and available join keys**.

## First Move
In the next 2 weeks, create a **duplicate decision matrix** with 100 sampled duplicate pairs from actual customer-facing views:

- Product and sales mark: “must collapse in UI,” “must remain separate,” or “unclear.”
- DS marks: “same entity for analytics,” confidence, and required signals.
- Engineering records which attributes are available in real time vs only in warehouse.

This forces one concrete outcome: a **policy split** between operational suppression and analytical resolution. Then implement the first product rule: **collapse records in customer-facing views when exact email match OR exact domain + company name match**, showing one primary card with linked alternates. No destructive merge.

## Why This Beats the Alternatives
**What’s wrong with the obvious approaches:**

- **Pure buy:** decent vendors will exceed your effective budget once implementation and integration are real, and they still will not reconcile sales UX urgency with DS’s probabilistic needs.
- **Pure build:** engineering will sink time into generalized resolution infrastructure when the immediate issue is visible duplicates.
- **One-model-for-all:** this creates governance fights and bad compromises on precision vs recall.

**What’s wrong with the previous directions:**

- **“Hide First, Resolve Second”** was still a hybrid canonicalization path over a vendor core. That accepts the premise that there should be one resolution backbone. I reject that premise.
- **“Fix Duplicate Visibility, Not Identity Resolution”** focused on the symptom in product views. That helps sales, but it strands DS. My direction explicitly separates and serves both use cases with different systems and owners.

## Biggest Risk
The biggest risk is **organizational refusal to accept two truths**: one identity treatment for product, another for analytics. If leadership insists on a single golden record, this direction dies—not for technical reasons, but because the company wants conceptual simplicity more than business results.

---

## Synthesis

## The Fork

The real choice is **Bet A: Hide First, Resolve Second** vs **Bet B: Visibility Overlay Only** vs **Bet C: Two-Track Identity Split**.

## Bet A: Hide First, Resolve Second
Buy a lightweight vendor or OSS matcher for offline probabilistic candidate generation, then build your own thin canonicalization layer to suppress visible duplicates and control merges with confidence bands. This works because it separates three actions that teams wrongly collapse into one: display linking, destructive merge, and analytics stitching. You get faster customer-facing improvement than a full in-house build, but keep product-specific logic a generic vendor will not handle well. It differs by being hybrid, federated, probabilistic with review, embedded in product read paths plus batch, and shared between product and engineering.
**First move:** Trial one low-cost matcher on the 500k profiles, then add a canonical-profile read layer to the two customer-facing screens where duplicate visibility costs revenue most.
**Sacrifice:** You give up the simplicity of one system and one policy; this path introduces governance complexity early.

## Bet B: Visibility Overlay Only
Do not build or buy identity resolution. Build a narrow read-time overlay service that collapses obvious duplicates only in customer-facing views using strict deterministic rules, while leaving source records untouched. This works because the acute business pain is duplicate visibility, not enterprise identity truth. With 500k profiles, engineering can implement high-precision suppression quickly and avoid risky false merges. It differs by being custom-built, no centralized graph, deterministic, real-time API/presentation-layer, and engineering-owned. You optimize for precision and time-to-visible-cleanliness, not recall.
**First move:** Pull 200 recent duplicate examples from the highest-value sales view, define five high-precision suppression rules with sales ops, and ship the overlay on that one screen.
**Sacrifice:** You give up a path to broad cross-system identity resolution; analytics and downstream systems remain fragmented.

## Bet C: Two-Track Identity Split
Reject the idea of one identity system. Build two fit-for-purpose layers: a product-facing linked-record suppression model owned by product+engineering, and a warehouse entity model owned by data science for probabilistic analytics stitching. This works because sales and DS need different truths, different confidence thresholds, and different failure modes. Operational views get deterministic or lightly reviewed links without destructive merges; analytics gets versioned probabilistic entities without rewriting source systems. It differs by using neither one platform nor one owner, a dual/federated architecture, mixed confidence models, pipeline-plus-product integration, and split ownership.
**First move:** Run a 100-pair duplicate decision workshop across sales, product, DS, and engineering to define which pairs must collapse in UI versus only unify in analytics.
**Sacrifice:** You give up the “golden record” story and accept permanent conceptual complexity across teams.

## Comparison

| | Timeline | Risk | What you learn | Strategic sacrifice |
|---|----------|------|----------------|---------------------|
| **Bet A** | 4–8 weeks to test on key views; grounded by vendor trial + thin read-layer integration on 500k profiles | Threshold confusion and policy sprawl across display, merge, and analytics | Whether vendor-grade matching is good enough to power customer-facing suppression without bulk merges | A single clean system story; you commit to hybrid governance |
| **Bet B** | 2–4 weeks for one high-usage screen; grounded by narrow UI/API scope and deterministic rules | False positives in collapsed views could erode sales trust fast | Whether most revenue pain is solved by presentation cleanup alone | Broad identity-platform optionality; downstream fragmentation remains |
| **Bet C** | 3–6 weeks to define policy split and ship first UI rules; analytics model timeline unknown — depends on warehouse data quality and join keys | Org misalignment: teams may reject two definitions of identity | Whether sales and DS truly need separate identity treatments and ownership | The golden-record strategy; you choose enduring dual systems over conceptual simplicity |
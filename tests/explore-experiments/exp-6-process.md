---
mode: explore
created: 2026-04-10T23:43:51-0700
model: gpt-5.4
directions: 3
prompt_versions: explore=2, diverge=3, synthesis=3
---
# Explore: How should we redesign our incident response process?

## Direction 1

## Brainstorm
1. Create a conventional weekly rotating primary/secondary on-call across product teams, backed by a single incident commander role and a shared P1 runbook template.
2. Stand up a small central SRE function that owns P1 response, standardizes tooling, and forces postmortems for every major incident.
3. Replace team-by-team escalation with a swarm model: one trained incident commander pages a cross-functional response pool, then pulls specialists only after containment.
4. Build a chat-ops-first incident system where every P1 spins up the same Slack channel, timeline bot, role assignments, and decision log automatically.
5. Make repeat incidents the core problem, not response speed: freeze feature work for any team whose service generates the same P1 twice without a permanently verified fix.
6. Kill informal on-call entirely and create an explicit “service ownership contract” where a team cannot ship a service unless its runbook, alerts, and backup coverage pass a readiness review.
7. Go uncomfortable and centralize all first response in a rotating “operations jury” of senior engineers from all teams, separating incident handling from service authorship on purpose.
8. Reframe the problem: you do not mainly have an incident-response problem, you have a documentation and accountability market failure caused by shared systems and diffused ownership.
9. Skip heavyweight postmortems and instead mine incident/chat/page data weekly for automated pattern detection, then force fixes on the top recurring alert clusters.
10. Optimize for customer communication first, not technical diagnosis: assign a dedicated external-comms lead for every P1 and measure time-to-trust rather than just MTTR.

## Direction: No Service Without an Incident-Ready Ownership Contract

## The Argument
The right redesign is to stop treating incidents as an on-call scheduling problem and start treating them as an ownership admission problem. Every service must have a named primary team, a trained rotating on-call, a minimum viable runbook, alert routing, and a backup responder before it is allowed to remain in production without exception. P1 handling then uses a shared swarm model: product-team primary owns diagnosis, a rotating incident commander runs the response, and specialists are pulled by skill only after immediate containment steps fail.

This differs sharply from the obvious options: ownership stays with product teams, escalation becomes a swarm rather than strict severity tiers, tooling starts with lightweight runbook and role templates instead of a heavy incident platform, learning happens through mandatory incident reviews plus a repeat-incident gate, and the response tradeoff is explicitly fast containment first.

**1. Why now?**  
Two things make this necessary now. First, your scale has crossed the threshold where informal heroics break: 12 P1s in a quarter, 3 teams per incident, and 40% repeat pages mean coordination failure is now a bigger problem than technical failure. Second, modern collaboration tools make lightweight standardization possible without building an SRE empire first: Slack/Teams workflows, templates, auto-created bridges, and simple service catalogs let you enforce readiness in weeks, not quarters. Two years ago you could still survive on tribal memory; now the incident volume and cross-team coupling make that impossible.

**2. What’s the workaround?**  
Today people are doing the usual bad substitutes: paging the engineer who “probably knows this area,” searching old Slack threads, pulling in three teams because nobody knows where responsibility starts or ends, and skipping postmortems because everyone is exhausted. Those workarounds prove the demand: the organization already wants a single owner, a repeatable first 15 minutes, and a way to avoid solving the same outage twice. They also reveal the constraint: any redesign that depends on a brand-new central team doing all the work will fail because the knowledge is still in product teams.

**3. Moment of abandonment**  
People abandon the current approach at minute 20–30 of a P1, when the first responder realizes there is no reliable runbook, no clear owner, and no confidence about who can make a risky containment change. At that point the incident turns into a social search problem. Design backward from that failure: the responder must know, immediately, who owns the service, what the first containment actions are, what dependencies matter, and who can authorize rollback, failover, or traffic shedding.

**4. 10x on which axis?**  
This is 10x better on **time-to-coordinated containment in the first 30 minutes**. Not MTTR overall—containment. That is the choke point your current process is failing on. If you can cut “who owns this / what do we do first / who’s in charge” from 30–60 minutes to 5 minutes, MTTR will follow. Is it merely good enough elsewhere? Yes. It is not the most elegant learning system and not the most automated tooling stack, but those weaknesses do not kill adoption because the core value is operational clarity under stress.

**5. Adjacent analogy**  
This is how aviation and surgery got safer: not by hiring a genius rescue team for every failure, but by refusing to operate without preflight/pre-op readiness checks, named roles, escalation rituals, and mandatory after-action learning. The mechanism is simple: standardize the first moves and ownership boundaries so human judgment is reserved for the genuinely novel parts. That transfers directly to incidents because your biggest losses are from confusion and repetition, not from a lack of raw engineering talent.

## First Move
Next week, pick the top 10 services involved in the last quarter’s P1s. For each service, force a 45-minute readiness review with the engineering manager and tech lead. By the end of that meeting each service must have: named primary team, primary/secondary on-call rotation for the next 8 weeks, a one-page P1 runbook, dependency list, rollback/kill-switch instructions, and the first 3 escalation contacts. No readiness review, no production changes except fixes to achieve readiness.

## Why This Beats the Alternatives
**Dedicated SRE team:** too slow and too detached. You will centralize pager pain without centralizing service knowledge, so SRE becomes a dispatcher with no authority and product teams stay sloppy.

**Unified incident tool first:** tooling won’t fix ownership ambiguity. A beautiful incident platform just makes it easier to be confused in a standard format.

**Just mandate postmortems:** useful but too downstream. Your system is failing before the review phase; only 30% of P1s even make it there now.

## Biggest Risk
Management flinches at the enforcement. If “incident-ready ownership contract” becomes advisory instead of mandatory, nothing changes: teams will promise to document later, informal on-call will continue, and the next P1 will still start with Slack archaeology. The redesign lives or dies on one hard rule: production responsibility requires explicit operational readiness.

---

## Direction 2

## Brainstorm
1. **Incident Guild Rotation with Skill Router** — shared guild-owned on-call, skill-based routing, chat-ops, mandatory incident review, optimize expert match over speed. **[ownership: shared; escalation: skill-based; tooling: chat-ops; learning: incident reviews; tradeoff: expert routing]**
2. **Swarm First, Queue Never** — rotating product-team primary, swarm escalation from first page, lightweight command board, automated pattern detection, optimize containment through parallel response. **[ownership: rotating; escalation: swarm; tooling: lightweight command board; learning: automated detection; tradeoff: containment]**
3. **Automation Gatekeeper Model** — no human first-line ownership for known classes, automation triages and executes runbooks, humans paged by failure mode, automated pattern mining, optimize repeat-incident elimination. **[ownership: automation+shared human backup; escalation: failure-mode routing; tooling: runbook automation; learning: automated detection; tradeoff: repeat prevention]**
4. **Customer-Comms-Led Incident Cell** — shared incident cell owns response, comms severity drives escalation, unified status tooling, incident reviews centered on customer impact, optimize trust and communication speed. **[ownership: shared cell; escalation: comms/impact-based; tooling: status-centric platform; learning: impact reviews; tradeoff: customer communication]**
5. **Follow-the-Sun Internal Responder Pool** — pooled responders across teams by weekly rotation, swarm escalation, runbook automation, blameless postmortems, optimize fatigue reduction and consistent coverage. **[ownership: pooled shared; escalation: swarm; tooling: automation; learning: postmortems; tradeoff: sustainability]**
6. **Service Certification Before Pager Eligibility** — no service may page humans until it has standard telemetry, one-click diagnostics, and tested runbooks; product teams rotate on-call; severity tiers remain; learning via certification audits; optimize page quality over response speed. **[ownership: rotating; escalation: severity-based; tooling: certification + diagnostics; learning: audits; tradeoff: page quality]**
7. **Incident Marketplace** — no fixed on-call by team; the first qualified responder claims incidents from a live pool, backed by specialist bench, chat-ops only, automated pattern detection, optimize utilization and expertise liquidity. **[ownership: open/shared; escalation: claim-based expert market; tooling: chat-ops; learning: automated detection; tradeoff: flexibility]**
8. **Repeat-Incident Kill Team** — temporary central squad owns every recurring P1/P2 class for 90 days, escalation by recurrence signature, automation-heavy tooling, weekly pattern reviews, optimize permanent page elimination over immediate MTTR. **[ownership: temporary central squad; escalation: recurrence-based; tooling: automation; learning: weekly pattern reviews; tradeoff: prevention]**

## Direction: Automation Gatekeeper Model

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| Informal “who knows this system?” paging and team-by-team manual triage | Human toil on known incidents, duplicate paging across 3 teams, bespoke docs nobody trusts | Executable runbooks, machine triage, recurrence tracking, explicit incident class ownership | A responder layer where automation contains known failures before humans join, with failure-mode routing instead of org-chart routing |

## The Argument
You do not have an on-call problem. You have a **repeatable-incidents-reaching-humans problem**.

Forty percent of pages are repeats. Average incident pulls in three teams. MTTR is four hours. That means your current process spends its first hour rediscovering ownership, context, and the first safe action. Redesigning around better human coordination alone will help, but it will not break the loop. The loop breaks when the most common incident classes stop starting as blank-slate human work.

The right redesign is an **Automation Gatekeeper**: every high-frequency incident class gets a machine-owned first response. Alerts no longer page “whoever is unlucky.” They hit a gate that classifies the failure, runs the relevant containment or diagnostics play, and only then pages the exact human role needed if automation cannot restore service.

This changes five things structurally:
- **Ownership model:** known incident classes are owned first by automation, with named human backups.
- **Escalation structure:** route by **failure mode**, not severity tier or product boundary.
- **Tooling:** executable runbooks, not static docs.
- **Learning:** automated pattern detection on repeat pages becomes the core learning loop.
- **Tradeoff:** prioritize **repeat elimination and accurate first action** over immediate full-team assembly.

**Why now?**  
You now have enough incident volume and repetition to justify codifying patterns. Twelve P1s in one quarter is not noise. Forty percent repeat rate is a catalog. The old informal model works only when incidents are rare and tribal knowledge is fresh. You have crossed the threshold where informality is the source of MTTR.

**What’s the workaround today?**  
Slack heroics, ad hoc Zoom rooms, searching old incidents, and paging multiple teams “just in case.” That is why on-call is dreaded: the job is not response, it is ambiguity absorption.

**10x on which axis?**  
**Time-to-correct-first-action.** Not total elegance. Not perfect root cause. The biggest win is making the first five minutes deterministic.

**Adjacent analogy:**  
This is how modern fraud and security operations evolved. The first layer is no longer an analyst reading raw alerts; it is automated playbooks that classify, enrich, and contain obvious cases, escalating only the ambiguous or novel ones.

## First Move
In the next two weeks, pull the last quarter’s 12 P1s and cluster them into the top 5 recurring failure modes. Assign one engineer from each product team plus one engineering manager to a **72-hour design sprint**. Their output is not a process doc. It is:
1. one standard incident schema,
2. one executable runbook template,
3. automation for the top **two** repeat incident classes to gather diagnostics and perform one safe containment step,
4. named backup humans for each failure mode.

Then change paging: those two alert classes must go through the gatekeeper first, not directly to people.

## Why This Beats the Alternatives
The obvious approach is a formal rotating on-call plus better postmortems. You need that eventually, but by itself it formalizes pain. It makes more people participate in a bad system.

A central SRE-style ownership model would improve discipline but creates a new bottleneck and lets product teams avoid operational maturity.

A swarm model speeds collaboration after mobilization, but your problem starts **before** collaboration: wrong people are being pulled into repetitive incidents with no executable first step.

A unified incident platform without automation gives you cleaner coordination on top of the same manual diagnosis.

This direction wins because it attacks the highest-leverage defect in your current system: repetitive, classifiable incidents still behave like novel emergencies.

## Biggest Risk
The automation layer becomes a thin wrapper around bad runbooks and loses trust. If the first two gatekeeper flows are not visibly faster and safer than current human triage, engineers will bypass it and the redesign will die.

---

## Direction 3

## Brainstorm
- **Follow-the-Sun Incident Desk** — shared weekly “incident desk” owned by a cross-team pair, swarm-based escalation, chat-ops first, mandatory incident review, optimize for customer communication continuity. **[ownership: shared; escalation: swarm; tooling: chat-ops; learning: incident reviews; tradeoff: customer communication]**
- **Reliability Jury Duty** — every engineer serves a short mandatory incident rotation outside their home team, skill-based routing to specialists, lightweight shared notebook instead of platform unification, pattern-detection learning, optimize for repeat-incident reduction. **[ownership: rotating non-product pool; escalation: skill-based; tooling: lightweight notebook; learning: automated pattern detection; tradeoff: recurrence prevention]**
- **Control Tower Model** — one incident commander cell triages all P1s, then dispatches teams by dependency map, timeline recorder tooling, blameless postmortems on every P1, optimize for fast containment. **[ownership: central command cell; escalation: dispatch routing; tooling: timeline recorder; learning: blameless postmortems; tradeoff: containment]**
- **Chaos Librarian Program** — no standing on-call at first response; alerts open a staffed triage queue during business hours plus fallback pager, escalation by known-service “capability owners,” documentation mining as primary tooling, automated pattern detection, optimize for root-cause codification. **[ownership: capability owners; escalation: capability-based; tooling: doc mining; learning: automated detection; tradeoff: root cause]**
- **Incident Market Maker** — responders bid in from an indexed skills roster, ad hoc swarm response, chat-room bot assembles context, incident reviews scored on reuse, optimize for shortest assembly time. **[ownership: opt-in responder bench; escalation: market/swarm hybrid; tooling: bot-assembled context; learning: review scoring; tradeoff: assembly speed]** *(contrarian)*
- **Freeze-and-Relay Protocol** — first responder’s only job is to freeze blast radius and hand off to a dedicated diagnosis relay team, strict two-lane escalation, minimal tooling changes, automated pattern detection for repeats, optimize for MTTC over MTTR. **[ownership: split containment/diagnosis teams; escalation: two-lane; tooling: minimal; learning: automated detection; tradeoff: containment speed]** *(contrarian)*
- **Dependency Cell Rotation** — rotate on-call by platform dependency group rather than product team, skill-based routing through service map, unified incident workspace, mandatory incident reviews, optimize for fewer cross-team handoffs. **[ownership: dependency-cell rotation; escalation: skill-based; tooling: unified workspace; learning: incident reviews; tradeoff: handoff reduction]**
- **Customer-First Incident Broadcast** — incidents are led by a communications captain plus technical swarm, escalation via swarm, status-page and internal broadcast tooling first, post-incident review only for externally visible incidents, optimize for trust and clarity. **[ownership: dual-role shared; escalation: swarm; tooling: broadcast-centric; learning: selective review; tradeoff: customer communication]**

## Direction: Reliability Jury Duty

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| Informal “whoever gets dragged in” incident ownership | Dependence on heroic domain experts joining every incident | Incident literacy across all 40 engineers | A mandatory rotating responder bench with a searchable skills ledger and repeat-incident radar |

## The Argument
You do not have an on-call problem. You have a **concentration-of-incident-knowledge problem**. That is why three teams get pulled into each P1, MTTR sits at four hours, and 40% of pages repeat. The same few people know how the system actually fails, everyone else dreads incidents, and learning never compounds.

**Reliability Jury Duty** fixes that by making incident response a short, mandatory, organization-wide civic duty. Each week, 4 engineers from different product teams form the responder bench. They are not primary owners of every service; they are trained first responders. One acts as lead, one as comms/timeline, two as investigators. Product specialists are pulled in only through **skill-based routing** when the bench hits a known gap.

That is structurally different from dedicated SRE ownership and from automation gatekeeping. It spreads ownership, routes by capability, uses a lightweight shared notebook/skills ledger rather than betting on one big platform, and learns primarily through **automated pattern detection** on incidents and pages, not sporadic postmortems.

**Why now?**  
Your current scale forces this. At 40 engineers and 12 P1s/quarter, you have enough incident volume to train responders but not enough to justify a fully separate SRE organization. Meanwhile, repeat incidents at 40% mean you are paying for the same ignorance over and over. The economics now favor broadening competence instead of deepening dependence on a few people.

**What’s the workaround today?**  
People are doing shadow escalation: paging the “usual adults,” DM’ing known experts, hunting scattered docs, and reconstructing system context live. That works only by burning out a small subset of engineers and making incident quality wildly inconsistent.

**10x on which axis?**  
**Responder coverage depth.** Not faster buttons — more engineers capable of meaningfully contributing in the first 15 minutes. That is the lever that cuts handoffs, dread, and repeats simultaneously.

**Adjacent analogy:**  
This is how hospitals and courts handle critical responsibility under constrained specialist supply. Not every citizen is a judge, but jury duty creates broad civic participation in a serious function; not every clinician is a specialist, but triage nurses stabilize, classify, and route effectively. You need triage competence distributed across the org.

## First Move
Within 2 weeks, create a **6-week pilot responder bench**: 4 engineers/week, each from a different team, scheduled in advance by engineering leadership. For every P1 during the pilot, the bench is paged first. They open a single incident notebook template with five required fields: symptom, suspected blast radius, customer impact, actions taken, specialists requested. Simultaneously, build a simple skills ledger in your wiki: every engineer lists services touched, infra skills, and past incidents. After each incident, tag cause and recurring signals in a shared sheet so repeat patterns become visible by week 3.

## Why This Beats the Alternatives
The obvious approach is “formalize on-call by team” or “hire/assign SRE ownership.” That preserves the same bottleneck: expertise stays local, incidents still drag in three teams, and dread becomes official instead of informal.

A pure automation-gatekeeper model also misses the main issue. Automation helps only after someone knows what to automate. Right now your knowledge is fragmented and your reviews are too sparse to produce good automations.

Compared with an incident-ready ownership contract, this does not require every team to become mature enough before service can operate. Compared with an automation gatekeeper, it does not wait for tooling standardization to create better response behavior. It changes the **social topology** of incidents first: more people become useful, fewer experts become single points of failure.

## Biggest Risk
Managers will protect their strongest engineers from jury duty, and the bench will become a dumping ground for whoever is available rather than a respected rotation. If that happens, quality drops and the model loses legitimacy fast.

---

## Synthesis

## The Fork

The real choice is Bet A: Service Ownership Contract vs Bet B: Automation Gatekeeper vs Bet C: Reliability Jury Duty.

## Bet A: Service Ownership Contract
Make incident readiness a production admission rule. Each service needs a named owner, rotating primary/secondary on-call, minimum runbook, alert routing, dependency map, and backup coverage. P1s run with product-team ownership plus a rotating incident commander and swarm escalation for specialists. This is the direct fix because your failures start with unclear ownership and missing first-step guidance, not lack of heroics. It changes ownership to product teams, escalation to swarm, tooling to lightweight runbook/role templates, learning to mandatory incident reviews, and optimizes fast containment.
**First move:** Review the 10 services involved in recent P1s and require owner, on-call rota, one-page runbook, rollback steps, and top escalation contacts before any non-fix production changes.
**Sacrifice:** You give up flexibility and tolerate slower feature delivery while teams meet the operational bar.

## Bet B: Automation Gatekeeper
Shift first response for repeatable incidents from humans to executable runbooks. Alerts hit a gate that classifies failure mode, gathers diagnostics, performs one safe containment step, and pages humans only if automation cannot restore service. This works if your real drag is repeated incidents reaching people as blank-slate emergencies. It differs sharply from Bet A: ownership is automation-plus-human backup, escalation is failure-mode routing, tooling is runbook automation, learning is automated pattern detection, and the tradeoff favors correct first action and repeat elimination over broad human mobilization.
**First move:** Cluster the last quarter’s P1s into top failure modes and automate diagnostics plus one safe containment action for the top two repeat classes, then route those alerts through the gate first.
**Sacrifice:** You defer broader incident literacy and accept weaker handling of novel incidents while investing in codifying known ones.

## Bet C: Reliability Jury Duty
Create a mandatory rotating responder bench: a weekly cross-team pool of engineers paged first for P1s. They stabilize, document, and route by skill, pulling specialists only when needed. The point is to spread incident competence beyond the usual experts so response quality stops depending on a few people. This differs from both others: ownership is a shared rotating pool, escalation is skill-based routing, tooling is a lightweight incident notebook plus skills ledger, learning is automated pattern detection, and the tradeoff favors capability distribution over immediate service-level ownership discipline or automation depth.
**First move:** Run a 6-week pilot with 4 engineers per week from different teams, a single incident notebook template, and a searchable skills ledger; page the bench first on every P1.
**Sacrifice:** You give up clear single-team accountability and accept temporary inefficiency while building broad responder capacity.

## Comparison

| | Timeline | Risk | What you learn | Strategic sacrifice |
|---|----------|------|----------------|---------------------|
| **Bet A** | 2–6 weeks to see faster containment and cleaner ownership | Managers may not enforce readiness gates; teams may create low-quality runbooks to comply | Which services lack real ownership and whether readiness discipline cuts coordination delay | Feature velocity and organizational flexibility; every service must meet a higher operating bar |
| **Bet B** | 4–8 weeks to judge first-action accuracy on top repeat classes | Poor automations lose trust and get bypassed; misclassification can slow response | Which incidents are truly repetitive and safe to codify into machine-led response | Investment shifts toward known failure modes, reducing optionality for broader human process redesign |
| **Bet C** | 3–6 weeks to see whether more engineers contribute effectively in incidents | Strong engineers may be withheld; bench quality may be uneven | Whether distributed triage capacity reduces expert bottlenecks and repeat social search | Clear service-by-service accountability; you choose shared capability over tighter ownership boundaries |
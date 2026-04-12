# Explore Intake Persona Simulations (Pass 5)

5 builders with real strategic problems. The protocol must produce a natural conversation that stays on their problem — register and flow are qualities observed in the transcript, not design goals of the test.

---

## Persona 1: Elena, 38, Series B CEO

**Role:** CEO, Series B SaaS (CRM for mid-market), 85 employees
**Problem:** Whether to pivot GTM from SMB to enterprise. Three enterprise deals stalling, SMB churn rising, board wants a decision by Q3.

### Initial Input

> We're a Series B CRM company selling to mid-market SMBs and I need to figure out whether we should pivot upmarket to enterprise. We have three enterprise deals in the pipeline that could each be worth 10x our average ACV but our entire product and team are built for SMB. Honestly I've been going back and forth on this for weeks.

### Simulated Answers

**A1** (likely question: something about what's driving the pivot consideration now)
> Two things happened in the same month. Our biggest SMB cohort hit 18-month churn — 40% of the Q1 2025 cohort is gone. And a Fortune 500 CHRO reached out cold asking if we could handle their use case. That was the moment where I thought okay maybe the market is telling us something. The board saw both data points and now they want a decision by Q3.

**A2** (likely question: threading on what the enterprise deals actually need)
> The three deals all want the same things — SSO, audit logs, custom workflows, and a dedicated CSM. We could probably ship SSO and audit logs in a quarter. Custom workflows is a 6-month rebuild of our core engine. The dedicated CSM thing — honestly that's the part I keep avoiding because it means hiring enterprise AEs and CSMs and that's a totally different org than what we have.

**A3** (likely question: threading on team/org impact)
> I have 22 engineers who've been building SMB features for two years. Three of them came from enterprise companies and would probably love it. The rest — I don't know. Our VP Eng is skeptical, she thinks we'd be chasing shiny objects and abandoning our base. She's not wrong about the risk but I think she's underweighting the churn signal. I haven't had the real conversation with her yet. That's probably the thing I'm most avoiding.

**A4** (likely question: threading on what happens if they don't pivot)
> If we stay SMB, we need to fix churn. Our NRR is 88% which is — not great. The product is sticky for the first year but then teams outgrow it. We've been losing deals to HubSpot on the low end and Salesforce on the high end. The middle is getting squeezed. I think we have maybe 18 months of runway on the current trajectory before the board starts asking harder questions about growth.

**A5** (likely question: threading on the 18-month runway or what "harder questions" means)
> The board isn't hostile — they backed us because they believe in the team. But they're looking at the same SaaS multiples everyone else is and a sub-100% NRR SMB play in 2026 is not what they signed up for. If we can show enterprise traction — even two of the three deals closing — that changes the narrative completely. But if we try and fail, we've burned 6 months of eng capacity AND the SMB product stalls. That's the thing that keeps me up.

### What a good conversation looks like
The interviewer stays on Elena's problem — the pivot decision, the board deadline, the team she hasn't talked to yet. Questions follow what she just said, not a coverage checklist.

---

## Persona 2: Raj, 44, CTO

**Role:** CTO, fintech company, 200-person eng org
**Problem:** Whether to begin monolith-to-microservices migration now or defer. Current monolith handles 12K TPS but deploy cycle is 4 hours and incident blast radius is total.

### Initial Input

> I need to evaluate the timing of a monolith-to-microservices migration for our core trading platform. The monolith currently handles 12K TPS with acceptable latency (p99 under 200ms) but our deploy cycle is 4 hours with full regression, and any incident has total blast radius across all product lines. The engineering org is 200 people across 14 teams, all deploying to the same artifact. I have three concerns: whether the performance overhead of a service mesh justifies the operational isolation, whether our current team topology maps to viable bounded contexts, and whether we can execute the migration without a feature freeze (which the business will not accept).

### Simulated Answers

**A1** (likely question: threading on one of the three concerns, probably team topology or deploy pain)
> The team topology concern is the one I have the least clarity on. We reorganized into domain-aligned teams 18 months ago (payments, risk, matching, settlement, compliance) but the code doesn't reflect those boundaries. Payments and risk share 340 database tables with no clear ownership; matching calls into settlement synchronously for 7 of its 12 core flows. The organizational boundaries exist on paper but the coupling in the codebase means teams still coordinate on every release. In practice, a change to risk scoring blocks the payments team for 2-3 days per sprint because of shared schema migrations.

**A2** (likely question: threading on the shared schema / coupling problem)
> We attempted a strangler fig approach for the compliance module in Q3 2025. The module was chosen because it had the fewest inbound dependencies (14 call sites versus 60+ for payments). The extraction took 11 weeks against a 6-week estimate. The primary cost overrun came from discovering implicit coupling through shared database views that weren't in our dependency graph. Post-extraction, compliance deploys independently (average 22 minutes), incident isolation is confirmed, and the team's velocity increased 30% measured by cycle time. The concern is that compliance was the easiest target; payments or risk extraction would be an order of magnitude more complex given the 340 shared tables.

**A3** (likely question: threading on what the compliance extraction taught them about feasibility of the harder modules)
> The compliance extraction validated the operational model (independent deploy, isolated blast radius, measurable velocity gain) but it also revealed that our dependency analysis tooling is insufficient for the remaining modules. We mapped static call graphs but missed runtime coupling (shared caches, event ordering assumptions, database triggers that span domains). For payments and risk specifically, I estimate 6-9 months of extraction work per module with a dedicated team of 4 senior engineers, during which those engineers are unavailable for feature work. The business is projecting 40% transaction volume growth in H2 2026 (new institutional product line), which means we need either the performance headroom from decomposition or a significant scaling investment in the monolith. Both paths cost roughly the same in engineering time; the question is which investment compounds.

**A4** (likely question: threading on which investment compounds, or the scaling tradeoff)
> The monolith scaling path is well-understood: vertical scaling plus read replicas plus selective caching. We can probably handle 20K TPS (a 67% increase) with 3 months of work and no architectural change. That buys us through Q1 2027. The microservices path gives us independent scaling per domain (payments at 3x, matching at 1.5x, settlement unchanged) but the service mesh overhead adds approximately 15ms to p99 latency per hop, and the critical path for trade execution crosses 4 services. Our SLA is 200ms p99; 4 hops at 15ms overhead consumes 60ms of that budget. The latency math is the technical constraint I cannot resolve with architecture alone; it requires either relaxing the SLA (which product will resist) or investing in a custom transport layer (which adds 2 months and ongoing maintenance burden).

### What a good conversation looks like
The interviewer stays on Raj's migration decision — the tradeoffs between scaling the monolith vs. decomposing, what the compliance extraction proved, and the latency math. Sufficiency should fire early — Raj provides dense, well-specified input.

---

## Persona 3: Kenji, 31, Solo Founder

**Role:** Solo founder, dev tools startup (CLI for database migrations), 18 months in, $8K MRR, bootstrapped
**Problem:** Whether to take VC funding ($1.5M seed offer on the table) or stay bootstrapped. Growth is steady but slow. Competitor just raised Series A.

### Initial Input

> ok so I've been building this database migration CLI tool for about 18 months — bootstrapped, just me — and I'm at like $8K MRR which honestly is more than I expected but also not enough to like, hire anyone or stop freelancing on the side. Anyway a VC firm reached out and they're offering $1.5M seed and I've been going back and forth on whether to take it because on one hand I could actually go full-time and hire 2 engineers but on the other hand I don't know if I want to be on the VC treadmill — like once you take that money you're kind of committed to the growth-at-all-costs thing right? And now my biggest competitor just raised a Series A so there's this pressure thing too. I don't know. I need to think through this.

### Simulated Answers

**A1** (likely question: threading on the competitor raising or the VC treadmill concern)
> Yeah so the competitor — they're called MigrateHQ — they just raised $4M and they're hiring like crazy. They have 6 engineers now I think. Their product is honestly not as good, like their CLI is clunky and they don't support half the databases I do, but they have a sales team now and they're showing up in all the same Slack communities and HN threads. I'm not — like I'm not panicking exactly but there's this feeling of watching someone build a bigger version of your thing with more resources and you're just one person. The thing is though, my users are really loyal. Like my NPS is insane for a CLI tool. People literally message me on Twitter saying they love it. So I don't know if the competitor thing is actually a threat or if I'm just scared of it.

**A2** (likely question: threading on what taking the money would actually change for users/product)
> Ok so this is the thing I keep going back to — if I take the money I'd hire two engineers and honestly the first thing I'd build is the team dashboard thing that like 30 of my paying users have asked for. Right now it's a single-user CLI and teams are hacking around it with shell scripts. The dashboard would open up the team/enterprise tier which is where the real money is — like my current users pay $29/month but the team plan could be $200/month per team. That's a completely different business. But — and this is the part that messes with me — I could also just build the dashboard myself over like 6 months while freelancing. It would be slower but I'd own 100% of the company and I wouldn't have to do the whole board meetings and quarterly updates thing. Anyway the VC said they're "founder-friendly" which — I mean they all say that right?

**A3** (likely question: threading on what "slower" actually means given the competitor)
> Yeah that's — that's actually the question isn't it. If I take 6 months to build the dashboard solo, MigrateHQ has 6 months with 6 engineers and a sales team to go grab the enterprise segment. And like, enterprise deals are sticky — once someone picks a migration tool and rolls it out to 50 developers you're not switching that. So there's a window thing. But also — I don't know, maybe the window isn't as small as I think? My users aren't enterprise, they're dev teams at mid-size companies, 20-100 devs. MigrateHQ is going after big enterprise, Fortune 500 type stuff. We might not even be competing for the same customers. I keep going back and forth on whether we're in the same market or adjacent markets.

**A4** (likely question: threading on same market vs adjacent markets)
> Honestly I think we're adjacent right now but converging. Like, my best users are platform engineers at companies with 50-200 devs — they picked my tool because it's fast and it works and they don't need a sales call to buy it. MigrateHQ is going top-down with enterprise sales. But the mid-market is where we'll collide eventually because those 50-200 dev companies grow into 500-dev companies and at some point they want the enterprise features. So the question is really about timing — do I need to be there with team features before my users outgrow the single-player tool, or do I have more runway than I think because the product-led growth thing keeps working as long as the product is better? I guess — I guess what I'm really asking is whether product quality is enough of a moat or if distribution wins regardless.

### What a good conversation looks like
The interviewer stays on Kenji's funding decision — the competitor pressure, what the money would actually change, the market overlap question, and whether product quality is enough of a moat. Kenji self-steers toward the real question; the interviewer follows his thread, not redirects.

---

## Persona 4: Maya, 50, VP Product (Public Company)

**Role:** VP Product, public company (B2B infrastructure, $400M ARR), owns the API platform product line
**Problem:** Platform strategy for their API product — whether to invest in a developer ecosystem (marketplace, SDKs, partner integrations) or double down on first-party features.

### Initial Input

> I lead the API platform product line at a public B2B infrastructure company. Our API product generates $85M ARR with 4,200 active customers. We are evaluating two strategic directions for the next fiscal year. Direction one is investing in a developer ecosystem: a marketplace for third-party integrations, open-source SDKs, and a partner program. Direction two is doubling down on first-party features: expanding our own integration library, building native workflow automation, and improving the core API performance. The decision has board-level visibility because it determines whether we allocate 40% of platform eng headcount to ecosystem infrastructure or to product features. I need to think through both paths rigorously.

### Simulated Answers

**A1** (likely question: threading on what's driving the decision now, or what the customer signal is)
> Three signals are converging. First, our top 50 customers by ARR have collectively submitted 180 integration requests in the last two quarters, and 60% of those requests are for products we will never build ourselves. Second, our competitor launched a marketplace eight months ago and is now cited in 30% of competitive loss reports as a differentiator. Third, our churn analysis shows that customers who use 3 or more integrations have 40% lower churn than single-integration customers. The data supports ecosystem investment. The concern is execution risk. We have never operated a marketplace, we have never managed third-party code quality, and our platform was not designed for extensibility. The first-party path is lower risk and higher confidence, but the data suggests it has a lower ceiling.

**A2** (likely question: threading on execution risk or the extensibility gap)
> The extensibility gap is the core technical risk. Our API was designed as a closed system with internal consumers only. Opening it to third-party developers requires a plugin architecture, a sandboxing model for third-party code, a review and certification process, and rate limiting per partner. Our platform engineering team estimates 4-6 months to build the foundation before any marketplace can launch. During that period, we ship zero marketplace value to customers. The first-party path has no such foundation cost. We could ship 15 new integrations in the same 4-6 months using our existing architecture. The question I keep returning to is whether the foundation cost is a one-time investment that compounds or a sunk cost if the marketplace doesn't reach critical mass.

**A3** (likely question: threading on marketplace critical mass or what determines adoption)
> Our developer relations team ran a survey of 200 current customers and 50 prospects. 72% said they would evaluate third-party integrations if available. 31% said they would build and publish integrations themselves if we provided the tooling. The question is conversion from stated intent to actual behavior. Marketplace economics are well-documented: you need approximately 50 quality integrations before the marketplace itself becomes a demand driver rather than a feature checkbox. At our current partnership pipeline, we project 20-25 integrations at launch. That is below the threshold. We could supplement with first-party integrations published through the marketplace to reach critical mass, but that blurs the strategic distinction between the two paths.

**A4** (likely question: threading on the blurred distinction or the hybrid approach)
> The hybrid approach has appeal but introduces organizational complexity. If we build first-party integrations through the marketplace architecture, the platform team builds ecosystem infrastructure while the integrations team builds through it. This validates the architecture with real usage and produces customer-visible value during the foundation period. The risk is that we optimize the architecture for our own consumption patterns rather than the diverse patterns of third-party developers. Internal teams follow our conventions and have access to internal APIs. Third-party developers will not. We have seen this pattern at previous companies where internal dogfooding produced an architecture that worked perfectly for the company and poorly for external developers.

### What a good conversation looks like
The interviewer stays on Maya's platform strategy — the ecosystem vs. first-party tradeoff, execution risk, marketplace critical mass, and the hybrid path. Sufficiency should fire early — Maya provides the decision, constraints, and concrete data upfront.

---

## Persona 5: Dara, 27, First-Time PM

**Role:** PM, B2B SaaS company, 2 years in role, first PM job, owns a feature that's underperforming
**Problem:** Whether to kill a collaboration feature (real-time co-editing) that launched 6 months ago with low adoption, or iterate on it.

### Initial Input

> I think I need to figure out whether to kill a feature or keep investing in it. We launched real-time co-editing in our project management tool about 6 months ago and adoption is not great — like 8% of DAU use it. I pushed pretty hard to get it built and now I'm the one who has to decide whether to pull the plug or try to fix it. I'm not sure if the problem is the feature itself or how we launched it.

### Simulated Answers

**A1** (likely question: threading on what the 8% are actually doing with it, or what the launch looked like)
> So the 8% who use it are actually pretty engaged. Their session times are 3x longer than average and they have lower churn. But they're almost all teams of 5 or fewer — the feature was designed for larger teams doing collaborative planning. We launched it as a tab in the project view with a blog post and an in-app tooltip. No onboarding flow, no template to start with, no use-case guidance. I think maybe the activation problem is real but I'm also not sure if better activation would move the number enough to matter. Our VP of Engineering has already flagged it as a maintenance burden because of the WebSocket infrastructure.

**A2** (likely question: threading on the activation gap or the small-team usage pattern)
> The small-team thing is interesting — I actually didn't expect that. We built it for 10-20 person teams doing quarterly planning sessions. But the people who love it are 3-5 person teams using it for daily standups and quick syncs. They basically turned it into a lightweight whiteboard. One customer literally told me "we stopped using Miro because your co-editing is faster for small stuff." That made me think maybe we built the right feature for the wrong audience. But our roadmap is focused on enterprise features for larger teams and I don't know if pivoting the feature toward small teams aligns with where the company is going.

**A3** (likely question: threading on the enterprise roadmap tension or what "aligns with where the company is going" means)
> Ok so this is the part where I'm actually more sure of myself. The company is moving upmarket. Our ICP used to be 20-50 person companies and now it's 200-500. The sales team is closing bigger deals and the feature requests are all about permissions, audit trails, SSO — enterprise stuff. Co-editing for small teams doesn't fit that narrative. But — and this is what I keep thinking about — what if the small-team use case IS the wedge into enterprise? Like, a 5-person product team inside a 500-person company discovers co-editing, loves it, and that drives bottom-up adoption. We've seen that pattern with our core product. I just don't have data to prove it would work for this feature.

**A4** (likely question: threading on whether there's a way to test the bottom-up hypothesis before committing)
> I could run a small experiment. Target teams of 3-7 within our existing enterprise accounts, add a lightweight onboarding flow optimized for quick sync use cases, and measure activation and expansion over 8 weeks. The eng cost is maybe 2 weeks of one engineer's time for the onboarding flow. If activation doubles in the target segment and we see any cross-team spread, that's signal. If it doesn't move, I have the data to kill it. The thing that makes me hesitate is that 8 weeks feels like a long time when the VP of Eng is already asking why we're maintaining the WebSocket infrastructure. But 2 weeks of eng time is cheap insurance against killing something that could have worked.

**A5** (likely question: threading on the VP Eng pressure or what happens if the experiment is inconclusive)
> If the experiment is inconclusive — like activation goes up 30% but no cross-team spread — honestly I'd probably kill it. The maintenance cost is real. WebSocket infra adds complexity to every deploy and we've had two incidents traced back to it. At some point the carrying cost outweighs the option value. I think my actual fear is that I'll kill it and six months later a competitor launches the same thing and it works. But that's not a reason to keep it. I know that. I just need to make the call with enough data that I can defend it when someone asks why we killed it.

### What a good conversation looks like
The interviewer stays on Dara's kill-or-iterate decision — the small-team adoption surprise, the enterprise roadmap tension, the bottom-up wedge hypothesis, and the experiment she's designing. Sufficiency should fire after the experiment plan — she has the decision, the data, and a test.

---

## What the 5 personas cover

| Persona | Problem type | Input clarity |
|---|---|---|
| Elena | Binary strategic pivot (SMB vs enterprise) | Moderate — has data but hasn't decided |
| Raj | Technical timing decision (migrate now vs defer) | High — well-specified, three named concerns |
| Kenji | Existential business decision (VC vs bootstrap) | Moderate — scattered but circling the real question |
| Maya | Platform strategy (ecosystem vs first-party) | High — structured, data-rich, clear options |
| Dara | Product decision (kill vs iterate a feature) | Moderate — has data, designing a test, needs to commit |

---
mode: explore
created: 2026-04-16T07:49:46-0700
model: gpt-5.4
directions: 4
prompt_versions: explore=3, diverge=4, synthesis=4
---
# Explore: Given the external feedback analysis, what should BuildOS actually change? Three

## Direction 1

## Brainstorm
- Add a hard tier declaration to `CLAUDE.md` and make `/setup` install only the hooks and skills for that tier, with higher-tier governance impossible unless explicitly upgraded.
- Implement file-level scope containment in BuildOS core as a generic pre-edit gate driven by task-spec `scope`, because autonomous agents need a portable safety boundary across repos.
- Keep autonomous execution out of BuildOS core and instead publish a reference orchestrator contract that downstream projects can implement differently.
- Build a full native `/auto` loop into BuildOS that chains plan-build-review-ship with retry budgets, because mode 4 autonomy is becoming the whole point of the framework.
- Remove most tier complexity from BuildOS and split it into separate distributions (`buildos-lite`, `buildos-governed`, `buildos-auto`) so wrong-tier deployment becomes structurally impossible.
- Treat “wrong tier” not as a config bug but as a product packaging failure: onboarding should start from observed team behavior and graduate controls only after usage evidence, not declared intent.
- Make scope containment the centerpiece and let tier/autonomy remain loose, arguing that the only universal primitive BuildOS should own is bounded authority.
- Do the uncomfortable thing: drop support for T0/T1 entirely from BuildOS and focus it only on T2/T3 teams, because lightweight users are better served by no framework than a framework trying to be light.
- Reframe the problem entirely: the issue is not missing features but lack of a clear kernel/userland boundary, so BuildOS should define a tiny governance kernel and push everything else to optional packs.
- Add an “admission controller” model like Kubernetes: every action passes through policy checks for tier, scope, and autonomy permissions, while workflow execution remains external.

## Direction: BuildOS should become a governance kernel: own tier guardrails and scope containment, but not the autonomous loop

## The Argument
BuildOS is a meta-framework, not an app. That means its job is to define the **portable safety and governance primitives** that should behave the same across repos. It should not own the full runtime behavior of autonomous delivery inside every downstream environment.

So the split is clear:

- **BuildOS core should solve Finding 1: wrong-tier guardrails**
- **BuildOS core should solve Finding 3: file-level scope containment**
- **BuildOS should not solve Finding 2 as a native end-to-end loop; it should define an interface/reference pattern for downstream orchestrators**

This is the most interesting direction because it imposes a **kernel/userland boundary** on a codebase that is already at risk of becoming a giant policy-and-runtime blob.

### Why now?
Two things changed.

First, AI usage has bifurcated. Two years ago, most teams were experimenting manually; now there is a real split between **assistant users** and **autonomous-agent users**. CloudZero’s rejection is proof that “one governance stack fits all” now actively harms adoption.

Second, autonomous agents are no longer just generating code; they are **executing multi-step work with delegated authority**. That makes generic containment primitives newly necessary. Worktree isolation was enough when agents mainly avoided collisions; it is not enough when they can refactor broadly and open PRs.

### What’s the workaround?
Today, teams work around wrong-tier deployment by social means: they ignore most of BuildOS, bypass hooks, or abandon the framework entirely. That is demand signal plus failure signal.

For autonomy, downstream projects already build ad hoc wrappers: CI jobs, shell scripts, task runners, bespoke “do plan/build/test/retry” loops. That proves the need is real—but also proves the implementation is environment-specific.

For scope containment, the workaround is task wording like “only touch `src/analytics/`,” code review vigilance, or isolated branches. Those are weak controls masquerading as policy.

### Moment of abandonment
People quit BuildOS at **setup and first week of use**, not after mastering it. The abandonment moment is when a mode 1–2 engineer sees logs, handoff docs, 20+ hooks, and 22 skills for a simple assistant workflow. Once they feel governed instead of helped, they are gone.

That means the first design priority is not “more capability.” It is **preventing accidental over-commitment**.

### 10x on which axis?
**Fit-to-user.** Not raw power, not completeness. A tier guardrail plus self-disabling hooks makes BuildOS 10x better at matching governance load to team maturity.

### Adjacent analogy
Kubernetes won by separating the **control plane** from workload-specific application logic. The platform owns scheduling, policy, admission, and isolation; apps own their runtime behavior. BuildOS should copy that pattern. Tier and scope are admission-control problems. The autonomous execution loop is workload logic.

### Specific scope
**Finding 1: Solve in BuildOS core**
- Add `tier` in `CLAUDE.md` frontmatter
- `/setup` installs the minimal valid package for that tier
- Hooks and skills self-disable above declared tier
- Upgrading tier requires an explicit command, not manual drift

**Finding 3: Solve in BuildOS core**
- Add `scope` to task spec
- Pre-edit hook blocks writes outside allowed paths
- Permit explicit escalation/override with audit trail
- Keep it path-based first; do not overreach into semantic/code-ownership policy yet

**Finding 2: Do not solve as core runtime**
- Publish a reference contract: required stages, state model, retry budget, artifact outputs, escalation points
- Optionally ship an example orchestrator, but keep it outside the kernel
- Downstream projects own execution because tests, deployment semantics, permissions, and failure handling are repo-specific

## First Move
Next week, implement a **Policy Kernel v1**:
1. Add `tier:` to `CLAUDE.md` frontmatter.
2. Change `/setup` to ask for tier and install only that tier’s hooks/skills.
3. Add `scope:` to task spec schema.
4. Add one pre-edit hook that denies writes outside `scope`.
5. Publish `docs/orchestrator-contract.md` defining how a downstream auto-loop should call `/plan`, build, `/review`, and `/ship`.

## Why This Beats the Alternatives
**Versus “just add the autonomous loop to core”**: that bloats BuildOS into a runtime product and forces one execution model onto wildly different repos, CI stacks, and release processes.

**Versus “only fix wrong-tier, leave scope downstream”**: that misses the real safety gap for autonomous agents. Scope containment is a universal governance primitive, exactly the kind of thing a meta-framework should own.

**Versus “leave all three to downstream projects”**: then BuildOS is documentation, not governance. If it cannot enforce fit and bounded authority, it is punting its core job.

## Biggest Risk
The kernel boundary may be politically hard to hold. Once you define an orchestrator contract, pressure will build to ship a “temporary” default loop in core, and that can drag BuildOS back into framework sprawl. The main risk is not technical failure; it is loss of discipline about what BuildOS is.

---

## Direction 2

## Brainstorm
- **Ship a certification suite, not new core features** — BuildOS defines conformance tests for tiering, autonomy handoff points, and file-scope policy; downstream implementations pass/fail against it. **[Approach, Scope, Success criteria, Who it affects]**
- **Turn BuildOS into a deployable profile generator** — `/setup` emits one of several precomposed operating profiles (Assistant, Guided, Autonomous), with static pruning of hooks/skills instead of runtime self-disabling. **[Approach, Tradeoff, Success criteria]**
- **Create a reference runner as a separate companion package** — keep BuildOS governance-only, but publish an optional `buildos-runner` that handles autonomous loops and scope enforcement contracts. **[Approach, Scope, Who it affects, Tradeoff]**
- **Move enforcement to repository CI/policy engines** — BuildOS only writes machine-readable policy manifests; GitHub Actions/OPA/pre-commit enforce tier and file-scope outside Claude runtime. **[Approach, Scope, Tradeoff, Success criteria]**
- **Adopt a “buy/borrow orchestration” strategy** — don’t build the autonomous loop; integrate BuildOS with existing agent runners/orchestrators via a narrow contract. **[Approach, Scope, Tradeoff, Who it affects]**
- **Make BuildOS installation interactive and use-case gated** — no universal setup; onboarding asks team mode, repo risk, and desired autonomy, then excludes most machinery by default. **[Approach, Tradeoff, Success criteria]**
- **Contrarian: remove in-band autonomy ambitions from BuildOS entirely** — BuildOS should only specify reviewable artifacts and stop trying to coordinate live agent behavior. **[Approach, Scope, Tradeoff, Success criteria]**
- **Contrarian: optimize for reversibility, not enforcement** — instead of blocking wrong-tier or out-of-scope edits, maximize rollback, audit diffs, and fast recovery. **[Approach, Tradeoff, Success criteria, Who it affects]**

## Direction: Publish BuildOS Conformance Tests, Not an Autonomous Core

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| Ad hoc arguments about what “belongs” in BuildOS | Pressure to add orchestration logic into the framework | Clarity of the BuildOS/downstream boundary | A conformance suite for tier fit, scope enforcement, and autonomy contracts |

## The Argument
BuildOS should solve **Finding 1 and Finding 3 as required conformance behaviors**, and treat **Finding 2 as an integration contract, not a built-in loop**.

The mechanism is the key difference: instead of expanding BuildOS into more runtime machinery, define a **testable compatibility standard** for any BuildOS deployment.

That means:

- **Wrong-tier guardrail:** mandatory. Any repo claiming “BuildOS-enabled” must pass a setup conformance test proving that a declared tier results in only the permitted hooks/skills/policies being active. Whether that’s implemented via `CLAUDE.md` frontmatter, generated config, or static pruning is up to the repo.
- **File-level scope containment:** mandatory for autonomous or multi-agent modes. Any T2/T3 deployment must pass a test showing that an agent scoped to `src/analytics/` cannot edit outside allowed paths without explicit escalation.
- **Autonomous execution loop:** optional. BuildOS should publish the contract an autonomous runner must satisfy: input artifact, allowed state transitions, test/review/ship checkpoints, audit outputs. But the actual loop belongs to downstream runners or a separate companion package.

**Why now?**  
Because the failure mode has changed from “missing features” to **unsafe or unusable deployments of a meta-framework**. CloudZero didn’t fail because the tier model was wrong; it failed because nothing enforced correct implementation. As BuildOS gets deployed into more contexts, the bottleneck is no longer inventing governance concepts. It’s ensuring those concepts survive contact with installation and orchestration.

**What’s the workaround?**  
Right now, teams are doing one of two bad workarounds:
1. **Manual trimming** — selectively ignoring hooks/skills/docs they don’t need, which is brittle and non-repeatable.
2. **Custom orchestration** — each downstream project invents its own agent runner and scope rules, with no common way to verify compatibility.

The conformance model fixes both. It gives downstream teams implementation freedom without ambiguity about what “correct BuildOS behavior” means.

**10x on which axis?**  
**Portability.** A meta-framework wins when many teams can adopt it safely in different environments without forking the philosophy every time.

**Adjacent analogy:**  
Think **Kubernetes conformance**, not “Kubernetes must ship every scheduler, cloud primitive, and workflow engine itself.” The ecosystem scaled because the core defined what compliant behavior looked like, while allowing many implementations.

So the right scope is:
- **BuildOS must standardize and test:** tier selection behavior, scope containment behavior, handoff artifacts, and autonomy checkpoints.
- **BuildOS should not own:** the long-running autonomous execution engine itself.
- **Downstream projects or companion tools should own:** the runner, retry strategy, environment-specific test commands, PR mechanics, and repo-specific escalation paths.

## First Move
Write a **BuildOS Conformance Spec v0.1** with 6 executable tests:

1. T0 install activates no T2/T3-only hooks.
2. T1 install preserves memory features without governance hooks.
3. T2/T3 install exposes active policy surface explicitly.
4. Scoped task cannot edit outside allowed paths.
5. Scoped task can request escalation and produce an audit trail.
6. Autonomous runner contract: given a task artifact, it must emit plan, test results, review output, and PR-ready summary in the required schema.

The first affected users are **maintainers deploying BuildOS into repos**, not end developers. This changes the conversation from “should BuildOS build X?” to “what behavior must any BuildOS deployment prove?”

## Why This Beats the Alternatives
The obvious approach is to add a `tier` field, add scope fields, and maybe build `/autoplan`-style execution into core. That solves symptoms in one implementation, but it also drags BuildOS deeper into runtime product territory.

This direction is better because BuildOS is a **meta-framework**. Meta-frameworks fail when they accumulate bespoke mechanics for every deployment mode. They succeed when they define enforceable contracts others can implement consistently.

It also differs from the previous direction by not making BuildOS the governance kernel in a live autonomous system. Instead, BuildOS becomes the **compatibility authority**. The optimization shifts from control to interoperability.

What’s wrong with the alternatives:
- **Adding the autonomous loop to core:** too opinionated, too environment-specific, and likely to create the next “wrong tier” problem for teams who don’t need autonomy.
- **Leaving everything to downstream repos:** guarantees drift and repeats CloudZero’s over-governance failure.
- **Runtime self-disabling only:** useful, but still an implementation detail. Without tests, every deployment can get it subtly wrong.

## Biggest Risk
The biggest risk is that conformance feels too abstract and doesn’t solve pain fast enough for teams who want a working autonomous developer now.

If the spec ships without a reference implementation or sample tests people can run in CI, it will read like architecture theater. The conformance suite must be executable from day one, or this direction dies.

---

## Direction 3

## Brainstorm
- **Ship a BuildOS Compatibility Profile and certify downstream runners/orchestrators against it** `[Approach, Scope, Who it affects, Success criteria]`
- **Turn BuildOS into a thin policy API: hooks expose machine-readable decisions, downstream tools own enforcement UX and autonomy** `[Approach, Tradeoff, Who it affects, Success criteria]`
- **Create a reference deployment pack by operating mode (Assistant / Guided / Autonomous), not by feature list** `[Approach, Scope, Tradeoff, Who it affects]`
- **Default-deny packaging: BuildOS installs almost nothing until a project explicitly enables capability bundles** `[Approach, Tradeoff, Success criteria]`
- **Offer BuildOS as a managed control plane maintained by a central platform team, not as a repo-embedded framework** `[Approach, Scope, Who it affects, Tradeoff]`
- **Split BuildOS into two products: Team Assist Kit and Agent Ops Kit** `[Approach, Scope, Who it affects, Success criteria]`
- **Contrarian: remove most hooks from core and replace them with generated repo policies checked in CI** `[Approach, Tradeoff, Scope, Success criteria]`
- **Uncomfortable: stop solving autonomy in BuildOS entirely and standardize the handoff contract between planner and external agent runners** `[Approach, Scope, Tradeoff, Who it affects]`

## Direction: Mode-Based Reference Packs, Not More Core Mechanics

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| One-size-fits-all BuildOS installs | Accidental exposure to T2/T3 machinery | Fit between user mode and deployed governance | Three opinionated reference packs: Assistant, Guided Delivery, Autonomous Agent |
| Implicit assumption that every repo should see all hooks/skills | Need for teams to reason about 20+ hooks up front | Adoption clarity during onboarding | A pack manifest that declares enabled hooks, skills, and required metadata |
| Ad hoc downstream assembly of autonomy and containment pieces | Meta-framework ambiguity at install time | Reproducibility of deployment choices | A pack-specific setup flow and acceptance checklist |

## The Argument
BuildOS should change **how it is packaged and deployed**, not just add another primitive.

The right move is to publish and support **three mode-based reference packs**:

1. **Assistant Pack**: solves the wrong-tier problem by making T0/T1 the default experience. Minimal hooks, minimal always-on process, no session-log burden.
2. **Guided Delivery Pack**: for teams that want stronger workflow governance but still keep humans in the loop.
3. **Autonomous Agent Pack**: includes file-level scope containment as a required control and defines the minimum contract an external runner must satisfy.

This accepts the premise that the three gaps are real, but it changes the mechanism. Instead of asking “which features should core BuildOS own?”, ask “what complete deployment shape should each mode get by default?”

That leads to clear scope decisions:

- **Wrong-tier guardrail: BuildOS must solve this.**  
  This is a packaging/onboarding failure inside the framework’s control. If BuildOS knows tiers exist, it must stop shipping an install shape that routinely violates them. In the packs model, the first decision is “what mode are you in?”, and the pack determines what gets enabled.

- **File-level scope containment: BuildOS should solve this for the Autonomous Agent Pack.**  
  Scope containment is governance, not business logic. It belongs in BuildOS when autonomous agents are in play. But it should not burden Assistant or Guided users. Put differently: containment is mandatory in one pack, irrelevant in another.

- **Autonomous execution loop: BuildOS should not become the general runner.**  
  It should define what the Autonomous Agent Pack expects from a runner: task spec format, allowed file scope declaration, success/failure signals, required review gates, PR handoff contract. The actual loop remains downstream or in an external orchestrator. BuildOS packages the governance environment for autonomy; it does not become the autonomy engine.

**Why now?**  
Because BuildOS has crossed the threshold where abstract flexibility is causing deployment failure. CloudZero already proved the current install shape can over-govern mainstream users. Also, the system is now large enough—22 skills, 21 hooks—that “just deploy core and selectively ignore things” is no longer credible.

**What’s the workaround?**  
Today people are manually under-installing, telling teams to ignore most of the framework, or relying on a local expert to decide what to enable. For autonomy, downstream projects stitch together their own runner around `/plan`, build, review, and ship. For scope, they rely on task wording and discipline. Those are fragile human workarounds.

**10x on which axis?**  
**Adoption fit.** The goal is not more capability; it is getting the right amount of BuildOS into the right repo.

**Adjacent analogy:**  
Kubernetes distributions succeeded not because every team assembled primitives themselves, but because opinionated distributions packaged different operational defaults for different needs. BuildOS needs distributions.

## First Move
Define and ship a **pack manifest** checked into the repo root, generated by `/setup`, with exactly three supported values: `assistant`, `guided`, `autonomous`.

Then map every existing hook and skill to one or more packs. That creates an immediate decision signal: if a hook or skill cannot be cleanly assigned, it is too ambiguously scoped.

The concrete first audience is new deployments and platform owners onboarding teams. Their setup flow changes from “install BuildOS” to “choose operating mode.”

## Why This Beats the Alternatives
The obvious approach is to add a `tier` field, add scope enforcement, and debate whether to add an autonomous loop. That treats symptoms independently and keeps the deployment problem unsolved. Teams would still face a sprawling framework with piecemeal toggles.

It also beats the previous directions:

- **Against “governance kernel”**: that still centers core architecture. This direction centers deployable operating modes. It optimizes for adoption and fit, not purity of system boundaries.
- **Against “conformance tests”**: tests help integrators after they choose an architecture. They do not solve the front-door problem that the wrong users are getting the wrong BuildOS in the first place.

This approach forces BuildOS to make explicit promises to distinct user types. That is the missing product move.

## Biggest Risk
The packs become superficial labels over the same bloated system. If “Assistant Pack” still drags in most hooks, docs, and expectations, nothing improves. This only works if each pack is materially smaller, clearer, and opinionated enough to exclude real functionality.

---

## Direction 4

## Brainstorm
- **Stop treating BuildOS as a runtime product; make it a packaging system with opinionated install profiles, and declare autonomous loops out of scope** — [Approach, Scope, Tradeoff, Success criteria]
- **The question is wrong because “BuildOS should scale from solo to autonomous” is an invalid product boundary; split BuildOS into “AssistOS” and “AgentOS” and stop optimizing one artifact for both** — [Approach, Scope, Who it affects, Success criteria]
- **The question is wrong because the main failure is adoption fit, not missing mechanics; prioritize uninstallability and default-minimal deployments over adding any new loop or guardrail logic** — [Approach, Tradeoff, Success criteria, Who it affects]
- **The question is wrong because autonomous execution is not a framework feature but an infrastructure liability; BuildOS should standardize handoff contracts to external orchestrators and refuse to own execution** — [Approach, Scope, Tradeoff, Who it affects]
- **Replace “solve the three gaps” with “define unsupported operating modes”; explicitly de-support mode-4 autonomy until downstreams prove repo-local safety primitives** — [Scope, Tradeoff, Success criteria, Who it affects]
- **The question is wrong because wrong-tier deployment is a sales/onboarding/configuration failure, not a governance failure; move solution from code to installer UX and docs defaults** — [Approach, Scope, Who it affects, Success criteria]
- **Contrarian: remove T3 ambitions from core BuildOS entirely and optimize only for T0–T2 governance, pushing autonomy and fine-grained containment into separate paid/pro team tooling** — [Scope, Tradeoff, Who it affects, Success criteria]

## Direction: Split the premise: BuildOS should not be one framework spanning assistant use and autonomous agents

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| Eliminate the assumption that one BuildOS artifact should serve T0 through T3 equally | Reduce core responsibility for execution orchestration and repo-specific containment | Raise clarity of operating boundary: governance kernel vs autonomous agent platform | Create a product line split: BuildOS Core (T0–T2) and Agent Pack contract (T3-only, downstream-owned) |

## The Argument
BuildOS should **solve only Finding 1 in core**, **partially solve Finding 3 as a minimal contract**, and **explicitly not solve Finding 2 in core**.

The question is wrong because:

1. **The question is wrong because it assumes “scale from solo to autonomous” means one artifact should implement both.** That’s how you get C9 users drowning in hooks meant for agent fleets.
2. **The question is wrong because it treats an autonomous build loop as a missing feature, when it is actually an operating model with repo-specific risk, CI coupling, credentials, rollback, and compute policy.** That belongs to downstream infrastructure.
3. **The question is wrong because it assumes safety primitives all belong in the same layer.** Wrong-tier protection is framework-level. File write scope is a thin framework contract plus repo-local policy. Execution loops are orchestration-layer behavior.

So the right answer:

- **Finding 1: BuildOS must solve this now.**
  This is the one clear core failure. The framework already knows about tiers but does not enforce them at install time. That is a product contradiction. Add install-time profile selection and hard self-disabling behavior for features above the selected tier. Success means teams cannot accidentally receive T2/T3 overhead when they asked for T0/T1.

- **Finding 2: BuildOS should not add an autonomous execution loop.**
  BuildOS should define the interface an orchestrator can call into—plan artifact format, task state transitions, expected gate outputs—but not own the loop that reads spec, edits code, runs tests, retries, and opens PRs. That loop depends on repo topology, CI shape, test economics, secret access, and rollback tolerance. If BuildOS owns it, it becomes an unreliable pseudo-CI system.

- **Finding 3: BuildOS should solve only the framework-shaped slice.**
  Add a generic task-scope schema and a hook that can enforce allowed paths if a downstream project declares them. BuildOS should not try to infer semantic file boundaries or maintain per-repo path policy. Core provides the enforcement mechanism; downstream provides the actual scope map.

**Why now?**  
Because the failure mode has moved from theoretical to observed. CloudZero already demonstrated that over-governance kills adoption. Also, as soon as people ask for mode-4 autonomy, the cost of ambiguous product boundaries explodes. You either narrow the core now or spend the next year accreting orchestrator logic into a governance framework.

**What’s the workaround today?**  
People manually trim CLAUDE.md, selectively ignore hooks, or simply reject BuildOS. For autonomy, downstream teams glue together ad hoc scripts or external orchestrators. For scope containment, they rely on prompt instructions and post hoc review. Those are all symptoms of the same issue: BuildOS is carrying an overly broad promise.

**10x on which axis?**  
**Adoption fit.** Not capability count.

**Adjacent analogy:**  
Kubernetes worked because it standardized control-plane contracts, not because it embedded every application runtime workflow. GitHub Actions doesn’t own your deployment architecture; it provides primitives and lets repos define the rest.

## First Move
Make a **hard product boundary decision in docs and installer behavior**:

1. Reposition **BuildOS Core = T0–T2 governance framework**.
2. Add `/setup` profiles that install only the selected tier’s assets and write `tier:` into `CLAUDE.md`.
3. Add a minimal `scope:` task schema and generic pre-edit path check hook.
4. Publish an **Agent Pack interface spec** for downstream orchestrators instead of building an autonomous loop.

The first concrete action: change `/setup` so users must choose `assistant`, `structured`, or `governed`, and the installer physically excludes higher-tier hooks/skills rather than merely documenting them.

## Why This Beats the Alternatives
The obvious approach is “just add all three”: tier guardrails, file scope checks, and an autonomous loop. That makes BuildOS more internally complete and externally less usable. It doubles down on the mistaken premise that one framework should span casual assistant use and autonomous software delivery.

It also beats the previous directions because:
- It is **not** making BuildOS a stronger governance kernel.
- It is **not** publishing tests instead of features.
- It is **not** creating reference packs around the same core mechanics.

This is a **product-boundary correction**: stop asking BuildOS to be universal. Fix the one core contradiction, provide one thin safety primitive, and explicitly refuse the orchestration problem.

## Biggest Risk
The biggest risk is organizational, not technical: **people may resist narrowing the promise of BuildOS** because “supports T0–T3” sounds strategically attractive. If leadership won’t give up the unified-story marketing, the codebase will keep absorbing mismatched responsibilities and recreate the same adoption failure at larger scale.

---

## Synthesis

## The Fork

The real choice is [Bet A: Governance Kernel] vs [Bet B: Conformance Standard] vs [Bet C: Product Split].

## Bet A: Governance Kernel
BuildOS core should directly own the universal governance primitives: hard tier guardrails at setup and file-level scope containment at edit time. It should not own the autonomous execution loop; instead, publish an orchestrator contract and maybe a sample runner outside core. This is the obvious path because it fixes the two concrete failures inside BuildOS’s control without turning the framework into a repo-specific runtime. It works if you hold a strict kernel/userland boundary: BuildOS enforces bounded authority; downstream tools decide how to execute work.
**First move:** Add `tier:` to `CLAUDE.md`, make `/setup` install only that tier’s hooks/skills, add `scope:` to task specs, ship one pre-edit path gate, and publish `orchestrator-contract.md`.
**Sacrifice:** You give up the simplicity of “one BuildOS with everything included” and the speed of shipping a native autonomous loop in core.

## Bet B: Conformance Standard
Don’t add much more runtime behavior to BuildOS. Define BuildOS as a compatibility standard with executable conformance tests for tier fit, scope enforcement, and autonomous-runner handoff artifacts. Downstream repos or companion tools can implement the mechanics however they want, but they must prove compliant behavior. This differs by optimizing for portability and interoperability, not direct control. It works if the real failure is drift between BuildOS’s philosophy and how teams actually deploy it. Success is not “core has the feature”; it is “any claimed BuildOS deployment passes the same tests.”
**First move:** Publish Conformance Spec v0.1 with executable tests for T0/T1/T2 installs, scoped write denial, escalation audit trail, and autonomous runner outputs.
**Sacrifice:** You give up immediate end-user relief; this helps maintainers and integrators first, not teams wanting a working default experience next week.

## Bet C: Product Split
Reject the premise that one BuildOS artifact should span assistant use and autonomous agents. Reposition BuildOS Core for T0–T2 only, and define a separate Agent Pack or product line for T3 autonomy with its own contract and tooling. Core still fixes wrong-tier deployment and may provide a thin scope primitive, but autonomy is explicitly out of scope for the main framework. This is the sharpest strategic break: optimize adoption fit by narrowing the promise, not by improving architecture inside the same product. It works if over-governance is fundamentally a product-boundary failure, not an implementation gap.
**First move:** Change positioning and `/setup` so users choose assistant/structured/governed profiles, physically exclude higher-tier assets, and publish an Agent Pack interface spec.
**Sacrifice:** You give up the unified “BuildOS scales cleanly from solo to autonomous” story and some cross-mode reuse.

## Comparison

| | Timeline | Risk | What you learn | Strategic sacrifice |
|---|----------|------|----------------|---------------------|
| **Bet A** | 1–3 weeks for first proof: setup changes, schema update, and one path gate are modest extensions to existing hooks/installer patterns | Boundary creep: pressure to keep adding runner behavior into core | Whether tier install + scope gates materially reduce first-week abandonment and unsafe edits | Giving up a monolithic core and delaying a native autonomous loop |
| **Bet B** | 2–4 weeks for a usable v0.1 if tests are mostly spec + CI fixtures; unknown if reference fixtures are missing | Abstractness risk: spec may feel like architecture theater without runnable tooling | Whether BuildOS needs stronger implementation control or just enforceable standards | Giving up direct product control over how deployments are built |
| **Bet C** | 1–2 weeks to change installer/profile packaging and docs; longer if codebase must be physically separated | Organizational risk: teams may resist narrowing scope or maintaining two product surfaces | Whether adoption improves more from narrowing audience than from adding mechanisms | Giving up the universal-framework positioning and some T0–T3 continuity |
---
mode: explore
created: 2026-04-11T11:25:10-0700
model: gpt-5.4
directions: 4
prompt_versions: explore=3, diverge=4, synthesis=4
---
# Explore: How should we rename and restructure 25 BuildOS CLI skills into a smaller, more 

## Direction 1

## Brainstorm
- Rename everything around user intent questions like `/what-next`, `/what-build`, `/is-it-ready`, and consolidate to 10–12 commands with `/status` as the main router.
- Keep most skills intact but give them clearer verb names, add aliases, and rely on better docs plus `/status` suggestions for discoverability.
- Split skills into two tiers: 6 daily-use commands the user memorizes, and a hidden specialist layer for rare design, audit, and governance tasks.
- Make the interface mostly automatic: session start auto-runs recall, pre-commit auto-runs review/qa, and the user only invokes a few high-level commands manually.
- Go aggressively contrarian and remove almost all named skills except `/status`, turning the system into a conversational router that translates natural requests into the right underlying script.
- Reframe the problem entirely: the issue is not naming but retrieval failure, so build a “moment-based command palette” keyed to states like “stuck,” “uncertain,” “ready to ship,” and “need options.”
- Merge by decision type rather than workflow stage: commands become `/decide`, `/explore`, `/plan`, `/check`, `/ship`, `/record`, regardless of which backend scripts run.
- Use metaphors instead of verbs—`/map`, `/stress-test`, `/draft`, `/gate`, `/launch`, `/logbook`—to make the set feel more distinct and memorable.
- Do the uncomfortable thing: kill `/autoplan`, `/debate`, and `/refine` as user-facing entries because they reflect system internals, not real moments of need.
- Create a question-first CLI where every command starts with “I need…” semantics: `/need-direction`, `/need-options`, `/need-a-plan`, `/need-a-check`, `/need-proof`, `/need-to-ship`.

## Direction: Intent Router with a 6-command daily layer and hidden specialists

## The Argument
The right move is to stop exposing the pipeline and start exposing the user’s moment of need.

Build a **two-layer system**:

**Daily layer: 6 commands**
- `/next` — what should I do now?  
- `/figure-out` — help me define/explore what to build  
- `/options` — show tradeoffs, alternatives, pressure-test thinking  
- `/plan` — turn a direction into an actionable plan  
- `/check` — is this ready / what’s wrong / validate quality  
- `/ship` — deploy and close the loop  

**Specialist layer: hidden but available**
- `/research`, `/audit`, `/setup`, `/docs`, `/capture`, `/design`
- Plus aliases for old names during migration

Behind the scenes, `/figure-out` can route to define/elevate/challenge, `/options` can route to debate or research, and `/check` can route to review/review-x/qa/governance/design-review depending on context. The underlying scripts stay unchanged. The user only memorizes the moments they actually feel.

### Why now?
Because the constraint has changed from “can the system do enough?” to “can one person reliably remember and invoke the right capability at the right moment?” Two years ago, the value was in accumulating skills. Today, with `/status` already acting as a router and `autoplan` already proving wrapper behavior works, you have enough system intelligence to **hide architecture and expose intent**. The modern CLI can infer context, suggest next actions, and auto-run routine checks. That makes consolidation possible now in a way it wasn’t when every skill had to be manually explicit.

### What’s the workaround?
Today, users do three things:
1. They type `/status` to remember what exists.
2. They reuse a small subset of memorable commands and forget the rest.
3. They ask in natural language instead of invoking a skill because they can’t recall the right one.

That is proven demand for a simpler intent layer. It also reveals the constraint: people do not think in your pipeline, they think in situational prompts like “what are my options?” or “is this code ready?”

### Moment of abandonment
People quit at the exact moment they have to translate a fuzzy mental state into a system-internal term.  
“I need to think this through” does not naturally map to `define`, `elevate`, `challenge`, or `debate`. So they skip the skill entirely, or pick the wrong one, or fall back to generic chat. Design backward from that failure point. The command should match the thought already in their head.

### 10x on which axis?
**Recall at the moment of need.**  
Not power. Not purity. Not architectural elegance. This direction is 10x better on “can I remember the right command in 2 seconds without consulting a manual?”

### Adjacent analogy
This is what happened in consumer photo apps. Early tools exposed internals: curves, levels, histograms, channel mixers. Modern tools expose intent: enhance, retouch, remove, blur background. The underlying operations still exist, but the user-facing layer matches the job-to-be-done. That transfer works here because your problem is the same: too many powerful primitives, too little retrieval under real working conditions.

## First Move
Next week, implement a **6-command alias layer** without deleting anything:

- `/next` → status
- `/figure-out` → routes among define/elevate/challenge
- `/options` → routes among debate/research
- `/plan` → plan/autoplan
- `/check` → review/review-x/qa/governance/design-review
- `/ship` → ship + optional capture/doc-sync prompt

Then mark the old commands as “advanced aliases” in help output, not primary entries. Update `/status` so every recommendation uses only the new top-layer names.

## Why This Beats the Alternatives
**Versus light rename-only:**  
Renaming 25 commands still leaves 25 retrieval problems. Better labels help, but quantity still kills recall.

**Versus single `/status` only:**  
A pure router is too opaque. Users still want a handful of stable handles they can trust and learn.

**Versus pipeline-ordered grouping:**  
That matches system architecture, not the user’s cognition. It optimizes for how BuildOS works, not how a solo dev reaches for help.

## Biggest Risk
`/check` and `/figure-out` may become overloaded umbrellas that feel vague or unpredictable. If routing is inconsistent, trust collapses and users go back to generic chat. The fix is strict routing rules, visible “why I chose this” feedback, and the ability to override into specialist commands when needed.

---

## Direction 2

## Brainstorm
- **Question-led menu**: replace command names with 8 “what am I trying to answer?” prompts like `what-next`, `what-build`, `is-it-worth-it`, `is-it-ready`; flat set, aggressive merge, contextual nudges, auto-run recall/review, clean break. **[naming, grouping, merge, discoverability, automation, migration]**
- **Mode switching instead of skills**: one `/work` command with persistent modes (`explore`, `decide`, `make`, `check`, `ship`) that remap sub-actions automatically by session state; workflow-stage naming, single entry point, very aggressive consolidation, router-first discoverability, high automation, deprecation period. **[naming, grouping, merge, discoverability, automation, migration]**
- **Job-story cards**: 10 commands phrased as user intents in sentence fragments (`help-me-decide`, `help-me-scope`, `help-me-validate`, `help-me-finish`), surfaced as status cards rather than memorized commands; intent naming, flat grouping, moderate merge, status-card discoverability, suggestion-heavy not auto-heavy, alias migration. **[naming, grouping, discoverability, automation]**
- **Checkpoint system**: stop thinking in commands; create 6 checkpoints (`start`, `decide`, `plan`, `build`, `release`, `close`) and have CLI run bundled skills at each checkpoint with optional add-ons; stage naming, pipeline grouping, aggressive merge, automation-by-default, clean break. **[naming, grouping, merge, automation, migration]**
- **Outcome tabs**: organize around artifacts, not actions — `brief`, `options`, `plan`, `code`, `release`, `knowledge`; each tab opens the relevant bundled skills; metaphor/artifact naming, tiered by output, moderate merge, UI discoverability over naming, mixed automation, alias migration. **[naming, grouping, merge, discoverability]**
- **Contrarian: keep names, kill memorization**: retain most existing commands, but make `/status` the mandatory front door that asks one question and dispatches; process change over rename, single router, low merge, router discoverability, high suggestion/auto-trigger, no migration burden. **[grouping, discoverability, automation, migration]**
- **Contrarian: split by risk, not task**: 7 commands named by consequence level (`explore`, `decide`, `commit`, `verify`, `release`, etc.), with governance/QA/review merged into “high-risk checks”; intent/risk naming, flat grouping, aggressive merge, nudge-based discovery, pre-commit automation, clean break. **[naming, grouping, merge, automation, migration]**

## Direction: Question-led menu

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| Implementation-shaped names, separate design micro-skills in main menu, duplicate “refine” concepts | Command count, recall burden, decision friction before doing work | Moment-of-need recognition, discoverability through plain language, automation for obvious background tasks | 8 question-led commands, auto-start bootstrap, auto-pre-ship checks, “did you mean…” nudges from `/status` |

## The Argument
The right move is to rename the surface layer around the user’s questions, not the system’s internals.

The user does not think “I should run debate, then elevate, then refine.” They think: **What should I build? Is this worth doing? What are my options? Is this ready to ship?** The command set should mirror that exact mental state.

### Proposed set
A flat set of **8 memorable commands**:

1. **`/what-next`** — project/session orientation  
   Replaces: `status`, parts of `recall`, `triage`

2. **`/what-build`** — figure out problem, scope, and plan  
   Replaces: `define`, `plan`, `autoplan`, parts of `elevate`

3. **`/is-it-worth-it`** — should we do this at all?  
   Replaces: `challenge`, some `debate`

4. **`/what-are-my-options`** — explore approaches and tradeoffs  
   Replaces: `debate`, `research`

5. **`/make-it-better`** — improve an idea, draft, or plan  
   Replaces: `refine`, `define`’s refine mode

6. **`/is-it-ready`** — quality, compliance, readiness checks  
   Replaces: `review`, `review-x`, `qa`, `governance`, design-review

7. **`/ship-it`** — release with final checks  
   Replaces: `ship`

8. **`/save-it`** — capture decisions and close out  
   Replaces: `capture`, `wrap-session`, `doc-sync`

Then move **rare skills out of the main menu**:
- `setup` stays separate
- `audit` stays separate
- design-heavy tools become an **optional design pack** behind `/design`

### Why now?
Two things changed:
1. You already have a router (`/status`) and an auto-wrapper (`/autoplan`). That means the system is mature enough to support a simpler front door without changing the underlying scripts.
2. The bottleneck is no longer capability; it’s recall. You already use most skills. The problem is retrieval at the right moment.

### What’s the workaround today?
Today the workaround is memory, habit, and accidental rediscovery:
- using `/status` as a partial router
- overusing familiar commands and forgetting others
- manually translating “I need confidence” into “maybe review-x? or qa? or governance?”

That’s expensive cognitive overhead for a solo dev.

### 10x on which axis?
**Recall at the moment of need.**  
Not raw power. Not elegance. The win is: the right command comes to mind instantly.

### Adjacent analogy
This is how consumer software beats expert software. People remember **“Ask AI,” “Share,” “Review changes”** far better than internal-engineering labels. Calendars use “Today” and “Next 7 days,” not “temporal-query-layer.”

## First Move
Create a **one-page alias map** and wire it into help output immediately.

Concretely:
- Add the 8 new command names as top-level aliases
- Mark old names as hidden-but-supported
- Update `/status` so every recommendation uses only the new names
- Auto-run `recall` on session start and bundle it into `/what-next`
- Auto-run baseline `review` checks inside `/ship-it` and suggest `/is-it-ready` before deploy

This affects every session immediately without touching underlying scripts.

## Why This Beats the Alternatives
The obvious approach is to keep the current structure and just pick better names. That fails because the count is still too high and overlaps remain (`define`/`refine`, `qa`/`governance`/`review`).

Another obvious approach is a single mega-router. That reduces memorization, but it makes every action dependent on interrogation by the system. For a solo dev, that adds interaction cost when you already know what you want. You need **a small memorable set**, not only a dispatcher.

Compared with the previous direction’s daily-layer/router model, this is different in mechanism:
- not tiered daily vs specialist
- not verbs like “check/plan”
- not hidden specialist architecture as the primary solution
- instead, a **flat question-led set** optimized for cognitive retrieval

It matches the user’s internal prompt, not workflow stage or system decomposition.

## Biggest Risk
Some question-style names may feel slightly awkward as slash commands.

If the commands feel too conversational or long, adoption drops. The fix is to keep the question framing in product language while allowing tight aliases:
- `/what-build` → alias `/build-what`
- `/is-it-ready` → alias `/ready`
- `/what-next` → alias `/next`

But the core idea must remain: the visible names answer the user’s moment of confusion, not the script author’s architecture.

---

## Direction 3

## Brainstorm
- **State-based workspace modes** — replace skills with 7 persistent work modes like Explore, Decide, Build, Verify, Ship; mode changes determine available commands and auto-runs. **[naming: workflow states; grouping: state machine not list/router; merge: aggressive <10; discoverability: contextual mode affordances; automation: high via mode hooks; migration: deprecation period]**
- **Milestone checklists, not skill names** — organize around concrete deliverables (“Idea Brief”, “Decision Made”, “Ready to Code”, “Ready to Ship”) with each checklist invoking hidden skills. **[naming: artifact/deliverable; grouping: milestone-ordered; merge: aggressive; discoverability: checklist progression; automation: hidden orchestration; migration: aliases then retire]**
- **Trigger-driven invisible automation** — stop asking the user to choose most skills; wire hooks to session start, repo state, branch events, and pre-ship checks so only ~6 explicit commands remain. **[naming: minimal explicit verbs; grouping: explicit vs automatic split; merge: aggressive; discoverability: system nudges + event triggers; automation: very high; migration: clean break for auto paths]**
- **Pinned “Now / Next / Risks” cockpit** — one persistent dashboard command surfaces current state, missing checks, and one-tap actions; skills become recommendations from the cockpit rather than memorized commands. **[naming: status-centric; grouping: dashboard actions; merge: moderate; discoverability: central cockpit; automation: suggested not hidden; migration: aliases]**
- **Role hats** — user switches between Founder, PM, Engineer, Designer, Release Manager; each hat exposes only relevant skills and defaults. **[naming: persona/role-based; grouping: contextual role bundles; merge: moderate; discoverability: role-scoped menus; automation: medium; migration: deprecation period]**
- **Artifact inbox/outbox** — every command operates on named artifacts (problem, options, plan, code, release); user asks “work on plan” or “check release,” system picks underlying skill. **[naming: noun/artifact-based; grouping: artifact lifecycle; merge: moderate; discoverability: artifact prompts; automation: medium-high; migration: aliases]**
- **Contrarian: kill explicit design skills** — fold all four design commands into Plan and Review with a `--design` lens; stop pretending design is a separate command family for a solo dev. **[naming: lens modifiers; grouping: collapsed by lens; merge: very aggressive; discoverability: contextual lenses; automation: medium; migration: clean break]**
- **Contrarian: keep most names, add mandatory exit prompts** — don’t rename heavily; enforce “what do you need next?” after each command to chain to the right next action. **[naming: minimal change; grouping: existing list; merge: light; discoverability: prompted transitions; automation: medium; migration: aliases]**

## Direction: Trigger-driven invisible automation

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| User burden to remember bootstrap/review/wrap commands | Visible command count from 25 to ~8 | Timeliness of the right skill appearing at the right moment | Event hooks for session start, code change, pre-commit, pre-ship |
| Duplicate “which one do I run?” choices | Overlap between QA/governance/review | Trust that routine checks won’t be forgotten | Explicit vs automatic command contract |
| Rarely used standalone design command family | Need to think in pipeline order | Use of /status as a control tower | Nudges tied to repo/project state |

## The Argument
The right fix is not just renaming. The real problem is recall burden. A solo dev should not have to remember 25 commands, especially for routine actions the system can infer.

So restructure the system into **two classes**:

1. **Automatic background skills**: run when events happen.  
2. **Explicit high-agency commands**: only for moments where the user is actually making a decision.

That yields a memorable surface like:

- `/figure-out` — problem framing + options + challenge
- `/plan` — generate implementation plan
- `/improve` — iterative refinement
- `/check` — code/release quality scan
- `/ship` — deploy
- `/research` — deep external research
- `/status` — cockpit and recommendations
- `/setup` — project setup

Everything else becomes hidden orchestration.

**Auto-run candidates**
- `recall` on session start
- `wrap-session` on session end or idle handoff
- `review` on pre-commit or before `/ship`
- `qa` + `governance` as part of `/check` and pre-ship hooks
- `capture` after major plan/decision outputs
- `triage` when input is pasted into inbox or issue intake
- `doc-sync` after `/ship` or merged plan completion
- `status` suggestions after each explicit command

**Merged explicit commands**
- `/figure-out` = define + elevate + challenge + debate modes split into one user-facing “help me decide what to build / what options exist”
- `/check` = review + review-x + qa + governance
- design tools stop being top-level skills; they become flags on `/plan` and `/check` such as `--design`

Why now? Because two things are already true: `/status` already behaves like a router, and `autoplan` already proves hidden orchestration is acceptable. You have evidence the system can coordinate skills behind the scenes. The remaining friction is legacy exposure of too many internals.

What’s the workaround today? The user is manually compensating with memory, habit, and `/status`. They either forget skills exist, overuse familiar ones, or run checks late. That is exactly the work software should remove.

**10x axis:** recall burden. The win is not 20% better naming. The win is cutting the number of things the user must remember by more than half.

**Adjacent analogy:** modern IDEs. Developers no longer manually invoke every formatter, linter, import sorter, and test selector. Good tooling runs some automatically and surfaces the rest only when needed.

## First Move
Define an **explicit/automatic contract** for every existing skill in one table.

Example first pass:
- Auto only: recall, wrap-session, capture, triage, doc-sync
- Auto + explicit via `/check`: review, review-x, qa, governance
- Explicit only: figure-out, plan, improve, research, ship, status, setup
- Fold into flags: design-consultation, design-review, design-shotgun, plan-design-review, audit

Then implement just **three hooks**:
1. session start → `recall`
2. pre-ship → `check` bundle
3. session end → `wrap-session` + `capture`

That produces a real signal quickly: whether usage improves when the user no longer has to remember routine commands.

## Why This Beats the Alternatives
The obvious approach is “rename the 25 commands into 12 nicer names.” That helps a bit, but it still assumes the user should remember and choose from a command catalog. That premise is wrong for routine steps.

It also beats the previous directions:
- It is **not** a router/menu model. The user is not being asked better questions to find the right tool.
- It is **not** a daily-layer/specialist hierarchy. There is no primary navigation taxonomy to memorize.
- It changes the mechanism from **selection** to **automation**.

For this user, the biggest misses are not obscure edge cases; they’re recurring tasks like recall, review, capture, and governance. Those should happen because the workflow reached the right trigger, not because the user remembered a noun.

## Biggest Risk
Over-automation erodes trust if hooks fire at the wrong time or feel opaque. If the user can’t predict why a check ran, or hidden orchestration feels slow/noisy, they’ll disable it and you lose the benefit. The contract must be explicit: what runs automatically, when, and how to skip it.

---

## Direction 4

## Brainstorm
- **Delete the skill layer entirely; keep only `/status` + a few irreversible actions** — the question is wrong because memorability is a symptom of over-exposed internals, not a naming problem. **[Naming: anti-naming/minimal; Grouping: single entry + tiny explicit set; Merge: ultra-aggressive; Discoverability: router only; Automation: high; Migration: clean break]**
- **Make skills invisible defaults attached to lifecycle events** — the question is wrong because “choosing the right skill” should not be a user task for bootstrap/review/capture/sync. **[Naming: event-based; Grouping: lifecycle hooks; Merge: aggressive; Discoverability: contextual nudges only; Automation: dominant; Migration: deprecate command use]**
- **Replace commands with 5 “jobs to be done” workspaces, not skills** — the question is wrong because the unit of memory should be outcome bundles (“figure out what to build”, “get this ready to ship”), not individual tools. **[Naming: JTBD; Grouping: workspace bundles; Merge: aggressive; Discoverability: enter workspace then guided flow; Automation: medium; Migration: clean break]**
- **Stop restructuring commands; build a commander that interprets plain English intents** — the question is wrong because users should say “is this ready?” and never learn command names. **[Naming: natural language; Grouping: none/user intent parsing; Merge: irrelevant at surface; Discoverability: language examples; Automation: medium-high; Migration: aliases forever]**
- **Expose only project states, not tools: Idea / Decision / Build / Release / Learn** — the question is wrong because users remember where the project is, not what helper exists. **[Naming: workflow-state; Grouping: state machine; Merge: aggressive; Discoverability: next-state prompts; Automation: medium; Migration: clean break]**
- **Charge a “manual invocation tax”: if a skill can be safely inferred, ban direct use** — the question is wrong because optionality created the confusion. **[Naming: reduced surface; Grouping: explicit-only for risky actions; Merge: high; Discoverability: none for hidden ops; Automation: very high; Migration: hard deprecation]**
- **Keep all 25 scripts but expose a personalized top-7 based on actual usage telemetry** — the question is wrong because there is no universally memorable set; the right set is user-specific. **[Naming: personalized; Grouping: adaptive shortlist; Merge: low underneath/high at surface; Discoverability: adaptive suggestions; Automation: low-medium; Migration: aliases + adaptive hide/show]**
- **Split the system by certainty level: Explore / Decide / Execute / Verify / Record** — the question is wrong because the real mental model is uncertainty management, not feature taxonomy. **[Naming: cognitive state; Grouping: 5 buckets; Merge: moderate; Discoverability: state-based prompts; Automation: medium; Migration: deprecation period]**

## Direction: Delete the skill layer; keep one command and a few irreversible actions

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| Most user-facing skill names, duplicate wrappers, manual bootstrap/review/capture choices | Command count, memorization burden, mode confusion, “which one now?” moments | Confidence, default guidance, consistency of use, use of forgotten capabilities | One primary entrypoint (`/status` or `/work`), a tiny set of explicit irreversible commands, event-driven automations |

## The Argument
The question is wrong because **you do not actually need a smaller memorable set of commands**. You need **fewer moments where the user must think about commands at all**.

Three ways the premise is wrong:

1. **The question is wrong because naming is not the root problem.**  
   The user forgets skills because too many internal steps are exposed. Better names help at the margins, but they do not solve “I have to pick from a tool catalog.”

2. **The question is wrong because command choice should not sit with the user for routine work.**  
   `/recall`, `/review`, `/capture`, `/doc-sync`, parts of `/qa` are system responsibilities. Asking a solo dev to remember these is avoidable cognitive load.

3. **The question is wrong because “smaller set” still preserves the wrong interface.**  
   Even 8–10 commands means learning taxonomy. The real mental model is: *where am I stuck and what outcome do I need?* That is better served by a single orchestrator.

So the right move is not “rename 25 into 12.” It is:

- **One primary entrypoint:** `/status` becomes the default working surface.
- **A very small explicit set for high-agency or irreversible actions only:** e.g. `/ship`, `/setup`, `/research`, maybe `/audit`.
- **Everything else becomes router-selected or auto-run.**

Concrete mapping:
- Auto-run on session start: `recall`
- Auto-suggest when ambiguity is high: define/elevate/challenge/debate cluster
- Auto-run before ship / pre-commit / PR-like checkpoints: review, qa, governance
- Auto-run on session end: capture, wrap-session, doc-sync
- Hidden specialist branch only when design-heavy work is detected: design-* tools
- `autoplan` absorbs plan/refine debate-selection logic instead of sitting beside them

What changed now? Two things:
- `/status` already exists as a router. The infrastructure for orchestration is already there.
- You already know which skills are strong candidates for automation and which are rare specialists. That makes simplification practical now, not speculative.

What’s the workaround today? The user manually remembers a private taxonomy, relies on habit, and underuses tools that don’t match moment-of-need language. That is exactly the behavior you want to eliminate.

10x axis: **cognitive overhead reduction**.  
Not “slightly better discoverability”; a drastic cut in decisions per session.

Adjacent analogy: modern IDEs. Good IDEs stopped making users manually invoke every formatter, linter, indexer, and refactor helper. They run the routine checks automatically and expose only meaningful decisions.

## First Move
**First concrete action:** redefine the public surface into two categories this week:

1. **Primary command:** `/status`  
   It accepts plain-language intents (“help me figure out what to build”, “is this code ready?”, “what are my options?”) and routes.

2. **Explicit commands only for irreversible or uncommon actions:**  
   `/ship`, `/setup`, `/research`, `/audit`, plus maybe `/design` as a single specialist umbrella.

Then hide the rest from the visible command list but keep them as internal aliases/scripts. That immediately tests the core bet: does removing the catalog reduce hesitation?

## Why This Beats the Alternatives
The obvious approach is to rename and merge into 8–12 commands. That is cleaner, but it still assumes the user should browse a command architecture. They should not.

Why this beats the previous directions:
- It is **not a better menu**.
- It is **not another intent router layer on top of many commands**.
- It is **not trigger-driven invisible automation as a supplement**.
- It is a **surface-area collapse**: most skills stop being product features.

That matters because the failure mode is not bad labels alone; it is exposing too many decisions. Any approach that preserves “pick the right command” preserves the core burden.

## Biggest Risk
The biggest risk is **loss of trust in the router**.  
If `/status` misroutes or feels opaque, the user will want the old explicit commands back. This dies if the orchestrator is not reliably better than manual choice.

---

## Synthesis

## The Fork

The real choice is **Bet A: Intent Layer** vs **Bet B: Automate the Routine** vs **Bet C: One Front Door**.

## Bet A: Intent Layer
Keep commands, but rename and merge them around the user’s moment of need. This is the direct answer: a small, memorable surface without rewriting the operating model. Use 6–8 explicit commands like `/next`, `/plan`, `/check`, `/ship`, plus a hidden specialist tier. `/status` recommends these names, but users still have stable handles they can learn. This works because it fixes recall while preserving autonomy and existing scripts. It’s the least disruptive path and the easiest to test quickly.
**First move:** Add an alias layer next week: six top-level intent commands mapped onto current skills; update `/status` and help to recommend only the new names; keep old commands as advanced aliases.
**Sacrifice:** You keep a command taxonomy. Recall improves, but you still ask the user to choose from a menu, and overlap may persist in umbrella commands like `/check`.

## Bet B: Automate the Routine
Stop treating all skills as things the user should remember. Split the system into explicit high-agency commands and automatic background actions triggered by hooks. Keep only a few manual commands such as `/figure-out`, `/plan`, `/check`, `/ship`, `/research`, `/status`; auto-run recall at session start, check bundles before ship, and capture/wrap at session end. This differs from Bet A because the mechanism is automation, not better naming. It works if most misses are routine steps users forget, not strategic moments they need named handles for.
**First move:** Create one table classifying every existing skill as auto-only, auto-plus-explicit, explicit-only, or folded into another command; implement three hooks: session start, pre-ship, session end.
**Sacrifice:** You give up some user control and transparency. The surface is simpler, but trust now depends on predictable hooks and clear skip/override rules.

## Bet C: One Front Door
Challenge the premise: don’t create a smaller command set; collapse the visible surface to a single router plus a few irreversible actions. `/status` becomes the mandatory front door, accepts plain-language intent, routes to hidden scripts, and suggests next actions. Keep only explicit outliers like `/ship`, `/setup`, `/research`, maybe `/audit`. This is the most aggressive consolidation and the clearest rejection of “memorize commands” as the interface. It works if the real problem is exposed internals, not bad names.
**First move:** Hide almost all commands from help, keep them as internal aliases, and make `/status` the default entry for everyday work with natural-language routing and visible reasoning.
**Sacrifice:** You abandon stable command handles and expert muscle memory. If routing is wrong or opaque, users lose confidence and the whole interface feels less controllable.

## Comparison

| | Timeline | Risk | What you learn | Strategic sacrifice |
|---|----------|------|----------------|---------------------|
| **Bet A** | 1–2 weeks to ship aliases/help updates; another 2–4 weeks of usage to know if recall improves | Users may find umbrella names vague; specialists may remain hidden too well | Whether a smaller intent-based vocabulary materially improves retrieval without changing behavior patterns | You commit to commands as the primary interface, limiting how far you can simplify later |
| **Bet B** | 1 week for policy table, 1–3 weeks for core hooks; 2–6 weeks to see if missed routine steps drop | Bad timing, noisy hooks, or opaque automation can erode trust fast | Which skills are truly routine enough to automate and where users still want manual control | You give up some explicitness and future portability to non-hooked environments |
| **Bet C** | Unknown — depends on router quality, natural-language reliability, and confidence in orchestration | Misrouting or opacity makes the system feel uncontrollable; fallback paths may re-expand the surface | Whether users actually prefer intent routing over command recall altogether | You give up the product shape of a command system and make the router the core dependency |
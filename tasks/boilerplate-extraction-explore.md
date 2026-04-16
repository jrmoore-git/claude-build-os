---
mode: explore
created: 2026-04-16T13:09:29-0700
model: gpt-5.4
directions: 4
prompt_versions: explore=3, diverge=4, synthesis=4
---
# Explore: Should we extract duplicated boilerplate (Interactive Question Protocol, Safety 

## Direction 1

## Brainstorm
- Extract only the high-confidence procedural duplicates into shared files: Interactive Question Protocol and maybe Completion Status, while leaving Safety Rules and OUTPUT SILENCE inline.
- Do a strict partial extraction: shared generic Safety Rules plus per-skill “delta” prohibitions appended locally, and test whether the split preserves enforcement.
- Don’t extract anything yet; treat the measured 120 cleanly extractable lines and ~3K token savings as too marginal to justify new failure modes.
- Invert the project: instead of shared reference files, generate skills from canonical templates at build time so runtime prompts stay fully inline.
- Move only authoring duplication, not execution duplication: create a source-of-truth boilerplate library for maintainers, but compile expanded skill files for the model.
- Make OUTPUT SILENCE more local, not more shared: duplicate it intentionally at every action point because it is the most violated rule and proximity matters more than elegance.
- Split skills into two classes—procedural skills that can reference shared protocols and judgment/safety-heavy skills that must remain monolithic—and stop pretending one mechanism should fit all 22.
- Reframe the question entirely: the problem is not duplicated text but unreliable rule salience, so invest in violation-resistant prompt placement and tests rather than token shaving.
- Use extraction as a test harness strategy, not an optimization strategy: centralize only blocks where you want synchronized behavior changes and measurable regression coverage.
- Take the uncomfortable route and add some duplication back on purpose, because repeated local constraints may be cheaper than one safety regression.

## Direction: Compile shared sources, keep runtime prompts inline

## The Argument
The right move is **not runtime shared reference files**. It is **build-time deduplication**: create canonical shared source blocks for maintainers, then compile them into fully expanded skill prompts at deploy time.

This is the most interesting direction because it changes the problem from “can the model reliably dereference shared instructions?” to “can humans stop maintaining boilerplate in 22 places without changing model behavior?” That is the real win.

### Why now?
Two things are true today that make this the right move now and not two years ago.

First, you now have **measured duplication data** rather than a hunch: only ~120 lines are cleanly extractable, OUTPUT SILENCE is already fragile, and Safety Rules are mixed with non-extractable skill-specific prohibitions. That evidence kills the fantasy of broad runtime modularization.

Second, you now have **mode-split evidence**: read-then-follow works for simple procedures, but conditional branching already failed in /design. That means the current models are good enough to support modular authoring workflows, but not reliable enough to justify moving salient runtime constraints further from the action point. The technology is sufficient for a build system, not sufficient for aggressive prompt indirection.

### What’s the workaround today?
The current workaround is obvious and revealing: **manual copy-paste boilerplate across skills**. That proves there is real demand for consistency, but it also reveals the non-negotiable constraint: teams have preferred duplication over indirection because local visibility preserves behavior. In other words, people are already telling you what matters more than elegance.

### Moment of abandonment
People will abandon runtime extraction the moment they hit a regression that is hard to reason about:
- OUTPUT SILENCE violations rise because the rule is no longer adjacent.
- A skill-specific prohibition gets weakened by being split from its generic wrapper.
- A conditional protocol branches incorrectly because the executor treats shared instructions as advisory context instead of immediate constraints.

That abandonment point is not theoretical; you already saw it in T3. Design backward from that failure: preserve runtime locality.

### 10x on which axis?
This is **10x better on maintainability per unit of behavioral risk**.

Not better overall. Not more elegant. Specifically: you get one canonical place to edit common protocols, but the model still sees the same fully inlined prompts. That is the only axis where a decisive win exists here.

### Adjacent analogy
This is how **front-end asset pipelines** and **infrastructure-as-code templating** won: engineers stopped hand-editing repeated artifacts, but production still receives flattened, explicit outputs. Browsers don’t import your design-system source files at runtime; they get compiled bundles. Same mechanism here: abstract for authors, expand for execution.

### What changes
- Shared source blocks become a maintainer tool, not an inference-time dependency.
- Runtime prompts remain explicit, local, and debuggable.
- Extraction scope is broad in source, conservative at runtime.

This differs from the obvious options on approach, tradeoff, and success criteria. The goal is not token savings. The goal is **authoring consistency without safety regressions**.

## First Move
Next week, implement a tiny build step for exactly two blocks:
1. **Interactive Question Protocol**
2. **Completion Status Protocol**

Create canonical source snippets and per-skill includes, then compile them into the existing skill files so deployed prompts remain expanded text. Do **not** touch Safety Rules or OUTPUT SILENCE. Success criterion: zero runtime behavior change in regression tests, plus one-edit propagation across all affected skills.

## Why This Beats the Alternatives
**Full runtime extraction** is the obvious idea, but it optimizes the wrong thing. ~3K tokens per multi-skill session is marginal, while the failure mode is safety and compliance drift.

**Partial runtime extraction** of “safe” blocks still creates two systems to reason about: local and referenced. That increases debugging complexity for a token win that barely matters.

**Do nothing** is safer than runtime extraction, but it leaves real maintenance pain untouched. If boilerplate must evolve, copy-paste entropy will keep accumulating.

## Biggest Risk
The biggest risk is that this solves the maintainer problem but not the original V2 optimization goal. If the project is judged purely on runtime token reduction, this will look like a sidestep. It is a sidestep—and the correct one—because the measured savings are too small to justify introducing inference-time indirection.

---

## Direction 2

## Brainstorm
- **Boilerplate linter + dedupe lockfile, no runtime indirection** — keep prompts physically duplicated but enforce canonical text via CI/codegen; differs on **Approach, Tradeoff, Success criteria, Who it affects**
- **Risk-tiered extraction only for low-consequence blocks** — extract Interactive Question Protocol only, ban extraction of OUTPUT SILENCE and mixed Safety Rules; differs on **Scope, Tradeoff, Success criteria**
- **Post-compile prompt assembly from structured fragments** — author in YAML/JSON atoms, generate full skill files before runtime; differs on **Approach, Who it affects, Success criteria**
- **Human process fix: boilerplate owners + change protocol** — no architectural change; assign owners and mandatory synchronized edits across affected skills; differs on **Approach, Who it affects, Tradeoff**
- **Model-behavior regression gate instead of source dedupe** — optimize for violation rate and task accuracy, not source cleanliness; differs on **Success criteria, Tradeoff, Scope**
- **Delete weakly valuable protocols rather than centralize them** — prune Completion Status and abbreviated Interactive Question variants where not essential; differs on **Approach, Scope, Tradeoff** *(contrarian)*
- **Buy the problem away with prompt-management tooling** — use an external prompt CMS/templates system for authoring/versioning, then export flat skills; differs on **Approach, Who it affects, Tradeoff** *(contrarian)*

## Direction: Boilerplate linter + dedupe lockfile, no runtime indirection

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| Runtime shared-reference lookup | Prompt drift across duplicated blocks | Safety fidelity at point of action | Canonical block registry + CI enforcement |
| Debates about partial extraction boundaries | Manual multi-file editing burden | Confidence in exact wording consistency | Auto-fix/codegen sync command |
| Need to trust read-then-follow for sensitive rules | Incentive to over-extract marginal savings | Measurable prompt hygiene | Drift reports by block and skill |

## The Argument
Do **not** move these blocks into shared reference files at runtime. Keep each skill self-contained, and solve the real problem — maintenance drift — with a build/process mechanism instead.

Why now? Because the new measurements changed the economics. You now know only ~120 lines are cleanly extractable, worth about ~3K tokens per multi-skill session, while the known risks are concentrated exactly in the most sensitive areas: mixed Safety Rules and already-fragile OUTPUT SILENCE. The /design spike proved read-then-follow can work for straightforward procedures, but it also exposed the failure mode you should care about: conditional behavior drift at execution time. That is a bad trade for marginal savings.

What’s the workaround today? People are manually copying boilerplate across skills and hoping edits stay synchronized. That creates two problems: inconsistent text over time and high edit overhead. A linter/lockfile approach fixes both without changing runtime behavior.

Mechanism:
- Define canonical boilerplate blocks in a registry in the repo.
- Annotate each skill file with markers for blocks that must match canonical text exactly or with approved local overrides.
- Add a CI check that detects drift and fails the build if a duplicated block no longer matches its canonical version.
- Add an autofix command that rewrites skill files from the registry.

This is structurally different from extraction. It optimizes for **authoring consistency**, not **runtime token reduction**. That is the right axis because the savings are marginal and the risk is operational.

10x axis: **Reliability of instruction enforcement**, not tokens.

Adjacent analogy: this is how teams manage generated API clients, SQL schemas, and protobufs. They don’t ask production to “reference shared definitions live”; they generate flat artifacts and enforce consistency in build tooling. Sensitive systems prefer expansion before execution.

Success criteria:
1. Zero runtime changes in skill behavior from dedupe work alone.
2. Drift across repeated boilerplate blocks falls to near-zero.
3. Editing a canonical block updates all intended skills in one command.
4. No increase in OUTPUT SILENCE or safety violations because wording remains local at point of use.

## First Move
Inventory the **safe canonical set** and wire one CI check.

Concretely:
1. Create `boilerplate_registry` with only the clearly repetitive, low-risk blocks first: Interactive Question Protocol and OUTPUT SILENCE text as they exist today.
2. Add per-skill annotations like `BEGIN CANONICAL:interactive_question_protocol`.
3. Write a script that compares annotated sections against the registry and prints exact diffs.
4. Run it once to produce a drift report across all 22 skills.

That first move gives you a decision signal immediately: how much duplicated text is truly stable enough to govern centrally without touching runtime behavior.

## Why This Beats the Alternatives
The obvious approach — shared reference files at runtime — optimizes the wrong thing. You save only ~3K tokens in multi-skill sessions after already saving ~43K in V1, but you increase dependence on the model correctly retrieving and applying distant instructions. Your own evidence says that breaks first on conditional or easy-to-forget behaviors. OUTPUT SILENCE is already the most violated rule; moving it away is reckless.

A selective extraction approach is safer than full extraction, but it still inherits the runtime indirection risk and creates two instruction classes: local and referenced. That increases cognitive complexity for a small payoff.

This also beats “just leave it alone.” Doing nothing preserves safety, but it preserves drift and editing pain. The linter/lockfile approach captures most maintenance benefits with effectively none of the runtime downside.

And it is fundamentally different from compiling shared sources for runtime use: the artifact the model sees remains a flat, self-contained skill file. No read-then-follow dependency is introduced.

## Biggest Risk
The team may over-engineer the tooling relative to the size of the problem. If the registry, annotations, and autofix flow become harder to maintain than the duplicated text itself, you’ve added process weight without enough payoff. The discipline here is strict: keep it to a tiny registry, a simple diff check, and flat generated output.

---

## Direction 3

## Brainstorm
- **Adopt a “duplication budget” and leave prompts inline unless measured drift exceeds a threshold** — [Approach, Tradeoff, Success criteria, Who it affects]
- **Build a prompt conformance test harness that rewrites nothing, but flags boilerplate divergence and rule placement regressions** — [Approach, Scope, Success criteria]
- **Split governance from runtime: maintain a canonical policy spec + generated review diffs, but keep shipped skill files fully expanded** — [Approach, Tradeoff, Who it affects, Success criteria]
- **Outsource consistency to a prompt registry/CMS workflow with approval gates instead of code-level extraction** — [Approach, Who it affects, Tradeoff]
- **Eliminate most candidate boilerplate by deleting low-value protocols rather than sharing them** — [Approach, Scope, Tradeoff] *(contrarian)*
- **Localize only authoring-time templates: snippets/macros in the editor, no runtime/shared-file dependency at all** — [Approach, Scope, Success criteria]
- **Create a rule proximity policy: duplicate critical rules on purpose, centralize only non-critical prose in docs** — [Approach, Tradeoff, Success criteria] *(contrarian)*

## Direction: Split governance from runtime

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| manual hunt-for-differences across 22 skills | authoring inconsistency and accidental drift | reviewability of shared policy changes | a canonical policy spec that generates comparison diffs against skill files |
| runtime dependency on shared reference files | debate about partial extraction at execution time | confidence that safety-critical rules stay local | a “governance pipeline” separate from runtime prompts |

## The Argument
Do **not** move these blocks into shared runtime reference files. Instead, create a **canonical source-of-truth for authoring and review**, while keeping each shipped skill self-contained.

This is the right direction because the evidence says the core problem is **maintenance drift**, not runtime capability. The measured upside of extraction is small: ~120 lines, ~3K tokens per multi-skill session, versus 43K already captured in V1. At the same time, the known failure modes hit exactly the wrong places: conditional branching already broke in `/design`, OUTPUT SILENCE is already the most-violated rule, and Safety Rules are partly non-extractable without weakening skill-specific prohibitions.

So accept the premise that duplication is real, but solve it with a different mechanism: **governance tooling, not runtime indirection**.

**Why now?**  
Because you now have enough measured evidence to stop guessing. You know:
- only 44% is cleanly extractable,
- some of the most critical blocks are the least safe to move,
- and the token savings are marginal relative to the risk.

That makes this the right moment to separate two concerns that were previously entangled:
1. **How do we keep 22 skills consistent?**
2. **How do we minimize runtime tokens?**

For this proposal, solve only #1.

**What’s the workaround today?**  
People are manually copying edits across skill files and relying on code review to spot drift. That is slow, error-prone, and exactly why duplicated boilerplate becomes costly over time.

**10x on which axis?**  
**Change safety.** Not token reduction. This gives a much better way to update repeated language without making execution more fragile.

**Adjacent analogy:**  
This is how many teams handle generated API clients or vendored configs: they keep a canonical spec and regenerate or diff outputs, but production artifacts stay explicit and local because runtime clarity beats indirection.

Mechanically:
- Define canonical versions of the extractable blocks for **authoring purposes**.
- Add a tool that checks each skill against those canonical blocks and produces a diff report.
- For blocks that must stay local or near the action point—especially OUTPUT SILENCE and mixed Safety Rules—mark them as **intentionally duplicated** and enforce placement, not extraction.
- Review changes through the canonical spec, then copy/update expanded text into skills.

Success looks like:
- fewer inconsistent boilerplate edits across skills,
- no runtime regression from moved instructions,
- and faster review when shared wording changes.

## First Move
Build a **prompt conformance checker** for the four candidate blocks.

Concrete first action:
1. Create canonical text files for:
   - Interactive Question Protocol
   - OUTPUT SILENCE
   - Completion Status Protocol
2. For Safety Rules, split only into:
   - `generic-safety-guidance` for comparison,
   - plus a required `skill-specific-safety` section that must remain in each skill.
3. Run the checker across all 22 skills and output:
   - exact matches,
   - near matches,
   - intentionally local exceptions,
   - placement warnings for OUTPUT SILENCE.

This affects prompt authors and reviewers immediately, without changing runtime behavior at all.

## Why This Beats the Alternatives
The obvious approach—shared reference files at runtime—optimizes the wrong thing. It saves a marginal number of tokens while increasing instruction distance, which is already risky for OUTPUT SILENCE and conditional procedures.

Compared with the previous directions:
- It does **not** compile shared sources into runtime prompts.
- It does **not** focus on boilerplate lint + lockfile as the primary artifact.

Instead, it changes the operating model: **centralize policy for humans and tooling, decentralize execution for the model**.

That is structurally different and better aligned with your evidence:
- self-contained prompts preserve safety fidelity,
- canonical governance reduces maintenance pain,
- and review diffs give you a clean decision signal on whether future extraction is worth it.

## Biggest Risk
The team may see this as “extra tooling without token savings” and reject it as overhead.

If that happens, it dies because its value depends on people caring more about **safe consistency** than about the small runtime savings.

---

## Direction 4

## Brainstorm
- **The question is wrong because 3K-token savings is below the threshold of strategic significance; set a minimum-payoff bar and drop this work.** [Approach, Tradeoff, Success criteria, Who it affects]
- **The question is wrong because duplication is not the core problem; rule violations are. Optimize for compliance telemetry on OUTPUT SILENCE and conditional procedures instead of deduping text.** [Approach, Scope, Success criteria]
- **The question is wrong because “shared reference files” assumes prompts are the unit of improvement; the real unit is behavior. Replace extraction work with eval-driven acceptance gates for each skill.** [Approach, Scope, Tradeoff, Success criteria]
- **The question is wrong because the mixed safety rules prove these blocks are not boilerplate in the only place that matters. Freeze safety text entirely and only edit skills with demonstrated failure modes.** [Approach, Scope, Tradeoff]
- **The question is wrong because centralization increases distance from the action point for already-violated rules. Intentionally duplicate critical rules and treat repetition as a control, not waste.** [Approach, Tradeoff, Success criteria]
- **The question is wrong because maintainability concerns are overstated at 22 skills / 272 lines; use a human checklist for synchronized edits and spend engineering time elsewhere.** [Approach, Who it affects, Success criteria]
- **The question is wrong because “extract or not” is a false binary; retire low-value protocols entirely unless they change measured outcomes.** [Approach, Scope, Tradeoff]
- **The question is wrong because this is premature optimization driven by visible duplication rather than observed cost; require a defect or latency justification before any refactor.** [Approach, Success criteria, Tradeoff]

## Direction: Don’t extract; impose a “measured-benefit or no-refactor” bar

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| shared-reference extraction work for now | prompt refactoring churn | evidence bar for prompt architecture changes | a refactor admission policy tied to token, fidelity, and violation metrics |

## The Argument
Do not extract duplicated boilerplate into shared reference files now. The question is wrong because:

1. **The question is wrong because it treats visible duplication as a problem by itself.** Your own data says only ~120 lines are safely extractable, worth about **~3K tokens per multi-skill session** after a prior optimization already saved **43K**. That is marginal by any reasonable standard.

2. **The question is wrong because it assumes centralization improves the system.** Your evidence says the opposite for the risky parts: **OUTPUT SILENCE is already the most-violated rule**, and moving it farther from the action point likely worsens adherence.

3. **The question is wrong because it frames “shared reference files” as a cleanliness win when the real constraints are behavioral fidelity and safety.** The safety blocks are mixed with skill-specific prohibitions that **cannot be extracted without losing enforcement**. That means the highest-stakes duplication is not actually clean boilerplate.

4. **The question is wrong because a 4/5 spike is not validation for this use case.** The failed test was exactly the kind of thing that matters here: **conditional branching drift**. Re-asking the initial question and adding extra formatting are not cosmetic failures; they show reference-following can mutate execution.

**Why now?**  
Because the new measurements changed the answer. Before measurement, extraction looked plausible. Now you know the extractable portion is small, the risky portion is the safety-critical portion, and the most-violated rule would likely get weaker if centralized. The right response to new evidence is to stop.

**What’s the workaround?**  
The workaround is the current system: keep duplicated text where it anchors behavior, and update it manually when needed. At this scale—22 skills, 272 lines total—that is not a crisis. It is cheaper than introducing indirection that weakens compliance.

**10x on which axis?**  
**Decision quality.** Not token savings. A hard evidence bar prevents low-yield refactors from stealing time from higher-return work.

**Adjacent analogy:**  
In safety-critical systems, redundancy is often intentional. Pilots don’t remove repeated checklist items because they look duplicated; repetition near the point of action is a control. OUTPUT SILENCE and skill-specific prohibitions look more like checklist controls than like reusable library code.

## First Move
Write and adopt a one-page **Prompt Refactor Admission Rule** in CLAUDE.md:

A prompt-structure change is only allowed if it shows, in measurement:
- meaningful token savings relative to current baseline,
- no drop in safety-rule fidelity,
- no increase in OUTPUT SILENCE violations,
- no new branching/procedure regressions in evals.

Then close Proposal 3 unless someone can produce evidence that exceeds that bar. After that, redirect effort to the actual observed failure modes: OUTPUT SILENCE adherence and conditional branching behavior.

## Why This Beats the Alternatives
The obvious approach—extract the clean 44%—optimizes for neatness, not outcome. You save a small amount of context while increasing indirection and risking compliance on already-fragile rules.

Previous directions all accept the premise that duplicated boilerplate should be structurally reorganized. That is the wrong starting point. The measured evidence says:
- the savings are small,
- the risky content is the important content,
- the spike failed on a behavior pattern relevant to this exact change.

So the best option is not a different extraction pattern. It is **not doing the refactor**.

This beats:
- **Compiling or centralizing sources:** still adds indirection for marginal gain.
- **Linting/dedupe machinery:** creates process overhead around a non-problem.
- **Governance/runtime splits:** elegant on paper, but still built on the false premise that this duplication should be removed.

## Biggest Risk
The main risk is cultural: the team may confuse “don’t refactor” with “accept prompt mess forever.” This only works if you pair the decision with a strict rule that future prompt architecture changes must clear an evidence bar. Without that discipline, you get neither cleanliness nor focus.

---

## Synthesis

## The Fork

The real choice is [Bet A: Selective Runtime Extraction] vs [Bet B: Authoring-Time Compilation] vs [Bet C: No Refactor, Raise the Evidence Bar].

## Bet A: Selective Runtime Extraction
Extract only the safest procedural boilerplate into shared runtime references: Interactive Question Protocol and possibly Completion Status. Keep OUTPUT SILENCE and mixed Safety Rules inline. This is the obvious path because it captures the real, measured duplication while limiting blast radius. It works if you treat extraction as narrow infrastructure, not a sweeping prompt architecture change, and validate with regression tests on the affected skills. The upside is modest token savings plus simpler synchronized edits; the key is disciplined scope. If runtime references can survive on low-consequence procedural text, you get evidence for where modular prompts are viable without betting safety-critical behavior on indirection.
**First move:** Extract Interactive Question Protocol in 2–3 low-risk skills and run behavior regressions.
**Sacrifice:** You accept a two-class prompt system—some rules local, some referenced—which makes prompts less uniform and debugging more complex.

## Bet B: Authoring-Time Compilation
Keep runtime prompts fully inline, but stop maintaining boilerplate by hand. Create canonical shared source blocks for maintainers, then compile expanded skill files at build time. This wins on maintainability without changing model behavior, which matters because the measured savings are small and the risky blocks are exactly the ones that should stay adjacent to the action. It works because it separates human abstraction from model execution: authors edit once, the model still sees explicit local text. Start with the clearly repetitive procedural blocks, not Safety Rules or OUTPUT SILENCE. Success is one-edit propagation with zero behavior change in evals.
**First move:** Build a tiny compile step for Interactive Question Protocol and Completion Status, generating unchanged flat skill files.
**Sacrifice:** You give up most runtime token savings and sidestep the original optimization goal in favor of safer maintenance.

## Bet C: No Refactor, Raise the Evidence Bar
Don’t extract or restructure now. The measured upside—about 120 lines and ~3K tokens per multi-skill session—is too small to justify new failure modes, especially when OUTPUT SILENCE is already fragile and conditional branching already regressed. This bet challenges the premise: duplication is not the problem; behavior fidelity is. It works if you impose a hard admission rule for prompt-architecture changes: no refactor without meaningful token savings, no safety regressions, and no increase in violations. Redirect effort to evals, telemetry, and fixing actual failure modes instead of tidying prompts.
**First move:** Adopt a prompt-refactor policy requiring measured payoff and regression-free evals before any structural change.
**Sacrifice:** You keep manual duplication and drift risk, and forgo maintainability improvements unless the problem gets worse.

## Comparison

| | Timeline | Risk | What you learn | Strategic sacrifice |
|---|----------|------|----------------|---------------------|
| **Bet A** | 1–2 weeks for a small pilot; grounded because only 1 protocol and a few low-risk skills change | Runtime indirection may weaken adherence or branch handling even in “safe” blocks | Whether models can reliably follow referenced procedural text in production-like skills | Simplicity of fully self-contained prompts; you commit to a hybrid architecture |
| **Bet B** | 1 week for a minimal build step; grounded because runtime behavior should remain unchanged | Tooling overhead or bad generation workflow could outweigh maintenance benefit | How much maintainability gain you can get without any behavior change | Most token-reduction upside; you optimize authoring, not inference |
| **Bet C** | Immediate policy decision; 1–2 weeks to define eval gates if absent | Team may underinvest in prompt hygiene and let drift accumulate | Whether the duplication problem is actually costly enough to justify future refactor | Maintainability improvements and any near-term structural cleanup optionality |
---
mode: explore
created: 2026-04-15T09:57:44-0700
model: gpt-5.4
directions: 4
prompt_versions: explore=3, diverge=4, synthesis=4
---
# Explore: How should BuildOS implement generalized AI user simulation (V2-V3 of /simulate)

## Direction 1

## Brainstorm
- Build a hybrid simulation harness with a fixed seed library of 5–10 high-fidelity personas plus OCEAN-based perturbations, auto-generated rubrics from each SKILL.md, and a standard converge-on-consensus loop.
- Generalize eval_intake.py into a reusable three-agent pipeline: executor, persona, judge, with transcript memory and a stopping rule based on score stability across scenarios.
- Create a skill ontology first: classify the 22 skills into a few interaction archetypes, then attach archetype-specific persona templates, rubric dimensions, and turn policies.
- Flip the problem: don’t simulate “users” first, simulate “failure modes” first, generating adversarial conversational conditions that expose where each skill breaks.
- Make V2 a “state-machine simulator,” not a chat simulator: each persona is defined by hidden goals, knowledge, patience, and constraints, and natural language is just a rendering layer over explicit state transitions.
- Use DPRF continuously: every real user transcript becomes training data that mutates persona generators and rubric weights, so simulation quality compounds over time instead of relying on a static library.
- Take the uncomfortable path and require a human only at the disagreement boundary: fully automate everything except cases where cross-model judges diverge or score deltas are decision-relevant.
- Abandon per-skill evaluation entirely and instead evaluate whether each skill preserves user momentum, trust, and task progress—three universal outcome metrics across all skills.
- Use small specialist models for persona enactment and larger models only for synthesis/judging, optimizing for simulation volume rather than maximal single-run realism.
- Treat /simulate as a compiler: parse SKILL.md into an intermediate representation with goals, required inputs, decision points, and failure conditions, then generate personas, scenarios, and rubrics from that IR.

## Direction: Compile skills into interaction state-machines, then simulate hidden-user-state—not just chat

## The Argument
The most interesting direction is to stop treating simulation as “prompt a fake user and see what happens” and instead build a **skill compiler** that turns each SKILL.md into an **interaction model**: required information, branch points, expected user responses, risk points, and success criteria. Then drive simulation with personas that have **hidden state**—goals, knowledge, constraints, patience, trust, and communication style—and let language be the surface expression of that state.

This is the right direction because the hard problem in BuildOS is not generating plausible dialogue. Models already do that. The hard problem is **multi-turn consistency and transferable evaluation across 22+ skills without manual setup**. A state-based architecture solves both. It gives the persona memory and behavioral coherence across turns, and it gives the judge something more objective than vibes: did the skill move hidden user state in the right direction?

**Why now?** Two things changed. First, LLMs are now good enough at structured extraction to reliably parse SKILL.md into intermediate representations—decision points, asks, outputs, stop conditions. Two years ago, this would have required brittle manual schemas. Second, cross-model orchestration is now practical and cheap enough that you can separate executor, persona, and judge at scale, which is essential to avoid leakage and sycophancy. The architecture is finally feasible.

**What’s the workaround today?** Teams either wait for real users, manually roleplay scenarios, or write narrow hand-authored evals for one skill at a time. BuildOS itself proved this with eval_intake.py: it worked, but only through 17 rounds of bespoke setup, hand-crafted personas, and manual interpretation. That is real demand disguised as toil.

**Moment of abandonment:** people quit when simulation becomes another form of manual QA. The failure point is not “the model isn’t smart enough”; it’s “every new skill requires custom persona writing, custom rubrics, and babysitting multi-turn runs.” Design backward from that. The simulator must auto-bootstrap from SKILL.md and only ask for human input when uncertainty is high.

**10x on which axis?** **Coverage per unit setup time.** Not realism overall—setup compression. A state-machine compiler lets one architecture generalize across many skills because the reusable unit is the interaction structure, not a bespoke prompt pack.

**Adjacent analogy:** This is how compilers and model-based testing beat handwritten test cases in software engineering. Instead of writing every test manually, you compile source into an intermediate representation, generate cases from branch structure, and validate transitions against expected invariants. The transfer works because skills are effectively conversational programs with latent state and branching logic.

Concretely, V2-V3 should work like this:
1. Parse each SKILL.md into an IR: objective, required user inputs, optional inputs, branch conditions, tool calls, AskUserQuestion moments, and expected outputs.
2. Map the skill to an interaction archetype: intake, diagnosis, planning, critique, prioritization, etc.
3. Generate personas as hidden-state bundles: OCEAN traits plus task goal, domain knowledge, urgency, cooperativeness, ambiguity tolerance, and truthfulness.
4. Run a separated three-agent simulation:
   - **System agent** executes the skill.
   - **Persona agent** responds from hidden state, not rubric knowledge.
   - **Judge agent** scores both transcript quality and state transition quality.
5. Stop when score distributions stabilize across archetypes/persona slices and no new failure modes emerge in N runs.
6. Route only disagreement cases or high-impact regressions to a human.

This also answers fixed vs dynamic personas: use a **hybrid**. Fixed anchor personas for continuity and regression tracking; generated state variations for breadth. Rubrics also become hybrid: universal dimensions from the interaction archetype, plus auto-extracted dimensions from the IR.

## First Move
Next week, build a compiler for 3 representative skills—one intake, one diagnostic, one planning skill. For each, extract:
- required inputs
- decision points
- AskUserQuestion nodes
- success/failure conditions

Then implement one hidden-state persona schema with 8 fields: goal, knowledge, urgency, patience, trust, cooperativeness, verbosity, and ambiguity tolerance. Run 50 simulations per skill with cross-model separation and compare whether failures cluster more usefully than the current transcript-only V1.

## Why This Beats the Alternatives
The obvious hybrid-library approach is too prompt-centric; it improves realism but not generalization. You still handcraft too much.

The “just auto-generate rubrics from SKILL.md” approach misses the real issue: rubrics alone don’t solve multi-turn coherence or natural AskUserQuestion behavior.

The “fully automate chat roleplay” approach produces fluent nonsense. Without hidden state and transition checks, you get plausible transcripts with weak signal and inflated confidence.

## Biggest Risk
The compiler could fail to extract the true interaction logic from messy SKILL.md files, producing a clean but wrong IR. If the parsed structure is wrong, everything downstream looks rigorous while evaluating the wrong thing.

---

## Direction 2

## Brainstorm
- **Trace-mining autopilot:** derive personas, rubrics, and failure modes from past skill transcripts and review artifacts instead of hand-designing a simulation framework. **[Approach, Scope, Success criteria, Who]**
- **Buy the benchmark:** outsource persona realism and judgment quality to an external human-panel / synthetic-data vendor, and use BuildOS only as orchestration + regression tracking. **[Approach, Tradeoff, Who, Scope]**
- **Capability-family templates:** cluster the 22 skills into 5–7 interaction families and generate simulation configs per family rather than per skill or universal generalization. **[Scope, Tradeoff, Success criteria]**
- **Replay + perturbation harness:** start from real or seeded canonical conversations, then mutate user turns, constraints, and objections to create test coverage, instead of generating whole users from scratch. **[Approach, Tradeoff, Success criteria]**
- **Judge-first architecture:** build generalized skill-dimension extraction and transcript scoring first; keep user simulation narrow and use human-authored scenario seeds until scoring is trustworthy. **[Approach, Scope, Tradeoff]**
- **Adversarial red-team market:** route each skill to a pool of specialized challenger agents optimized to break procedures, not emulate average users. **[Approach, Success criteria, Who]** *(contrarian)*
- **Kill full automation at the last mile:** automate simulation generation and scoring, but require human sign-off only on deltas that move the skill policy surface. **[Tradeoff, Who, Success criteria]** *(contrarian)*

## Direction: Replay + perturbation harness

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| Need to invent every user from scratch | Dependence on manual persona authoring | Coverage of realistic edge cases and multi-turn consistency | A conversation mutation engine with transcript-grounded scenario generation |

## The Argument
The right move is to stop treating V2-V3 as a “generalized synthetic human” problem and instead treat it as a **conversation coverage** problem.

Mechanism: Build a harness that starts from a small library of canonical interaction traces per skill-family, then systematically perturbs them: user goals, patience, expertise, answer completeness, objection style, ambiguity, missing context, contradictory answers, and follow-up responsiveness. The agent under test runs against these mutated trajectories; a separate judge scores the resulting transcript on inferred skill dimensions.

This is structurally different from building hidden user-state machines. You are not modeling a full latent human. You are **mutating realistic conversational situations**.

Why now? Two things changed:
1. You already proved manually that transcript-based iteration works (`eval_intake.py`, 17 rounds). That means the missing piece is scalable test generation, not proof of concept.
2. Research says multi-turn consistency requires explicit state tracking and leakage control. Replay-based simulation gives you both naturally: the seed trace carries coherent state, and the mutation layer can be sandboxed away from the skill procedure and rubric.

What’s the workaround today? Teams either wait for real users, or they handcraft a few personas and prompts. Both are slow and brittle. Handcrafted personas look broad but often miss the exact conversational breakdowns that cause skill failures in practice: vague answers, hostile reframing, premature conclusions, inconsistent follow-ups.

How it works:
- **Cluster skills into interaction families**: interview/intake, planning, diagnosis, coaching, synthesis, etc.
- For each family, create **3–5 seed traces** from existing personas or manually authored “golden” runs.
- Build a **mutation engine** that rewrites only the user side and scenario conditions along controlled axes: OCEAN traits, domain expertise, verbosity, cooperativeness, goal clarity, factual consistency, and adversarial pressure.
- Maintain a **turn-level scenario state** separate from the transcript so AskUserQuestion can be answered naturally and consistently.
- Auto-extract provisional rubric dimensions from `SKILL.md` plus judge rationales from prior runs, then have the judge score transcript outcomes against those dimensions.
- Iterate until convergence on **failure discovery rate**, not just average score: stop when N additional perturbation batches stop surfacing materially new failure classes.

10x axis: **coverage per seed conversation**. One good seed should generate dozens of realistic, targeted tests.

Adjacent analogy: This is fuzz testing for conversations. Software teams stopped relying on one handcrafted input and started mutating valid inputs to expose boundary failures. BuildOS should do the same for interactive skills.

## First Move
Take 3 skills that span different interaction families: one intake skill, one advisory skill, one diagnostic skill.

For each:
1. Produce 2 canonical transcripts using your existing cross-model setup.
2. Define 8 mutation knobs on the user side only: expertise, cooperativeness, verbosity, ambiguity, consistency, urgency, skepticism, and goal stability.
3. Implement a mutator that edits the seed scenario state and generates user replies turn-by-turn without seeing the skill procedure or rubric.
4. Run 50 perturbed conversations per skill and cluster judge rationales into repeated failure types.

The first decision signal: do these perturbations surface more unique actionable failure classes per engineer-hour than writing new personas?

## Why This Beats the Alternatives
The obvious approach is a generalized persona generator. That sounds elegant but pushes you into the hardest problem first: robust latent-human simulation across all 22 skills. It is expensive, hard to validate, and easy to overfit.

Manual per-skill rubrics and persona sets do not scale. Full universal automation without seeds will generate broad but shallow tests. Outsourcing the whole problem gives you less control over leakage, iteration speed, and integration with `debate.py`.

Compared with the previous direction, this does not require compiling skills into explicit interaction state-machines or simulating hidden user state as the core artifact. The artifact here is the **seed conversation + mutation space**. State exists, but only to preserve coherence during perturbation. That is a process harness, not a simulation architecture.

## Biggest Risk
If your seed traces are too narrow or too idealized, the mutation engine will produce lots of variants of the same conversation and create a false sense of coverage. The whole approach lives or dies on the diversity and representativeness of the initial seed library.

---

## Direction 3

## Brainstorm
- **Failure taxonomy + metamorphic test generator** — derive skill-agnostic failure modes and auto-generate challenge scenarios/rubrics from them, then score invariants instead of personas. **[Approach, Scope, Success criteria, Tradeoff]**
- **Production trace distillation pipeline** — mine anonymized real skill transcripts into reusable scenario seeds, rubric dimensions, and likely user-response branches; simulation becomes replay-from-distribution rather than persona invention. **[Approach, Who it affects, Success criteria, Scope]**
- **LLM-as-panel calibration market** — run multiple independent judges/persona generators, weight them by historical agreement with human spot-checks, and optimize ensemble calibration instead of a single architecture. **[Approach, Tradeoff, Success criteria, Who it affects]**
- **Skill schema compiler** — require each SKILL.md to compile into a declarative interaction contract (inputs, turn types, success claims, unsafe shortcuts); generate tests/judges from the contract rather than free-form prompt simulation. **[Approach, Scope, Tradeoff, Who it affects]**
- **Human gating at uncertainty spikes** — automate most runs, but route only transcripts with high model disagreement/novel failure clusters to humans; optimize reviewer throughput, not full autonomy. **[Approach, Tradeoff, Who it affects, Success criteria]**
- **Buy the benchmark: external evaluator marketplace** — outsource periodic human+LLM benchmark creation for each skill family, then use internal simulation only for regression against those gold sets. **[Approach, Who it affects, Tradeoff, Scope]**
- **Contrarian: eliminate generalized simulation for half the skills** — split skills into interactive vs procedural; only build rich simulation for true conversational skills, and use static linting/property tests for the rest. **[Scope, Tradeoff, Success criteria, Who it affects]**
- **Contrarian: optimize mutation sensitivity, not human realism** — success is whether the eval catches skill changes that matter, not whether personas “feel real”; benchmark on bug-detection power against known bad skill variants. **[Success criteria, Tradeoff, Approach, Scope]**

## Direction: Production Trace Distillation Pipeline

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| Manual per-skill persona/rubric authoring | Reliance on handcrafted fictional personas as the primary source of truth | Fidelity to actual user language, objections, branching patterns, and failure modes | A transcript mining layer that distills scenario seeds, rubric candidates, and response policies from real usage |

## The Argument
BuildOS should implement V2-V3 around **distilling real usage traces into simulation assets**: scenario seeds, inferred user archetypes, branch libraries for AskUserQuestion turns, and candidate evaluation dimensions. The core mechanism is not “better simulated humans.” It is **learning the test distribution from actual conversations**, then using cross-model simulation to expand and stress it.

**Why now?**  
Three things changed. First, BuildOS already has enough structure—22 skills, SKILL.md procedures, debate.py, and a proven cross-model loop—to operationalize mined assets immediately. Second, the research now supports separation of roles and small specialized models, which makes transcript labeling and response-policy distillation cheap enough to run continuously. Third, the manual eval_intake.py success showed the bottleneck is not raw generation; it is authoring high-quality personas, scenarios, and rubrics. Mining traces removes that authoring bottleneck.

**What’s the workaround today?**  
Today the workaround is a mix of waiting for user feedback, hand-writing personas, and manually inventing rubrics after reading transcripts. That is slow, biased toward memorable edge cases, and impossible to scale across 22+ skills without drift.

### How it works
1. **Instrument every skill interaction** to capture transcript, turn type, tool calls, user edits, abandonment, retries, and downstream accept/reject signals.
2. **Distill transcripts into simulation assets**:
   - cluster users by behavior and language style into archetypes,
   - extract recurring intents/objections/questions,
   - identify branch points for interactive turns,
   - infer quality dimensions from what predicts acceptance, rework, or abandonment.
3. **Compile per-skill-family test packs**:
   - scenario seeds from real starts,
   - response policies for likely user replies,
   - auto-generated rubrics from observed success/failure drivers.
4. **Use cross-model simulation only after this grounding step** to expand coverage: adversarial variants, low-frequency branches, OCEAN perturbations around real archetypes.
5. **Convergence criterion** becomes empirical: stop iterating when new skill versions no longer improve scores on mined high-frequency failures and no longer change outcomes on the top branch clusters.

This resolves the main tensions cleanly:
- **Fixed vs dynamic personas:** neither. Use a **seeded archetype library learned from traces**, refreshed continuously.
- **Manual vs auto rubrics:** infer candidate dimensions from outcomes, then human-review only the top dimensions per skill family.
- **Automated vs HITL:** humans review the mined schema and disputed dimensions, not individual runs.
- **Multi-turn AskUserQuestion:** reply generation comes from **branch libraries distilled from actual user answers**, then generalized by models.

**10x on which axis?**  
**Setup time per skill.** Instead of manually building personas and rubrics for each new skill, BuildOS gets them from observed usage patterns and only asks humans to validate deltas.

**Adjacent analogy:**  
This is how modern self-driving stacks improved: not by hand-authoring every scenario first, but by mining fleet data for disengagements, then turning those into simulation cases and regression suites.

## First Move
Pick **3 high-traffic, interaction-heavy skills** and add a transcript distiller that outputs:
- top 20 user intent clusters,
- top 20 objection/question patterns,
- top branch points after AskUserQuestion,
- candidate quality dimensions correlated with user acceptance/edit distance.

Then compare two eval packs on the same skill revision: one built manually, one built from mined traces. If the mined pack catches at least as many known defects and produces more stable rubric agreement, make it the V2 backbone.

## Why This Beats the Alternatives
The obvious approach is to build a generalized persona engine plus auto-rubric generator from prompts alone. That overfits to what the models imagine users do. It scales elegantly on paper and drifts from reality in practice.

Compared with the previous directions:
- A **state-machine hidden-user simulator** assumes you can model user behavior upfront. This direction assumes user behavior is best **observed**, then abstracted.
- A **replay + perturbation harness** starts from existing cases and mutates them. Useful, but still anchored to explicit examples. This direction builds a **living distribution model**: archetypes, branch frequencies, and rubric signals continuously refreshed from production data.

This is structurally different because the centerpiece is **data distillation**, not simulation architecture or test harness mechanics.

## Biggest Risk
The biggest risk is **insufficient or low-quality trace signal**. If BuildOS lacks enough transcript volume, reliable accept/reject outcomes, or permission to log useful interaction detail, the distillation layer will produce noisy archetypes and bad rubrics. Without that data substrate, this direction collapses back into speculative prompting.

---

## Direction 4

## Brainstorm
- **Don’t build generalized simulation; build a real-user microfeedback network** — the question is wrong because synthetic users are being asked to replace the highest-signal source; use in-product rapid trials with recruited power users instead. **[Approach, Tradeoff, Who, Success]**
- **The question is wrong because “generalized across 22 skills” is the wrong optimization target** — cluster skills into 4–6 interaction archetypes and only simulate archetypes, not every skill. **[Scope, Approach, Success]**
- **The question is wrong because the bottleneck is not user simulation but skill observability** — instrument each skill to emit structured decision traces and failure signatures; improve feedback from executions rather than generating fake users. **[Approach, Scope, Tradeoff, Success]**
- **The question is wrong because convergence is a false goal** — optimize for early failure discovery via red-team interaction fuzzing, not human-likeness or iterative convergence. **[Success, Tradeoff, Approach]**
- **The question is wrong because “without manual per-skill configuration” is overconstrained** — require a tiny skill contract per skill (interaction type, desired outcome, forbidden behaviors) and make everything else automatic. **[Scope, Tradeoff, Who]**
- **The question is wrong because simulation should not sit before shipping** — ship narrower skills earlier behind confidence gating and collect live deltas; use simulation only as a regression harness after first contact with reality. **[Approach, Success, Who]**
- **Replace persona simulation with artifact-based evaluation** — the question is wrong because many skills can be judged from outputs and transcript structure alone; skip user emulation unless the skill truly depends on latent user psychology. **[Scope, Approach, Tradeoff]**
- **The question is wrong because “85% of real feedback” is not the right KPI** — target “catch 80% of ship-blocking failures before release” via hybrid static analysis + limited live canaries, not broad realism. **[Success, Tradeoff, Approach]**

## Direction: Stop Chasing Generalized User Simulation; Build Skill Contracts + Live Canaries

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| Requirement for full generalized user simulation before shipping | Dependence on synthetic realism, convergence loops, and zero-config ambition | Signal quality from real interactions, observability, and release confidence | A per-skill contract, confidence gating, and micro-canary feedback pipeline |

## The Argument
The question is wrong because it assumes the main problem is “how do we simulate users well enough.” It isn’t. The real problem is **how BuildOS gets trustworthy pre-ship feedback cheaply and quickly**. Full generalized AI user simulation is one possible means, but it is not the best system-level answer.

The question is wrong because **“generalize across 22+ skills without manual per-skill configuration” is the wrong constraint**. Skills differ in interaction shape, risk, and evaluability. Forcing zero-config generality guarantees a mushy evaluator. A **tiny skill contract** is the right abstraction: each skill declares interaction archetype, success outcome, allowed evidence sources, and critical failure modes. That is not burdensome; it is the minimum metadata needed for trustworthy automation.

The question is wrong because **simulated realism is being treated as the key metric**. BuildOS does not need a fake user that feels human; it needs a system that catches ship-blocking defects early. Those are different goals. A live canary with 5–10 targeted real interactions can outperform hundreds of simulated runs for interactive skills, especially where AskUserQuestion quality depends on nuance, trust, or ambiguity.

The question is wrong because **convergence is not the primary objective**. You can converge on the wrong synthetic world. What matters is release confidence calibrated to actual user behavior. Use simulation as a helper, not the source of truth.

### What to do instead
Build a **Skill Contract + Confidence Gate** system:

- Each SKILL.md gets a compact contract:
  - interaction archetype: interview, diagnosis, planning, transformation, instruction, critique
  - expected artifact/output
  - key quality dimensions
  - hard-fail behaviors
  - whether real-user response nuance is essential
- Route skills by contract:
  - **Artifact-heavy skills**: evaluate mostly from outputs/transcripts; no persona needed.
  - **Interaction-critical skills**: require micro-canary with real users before broad release.
- Use existing /simulate only for **regression and coverage expansion**, not as the sole go/no-go.
- Release behind a **confidence gate**:
  - pass smoke/invariants
  - pass contract-derived rubric
  - if interaction-critical, complete a small real-user canary

### Why now?
Two things changed:
1. You already proved manual cross-model simulation works enough to be useful, which means the next bottleneck is **trust calibration**, not raw generation.
2. You already have 22 skills and existing users/personas, so the cost of being wrong scales fast. The system now needs **decision quality**, not more simulation sophistication.

### What’s the workaround today?
Today the workaround is exactly what you described: wait for real usage over days, or run labor-intensive manual cross-model loops like `eval_intake.py`. This direction replaces “days of accidental learning” with **intentional micro-canaries plus reusable contracts**.

### 10x on which axis?
**Release confidence per unit time.**

### Adjacent analogy
This is how modern software delivery evolved: teams stopped trying to predict everything in staging and instead used **contracts, observability, and canaries** to learn safely from production.

## First Move
Pick 5 representative skills and add a one-page `SIM_CONTRACT.yaml` to each with:
- archetype
- output target
- 3–5 quality dimensions
- hard fails
- “needs real-user canary: yes/no”

Then implement a release rule in `/simulate`: no skill ships unless it passes smoke tests plus contract checks; interaction-critical skills also require a short canary review packet from real sessions. This first move forces the right abstraction and immediately reveals which skills actually need simulation.

## Why This Beats the Alternatives
The obvious approach is to invest heavily in persona generators, rubric synthesis, and iterative convergence. That overfits to the premise. It optimizes for synthetic completeness, not trustworthy shipping decisions.

It also beats the previous directions:
- Not a hidden-user-state simulator
- Not a replay/perturbation harness
- Not a trace distillation pipeline

Those all assume the answer is a better simulation engine. This direction says **don’t make simulation carry the whole load**. Use smaller, clearer machinery: contracts for structure, simulation for regressions, canaries for truth.

The result is structurally different:
- narrower scope
- explicit human role
- success measured by pre-ship defect catch rate and release confidence, not synthetic-human alignment

## Biggest Risk
The biggest risk is organizational: BuildOS may resist adding per-skill contracts because “manual config” feels like backsliding. If the team refuses that tiny explicit layer, it will keep chasing a magical zero-config evaluator and get brittle, low-trust automation instead.

---

## Synthesis

## The Fork

The real choice is [Bet A: Skill-Compiler Simulator] vs [Bet B: Replay-Perturbation Harness] vs [Bet C: Contracts + Live Canaries].

## Bet A: Skill-Compiler Simulator
Build the obvious generalized solution: compile each SKILL.md into an interaction model, then simulate users with hidden state rather than free-form roleplay. This directly attacks the stated goal: reusable, low-config evaluation across 22+ skills. It works if the compiler extracts required inputs, branch points, AskUserQuestion nodes, and success/failure conditions well enough to drive a three-agent loop: executor, persona, judge. Fixed anchor personas give regression stability; generated state variations give breadth. Success is broad coverage per skill with minimal hand-authoring and more coherent multi-turn failures than transcript-only evals.
**First move:** Implement the compiler for 3 skills—intake, diagnosis, planning—and run 50 simulations each using an 8-field hidden-state persona schema.
**Sacrifice:** You commit to a heavier platform bet upfront and accept that wrong IR extraction can make the whole system look rigorous while testing the wrong thing.

## Bet B: Replay-Perturbation Harness
Don’t model humans from scratch; model conversation coverage. Start from a small set of canonical transcripts by interaction family, then mutate user-side variables—expertise, ambiguity, cooperativeness, urgency, consistency, skepticism—to generate realistic boundary cases. This is a fuzz-testing approach, not a generalized simulator. It’s narrower, faster to validate, and optimized for failure discovery per engineer-hour. State exists only to preserve coherence during perturbation, not as a full latent-user architecture. Success is whether each seed trace produces many distinct, actionable failure classes without bespoke persona writing.
**First move:** For 3 skills, create 2 seed traces each, define 8 user mutation knobs, run 50 perturbed conversations, and cluster judge rationales into recurring failures.
**Sacrifice:** You give up the ambition of a universal simulation engine and remain dependent on the breadth and quality of seed conversations.

## Bet C: Contracts + Live Canaries
Challenge the premise: don’t make synthetic simulation carry the whole evaluation burden. Add a tiny per-skill contract—archetype, output target, quality dimensions, hard fails, needs-real-user-canary yes/no—then use simulation only for regressions and coverage expansion. For interaction-critical skills, require a short live canary before broader release. This optimizes for release confidence and ship-blocking defect catch rate, not synthetic realism or zero-config elegance. It affects PMs, reviewers, and release process more than modeling architecture. Success is calibrated shipping decisions, not whether personas feel human.
**First move:** Add SIM_CONTRACT.yaml to 5 representative skills and enforce a release gate: smoke tests + contract checks, plus real-user canary where required.
**Sacrifice:** You abandon the pure zero-config vision and accept some manual metadata and human involvement as permanent parts of the system.

## Comparison

| | Timeline | Risk | What you learn | Strategic sacrifice |
|---|----------|------|----------------|---------------------|
| **Bet A** | 2–4 weeks for a credible pilot on 3 skills; longer for broad rollout because compiler quality must be validated skill-by-skill | IR extraction may misread messy SKILL.md files; hidden-state simulation may seem coherent but be wrong | Whether interaction structure can be auto-extracted well enough to generalize across skill families | Commits to a platform-heavy architecture and de-prioritizes simpler, lower-ceremony paths |
| **Bet B** | 1–2 weeks for first signal, given existing eval_intake-style traces and modest mutation tooling | Seed traces may be too narrow, producing lots of variants of the same failure | Which user-side perturbations actually surface new failures and which skill families are coverage-poor | Gives up the claim of universal user simulation and accepts a harness built around examples |
| **Bet C** | 1 week to trial contracts and gates on 5 skills; canary learning speed depends on access to real users | Team may resist manual contracts; canary process may be operationally hard to run consistently | Which skills truly need rich interaction testing versus artifact/output checks | Abandons zero-config purity and the idea that simulation alone should decide ship/no-ship |
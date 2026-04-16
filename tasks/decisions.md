# Decisions

Settled architectural and product decisions. Each entry records what was decided, why, and what alternatives were considered.

**Convention:** Titles are assertions, not topics. "Web auth must use HttpOnly cookies because query-param tokens leak" — not "Auth decision." The title IS the takeaway.

---

### D1: BuildOS defaults to Python + Shell; TypeScript/Bun allowed when there's a concrete reason
**Decision:** Python 3.11+ and Bash remain the default for new scripts. TypeScript/Bun is allowed when adapting existing TypeScript reference code (e.g., gstack patterns), or when types deliver real value for the specific script. The decision is per-script, not per-project. Skills remain Markdown with YAML frontmatter.
**Rationale:** Original D1 (2026-03-01) banned JS/TS entirely. Revisited 2026-04-15 after studying gstack's skill validation system (TypeScript/Bun, 1,573 lines of structural tests). Existing Python codebase (debate.py 4,136 lines, 17 hooks, sim_compiler.py, LiteLLM dependency) stays Python — rewriting for language consistency is churn. But new tooling shouldn't be blocked from TypeScript when the reference implementation is TypeScript. Claude writes both equally well; the bottleneck is never the language.
**Alternatives considered:** (a) Full migration to TypeScript/Bun (rejected: massive rewrite effort, LiteLLM is Python-only), (b) Strict Python-only (rejected: artificially rewrites proven TypeScript patterns from scratch), (c) TypeScript for all new code (rejected: most new scripts interact with existing Python — per-script choice is more pragmatic)
**Date:** 2026-03-01, revised 2026-04-15

### D2: Cross-model debate via LiteLLM proxy, not direct API calls
**Decision:** All multi-model calls route through a local LiteLLM proxy at localhost:4000. Scripts use `llm_client.py` which calls the proxy. Direct API calls to Anthropic/OpenAI/Google are prohibited in application code.
**Rationale:** Cross-model debate requires calling Claude, GPT, and Gemini from the same codebase. Direct API calls mean 3 different SDKs with different auth, retry, and error patterns. LiteLLM provides a unified OpenAI-compatible interface with model routing, fallbacks, and cost tracking in one place.
**Alternatives considered:** (a) Direct SDK calls per provider (rejected: 3x auth/retry complexity), (b) Anthropic's model routing (rejected: doesn't cover non-Anthropic models), (c) Cloud-hosted LiteLLM (rejected: adds latency and external dependency for local dev)
**Date:** 2026-03-01

### D3: Skills are SKILL.md prompt documents, not executable code modules
**Decision:** Each skill is a Markdown file (`.claude/skills/<name>/SKILL.md`) with YAML frontmatter and a procedure section. The Claude Code harness loads and executes them as prompts. Skills do not import each other or share code — shared logic lives in `scripts/`.
**Rationale:** Skills are instructions for Claude, not programs. Making them Markdown keeps them readable, auditable, and editable without a build step. Code reuse happens at the script layer (debate.py, llm_client.py), not the skill layer.
**Alternatives considered:** (a) Python skill modules with decorators (rejected: over-engineering for prompt documents), (b) YAML-only skills (rejected: procedures need freeform text that YAML makes awkward), (c) Skills that import shared skill libraries (rejected: creates hidden coupling between prompt documents)
**Date:** 2026-03-01

### D4: Security posture is a user choice via --security-posture flag, not a pipeline default
**Decision:** Add `--security-posture` (1-5) to `debate.py`. At 1-2, security findings are advisory-only and PM is the final arbiter. At 4-5, security can block. Default: 3 (balanced). Skills ask the user before running.
**Rationale:** A velocity-focused analysis spent significant pipeline capacity injecting security controls (egress policies, approval gates, credential rotation) into a speed-focused recommendation. Security was over-rotating as the de facto final arbiter when PM should have been.
**Alternatives considered:** (a) Remove security persona entirely at low posture (rejected: still useful for advisory), (b) Hard-code posture per topic type (rejected: user should decide), (c) No change — always balanced (rejected: proven to waste pipeline capacity on wrong priorities)
**Date:** 2026-04-10

### D5: Thinking modes are single-model, not multi-model — prompt design drives quality, not model diversity
**Decision:** explore, pressure-test, and pre-mortem use single-model calls. Multi-model reserved for validate and refine only.
**Rationale:** Tested 3 different models vs 1 model prompted 3 times with forced divergence on a strategic decision. Single-model with divergence prompts produced more diverse output than multi-model. The value comes from prompt design, not model diversity. Multi-model still proven for review (cross-family error detection) and refinement (models improve on other families' output).
**Alternatives considered:** (a) All modes multi-model (rejected: 3x cost, no quality gain for thinking modes), (b) All modes single-model (rejected: validate/refine genuinely benefit from cross-family diversity)
**Date:** 2026-04-10

### D6: Explore flow presents 3 bets with fork-first format, not 1 committed direction
> **SUPERSEDED by D11 (2026-04-11).** Core principle (multi-direction > single-direction) carried forward. All implementation specifics (fork-first format, comparison table, 150-word descriptions, hardcoded product-market dimensions, "3 bets" framing) replaced. See tasks/decision-audit-d6.md.

**Decision:** Explore generates 8-10 brainstorm options, clusters into exactly 3 bets that differ on 2+ dimensions (customer, product form, business model, distribution), presents the fork statement first, then 150-word descriptions and a comparison table. Human picks or redirects.
**Rationale:** Previous flow picked "the most interesting" direction and developed it fully. This skipped the obvious-but-correct answer for novelty. Fork-first with 3 bets lets the human see the trade-off before the AI commits. Tested across 15 personas, 4.6/5 average.
**Alternatives considered:** (a) Pick 1 and develop fully (rejected: skips obvious answers, no human steering), (b) Present all 8-10 brainstorm items (rejected: too many half-baked options to compare), (c) 2 bets (rejected: creates false binary, tested and confirmed)
**Date:** 2026-04-10

### D7: Pre-flight uses GStack-style adaptive questioning, not batch questionnaires
**Decision:** Before running explore or pressure-test, the system conducts a 3-4 question discovery conversation. Questions are selected adaptively from a bank based on prior answers, one at a time, with push-until-specific. Not a fixed list dumped at once.
**Rationale:** 5 questions dumped at once (v1) felt like a form and the user rejected it. Research shows 3+ upfront questions cause 20-40% abandonment in consumer flows, but GStack proved that one-at-a-time with push-until-specific works for high-stakes discovery. Tested across 20+ simulated personas at 4.8-5.0/5. Key rules: discovery rule (never state the insight), never do the math for them, viability doubt completion.
**Alternatives considered:** (a) No pre-flight, generate then iterate (rejected: wrong frames anchor strategic output), (b) 5 questions as a batch (rejected: user rejected it), (c) 1 question only (rejected: insufficient to break deep anchors per testing)
**Date:** 2026-04-10

### D8: Upgrade /status with smart routing instead of creating /next
> **Rationale update (2026-04-15, audit D8):** Hook rejection rationale ("binary block/allow," "annoying") is obsolete. D16 proved hooks can inject non-blocking advisory suggestions via hook-intent-router.py. Core routing decision holds; the anti-hook precedent does not.

**Decision:** Enhance the existing `/status` skill with a context-aware routing table instead of creating a new `/next` command. The routing table reads git state, artifacts, context budget, and audit log to suggest the specific next skill and mode.
**Rationale:** Debate session surfaced the concept of "nudges" (suggesting the right skill at the right moment). Three implementation options evaluated: (a) rules text, (b) hooks, (c) a new `/next` command. The `/next` concept was strong but creating a separate command duplicates `/status` purpose — two commands answering "what should I do?" is worse than one. `/status` already reads git state and artifacts with a static 6-row routing table. Upgrading to 13 priority-ordered conditions with contextual overlays gives the same result without a new command.
**Alternatives considered:** (a) New `/next` skill (rejected: duplicates `/status` purpose), (b) Auto-nudge hooks (rejected: gets annoying, binary block/allow doesn't suit suggestions), (c) Advisory rule text (rejected: drops under context pressure)
**Date:** 2026-04-10

### D9: Consolidate scattered exploration guidance into "Inspect before acting" CLAUDE.md rule
**Decision:** Rename "Retrieve before planning" → "Inspect before acting" in CLAUDE.md with 3 concrete behavioral rules: (1) read file + context before editing, (2) Grep/Read before answering code questions, (3) never claim "doesn't support" without checking.
**Rationale:** Cross-model refinement (6 rounds, 3 models) found 18+ matches across 7 phrasings of exploration guidance scattered across skills — but no consolidated rule and no structural enforcement. Fix 2 (advisory rule) ships immediately at zero cost. Fix 1 (pre-edit hook) deferred because refinement revealed PreToolUse hook infrastructure doesn't exist yet — larger scope than estimated.
**Alternatives considered:** (a) Pre-edit hook only (rejected for now: requires building hook infrastructure from scratch), (b) Do nothing (rejected: qualitative complaints are consistent), (c) Both fixes together (rejected: hook scope too large for this session, rule can ship independently)
**Date:** 2026-04-10

### D11: Explore mode is domain-agnostic with adaptive dimensions, not product-market-specific
**Decision:** Redesign explore mode to derive divergence dimensions from the problem domain instead of hardcoding product-market dimensions (customer, revenue, distribution, product form, wedge). Pre-flight becomes an adaptive tree that infers domain and generates forcing questions on the fly. Existing pre-flight files (product, solo-builder, architecture) become reference material, not routes. Direction 2 forced to differ on mechanism; Direction 3 forced to challenge the question's premise.
**Rationale:** Explore was hardcoded for product-market strategy — engineering, organizational, research, and career questions got asked "who pays?" and "what's the adoption barrier?" Tested across 8 domains with 5 rounds of iteration. Non-product questions went from 3.4-3.8 avg to 4.4+ avg. Domain appropriateness hit 5.0 on all non-product experiments (zero product-language leakage). Premise-challenge constraint on Direction 3 was the single highest-leverage change (+1.0 on career, +1.0 on organizational).
**Alternatives considered:** (a) Add more bucket types (rejected: creates the same rigidity problem), (b) One fully generic prompt with no dimensions (rejected: without dimensions, directions converge on the same mechanism), (c) Let the model self-derive dimensions without pre-flight (rejected: pre-flight context quality determines output quality — D7 finding still holds)
**Date:** 2026-04-11

### D10: /think discover generates the PRD interactively because blank templates freeze new team members
**Decision:** Add Phase 6.5 to `/think discover` that generates or validates `docs/project-prd.md` from the design doc conversation. Three paths: generate from conversation (with 3 follow-up questions for gaps), validate a user-drafted PRD, or skip. PRD template expanded from 6 to 9 sections based on Claude/AI PRD best practices research.
**Rationale:** BuildOS is meant to be cloned by team members to build products. The blank PRD template was the first thing they'd see and the most likely place to stall. `/think discover` already asks all the hard questions — the PRD should be a byproduct of that conversation, not a separate writing exercise. Research (Anthropic docs, ChatPRD, AddyOsmani, OpenAI PM template) confirmed 3 missing sections: acceptance criteria (machine-verifiable), constraints (AI can't infer from omission), and verification plan (self-verify before done).
**Alternatives considered:** (a) Only generate from conversation (rejected: some people think better by writing first), (b) Separate `/prd` skill (rejected: adds another step to learn; design doc → PRD is a natural continuation), (c) Make `/setup` smarter (rejected: `/setup` runs once at project init, not per-feature)
**Date:** 2026-04-10

### D12: Skill rename uses rip-and-replace (no aliases) because solo user means zero backward-compat overhead
**Decision:** Consolidate 25 skills to 15 with clean renames and merges, no alias layer or backward-compatibility shims. Old skill directories deleted entirely. Renames: define→think, refine→polish, wrap-session→wrap, capture→log, doc-sync→sync. Merges: recall+status→start, review+review-x+qa+governance→check, 4 design skills→design, debate explore→explore, debate pressure-test→pressure-test. challenge gained --deep (old debate validate). plan gained --auto (old autoplan). 12 old directories deleted.
**Rationale:** Solo developer, no external users of the skill names. Aliases add maintenance debt and confusing dual-path behavior for zero benefit. Rip-and-replace is the cleanest path when you control all consumers.
**Alternatives considered:** (a) Keep old names as aliases routing to new skills (rejected: maintenance debt for zero users), (b) Gradual deprecation with warnings (rejected: same reasoning — no one to warn), (c) Keep the 25-skill structure (rejected: too many skills with overlapping concerns, naming was inconsistent)
**Date:** 2026-04-11

### D13: Cross-model evaluation must use review-panel (parallel) not serial review calls — orchestration discipline beats code changes
**Decision:** Three rules for cross-model evaluation workflows: (1) Always use `review-panel` (parallel 3 models) instead of 3× `review` (serial) for independent evaluations. (2) Run all persona simulations as parallel Agent calls, not serial. (3) Stop iterating when consensus hits target — don't chase diminishing returns past first convergence.
**Rationale:** Explore intake eval took ~75 min wall-clock. Root cause: 18 serial API calls (6 rounds × 3 models) when each round's 3 calls are independent. `review-panel` already parallelizes via ThreadPoolExecutor. 5 persona sims ran mostly serial when all 5 are independent. Rounds 16-17 chased edge cases after 3/3 register consensus in Round 15. Estimated savings: ~55 min (75→20 min) from orchestration changes alone, zero code changes.
**Alternatives considered:** (a) Add `--parallel` flag to `refine` (rejected: rounds are inherently serial — each depends on previous output), (b) Automate triage between eval rounds (rejected: human judgment on "real issue vs. model taste" is the key sensor), (c) Combine register+flow eval into one prompt per model (considered: low-risk, halves calls per round, but secondary to the parallel vs. serial fix), (d) Batch multiple fixes per round (risky: compounds regressions, loses the triage sensor between fixes)
**Date:** 2026-04-11

### D14: /check renamed to /review because the name should match the action
**Decision:** Rename `/check` to `/review` across the entire codebase (directory, SKILL.md, 193 cross-references in 39 files). The skill is a cross-model code review — "check" undersells it and sounds like a lint check.
**Rationale:** Users reach for "review my code" not "check my code." The modes (`--qa`, `--governance`, `--second-opinion`) are all review sub-modes. The old name was `/review` before the D12 consolidation — this restores clarity.
**Alternatives considered:** (a) `/code-review` (rejected: 11 chars + hyphen, too much friction for frequent use), (b) Keep `/check` (rejected: ambiguous with lint/status checks)
**Date:** 2026-04-11

### D15: /review auto-detects content type — code gets personas, documents get cross-model evaluation via --models
**Decision:** `/review` detects whether the input is code (git diff) or a non-code document. Code routes to `review-panel --personas` (persona framing appropriate for code). Documents route to `review-panel --models` with a content-appropriate eval prompt (no persona framing). Added `--models` flag to `review-panel` as mutually exclusive with `--personas` — bypasses persona lookup entirely. Key distinction: `/review` evaluates, `/polish` improves.
**Rationale:** PM/Security/Architecture lenses are designed for code diffs — sending a strategy doc through them produces irrelevant findings. The original D15 routed documents to `refine` (iterative improvement), but `/review` should evaluate, not improve. `review-panel --models` runs 3 independent models in parallel with the caller's eval prompt as the only system prompt. L21 proved that advisory behavioral fixes (lessons, rules) don't survive execution pressure — structural enforcement via the `--models` flag prevents persona mismatch.
**Alternatives considered:** (a) Always use personas (rejected: wrong lenses for non-code), (b) Add document-specific personas to config (rejected: conflates "which model" with "what framing" — the eval prompt IS the framing), (c) Make `--personas` accept model names when they don't match config (rejected: magical, less explicit), (d) Behavioral fix only via lessons (rejected: L21 was violated within one turn of being written)
**Date:** 2026-04-11

### D16: Natural language is the primary interface — slash commands are power-user shortcuts
**Decision:** BuildOS routes users to skills via natural language intent, not memorized commands. Three layers: (1) `.claude/rules/natural-language-routing.md` — advisory routing table + proactive pattern recognition, (2) `hooks/hook-intent-router.py` (UserPromptSubmit) — deterministic keyword-based intent classification, injects routing suggestions as context Claude sees every time, (3) `hooks/hook-error-tracker.py` (PostToolUse:Bash) — tracks recurring errors, feeds proactive `/investigate` suggestions after 2+ failures of same class. Suggestions are advisory (never block), fire once per skill per session (nag prevention), and add ~28ms per user message.
**Rationale:** 19 skills with specific invocation patterns create a memorization burden. Users shouldn't need to look at GitHub or print a cheat sheet to use the system. The `/` menu is the discovery surface, but it only works if you already know skill names. Natural language intent ("something broke" → `/investigate`) is the zero-memorization interface. Hooks make the routing deterministic — the suggestion fires 100% of the time the pattern matches, unlike advisory rules which Claude may skip under context pressure. Performance profiled: all hooks <80ms, total system overhead 3-6% of Claude API call time.
**Alternatives considered:** (a) Advisory rule only (rejected: not deterministic — Claude skips rules under context pressure), (b) Blocking hook that forces skill invocation (rejected: hostile UX, can't override for edge cases), (c) Interactive menu on every message (rejected: slows down power users who know what they want), (d) Reduce skill count to reduce memorization (rejected: skills serve distinct roles, the problem is discoverability not count)
**Date:** 2026-04-11

### D17: Refine critique mode — document-type-aware refinement prevents consulting-deliverable drift
**Decision:** Added `--mode critique` to `debate.py refine` with three-layer auto-detection (frontmatter → content heuristic → default). Critique mode uses dedicated prompts ("sharper, not more elaborate"), strips recommendation-preservation and strategic-posture rules, defaults to 2 rounds, and includes drift detection on stderr. Parked model routing (Track 2) — no outcome quality data to justify it. 
**Rationale:** Refine rounds on the Brady VP sales memo turned a sharp pressure-test ("is this a methodology problem or a GTM focus problem?") into a 120-day pilot plan with fabricated success criteria and owner assignments. Root cause: two prompt rules (REFINE_STRATEGIC_POSTURE_RULE, REFINE_RECOMMENDATION_PRESERVATION_RULE) assume all documents are proposals. On critiques, "more specific" means "more actionable" which means "consulting deliverable." A/B test on Brady: proposal mode +127% size, critique mode -21%. Full audit of 10 prior refined docs showed proposals refine correctly (7/10 sharpened, 3/10 same), confirming the fix is correctly scoped to critique inputs only.
**Alternatives considered:** (a) Prompt-only fix without mode detection (rejected: users forget --mode flag, same failure), (b) Universal prompt change (rejected: proposal mode works correctly, don't break it), (c) Post-processing output filter (rejected: too blunt, can't distinguish legitimate specificity from drift)
**Date:** 2026-04-13

### D18: Keep Gemini 3.1 Pro with timeout hardening — not worth swapping to Grok 4 or downgrading to 2.5
> **Implementation update (2026-04-15):** Fallback was only wired in `refine` command. Audit found 11 of 12 `_call_litellm` call sites had no fallback — ~6.4% of challenge runs silently lost one voice on Gemini timeout. Fixed: all call sites now use `_call_with_model_fallback` with `_get_fallback_model` helper. 903 tests pass.

**Decision:** Keep Gemini 3.1 Pro Preview in the debate rotation. Add per-model timeout (120s vs 300s default) and automatic fallback to next model in rotation on timeout. Don't swap to Grok 4 (requires new account/API key), don't downgrade to Gemini 2.5 Pro (Intelligence Index 35 vs 53/57 for Opus/GPT — too weak).
**Rationale:** Gemini 3.1 Pro has high TTFT (~29s, p99=542s) but strong reasoning (Intelligence Index 57). Timeout + fallback handles the latency tail without losing the quality. Grok 4 is stronger (II 73, TTFT <2-7s) but requires xAI account setup. Gemini 2.5 Pro benchmarks a full tier below (SWE-bench 73.1% vs 78.2%).
**Alternatives considered:** (a) Swap to Grok 4 (rejected: new account friction, user chose not to), (b) Downgrade to Gemini 2.5 Pro (rejected: measurably weaker), (c) Remove Gemini entirely (rejected: cross-family diversity is the point of the debate engine)
**Date:** 2026-04-14

### D19: compactPrompt is not a valid Claude Code settings.json field — only CLAUDE.md Compact Instructions works
**Decision:** The only lever for controlling compaction behavior is the `## Compact Instructions` section in CLAUDE.md. `compactPrompt` in `~/.claude/settings.json` does not exist in the schema — multiple web sources and model recommendations were wrong about this.
**Rationale:** Schema validation rejected the field. Tested empirically. The `## Compact Instructions` section is re-read from disk during compaction (both auto and manual), so it reliably survives.
**Alternatives considered:** (a) `compactPrompt` in settings.json (rejected: schema validation failure), (b) Both levers (rejected: only one exists)
**Date:** 2026-04-14

### D20: Keep sim infrastructure and generalize eval_intake.py — no external tool meets the requirements
**Decision:** Keep all V2 sim scripts (sim_compiler.py, sim_persona_gen.py, sim_rubric_gen.py, sim_driver.py). Do not adopt DeepEval, Inspect AI, Promptfoo, LangSmith, Braintrust, Ragas, or Patronus. Generalize eval_intake.py's proven 3-agent architecture across interactive skills using the V2 code. Reverse the session 7-8 "commodity, don't build" verdict — it was wrong due to missing operational evidence (L28).
**Rationale:** eval_intake.py proved that iterative 3-agent simulation (17 rounds, 3.3→4.5/5) produces quality improvements no other testing approach replicates. Deep investigation of 7 external tools found none support: (a) structured persona cards with hidden truth and behavior scripts, (b) information asymmetry enforced at the architecture level, (c) agent procedure testing (all are built for chatbot eval). The "commodity" label was applied at the wrong abstraction level — multi-turn simulation exists as a category, but the specific kind BuildOS needs doesn't exist as a product.
**Alternatives considered:** (a) Kill sim scripts, adopt DeepEval (rejected: no structured hidden state, hardcoded simulator prompts, chatbot-only), (b) Kill sim scripts, adopt Inspect AI (rejected: best framework but you still write the sim loop yourself — no savings), (c) Kill sim scripts, adopt nothing, validate manually (rejected: eval_intake.py proved manual validation takes days per skill and doesn't scale to 8-10 interactive skills), (d) Build from scratch ignoring V2 code (rejected: 1,355 lines already exist with 48 tests)
**Date:** 2026-04-15

### D21: Standard /challenge includes judge step — adversarial challengers no longer get the last voice
**Decision:** Standard `/challenge` pipeline is now: challengers → independent judge → session synthesis. The judge sees both the proposal's evidence and the challengers' findings simultaneously and evaluates whether challenges engaged with the proposal's evidence or made generic conservative claims. Judge model must not overlap with any challenger model. The judge prompt is reframed from "evaluate challenges" to "weigh both sides" with explicit instructions to check for conservative bias, cost-of-inaction, and whether challengers engaged with operational evidence.
**Rationale:** Tested on context-packet-anchors proposal (session 13). Without judge: session model synthesized challengers' "over-engineered" framing into maximal descoping (skip extraction, just use prompt instructions). With judge: independent model kept the extraction approach and asked for robustness measures. The descoping recommendation didn't engage with A/B evidence showing explicit context outperforms implicit. Root cause: adversarial models are incentivized to find flaws, and the session model is biased by recency toward the last voice. Adding ~20s of judge time corrects a structural bias that was producing systematically conservative recommendations.
**Alternatives considered:** (a) Add a rebuttal step instead of a judge (rejected: requires generating a rebuttal from the proposal author's perspective, which is more complex and still filtered through the session model), (b) Keep judge in --deep only (rejected: the bias exists in every standard challenge, not just deep ones), (c) Change challenger prompts to be less adversarial (rejected: adversarial framing is the point — the fix is adding balance, not removing challenge)
**Date:** 2026-04-15

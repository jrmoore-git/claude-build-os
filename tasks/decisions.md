# Decisions

Settled architectural and product decisions. Each entry records what was decided, why, and what alternatives were considered.

**Convention:** Titles are assertions, not topics. "Web auth must use HttpOnly cookies because query-param tokens leak" — not "Auth decision." The title IS the takeaway.

---

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
**Decision:** Explore generates 8-10 brainstorm options, clusters into exactly 3 bets that differ on 2+ dimensions (customer, product form, business model, distribution), presents the fork statement first, then 150-word descriptions and a comparison table. Human picks or redirects.
**Rationale:** Previous flow picked "the most interesting" direction and developed it fully. This skipped the obvious-but-correct answer for novelty. Fork-first with 3 bets lets the human see the trade-off before the AI commits. Tested across 15 personas, 4.6/5 average.
**Alternatives considered:** (a) Pick 1 and develop fully (rejected: skips obvious answers, no human steering), (b) Present all 8-10 brainstorm items (rejected: too many half-baked options to compare), (c) 2 bets (rejected: creates false binary, tested and confirmed)
**Date:** 2026-04-10

### D7: Pre-flight uses GStack-style adaptive questioning, not batch questionnaires
**Decision:** Before running explore or pressure-test, the system conducts a 3-4 question discovery conversation. Questions are selected adaptively from a bank based on prior answers, one at a time, with push-until-specific. Not a fixed list dumped at once.
**Rationale:** 5 questions dumped at once (v1) felt like a form and the user rejected it. Research shows 3+ upfront questions cause 20-40% abandonment in consumer flows, but GStack proved that one-at-a-time with push-until-specific works for high-stakes discovery. Tested across 20+ simulated personas at 4.8-5.0/5. Key rules: discovery rule (never state the insight), never do the math for them, viability doubt completion.
**Alternatives considered:** (a) No pre-flight, generate then iterate (rejected: wrong frames anchor strategic output), (b) 5 questions as a batch (rejected: user rejected it), (c) 1 question only (rejected: insufficient to break deep anchors per testing)
**Date:** 2026-04-10

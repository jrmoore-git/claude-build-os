# Lessons

Mistakes, surprises, and patterns worth remembering. Each entry is a lesson learned from real work on this project.

**Convention:** Titles are assertions, not topics. "Long sessions silently eat their own corrections — compact at 50-70% context" — not "Session quality." The title IS the takeaway.

**Target:** Keep this file under 30 active entries. When it grows beyond that, promote recurring lessons to `.claude/rules/` files and archive one-offs.

---

| # | Lesson | Source | Rule |
|---|---|---|---|
| L25 | Review-after-build has no enforcement — advisory rules in 3 places all failed silently | Built /simulate (6 files), ran /simulate to validate, fixed issues, declared done — never suggested /review. Plan said "run /review when complete", routing table condition #6 matched (3+ files, no review artifact), but all three are advisory text. No hook checks mid-session state. The intent router watches user messages, not workflow state. Context decay over a long build session made the advisory invisible. | Advisory rules fail under context pressure. Review-after-build needs structural enforcement: either a post-build hook or mid-session state check in the intent router. |
| L27 | Significant scope expansion between versions is a new proposal — V1 approval doesn't cover V2 | V1 /simulate was challenged correctly (session 4: propose → challenge → plan → build). V2 was 4x larger scope (IR extraction, persona generation, 3-agent simulation loops, rubric generation) but was treated as an "evolution" of V1. Sessions 7-8 built 2,073 lines of V2 code, THEN challenged it. The challenge ran too late and all 3 models converged on a wrong "don't build" verdict because they lacked operational evidence. Root cause: V2 felt like V1 continuation, not new work needing its own gate. | When scope significantly expands between versions (new abstractions, 2x+ code, new infrastructure), treat it as a new proposal requiring its own /challenge gate — even if the prior version was already approved. "Evolving an approved design" and "proposing new work" feel the same in the moment but aren't. |
| L28 | Cross-model panels converge on wrong answers when operational evidence is missing from input | 3 independent models all said "sim-compiler is commodity, don't build" — unanimous and wrong. Root cause: proposal lacked eval_intake.py's track record (17 rounds, 3.3→4.5 improvement). Models said "DeepEval does this" without anyone checking whether DeepEval actually meets the specific requirements (it doesn't — no structured persona hidden state, hardcoded simulator prompts, no agent procedure testing). Absence of bugs was treated as absence of need (survivorship bias). Dramatic quantitative findings (18/22 missing Safety Rules) crowded out qualitative evidence (simulation proved its value). | Challenge inputs must include operational evidence when it exists. "Commodity" claims about external tools must be verified against specific requirements before influencing judgment, not just category-matched. Unanimous convergence from models with the same incomplete context is correlated error, not strong consensus. |
| L29 | Standard /challenge has structural conservative bias — adversarial challengers get the last voice, no rebuttal | Tested on context-packet-anchors proposal (session 13). Challengers unanimously recommended "descope to prompt-only, skip extraction" — session model synthesized this into maximal descoping. Independent judge (GPT-5.4) seeing both proposal evidence and challengers simultaneously reached a different conclusion: keep the extraction approach, make it robust. The descoping recommendation didn't engage with the A/B evidence showing explicit context outperforms implicit. Root cause: pipeline was proposal → challengers → synthesis, where synthesis is biased by recency toward the adversarial voice. | Standard /challenge now includes a judge step (challenge → judge → synthesize). The judge sees both sides simultaneously and evaluates whether challengers engaged with proposal evidence or made generic conservative claims. Also: judge model must not be the same as any challenger model (self-evaluation bias). |
| L30 | V2 pipeline quality gap is structural (persona format + mid-loop interventions), not architectural — and the fix isn't more automation | Built full V2 pipeline (1,520 lines, 151 tests), scored 3.11/5 vs eval_intake's 4.73. Added turn_hooks (spike), got to 3.70. Three root causes resist generalization: thin persona cards, skill-specific register rules, hooks bolted on rather than co-evolved. Cross-model panel (3 models) converged: eval_intake's quality came from 17 iterations of watching-and-fixing, not from any architectural decision. Front-loading knowledge via questionnaire won't work because humans are better critics than oracles. | Simulation quality comes from iterative refinement on concrete failures, not from upfront configuration or automation. When building evaluation frameworks, design for critique loops (run → review transcript → annotate failures → adjust → rerun) not for zero-setup automation. |
| L31 | Rubric dimensions must measure product outcomes not interaction style | Spike optimization focused on register_match and flow — style dimensions. The actual value question is: did the skill identify the real problem, reach a useful conclusion, help the user make a better decision? Style dims are noise that distracts from substance. | When building rubrics or evaluation criteria for skills, frame dimensions around: problem identification, conclusion quality, decision support, time efficiency. Drop tone/register/flow dimensions unless the skill is specifically about communication. |
| L32 | Runtime directive injection degrades simulation quality — eval_intake worked by changing skill prompts, not runtime context | D22 critique loop spike: hand-crafted directives injected every turn scored 1.78 avg vs 2.50 baseline (degradation, not improvement). 3-model pre-mortem converged on "wrong mechanism" — eval_intake's 17 iterations changed SKILL.md text directly, not runtime executor context. Injecting directives adds cognitive load to the executor without changing its core instructions. | Simulation quality improvements must modify the skill prompt itself (the artifact being tested), not the simulation runtime. If building future critique loops, the output of each iteration should be a SKILL.md diff, not a runtime directive. |

---

## Promoted lessons

When a lesson has been promoted to a `.claude/rules/` file or a hook, remove it from the active table above and record the promotion here. This keeps the active list lean (target: ≤30 entries) while preserving provenance. See [the enforcement ladder](../docs/the-build-os.md#part-v-the-enforcement-ladder) for when to escalate.

Before promoting a lesson, state how you would catch a violation of the resulting rule. If you can't describe a concrete test, the lesson isn't ready for promotion.

| # | Promoted to | Date |
|---|---|---|
| L12 (original) | `.claude/rules/security.md` — "Use HttpOnly cookies, never auth in URLs" | 2026-03-01 |
| L20 | `.claude/rules/skill-authoring.md` — "Persona Definition — Problem-First, No Style Classification" | 2026-04-11 |
| L22 | `.claude/rules/skill-authoring.md` — "Skill frontmatter description must be single-line quoted string" | 2026-04-14 |

## Archived lessons

Lessons that are resolved, one-offs, or subsumed by decisions. Kept for provenance.

| # | Reason | Date |
|---|---|---|
| L10 | Subsumed by D4 (security posture flag) | 2026-04-14 |
| L11 | Subsumed by D5 (thinking mode matching) | 2026-04-14 |
| L13 | Subsumed by D11 (D6 was intermediate step; D11 replaced all D6 implementation specifics) | 2026-04-15 |
| L14 | Subsumed by D7 (pre-flight discovery) | 2026-04-14 |
| L15 | Subsumed by D7 (adaptive questioning) | 2026-04-14 |
| L16 | Subsumed by D5 (single-model for thinking) | 2026-04-14 |
| L17 | Fix shipped in audit-batch2 (field name mismatches) | 2026-04-11 |
| L18 | Fix shipped (standalone test scripts in run_all.sh) | 2026-04-11 |
| L21 | Structurally fixed by D15 (review-panel --models) | 2026-04-11 |
| L23 | Resolved — security posture modifier wired to --models path | 2026-04-11 |
| L19 | Subsumed by D13 (use review-panel, not serial review) | 2026-04-15 |
| L24 | Resolved — fix shipped in wrap/SKILL.md Step 4 (Read→Write adjacency) | 2026-04-15 |
| L26 | Promoted to memory (feedback_diagnostic_not_work_order.md) + /start Safety Rules | 2026-04-15 |

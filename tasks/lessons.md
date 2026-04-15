# Lessons

Mistakes, surprises, and patterns worth remembering. Each entry is a lesson learned from real work on this project.

**Convention:** Titles are assertions, not topics. "Long sessions silently eat their own corrections — compact at 50-70% context" — not "Session quality." The title IS the takeaway.

**Target:** Keep this file under 30 active entries. When it grows beyond that, promote recurring lessons to `.claude/rules/` files and archive one-offs.

---

| # | Lesson | Source | Rule |
|---|---|---|---|
| L19 | Cross-model evaluation loops are too slow — 37 serial `review` calls when `review-panel` exists | Investigation (2026-04-11) corrected the decomposition: NOT 6 refine rounds × 3 calls. Actually 37 serial `debate.py review` calls across 12+ eval rounds, averaging 1.3 min each (~48 min total). `review-panel` already parallelizes via ThreadPoolExecutor — the fix is at the orchestration layer (use `review-panel` instead of 3× serial `review`), not in debate.py itself. D13 already prescribes this fix. | Use `review-panel` for independent multi-model evaluation. Never call `review` 3× serially on the same input (D13). The parallelism infrastructure exists — the orchestration layer must use it. |
| L24 | Write tool fails during /wrap because parallel sessions' Stop hook modifies current-state.md between Read and Write | /wrap reads docs early (Step 1), writes late (Steps 4-6). Parallel session's `hook-stop-autocommit.py` calls `mark_current_state_stale()` in the gap, tripping the Write tool's staleness check. Fix: Read immediately before Write — no intervening tool calls. | Read → Write must be adjacent for any file that parallel sessions can modify. Added instruction to wrap/SKILL.md Step 4. |
| L25 | Review-after-build has no enforcement — advisory rules in 3 places all failed silently | Built /simulate (6 files), ran /simulate to validate, fixed issues, declared done — never suggested /review. Plan said "run /review when complete", routing table condition #6 matched (3+ files, no review artifact), but all three are advisory text. No hook checks mid-session state. The intent router watches user messages, not workflow state. Context decay over a long build session made the advisory invisible. | Advisory rules fail under context pressure. Review-after-build needs structural enforcement: either a post-build hook or mid-session state check in the intent router. |
| L26 | /start STALE flag triggered autopilot — overwrote good docs without being asked | /start detected STALE marker + auto-commit-pending. User asked "do you have this context?" (a yes/no question). Instead of answering, went on autopilot and rewrote handoff.md, session-log.md, and current-state.md — overwriting session 7+8's successful manual wrap. Root cause: treated infrastructure signals (STALE flag) as implicit permission to act. STALE means "verify before trusting" not "rewrite now." | A diagnostic flag is not a work order. When /start flags something, report it to the user — don't fix it unprompted. Answer questions before acting. If the user asks a question, the response is an answer, not a file write. |
| L27 | Significant scope expansion between versions is a new proposal — V1 approval doesn't cover V2 | V1 /simulate was challenged correctly (session 4: propose → challenge → plan → build). V2 was 4x larger scope (IR extraction, persona generation, 3-agent simulation loops, rubric generation) but was treated as an "evolution" of V1. Sessions 7-8 built 2,073 lines of V2 code, THEN challenged it. The challenge ran too late and all 3 models converged on a wrong "don't build" verdict because they lacked operational evidence. Root cause: V2 felt like V1 continuation, not new work needing its own gate. | When scope significantly expands between versions (new abstractions, 2x+ code, new infrastructure), treat it as a new proposal requiring its own /challenge gate — even if the prior version was already approved. "Evolving an approved design" and "proposing new work" feel the same in the moment but aren't. |
| L28 | Cross-model panels converge on wrong answers when operational evidence is missing from input | 3 independent models all said "sim-compiler is commodity, don't build" — unanimous and wrong. Root cause: proposal lacked eval_intake.py's track record (17 rounds, 3.3→4.5 improvement). Models said "DeepEval does this" without anyone checking whether DeepEval actually meets the specific requirements (it doesn't — no structured persona hidden state, hardcoded simulator prompts, no agent procedure testing). Absence of bugs was treated as absence of need (survivorship bias). Dramatic quantitative findings (18/22 missing Safety Rules) crowded out qualitative evidence (simulation proved its value). | Challenge inputs must include operational evidence when it exists. "Commodity" claims about external tools must be verified against specific requirements before influencing judgment, not just category-matched. Unanimous convergence from models with the same incomplete context is correlated error, not strong consensus. |

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
| L13 | Subsumed by D6 (fork-first format) | 2026-04-14 |
| L14 | Subsumed by D7 (pre-flight discovery) | 2026-04-14 |
| L15 | Subsumed by D7 (adaptive questioning) | 2026-04-14 |
| L16 | Subsumed by D5 (single-model for thinking) | 2026-04-14 |
| L17 | Fix shipped in audit-batch2 (field name mismatches) | 2026-04-11 |
| L18 | Fix shipped (standalone test scripts in run_all.sh) | 2026-04-11 |
| L21 | Structurally fixed by D15 (review-panel --models) | 2026-04-11 |
| L23 | Resolved — security posture modifier wired to --models path | 2026-04-11 |

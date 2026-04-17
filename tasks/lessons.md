# Lessons

Mistakes, surprises, and patterns worth remembering. Each entry is a lesson learned from real work on this project.

**Convention:** Titles are assertions, not topics. "Long sessions silently eat their own corrections — compact at 50-70% context" — not "Session quality." The title IS the takeaway.

**Target:** Keep this file under 30 active entries. When it grows beyond that, promote recurring lessons to `.claude/rules/` files and archive one-offs.

---

| # | Lesson | Source | Rule |
|---|---|---|---|
| L25 | Review-after-build has no enforcement — advisory rules in 3 places all failed silently | Built /simulate (6 files), ran /simulate to validate, fixed issues, declared done — never suggested /review. Plan said "run /review when complete", routing table condition #6 matched (3+ files, no review artifact), but all three are advisory text. No hook checks mid-session state. The intent router watches user messages, not workflow state. Context decay over a long build session made the advisory invisible. | Advisory rules fail under context pressure. Review-after-build needs structural enforcement: either a post-build hook or mid-session state check in the intent router. |
| L28 | Cross-model panels converge on wrong answers when operational evidence is missing from input | 3 independent models all said "sim-compiler is commodity, don't build" — unanimous and wrong. Root cause: proposal lacked eval_intake.py's track record (17 rounds, 3.3→4.5 improvement). Models said "DeepEval does this" without anyone checking whether DeepEval actually meets the specific requirements (it doesn't — no structured persona hidden state, hardcoded simulator prompts, no agent procedure testing). Absence of bugs was treated as absence of need (survivorship bias). Dramatic quantitative findings (18/22 missing Safety Rules) crowded out qualitative evidence (simulation proved its value). | Challenge inputs must include operational evidence when it exists. "Commodity" claims about external tools must be verified against specific requirements before influencing judgment, not just category-matched. Unanimous convergence from models with the same incomplete context is correlated error, not strong consensus. |
| L30 | V2 pipeline quality gap is structural (persona format + mid-loop interventions), not architectural — and the fix isn't more automation | Built full V2 pipeline (1,520 lines, 151 tests), scored 3.11/5 vs eval_intake's 4.73. Added turn_hooks (spike), got to 3.70. Three root causes resist generalization: thin persona cards, skill-specific register rules, hooks bolted on rather than co-evolved. Cross-model panel (3 models) converged: eval_intake's quality came from 17 iterations of watching-and-fixing, not from any architectural decision. Front-loading knowledge via questionnaire won't work because humans are better critics than oracles. | Simulation quality comes from iterative refinement on concrete failures, not from upfront configuration or automation. When building evaluation frameworks, design for critique loops (run → review transcript → annotate failures → adjust → rerun) not for zero-setup automation. |
| L31 | Rubric dimensions must measure product outcomes not interaction style | Spike optimization focused on register_match and flow — style dimensions. The actual value question is: did the skill identify the real problem, reach a useful conclusion, help the user make a better decision? Style dims are noise that distracts from substance. | When building rubrics or evaluation criteria for skills, frame dimensions around: problem identification, conclusion quality, decision support, time efficiency. Drop tone/register/flow dimensions unless the skill is specifically about communication. |
| L32 | Runtime directive injection degrades simulation quality — eval_intake worked by changing skill prompts, not runtime context | D22 critique loop spike: hand-crafted directives injected every turn scored 1.78 avg vs 2.50 baseline (degradation, not improvement). 3-model pre-mortem converged on "wrong mechanism" — eval_intake's 17 iterations changed SKILL.md text directly, not runtime executor context. Injecting directives adds cognitive load to the executor without changing its core instructions. | Simulation quality improvements must modify the skill prompt itself (the artifact being tested), not the simulation runtime. If building future critique loops, the output of each iteration should be a SKILL.md diff, not a runtime directive. |
| L33 | debate.py --enable-tools produces false verification claims with high confidence — deterministic checks beat probabilistic review for verifiable facts | Challenge session 18: Claude Opus ran 54 tool calls (125s, hit max turns) and falsely claimed BuildOS hooks don't exist (searched scripts/ instead of hooks/). GPT-5.4 made the same error in 8 tool calls (31s). Judge accepted the false claim at 0.98 confidence. A single `ls hooks/` would have answered correctly in 0.1s. Meanwhile, Gemini 503'd for 18 min through 4 retries. | For verifiable claims (file exists, function present, config value), use deterministic checks (grep, ls, test hooks) not multi-model debate. Consider removing --enable-tools from /challenge — the tool calls produced false confidence, not better results. debate.py's value is subjective judgment (scope, design, architecture), not fact verification. |
| L36 | Zero-functionality refactors of a monolith are safe when the test suite is fast and commits stay small | debate.py split this session: 4,629 → 4,369 lines across 4 commits, each extracting one subcommand. Pattern: function body moves to `scripts/debate_<topic>.py` verbatim; debate.py re-imports the name; a lazy `import debate` inside the new module pulls shared state. 923 tests stayed green between every commit (7s suite enabled fast verification). Zero behavior change by construction — no logic moved relative to callers. | Fast test suite (sub-10s) + small commits + lazy imports for shared state = monolith extraction without risk. Don't need a full package restructure; sibling modules work if the monolith is already the shared-state module. The "cannot lose any functionality" constraint is met by construction — extraction is a rename, not a refactor. |
| L37 | Rules that depend on author discipline keep failing — enforcement has to live in a single owned surface, not in prose | `/start` dumped raw JSON from 4 diagnostic scripts at every session start even though `.claude/rules/skill-authoring.md` already had a "No Framework Plumbing" rule. The rule caught violations only when the user complained. Fix was structural: scripts go silent-on-success, `scripts/bootstrap_diagnostics.py` is the one file that owns the user-visible output surface. New diagnostics register with the wrapper instead of adding Bash calls to the skill — authors physically can't leak plumbing because they don't touch stdout. | When a class of violation recurs despite an existing rule, escalate on the enforcement ladder: move the behavior into a single-owner artifact (wrapper, hook, codegen, generated file) so "leaking" stops being a thing authors can accidentally do. Prose rules work for one-offs; recurring patterns need structural ownership. |
| L39 | Monolith extractions surface latent module-identity splits when test files manipulate `sys.modules` — refines L36 with the boundary condition | debate.py split 6/N (cmd_explore extraction). 3 test files (test_debate_posture_floor.py, test_debate_pure.py, test_debate_utils.py) had a module-level `for mod in sys.modules: del sys.modules[mod]; import debate` block. At pytest collection time this created two distinct `debate` module objects. `fake_credentials` patched module A (test_debate_commands.py's `debate` reference). The extracted `cmd_explore`'s lazy `import debate` resolved to module B from sys.modules → unpatched → 3 `TestCmdExplore` tests failed in the full suite, passed in isolation. Before the extraction, `cmd_explore` lived inside module A; its `__globals__` lookup pointed at A regardless of what sys.modules contained. The lazy-import pattern's "zero behavior change" property held only because no one was mutating sys.modules between collection and test run. Prior session's diagnosis ("pre-existing test-ordering pollution, not extraction regression") was wrong — the extraction is what surfaced the bug. Fixed by removing the cargo-cult sys.modules block from the 3 test files (commit c993edf), then committing the split. | L36's "safe by construction" claim is correct only when no test code manipulates `sys.modules`. Before any monolith extraction: `grep -rn 'sys\.modules' tests/`. If matches exist, fix them first (they're almost always cargo-cult — a plain `import debate` exposes everything). After extracting, run the FULL suite (not just the file-under-test) at least once to catch lazy-import vs. fixture-patching gaps. Module-identity splits are invisible at code-review time — they only surface when call-time lookup meets cross-module monkeypatching. |

---

## Promoted lessons

When a lesson has been promoted to a `.claude/rules/` file or a hook, remove it from the active table above and record the promotion here. This keeps the active list lean (target: ≤30 entries) while preserving provenance. See [the enforcement ladder](../docs/the-build-os.md#part-v-the-enforcement-ladder) for when to escalate.

Before promoting a lesson, state how you would catch a violation of the resulting rule. If you can't describe a concrete test, the lesson isn't ready for promotion.

| # | Promoted to | Date |
|---|---|---|
| L12 (original) | `.claude/rules/security.md` — "Use HttpOnly cookies, never auth in URLs" | 2026-03-01 |
| L20 | `.claude/rules/skill-authoring.md` — "Persona Definition — Problem-First, No Style Classification" | 2026-04-11 |
| L22 | `.claude/rules/skill-authoring.md` — "Skill frontmatter description must be single-line quoted string" | 2026-04-14 |
| L27 | `.claude/rules/workflow.md` — "Scope expansion = new challenge gate" | 2026-04-16 |
| L34 | `hooks/hook-context-inject.py` — PreToolUse:Write\|Edit context injection (test names + import sigs + git log) | 2026-04-16 |
| L38 | `.claude/settings.json` — all hook commands rewritten to use `$CLAUDE_PROJECT_DIR/hooks/...` | 2026-04-16 |

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
| L29 | Subsumed by D21 (judge step shipped in standard /challenge) | 2026-04-16 |
| L35 | Resolved — Stop-hook safety net removed in commit 9e69929 (−141 lines) | 2026-04-16 |

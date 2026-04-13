---
scope: "Three debate engine upgrades: refine critique mode, intelligent model routing, context-aware skills"
surfaces_affected: "scripts/debate.py, config/debate-models.json, .claude/skills/think/SKILL.md, .claude/skills/*/SKILL.md, .claude/rules/reference/debate-invocations.md"
verification_commands: "python3.11 -m pytest tests/test_debate_smoke.py -v && python3.11 scripts/debate.py review --help && python3.11 scripts/debate.py refine --help"
rollback: "git revert <sha>"
review_tier: "Tier 1.5"
verification_evidence: "PENDING"
challenge_skipped: true
---

# Plan: Debate Engine Upgrades (3 tracks)

Three independent improvements that came out of the 2026-04-13 review session. They share no code dependencies and can be built in any order or in parallel.

## Track 1: Refine Critique Mode

**Brief:** `~/debates/tasks/buildos-refine-mode-upgrade.md` (reviewed by 4 models, updated with all feedback)
**What:** Add `--mode critique` to the refine subcommand. Auto-detect from pressure-test frontmatter.
**Why:** Refine rounds degrade critique quality by converting observations into implementation plans.
**Touches:** `scripts/debate.py` (cmd_refine, refine prompts, argparse), `debate-invocations.md`
**Size:** M — new prompts require iteration

### Build steps
1. Change `--mode` argparse default to `None`, add `{proposal, critique}` choices
2. Change `--rounds` argparse default to `None`, resolve based on effective mode (critique=2, proposal=6)
3. Add `_detect_refine_mode()` helper: reads frontmatter, resolves three-way logic
4. Write `CRITIQUE_REFINE_FIRST_ROUND_PROMPT` and `CRITIQUE_REFINE_SUBSEQUENT_ROUND_PROMPT`
5. Write `REFINE_CRITIQUE_POSTURE_RULE` (replaces strategic posture rule in critique mode)
6. Branch in `cmd_refine` round loop: proposal path unchanged, critique path uses new prompts
7. Keep `EVIDENCE_TAG_INSTRUCTION` and `{judgment_context}` in both modes
8. Verification: 6 test cases per the updated brief

## Track 2: Intelligent Model Routing

**Design doc:** `tasks/model-routing-design.md`
**What:** Add `task_routing` config and `--model auto` / `--models auto` to the review command.
**Why:** Model selection is ad-hoc. Different models have measurably different strengths.
**Touches:** `config/debate-models.json`, `scripts/debate.py` (_resolve_reviewers, new classifier), `debate-invocations.md`
**Size:** S-M — config + ~50 lines routing logic + heuristic classifier

### Open questions (resolve before building)
1. `auto` as default vs explicit flag
2. Perplexity routing: automatic vs flag-triggered
3. Per-skill overrides vs global config only

### Build steps
1. Add `task_routing` and `panel_routing` sections to `debate-models.json`
2. Write `_classify_task_type(input_text, prompt, file_path)` heuristic
3. Wire `auto` into `_resolve_reviewers()` — when model is "auto", classify and look up
4. Log routing decision to stderr
5. Update `debate-invocations.md` with auto examples
6. Verification: route implementation review → GPT, strategic review → Claude, panel auto → 3-model mix

## Track 3: Context-Aware Skills

**Design doc:** `tasks/context-aware-skills-design.md`
**What:** Add Phase 0 context assessment to skills so they skip intake questions when conversation already has the answers.
**Why:** Skills assume cold starts. Mid-conversation invocations re-ask things that are already known.
**Touches:** `.claude/skills/think/SKILL.md` (first), then other skills
**Size:** S — prompt-level change, ~10 lines per skill

### Build steps
1. Write shared Phase 0 preamble text
2. Add to `/think` SKILL.md (both discover and refine modes)
3. Test: invoke `/think discover` with rich conversation context → should skip intake
4. If validated, roll out to `/challenge`, `/explore`, `/investigate`
5. Verification: invoke skill mid-conversation, confirm it references existing context instead of re-asking

## Execution Strategy

**Decision:** parallel — all three tracks are independent
**Pattern:** fan-out

| Track | Files | Depends On | Isolation |
|-------|-------|------------|-----------|
| 1: Refine critique mode | debate.py (cmd_refine section), debate-invocations.md | — | worktree |
| 2: Model routing | debate.py (_resolve_reviewers), debate-models.json, debate-invocations.md | — | worktree |
| 3: Context-aware skills | .claude/skills/think/SKILL.md | — | none (prompt-only) |

**Conflict zone:** Tracks 1 and 2 both touch `debate.py` and `debate-invocations.md`. If built in parallel worktrees, merge reconciliation needed. If built sequentially, no conflicts.

**Synthesis:** Main agent merges branches, runs smoke tests, resolves any debate-invocations.md conflicts.

## Priority Order

1. **Track 3 (context-aware skills)** — smallest change, highest immediate friction reduction, validates approach before investing in larger tracks
2. **Track 1 (refine critique mode)** — fully specified, reviewed by 4 models, ready to build
3. **Track 2 (model routing)** — open questions need resolution first

## Verification

- All existing smoke tests pass: `python3.11 -m pytest tests/test_debate_smoke.py -v`
- Track 1: `debate.py refine --help` shows `--mode` flag
- Track 2: `debate.py review --model auto` routes correctly
- Track 3: `/think discover` skips intake when context exists

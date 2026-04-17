---
scope: "Audit whether dual-mode (paired tools-on + tools-off) generalizes from Frame to architect/security/pm personas via n=5 paired-validation matrix; ship persona-expansion extensions conditional on pre-committed 5/5-bidirectional threshold."
surfaces_affected: "scripts/debate.py, config/debate-models.json, .claude/skills/challenge/SKILL.md, .claude/rules/review-protocol.md, tests/test_debate_pure.py, tasks/dual-mode-generalization-results.md, tasks/lessons.md"
verification_commands: "python3.11 -m pytest tests/test_debate_pure.py -v && python3.11 scripts/debate.py check-models && cat tasks/dual-mode-generalization-results.md"
rollback: "git revert HEAD for code changes; rm -rf tasks/dual-mode-generalization-{architect,security,pm}/ tasks/dual-mode-generalization-results.md to discard research artifacts"
review_tier: "Tier 1.5"
verification_evidence: "PENDING"
challenge_skipped: true
challenge_skip_reason: "Extension of existing Frame persona-expansion pattern with pre-committed validation threshold; no new abstraction, no new dependency, no scope expansion beyond what L43 explicitly opens. User confirmed skip after /think refine."
related_briefs: "tasks/dual-mode-generalization-think.md"
validation_precedent: "tasks/frame-lens-validation.md (Round 1 methodology)"
shipped_commit:
components:
  - Phase 0 architect smoke test (single paired run)
  - Architect persona matrix (5 proposals x 2 modes)
  - Security persona matrix (5 proposals x 2 modes)
  - PM persona matrix (5 proposals x 2 modes)
  - Results synthesis + per-persona decision + L43 update
  - Conditional ship (debate.py + config + skill + rule + tests)
---

# Plan: Dual-Mode Generalization Audit

Extend the Frame lens dual-mode pattern to architect/security/pm personas, conditional on each passing the same 5/5-bidirectional threshold Frame did. Pre-committed methodology, pre-committed decision criterion, conditional ship.

## Build Order

### Phase 0 — Smoke test (blocking gate)
1. Run architect persona, tools-on + tools-off, on the `autobuild` proposal. Verify: (a) both modes return structured MATERIAL findings, (b) no debate.py crash, (c) latency within Round 1 precedent (<120s per half typical, outliers noted).
2. If Phase 0 fails: fix-forward on debate.py persona-expansion logic before scaling. Do not proceed to Phase 1 on broken infra.

### Phase 1 — Persona matrices (3 independent tracks, one per persona)
3. For each persona (architect / security / pm), run each of the 5 proposals (autobuild, explore-intake, learning-velocity, streamline-rules, litellm-fallback) twice — once `--enable-tools`, once without. 10 runs per persona, 30 total.
4. Write outputs to `tasks/dual-mode-generalization-{persona}/{proposal}-{mode}.md` for traceability.

### Phase 2 — MATERIAL-finding tagging + decision
5. For each (persona, proposal) pair, tag each MATERIAL finding as one of: `tools-on-exclusive`, `tools-off-exclusive`, `present-in-both`. Use the same rubric as frame-lens-validation Round 1.
6. Build per-persona 5-row table: proposal × finding-count-by-tag. Mark each proposal as `BIDIRECTIONAL` (both modes have ≥1 exclusive finding) or not.
7. Apply pre-committed decision: adopt dual-mode for persona iff **all 5/5 proposals are BIDIRECTIONAL**. Record verdict per persona.
8. Write `tasks/dual-mode-generalization-results.md` with all three persona tables, the verdicts, and a cross-persona summary.
9. Update `tasks/lessons.md` L43 with per-persona evidence — regardless of adopt/decline. This step runs whether or not any persona adopts.

### Phase 3 — Conditional ship (only for personas that pass)
10. If **no persona passes**: stop. L43 now documents Frame's dual-mode is unique to candidate-set critique. Commit research artifacts + L43 update.
11. If **≥1 persona passes**:
    - Extend `scripts/debate.py` persona-expansion logic to cover the passing personas (Frame is the template).
    - Update `config/debate-models.json` with `{persona}_factual_model` entries matching Frame's pattern.
    - Update `.claude/skills/challenge/SKILL.md` Step 6 + Step 7 + Step 1 example persona lists.
    - Update `.claude/rules/review-protocol.md` Stage 1 paragraph to document the generalized dual-mode coverage.
    - Extend `tests/test_debate_pure.py` with validator scope tests + per-persona TestPersona class (Frame precedent).
12. Run `python3.11 -m pytest tests/test_debate_pure.py` — all pass.
13. Run `/review` on the diff (Tier 1.5 requires quality review).
14. Record `shipped_commit: <hash>` in this plan's frontmatter after merge.

## Files

| File | Action | Scope |
|---|---|---|
| `tasks/dual-mode-generalization-{architect,security,pm}/*.md` | create (30 files) | Debate run outputs, one per (persona, proposal, mode) |
| `tasks/dual-mode-generalization-results.md` | create | Per-persona tables + verdicts + cross-persona summary |
| `tasks/lessons.md` | modify | Update L43 with per-persona evidence (always, regardless of outcome) |
| `scripts/debate.py` | modify (conditional) | Extend persona-expansion logic to passing personas |
| `config/debate-models.json` | modify (conditional) | Add `{persona}_factual_model` entries |
| `.claude/skills/challenge/SKILL.md` | modify (conditional) | Update default persona list references |
| `.claude/rules/review-protocol.md` | modify (conditional) | Update Stage 1 paragraph |
| `tests/test_debate_pure.py` | modify (conditional) | Validator scope + per-persona test classes |

## Execution Strategy

**Decision:** sequential for Phase 0 → Phase 2; Phase 1's three persona matrices are parallelizable but default to sequential (Frame precedent; API latency is the real bottleneck, not tool orchestration).
**Pattern:** pipeline with optional map-reduce in Phase 1.
**Reason:** Phase 0 smoke test MUST gate Phase 1 (broken infra invalidates the matrix). Phase 2 tagging depends on all of Phase 1. Phase 3 ship is conditional on Phase 2 verdicts. Persona matrices in Phase 1 write to disjoint output dirs and don't share code state, so they are eligible for parallel worktree agents if session time pressure appears — but Frame validated serially in single session with no issue.

| Subtask | Files | Depends On | Isolation |
|---|---|---|---|
| Phase 0 smoke | 1 debate run output | — | main session |
| Architect matrix | 10 debate outputs in `tasks/dual-mode-generalization-architect/` | Phase 0 pass | worktree or serial |
| Security matrix | 10 debate outputs in `tasks/dual-mode-generalization-security/` | Phase 0 pass | worktree or serial |
| PM matrix | 10 debate outputs in `tasks/dual-mode-generalization-pm/` | Phase 0 pass | worktree or serial |
| Synthesis | results.md + L43 update | All 3 matrices | main session |
| Ship (conditional) | debate.py, config, skill, rule, tests | Synthesis verdict ≥1 pass | main session |

**Synthesis:** Main session reads all three persona matrices, tags findings, builds tables, applies 5/5-bidirectional threshold, updates L43, then gates Phase 3.

## Verification

```bash
# Phase 0 gate
ls tasks/dual-mode-generalization-architect/autobuild-tools-{on,off}.md

# Phase 2 gate
test -f tasks/dual-mode-generalization-results.md && \
  grep -E 'VERDICT: (ADOPT|DECLINE)' tasks/dual-mode-generalization-results.md | wc -l  # should be 3

# Phase 3 gate (only if any persona adopted)
python3.11 -m pytest tests/test_debate_pure.py -v
python3.11 scripts/debate.py check-models

# L43 always updated
grep -A2 'L43' tasks/lessons.md | head -20
```

## Notes

- **Pre-committed threshold:** Adopt-iff-5/5-bidirectional. Locked before runs. Re-fitting after seeing data counts as a threshold change, not an adoption — document explicitly.
- **No new abstractions.** Persona-expansion logic already exists in `scripts/debate.py` from Frame shipping. This plan reuses it.
- **No scope pivot allowed mid-run.** Per L45, if evaluative language appears mid-session ("is 3/5 enough?", "maybe this one proposal doesn't count"), re-read this plan's frontmatter before acting.
- **Cost/time estimate:** 30 debate.py runs × ~60-120s per run ≈ 30-60 min API wall time, parallelizable. Labor: 1-2 sessions end-to-end.

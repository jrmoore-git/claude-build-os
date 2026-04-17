---
scope: "Audit whether running dual-mode Frame (structural + factual) at proposal intake — BEFORE /challenge fires — reliably catches the frame errors Frame-inside-challenge catches today; ship intake-check mechanism conditional on pre-committed reproduction threshold."
surfaces_affected: "scripts/debate.py, config/debate-models.json, .claude/skills/challenge/SKILL.md, .claude/rules/review-protocol.md, tests/test_debate_pure.py, tasks/frame-reach-intake-audit-runs/, tasks/frame-reach-intake-audit-results.md, tasks/lessons.md"
verification_commands: "python3.11 -m pytest tests/test_debate_pure.py -v && python3.11 scripts/debate.py intake-check --help && cat tasks/frame-reach-intake-audit-results.md"
rollback: "git revert HEAD for code changes; rm -rf tasks/frame-reach-intake-audit-runs/ tasks/frame-reach-intake-audit-results.md to discard research artifacts"
review_tier: "Tier 1.5"
verification_evidence: "PENDING"
challenge_skipped: true
challenge_skip_reason: "User explicitly chose /plan after reviewing /challenge option; audit is a bounded research experiment reusing existing Frame prompts; new subcommand is a composable primitive with no new abstraction beyond what Frame already uses."
related_briefs: "tasks/frame-reach-intake-audit-think.md"
validation_precedent: "tasks/frame-lens-validation.md (Round 2 data is the ground-truth baseline)"
pre_committed_threshold: "See 'Threshold (LOCKED)' section below. No re-fitting after runs execute (L45)."
shipped_commit:
components:
  - Design intake prompt + pick negative-control proposal
  - Run intake dual-mode on 5 audit proposals (10 runs)
  - Run intake on negative-control proposal (2 runs)
  - Tag reproduction rate against frame-lens-validation Round 2 data
  - Results doc + L43 update (research evidence)
  - Conditional ship of debate.py intake-check subcommand + skill wiring
---

# Plan: Frame-Reach Intake Audit

Measure whether dual-mode Frame at proposal intake reliably reproduces the frame errors Frame-inside-challenge catches. Pre-committed threshold. Ship intake-check as a new `debate.py` subcommand + pre-`/challenge` skill step only if threshold passes.

## Threshold (LOCKED — do not re-fit after runs)

Adopt intake-check iff ALL of:

1. **Reproduction rate ≥70% per proposal.** For each of the 5 proposals (autobuild, explore-intake, learning-velocity, streamline-rules, litellm-fallback), intake catches ≥70% of Round 2 Frame-in-challenge MATERIAL findings. (Allows stochastic drift; rejects catastrophic drops.)
2. **Expensive-to-miss binary gate.** On litellm-fallback, intake reproduces the "already-shipped" finding that flipped verdict REVISE → REJECT in Round 2. This is the single highest-cost finding in the corpus; missing it breaks the whole value argument.
3. **Negative control: 0 MATERIAL frame findings on the clean proposal.** Picks a 6th proposal known to be cleanly framed (frame-lens-plan.md after shipping, or equivalent — Phase 0 decides). Intake running on it must produce 0 MATERIAL frame findings. Bounds false-positive rate.

No "novel findings" bonus criterion — since intake uses identical Frame prompts to Round 2, novel findings at intake time would be LLM stochasticity, not real signal. The audit is a RELIABILITY test, not a value-add test. Compute-savings is the downstream value argument, separate from this pass/fail.

## Mechanism (LOCKED)

New `debate.py intake-check` subcommand. Reuses existing `frame-structural` and `frame-factual` prompts from `PERSONA_PROMPTS`. Output: same structure as `debate.py challenge` (anonymized challengers, MATERIAL/ADVISORY tags, verdict).

Why new subcommand vs. hook or inline skill step:
- **Composable primitive.** Other skills can call intake-check independently of `/challenge`. If later we want intake on `/explore` output, a review input, or a PR description, the subcommand exists.
- **Testable in isolation.** Has its own tests; CLI lets us reproduce runs deterministically.
- **Clean rollback.** New code, no modification to existing challenge flow unless the skill body wires it in (Phase 3).

Trade-off: requires a skill-side wiring change (pre-`/challenge` step) to actually run intake before challenge. That's Phase 3 work, only if threshold passes.

## Build Order

### Phase 0 — Design + setup (blocking gate)
1. Write `tasks/frame-reach-intake-audit-prompt.md` specifying the intake prompt. Starting point: reuse `PERSONA_PROMPTS["frame"]` and `PERSONA_PROMPTS["frame-factual"]` verbatim (the brief's Assumption #1). If adaptation is needed, document the diff.
2. Pick the negative-control proposal. Candidates: `tasks/frame-lens-plan.md` (shipped, post-review), `tasks/autobuild-plan.md` (shipped-clean) — pick by grep'ing git log for proposals that passed `/challenge` with no MATERIAL frame findings. Note choice in the audit's prompt doc.
3. Extend `scripts/debate.py` with `cmd_intake_check` — minimal wrapper around the existing challenge dispatch logic that forces `--personas frame` + `--enable-tools`, same persona-expansion path. ~40 LOC.
4. Smoke test: `python3.11 scripts/debate.py intake-check --proposal tasks/autobuild-proposal.md --output /tmp/intake-smoke.md`. Verify output structure matches `challenge` output (frontmatter + `## Challenger A (frame-structural)` + `## Challenger B (frame-factual)` sections).

### Phase 1 — Audit runs (12 total API calls, 6 subcommand invocations)
5. Run intake-check on 5 audit proposals. 5 invocations, each producing dual-mode output (structural + factual in one file). Parallel execution — 10 API calls under the hood, but 5 shell commands.
6. Run intake-check on the negative-control proposal. 1 invocation, 2 API calls.
7. Write outputs to `tasks/frame-reach-intake-audit-runs/{proposal}-intake.md` (one file per proposal — the subcommand handles dual-mode internally, unlike the dual-mode-generalization audit which split modes across files).

### Phase 2 — Tagging + threshold application
8. For each of the 5 audit proposals, read its intake output and the corresponding frame-in-challenge MATERIAL findings from `tasks/frame-lens-validation.md` Round 2. Tag each Round 2 MATERIAL finding as `reproduced` or `missed` by intake. Count per-proposal reproduction rate.
9. Apply Threshold #1: per-proposal reproduction ≥70%. If any proposal is <70% → DECLINE.
10. Apply Threshold #2: check that litellm-fallback intake output contains the "already-shipped" finding (grep for "shipped" or "commit" or specific commit SHAs from Round 2). If missed → DECLINE.
11. Apply Threshold #3: verify negative-control intake output contains zero MATERIAL frame findings. If >0 → DECLINE.
12. Write `tasks/frame-reach-intake-audit-results.md` with per-proposal reproduction table, threshold-check outcomes, and verdict.
13. Update `tasks/lessons.md` L43 (extend with intake-reach evidence) OR add L46 — regardless of outcome.

### Phase 3 — Conditional ship (only if all three threshold gates pass)
14. **If threshold failed:** stop. Document in L43/L46 why intake-stage Frame doesn't reliably reproduce challenge-stage Frame. Defer judge/refine/premortem audits pending this learning.
15. **If threshold passed:**
    - Wire `intake-check` into `.claude/skills/challenge/SKILL.md` as a pre-challenge Phase 0 step. If intake raises MATERIAL frame findings → present to user with verdict (REJECT / REVISE / PROCEED) before running `/challenge` personas.
    - Update `.claude/rules/review-protocol.md` Stage 1 paragraph to document intake-stage frame-check.
    - Add `TestIntakeCheck` class to `tests/test_debate_pure.py` — smoke test, argparse shape, output-file validity.
    - Update `config/debate-models.json` if intake needs its own `intake_factual_model` (otherwise reuses `frame_factual_model`).
16. Run `python3.11 -m pytest tests/test_debate_pure.py` — all pass.
17. Run `/review` on the diff (Tier 1.5).
18. Record `shipped_commit: <hash>` in this plan's frontmatter after merge.

## Files

| File | Action | Scope |
|---|---|---|
| `tasks/frame-reach-intake-audit-prompt.md` | create | Intake prompt spec + negative-control choice |
| `scripts/debate.py` | modify | Add `cmd_intake_check` + argparse (~40 LOC) |
| `tasks/frame-reach-intake-audit-runs/*.md` | create (6 files) | 5 proposals + 1 negative control |
| `tasks/frame-reach-intake-audit-results.md` | create | Reproduction table + threshold outcomes + verdict |
| `tasks/lessons.md` | modify | L43 extension or new L46 on intake-reach evidence |
| `.claude/skills/challenge/SKILL.md` | modify (conditional) | Pre-challenge intake-check step |
| `.claude/rules/review-protocol.md` | modify (conditional) | Stage 1 paragraph update |
| `tests/test_debate_pure.py` | modify (conditional) | TestIntakeCheck class |
| `config/debate-models.json` | modify (conditional) | Intake model config if distinct from frame-factual |

## Execution Strategy

**Decision:** sequential Phase 0 → Phase 1 → Phase 2 → Phase 3; Phase 1's 6 invocations are parallelizable but trivially so (the subcommand handles dual-mode internally).
**Pattern:** pipeline.
**Reason:** Phase 0 must unblock Phase 1 (no subcommand = no runs). Phase 1 must unblock Phase 2 (no runs = no tagging). Phase 3 is conditional on Phase 2 verdict. Within Phase 1, 6 background bash calls (same pattern as dual-mode-generalization audit).

| Subtask | Files | Depends On | Isolation |
|---|---|---|---|
| Phase 0 subcommand | scripts/debate.py + prompt doc | — | main session |
| Phase 1 audit runs | 6 files in `tasks/frame-reach-intake-audit-runs/` | Phase 0 complete | parallel bash, main session |
| Phase 2 tagging | results.md + L43/L46 update | All Phase 1 | main session |
| Phase 3 ship (conditional) | skill + rule + tests + config | Phase 2 PASS verdict | main session |

**Synthesis:** Main session tags findings against Round 2, applies three threshold gates, writes verdict. Phase 3 executes only on PASS.

## Verification

```bash
# Phase 0 gate
python3.11 scripts/debate.py intake-check --help

# Phase 1 gate
ls tasks/frame-reach-intake-audit-runs/*.md | wc -l  # should be 6

# Phase 2 gate
grep -E 'VERDICT: (PASS|DECLINE)' tasks/frame-reach-intake-audit-results.md

# Phase 3 gate (only if PASS)
python3.11 -m pytest tests/test_debate_pure.py::TestIntakeCheck -v
grep -q 'intake-check' .claude/skills/challenge/SKILL.md
```

## Notes

- **Pre-committed threshold is LOCKED.** All three gates (per-proposal 70%, litellm-fallback binary, negative control 0) must pass. Re-fitting after seeing data = threshold change, not adoption. Per L45.
- **Round 2 is the ground truth.** `tasks/frame-lens-validation.md` Round 2 findings are the baseline. If Round 2 is wrong (unlikely — it passed peer review), this audit's comparison is compromised.
- **The audit is a reliability test, not a value-add test.** Since intake reuses Frame prompts, finding-count equality is the expected outcome. The compute-savings argument (don't run 3 personas on a frame-broken proposal) is the real ship rationale; this audit proves the safety precondition.
- **Judge/refine/premortem deferred.** Each is a separate audit with its own threshold pre-commit. If intake fails, those audits may be redesigned based on what we learn here.
- **Dual-mode-generalization evidence disposition (out of scope).** 30 uncommitted runs + architect-adopt verdict from prior work are still on disk. Flagging for session-end decision (commit as research-only, fold into intake results, or leave uncommitted). NOT part of this plan's build order.
- **Cost estimate:** 12 debate.py runs × ~30-100s ≈ 6-20 min API wall time, parallelizable. Labor: 1-2 hours including tagging + conditional ship.

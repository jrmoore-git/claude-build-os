---
topic: judge-stage-frame-reach-audit
phase: 0x + 0a
created: 2026-04-17
related_plan: tasks/judge-stage-frame-reach-audit-plan.md
related_design: tasks/judge-stage-frame-reach-audit-design.md
related_challenge: tasks/judge-stage-frame-reach-audit-challenge.md
verdict: DECLINE
gate_outcome: DECLINE
---

# Judge-Stage Frame-Reach Audit — Phase 0x + Phase 0a Results

## Verdict

**VERDICT: DECLINE** — 1 missed-disqualifier of 5 baseline judge reruns. Threshold was 0-1 → DECLINE. Pre-committed gate per plan Phase 0a step 9. No re-fitting per L45.

Phase 1 (main audit) does not run. Plan-v2 for judge-stage Frame-reach is NOT drafted — the corpus-design learning below supersedes the prior design.

## Phase 0x — Orchestration Readiness: PASS

Smoke test on `tasks/autobuild-judgment.md` / `tasks/autobuild-proposal.md` / `tasks/autobuild-findings.md`:
- Family-overlap check: `author_family=claude`, `frame_structural=gemini` → PASS.
- Credential-pattern pre-check: no matches.
- Frame-structural (gemini-3.1-pro): 11.3s, 1 MATERIAL finding, verdict REVISE.
- Frame-factual (gpt-5.4): 32.1s, 32 tool calls, 2 MATERIAL findings, verdict REVISE.
- Aggregation rule applied: (REVISE, REVISE) → REVISE.
- Output written to `tasks/judge-stage-frame-reach-audit-runs/phase0x-smoke-autobuild.md`.

Orchestration harness confirmed functional. Family-overlap enforcement and credential pre-check operate before any LLM call.

## Phase 0a — Baseline Judge Error Rate

### Corpus

Five Round 2 frame-lens-validation archived debate outputs:

| Slug | Challenge file | Proposal file | Ground-truth verdict (Round 2) |
|---|---|---|---|
| autobuild | `tasks/autobuild-findings.md` | `tasks/autobuild-proposal.md` | REVISE |
| explore-intake | `tasks/explore-intake-challenge.md` | `tasks/explore-intake-proposal.md` | REVISE |
| learning-velocity | `tasks/learning-velocity-findings-v2.md` | `tasks/learning-velocity-proposal.md` | REVISE |
| streamline-rules | `tasks/streamline-rules-challenge.md` | `tasks/streamline-rules-proposal.md` | REVISE |
| litellm-fallback | `tasks/litellm-fallback-challenge.md` | `tasks/litellm-fallback-proposal.md` | **REJECT** (Frame flipped from REVISE via already-shipped detection) |

### Baseline Verdicts (cmd_judge gpt-5.4, re-run 2026-04-17)

| Proposal | Baseline Verdict | Accepted | Dismissed | Tagging vs Ground Truth |
|---|---|---|---|---|
| autobuild | REVISE | 2 | 2 | **correct** |
| explore-intake | REVISE | 2 | 2 | **correct** |
| learning-velocity | REVISE | 2 | 2 | **correct** |
| streamline-rules | REVISE | 2 | 2 | **correct** |
| litellm-fallback | REVISE | 2 | 2 | **missed_disqualifier** |

### Error-Class Counts

- `correct`: 4
- `missed_disqualifier`: 1 (litellm-fallback)
- `false_dismiss`: 0
- `collapsed_defect`: 0

### Gate Application

Pre-committed Phase 0a gate (plan step 9):
- ≥5 missed_disqualifier → PROCEED to plan-v2
- 2-4 errors → DEFER 2-4 weeks for passive corpus growth
- **0-1 errors → DECLINE**

Observed: 1 missed_disqualifier → **DECLINE**.

## Error-Shape Analysis

The single missed-disqualifier (litellm-fallback) is not a pattern — it is a **corpus-measurement misalignment artifact**. Investigation:

- Round 2 ground truth for litellm-fallback = REJECT. The REJECT verdict depended on Frame's factual-mode finding that `scripts/llm_client.py` already implements Anthropic fallback (`_dispatch` detects connection-refused, flips `_FALLBACK_ACTIVE`, etc.). Without Frame in the challenger set, this fact is absent from the input the judge receives.
- The baseline judge on `tasks/litellm-fallback-challenge.md` is given 3-persona findings (architect/security/pm via opus-4-6/gemini/gpt-5.4). None of those three flagged "feature already shipped" in Round 2's archived challenge.
- Baseline judge produced REVISE — the correct verdict *given its input*. It would be impossible for judge to produce REJECT without someone (challenger) surfacing the already-shipped evidence.

This is not "judge missed a disqualifier it should have caught." It is "judge's input did not contain the disqualifying evidence."

The remaining 4 proposals (ground truth REVISE) could not have produced missed-disqualifier errors under any judge behavior — the correct verdict is REVISE, so any baseline verdict of PROCEED/REVISE on them is correct-or-less-strict, not missed-disqualifier.

**Net:** The Round 2 corpus cannot measure judge-stage missed-disqualifier behavior independently of challenger-input completeness. The audit was measuring the wrong thing — or, more precisely, the corpus was Frame-dependent ground truth paired with Frame-absent judge input.

## Learnings

1. **Corpus-ground-truth alignment is a prerequisite.** A corpus where ground truth depends on signals NOT present in the measurement input produces systematic "missed disqualifier" readings that don't measure judge quality. Future judge-stage audits need one of:
   - Corpus where ground truth is derivable from the 3-persona findings alone (no Frame-dependent ground truth), OR
   - Measurement design that feeds Frame-augmented findings to judge (so judge has the same evidence the ground truth used).

2. **Phase 0a as a kill-switch worked.** The pre-committed gate stopped work after ~30 min once the corpus-misalignment became clear. Without the gate, we would have built Phase 0c/0d/0e/Phase 1 on top of a corpus that can't discriminate.

3. **Phase 0x orchestration is reusable.** `scripts/judge_frame_orchestrator.py` is now on disk with tools + family check + credential pre-check working. Any future judge-stage audit can reuse it without rebuilding. Sunk cost on Phase 0x is not wasted — it is a reusable primitive.

4. **Baseline cmd_judge (gpt-5.4, 2026-04-17 config) handles the 3-persona case correctly on this corpus.** 4/5 verdicts matched ground truth. The one deviation is attributable to input-completeness, not adjudication error. This is a null signal on "is baseline judge unreliable enough to need Frame at the judge stage" — we have no positive evidence either way from this corpus.

## Next Action

- **This plan is CLOSED.** Phase 1/3 do not execute.
- Do NOT draft plan-v2 on the Round 2 corpus. Any future judge-stage Frame-reach audit must first design a corpus that survives the measurement-independence check above.
- Candidate corpus-design approaches (future session, not this one):
  - **Frame-augmented corpus:** Include Frame findings in the challenger set before running baseline judge. Measures "does judge handle a full 4-persona input correctly?" — but then Frame-at-judge would be redundant with Frame-in-challenge.
  - **Labeled debate-log corpus:** Exhaustively label `stores/debate-log.jsonl` for historical judge verdicts where ground truth is derivable from challenger findings alone (no Frame dependence).
  - **Synthetic judge-error corpus:** Hand-build challenge outputs with embedded disqualifiers that baseline judge systematically mishandles. Realism trade-off noted by Challenge 8.
- **Update L43** with judge-stage corpus-misalignment evidence (below).

## Files Produced

- `scripts/judge_frame_orchestrator.py` (new, reusable)
- `tasks/judge-stage-frame-reach-audit-runs/phase0x-smoke-autobuild.md`
- `tasks/judge-stage-frame-reach-audit-runs/phase0a-baseline-autobuild.md`
- `tasks/judge-stage-frame-reach-audit-runs/phase0a-baseline-explore-intake.md`
- `tasks/judge-stage-frame-reach-audit-runs/phase0a-baseline-learning-velocity.md`
- `tasks/judge-stage-frame-reach-audit-runs/phase0a-baseline-streamline-rules.md`
- `tasks/judge-stage-frame-reach-audit-runs/phase0a-baseline-litellm-fallback.md`
- This file.

## Compute Used

- Phase 0x smoke: 1 orchestrator run (2 LLM calls + 32 tool calls), ~32s wall.
- Phase 0a: 5 parallel `cmd_judge` invocations (each with claim verifier + consolidation + judge), ~1-2 min wall (parallel).
- Total API calls: ~20-25. Total wall time for execution: ~3-5 min. Dev time for orchestrator: ~1.5 hr.

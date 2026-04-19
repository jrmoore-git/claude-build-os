---
topic: arm-study-n10-kickoff
created: 2026-04-19
phase: pre-kickoff handoff
status: BLOCKED-on-user-authorization
prerequisites_for_kickoff:
  - cost sign-off (per L49)
  - 10-proposal selection sign-off
  - session-isolation protocol (per D38)
---

# Arm-study n=10 kickoff — handoff

Steps 1–6 of the autonomous run are complete (commits `b18d97c` →
`ce4105a` on main). REDESIGNs A/B/C shipped + post-build review patches
+ B-variant pre-registration + n=3 sanity rerun. Step 7 (n=10 kickoff)
needs explicit user authorization before spending real money.

## What's ready

| Concern | Status |
|---------|--------|
| FALSIFIED-mechanism classifier (REDESIGN A) | Built; calibration script ready (`scripts/arm_study_a3_calibration.py`); INV-1 hand-labeling not yet run on 60 collected claims |
| Multi-model discoverer ensemble + matcher v2 (REDESIGN B) | Built; not yet exercised on real data |
| Paired bootstrap thresholds (REDESIGN C) | Built; locked thresholds JSON committed (SHA256 captured per-run); n=3 rerun verified methodology |
| B-variant pre-registration | Locked (`tasks/arm-study-b-prereg.md`) |
| Cross-model `/review` post-build | Round 1 + Round 2 patches landed; round 3 deferred (diminishing returns) |

## Gate 1 — Cost sign-off (per L49)

Real-data projection from `stores/debate-log.jsonl` (20 most recent
challenges + 20 most recent reviews):

- Per-arm challenger run mean: **$3.68** (median $4.30, max $9.28)
- 20 arm runs (10 proposals × 2 arms): **~$73.69**
- Discoverer ensemble (Sonnet + GPT + Gemini × 10): **~$15-25**
- Verifier + REDESIGN A classifier passes: **~$5**
- REDESIGN B borderline adjudicator: **<$1**
- Retrospective scorer (Dim 6): **~$5**
- **Total estimated: $100-130**

This excludes any iteration cost if the n=10 run reveals issues
requiring partial reruns. Worst case (one arm fully reruns): +$50.

Confirm before kickoff:
- [ ] Cost authorized
- [ ] Iteration budget acknowledged

## Gate 2 — 10-proposal selection sign-off

From `tasks/arm-study-workload-inventory.md` proposed-10:

| # | Proposal | Stratum | Date |
|---|----------|---------|------|
| 1 | streamline-rules | governance | 2026-04-12 |
| 2 | read-before-edit-hook | governance | 2026-04-15 |
| 3 | learning-velocity | governance | 2026-04-11 |
| 4 | managed-agents-dispatch | architecture/design | 2026-04-10 |
| 5 | litellm-fallback | architecture/design | 2026-04-12 |
| 6 | efficiency-pass-2 | architecture/design | 2026-04-18 |
| 7 | autobuild | code-change | 2026-04-16 |
| 8 | buildos-improvements | code-change | 2026-04-16 |
| 9 | debate-efficacy-study | research/exploratory | (date in inventory) |
| 10 | judge-stage-frame-reach-audit | research/exploratory | (date in inventory) |

Confirm before kickoff:
- [ ] Selection approved (or sub list)
- [ ] Proposal artifacts at `tasks/<slug>-proposal.md` exist for each

## Gate 3 — Session-isolation protocol (per D38)

Plan calls for 3 separate Claude Code sessions: arm-A, arm-B, scorer.
Bias-control rationale: each Claude Code session sees only one arm's
output, can't cross-contaminate when reasoning about results.

Two execution paths:

**Path A — Strict isolation (per spec):**
- User opens 3 Claude Code sessions manually.
- Session 1: `python3.11 scripts/arm_study_orchestrator.py --arm-only a --proposals <list> --run-id n10-2026-04-XX`
- Session 2: `python3.11 scripts/arm_study_orchestrator.py --arm-only b --proposals <list> --run-id n10-2026-04-XX`
- Session 3: scorer + miss-discoverer + retrospective + verdict.
- Methodologically clean.

**Path B — Same-session with subprocess isolation:**
- Run all 3 stages as subprocesses inside this Claude Code session.
- Each subprocess is process-isolated; orchestrator never asks the
  parent session for anything mid-run.
- Risk: my reasoning about Arm A's outputs (in conversation) could
  shape my outputs about Arm B (small but non-zero).
- Mitigation: I emit no analysis between subprocess steps; each step
  is a Bash invocation + a status line.

Recommended: **Path A** — the bias-control rationale (D38) was specifically
about session isolation, not subprocess isolation. The cost of opening 3
sessions is small; the cost of a methodological hole in a $100+ study
is large.

Confirm before kickoff:
- [ ] Path A (separate sessions) — recommended
- [ ] Path B (same session, subprocess) — acceptable if A impractical

## What I'll do once gates clear

If Path A: produce the 3 ready-to-paste commands for each session and a
final-stage script for Step 8 (apply B variants to scored.json).

If Path B: kick off arm-A as a background subprocess in this session,
monitor; on completion, kick off arm-B; on completion, scorer +
discoverer + retrospective + verdict; then Step 8.

## Step 8 (post-n=10) preview

After scored.json files exist:
1. Verify SHA256 lock against `arm_study_thresholds.json` via `--expected-thresholds-sha`.
2. Apply each B variant from `tasks/arm-study-b-prereg.md` (3 variants × multiple settings).
3. Emit `stores/arm-study/sensitivity-report-n10.md` with per-dim verdict under each variant.
4. Flag any dim where verdict differs across variants ("weight-fragile" / "stratification-fragile" / "composition-fragile").

This is mostly arithmetic over scored.json — no significant additional LLM
cost.

## Status

**BLOCKED on user authorization**. Steps 1–6 + post-build patches done
on commits `b18d97c` → `ce4105a`. Awaiting go on cost + selection +
session-isolation protocol.

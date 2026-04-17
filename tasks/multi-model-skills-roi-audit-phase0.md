---
topic: multi-model-skills-roi-audit
created: 2026-04-17
phase: 0 (feasibility check)
verdict: GO
related_design: tasks/multi-model-skills-roi-audit-design.md
---

# Phase 0 — Feasibility Check for `/challenge` ROI Audit

## Verdict

**GO.** Corpus density clears the design threshold by ~20x. Proceed to Phase 1.

## Corpus Map

| Metric | Value |
|---|---|
| Total `/challenge` invocations logged in `stores/debate-log.jsonl` | 111 |
| After filtering efficacy-study arm-D synthetic runs | 99 |
| With output still on disk (auditable) | 66 |
| **MATERIAL findings across disk-resident corpus** | **451** |
| Runs with ≥1 downstream artifact (plan / review / refined / session-log mention) | 33 / 66 (50%) |
| Runs with decisions.md mention | ~0 |
| Time concentration | 108 / 111 entries in April 2026 |

## Phase-Breakdown of Full Log (for later phases)

| Phase | Count |
|---|---|
| challenge | 111 |
| review | 88 |
| refine | 76 |
| review-panel | 61 |
| judge | 39 |
| explore | 34 |
| outcome | 16 (all `test-proposal` dev entries — no real labels) |
| compare | 14 |
| pressure-test | 12 |
| pre-mortem | 7 |
| research | 1 |
| synthesize | 1 |

Total multi-model invocations logged: 460. Plenty of cross-skill data for Phase 3 replication.

## Infrastructure Gaps Discovered

1. **Output deletion untracked.** 33 of 99 real `/challenge` runs have no file on disk. Post-ship cleanup is eating audit evidence. **Fix candidate:** `/wrap` preserves challenge/review outputs for a configurable retention window, or archives them to `stores/challenge-archive/` before `/ship` moves on.
2. **`decisions.md` is not the right outcome source.** Zero sampled runs link their findings to a decision entry. Outcome tracing will route through: `tasks/<topic>-plan.md` frontmatter (`shipped_commit`, `implementation_status`), `tasks/*-review.md` artifacts, git commit messages, and session-log entries.
3. **`cmd_outcome_update` tool is live but only populated with test data.** All 16 `outcome` log entries are dev/test for `test-proposal`. Real outcome labels are net-new labor. Recommendation: wire `cmd_outcome_update` into `/ship` so every shipped feature emits an outcome entry for its originating `/challenge` or `/review`.

## Recommendation for Phase 1 Scope

**First labeling pass: ~20 most-recent non-autopilot `/challenge` runs with ≥1 downstream artifact.**

Rationale: that narrows 451 findings to ~100-150 — enough to build and stress-test the 4-category rubric without drowning in labor. After rubric is frozen on that subset, extend to the full 66-run corpus if needed for confidence. If the rubric converges and the verdict is clear at n≈20, stop there; L44's n≥5 bar is cleared by 4x.

## Not Blocking Phase 1 But Worth Noting

- **Contamination caveat stands.** The same Claude that labels findings may have seen those proposals in context. Mitigation: dual-label 20% with Justin, measure inter-rater agreement.
- **Corpus recency helps.** Fresh memory (April 2026) means outcome-tracing against commits is straightforward — no archaeology into March/February proposals.
- **`/review`, `/polish`, `/pressure-test`, etc. corpora are viable for Phase 3.** 88/76/12 entries respectively. No need to widen Phase 1 scope preemptively.

## Next Action

Write the Phase 1 labeling rubric. Target file: `tasks/multi-model-skills-roi-audit-rubric.md`. Pilot on 5 findings, iterate, freeze. Then label ~20 invocations, compute ROI, emit verdict.

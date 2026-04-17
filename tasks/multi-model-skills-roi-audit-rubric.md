---
topic: multi-model-skills-roi-audit
phase: 1 (rubric)
created: 2026-04-17
status: DRAFT (pilot pending)
related_design: tasks/multi-model-skills-roi-audit-design.md
---

# Phase 1 Labeling Rubric

For every `[MATERIAL]` finding in audited `/challenge` (and later other-skill) runs, assign one label from the table. Rubric is v0 — pilot on 5 findings, revise, then freeze.

## Labels

| Label | Name | Weight | Assign when… |
|---|---|---|---|
| **(a)** | Prevented real problem | **+3** | Finding names a concrete problem that would have caused incident / rework / security issue / wrong-thing-shipped. A commit exists that addresses it AND the fix was non-trivial (would have cost hours+ to discover post-ship, or is an irreversible class — data loss, security, production). |
| **(b)** | Changed plan meaningfully | **+1** | Finding altered the proposal / plan / implementation in a way that's visible downstream (session-log reference, plan revision, refined artifact, review escalation). Change is real but not catastrophic-avoiding — e.g., scope contraction, different ordering, different abstraction. |
| **(c)** | Noise / ignored | **0** | Finding was acknowledged but not acted on. No commit, no plan revision, no refined mention. Includes valid-but-unacted — the finding may have been correct but did not trigger any change. Default label when no downstream signal exists. |
| **(d)** | Actively wrong | **-1** | Finding's premise was false: hallucinated fact, misread code, named a problem that didn't exist, recommended an action contradicted by a more-accurate check. L33-style false claims. Still counts as negative even if reader caught the error — it consumed reader attention. |
| **(e)** | Mixed / unclear | **skip** | Escape hatch. Use when the finding splits into 3+ sub-claims with different labels, or when evidence is too thin to decide (original proposal deleted, downstream context missing). Tracked separately; excluded from ROI aggregation. Cap at 15% of findings — if higher, rubric needs sharpening. |

## How to Label (Decision Tree)

```
Finding found, what's its status?
│
├── Premise false? (hallucinated fact, misread code, wrong claim)
│   → (d) Actively wrong
│
├── Premise true. Did anything downstream change because of this finding?
│   │
│   ├── Yes — a commit exists that addresses it
│   │   │
│   │   ├── Would the problem have caused incident / rework / security /
│   │   │   wrong-direction-ship?
│   │   │   → (a) Prevented real problem
│   │   │
│   │   └── Smaller change — scope / ordering / abstraction / clarity
│   │       → (b) Changed plan meaningfully
│   │
│   └── No downstream signal — no commit, no plan revision, no refined entry
│       → (c) Noise / ignored
│
└── Can't tell (thin evidence, corrupted chain, finding is ambiguous)
    → (e) Mixed / unclear
```

## Evidence Sources (in priority order)

1. **`tasks/<topic>-plan.md` frontmatter** — `shipped_commit`, `implementation_status` (`shipped` / `partial` / `rejected`), refinement notes
2. **`tasks/<topic>-refined.md`** — did the refinement phase adopt or reject the finding?
3. **Git log** — `git log --oneline --all -- tasks/<topic>-proposal.md tasks/<topic>-design.md <inferred-source-files>` — look for commits around the /challenge timestamp that reference the finding's content
4. **`tasks/<topic>-review.md`** — if review artifact exists, did it confirm or contradict the challenge finding?
5. **`tasks/session-log.md`** — grep for the debate_id, read surrounding entries for outcome hints
6. **Original proposal text** — was the proposal revised between `/challenge` and any downstream artifact?
7. **`tasks/decisions.md`** — low hit rate per Phase 0, but check if the finding's content appears in a D-entry

## Ambiguity-Resolution Rules

- **"Valid but irrelevant"** — finding was correct but did not prompt any change. Label **(c)**, not **(a)**. (a) requires action AND downstream change.
- **"Correct and acted on months later"** — if the action happened outside the auditable window (no commit in the 14 days post-challenge AND no plan/refined artifact reference), label **(c)**. Time-bounded to prevent hindsight inflation.
- **"Partially right, partially wrong"** — if ≥60% of the finding's claim is wrong, label **(d)**. If <60% wrong, use the label that matches the ≥60% correct portion.
- **"Blocked by outcome we can't see"** — if the proposal was abandoned entirely and no downstream exists, the finding is ambiguous. Label **(e)**.
- **"Finding shaped thinking but no specific commit"** — if session-log explicitly references the finding as altering the direction (even without a commit), label **(b)**. If the shaping is inferred, label **(c)**.

## Weighting Rationale

- **+3 for (a):** catching one real problem often pays for many failed runs. Asymmetric consequence.
- **+1 for (b):** real value, but easier to substitute (a careful self-review might catch many of these).
- **0 for (c):** correctness does not equal value. Findings that don't change behavior don't earn ROI.
- **-1 for (d):** false findings cost reader attention and risk false-confident mistakes (L33 precedent). Real negative externality.
- **Revisit after pilot.** Scheme is a starting point. Sensitivity analysis during pilot: if verdict flips between +3/0/-1 and +5/0/-2, weighting is load-bearing and must be deliberated further.

## Procedure per Finding

1. Open the `/challenge` output file (`tasks/<topic>-challenge.md` or equivalent).
2. Read the finding verbatim. Extract: what it claims, what action it recommends, which file(s)/system(s) it references.
3. Run the decision tree. Label.
4. Record in results table:
   - `debate_id`
   - Finding index (1, 2, 3…)
   - Label (a/b/c/d/e)
   - Evidence (commit hash, plan reference, or "no downstream")
   - 1-line justification
5. If any ambiguity, note and discuss.

## Dual-Label Protocol

After I (Claude) label a batch, Justin re-labels a random 20% of findings independently (no visibility of my labels). Compute inter-rater agreement:

- **≥80%** → rubric is working, proceed to full labeling.
- **<80%** → rubric is ambiguous. Review each disagreement. Refine rubric. Re-pilot.

## Output

Per-run results: `tasks/multi-model-skills-roi-audit-challenge-findings-<date>.md` (one table of labeled findings).

Aggregated verdict: `tasks/multi-model-skills-roi-audit-challenge-results.md` with:
- Label distribution (% a / b / c / d / e)
- Per-invocation ROI (cost $ + time vs weighted value)
- Aggregate ROI
- Verdict: **keep** / **tune** / **drop** for `/challenge`
- If keep/tune: open tuning questions for Phase 2 (absorbs `debate-efficacy-study-plan.md`)

## Cost Side (paired with labels)

For each audited invocation, capture from `stores/debate-log.jsonl`:
- API spend (`costs.total_usd`)
- Wall time (derive from `timestamp` pairs if available; else estimate at ~100s per invocation)
- Number of MATERIAL findings produced
- Model mix (from `mapping`)

## Next Action

Pilot the rubric on 5 findings from the most recent 2-3 non-autopilot `/challenge` runs. If rubric converges in one pass (no major ambiguity), freeze and proceed to full labeling of ~20 runs. If ambiguity surfaces, revise and re-pilot.

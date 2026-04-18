---
debate_id: learning-velocity-v3
created: 2026-04-18T10:00:09-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# learning-velocity-v3 — Refined Document

## Round 1 (gemini-3.1-pro)
The document is highly pragmatic, well-scoped, and grounded in recent operational failures. The "Simplest Version" section correctly identifies the smallest viable increment to test the hypothesis before building complex automation. 

To improve executability, the revised document concretizes the "git log math" so the implementer knows exactly what metrics to extract, and formalizes the proposed approach into a strict set of actionable recommendations.

### Frame Check
Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The document is already strong: it has a concrete problem statement, preserves operational evidence, and gives three actionable recommendations with scope limits and non-goals. The prior revision appears to have improved decisiveness and kept recommendations executable.

Remaining issues I addressed:
- Tightened a few causal claims that were stronger than the cited evidence supports.
- Clarified that some proposed metrics depend on consistent status transitions in `tasks/lessons.md`; otherwise they should surface as partial metrics rather than silently fail.
- Made the scheduling and output behavior for `/healthcheck` more explicit so the recommendations are easier to implement without changing their substance.
- Reduced a small amount of repetition across Problem, Recommendations, and Baseline sections.

### Frame Check
- Unstated load-bearing assumption: The proposal assumes `tasks/lessons.md` history is structured consistently enough that `git log` can reliably detect lesson creation, edits, resolution, and promotion states. If that assumption is false, Recommendation 1's metric design does not hold and needs re-framing, not prose polish.
- Inflated problem: The document uses one manual investigation sample (3 of 4 lessons stale/wrong) plus anecdotal failures to support broad claims like "the system currently adds friction but never removes it." The recommendation set is still directionally plausible, but the problem framing slightly overgeneralizes from limited evidence in a way that would require re-scoping or reframing, not just wording changes.

## Final Refined Document

---
topic: learning-velocity
created: 2026-04-11
---
# Learning Velocity — Close the Measurement, Verification, and Pruning Gaps

## Problem
BuildOS has an enforcement ladder (lesson -> rule -> hook -> architecture) that catches and corrects mistakes, but no mechanism to measure whether those corrections reduce recurrence over time. The system captures failures, but it does not systematically verify whether active lessons remain true or whether accumulated governance still earns its keep.

A recent manual `/investigate --claim` run found 3 of 4 tested lessons contained stale or wrong information. That is sufficient evidence of a real verification gap, though not by itself proof that most lessons are stale. Separately, the system has no built-in mechanism to identify redundant rules, inactive hooks, or governance that no longer carries load. The result is governance that accumulates without a feedback loop for usefulness, retirement, or simplification.

## Recommendations

Implement the following three capabilities in the existing `/healthcheck` skill, with measurement first because it is the dependency for judging whether the rest improves system behavior.

### 1. Implement Measurement (Phase 1)
Calculate four learning-velocity metrics from `git log` on `tasks/lessons.md` and add them to `/healthcheck` Step 6 output. This requires ~15 lines of bash/python and no new infrastructure.

If `tasks/lessons.md` history does not consistently encode creation, edit, resolution, and promotion transitions, `/healthcheck` should emit whichever metrics are computable and explicitly report which ones could not be derived from current history format, rather than fabricating values.

Metrics:
* **Time-to-Promotion:** Average days a lesson spends active before moving to a rule or hook.
* **Recurrence Rate:** Frequency of edits to the same lesson, used as a proxy for lessons that are not sticking cleanly.
* **Throughput:** Number of lessons resolved or promoted per week.
* **Staleness:** Number of active lessons untouched for >14 days.

Add the metrics to normal `/healthcheck` reporting; do not create a separate dashboard or storage system.

### 2. Automate Scheduled Verification (Phase 2)
When a `/healthcheck` full scan detects stale lessons (>14 days with no activity), automatically execute `/investigate --claim` on the top 2-3 stalest active entries.

Execution rules:
* Do not scan all stale lessons; cross-model panel calls are expensive.
* Rank by oldest last-touch time and inspect only the top 2-3 candidates per full scan.
* Surface the verification results directly in `/healthcheck` output so stale or invalid lessons become visible during routine maintenance.

Rationale:
* The stalest lessons are the most likely place for outdated context to persist unchallenged.
* This adds targeted verification without turning `/healthcheck` into a high-cost batch job.

### 3. Implement Redundancy and Pruning Checks (Phase 2)
Add rule and hook redundancy detection to the `/healthcheck` full scan. Flag candidates for manual removal; **never auto-prune**.

Checks:
* **Rule Check:** "Does a hook already enforce this rule?" If yes, flag the rule as potentially redundant.
* **Hook Check:** "Has this hook fired in the last 30 days?" If no, flag the hook for review.

Output behavior:
* Report flagged items as review candidates, not removal actions.
* Keep the decision manual, since low usage can mean either irrelevance or successful prevention.

### Non-Goals
- **Positive signal capture as a new system:** Promoted rules already encode validated "do this" patterns. No separate positive-capture mechanism is required here.
- **Dashboards or UI:** Metrics surface only in CLI `/healthcheck` output.
- **Automated pruning:** The system flags candidates; the user decides what to remove.

## Current System Failures
1. 2026-04-11: Manual `/investigate --claim` on 4 active lessons found 3 with stale or wrong information (L17 wrong field names, L18 structurally fragile claim, L19 wrong decomposition numbers). Nothing triggered this check automatically.
2. 2026-04-11: L21 marked Resolved but still in active table — discovered manually during investigation, not by any automated check (before healthcheck was built).
3. Ongoing: No way to answer "are we making fewer mistakes over time?" or "are lessons getting promoted faster?" The enforcement ladder has no feedback loop on its own effectiveness.

## Operational Context
- Active lessons: ~12 in `tasks/lessons.md` (well under 30 target)
- Rules: 8 files in `.claude/rules/` (excluding `reference/`)
- Hooks: 17 in `hooks/`
- `debate-log.jsonl`: ~95 entries, 5-10 `debate.py` runs/day
- `/investigate --claim` costs: 1 cross-model panel call per lesson (~30s each, $0.05-0.10 per call)
- `/healthcheck` full scan: runs when >7d since last scan or lessons >25 — currently low frequency

## Baseline Performance
- Current measurement: none. No metrics on learning velocity exist.
- Current verification: none. Lessons are only verified when someone manually runs `/investigate --claim`.
- Current pruning: archival exists (move Resolved/Promoted lessons to archived section). No active pruning of rules or hooks. No redundancy detection.
- Current positive capture: rules encode validated patterns when promoted from lessons. No other mechanism.

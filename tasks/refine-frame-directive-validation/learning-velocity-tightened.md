---
debate_id: learning-velocity-tightened
created: 2026-04-18T09:56:30-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# learning-velocity-tightened — Refined Document

## Round 1 (gemini-3.1-pro)
The document clearly identifies a critical governance problem: the system accumulates rules and lessons but lacks a feedback loop to prune stale or redundant constraints. The evidence (3 of 4 investigated lessons being stale) strongly supports the need for automated verification. 

**Improvements made:**
- **Completeness:** The original draft references "4 computed learning velocity metrics" but never defines them. I have explicitly defined these four metrics based on what can actually be extracted via `git log` on a markdown file.
- **Clarity:** Specified the exact mechanism for the "Simplest Version" to ensure it is immediately executable.
- **Dependency Flag:** Noted that pruning hooks based on "fired in the last 30 days" requires hook execution logging, ensuring the implementation doesn't hit a wall.

### Frame Check
Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The revision is strong: it defines a concrete problem, preserves the operational evidence, and keeps recommendations actionable rather than drifting into “study it further.” The phased approach is also appropriate because Phase 1 produces a decision signal cheaply before adding recurring verification work.

Remaining issues I corrected:
- Tightened the recommendation so Phase 1 has explicit acceptance criteria instead of “prove reliable,” which was underspecified.
- Clarified that the proposed metrics are proxies from `git log`, not direct measures of true mistake recurrence. Without that caveat, the document over-claims what the metrics can show.
- Narrowed scheduled verification triggers so they do not imply every stale lesson is high-risk merely because it is old; age is now treated as a prioritization heuristic.
- Made pruning checks more operationally specific, especially the hook-logging dependency and what “fired in the last 30 days” means.
- Improved flow and wording while preserving the evidence sections and all three proposed changes.

### Frame Check
Frame check: document's frame is sound.

## Final Refined Document

---
topic: learning-velocity
created: 2026-04-11
---
# Learning Velocity — Close the Measurement, Verification, and Pruning Gaps

## Problem
BuildOS has an enforcement ladder (lesson -> rule -> hook -> architecture) that catches and corrects mistakes, but it does not measure whether those corrections reduce recurrence over time. The system records failures, but it does not systematically verify whether recorded lessons are still true, and it does not identify governance that is no longer earning its keep.

As a result, governance accumulates: lessons, rules, and hooks are added, but there is no built-in mechanism to answer:
- Are lessons being resolved faster?
- Are validated lessons being promoted into stronger enforcement?
- Are old lessons still correct?
- Are existing rules or hooks now redundant or obsolete?

A manual `/investigate` run already showed the failure mode: 3 of 4 tested lessons contained stale or wrong information, and nothing currently triggers that verification automatically.

The result is one-way friction. Governance adds cost to sessions through slower execution, higher token consumption, and diluted context, but there is no corresponding removal loop.

## Proposed Approach

Add three capabilities to the existing `/healthcheck` skill to close the feedback loop.

1. **Measurement** — Compute 4 learning-velocity metrics derived directly from `git log` on `tasks/lessons.md`. This requires no new infrastructure: append the `git log` analysis to `/healthcheck` full-scan output.
   * *Metric 1 (Active Age):* Average days since creation for currently active lessons.
   * *Metric 2 (Time-to-Resolution):* Average days between a lesson's addition and its resolution or promotion.
   * *Metric 3 (Promotion Ratio):* Percentage of resolved lessons that are promoted to rules versus simply archived.
   * *Metric 4 (Churn Rate):* Frequency of edits to existing lessons, used as a proxy for lesson instability or recurring confusion.

   These are operational proxies from repository history, not direct proof of mistake recurrence. They are still sufficient to detect whether lessons are aging out, turning over, and graduating into stronger controls.

2. **Scheduled Verification** — When a `/healthcheck` full scan detects stale lessons (>14 days with no `git` activity), automatically execute `/investigate --claim` on the top 2-3 stalest entries. Cap the batch size to control cost. Use age as a prioritization heuristic, not as proof that a lesson is wrong. The purpose is to sample the highest-risk stale claims during each full scan.

3. **Pruning** — Introduce rule and hook redundancy checks in `/healthcheck` full scan output.
   * *Rule Check:* “Does a hook already enforce this?” If yes, flag the rule as potentially redundant governance.
   * *Hook Check:* “Has this hook executed in the last 30 days?” If no, flag it as potentially obsolete. This requires basic execution logging.
   * *Action:* Flag candidates in the output only. Never auto-prune; require explicit user confirmation before removing any rule or hook.

**Non-goals:**
- **Positive signal capture as a new governance file or system:** Rules already encode “do this” when promoted from lessons. That remains the positive-capture mechanism.
- **Dashboards or reporting UI:** Metrics surface only in `/healthcheck` CLI output.
- **Automated pruning:** `/healthcheck` identifies candidates; humans decide removal.

## Simplest Version (Phase 1)
Implement Measurement only.

Add the 4 velocity metrics to `/healthcheck` Step 6 output using lightweight `git log` parsing. Keep implementation minimal: bash or Python is sufficient.

Run the updated `/healthcheck` for 2-3 full-scan cycles and confirm:
- the metrics compute correctly from known lesson history,
- the output is stable enough to read during routine use,
- the values are interpretable enough to support a later verification and pruning decision.

If those conditions hold, implement Scheduled Verification next, then Pruning.

This sequencing matters:
- Phase 1 is cheap and immediately useful.
- Phase 2 adds recurring model-call cost and should be driven by observed stale-lesson patterns.
- Phase 3 depends on basic hook execution logging and should follow once the system can already measure lesson flow.

### Current System Failures
1. **2026-04-11:** Manual `/investigate --claim` on 4 active lessons found 3 with stale or wrong information (L17 wrong field names, L18 structurally fragile claim, L19 wrong decomposition numbers). Nothing triggered this check automatically.
2. **2026-04-11:** L21 marked Resolved but remained in the active table — discovered manually during investigation, not by any automated check (occurred before healthcheck was built).
3. **Ongoing:** No way to answer “are we making fewer mistakes over time?” or “are lessons getting promoted faster?” The enforcement ladder currently operates without a feedback loop on its own effectiveness.

### Operational Context
- **Active lessons:** ~12 in `tasks/lessons.md` (well under the 30 target limit)
- **Rules:** 8 files in `.claude/rules/` (excluding `reference/`)
- **Hooks:** 17 in `hooks/`
- **Debate logs:** `debate-log.jsonl` has ~95 entries, 5-10 `debate.py` runs/day
- **Investigation costs:** `/investigate --claim` requires 1 cross-model panel call per lesson (~30s each, $0.05-0.10 per call)
- **Healthcheck frequency:** `/healthcheck` full scan runs when >7 days since the last scan or when active lessons >25 (currently low frequency)

### Baseline Performance
- **Current measurement:** None. No metrics on learning velocity exist.
- **Current verification:** None. Lessons are only verified when a user manually executes `/investigate --claim`.
- **Current pruning:** Archival exists (moving Resolved/Promoted lessons to an archived section). There is no active pruning of rules or hooks, and no redundancy detection.
- **Current positive capture:** Rules encode validated patterns when promoted from lessons. No other mechanism exists.

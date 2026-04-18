---
debate_id: learning-velocity-v4
created: 2026-04-18T11:23:06-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# learning-velocity-v4 — Refined Document

## Round 1 (gemini-3.1-pro)
The document clearly identifies a structural problem in the governance system: it operates as an append-only log, accumulating friction without a mechanism to measure effectiveness or prune dead weight. The proposed integration into the existing `/healthcheck` skill is a pragmatic, low-overhead solution.

**Improvements made:**
- **Clarity on Metrics:** The original document referenced "4 computed learning velocity metrics" but never defined them. I have explicitly defined a logical set of four metrics (Cycle Time, Promotion Volume, Stale Ratio, Recurrence) that can be reliably extracted via `git log` and diff analysis.
- **Actionability:** Converted the "Proposed Approach" and "Simplest Version" into a strict, phased set of Recommendations to ensure immediate execution without getting bogged down in the more expensive verification steps upfront.

### Frame Check
Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The revision is already strong: it states a concrete problem, preserves operational evidence, and gives three actionable recommendations with constraints and non-goals. The main opportunities were to tighten a few recommendation details so they are directly implementable, reduce ambiguity in how metrics are computed, and avoid overclaiming on pruning logic.

I made these improvements:
- Clarified exact computation rules for the 4 metrics so implementation is reproducible.
- Tightened Recommendation 2 so the trigger condition, cap, and execution behavior are explicit.
- Narrowed Recommendation 3’s “redundant governance” claim: a rule with a corresponding hook is not automatically redundant in all cases, so the revised text treats it as a review candidate rather than a definitive duplicate.
- Preserved all evidence-bearing sections and factual context.
- Improved flow by separating problem, recommendations, implementation notes, and evidence.

### Frame Check
- Inflated problem: covered at “Current System Failures” and “Operational Context.” The document supports the problem with specific failure examples and bounded system size.
- False binary: covered in “Non-Goals.” The document does not force a binary between positive-signal capture and governance reduction; it explicitly keeps rules as the positive capture mechanism while adding measurement and pruning checks.
- Unstated load-bearing assumption: covered inline in revised recommendations. The revision now narrows pruning to “review candidates” and gates Recommendations 2 and 3 on useful signal from Recommendation 1.
- Frame check: document's frame is sound.

## Final Refined Document

# Learning Velocity — Close the Measurement, Verification, and Pruning Gaps

## Problem
BuildOS has an enforcement ladder — lesson -> rule -> hook -> architecture — that catches and corrects mistakes, but it does not measure whether those corrections reduce recurrence over time. The system records failures, but it does not verify whether active lessons remain true, and it does not show whether accumulated governance is improving outcomes or just adding friction.

A manual `/investigate --claim` run recently found that 3 of 4 tested lessons contained stale or wrong information. Nothing triggers that verification automatically today. Governance can therefore accumulate without proof that it is still load-bearing. That has a direct cost: slower sessions, more context consumed, and more stale guidance carried forward.

## Recommendations

Add the following three capabilities to the existing `/healthcheck` skill. Implement Recommendation 1 immediately. Implement Recommendations 2 and 3 only if the initial metrics produce useful signal in normal operation.

### 1. Implement Measurement via Git Log (Phase 1)
Calculate and output 4 learning-velocity metrics from `git log` history on `tasks/lessons.md`. Add them to `/healthcheck` Step 6 output. This is a small implementation: approximately 15 lines of bash or Python. [EVIDENCED: original proposal states “This requires ~15 lines of bash/python and no new infrastructure.”]

Compute these 4 metrics:

- **Cycle Time:** Average number of days between a lesson first appearing in the active table and that lesson being moved out of the active table to Promoted, Resolved, or archived status.
- **Promotion Volume:** Number of lessons moved from the active table into rules or hooks in the last 30 days.
- **Stale Ratio:** Percentage of currently active lessons with no modification in more than 14 days.
- **Recurrence:** Count of cases where a lesson topic previously marked resolved, promoted, or archived later reappears in the active table.

Implementation notes:
- Use `git log --follow tasks/lessons.md` and parse row-level changes by lesson identifier or stable lesson title.
- If historical edits are too inconsistent to recover a metric reliably, print `unknown` for that metric rather than inventing a value.
- Output the metrics in a compact block in Step 6 so they remain visible in normal terminal use.

### 2. Automate Scheduled Verification for Stale Lessons
When a `/healthcheck` full scan finds active lessons with no modification in more than 14 days, automatically run `/investigate --claim` on the 2 stalest lessons by default, with a hard cap of 3 in a single run.

Execution rules:
- Only run this during a full scan, not a lightweight scan.
- Rank candidates by oldest last-modified timestamp.
- Skip lessons already investigated in the last 7 days during a prior healthcheck-triggered run.
- Emit the selected lesson IDs in the `/healthcheck` output before triggering investigation.

Constraint:
- Hard-cap execution at 3 lessons per run to control token cost and scan time. The proposal’s stated lesson investigation cost is 1 cross-model panel call per lesson, about 30 seconds and $0.05–0.10 per call. [EVIDENCED: from “Operational Context”]

Why this is second, not first:
- This verification loop is useful only if Recommendation 1 shows that stale lessons are common enough, persistent enough, or recurrence-linked enough to justify routine automated checks.

### 3. Flag Governance Candidates for Pruning
Add a governance utility check to the `/healthcheck` full scan. Surface review candidates for removal, but never auto-prune.

Checks:
- **Rule/Hook overlap check:** For each rule in `.claude/rules/`, check whether a corresponding hook exists in `hooks/` that enforces the same behavior. If yes, flag the pair for review as possible duplicate governance. Do not mark it definitively redundant without human review; some rule-and-hook pairs may serve different functions.
- **Hook utility check:** For each hook, inspect execution logs. If a hook has not fired in the last 30 days, flag it for potential archival review.

Output requirements:
- Print flagged items in `/healthcheck` with a short reason: `possible duplicate enforcement` or `inactive for 30d`.
- Do not delete, disable, or modify any rule or hook automatically.

Why this is third, not first:
- Pruning only makes sense after measurement exists. If Recommendation 1 shows little governance churn or little lesson accumulation, pruning may not be worth adding to `/healthcheck`.

## Non-Goals
- **Positive signal capture as a new system:** Rules already encode “do this” when promoted from lessons. That remains the positive capture mechanism; this proposal does not add a parallel system.
- **Dashboards or reporting UI:** The metrics appear only in `/healthcheck` terminal output, not in a separate reporting tool.
- **Automated pruning:** `/healthcheck` flags candidates for user review. It never deletes governance files autonomously.

### Current System Failures
1. 2026-04-11: Manual `/investigate --claim` on 4 active lessons found 3 with stale or wrong information (L17 wrong field names, L18 structurally fragile claim, L19 wrong decomposition numbers). Nothing triggered this check automatically.
2. 2026-04-11: L21 marked Resolved but still in active table — discovered manually during investigation, not by any automated check (before healthcheck was built).
3. Ongoing: No way to answer "are we making fewer mistakes over time?" or "are lessons getting promoted faster?" The enforcement ladder has no feedback loop on its own effectiveness.

### Operational Context
- Active lessons: ~12 in `tasks/lessons.md` (well under 30 target)
- Rules: 8 files in `.claude/rules/` (excluding `reference/`)
- Hooks: 17 in `hooks/`
- `debate-log.jsonl`: ~95 entries, 5-10 `debate.py` runs/day
- `/investigate --claim` costs: 1 cross-model panel call per lesson (~30s each, $0.05-0.10 per call)
- `/healthcheck` full scan: runs when >7d since last scan or lessons >25 — currently low frequency

### Baseline Performance
- Current measurement: none. No metrics on learning velocity exist.
- Current verification: none. Lessons are only verified when someone manually runs `/investigate --claim`.
- Current pruning: archival exists (move Resolved/Promoted lessons to archived section). No active pruning of rules or hooks. No redundancy detection.
- Current positive capture: rules encode validated patterns when promoted from lessons. No other mechanism.

## Implementation Order
1. Add the 4 Step 6 metrics to `/healthcheck`.
2. Run with those metrics long enough to confirm they produce useful signal.
3. If they do, enable stale-lesson auto-verification during full scans.
4. If the metrics also show governance accumulation without corresponding utility, add pruning candidate checks.

## Success Criteria
This change is successful if `/healthcheck` can answer, from existing repository state and logs:

- Are active lessons aging out or getting promoted?
- Are stale lessons being verified without manual intervention?
- Are previously resolved topics recurring?
- Which rules or hooks look inactive or duplicative enough to review for removal?

If those questions can be answered directly in normal `/healthcheck` output, the feedback loop is closed enough to justify the added scan logic.

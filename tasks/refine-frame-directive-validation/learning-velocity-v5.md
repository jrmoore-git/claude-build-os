---
debate_id: learning-velocity-v5
created: 2026-04-18T11:26:18-0700
phase: refine
rounds: 2
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-7
seeded_from_judgment: no
---
# learning-velocity-v5 — Refined Document

## Round 1 (gemini-3.1-pro)
The document clearly identifies a systemic gap (governance accumulates without validation or pruning) and proposes a highly pragmatic, low-infrastructure solution by piggybacking on the existing `/healthcheck` command. 

Two key improvements were made:
1. **Defined the undefined:** The original text referenced "4 computed learning velocity metrics" but never named them. I defined four specific, computable metrics based on git history (Time-to-Resolution, Promotion Rate, Lesson Lifespan, and Recurrence/Churn). 
2. **Mitigated a load-bearing assumption:** The pruning logic assumed that a hook not firing in 30 days means it isn't "earning its keep." This ignores rare but critical safety/security hooks. I added a `critical` exemption to the pruning recommendation.

### Frame Check
Frame check: document's frame is sound.

## Round 2 (gpt-5.4)
The revision is already strong: it has a clear problem statement, preserves operational evidence, and keeps recommendations concrete. I tightened the frame in three places.

First, the rollout previously implied a strict two-phase dependency where metrics must be added and observed for 2–3 sessions before any other work proceeds. That was weaker than necessary. I kept the sequence but made the dependency explicit only where it matters: verification and pruning do not depend on long observation windows, but they should ship after the metrics work so `/healthcheck` stays understandable and implementation remains small.

Second, the stale-lesson verification trigger depended on an unstated assumption that “stale” can be determined purely from age and git inactivity. I preserved that heuristic but clarified it as a prioritization rule for investigation, not proof that the lesson is wrong. That makes the recommendation more defensible without softening it.

Third, the pruning section had a mild false-binary risk around “rule redundant if hook exists.” I narrowed this to “hook fully enforces the same behavior” and added a requirement to flag for review rather than treat mere overlap as redundancy. That keeps the recommendation actionable while avoiding incorrect pruning signals.

I also made a few prose-level improvements:
- clarified exactly what each metric is for
- made cost and trigger language more precise
- tightened the rollout into implementation steps instead of comfort phases
- preserved all original recommendation entries and all evidence-bearing sections

### Frame Check
Frame check: document's frame is sound.

## Final Refined Document

# Learning Velocity — Close the Measurement, Verification, and Pruning Gaps

## Problem
BuildOS has an enforcement ladder (lesson -> rule -> hook -> architecture) that catches and corrects mistakes, but it does not measure whether those corrections reduce recurrence. The system captures failures but not whether the resulting governance is effective, current, or still necessary. Governance accumulates (lessons, rules, hooks), but nothing measures whether it is earning its keep or identifies what is no longer load-bearing. A manual `/investigate` run just proved 3 of 4 tested lessons had stale or wrong information, and nothing triggers that automatically.

The result is one-way governance growth: the system adds friction but never removes it. More governance is not better governance if it only increases session drag and context consumption.

## Recommendations

Add three capabilities to the existing `/healthcheck` skill to close the learning loop.

### 1. Implement Git-Derived Velocity Metrics
Inject four computed learning velocity metrics into the `/healthcheck` full scan output, derived from `git log` on `tasks/lessons.md`. No new infrastructure is required.

* **Time-to-Resolution:** Average days a lesson spends in the active table before moving to Promoted or Resolved.
* **Promotion Rate:** Percentage of resolved lessons that graduate to rules or hooks rather than being archived without enforcement.
* **Active Lifespan:** Average age of currently active lessons, to identify stagnation.
* **Churn/Recurrence:** Frequency of edits to previously resolved lessons, to identify incomplete learning or regressions.

These metrics answer the currently unanswerable questions: whether lessons are moving, whether they are producing enforceable outcomes, and whether “resolved” items stay resolved.

### 2. Automate Stale Lesson Verification
When a `/healthcheck` full scan detects stale active lessons, automatically run `/investigate --claim` on the top 2–3 stalest entries.

Use this trigger:
- lesson is older than 14 days
- no recent git activity on that lesson entry
- rank candidates by staleness and investigate at most 3 per run

This is a prioritization heuristic, not proof the lesson is wrong. It targets the entries most likely to contain outdated system realities or context-poisoning hallucinations.

* **Scope limit:** Cap at 3 to control cost. **EVIDENCED:** proposal text states `/investigate --claim` costs $0.05–0.10 per call, so 3 calls cost about $0.15–$0.30 per run.
* The healthcheck should print which lessons were selected and why, so the investigation step is inspectable.

### 3. Implement Redundancy and Staleness Flagging (Pruning)
Add a governance pruning check to the `/healthcheck` full scan. It should flag candidates for user review; **never auto-prune**.

* **Rule Redundancy:** For each rule, check whether a hook already fully enforces the same behavior. If yes, flag the rule as potentially redundant governance.
* **Hook Staleness:** For each hook, check whether it has fired in the last 30 days. If not, flag it for potential removal, unless the hook is tagged as `[critical]` or is a security invariant.

The output should distinguish:
- **overlap:** rule and hook partially cover the same failure mode
- **likely redundant:** hook fully enforces the rule’s behavior
- **stale but protected:** hook inactive but exempt because it is critical or security-related
- **stale candidate:** hook inactive and not exempt

This keeps pruning useful without treating overlap as equivalence.

## Non-Goals
- **Positive signal capture as a new system:** Rules already encode “do this” when promoted from lessons.
- **Dashboards or reporting UI:** Metrics surface entirely in `/healthcheck` CLI output.
- **Automated pruning:** Pruning candidates are flagged for the user to delete; the system does not delete files itself.

## Rollout Plan (Simplest Version First)
**Step 1:** Add the 4 velocity metrics to `/healthcheck` Step 6 output using `git log` over `tasks/lessons.md`. This requires a small implementation footprint, originally estimated in the proposal at ~15 lines of bash/python.

**Step 2:** In the same full-scan path, add stale-lesson selection logic:
- identify active lessons older than 14 days with no recent git activity
- rank by staleness
- run `/investigate --claim` for at most 3 entries
- print the selected lessons, age, and last activity

**Step 3:** Add pruning flags:
- compare rules against hooks for full-enforcement redundancy
- flag hooks with no fires in the last 30 days unless `[critical]` or security-invariant
- report candidates only; require explicit user action for removal

Sequence matters for implementation simplicity, not because later steps require long observation windows. The metrics should land first so `/healthcheck` output remains interpretable as new checks are added.

### Current System Failures
1. 2026-04-11: Manual `/investigate --claim` on 4 active lessons found 3 with stale or wrong information (L17 wrong field names, L18 structurally fragile claim, L19 wrong decomposition numbers). Nothing triggered this check automatically.
2. 2026-04-11: L21 marked Resolved but still in active table — discovered manually during investigation, not by any automated check (before healthcheck was built).
3. Ongoing: No way to answer "are we making fewer mistakes over time?" or "are lessons getting promoted faster?" The enforcement ladder has no feedback loop on its own effectiveness.

### Operational Context
- Active lessons: ~12 in tasks/lessons.md (well under 30 target)
- Rules: 8 files in .claude/rules/ (excluding reference/)
- Hooks: 17 in hooks/
- debate-log.jsonl: ~95 entries, 5-10 debate.py runs/day
- `/investigate --claim` costs: 1 cross-model panel call per lesson (~30s each, $0.05-0.10 per call)
- `/healthcheck` full scan: runs when >7d since last scan or lessons >25 — currently low frequency

### Baseline Performance
- Current measurement: none. No metrics on learning velocity exist.
- Current verification: none. Lessons are only verified when someone manually runs `/investigate --claim`.
- Current pruning: archival exists (move Resolved/Promoted lessons to archived section). No active pruning of rules or hooks. No redundancy detection.
- Current positive capture: rules encode validated patterns when promoted from lessons. No other mechanism.

---
debate_id: learning-velocity-intake
created: 2026-04-17T16:17:01-0700
mapping:
  A: claude-sonnet-4-6
  B: gpt-5.4
personas:
  A: frame-structural
  B: frame-factual
---
# learning-velocity-intake — Challenger Reviews

## Challenger A (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [ADVISORY]**: The proposal treats "stale by date" as a reliable proxy for "likely wrong." The three failing lessons (L17, L18, L19) were found stale, but the proposal doesn't establish that staleness *caused* the errors — L17 had wrong field names, which is a code-change problem, not a time problem. A lesson could be 90 days old and still correct (stable domain), or 3 days old and already wrong (fast-moving API). The verification trigger (>14d, no activity) may miss the actual failure mode: lessons that reference implementation details that changed in git. A git-blame-based trigger ("files referenced in this lesson were modified since lesson was written") would be more precise than age alone. [COST: SMALL]

2. **ALTERNATIVE [MATERIAL] [COST: SMALL]**: The candidate set omits a **passive recurrence counter** as a standalone first step, which is cheaper than even the "simplest version" and directly answers the stated problem ("no way to measure whether corrections are reducing recurrence"). The proposal's 4 velocity metrics are derived from git log on `lessons.md` — but recurrence of the *same mistake* is the signal that matters, and that's already partially captured in `debate-log.jsonl` (95 entries, 5-10 runs/day) and `hooks/hook-error-tracker.py` (which already normalizes and signatures errors). Mining `hook-error-tracker`'s existing data for repeat-offense patterns costs near zero and directly measures "are we making fewer mistakes over time?" — the stated gap. The proposal skips this existing data source entirely and proposes new git-log math instead.

3. **ASSUMPTION [MATERIAL] [COST: TRIVIAL]**: The proposal assumes `/healthcheck` full scan is the right delivery vehicle, but then notes it "runs when >7d since last scan or lessons >25 — currently low frequency." If the scan runs infrequently, the velocity metrics surface infrequently, and the verification trigger (auto-run `/investigate` on stalest lessons) fires infrequently. The proposal doesn't resolve this tension: if the metrics matter, the scan frequency should be addressed; if the scan frequency is fine, the metrics aren't urgent. This is load-bearing because it affects whether Capability 2 (scheduled verification) ever fires in practice.

4. **OVER-ENGINEERED [ADVISORY]**: The rule/hook redundancy check (Capability 3) requires the system to reason about semantic overlap between natural-language rules and hook behavior — "does a hook already enforce this?" This is not a mechanical check; it requires LLM judgment or a maintained mapping. The proposal frames it as a `/healthcheck` addition but doesn't specify the mechanism. If it's LLM-based, it adds cost and latency to every full scan. If it's a manually maintained mapping, it's another governance artifact that can go stale. The proposal's own non-goal ("never auto-prune") limits the value of this detection — flagging candidates that a human must then evaluate may not justify the complexity of building the detector.

5. **ALTERNATIVE [ADVISORY]**: A missing candidate is **lesson promotion rate as the sole initial metric** — tracking how long lessons spend in "active" before being promoted to rules or archived. This is a single number, computable from git log on `lessons.md`, and directly measures the enforcement ladder's throughput. The proposal proposes 4 metrics without specifying what they are or how they'd change behavior. One well-defined metric with a clear action threshold (e.g., "if median promotion time > 30d, the ladder is clogged") is more actionable than 4 undefined ones.

6. **ASSUMPTION [ADVISORY]**: The proposal states "Rules already encode 'do this' when they're promoted from lessons. That's the positive capture mechanism." This is asserted as a non-goal justification but isn't verified — the proposal itself notes that 3 of 4 tested lessons had wrong information, suggesting the promotion pipeline may not be functioning as described. If lessons aren't being promoted (or are being promoted with stale content), the "positive capture is already handled" assumption is doing load-bearing work in scoping out a real gap.

---

## Concessions

1. **The simplest version is genuinely simple.** ~15 lines of git-log math added to an existing skill is a proportionate first step, and the proposal correctly gates the more expensive capabilities (verification, pruning) on evidence of usefulness.

2. **The problem statement is concrete and evidenced.** Three specific lesson failures on a specific date, with specific error types, is a real data point — not inflated severity. The "ongoing" failure (no recurrence measurement) is structural, not anecdotal.

3. **The non-goals are well-scoped.** Explicitly ruling out dashboards, new governance files, and auto-pruning keeps the proposal from becoming a platform build. The flag-don't-prune stance on Capability 3 is the right call.

---

## Verdict

**REVISE** — The frame is mostly sound and the scope is appropriately modest, but two issues warrant revision before building: (1) the proposal ignores `hook-error-tracker.py`'s existing error-signature data, which already captures recurrence and is a cheaper/more direct answer to the stated measurement gap than new git-log math; (2) the staleness-as-proxy-for-wrongness assumption should be replaced or supplemented with a file-modification trigger, since the actual failure mode in the evidence (wrong field names, wrong API behavior) is caused by code changes, not time passage.

---

## Challenger B (frame-factual) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal’s premise that BuildOS has “no way to measure whether corrections are reducing recurrence” is no longer true. `scripts/lesson_events.py` already computes learning-velocity metrics including average resolution time, recurrence rate, 30-day created/resolved/promoted counts, and stale-rate output under `## Learning Velocity` (`scripts/lesson_events.py:120-169`). That materially changes the “add measurement” recommendation: this is not greenfield work, it’s either wiring existing metrics into `/healthcheck` or validating whether the existing event-log basis is adequate. Recent commit history also shows this is current work, not dead code (`e60e35b`, `62e317b`, `fee8ee0` affecting `scripts/lesson_events.py`).

2. [OVER-ENGINEERED] [MATERIAL] [COST:SMALL]: The pruning proposal partially duplicates infrastructure that already exists for hook-usage analysis. `hooks/hook-session-telemetry.py` already records session telemetry, and `scripts/session_telemetry_query.py` already exposes `hook-fires --window Nd` plus a built-in `prune-candidates` mode with explicit thresholds and session-count gating (`scripts/session_telemetry_query.py:1-17`, `42-47`, `180-215`). So “for each hook: has this fired in the last 30 days?” is already covered by existing telemetry/query surfaces; adding another pruning pass inside `/healthcheck` risks duplicating logic and potentially diverging from the established rubric.

3. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The proposal says “Current measurement: none,” but the repo already contains both measurement mechanisms and freshness checks for operational state. Beyond `lesson_events.py`, there is also a dedicated freshness checker for `docs/current-state.md` (`scripts/check-current-state-freshness.py:1-50`). That doesn’t fully solve lesson verification, but it falsifies the broader framing that the system only “adds friction but never removes it” and has no automated feedback mechanisms at all. The recommendation should be reframed around specific missing links—e.g. lesson claim verification automation—not around absence of measurement in general.

4. [UNDER-ENGINEERED] [ADVISORY]: The proposed quantitative claims about `/investigate --claim` cost/frequency are unsupported in the verified codebase. I found no repository evidence here for “1 cross-model panel call per lesson (~30s each, $0.05-0.10 per call)” or “5-10 debate.py runs/day”; by repo standard these should be treated as SPECULATIVE unless backed by proposal-local data or store/log inspection. They shouldn’t drive automatic top-2/3 verification policy without measurement first.

## Concessions
- The proposal is directionally right that stale lesson claims are a real risk; nothing I verified shows an existing automatic lesson-claim verifier tied to staleness.
- The “flag, don’t auto-prune” posture aligns with the existing telemetry tooling’s cautionary framing and is appropriately conservative.
- Integrating useful signals into an existing `/healthcheck` surface is preferable to creating a separate dashboard/UI.

## Verdict
REVISE — the core problem may be valid, but the proposal materially overstates what is missing by ignoring already-shipped learning metrics and hook-pruning telemetry, so it should be rewritten to extend existing surfaces rather than propose them as new.

---

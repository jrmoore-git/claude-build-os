---
debate_id: learning-velocity
created: 2026-04-17T13:21:55-0700
mapping:
  A: claude-opus-4-7
  B: claude-sonnet-4-6
  C: claude-sonnet-4-6
  D: claude-sonnet-4-6
  E: claude-opus-4-7
personas:
  A: architect
  B: security
  C: pm
  D: frame-structural
  E: frame-factual
---
# learning-velocity — Challenger Reviews

## Challenger A (architect) — Challenges
So `lesson_events.py` is referenced once in skills and once in docs — minimal integration. The proposal's "simplest version" (git log math) is strictly worse than wiring in existing `lesson_events.py metrics`. Also confirmed `prune-candidates` subcommand already exists in `session_telemetry_query.py` with a documented rubric (class tags, fire thresholds, session-count gate = 30).

## Challenges

1. [OVER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: The "simplest version — 4 velocity metrics derived from git log math on tasks/lessons.md" duplicates `scripts/lesson_events.py`, which already exists with tests (`tests/test_lesson_events.py`) and computes the *exact same 4 metrics* from a structured event log (`stores/lesson-events.jsonl`): avg resolution time, recurrence rate, 30d promotions/resolutions, stale rate. It even has a `seed` command for bootstrap. Re-deriving these from git log is strictly worse — git commits conflate multiple lesson edits, can't distinguish `violated` from `updated`, and lose the `promoted`/`archived` signal that `lesson_events.py` captures explicitly. EVIDENCED: file `scripts/lesson_events.py` (272 lines) with `compute_metrics` implementing Metrics 1–4 verbatim. Fix: `/healthcheck` should shell out to `python3.11 scripts/lesson_events.py metrics --json` — ~3 lines, not 15.

2. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal assumes `lesson_events.jsonl` is being populated. It's not — zero hooks reference `lesson_events` and only one skill/doc mentions it. The existing infrastructure is orphaned. Without event logging wired into the lesson lifecycle (create/resolve/promote/archive/violated transitions), both the proposal's metrics AND the existing `compute_metrics` output garbage. The real missing piece is a *write path* (hook on lessons.md edits? `/wrap` integration? `finding_tracker` transitions?), not a *read path*. EVIDENCED: `check_code_presence` shows 0 hook references to `lesson_events`. This reframes the problem: measurement infrastructure exists; feeding it doesn't.

3. [OVER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: The "hook redundancy / fired-in-30-days" pruning check also already exists as `session_telemetry_query.py prune-candidates`, with a two-class rubric, session-count gate (≥30), block-rate threshold (10%), fire threshold (5), and a documented rubric (`docs/reference/hook-pruning-rubric.md`). The proposal describes re-inventing this with a cruder heuristic ("fired in last 30d? no → flag"). Recent commit `62e317b "Hook class tags + pruning rubric"` shipped this deliberately with gates that prevent false-positive pruning of rare-but-critical enforcement hooks. EVIDENCED: `cmd_prune_candidates`, `PRUNE_FIRE_THRESHOLD=5`, `SESSION_COUNT_GATE=30` in `scripts/session_telemetry_query.py`. Fix: `/healthcheck` calls the existing command.

4. [RISK] [MATERIAL] [COST:SMALL]: Auto-running `/investigate --claim` on top 2–3 stalest lessons inside `/healthcheck` couples a diagnostic/read-only skill to a cross-model LLM call costing $0.05–$0.10 each (EVIDENCED from proposal). That's $0.15–$0.30 per healthcheck full scan. More importantly, it breaks the mental model of `/healthcheck` (currently cheap, deterministic, frequent) by injecting nondeterministic LLM spend. A lesson being stale >14d is a weak signal — it may just be correct-and-stable. Better: `/healthcheck` *flags* stale lessons, user decides whether to `/investigate`. Preserves the skill's contract.

5. [ALTERNATIVE] [ADVISORY]: Rule-redundancy check ("does a hook already enforce this rule?") is the one novel piece not already built, but framing it as a mechanical check is the wrong abstraction — rule text and hook behavior aren't textually comparable. A lighter version: require each new rule's frontmatter to declare `enforced_by: <hook-name|none>`, then `/healthcheck` flags rules with `enforced_by: none` that are older than N days (never got a hook) AND rules whose named hook hasn't fired recently. This turns a semantic question into a deterministic one and leverages the existing hook-class telemetry.

6. [UNDER-ENGINEERED] [ADVISORY]: No mention of what happens when `lesson-events.jsonl` disagrees with `tasks/lessons.md` (the source of truth). The 2026-04-11 failure the proposal cites (L21 marked Resolved but still in active table) is precisely a consistency-drift problem between the file and any derived event stream. A reconciliation check (seed vs. current state diff) would catch this class of bug directly and is absent from the proposal.

## Concessions
1. The diagnosis is correct and important: enforcement ladder has no feedback loop, governance accumulates without pruning, and manual investigation found 3/4 stale lessons — that's a real signal.
2. Choosing to extend `/healthcheck` rather than build a new skill/dashboard respects existing surfaces.
3. "Flag candidates — never auto-prune" is the right safety posture and matches the existing `prune-candidates` rubric's philosophy.

## Verdict
REVISE — the problem is real, but the proposal redescribes two subsystems that already exist (`lesson_events.py`, `session_telemetry_query.py prune-candidates`); the correct work is wiring lesson-lifecycle *writes* into hooks and surfacing existing metrics/prune-candidates output in `/healthcheck`, not implementing git-log math.

---

## Challenger B (security) — Challenges
## Challenges

1. **RISK [ADVISORY]**: The proposal claims `/investigate --claim` costs "$0.05-0.10 per call" — ESTIMATED (assumes ~1 cross-model panel call at current LiteLLM pricing). The actual cost depends on lesson length, model selection, and whether fallback models activate. At 2-3 stalest lessons per healthcheck run and 5-10 debate.py runs/day, the auto-verification budget is bounded and low-risk, but the estimate should be validated against `debate_common.py`'s `_estimate_cost` output before treating it as a hard budget.

2. **RISK [ADVISORY]**: The "hook fired in last 30 days" pruning signal relies on `stores/session-telemetry.jsonl` hook_fire events. Tool verification confirms `hook_fire` appears 7 times in hooks/ and 2 times in scripts/, but `log_event("hook_fire"` as a literal string was not found — meaning the telemetry coverage of hook fires may be incomplete. If some hooks don't emit telemetry on fire, the pruning signal will produce false positives (flagging active hooks as candidates for removal). [COST: SMALL — audit which hooks emit telemetry vs. which don't, add missing emissions]

3. **RISK [MATERIAL] [COST: SMALL]**: The proposal's "scheduled verification" step auto-runs `/investigate --claim` on the 2-3 stalest lessons during a healthcheck full scan. The healthcheck skill is described as running "when >7d since last scan or lessons >25." If a lesson is stale because it encodes a claim that's now *correct* (i.e., the system evolved to match it), auto-investigation will still spend $0.10-0.30 per healthcheck run on a non-problem. More critically: if the investigation result is wrong (LLM hallucination about current codebase state), it could flag a valid lesson for removal. The proposal says "flag candidates — never auto-prune" for rules/hooks, but doesn't apply the same explicit safeguard to lesson verification output. The skill should emit investigation results as advisory findings, not as direct lesson status updates.

4. **ASSUMPTION [MATERIAL] [COST: TRIVIAL]**: The proposal assumes `lesson_events.py` metrics (avg_resolution_days, recurrence_rate_pct, recent_promotions_30d, stale_rate) are already computed and available for healthcheck to consume. Tool verification confirms `lesson_events.py` exists with `compute_metrics` and the metrics are implemented. However, the proposal's "simplest version" describes adding "4 velocity metrics (git log math)" as ~15 lines of bash/python — but `lesson_events.py` already implements these metrics from the event log, not git log. The proposal conflates two different data sources. If `stores/lesson-events.jsonl` is sparse or missing (the file wasn't found in skills references), the metrics will be empty. The healthcheck integration should call `lesson_events.py compute_metrics` rather than re-implementing git log math.

5. **ASSUMPTION [ADVISORY]**: The rule/hook redundancy check ("does a hook already enforce this rule?") requires semantic matching between natural-language rule text and hook behavior. The proposal doesn't specify how this matching works. A naive string-search approach will produce both false positives (rule mentions a concept a hook also mentions, but they're not redundant) and false negatives (hook enforces a rule using different terminology). This is flagged as advisory because the proposal correctly says "flag candidates — never auto-prune," so false positives are annoying but not dangerous.

6. **RISK [ADVISORY]**: The proposal's "non-goal" of positive signal capture dismisses the gap too quickly. Rules encode "do this" when promoted from lessons — but tool verification shows 8 rule files and ~12 active lessons, with no automated check that promoted lessons actually have corresponding rule coverage. A lesson marked "Promoted" with no corresponding rule update is a silent gap. This is pre-existing, not introduced by this proposal, but the proposal's velocity metrics won't catch it.

7. **UNDER-ENGINEERED [ADVISORY]**: The `session_telemetry_query.py` `cmd_prune_candidates` function (verified to exist at line 300) already implements hook pruning candidate detection with a `SESSION_COUNT_GATE` guard. The proposal doesn't mention integrating with this existing function — it describes building the pruning check from scratch in healthcheck. This is duplication risk. The healthcheck integration should call `session_telemetry_query.py prune-candidates` rather than re-implementing the logic.

## Concessions

1. **The incremental rollout is correct**: Starting with just the 4 velocity metrics (~15 lines) before adding verification and pruning is the right sequencing. The metrics are low-risk, immediately useful, and validate whether the feedback loop is worth building out.

2. **The "flag, never auto-prune" constraint on rules/hooks is the right safety boundary**: Given that false positives in pruning detection could remove load-bearing governance, requiring human confirmation before any removal is appropriate. The proposal is explicit about this.

3. **The problem statement is well-evidenced**: Three concrete failures on 2026-04-11 with specific lesson IDs (L17, L18, L19, L21) and a clear description of what went wrong. This is not speculative — the system demonstrably failed to catch stale lessons automatically.

## Verdict

**REVISE** — The core proposal is sound and addresses a real gap, but two issues need resolution before implementation: (1) the auto-investigation output from `/investigate --claim` must be explicitly scoped as advisory-only with no automated lesson status changes, matching the same "flag, never auto-act" constraint applied to rule/hook pruning; and (2) the healthcheck integration should call the already-implemented `lesson_events.py compute_metrics` and `session_telemetry_query.py prune-candidates` rather than re-implementing their logic, to avoid duplication and ensure the telemetry coverage gap in hook_fire emissions is audited first.

---

## Challenger C (pm) — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL] [COST:SMALL]**: The proposal treats `lesson_events.py` + `compute_metrics()` as new work, but both already exist and are tested. EVIDENCED: `compute_metrics` exists in `scripts/lesson_events.py` (verified), covers avg_resolution_days, recurrence_rate_pct, recent_promotions_30d, and stale_rate. `session_telemetry_query.py` already has `cmd_prune_candidates()` for hook fire frequency. The "simplest version" (~15 lines of bash/python) is already substantially built. The proposal needs to be reframed as *wiring existing tools into `/healthcheck`*, not building new measurement infrastructure. The actual delta is smaller than described, which is good — but the proposal's framing obscures this and risks re-implementing what exists.

2. **ASSUMPTION [MATERIAL] [COST:SMALL]**: The proposal assumes `lesson_events.py` is being populated by hooks at lesson lifecycle events. EVIDENCED: `log_event` appears in hooks (5 matches) and skills (1 match), but `lesson-events.jsonl` is only referenced in `scripts/lesson_events.py` itself — not in any hook. If hooks aren't writing lifecycle events to the JSONL store, `compute_metrics()` will return empty/zero metrics regardless of how it's wired into `/healthcheck`. This is a silent failure mode: the metrics surface but show nothing meaningful. The proposal should verify the event-logging pipeline is live before treating metrics as actionable.

3. **RISK [MATERIAL] [COST:SMALL]**: The scheduled verification step (auto-run `/investigate --claim` on top 2-3 stalest lessons during `/healthcheck` full scan) introduces a cost spike that isn't gated. ESTIMATED: 2-3 calls × $0.05-0.10 = $0.10-0.30 per full scan. At low frequency this is fine, but `/healthcheck` full scan triggers when lessons >25 — a condition that could be hit repeatedly in active development. The proposal says "not all — that's expensive" but doesn't specify a cost cap, a flag to skip verification, or a minimum staleness threshold beyond ">14d." Without a guard, a session that repeatedly crosses the lesson-count threshold could trigger multiple verification runs in one day. SPECULATIVE on exact frequency, but the missing guard is a design gap.

4. **OVER-ENGINEERED [ADVISORY]**: The rule/hook redundancy check ("does a hook already enforce this rule?") requires semantic matching between natural-language rule files and hook behavior — a hard NLP problem dressed up as a simple scan. EVIDENCED: Rules are in `.claude/rules/*.md` (natural language), hooks are Python/bash with `hook-class:` tags. There's no structured mapping between them. A naive string-match will produce false positives (rule mentions "read before edit," hook is `hook-read-before-edit.py` — flagged as redundant when the rule is the *why* and the hook is the *enforcement*). The proposal says "flag candidates — never auto-prune," which limits blast radius, but the false-positive rate could make the output noisy enough to be ignored. This is the weakest of the three capabilities and should be descoped from the initial implementation.

5. **UNDER-ENGINEERED [ADVISORY]**: The "stalest lessons" selection for auto-verification uses age (>14d, no activity) as a proxy for staleness risk, but the 2026-04-11 failures (L17, L18, L19) were stale because the *codebase changed under them*, not because time passed. A lesson about field names goes stale when the schema changes, not after 14 days. Age-based selection will miss recently-created lessons that reference fast-moving code. A better signal would be: lessons whose referenced files have had commits since the lesson was created. This is achievable with `get_recent_commits` (already exists in `debate_tools.py`) but isn't proposed.

6. **RISK [ADVISORY]**: The proposal's "simplest version" (just the 4 metrics) is correctly identified as the right starting point, but the full proposal bundles all three capabilities together without a clear decision gate between them. The text says "if those numbers are useful after 2-3 sessions, add verification and pruning steps" — but this gate isn't encoded anywhere. Without it, the implementation will likely ship all three at once because the proposal presents them as a coherent package.

---

## Concessions

1. **The problem is real and evidenced.** Three of four manually-tested lessons were stale or wrong on the same day. That's a 75% failure rate on a manual spot-check, and nothing triggered it automatically. The cost of stale lessons (poisoned context, wrong field names in generated code) is higher than the cost of the proposed fix.

2. **The scope discipline is good.** Non-goals are explicit and correctly exclude dashboards, new governance files, and automated pruning. The proposal correctly identifies that the enforcement ladder already has a positive-capture mechanism (rule promotion) and doesn't try to build a parallel one.

3. **The simplest version is genuinely simple.** Wiring `compute_metrics()` into `/healthcheck` Step 6 is ~15 lines and uses already-tested infrastructure. The proposal correctly names this as the entry point rather than shipping all three capabilities at once.

---

## Verdict

**REVISE** — The core direction is sound and the problem is evidenced, but the proposal needs two fixes before implementation: (1) verify the `lesson_events.py` event-logging pipeline is actually being populated by hooks (silent failure risk if it isn't), and (2) add a cost/frequency guard to the auto-verification step. The rule/hook redundancy check should be descoped from v1 — it's the weakest capability and the most likely to produce noisy false positives. Ship metrics + age-gated verification; revisit redundancy detection only if the metrics reveal a governance bloat problem worth solving.

---

## Challenger D (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [ADVISORY]**: The proposal treats "stale by age" (>14d, no git activity) as a reliable proxy for "likely wrong." But a lesson about a stable architectural decision *should* have no recent git activity — that's evidence it's settled, not evidence it's stale. The 3 failing lessons from the manual run were wrong because the underlying system changed, not because they were old. Age-based staleness detection will generate false positives on good, stable lessons and may miss recently-added lessons that are already wrong. The actual signal is "the system this lesson describes has changed" — which is detectable via git log on the *referenced files*, not on lessons.md itself.

2. **ALTERNATIVE [MATERIAL] [COST:SMALL]**: The proposal's "stalest 2-3 lessons" selection heuristic is missing a more precise candidate: lessons that reference specific field names, function signatures, or file paths that have since changed in git. A targeted `git log --follow` on files mentioned in each lesson body would surface *actually invalidated* lessons rather than merely old ones. This is ~30-50 lines of Python and would have caught all 3 failures from the manual run (L17 wrong field names, L18 structurally fragile claim, L19 wrong decomposition numbers) without running `/investigate` on stable-but-old lessons. The proposal's age heuristic is a weaker substitute for this.

3. **ASSUMPTION [ADVISORY]**: The hook "has this fired in the last 30 days?" pruning criterion assumes hook telemetry is reliably captured and queryable. The manifest shows `hook-session-telemetry.py` and `scripts/session_telemetry_query.py` exist, but the proposal doesn't verify that *all* hooks emit queryable fire events. Shell hooks (`.sh` files) may not emit structured telemetry. If 6 of 17 hooks are shell-based and don't log fires, the 30-day criterion will flag them as candidates for pruning when they may be firing constantly. This is a data-quality assumption that should be verified before the pruning step is built.

4. **OVER-ENGINEERED [ADVISORY]**: The "rule redundancy check" (does a hook already enforce this rule?) is framed as automatable, but the relationship between rules and hooks is semantic, not structural. A rule saying "read before edit" and a hook named `hook-read-before-edit.py` are obviously paired — but a rule about "decompose large tasks" and `hook-decompose-gate.py` may be complementary rather than redundant (the rule guides authoring intent; the hook enforces a gate). Automated redundancy detection will either be trivially name-matching (low value) or require LLM interpretation (expensive). The proposal doesn't acknowledge this gap. Flagging by name similarity is cheap but misleading; flagging by semantic overlap requires the same `/investigate` cost as lesson verification.

5. **ASSUMPTION [MATERIAL] [COST:TRIVIAL]**: The "Simplest Version" section correctly identifies the 15-line git log math as the right starting point, but the proposal then describes all three capabilities (measurement, verification, pruning) as a single `/healthcheck` addition. The framing implies these ship together or in close sequence. The actual dependency structure is: measurement is independent and cheap; verification depends on having a good staleness signal (see finding #1 and #2 above); pruning depends on telemetry completeness (finding #3). Shipping verification before fixing the staleness signal will burn `/investigate` budget on false positives. The proposal should explicitly gate verification on measurement proving useful, and gate pruning on telemetry audit — which it gestures at in "Non-goals" but doesn't enforce structurally.

---

## Concessions

1. **The scope is correctly bounded.** Extending `/healthcheck` rather than building a new system is the right call. The existing skill is the natural home for this, and the non-goals list (no dashboards, no new governance files, no auto-pruning) correctly resists scope creep.

2. **The "flag, never auto-prune" constraint is sound.** Automated removal of governance artifacts in a system that enforces its own rules is a correctness risk. The proposal correctly treats pruning as human-confirmed.

3. **The phased rollout (metrics first, then verification, then pruning) is the right sequencing.** The "Simplest Version" section demonstrates genuine restraint and the proposal earns credit for naming the incremental path explicitly.

---

## Verdict

**REVISE** — The core frame is sound (extend `/healthcheck`, phase the work, flag don't auto-prune), but the staleness-by-age heuristic is a materially weaker signal than change-detection on referenced artifacts, and the pruning step has an unverified dependency on shell-hook telemetry completeness. Neither issue blocks the metrics phase, but both should be resolved before the verification and pruning phases are built.

---

## Challenger E (frame-factual) — Challenges
`lesson_events.py metrics` is referenced in the skills directory — likely in healthcheck itself. So Part 1 of the proposal (velocity metrics in healthcheck) is already shipped. Parts 2 and 3 are the genuinely new asks.

## Challenges

1. **[OVER-ENGINEERED] [MATERIAL] [COST:TRIVIAL to fix the framing]:** Proposal pillar #1 ("Measurement — 4 computed learning velocity metrics") is **already shipped**. `scripts/lesson_events.py` (272 lines, committed in the same 2026-04-11 session the proposal cites) implements exactly four metrics: avg resolution days, recurrence rate %, 30d promotions/resolutions/created, stale rate % — emitted under a literal `## Learning Velocity` header (lines 83–171). It's event-log-based rather than git-log-based, which is strictly better (git log over `tasks/lessons.md` would count every unrelated edit as activity). `check_code_presence` also finds `lesson_events.py metrics` referenced from the skills directory, meaning it's already wired into `/healthcheck`. The proposal's "Baseline Performance: Current measurement: none" is factually false.

2. **[OVER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]:** Proposal pillar #3's hook-fire check ("has this hook fired in the last 30 days?") is **already shipped** as `scripts/session_telemetry_query.py prune-candidates` / `hook-fires`, gated on ≥30 sessions and using a two-class enforcement rubric (`# hook-class:` annotations, `docs/reference/hook-pruning-rubric.md`). The proposal describes building this capability from scratch without acknowledging the existing command. The real gap is wiring `prune-candidates` into `/healthcheck` output, not building the logic.

3. **[ASSUMPTION] [MATERIAL] [COST:SMALL]:** The proposal's rule-redundancy check ("for each rule: does a hook already enforce this?") is the one genuinely novel piece, but there is no mechanical way to answer that question — rules are prose and hooks are code. Treating it as "~15 lines of bash/python" in the Simplest Version is wrong; the simplest version as written covers metrics (already done), not redundancy. The proposal should either drop redundancy detection or acknowledge it requires an LLM-based mapping pass.

4. **[ALTERNATIVE] [MATERIAL] [COST:SMALL]:** The genuine remaining work — scheduled auto-verification of the stalest 2-3 lessons via `/investigate --claim` — is a clean, small increment that could ride directly on top of the existing `compute_metrics()` output (it already surfaces `stale_count` and per-lesson latest-timestamp data in `by_lesson`). Frame the proposal as "add two thin consumers (verification trigger + pruning surface) on top of existing `lesson_events.py` and `session_telemetry_query.py`," not as a three-pillar new build.

5. **[ASSUMPTION] [ADVISORY]:** "Hooks: 17 in hooks/" — the manifest shows 23 files in `hooks/`. Even excluding `.sh` wrappers and the `pre-commit-banned-terms.sh` helper, the count is higher than 17. Minor, but it suggests the operational context block wasn't recomputed.

## Concessions
- The auto-verification idea (Part 2) is genuinely not implemented and is a real gap — no scheduled `investigate --claim` exists.
- The non-goals are well-chosen (no dashboards, no auto-prune, no new positive-capture file).
- The cost estimate for `/investigate --claim` (~$0.05–0.10/call, ~30s) is plausible and correctly motivates limiting to top-2–3 stalest lessons rather than all.

## Verdict
**REVISE** — two of the three "new" pillars are already shipped (`scripts/lesson_events.py` metrics + `session_telemetry_query.py prune-candidates`); the proposal should be rescoped to the genuine deltas: (a) surface `prune-candidates` inside `/healthcheck`, (b) add stale-lesson auto-verification on top of existing `compute_metrics()` output, and (c) decide whether rule↔hook redundancy detection is worth its actual (non-trivial) cost.

---

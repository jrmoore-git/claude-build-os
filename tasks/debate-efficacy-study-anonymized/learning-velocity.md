# Anonymized Findings — learning-velocity

Total: 51 findings pooled from two anonymous reviewer panels.
Arm C contributed 29; arm D contributed 22.
Arm identity is withheld from the judge by design.

---

## Finding 1

[OVER-ENGINEERED] [ADVISORY]: The proposal’s “git log math on `tasks/lessons.md`” is a weaker basis than the already-shipped structured event log. `lesson_events.py` computes lifecycle metrics from explicit `created/resolved/promoted/violated/updated` events (`scripts/lesson_events.py:33-36,72-99`), whereas git history on one markdown file will conflate formatting edits, bulk cleanup, and unrelated lesson churn. If `/healthcheck` needs velocity metrics, it should read the event log first and only fall back to git when coverage is missing.

## Finding 2

[ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal assumes `lesson_events.jsonl` is being populated. It's not — zero hooks reference `lesson_events` and only one skill/doc mentions it. The existing infrastructure is orphaned. Without event logging wired into the lesson lifecycle (create/resolve/promote/archive/violated transitions), both the proposal's metrics AND the existing `compute_metrics` output garbage. The real missing piece is a *write path* (hook on lessons.md edits? `/wrap` integration? `finding_tracker` transitions?), not a *read path*. EVIDENCED: `check_code_presence` shows 0 hook references to `lesson_events`. This reframes the problem: measurement infrastructure exists; feeding it doesn't.

## Finding 3

[ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal says “Current measurement: none” and frames learning-velocity metrics as missing, but the repo already ships a dedicated `scripts/lesson_events.py` that explicitly “Computes learning velocity metrics from the event log” and exposes a `metrics` command (`scripts/lesson_events.py:2-6,14-19,72-99`). It is also covered by tests (`tests/test_lesson_events.py:1-5`). That changes the recommendation: the gap is not absence of measurement infrastructure, but that `/healthcheck` is not consuming the existing one or that event logging is incomplete.

## Finding 4

**ALTERNATIVE [MATERIAL] [COST:SMALL]**: The proposal's "simplest version" (4 git-log metrics in `/healthcheck`) is sound, but the jump to auto-triggering `/investigate --claim` on the top 2-3 stalest lessons is a missing intermediate candidate: **a ranked staleness report without auto-invocation**. The user sees "these 3 lessons haven't been touched in 30+ days" and manually decides which to investigate. This captures ~80% of the value (surfacing candidates) at zero cost in `/investigate` calls and zero risk of automated cross-model panel calls running unexpectedly during a healthcheck. The proposal acknowledges the simplest version but then skips this intermediate in the candidate set — jumping from "metrics only" to "auto-run investigate." The middle option (ranked list, manual trigger) is absent.

## Finding 5

[RISK] [MATERIAL] [COST:SMALL]: Auto-running `/investigate --claim` on top 2–3 stalest lessons inside `/healthcheck` couples a diagnostic/read-only skill to a cross-model LLM call costing $0.05–$0.10 each (EVIDENCED from proposal). That's $0.15–$0.30 per healthcheck full scan. More importantly, it breaks the mental model of `/healthcheck` (currently cheap, deterministic, frequent) by injecting nondeterministic LLM spend. A lesson being stale >14d is a weak signal — it may just be correct-and-stable. Better: `/healthcheck` *flags* stale lessons, user decides whether to `/investigate`. Preserves the skill's contract.

## Finding 6

**[ALTERNATIVE] [MATERIAL] [COST:SMALL]:** The genuine remaining work — scheduled auto-verification of the stalest 2-3 lessons via `/investigate --claim` — is a clean, small increment that could ride directly on top of the existing `compute_metrics()` output (it already surfaces `stale_count` and per-lesson latest-timestamp data in `by_lesson`). Frame the proposal as "add two thin consumers (verification trigger + pruning surface) on top of existing `lesson_events.py` and `session_telemetry_query.py`," not as a three-pillar new build.

## Finding 7

[ALTERNATIVE] [MATERIAL] [COST:TRIVIAL]: The proposal suggests writing new logic to check if a hook has "fired in the last 30 days" to identify pruning candidates. This exact capability is already implemented in `scripts/session_telemetry_query.py prune-candidates`, which analyzes actual run data in `stores/session-telemetry.jsonl` against a formal rubric. The implementation should call this existing script rather than reinventing the check.

## Finding 8

**OVER-ENGINEERED [ADVISORY]**: The proposal bundles three distinct capabilities (measurement, verification, pruning) into a single `/healthcheck` extension and frames them as one proposal. Each has different data sources, different failure modes, and different implementation costs. The "simplest version" wisely isolates just the metrics, but the framing of all three as a unified "learning velocity" feature risks scope creep where the metrics land, seem useful, and then verification and pruning get added before the metrics have proven their value. The proposal partially guards against this with the "if useful after 2-3 sessions" gate, but that gate is informal and not enforced by the structure of the proposal.

## Finding 9

[ALTERNATIVE] [MATERIAL] [COST:SMALL]: The pruning proposal overlooks that hook-pruning infrastructure already exists. `hooks/hook-session-telemetry.py` records hook/context telemetry (`hooks/hook-session-telemetry.py:3-12,33-43`), and `scripts/session_telemetry_query.py` already has `hook-fires` and `prune-candidates` subcommands with explicit thresholds/gates for low-value hooks (`scripts/session_telemetry_query.py:2-17,42-47`). Recent commits also show this shipped on 2026-04-16 (`fee8ee0`, `62e317b`). So building a new `/healthcheck` “has this hook fired in 30 days?” check would duplicate existing telemetry analysis unless it is just a wrapper over `session_telemetry_query.py`.

## Finding 10

**ASSUMPTION [ADVISORY]**: The proposal treats "stale by age" (>14d, no git activity) as a reliable proxy for "likely wrong." But a lesson about a stable architectural decision *should* have no recent git activity — that's evidence it's settled, not evidence it's stale. The 3 failing lessons from the manual run were wrong because the underlying system changed, not because they were old. Age-based staleness detection will generate false positives on good, stable lessons and may miss recently-added lessons that are already wrong. The actual signal is "the system this lesson describes has changed" — which is detectable via git log on the *referenced files*, not on lessons.md itself.

## Finding 11

**ASSUMPTION [ADVISORY]**: The hook "has this fired in the last 30 days?" pruning criterion assumes hook telemetry is reliably captured and queryable. The manifest shows `hook-session-telemetry.py` and `scripts/session_telemetry_query.py` exist, but the proposal doesn't verify that *all* hooks emit queryable fire events. Shell hooks (`.sh` files) may not emit structured telemetry. If 6 of 17 hooks are shell-based and don't log fires, the 30-day criterion will flag them as candidates for pruning when they may be firing constantly. This is a data-quality assumption that should be verified before the pruning step is built.

## Finding 12

[UNDER-ENGINEERED] [ADVISORY]: “Rule/hook redundancy check” is likely to produce misleading matches unless you specify how semantic overlap is determined. A rule can constrain behavior broadly while a hook enforces only one narrow pathway, and collapsing them risks weakening defense-in-depth. This is not a reason to reject the proposal because you already avoid auto-prune, but the output should explicitly distinguish “overlapping,” “partially enforced,” and “fully machine-enforced” rather than binary redundant/not redundant.

## Finding 13

[ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The pruning idea assumes “hook hasn’t fired in 30 days” is meaningful enough to flag governance as potentially unnecessary, but the existing telemetry tooling explicitly warns against acting directly on those signals. `scripts/session_telemetry_query.py` says findings are “candidates for investigation, not evidence for deletion” and notes read/outcome bucketing is incomplete; the hook telemetry itself is advisory, observer-only, and best-effort (`hooks/hook-session-telemetry.py` swallows exceptions and always exits 0). That makes low-fire-rate data especially vulnerable to false negatives from collection gaps, low event frequency, or hooks that are valuable precisely because they rarely trigger. Keep the candidate framing, but raise the bar: require telemetry health checks and classify hooks by preventive value before surfacing prune pressure.

## Finding 14

**RISK [ADVISORY]**: The proposal's "simplest version" (just the 4 metrics) is correctly identified as the right starting point, but the full proposal bundles all three capabilities together without a clear decision gate between them. The text says "if those numbers are useful after 2-3 sessions, add verification and pruning steps" — but this gate isn't encoded anywhere. Without it, the implementation will likely ship all three at once because the proposal presents them as a coherent package.

---

## Finding 15

**ASSUMPTION [MATERIAL] [COST:TRIVIAL]**: The hook "has this fired in the last 30 days?" check assumes telemetry exists and is queryable per-hook. The manifest shows `hook-session-telemetry.py` and `session_telemetry_query.py` exist, but the proposal doesn't verify that per-hook fire counts are actually logged in a queryable form. If telemetry logs session-level events but not per-hook invocation counts, the 30-day hook activity check has no data source and the entire pruning candidate feature is unimplementable as described. This needs verification before the pruning step is scoped.

## Finding 16

[ALTERNATIVE] [ADVISORY]: Rather than bolting three things onto `/healthcheck`, consider that `/healthcheck` should be the *reader* and the scripts should remain the *authors* of truth. Current pattern in the repo: scripts compute, skills narrate. A 10-line Step 6 that shells out to `lesson_events.py metrics` and `session_telemetry_query.py prune-candidates --window 30d` and formats the output preserves that separation. The proposal's "add capabilities to the skill" framing risks duplicating logic across skill and scripts.

## Finding 17

[OVER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: The "simplest version — 4 velocity metrics derived from git log math on tasks/lessons.md" duplicates `scripts/lesson_events.py`, which already exists with tests (`tests/test_lesson_events.py`) and computes the *exact same 4 metrics* from a structured event log (`stores/lesson-events.jsonl`): avg resolution time, recurrence rate, 30d promotions/resolutions, stale rate. It even has a `seed` command for bootstrap. Re-deriving these from git log is strictly worse — git commits conflate multiple lesson edits, can't distinguish `violated` from `updated`, and lose the `promoted`/`archived` signal that `lesson_events.py` captures explicitly. EVIDENCED: file `scripts/lesson_events.py` (272 lines) with `compute_metrics` implementing Metrics 1–4 verbatim. Fix: `/healthcheck` should shell out to `python3.11 scripts/lesson_events.py metrics --json` — ~3 lines, not 15.

## Finding 18

**ASSUMPTION [MATERIAL] [COST: TRIVIAL]**: The proposal assumes `lesson_events.py` metrics (avg_resolution_days, recurrence_rate_pct, recent_promotions_30d, stale_rate) are already computed and available for healthcheck to consume. Tool verification confirms `lesson_events.py` exists with `compute_metrics` and the metrics are implemented. However, the proposal's "simplest version" describes adding "4 velocity metrics (git log math)" as ~15 lines of bash/python — but `lesson_events.py` already implements these metrics from the event log, not git log. The proposal conflates two different data sources. If `stores/lesson-events.jsonl` is sparse or missing (the file wasn't found in skills references), the metrics will be empty. The healthcheck integration should call `lesson_events.py compute_metrics` rather than re-implementing git log math.

## Finding 19

[ALTERNATIVE] [ADVISORY]: Rule-redundancy check ("does a hook already enforce this rule?") is the one novel piece not already built, but framing it as a mechanical check is the wrong abstraction — rule text and hook behavior aren't textually comparable. A lighter version: require each new rule's frontmatter to declare `enforced_by: <hook-name|none>`, then `/healthcheck` flags rules with `enforced_by: none` that are older than N days (never got a hook) AND rules whose named hook hasn't fired recently. This turns a semantic question into a deterministic one and leverages the existing hook-class telemetry.

## Finding 20

[ALTERNATIVE] [ADVISORY]: Your own “Simplest Version” is the safer sequencing: ship only the git-log learning metrics first, then use observed utility to justify verification/pruning. Given `docs/current-state.md` shows the project already has lesson-volume pressure and multiple active followups, adding automatic outbound verification and pruning heuristics now mixes measurement with action. The risk of not changing is that stale lessons continue unchecked; the risk of changing too much at once is noisy automation and new external-data exposure. Metrics-first best balances both.

## Finding 21

[UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposal says `/healthcheck` should auto-run `/investigate --claim` on stale lessons, but it does not define a trust boundary for what claim text gets sent to external models or how sensitive lesson content is filtered first. `scripts/research.py` already calls an external API directly, and `scripts/llm_client.py` is a shared outbound LLM path; if lesson entries can contain repository specifics, incident details, or copied internal text, scheduled verification creates a new automatic data-exfiltration path that today appears manual and intentional rather than backgrounded. Fix: require a redact/minimize step before outbound verification and a clear allowlist of fields sent off-repo.

## Finding 22

[UNDER-ENGINEERED] [ADVISORY]: No mention of what happens when `lesson-events.jsonl` disagrees with `tasks/lessons.md` (the source of truth). The 2026-04-11 failure the proposal cites (L21 marked Resolved but still in active table) is precisely a consistency-drift problem between the file and any derived event stream. A reconciliation check (seed vs. current state diff) would catch this class of bug directly and is absent from the proposal.

## Finding 23

**ASSUMPTION [MATERIAL] [COST:SMALL]**: The proposal treats `lesson_events.py` + `compute_metrics()` as new work, but both already exist and are tested. EVIDENCED: `compute_metrics` exists in `scripts/lesson_events.py` (verified), covers avg_resolution_days, recurrence_rate_pct, recent_promotions_30d, and stale_rate. `session_telemetry_query.py` already has `cmd_prune_candidates()` for hook fire frequency. The "simplest version" (~15 lines of bash/python) is already substantially built. The proposal needs to be reframed as *wiring existing tools into `/healthcheck`*, not building new measurement infrastructure. The actual delta is smaller than described, which is good — but the proposal's framing obscures this and risks re-implementing what exists.

## Finding 24

[RISK] [MATERIAL] [COST:SMALL]: Auto-running `/investigate --claim` on the "top 2–3 stalest lessons" during `/healthcheck` couples a cheap local check to a cross-model panel call (EVIDENCED from proposal: "$0.05–0.10 per call", "~30s each"). Scheduled verification inside a lint-like skill changes `/healthcheck` from fast/idempotent to slow-and-billable, and will fire whenever stalest-set stays stale (same 2–3 lessons re-verified every full scan until someone edits them). Needs at minimum: (a) a "last verified" timestamp per lesson to avoid re-verifying the same stale lesson every run, and (b) a session-count or time-budget gate analogous to the `SESSION_COUNT_GATE=30` pattern already established in `session_telemetry_query.py`.

## Finding 25

[ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal says “Current verification: none” and “Nothing triggers this check automatically,” but there is already automated freshness / stale-state verification in the codebase. `scripts/check-current-state-freshness.py` compares `docs/current-state.md` against recent git activity and flags staleness (`scripts/check-current-state-freshness.py:17-48`), and `scripts/verify-plan-progress.py` verifies memory claims against on-disk plans, session logs, and artifacts (`scripts/verify-plan-progress.py:3-12`). Those are not lesson-claim verification specifically, but they falsify the stronger premise that BuildOS has no automated verification mechanisms.

## Finding 26

[ALTERNATIVE] [MATERIAL] [COST:TRIVIAL]: The proposal suggests building a new capability using "git log math" to compute learning velocity metrics. This duplicates existing infrastructure. The repository already contains `scripts/lesson_events.py`, which maintains structured lifecycle events in `stores/lesson-events.jsonl` and exposes a `metrics` subcommand specifically designed to compute learning velocity. The `/healthcheck` skill should just invoke this existing command.

## Finding 27

**ASSUMPTION [ADVISORY]**: "For each rule: does a hook already enforce this?" assumes rule-to-hook redundancy is mechanically detectable — i.e., that rules and hooks have overlapping, comparable scope declarations. With 8 rule files and 17 hooks, this mapping is likely semantic, not structural. A hook named `hook-pre-edit-gate.sh` may partially enforce a rule about read-before-edit, but "partially" is doing a lot of work. The redundancy check as described would require either LLM judgment (expensive) or keyword matching (unreliable). The proposal doesn't address how this detection actually works, which means it may produce noisy or misleading redundancy flags.

## Finding 28

**UNDER-ENGINEERED [ADVISORY]**: The "stalest lessons" selection for auto-verification uses age (>14d, no activity) as a proxy for staleness risk, but the 2026-04-11 failures (L17, L18, L19) were stale because the *codebase changed under them*, not because time passed. A lesson about field names goes stale when the schema changes, not after 14 days. Age-based selection will miss recently-created lessons that reference fast-moving code. A better signal would be: lessons whose referenced files have had commits since the lesson was created. This is achievable with `get_recent_commits` (already exists in `debate_tools.py`) but isn't proposed.

## Finding 29

[RISK] [ADVISORY]: Automatically triggering `/investigate --claim` during a `/healthcheck` introduces unprompted model panel invocations. While constrained to 2-3 lessons, this could unexpectedly consume tokens and distract the orchestrator from the primary user objective that triggered the healthcheck.

## Finding 30

**RISK [ADVISORY]**: The proposal claims `/investigate --claim` costs "$0.05-0.10 per call" — ESTIMATED (assumes ~1 cross-model panel call at current LiteLLM pricing). The actual cost depends on lesson length, model selection, and whether fallback models activate. At 2-3 stalest lessons per healthcheck run and 5-10 debate.py runs/day, the auto-verification budget is bounded and low-risk, but the estimate should be validated against `debate_common.py`'s `_estimate_cost` output before treating it as a hard budget.

## Finding 31

**UNDER-ENGINEERED [ADVISORY]**: The `session_telemetry_query.py` `cmd_prune_candidates` function (verified to exist at line 300) already implements hook pruning candidate detection with a `SESSION_COUNT_GATE` guard. The proposal doesn't mention integrating with this existing function — it describes building the pruning check from scratch in healthcheck. This is duplication risk. The healthcheck integration should call `session_telemetry_query.py prune-candidates` rather than re-implementing the logic.

## Finding 32

**OVER-ENGINEERED [ADVISORY]**: The rule/hook redundancy check ("does a hook already enforce this rule?") requires semantic matching between natural-language rule files and hook behavior — a hard NLP problem dressed up as a simple scan. EVIDENCED: Rules are in `.claude/rules/*.md` (natural language), hooks are Python/bash with `hook-class:` tags. There's no structured mapping between them. A naive string-match will produce false positives (rule mentions "read before edit," hook is `hook-read-before-edit.py` — flagged as redundant when the rule is the *why* and the hook is the *enforcement*). The proposal says "flag candidates — never auto-prune," which limits blast radius, but the false-positive rate could make the output noisy enough to be ignored. This is the weakest of the three capabilities and should be descoped from the initial implementation.

## Finding 33

**ASSUMPTION [ADVISORY]**: The rule/hook redundancy check ("does a hook already enforce this rule?") requires semantic matching between natural-language rule text and hook behavior. The proposal doesn't specify how this matching works. A naive string-search approach will produce both false positives (rule mentions a concept a hook also mentions, but they're not redundant) and false negatives (hook enforces a rule using different terminology). This is flagged as advisory because the proposal correctly says "flag candidates — never auto-prune," so false positives are annoying but not dangerous.

## Finding 34

**RISK [ADVISORY]**: The proposal's "non-goal" of positive signal capture dismisses the gap too quickly. Rules encode "do this" when promoted from lessons — but tool verification shows 8 rule files and ~12 active lessons, with no automated check that promoted lessons actually have corresponding rule coverage. A lesson marked "Promoted" with no corresponding rule update is a silent gap. This is pre-existing, not introduced by this proposal, but the proposal's velocity metrics won't catch it.

## Finding 35

**ASSUMPTION [ADVISORY]**: The proposal treats "stale by age" (>14d, no git activity) as a reliable proxy for "likely wrong." But a lesson about a stable architectural decision may have zero git activity precisely *because* it's correct and settled. Age-based staleness detection will generate false positives on the most durable, well-validated lessons while missing recently-added lessons that were wrong from day one (like L17/L18/L19, which were apparently fresh). The actual failure mode in the cited examples isn't age — it's that lessons were never verified at creation. The framing conflates "old" with "stale."

## Finding 36

**OVER-ENGINEERED [ADVISORY]**: The "rule redundancy check" (does a hook already enforce this rule?) is framed as automatable, but the relationship between rules and hooks is semantic, not structural. A rule saying "read before edit" and a hook named `hook-read-before-edit.py` are obviously paired — but a rule about "decompose large tasks" and `hook-decompose-gate.py` may be complementary rather than redundant (the rule guides authoring intent; the hook enforces a gate). Automated redundancy detection will either be trivially name-matching (low value) or require LLM interpretation (expensive). The proposal doesn't acknowledge this gap. Flagging by name similarity is cheap but misleading; flagging by semantic overlap requires the same `/investigate` cost as lesson verification.

## Finding 37

[ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The proposal's "Baseline Performance" section asserts "Current measurement: none" and "No metrics on learning velocity exist." This is factually wrong. `scripts/lesson_events.py` defines `compute_metrics` (EVIDENCED: read lines 100–149) computing avg resolution time, recurrence rate, 30-day promotions/resolutions, and stale rate — the exact four metrics the proposal wants to add. `scripts/session_telemetry_query.py` (EVIDENCED: file header + `prune-candidates` subcommand with `SESSION_COUNT_GATE=30`, `PRUNE_FIRE_THRESHOLD=5`) already implements hook-fire counting and prune-candidate flagging with a gated rubric (`docs/reference/hook-pruning-rubric.md`). The real gap is **wiring, not building** — `/healthcheck` doesn't call these scripts. Rewrite the proposal as "integrate existing `lesson_events.py metrics` and `session_telemetry_query.py prune-candidates` into `/healthcheck` Step 6" — that's a few lines of shell invocation, not "~15 lines of git log math."

## Finding 38

[UNDER-ENGINEERED] [ADVISORY]: "Rule/hook redundancy check — for each rule, does a hook already enforce this?" is proposed as if this is mechanically computable. It isn't — rule↔hook mapping is semantic. The existing `prune-candidates` rubric sidesteps this honestly by using *fire rate and block rate* as observable proxies. The proposal should either (a) adopt that same observable-proxy approach for rules (do rules get cited/read? `context_reads` telemetry already exists — EVIDENCED lines 218–249) or (b) drop the rule-redundancy feature and keep only hook-pruning surfacing.

## Finding 39

**[OVER-ENGINEERED] [MATERIAL] [COST:TRIVIAL to fix the framing]:** Proposal pillar #1 ("Measurement — 4 computed learning velocity metrics") is **already shipped**. `scripts/lesson_events.py` (272 lines, committed in the same 2026-04-11 session the proposal cites) implements exactly four metrics: avg resolution days, recurrence rate %, 30d promotions/resolutions/created, stale rate % — emitted under a literal `## Learning Velocity` header (lines 83–171). It's event-log-based rather than git-log-based, which is strictly better (git log over `tasks/lessons.md` would count every unrelated edit as activity). `check_code_presence` also finds `lesson_events.py metrics` referenced from the skills directory, meaning it's already wired into `/healthcheck`. The proposal's "Baseline Performance: Current measurement: none" is factually false.

## Finding 40

**RISK [ADVISORY]**: The `/investigate --claim` auto-trigger during healthcheck creates a cost coupling: a routine healthcheck scan now has variable cost depending on how many lessons are stale. At $0.05-0.10 per call and 2-3 lessons per scan, that's $0.10-0.30 per healthcheck — SPECULATIVE (no data on healthcheck frequency). If healthcheck runs frequently or if lesson count grows, this cost compounds silently. The proposal caps at "top 2-3 stalest" which bounds it, but the bound isn't enforced by any mechanism described.

---

## Finding 41

[OVER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: The "hook redundancy / fired-in-30-days" pruning check also already exists as `session_telemetry_query.py prune-candidates`, with a two-class rubric, session-count gate (≥30), block-rate threshold (10%), fire threshold (5), and a documented rubric (`docs/reference/hook-pruning-rubric.md`). The proposal describes re-inventing this with a cruder heuristic ("fired in last 30d? no → flag"). Recent commit `62e317b "Hook class tags + pruning rubric"` shipped this deliberately with gates that prevent false-positive pruning of rare-but-critical enforcement hooks. EVIDENCED: `cmd_prune_candidates`, `PRUNE_FIRE_THRESHOLD=5`, `SESSION_COUNT_GATE=30` in `scripts/session_telemetry_query.py`. Fix: `/healthcheck` calls the existing command.

## Finding 42

**ALTERNATIVE [MATERIAL] [COST:SMALL]**: The proposal's "stalest 2-3 lessons" selection heuristic is missing a more precise candidate: lessons that reference specific field names, function signatures, or file paths that have since changed in git. A targeted `git log --follow` on files mentioned in each lesson body would surface *actually invalidated* lessons rather than merely old ones. This is ~30-50 lines of Python and would have caught all 3 failures from the manual run (L17 wrong field names, L18 structurally fragile claim, L19 wrong decomposition numbers) without running `/investigate` on stable-but-old lessons. The proposal's age heuristic is a weaker substitute for this.

## Finding 43

**ASSUMPTION [MATERIAL] [COST:SMALL]**: The proposal assumes `lesson_events.py` is being populated by hooks at lesson lifecycle events. EVIDENCED: `log_event` appears in hooks (5 matches) and skills (1 match), but `lesson-events.jsonl` is only referenced in `scripts/lesson_events.py` itself — not in any hook. If hooks aren't writing lifecycle events to the JSONL store, `compute_metrics()` will return empty/zero metrics regardless of how it's wired into `/healthcheck`. This is a silent failure mode: the metrics surface but show nothing meaningful. The proposal should verify the event-logging pipeline is live before treating metrics as actionable.

## Finding 44

[OVER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: "4 computed learning velocity metrics derived from git log on `tasks/lessons.md`" reinvents what the event log already gives you structurally. Git-log math on a markdown file is a fragile derivation (re-parses diffs, can't distinguish promotion vs archival vs edit) when `stores/lesson-events.jsonl` already has typed lifecycle events (`created|resolved|promoted|archived|violated|updated`). Picking git log over the event log as the data source would be a regression against an existing cleaner abstraction. Fix: use `lesson_events.py metrics --json`.

## Finding 45

**ASSUMPTION [MATERIAL] [COST:TRIVIAL]**: The "Simplest Version" section correctly identifies the 15-line git log math as the right starting point, but the proposal then describes all three capabilities (measurement, verification, pruning) as a single `/healthcheck` addition. The framing implies these ship together or in close sequence. The actual dependency structure is: measurement is independent and cheap; verification depends on having a good staleness signal (see finding #1 and #2 above); pruning depends on telemetry completeness (finding #3). Shipping verification before fixing the staleness signal will burn `/investigate` budget on false positives. The proposal should explicitly gate verification on measurement proving useful, and gate pruning on telemetry audit — which it gestures at in "Non-goals" but doesn't enforce structurally.

---

## Finding 46

**[ASSUMPTION] [MATERIAL] [COST:SMALL]:** The proposal's rule-redundancy check ("for each rule: does a hook already enforce this?") is the one genuinely novel piece, but there is no mechanical way to answer that question — rules are prose and hooks are code. Treating it as "~15 lines of bash/python" in the Simplest Version is wrong; the simplest version as written covers metrics (already done), not redundancy. The proposal should either drop redundancy detection or acknowledge it requires an LLM-based mapping pass.

## Finding 47

**[OVER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]:** Proposal pillar #3's hook-fire check ("has this hook fired in the last 30 days?") is **already shipped** as `scripts/session_telemetry_query.py prune-candidates` / `hook-fires`, gated on ≥30 sessions and using a two-class enforcement rubric (`# hook-class:` annotations, `docs/reference/hook-pruning-rubric.md`). The proposal describes building this capability from scratch without acknowledging the existing command. The real gap is wiring `prune-candidates` into `/healthcheck` output, not building the logic.

## Finding 48

**[ASSUMPTION] [ADVISORY]:** "Hooks: 17 in hooks/" — the manifest shows 23 files in `hooks/`. Even excluding `.sh` wrappers and the `pre-commit-banned-terms.sh` helper, the count is higher than 17. Minor, but it suggests the operational context block wasn't recomputed.

## Finding 49

**RISK [ADVISORY]**: The "hook fired in last 30 days" pruning signal relies on `stores/session-telemetry.jsonl` hook_fire events. Tool verification confirms `hook_fire` appears 7 times in hooks/ and 2 times in scripts/, but `log_event("hook_fire"` as a literal string was not found — meaning the telemetry coverage of hook fires may be incomplete. If some hooks don't emit telemetry on fire, the pruning signal will produce false positives (flagging active hooks as candidates for removal). [COST: SMALL — audit which hooks emit telemetry vs. which don't, add missing emissions]

## Finding 50

**RISK [MATERIAL] [COST:SMALL]**: The scheduled verification step (auto-run `/investigate --claim` on top 2-3 stalest lessons during `/healthcheck` full scan) introduces a cost spike that isn't gated. ESTIMATED: 2-3 calls × $0.05-0.10 = $0.10-0.30 per full scan. At low frequency this is fine, but `/healthcheck` full scan triggers when lessons >25 — a condition that could be hit repeatedly in active development. The proposal says "not all — that's expensive" but doesn't specify a cost cap, a flag to skip verification, or a minimum staleness threshold beyond ">14d." Without a guard, a session that repeatedly crosses the lesson-count threshold could trigger multiple verification runs in one day. SPECULATIVE on exact frequency, but the missing guard is a design gap.

## Finding 51

**RISK [MATERIAL] [COST: SMALL]**: The proposal's "scheduled verification" step auto-runs `/investigate --claim` on the 2-3 stalest lessons during a healthcheck full scan. The healthcheck skill is described as running "when >7d since last scan or lessons >25." If a lesson is stale because it encodes a claim that's now *correct* (i.e., the system evolved to match it), auto-investigation will still spend $0.10-0.30 per healthcheck run on a non-problem. More critically: if the investigation result is wrong (LLM hallucination about current codebase state), it could flag a valid lesson for removal. The proposal says "flag candidates — never auto-prune" for rules/hooks, but doesn't apply the same explicit safeguard to lesson verification output. The skill should emit investigation results as advisory findings, not as direct lesson status updates.

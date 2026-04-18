---
debate_id: learning-velocity
created: 2026-04-17T13:29:19-0700
mapping:
  A: claude-opus-4-7
  B: gpt-5.4
  C: gemini-3.1-pro
  D: claude-sonnet-4-6
  E: gpt-5.4
personas:
  A: architect
  B: security
  C: pm
  D: frame-structural
  E: frame-factual
---
# learning-velocity — Challenger Reviews

## Challenger A (architect) — Challenges
I now have enough. The proposal's premise is materially wrong: `lesson_events.py compute_metrics` already computes velocity metrics (resolution time, recurrence, promotions, stale rate), and `session_telemetry_query.py prune-candidates` already implements hook pruning with a documented rubric and a 30-session gate. The healthcheck skill isn't wired to them.

## Challenges

1. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The proposal's "Baseline Performance" section asserts "Current measurement: none" and "No metrics on learning velocity exist." This is factually wrong. `scripts/lesson_events.py` defines `compute_metrics` (EVIDENCED: read lines 100–149) computing avg resolution time, recurrence rate, 30-day promotions/resolutions, and stale rate — the exact four metrics the proposal wants to add. `scripts/session_telemetry_query.py` (EVIDENCED: file header + `prune-candidates` subcommand with `SESSION_COUNT_GATE=30`, `PRUNE_FIRE_THRESHOLD=5`) already implements hook-fire counting and prune-candidate flagging with a gated rubric (`docs/reference/hook-pruning-rubric.md`). The real gap is **wiring, not building** — `/healthcheck` doesn't call these scripts. Rewrite the proposal as "integrate existing `lesson_events.py metrics` and `session_telemetry_query.py prune-candidates` into `/healthcheck` Step 6" — that's a few lines of shell invocation, not "~15 lines of git log math."

2. [OVER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: "4 computed learning velocity metrics derived from git log on `tasks/lessons.md`" reinvents what the event log already gives you structurally. Git-log math on a markdown file is a fragile derivation (re-parses diffs, can't distinguish promotion vs archival vs edit) when `stores/lesson-events.jsonl` already has typed lifecycle events (`created|resolved|promoted|archived|violated|updated`). Picking git log over the event log as the data source would be a regression against an existing cleaner abstraction. Fix: use `lesson_events.py metrics --json`.

3. [RISK] [MATERIAL] [COST:SMALL]: Auto-running `/investigate --claim` on the "top 2–3 stalest lessons" during `/healthcheck` couples a cheap local check to a cross-model panel call (EVIDENCED from proposal: "$0.05–0.10 per call", "~30s each"). Scheduled verification inside a lint-like skill changes `/healthcheck` from fast/idempotent to slow-and-billable, and will fire whenever stalest-set stays stale (same 2–3 lessons re-verified every full scan until someone edits them). Needs at minimum: (a) a "last verified" timestamp per lesson to avoid re-verifying the same stale lesson every run, and (b) a session-count or time-budget gate analogous to the `SESSION_COUNT_GATE=30` pattern already established in `session_telemetry_query.py`.

4. [UNDER-ENGINEERED] [ADVISORY]: "Rule/hook redundancy check — for each rule, does a hook already enforce this?" is proposed as if this is mechanically computable. It isn't — rule↔hook mapping is semantic. The existing `prune-candidates` rubric sidesteps this honestly by using *fire rate and block rate* as observable proxies. The proposal should either (a) adopt that same observable-proxy approach for rules (do rules get cited/read? `context_reads` telemetry already exists — EVIDENCED lines 218–249) or (b) drop the rule-redundancy feature and keep only hook-pruning surfacing.

5. [ALTERNATIVE] [ADVISORY]: Rather than bolting three things onto `/healthcheck`, consider that `/healthcheck` should be the *reader* and the scripts should remain the *authors* of truth. Current pattern in the repo: scripts compute, skills narrate. A 10-line Step 6 that shells out to `lesson_events.py metrics` and `session_telemetry_query.py prune-candidates --window 30d` and formats the output preserves that separation. The proposal's "add capabilities to the skill" framing risks duplicating logic across skill and scripts.

## Concessions
- Correct diagnosis that the enforcement ladder has no feedback loop surfaced to the user — even though the measurement primitives exist, nothing consumes them.
- Correct instinct to flag-not-auto-prune; aligns with the existing `prune-candidates` footer ("Findings are candidates for investigation, not evidence for deletion").
- "Simplest version first" framing is right; the actual simplest version is even smaller than claimed (shell out to existing tools, don't write git log math).

## Verdict
REVISE — the goal is right and the risk of *not* closing this loop is real (3 of 4 lessons found stale in one manual pass is a concrete failure), but the proposal must be rewritten against the actual codebase: integrate `lesson_events.py compute_metrics` and `session_telemetry_query.py prune-candidates` into `/healthcheck`, drop the git-log-math reinvention, and add a verification-cooldown before auto-invoking `/investigate --claim`.

---

## Challenger B (security) — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposal says `/healthcheck` should auto-run `/investigate --claim` on stale lessons, but it does not define a trust boundary for what claim text gets sent to external models or how sensitive lesson content is filtered first. `scripts/research.py` already calls an external API directly, and `scripts/llm_client.py` is a shared outbound LLM path; if lesson entries can contain repository specifics, incident details, or copied internal text, scheduled verification creates a new automatic data-exfiltration path that today appears manual and intentional rather than backgrounded. Fix: require a redact/minimize step before outbound verification and a clear allowlist of fields sent off-repo.

2. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The pruning idea assumes “hook hasn’t fired in 30 days” is meaningful enough to flag governance as potentially unnecessary, but the existing telemetry tooling explicitly warns against acting directly on those signals. `scripts/session_telemetry_query.py` says findings are “candidates for investigation, not evidence for deletion” and notes read/outcome bucketing is incomplete; the hook telemetry itself is advisory, observer-only, and best-effort (`hooks/hook-session-telemetry.py` swallows exceptions and always exits 0). That makes low-fire-rate data especially vulnerable to false negatives from collection gaps, low event frequency, or hooks that are valuable precisely because they rarely trigger. Keep the candidate framing, but raise the bar: require telemetry health checks and classify hooks by preventive value before surfacing prune pressure.

3. [UNDER-ENGINEERED] [ADVISORY]: “Rule/hook redundancy check” is likely to produce misleading matches unless you specify how semantic overlap is determined. A rule can constrain behavior broadly while a hook enforces only one narrow pathway, and collapsing them risks weakening defense-in-depth. This is not a reason to reject the proposal because you already avoid auto-prune, but the output should explicitly distinguish “overlapping,” “partially enforced,” and “fully machine-enforced” rather than binary redundant/not redundant.

4. [ALTERNATIVE] [ADVISORY]: Your own “Simplest Version” is the safer sequencing: ship only the git-log learning metrics first, then use observed utility to justify verification/pruning. Given `docs/current-state.md` shows the project already has lesson-volume pressure and multiple active followups, adding automatic outbound verification and pruning heuristics now mixes measurement with action. The risk of not changing is that stale lessons continue unchecked; the risk of changing too much at once is noisy automation and new external-data exposure. Metrics-first best balances both.

## Concessions
- The proposal correctly avoids auto-pruning and frames pruning output as candidate generation, which contains privilege-escalation risk from automated governance removal.
- Reusing `/healthcheck` instead of creating a new service keeps operational complexity low and limits new attack surface.
- The proposal identifies a real current failure mode: stale lesson content can mislead future sessions, and today that verification is largely manual.

## Verdict
REVISE — the direction is sound, but automatic lesson verification needs explicit outbound-data minimization rules, and pruning signals need stronger caveats/guardrails before they should influence governance decisions.

---

## Challenger C (pm) — Challenges
## Challenges
1. [ALTERNATIVE] [MATERIAL] [COST:TRIVIAL]: The proposal suggests building a new capability using "git log math" to compute learning velocity metrics. This duplicates existing infrastructure. The repository already contains `scripts/lesson_events.py`, which maintains structured lifecycle events in `stores/lesson-events.jsonl` and exposes a `metrics` subcommand specifically designed to compute learning velocity. The `/healthcheck` skill should just invoke this existing command.
2. [ALTERNATIVE] [MATERIAL] [COST:TRIVIAL]: The proposal suggests writing new logic to check if a hook has "fired in the last 30 days" to identify pruning candidates. This exact capability is already implemented in `scripts/session_telemetry_query.py prune-candidates`, which analyzes actual run data in `stores/session-telemetry.jsonl` against a formal rubric. The implementation should call this existing script rather than reinventing the check.
3. [RISK] [ADVISORY]: Automatically triggering `/investigate --claim` during a `/healthcheck` introduces unprompted model panel invocations. While constrained to 2-3 lessons, this could unexpectedly consume tokens and distract the orchestrator from the primary user objective that triggered the healthcheck.

## Concessions
1. Correctly identifies the systemic risk of governance accumulation (lessons, rules, hooks) without mechanisms to prune stale constraints.
2. Sensibly limits the automated verification to the top 2-3 stalest lessons to control cross-model panel costs.
3. Proposing a rule/hook redundancy check addresses a genuine blind spot in the current enforcement ladder.

## Verdict
REVISE: The core goals are sound and address a real problem, but the implementation should leverage the already existing `lesson_events.py` and `session_telemetry_query.py` scripts rather than building duplicate capabilities.

---

## Challenger D (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [ADVISORY]**: The proposal treats "stale by age" (>14d, no git activity) as a reliable proxy for "likely wrong." But a lesson about a stable architectural decision may have zero git activity precisely *because* it's correct and settled. Age-based staleness detection will generate false positives on the most durable, well-validated lessons while missing recently-added lessons that were wrong from day one (like L17/L18/L19, which were apparently fresh). The actual failure mode in the cited examples isn't age — it's that lessons were never verified at creation. The framing conflates "old" with "stale."

2. **ALTERNATIVE [MATERIAL] [COST:SMALL]**: The proposal's "simplest version" (4 git-log metrics in `/healthcheck`) is sound, but the jump to auto-triggering `/investigate --claim` on the top 2-3 stalest lessons is a missing intermediate candidate: **a ranked staleness report without auto-invocation**. The user sees "these 3 lessons haven't been touched in 30+ days" and manually decides which to investigate. This captures ~80% of the value (surfacing candidates) at zero cost in `/investigate` calls and zero risk of automated cross-model panel calls running unexpectedly during a healthcheck. The proposal acknowledges the simplest version but then skips this intermediate in the candidate set — jumping from "metrics only" to "auto-run investigate." The middle option (ranked list, manual trigger) is absent.

3. **ASSUMPTION [MATERIAL] [COST:TRIVIAL]**: The hook "has this fired in the last 30 days?" check assumes telemetry exists and is queryable per-hook. The manifest shows `hook-session-telemetry.py` and `session_telemetry_query.py` exist, but the proposal doesn't verify that per-hook fire counts are actually logged in a queryable form. If telemetry logs session-level events but not per-hook invocation counts, the 30-day hook activity check has no data source and the entire pruning candidate feature is unimplementable as described. This needs verification before the pruning step is scoped.

4. **ASSUMPTION [ADVISORY]**: "For each rule: does a hook already enforce this?" assumes rule-to-hook redundancy is mechanically detectable — i.e., that rules and hooks have overlapping, comparable scope declarations. With 8 rule files and 17 hooks, this mapping is likely semantic, not structural. A hook named `hook-pre-edit-gate.sh` may partially enforce a rule about read-before-edit, but "partially" is doing a lot of work. The redundancy check as described would require either LLM judgment (expensive) or keyword matching (unreliable). The proposal doesn't address how this detection actually works, which means it may produce noisy or misleading redundancy flags.

5. **OVER-ENGINEERED [ADVISORY]**: The proposal bundles three distinct capabilities (measurement, verification, pruning) into a single `/healthcheck` extension and frames them as one proposal. Each has different data sources, different failure modes, and different implementation costs. The "simplest version" wisely isolates just the metrics, but the framing of all three as a unified "learning velocity" feature risks scope creep where the metrics land, seem useful, and then verification and pruning get added before the metrics have proven their value. The proposal partially guards against this with the "if useful after 2-3 sessions" gate, but that gate is informal and not enforced by the structure of the proposal.

6. **RISK [ADVISORY]**: The `/investigate --claim` auto-trigger during healthcheck creates a cost coupling: a routine healthcheck scan now has variable cost depending on how many lessons are stale. At $0.05-0.10 per call and 2-3 lessons per scan, that's $0.10-0.30 per healthcheck — SPECULATIVE (no data on healthcheck frequency). If healthcheck runs frequently or if lesson count grows, this cost compounds silently. The proposal caps at "top 2-3 stalest" which bounds it, but the bound isn't enforced by any mechanism described.

---

## Concessions

1. **The "simplest version" is correctly identified and appropriately scoped.** 15 lines of git-log math in `/healthcheck` is a genuine minimal viable step, and the proposal correctly gates further investment on demonstrated usefulness.

2. **Non-goals are well-drawn.** Explicitly ruling out dashboards, new governance files, and automated pruning prevents the most common scope inflation failure modes for observability proposals.

3. **The problem evidence is concrete.** Three specific lesson failures on a specific date, with specific error types (wrong field names, structurally fragile claim, wrong numbers), is real evidence — not inflated severity. The "ongoing" failure (no feedback loop) is structural, not anecdotal.

---

## Verdict

**REVISE** — The candidate set is missing the intermediate option (ranked staleness report without auto-invocation of `/investigate`) which is cheaper, lower-risk, and captures most of the verification value. The hook-activity data source assumption needs verification before the pruning step is scoped. Neither issue requires rethinking the proposal's core frame, which is sound — just tighten the candidate set to include the manual-trigger intermediate and add a data-source verification step before committing to the pruning feature.

---

## Challenger E (frame-factual) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal says “Current measurement: none” and frames learning-velocity metrics as missing, but the repo already ships a dedicated `scripts/lesson_events.py` that explicitly “Computes learning velocity metrics from the event log” and exposes a `metrics` command (`scripts/lesson_events.py:2-6,14-19,72-99`). It is also covered by tests (`tests/test_lesson_events.py:1-5`). That changes the recommendation: the gap is not absence of measurement infrastructure, but that `/healthcheck` is not consuming the existing one or that event logging is incomplete.

2. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal says “Current verification: none” and “Nothing triggers this check automatically,” but there is already automated freshness / stale-state verification in the codebase. `scripts/check-current-state-freshness.py` compares `docs/current-state.md` against recent git activity and flags staleness (`scripts/check-current-state-freshness.py:17-48`), and `scripts/verify-plan-progress.py` verifies memory claims against on-disk plans, session logs, and artifacts (`scripts/verify-plan-progress.py:3-12`). Those are not lesson-claim verification specifically, but they falsify the stronger premise that BuildOS has no automated verification mechanisms.

3. [ALTERNATIVE] [MATERIAL] [COST:SMALL]: The pruning proposal overlooks that hook-pruning infrastructure already exists. `hooks/hook-session-telemetry.py` records hook/context telemetry (`hooks/hook-session-telemetry.py:3-12,33-43`), and `scripts/session_telemetry_query.py` already has `hook-fires` and `prune-candidates` subcommands with explicit thresholds/gates for low-value hooks (`scripts/session_telemetry_query.py:2-17,42-47`). Recent commits also show this shipped on 2026-04-16 (`fee8ee0`, `62e317b`). So building a new `/healthcheck` “has this hook fired in 30 days?” check would duplicate existing telemetry analysis unless it is just a wrapper over `session_telemetry_query.py`.

4. [OVER-ENGINEERED] [ADVISORY]: The proposal’s “git log math on `tasks/lessons.md`” is a weaker basis than the already-shipped structured event log. `lesson_events.py` computes lifecycle metrics from explicit `created/resolved/promoted/violated/updated` events (`scripts/lesson_events.py:33-36,72-99`), whereas git history on one markdown file will conflate formatting edits, bulk cleanup, and unrelated lesson churn. If `/healthcheck` needs velocity metrics, it should read the event log first and only fall back to git when coverage is missing.

## Concessions
- The proposal is directionally right that governance should be evaluated for value, not only accumulated.
- It is reasonable to surface existing measurement/pruning signals through `/healthcheck` rather than requiring operators to remember separate scripts.
- The proposal correctly keeps pruning advisory-only rather than auto-deleting rules/hooks.

## Verdict
REVISE — the motivation is partly valid, but key “current state” claims are stale because measurement and pruning infrastructure already exist and should be integrated, not rebuilt.

---

---
topic: buildos-improvements
created: 2026-04-16
recommendation: proceed-with-fixes
complexity: medium
review_backend: cross-model
personas: [architect, security, pm]
challengers: [claude-opus-4-6, gpt-5.4, gemini-3.1-pro]
judge: claude-sonnet-4-6
findings_accepted: 5
findings_dismissed: 6
blocking_spikes: 0
---
# BuildOS Improvements — Challenge Gate Synthesis

## Recommendation: PROCEED-WITH-FIXES

The proposal's core architecture is sound and the prioritization (ship #1 and #2 first) is correct. Three fixes must land inline with the build, not be deferred. None is >20 lines of code; all are specification-level. No blocking spikes required.

## Context Summary

Seven-change bundle against BuildOS framework: four load-bearing (#1 structural review gate, #2 telemetry-then-prune, #3 `/review` learning loop, #4 Tier 0 install footprint), three hygiene (#5 strip Essential Eight, #6 delete anti-slop word list, #7 held as speculative). Independently valuable; ordered by value/effort; simplest version is ship #1+#2 first.

## Cross-Model Panel

- **Challengers:** claude-opus-4-6, gpt-5.4, gemini-3.1-pro (3 personas × 3 models = 9 lenses)
- **Judge:** claude-sonnet-4-6 (non-challenger)
- **Raw findings:** 22 → consolidated to 17
- **Judge verdict:** 5 accepted, 6 dismissed, 0 escalated, 0 spiked
- **Tool-verified claims (Grade A):** 6 of 11 judged findings

## Material Findings Accepted — Inline Fixes

### Fix 1: `PostToolUse:Write|Edit` is not a platform event — use generic `PostToolUse` with JSON filtering

**Finding:** Tool-verified that neither `PostToolUse:Write` nor `PostToolUse:Edit` appears anywhere in hooks or settings. All 8 existing PostToolUse hooks use the generic event and filter internally on tool name.
**Cost:** Trivial — ~5 lines of proposal/plan text; hook itself is still ~60-80 lines but shape changes.
**Action:** In the build plan for #1, specify: "Hook registers on generic `PostToolUse`; reads stdin JSON; filters for `tool_name in {Write, Edit}` before counting. See `hook-post-tool-test.sh` for precedent." LOC estimate revises from ~60 to ~80-100.

### Fix 2: Specify the re-fire policy for #1 (don't repeat L25's suppression failure)

**Finding:** The existing intent-router has a `review-proactive` path that fires once via `already_suggested()` and gets silently suppressed — that's L25. The proposed counter-based hook has the same risk if re-fire is unspecified.
**Cost:** Trivial — one design decision + ~10 lines of hook logic.
**Action:** Pick and document: **re-fire every 5 additional edits past the threshold until a `tasks/*-review.md` artifact exists OR the session ends.** No silent suppression. This is the point — advisory rules fail because they go quiet; this hook stays loud. Flag the threshold (10 edits / 5 re-fire) for review after 30 sessions of telemetry data.

### Fix 3: Replace #2's pruning metric — two-class rubric, not `fire_rate × block_rate` (unanimous finding)

**Finding:** All three challengers independently identified this. Advisory/injection hooks (intent-router, context-inject, session-telemetry) have `block_rate = 0` by design. The proposed metric would falsely flag them for removal. Additionally, rare-but-critical enforcement hooks (credential leakage, protected-file) have high value at low fire rates.
**Cost:** Small — tagging each of the 21 hooks with class+severity is ~30 minutes; rubric redesign is ~1 page of telemetry-plan text.
**Action:** Before running telemetry, tag each hook as either:
- **Advisory/injection** (context-inject, intent-router, session-telemetry, read-before-edit reminder): pruning requires qualitative review of "does this change observable behavior?" — no volume metric
- **Enforcement, low-severity** (skill-lint, syntax-check, ruff): pruning by `fire_rate × block_rate` below threshold is OK
- **Enforcement, high-severity** (guard-env, plan-gate, review-gate, pre-edit-gate, agent-isolation): exempt from volume-based pruning regardless of fire rate

### Fix 4: Replace "2 weeks" with a session-count gate for #2

**Finding:** Single-developer + one external pilot will not produce 21-hook fire-rate distributions with stable signal in 2 calendar weeks.
**Cost:** Trivial — one line in the telemetry plan.
**Action:** Gate pruning on **30 sessions minimum OR 4 calendar weeks, whichever is later.** Define "session" as a think→build→commit cycle.

### Fix 5: Descope #3 — drop the automated system; ship the manual annotation pattern

**Finding:** Tool-verified that `review-log.jsonl`, `review_feedback.py`, and a dismiss-finding UX do not exist. The "one JSONL store and one script" estimate materially undercounts the build. The proposal's own L32 lesson ("modify the skill prompt itself, not runtime context") points to the simpler answer.
**Cost:** Trivial — removes ~70% of the #3 scope.
**Action:** Descope #3 to:
- When a `/review` finding is dismissed, the author manually appends it as a negative example to the relevant lens section in `.claude/rules/review-protocol.md`.
- Add a one-line prompt in the `/review` skill output: "If you dismissed findings, add them as negative examples to `.claude/rules/review-protocol.md` before commit."
- Drop `stores/review-log.jsonl`, `scripts/review_feedback.py`, and the `/log --dismiss-finding` flow entirely. Revisit automation only if telemetry (#2) shows dismissed-finding volume justifies it.

## Findings Dismissed (with rationale)

- **Session-state flag trust boundary** — dismissed: single-developer deployment, threat model doesn't warrant it. Re-materialize if framework goes multi-user.
- **#1 could be a 5-line fix to existing intent-router suppression** — dismissed: the two hooks fire on different boundaries (user prompt vs. post-write); they're complementary. The new hook catches the gap between prompts that the existing hook can't see.
- **#3 prompt-injection risk** — mooted by Fix 5 (descope removes the injection path).
- **#4 tiered install lacks tests** — advisory; addressable with a simple tier-file-manifest validation script during build, not a gate.
- **#4 may weaken baseline protections** — advisory; proposal's Tier 1 (read-before-edit, pre-commit-tests) already addresses this.
- **Remove #7 from the numbered list entirely** — advisory, editorial; keeping it labeled "hold" serves as an explicit pre-decision and prevents re-proposal. Stays.

## Complexity Score: medium

One new hook (#1), one new rubric (#2), one skill-output line + rules update (#3 post-descope), one setup template split (#4), three doc edits (#5, #6, #7-hold). New concepts: the hook-class tagging (advisory vs enforcement, low vs high severity) is one genuinely new concept with a clear purpose. Deletion cost is low — most changes are reversible via git revert; the pruned hooks after #2 are harder to restore but only lose signal, not correctness.

## Tensions Surfaced

**Challenger A (Claude) pushed harder to simplify** (suggested #1 could be a 5-line fix, suggested #3 descope, suggested #7 removal). **Challenger B (GPT-5.4) pushed harder on security/trust** (session-state flag, prompt-injection paths). **Challenger C (Gemini) ran fewer tool calls** (2 vs 45 and 11) but converged with A on the #2 rubric problem. The unanimous #2 rubric finding is the strongest signal — it survived three very different review styles.

## Cost of NOT Building

- **L25 stays open indefinitely.** Every multi-session build risks repeating the same miss.
- **Telemetry data never generated.** Hook pruning stays hunch-driven. Scott-pilot framing question stays unanswered.
- **`/review` keeps failing the same way.** L30-L32's conclusion never operationalizes.
- **Tier 0 adoption stays friction-heavy** for any new user.

None of these are being addressed by other workstreams. Cost of deferral compounds.

## Simplest Version (revised post-challenge)

Ship **#1 + #2 + #3-descoped** in one commit or linked sequence. With Fix 5 applied, #3 is now small enough to bundle.

- **#1:** one new hook file (~80-100 lines), one flag file, ~5 lines in intent router.
- **#2:** execute existing plan after tagging hooks (30 min) and updating rubric (~1 page of plan text).
- **#3-descoped:** two lines in `/review` skill output + convention documented in `review-protocol.md`.

Defer #4, #5, #6 to a separate bundle (hygiene cleanup, no architectural dependency on #1-#3). #7 stays held.

## Artifacts

- `tasks/buildos-improvements-proposal.md` — input proposal
- `tasks/buildos-improvements-enriched.md` — debate input with prior context
- `tasks/buildos-improvements-findings.md` — raw 3-model challenger output
- `tasks/buildos-improvements-judgment.md` — independent judge (sonnet-4-6) verdict
- `tasks/buildos-improvements-challenge.md` — this synthesis

## Next Step

**`/plan buildos-improvements-bundle-1`** scoping the build to #1 + #2-tagging + #3-descoped, applying the 5 inline fixes from this synthesis. The hygiene bundle (#4, #5, #6) can stay on the backlog as a separate plan.

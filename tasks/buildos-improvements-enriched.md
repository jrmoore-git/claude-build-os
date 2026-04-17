---
topic: buildos-improvements
created: 2026-04-16
---
# BuildOS Framework Improvements — Seven Changes

## Project Context
BuildOS is a governance framework for multi-session development with Claude Code. Core abstractions: state on disk (PRD, decisions, lessons, handoff), staged pipeline (think → challenge → plan → build → review → ship), enforcement ladder (lesson → rule → hook → architecture), and cross-model review via three model families. Current surface: 22 skills, 23 hooks, 31 scripts, 8 rule files. Used primarily by the author on personal projects; being piloted with an external user (Scott).

## Recent Context
- Session-telemetry plan was written, reviewed across 3 models, and pre-mortem'd this session (2026-04-16 late evening). It is ship-ready but not yet executed. Motivation: Scott-pilot framing revealed that BuildOS has two distinct value claims (session infrastructure vs governance enforcement) and no current way to distinguish them in data.
- Monolith extraction of `debate.py` has been ongoing over the last ~5 sessions (4,629 → 4,369 lines across 6 commits). Latent test-ordering bug surfaced in session 6 (L39) and was resolved.
- Three-way model panel converged on a wrong answer earlier in April (L28) because operational evidence was missing from the input, motivating stricter proposal templates.
- L25 documented that review-after-build has no structural enforcement — advisory rules in 3 places all fail silently under context pressure. Still open as of this session.

## Problem
Three pressures are compounding on the framework:

1. **Surface area has outgrown intuition.** The author can no longer tell which of the 21 hooks earn their keep per session. The session-telemetry plan addresses this by instrument; it hasn't been run yet.
2. **The most-documented failure mode is still structurally unenforced.** L25 (advisory review-after-build fails under context pressure) has been open for ~3 weeks. The intent router watches user messages, not workflow state. The gate exists at commit time but gets bypassed via `[TRIVIAL]` when context is already decayed.
3. **The review protocol has no learning loop.** L30-L32 concluded that simulation quality comes from iterative refinement on concrete failures, not upfront configuration. That conclusion has not propagated into `/review` — a reviewer that fails today fails the same way tomorrow.

Secondary pressures (lower priority): Tier 0 install footprint doesn't match the README's "start small" pitch; three struck-through Essential Eight invariants carry DNA from a different project; anti-slop word list catches symptoms, not causes.

## Proposed Approach

Seven changes, independently valuable. Ordered roughly by value/effort.

### #1 — Structural review gate after build
Add `hook-post-build-review.py` (PostToolUse:Write|Edit). It maintains a per-session counter of edits since the last `tasks/*-review.md` was written. When the counter crosses a threshold (proposal: 10 edits within an active plan) OR a plan's `implementation_status` flips to `shipped`, the hook writes a state flag read by the intent router, which injects a non-advisory suggestion to run `/review` before commit. Existing `hook-review-gate.sh` (commit-time) continues to catch the commit boundary. This hook catches the build boundary earlier.

### #2 — Ship the telemetry plan, then prune hooks
Execute `tasks/session-telemetry-plan.md` (already specced and reviewed). Run for 2 weeks. Then prune hooks whose `(fire_rate × block_rate)` falls below a threshold to be set after seeing the distribution. Target ceiling: 12-15 hooks (down from 21 active).

### #3 — `/review` learns from dismissed findings
Every `/review` run appends findings + lens + reviewer model to `stores/review-log.jsonl`. Add a `/log --dismiss-finding <finding-id>` flow (or a post-commit annotation) that tags findings as dismissed. Add `scripts/review_feedback.py` that, on each new `/review` run, retrieves the 3-5 most recent dismissed findings matching the current lens and injects them as negative examples in the lens prompt ("do not flag X-category findings unless Y"). Local, prompt-level accretion. No RLHF.

### #4 — Tier 0 install footprint matches the README
Currently `/setup` installs Tier 2 surface regardless of tier declaration. Split templates into three tiers. Tier 0 ships exactly: `CLAUDE.md` stub, `tasks/lessons.md`, `tasks/handoff.md`. Tier 1 adds: `tasks/decisions.md`, `docs/project-prd.md`, and 2 advisory hooks (read-before-edit, pre-commit-tests). Tier 2 is the current surface. `/setup` asks for tier explicitly and only copies what matches.

### #5 — Strip Essential Eight strike-throughs from CLAUDE.md
Replace the 8-item list (3 struck through) with the 5 invariants that actually apply to BuildOS. The struck-through items (approval gating, state machine validation, exactly-once scheduling) are DNA from a different project (downstream outbox). Carrying them as "N/A" is text pollution at the top of a load-bearing doc.

### #6 — Delete or replace the anti-slop word list
Current: 17 banned words in `code-quality.md`. Symptoms-level. False positives on legitimate technical writing ("robust under concurrent writes", "comprehensive test coverage"). Two options:
  - **Delete.** Trust authors. Reviewers catch real slop in context.
  - **Replace with proximity heuristic.** `pre-commit-banned-terms.sh` exists; convert it to flag paragraphs with ≥3 marketing-adjacent constructions in proximity (adjective pile-ups, hollow comparatives, vague claim density), not individual words.

Recommendation: delete. The cost of a false positive (author rewrites a legitimate sentence) exceeds the cost of a false negative (slop passes through a human reviewer).

### #7 — [Speculative — explicitly pressure-test before building] Model-tier-aware hook activation
Some hooks (read-before-edit, bash-fix-forward) were written for weaker models. On Opus 4.7, their failure modes may be rare enough that the hooks are net-negative overhead. Add optional `min_model_tier` annotation to hooks in settings.json; sessions where `CLAUDE_MODEL` meets the threshold auto-skip. Held separately because false negatives could be silent and expensive.

**Non-goals:**
- No rewrite of the debate.py engine. Monolith extraction is in progress; don't interleave.
- No new skills. The skill count (22) is not the problem.
- No attempt to multi-player-ify the framework (multi-human review, team handoff). Explicitly single-developer-focused.
- No new rule files. Changes land in existing rules or as hooks.
- No migration of the stores/ format. Append-only JSONL stays.

## Simplest Version

Ship only #1 and #2. They are the highest-value, each standalone, and each creates evidence that informs whether #3-#7 are worth pursuing. #1 closes the most-documented failure mode. #2 generates the data to make the rest of the pruning decisions evidence-based. If #1 and #2 prove insufficient after 2-3 weeks of use, the remaining 5 stay on the backlog.

The even smaller version: just #1. It's a single hook file (~60 lines), a flag file, and 5 lines added to the intent router. Ships in one commit. If that alone changes the review-after-build rate materially, the case for the rest is strengthened.

### Current System Failures

Three concrete instances of the problems this proposal addresses:

1. **L25 (review-after-build gap):** "Built /simulate (6 files), ran /simulate to validate, fixed issues, declared done — never suggested /review. Plan said 'run /review when complete', routing table condition #6 matched (3+ files, no review artifact), but all three are advisory text. No hook checks mid-session state." Active lesson, unresolved.

2. **L28 (cross-model panel converged on wrong answer):** "3 independent models all said 'sim-compiler is commodity, don't build' — unanimous and wrong. Root cause: proposal lacked eval_intake.py's track record. Models said 'DeepEval does this' without anyone checking whether DeepEval actually meets the specific requirements." Same-family reviewers will converge the same way next time — no learning loop.

3. **Telemetry session (2026-04-16):** The author had to spec a ~210-LOC telemetry plan and run a 3-model document review + 1-model pre-mortem to decide *whether the framework's hooks are earning their keep*. That the question needs instrumentation to answer is itself the failure — the system has outgrown intuition about its own value.

### Operational Context

Real numbers from the running system:

- **Hooks active:** 23 hook files in `hooks/`. Per CLAUDE.md tier declaration, Tier 0 activates 5, Tier 1 activates 8, Tier 2 activates all. Default is Tier 3 (fail closed).
- **Skills:** 22 user-invocable skills in `.claude/skills/`.
- **Scripts:** 31 in `scripts/`, including `debate.py` (~4,369 lines after 6 extractions), `bootstrap_diagnostics.py` (silent-on-success wrapper for session start).
- **Rule files:** 8 in `.claude/rules/` (code-quality, design, natural-language-routing, orchestration, review-protocol, security, session-discipline, skill-authoring) + `bash-failures.md` + `workflow.md` + `reference/platform.md`.
- **Debate log:** `stores/debate-log.jsonl` has 417 entries across the framework's life.
- **Session log:** `tasks/session-log.md` is 3,318 lines (mature). Lessons: 60 lines, decisions: 175 lines.
- **Lessons file state:** 9 active lessons (L25, L28, L30, L31, L32, L33, L36, L37, L39). 6 promoted (to rules or hooks). 16 archived. Target ≤30 active.

### Operational Evidence

Prior attempts at pieces of this proposal:

- **#1 (review-after-build):** Three advisory surfaces have been tried (plan text, routing table condition #6, intent router). All failed silently under context pressure (L25 documents the case). No structural enforcement has been built yet. No evidence either direction on whether a PostToolUse-counter approach will work — net new.
- **#2 (telemetry-then-prune):** Telemetry plan exists, reviewed, pre-mortem'd. Not executed. No prior pruning based on data.
- **#3 (review learning loop):** L30-L32 explored iterative refinement on concrete failures in the eval_intake context. Found: simulation quality improvements must modify the skill prompt itself (the artifact), not runtime context. The proposal here adapts that finding to `/review` — modify the lens prompt, not the runtime, using dismissed findings as negative examples. Adaptation, not duplication.
- **#4 (Tier 0 install):** No prior attempt. Current `/setup` treats tier as a declaration, not an install gate.
- **#5 (Essential Eight):** No prior attempt. Text has been in CLAUDE.md since framework inception.
- **#6 (anti-slop word list):** `pre-commit-banned-terms.sh` exists and enforces the list. No prior attempt at a proximity heuristic or deletion. No data on false-positive rate.
- **#7 (model-tier annotations):** No prior attempt. Speculative.

### Baseline Performance

Current behavior on the dimensions this proposal changes:

- **Review-after-build rate:** Unmeasured. L25 provides one known-miss case. No systematic data — part of #2's motivation.
- **Hook fire rate:** Unmeasured. No per-hook instrumentation exists yet (fixed by #2).
- **Review finding dismissal rate:** Unmeasured. Findings are currently written to `tasks/*-review.md` with no post-commit tracking of which were applied vs. ignored.
- **Tier 0 adoption friction:** Unknown. No user-facing metric. Anecdotal: the Scott pilot is proceeding at Tier 2 by default.
- **Anti-slop false-positive rate:** Unknown. `pre-commit-banned-terms.sh` logs hits but not dismissed-as-legitimate counts.

## Summary — What This Proposal Is and Isn't

- **Is:** A bundle of 7 surgical changes, most of which are subtractions or small additions (the largest is #3, which adds one JSONL store and one script). Four are load-bearing (#1, #2, #3, #4); three are hygiene (#5, #6, #7-hold).
- **Isn't:** A redesign. No change to the pipeline, the enforcement ladder, the LLM boundary, the cross-model review model, or the skill set. The framework's core architecture stands; this proposal tightens its calibration.
- **Cost of not building:** L25 stays open. Telemetry stays unexecuted. `/review` stays non-learning. Tier 0 adoption stays friction-heavy. These failure modes compound; none are currently being addressed by other workstreams.

## Prior Context (auto-enriched)

Relevant lessons retrieved by `scripts/enrich_context.py`:
- **L25** — Review-after-build has no enforcement; advisory rules in 3 places all failed silently. Directly motivates change #1.
- **L32** — Runtime directive injection degrades simulation quality. Informs change #3: modify the lens prompt (the artifact), not runtime context.
- **L33** — `debate.py --enable-tools` produces false verification claims with high confidence. **Challengers should verify file existence with deterministic tools (ls/grep), not rely on LLM recall.** Relevant for this challenge run itself.
- **L36** — Zero-functionality refactors of a monolith are safe when test suite is fast and commits stay small. Relevant to how #3 would be implemented.
- **L37** — Rules that depend on author discipline keep failing; enforcement has to live in a single owned surface. Directly supports the promotion logic for #1.

Relevant decisions:
- **D5** — Thinking modes are single-model. Multi-model reserved for validate/refine. Cross-model challenge is the right tool here (go/no-go decision, not exploration).
- **D12** — Solo user, rip-and-replace for renames (no backward-compat). Relevant to #4, #5, #6 (subtractions).
- **D13** — Use review-panel (parallel) for cross-model evaluation. Current skill default.
- **D20** — Keep sim infrastructure; no external tool meets the requirements. Precedent for "build-vs-adopt" calls in the framework.
- **D24** — Session-start diagnostics are silent-on-success; `bootstrap_diagnostics.py` owns the user-visible surface. Pattern precedent for #1's "single owned surface" logic.

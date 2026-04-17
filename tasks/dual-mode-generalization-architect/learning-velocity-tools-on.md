---
debate_id: learning-velocity-tools-on
created: 2026-04-17T14:51:42-0700
mapping:
  A: claude-opus-4-7
personas:
  A: architect
---
# learning-velocity-tools-on — Challenger Reviews

## Challenger A (architect) — Challenges
Devastating finding. `scripts/lesson_events.py` **already exists and already implements velocity metrics** from a dedicated event log (`stores/lesson-events.jsonl`). The proposal says "derive from git log on tasks/lessons.md" as if this doesn't exist. This is a parallel, inferior measurement layer.

I have enough evidence for a strong review.

## Challenges

1. **OVER-ENGINEERED / ALTERNATIVE** [MATERIAL] [COST:TRIVIAL]: The pruning heuristic in the proposal ("has this hook fired in 30 days?") duplicates and *regresses* existing infrastructure. `scripts/session_telemetry_query.py` already exports `cmd_prune_candidates` with a 4-class rubric (enforcement-high/low, advisory, unknown), a two-gate test (`SESSION_COUNT_GATE=30` sessions AND `FIRST_SESSION_AGE_DAYS=28`), `block_rate` as signal (not just "did it fire"), and an `enforcement-high` exemption — plus a documented rubric cited as `docs/reference/hook-pruning-rubric.md` and the `# hook-class:` tag convention (commit `62e317b`). The proposed "fired in 30d?" check would flag a correctly-calibrated enforcement-high hook for pruning the moment nobody violates it, which is the *opposite* of the intended signal. Fix: have `/healthcheck` shell out to `session_telemetry_query.py prune-candidates` instead of inventing a new rule. EVIDENCED: `cmd_prune_candidates` verified present; constants `SESSION_COUNT_GATE`, `PRUNE_FIRE_THRESHOLD`, `PRUNE_BLOCK_RATE_THRESHOLD`, `CLASS_ORDER` confirmed in source.

2. **OVER-ENGINEERED / ALTERNATIVE** [MATERIAL] [COST:TRIVIAL]: The measurement layer ("git log math on tasks/lessons.md") duplicates `scripts/lesson_events.py`, which already exists with `log_event`, `compute_metrics`, `seed_from_lessons`, `VALID_STATUSES = {created, resolved, promoted, archived, violated, updated}`, and a dedicated event store at `stores/lesson-events.jsonl`. Git log math is strictly worse: it can't distinguish "promoted" from "archived" from "edited for a typo," and it re-derives state that's already logged. Fix: `/healthcheck` should call `lesson_events.py metrics --json`. EVIDENCED: `scripts/lesson_events.py` file content inspected, lines 1–50.

3. **ASSUMPTION** [MATERIAL] [COST:SMALL]: The proposal assumes the problem is "no measurement/verification/pruning exists." The verified problem is narrower: **the capabilities exist but aren't wired into `/healthcheck`**. I searched the `skills` file set for `session_telemetry_query` and `hook-fires` and got zero matches; neither does `/healthcheck` appear to invoke `lesson_events.py metrics` (proposal itself concedes "Current measurement: none"). That reframes the work from "build three capabilities" to "wire three existing scripts into the healthcheck skill and add the stale-lesson → `/investigate --claim` trigger." This is a substantially smaller change and changes the recommendation from "build new" to "integrate existing." EVIDENCED: `check_code_presence` on `skills` for `session_telemetry_query` returned `exists=false`; `hook-fires` returned `exists=false`.

4. **RISK** [MATERIAL] [COST:TRIVIAL]: Auto-running `/investigate --claim` on 2–3 stalest lessons per full-scan is the one genuinely new capability. At the stated cost (EVIDENCED from proposal: $0.05–0.10/call, ~30s each) and low full-scan frequency, the budget is fine. But the selection rule ("stalest, no activity >14d") will repeatedly re-verify the *same* stale lessons across scans if the user doesn't act on the verdict — burning spend on known-stale items. Add a "don't re-verify within N days unless lesson text changed" guard. This is a 5-line memo in `stores/`, not architecture.

5. **UNDER-ENGINEERED** [ADVISORY]: "Rule redundancy vs hooks" is proposed as a string/semantic match ("does a hook already enforce this?"). That's the hardest of the three capabilities and the proposal hand-waves it. Rules and hooks don't share vocabulary — e.g., `rules/security.md` vs `hook-guard-env.sh` or `hook-pre-edit-gate.sh`. Without a declared mapping (frontmatter: `enforces-rule: security.md#no-secrets-in-commits`), this check will either over-flag or silently miss. Defer this third capability until a rule↔hook link is explicit in metadata.

6. **ADVISORY**: The "Simplest Version" (15 lines of git-log bash in Step 6) is actively the wrong starting point given `lesson_events.py metrics --json` already returns the numbers. Starting with git-log math means committing a second source of truth that will drift.

## Concessions

1. The problem statement is real and well-evidenced: L17/L18/L19 staleness (EVIDENCED from proposal) and the absence of a feedback loop on the enforcement ladder are genuine gaps.
2. Correctly refuses to build a dashboard or auto-pruning — surfacing candidates in `/healthcheck` output and keeping the human in the loop matches the existing pattern (`FOOTER` in `session_telemetry_query.py` says exactly this: "Findings are candidates for investigation, not evidence for deletion").
3. Correctly identifies that "rules encode the positive pattern when lessons get promoted" — no new positive-capture system needed.

## Verdict

**REVISE** — the *goal* is right and the gaps are real, but two of three proposed capabilities reinvent existing scripts (`lesson_events.py`, `session_telemetry_query.py prune-candidates`) with weaker heuristics; the actual work is integration into `/healthcheck` plus the stale-lesson auto-verify trigger, which is materially smaller than the proposal describes.

---

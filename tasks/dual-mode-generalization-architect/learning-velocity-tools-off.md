---
debate_id: learning-velocity-tools-off
created: 2026-04-17T14:50:41-0700
mapping:
  A: claude-opus-4-7
personas:
  A: architect
---
# learning-velocity-tools-off — Challenger Reviews

## Challenger A (architect) — Challenges
## Challenges

1. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The "staleness = age + no activity" heuristic is unvalidated. The 2026-04-11 investigation found L17/L18/L19 stale — but were they the *oldest* lessons with *no activity*, or just randomly sampled? If staleness correlates poorly with age, auto-running `/investigate --claim` on the stalest 2-3 will waste panel calls on lessons that are fine while recently-touched-but-wrong lessons rot. EVIDENCED: 3/4 lessons tested were stale (small N). SPECULATIVE: that age-based selection would have caught those same three. Fix: record which selection heuristic would have flagged the known-stale lessons before committing to "stalest N."

2. [UNDER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: The rule-vs-hook redundancy check is defined as "does a hook already enforce this?" but there's no specified matching mechanism. String match on filenames? Tag metadata? LLM judgment? Without a concrete rule, this step either becomes a noisy LLM call every healthcheck or produces nothing. Specify the match criterion before shipping — even "both reference the same rule ID in frontmatter" is enough.

3. [RISK] [ADVISORY]: Hook "hasn't fired in 30 days" conflates "not load-bearing" with "successfully preventing the bad behavior." A hook that blocks a mistake people stopped making *because the hook exists* looks identical to dead code. Flagging-only (not auto-prune) mitigates this, but the flag language matters — "candidate for removal" will bias the reviewer. Frame as "low-activity hook, confirm still needed."

4. [ALTERNATIVE] [ADVISORY]: Velocity metrics from git log on a single file (`tasks/lessons.md`) will miss promotions *out* of lessons into rules/hooks — which is the signal you most want (ladder is working). Consider also diffing `.claude/rules/` and `hooks/` additions over the same window. Still trivial git log math.

5. [OVER-ENGINEERED] [ADVISORY]: Auto-running `/investigate --claim` inside `/healthcheck` couples two skills. At 5-10 debate runs/day and $0.05-0.10/call, cost isn't the issue (ESTIMATED: 2-3 calls per full scan × low scan frequency = pennies/week), but a healthcheck that silently spends money and 60-90s is surprising. Print the candidates and let the user run `/investigate` explicitly — or require an `--auto-verify` flag. Preserves the "simplest version" discipline the proposal already advocates.

## Concessions
1. Correctly identifies that governance-without-feedback is the real failure mode, and the enforcement ladder has no self-measurement.
2. "Simplest version = 15 lines of git log math, ship first, add rest if useful" is exactly the right sequencing.
3. Resisting the temptation to build a dashboard or new governance file is disciplined — metrics belong in the existing tool.

## Verdict
APPROVE — ship the simplest version (metrics only) as specified; defer verification and pruning until the metrics themselves prove useful, and tighten the staleness heuristic and redundancy-match criterion before those phases land.

---

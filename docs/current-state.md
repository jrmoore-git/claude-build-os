# Current State — 2026-04-17 (Frame lens shipped)

## What Changed This Session
- Frame lens shipped as 4th `/challenge` persona — critiques the candidate set itself (binary framings, missing compositional candidates, source-driven proposals, problem inflation), not the candidates inside the proposal.
- Dual-mode expansion under `--enable-tools`: `frame-structural` (claude-sonnet-4-6, no tools — structural reasoning) + `frame-factual` (gpt-5.4, tools on — staleness/already-shipped verification) running in parallel.
- Cross-family routing (sonnet structural + gpt-5.4 factual) via new config key `frame_factual_model`. Validated as BETTER on 4/5 historical proposals than same-family.
- n=5 paired validation across historical proposals (autobuild, explore-intake, learning-velocity, streamline-rules, litellm-fallback): ~30 novel MATERIAL findings beyond the original 3-persona panel; one verdict flipped REVISE → REJECT.
- Orthogonal fixes shipped alongside: `_validate_challenge` scoped to `## Challenges` section (no more false-positive Concessions warnings); `_build_frontmatter` expands nested dicts as YAML keys (no more Python repr); fallback flip moved before persona expansion (`/review`-found bug).
- Cross-model `/review` PASSED. 1 MATERIAL fixed inline (fallback ordering), 6 advisories tracked.
- Lessons L43 (tool-bias on frame critique + dual-mode + cross-family) and L44 (n=1 is not data; quality-first methodology) added. Decision D28 recorded.
- 965 tests pass (was 957). Added `TestFramePersona` (6 tests) + 2 new validator scope tests.

## Current Blockers
- None blocking next-session work.

## Next Action
Run paired output-quality audit (n=5, paired comparisons, quality first per L44) across other personas (architect, security, pm) and other multi-model systems (judge round, refine rotation, `/review` lenses, `/polish` rounds, `/explore` directions, `/pressure-test` models). Determine where the verification-vs-reasoning tool-posture axis from L43 generalizes.

## Recent Commits
- `b9b3a79` — Frame lens plan: record shipped_commit bfdf4ff
- `bfdf4ff` — Frame lens: 4th /challenge persona with dual-mode cross-family expansion
- `72e145e` — Session wrap 2026-04-16: Frame lens plan recovered + on disk

## Followup tracked (post-ship, not blocking)
- Sonnet structural latency outlier (324s on litellm-fallback in cross-family run) — separate investigation.
- Lessons at 34/30 — triage needed (candidates: L41 hook-symlink now resolved; L43 could promote to .claude/rules/).
- Application of paired audit to other personas — primary goal of next session.

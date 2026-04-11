# Handoff — 2026-04-10

## Session Focus
Fixed root cause of noisy debate.py invocations: created invocation reference doc so future sessions don't guess at CLI arguments.

## Decided
- Architecture-level fix (reference doc at decision point) over hook-level enforcement (forcing --help reads)

## Implemented
- `.claude/rules/reference/debate-invocations.md` — patterns for challenge, judge, refine, review, review-panel, explore, pressure-test, pre-mortem, full pipeline
- CLAUDE.md pointer: "read invocation reference before calling directly"

## NOT Finished (carried over)
- **Update gstack 0.14.5.0 → 0.16.3.0** — gets browser data platform
- **Create `scripts/browse.sh`** — thin wrapper, fixes two broken design skills
- deploy_all.sh customization for BuildOS
- Audit findings 11-13
- `/define discover` live test

## Next Session Should
1. Read this handoff
2. Update gstack to 0.16.3.0 and create `scripts/browse.sh`
3. Test `/browse` and `/qa` end-to-end
4. Pick up carried-over items

## Key Files Changed
CLAUDE.md
.claude/rules/reference/debate-invocations.md

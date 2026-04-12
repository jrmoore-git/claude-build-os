---
topic: gstack-integration
created: 2026-04-11
---
# gstack Integration Strategy — What to Borrow, What to Ignore

## Problem
gstack (Garry Tan's AI engineering framework) is installed at ~/.claude/skills/gstack/ with 31 skills and a headless browser binary. BuildOS's `/design` skill (3 of 4 modes) references `scripts/browse.sh` which doesn't exist — those modes are non-functional. Meanwhile gstack continues shipping updates (0.14.5 → 0.16.3+) with capabilities BuildOS doesn't replicate. Without a deliberate integration strategy, we either miss complementary value or accidentally duplicate work.

## Proposed Approach
Four-tier integration:

1. **Finish what's started:** Build `scripts/browse.sh` as thin wrapper around gstack's browse binary. This unblocks `/design review`, `/design consult`, `/design variants`.
2. **Adopt complementary skills via symlink:** Add `/benchmark` (performance regression), `/canary` (post-deploy monitoring), `/investigate` (structured debugging). These fill real gaps in the post-`/ship` pipeline.
3. **Version upgrade:** Update gstack 0.14.5 → 0.16.3 after browse.sh works. Adds scrape, data, media, network interception.
4. **Keep BuildOS versions of overlapping skills:** All review, planning, challenge, and session management stays BuildOS-native. gstack equivalents are weaker (single-model vs cross-model debate).

**Non-goals:**
- Not replacing any BuildOS skill with a gstack equivalent
- Not forking or modifying gstack source
- Not adding gstack's design binary until it exits draft status
- Not building our own browser — gstack owns that runtime

## Simplest Version
Build `scripts/browse.sh` (estimated ~20 lines). Test `/design review` against a real page. If it works, the strategy is validated — gstack's browser complements BuildOS's thinking layer.

### Current System Failures
1. `/design review` mode calls `bash scripts/browse.sh goto` — file doesn't exist, mode is broken (lines 128, 176-178, 554, 627 of design/SKILL.md)
2. `/design consult` Phase 0 visual competitive research is non-functional — depends on browse.sh
3. `/design variants` can't generate visual comparisons — depends on browse.sh
4. No post-deploy monitoring after `/ship` completes — canary gap

### Operational Context
- debate.py: 176 entries in debate-log.jsonl, runs ~5-10 times/day
- gstack installed at v0.14.5.0, current release is 0.16.3.0
- Browse binary exists at ~/.claude/skills/gstack/browse/dist/browse (~58MB compiled)
- 3 gstack skills already symlinked into BuildOS (/browse, /connect-chrome, /setup-browser-cookies)
- 18 BuildOS-native skills active

### Baseline Performance
- `/design review`: Non-functional (browse.sh missing)
- `/design consult` Phase 0: Non-functional (browse.sh missing)
- `/design variants`: Non-functional (browse.sh missing)
- Post-deploy monitoring: Does not exist
- Performance regression detection: Does not exist

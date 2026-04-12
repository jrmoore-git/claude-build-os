---
topic: gstack-integration
created: 2026-04-11
scope: strategy
review_backend: cross-model
security_posture: 2
recommendation: SIMPLIFY
complexity: low
challengers: claude-opus-4-6, gpt-5.4, gemini-3.1-pro
tag: MATERIAL
---
# Challenge Result: gstack-integration

## Recommendation: SIMPLIFY

The core fix (unblocking `/design` modes) is unanimously validated. The broader 4-tier integration strategy is premature — scope to Tier 1 only, defer Tiers 2-4 to separate proposals.

## Consensus Findings (all 3 challengers agree)

1. **The problem is real.** `scripts/browse.sh` doesn't exist, `/design` SKILL.md references it on 4+ lines, 3 of 4 design modes are non-functional. This is a genuine broken-window.

2. **The non-goals are correct.** Not forking gstack, not replacing BuildOS skills, not building a competing browser — these boundaries prevent the most likely failure modes.

3. **Tiers 2-4 are premature.** Symlinks for `/benchmark`, `/canary`, `/investigate` should not be pre-approved here. Each needs its own review for: credential handling, external network calls, logging behavior, and how it hooks into the existing pipeline. Without pipeline integration (e.g., `/ship` triggering `/canary`), they become shelfware.

4. **Version upgrade must be isolated.** Don't build against 0.14.5 then upgrade underneath. Either build against 0.16.3 from the start, or document the stable interface contract.

## Material Challenges

### browse.sh wrapper vs. composing with /browse skill (Challenger C)
Challenger C argues `browse.sh` is redundant since `/browse` is already symlinked — `/design` should compose with the existing skill directly instead of wrapping the raw binary. This is a genuine architectural question: wrapper script vs. skill composition. **The proposal should evaluate both approaches.**

### Hard dependency on unversioned external binary (Challenger A)
The 58MB browse binary lives in `~/.claude/skills/gstack/browse/dist/browse` — a user-home path BuildOS doesn't control. The wrapper needs: existence check, version check, graceful failure when missing (CI, new machines, onboarding).

### URL/cookie guardrails (Challenger B)
If browse.sh passes arbitrary URLs to the browser, it opens SSRF and local file access patterns. At security posture 2, this is advisory not blocking, but minimum guardrails are cheap: scheme allowlist (http/https), denylist for localhost/private ranges, careful cookie handling.

### Unverified asset claims (Challengers A + B)
Several claims in the proposal (3 skills already symlinked, binary size, gstack version) were not independently verified by challengers. Treat as plausible but confirm before building.

## Advisory Findings

- The 4-tier structure may be over-formalized for what is currently: write one wrapper/integration, test it (Challenger A)
- gstack skills like `/benchmark` and `/canary` may expose production URLs, telemetry, or deployment credentials — review before adopting (Challenger B)
- The claim "gstack equivalents are weaker" should be re-evaluated if gstack improves in future versions (Challenger A)

## Revised Scope

**Build only Tier 1:**
1. Determine whether browse.sh wrapper or `/browse` skill composition is the right integration point
2. Implement with existence/version checking and graceful degradation
3. Add minimal URL guardrails (advisory at posture 2, but cheap)
4. Test `/design review` against a real page end-to-end
5. Defer all other tiers to future proposals after Tier 1 proves the pattern

## Artifacts
- `tasks/gstack-integration-proposal.md` — original proposal
- `tasks/gstack-integration-findings.md` — raw challenger output
- `tasks/gstack-integration-challenge.md` — this synthesis

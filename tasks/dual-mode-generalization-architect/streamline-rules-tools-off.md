---
debate_id: streamline-rules-tools-off
created: 2026-04-17T14:50:52-0700
mapping:
  A: claude-opus-4-7
personas:
  A: architect
---
# streamline-rules-tools-off — Challenger Reviews

## Challenger A (architect) — Challenges
## Challenges

1. [ASSUMPTION] [ADVISORY]: "Instruction compliance decreases as instruction count grows" is cited as motivation but the proposal doesn't quantify it for this specific ruleset. SPECULATIVE — the 10-12% token recovery is EVIDENCED as arithmetic but the *compliance benefit* is unmeasured. This doesn't block the proposal (the ambiguity fixes stand on their own merit) but don't oversell the verbosity cuts.

2. [RISK] [MATERIAL] [COST:TRIVIAL]: Cross-file references ("See code-quality.md", "See review-protocol.md Definition of Done") create a new failure mode: if Claude only loads CLAUDE.md in a given context, the referenced content isn't present. You're trading duplication for a dependency graph. For rules that are *always* in effect (simplicity, verify-before-done, document-first), losing the inline statement in CLAUDE.md means relying on Claude to follow the pointer. Mitigation: keep the one-line directive inline in CLAUDE.md and put only *elaboration* behind the reference. Your 2B and 2C already do this correctly; 2A and 2G do not — they move the directive itself out. Fix: preserve the imperative sentence in CLAUDE.md, move only the explanation.

3. [RISK] [MATERIAL] [COST:TRIVIAL]: Phase 1A changes CLAUDE.md from "after" to "before" material decisions — but "document before implementing" has a failure mode the current wording avoids: decisions made mid-implementation (discovered constraints, pivots) need to be captured too. "Before implementing" can be read as "only before, not during/after." Recommend: "Record material decisions in decisions.md as they are made — before implementation when possible, immediately after when discovered mid-work. Never defer past session end." This resolves the contradiction without creating a new gap.

4. [ASSUMPTION] [ADVISORY]: Phase 1C designates CLAUDE.md as canonical for skip conditions because it's "always loaded." But workflow.md's T2/standard tier logic is the *mechanism* for skip decisions; CLAUDE.md just lists categories. These aren't the same abstraction — one is a category list, one is a tier-based decision procedure. Verify they're actually equivalent before declaring "no change needed" to workflow.md. If the tier table implies additional skip conditions not in CLAUDE.md's list, you've introduced a new contradiction while claiming to fix one.

5. [OVER-ENGINEERED] [ADVISORY]: Phase 3A (removing origin tags, ~50 tokens) and 3B (~100 tokens) together save ~150 tokens — ~1% of total. The effort-to-value ratio is low and origin tags can serve a real purpose (knowing *why* a rule exists affects how strictly to apply it at the edges). If you're cutting them, cut them because they're noise, not for the token budget. Consider keeping origin tags on rules that came from specific incidents — that provenance helps future reasoning about whether the rule still applies.

6. [UNDER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: No rollback or validation plan. How do you verify the "same governance" claim post-change? Recommend: (a) run a known-contradiction prompt through Claude pre- and post-change and confirm behavior is unchanged or improved; (b) keep the diff reviewable in one PR per phase so Phase 1 (ambiguity) can ship even if Phase 2 (deduplication) is contested. Bundling all three phases risks one objection blocking the ambiguity fixes, which are the highest-value part.

## Concessions

1. Phase 1 (ambiguity fixes) is unambiguously correct work — contradictions in rule files are pure liability and the proposal correctly identifies the outlier in each case.
2. The proposal correctly distinguishes "remove duplication" from "remove rules" and preserves hook enforcement. The constraint discipline is good.
3. Designating canonical locations based on which file has the more complete treatment (e.g., code-quality.md for simplicity, security.md for LLM boundary) is the right heuristic rather than arbitrary choice.

## Verdict

REVISE — ship Phase 1 as its own change, fix the inline-directive-vs-reference pattern in 2A/2G, and tighten the 1A wording before merging. The ambiguity work is clearly net-positive; the deduplication work is sound in principle but has a few spots where the reference replaces the rule itself rather than just the elaboration.

---

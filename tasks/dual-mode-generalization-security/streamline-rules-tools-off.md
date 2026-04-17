---
debate_id: streamline-rules-tools-off
created: 2026-04-17T14:50:49-0700
mapping:
  A: gpt-5.4
personas:
  A: security
---
# streamline-rules-tools-off — Challenger Reviews

## Challenger A (security) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal assumes cross-file references preserve behavior because the same files remain available, but that only holds if the runtime always loads linked rule files with equal priority and visibility. If some surfaces are conditionally loaded, summarized, or truncated, replacing duplicated hard rules with “see X” can weaken enforcement at the trust boundary between always-present instructions and sometimes-present references. The proposal should explicitly verify file loading semantics for `CLAUDE.md` vs `.claude/rules/*.md` vs `.claude/rules/reference/*.md` before treating deduplication as governance-neutral.

2. [RISK] [MATERIAL] [COST:TRIVIAL]: Phase 2 moves several operationally important directives out of always-loaded or high-salience locations into references, which creates a prompt-instruction dilution risk even if the content technically still exists. In particular, “verify before done,” “fix-forward,” and documentation timing affect whether untrusted intermediate outputs are accepted without validation. The risk of the change is reduced compliance due to indirection; the risk of not changing is continued ambiguity and token bloat. A safer version would keep terse normative statements in the top-level file and deduplicate only explanatory text.

3. [ASSUMPTION] [ADVISORY]: The quantitative savings are **ESTIMATED**: assumes the cited ~12,810-token total and that the listed cuts survive formatting and replacement text with no offsetting additions. The proposal gives a reasonable breakdown, but the claimed ~1,200-1,500 token recovery and ~10-12% reduction should be validated against actual rendered prompt assembly before being used to justify prioritization.

4. [RISK] [ADVISORY]: Tightening prose in security-sensitive rules can remove examples that currently disambiguate edge cases. The allowlist and CSV formula-injection rewrites look directionally sound, but compression in security guidance should be checked to ensure no trusted/untrusted data handling nuance is lost for future maintainers.

## Concessions
- The proposal identifies real contradictions and resolves them in a coherent direction, especially the “before vs after” documentation rule.
- It explicitly preserves hooks and avoids changing enforcement mechanisms, which limits security regression surface.
- It distinguishes canonical sources from references rather than deleting rules outright, which is safer than broad simplification.

## Verdict
REVISE — the cleanup is mostly sound, but it needs explicit validation of rule-loading semantics and should retain short top-level normative statements for critical controls rather than relying on indirection alone.

---

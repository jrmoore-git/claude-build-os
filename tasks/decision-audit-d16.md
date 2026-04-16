---
decision: D16
original: "Natural language is the primary interface — slash commands are power-user shortcuts"
verdict: HOLDS
audit_date: 2026-04-15
models: gpt-5.4, claude-opus-4-6, gemini-3.1-pro
---
# D16 Audit

## Original Decision

BuildOS routes users to skills via natural language intent, not memorized commands. Three layers: (1) advisory routing rule in `.claude/rules/natural-language-routing.md`, (2) `hooks/hook-intent-router.py` (UserPromptSubmit) — deterministic regex-based intent classification with artifact-state awareness, (3) `hooks/hook-error-tracker.py` — proactive `/investigate` suggestions after 2+ same-class failures. Suggestions are advisory, fire once per skill per session.

## Original Rationale

Advisory rules fail under context pressure (proven: L21, L25, L29). 22 skills create a memorization burden. Hooks make suggestions deterministic without being blocking. Performance: ~28ms overhead per message.

## Audit Findings

**3-model review: 2× HOLDS, 1× REVIEW**

The core rationale holds across all three models. The REVIEW verdict (gpt-5.4) identifies enhancements, not architectural flaws.

**What holds:**
- The problem (memorization burden, advisory rule failure) is real and empirically documented
- Three-layer architecture is sound and internally consistent with project lessons
- Advisory-never-blocking posture is correct for a solo developer context
- Proactive artifact-gap routing (proposal-no-challenge, plan-no-premortem, dirty-tree-no-review) is the highest-value component and directly addresses L25

**Material findings from review panel:**

1. **ADR description overstates implementation.** "Natural language intent" implies semantic understanding; the actual implementation is deterministic regex + artifact-state checks. Low risk — framing issue only.

2. **First-match-wins misses compound-intent messages.** "Review this and also build a new feature" routes only to `/review`. This is a known gap (documented in implementation). Multi-intent routing was not explored as an alternative. Moderate risk, low frequency.

3. **No regression tests for 577-line routing hook.** Regex patterns can drift as skills evolve. The hook warrants a sample-message/expected-skill test file.

4. **Advisory rule and hook can diverge.** The `<!-- Enforced-By -->` annotation is informational, not enforced. A sync check or lint would prevent drift.

## Verdict

**HOLDS.** The decision is grounded in empirical failure evidence (L21, L25, L29), correctly positions the approach in the advisory-not-blocking design space, and addresses the real problem. The three-model panel found no architectural flaw.

Two enhancements are worth tracking but do not change the verdict: (a) add routing tests for the hook, (b) consider multi-intent matching for compound prompts.

## Risk Assessment

| Scenario | Risk |
|---|---|
| Keep as-is | Low — known gaps degrade gracefully (advisory suggestions, not gates) |
| Revert to advisory-only | High — re-introduces the exact failures that motivated D16 |
| Make blocking | High — hostile UX, breaks override path for edge cases |
| Add tests + multi-intent | Low — incremental enhancement, no architectural change |

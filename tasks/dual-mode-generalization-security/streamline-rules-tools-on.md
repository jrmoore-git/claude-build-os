---
debate_id: streamline-rules-tools-on
created: 2026-04-17T14:50:58-0700
mapping:
  A: gpt-5.4
personas:
  A: security
---
# streamline-rules-tools-on — Challenger Reviews

## Challenger A (security) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal assumes all “canonical” references are always co-loaded or reliably reachable at the moment the rule matters, but the repo already encodes load-scope differences in frontmatter and file placement. For example, `.claude/rules/security.md` is scoped by globs and contains security-critical guidance like secret redaction, shell argument leakage, untrusted-text handling, and the LLM boundary. Moving CLAUDE-facing summaries to indirect references can weaken enforcement at the trust boundary if the active prompt no longer includes the operative rule text when handling untrusted input or credentials. Before deduplicating, verify the runtime loading model for `CLAUDE.md` vs `.claude/rules/*.md` vs reference docs and preserve direct inclusion for rules needed at decision time, not just discoverability time.

2. [RISK] [MATERIAL] [COST:SMALL]: Phase 1 changes alter normative behavior, not just wording. Example: changing “update decisions.md after material decisions” to “before implementing material decisions” affects sequencing and could create pressure to persist tentative or sensitive design details earlier than today. In a system that writes to `tasks/decisions.md`, `tasks/session-log.md`, and handoff artifacts, earlier documentation can increase exposure of unreviewed plans, security-sensitive implementation details, or credentials-adjacent context if operators are not disciplined. The proposal should explicitly define what must be documented before implementation and what must remain out of durable artifacts (secrets, exploit details, raw untrusted content).

3. [UNDER-ENGINEERED] [MATERIAL] [COST:MEDIUM]: The proposal claims “same governance, same enforcement, same rules,” but it does not include a regression method to prove semantic equivalence after compression. Given existing contradictions and security-sensitive rules, this needs a diff-driven validation step: enumerate every imperative/prohibition in source files, map each to its canonical destination, and fail the change if any directive is lost, softened, or moved out of scope. Without that, the main risk of the change is silent policy regression; the risk of not changing is continued ambiguity and token waste.

4. [ASSUMPTION] [ADVISORY]: The quantitative benefit is only estimated. “~12,810 tokens” and “~1,200-1,500 recoverable (~10-12%)” are ESTIMATED based on the proposal’s own counts; no measured tokenization data from the files is provided here. That does not invalidate the direction, but those numbers should not drive prioritization without a reproducible count.

5. [ALTERNATIVE] [ADVISORY]: Instead of replacing duplicated sections with one-line references, consider retaining terse local “must/never” bullets for high-risk areas and moving only rationale/examples to canonical files. That gives most of the token savings while reducing the chance that a security or review invariant becomes non-operative when a reference is missed.

## Concessions
- Correctly identifies real ambiguity already visible in the docs, such as conflicting `/challenge` skip conditions and differing orient-before-planning guidance.
- Preserves hook-backed enforcement boundaries; the proposal does not suggest weakening code-level controls or changing hooks.
- The tightened security wording shown for allowlist checks, CSV formula injection, and worktree path handling is clearer and keeps the core protection intent.

## Verdict
REVISE — the streamlining direction is sound, but you need an explicit semantic-equivalence and load-scope safety check to ensure compression doesn’t silently weaken security- or review-critical rules.

---

---
debate_id: streamline-rules-intake
created: 2026-04-17T16:17:03-0700
mapping:
  A: claude-sonnet-4-6
  B: gpt-5.4
personas:
  A: frame-structural
  B: frame-factual
---
# streamline-rules-intake — Challenger Reviews

## Challenger A (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL] [COST:SMALL]:** The proposal treats "same governance, same enforcement" as a given, but the deduplication strategy (canonical file + one-line reference) assumes Claude reliably follows cross-file references at inference time. There is no evidence cited that Claude actually loads and integrates referenced files when it encounters "see workflow.md for the full checklist." If the always-loaded CLAUDE.md previously contained the full rule and now contains only a pointer, compliance may drop for exactly the rules the proposal claims to preserve. The proposal's own premise — "instruction compliance decreases as instruction count grows" — is SPECULATIVE (no citation, no measurement against this codebase). The inverse claim (that pointers are as effective as inline rules) is equally unverified. This is load-bearing for the entire Phase 2 strategy.

2. **ASSUMPTION [MATERIAL] [COST:SMALL]:** The proposal assumes all 15 files are loaded in every session. The repository manifest shows `hook-context-inject.py` (which injects context dynamically), `tier_classify.py`, and `hook-tier-gate.sh` — suggesting context loading is conditional and tier-dependent. If rule files are selectively loaded based on task tier, then "canonical file" placement matters enormously: moving a rule from CLAUDE.md (always-loaded) to code-quality.md (possibly tier-gated) is a governance regression, not neutral compression. The proposal never audits which files are loaded under which conditions before designating canonicals.

3. **ALTERNATIVE [MATERIAL] [COST:SMALL]:** A missing candidate is **inline annotation rather than cross-file reference**. Instead of "See code-quality.md. The simplest version wins unless there's evidence otherwise," the CLAUDE.md entry could be compressed to a single terse line ("Simplest version wins. No docstrings unless public API.") without creating a dependency on another file being loaded. This captures ~80% of the token savings from Phase 2 with zero compliance risk from broken reference chains. The proposal never considers this middle path between "full duplication" and "pointer-only."

4. **OVER-ENGINEERED [ADVISORY] [COST:TRIVIAL]:** Phase 3 (verbosity tightening) is the highest-confidence, lowest-risk work in the proposal — pure compression with no structural changes. Yet it's sequenced last and bundled with the riskier Phase 1 and Phase 2 changes. Phases 1 and 3 could be shipped independently and immediately; Phase 2 (the structurally risky deduplication) could be held pending evidence. The proposal doesn't offer this decomposition.

5. **ASSUMPTION [ADVISORY] [COST:TRIVIAL]:** The token count (12,810 total, 1,200-1,500 recoverable) is ESTIMATED with no methodology shown. The 10-12% recovery figure is presented as if precise. Given that context window economics are the stated motivation, the proposal should show per-file token counts to validate that the canonical-file strategy actually reduces tokens in the loaded context (not just in files that may not be loaded together).

6. **ALTERNATIVE [ADVISORY] [COST:TRIVIAL]:** The proposal doesn't consider **consolidating files rather than cross-referencing them**. If session-discipline.md and workflow.md both duplicate CLAUDE.md content, one option is merging session-discipline.md into CLAUDE.md's session section and eliminating the file. Fewer files with denser content may outperform many files with pointers, especially if file-loading has overhead or the reference chain is fragile.

7. **RISK [ADVISORY] [COST:TRIVIAL]:** Fix 1A ("document before or after implementation") changes CLAUDE.md's behavior for decisions.md updates. The proposal asserts "after" is the outlier without examining whether the distinction was intentional — decisions.md may have been deliberately post-hoc (record what was decided, not what you plan to decide). Aligning to "before" could cause Claude to write speculative decisions that never get implemented, polluting the decisions log. The proposal treats this as a typo fix when it may be a semantic difference.

---

## Concessions

1. **Phase 1 contradiction fixes are well-scoped.** The four ambiguities identified (1A–1D) are genuine: conflicting before/after, inconsistent skip conditions, and the 6-vs-8 invariant mismatch are real governance problems that force Claude to make arbitrary choices. These fixes are low-risk and high-value.

2. **Phase 3 verbosity cuts are sound.** The specific compression targets (origin tags, preambles, over-explained rules) are correctly identified as pure noise. The proposed rewrites preserve directive content while cutting explanation. This is the strongest part of the proposal.

3. **The constraint framing is honest.** Explicitly stating "no rules removed, no hooks changed, no enforcement weakened" and calling this compression-not-reduction is the right frame. It correctly scopes the work and prevents scope creep.

---

## Verdict

**REVISE** — Phase 1 and Phase 3 are approvable as-is; Phase 2's cross-file reference strategy rests on an unverified assumption that pointers are compliance-equivalent to inline rules, and skips the simpler alternative of terse inline compression. The proposal should either (a) split Phase 2 out for separate validation, or (b) replace pointer-only deduplication with terse-inline compression for rules in always-loaded files.

---

## Challenger B (frame-factual) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal’s baseline inventory is stale/wrong: it says the rule set is “CLAUDE.md + 10 rule files + 4 reference files” and repeatedly targets `CLAUDE.md` plus `.claude/rules/reference/*.md`, but the repo manifest provided for this review does not list `CLAUDE.md` at all, and the actual reference path in the repo is `docs/reference/code-quality-detail.md`, not `.claude/rules/reference/*.md`. Tool verification also shows rule files already point to `docs/reference/code-quality-detail.md` (`.claude/rules/code-quality.md:50`). This changes the execution plan because a large fraction of the proposed edits target files/paths that are not the current surface.  

2. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: Several “current contradiction” examples are not present in the current repo state. For example, `workflow.md` already says “Pipeline tiers: see CLAUDE.md. Skip conditions for /challenge: defined authoritatively in CLAUDE.md” and “Verify before done — see review-protocol.md Definition of Done” (`.claude/rules/workflow.md:9,19`), meaning parts of Phase 2C/2D are already shipped. Likewise, `security.md` already contains the tightened allowlist and CSV-formula wording nearly verbatim (`.claude/rules/security.md:24-25`), and `orchestration.md` already has the compressed relative-path guidance (`.claude/rules/orchestration.md:43-45`). The proposal overstates remaining duplication/verbosity and should be rescoped to the deltas that still exist.

3. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal claims a contradiction around the “essential eight” invariant text, but tool checks did not find either cited current phrasing (`"6 of 8 apply"` not found via docs search; `"The essential eight invariants apply to every change"` not found in rules). That makes one of the four headline contradictions unverified. Since the proposal’s motivation depends on “4 contradictions,” this weakens both prioritization and expected impact.

4. [UNDER-ENGINEERED] [ADVISORY]: The token-savings claim is not grounded in repo evidence here. “~12,810 tokens” and “~1,200–1,500 recoverable” are **SPECULATIVE**: no measured file contents, counts, or script output were cited in the proposal, and multiple suggested compressions are already present in the current files. The recommendation may still be directionally fine, but the quantitative justification needs a fresh measurement before it drives scope.

## Concessions
- The proposal is directionally right that the ruleset is being actively streamlined already: `workflow.md` already delegates pipeline tiers and skip conditions instead of duplicating them.
- The security-tightening examples are good patterns, and the repo already reflects that concise style in `security.md`.
- The “same governance, less noise” goal is consistent with current rule wording in several files and is a reasonable objective.

## Verdict
REVISE — the proposal’s core goal is plausible, but its factual baseline is stale enough (wrong target files/paths and already-shipped edits presented as pending) that it needs a fresh repo-grounded diff before acting.

---

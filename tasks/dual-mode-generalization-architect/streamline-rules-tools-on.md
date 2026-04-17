---
debate_id: streamline-rules-tools-on
created: 2026-04-17T14:51:37-0700
mapping:
  A: claude-opus-4-7
personas:
  A: architect
---
# streamline-rules-tools-on — Challenger Reviews

## Challenger A (architect) — Challenges
Confirmed. The current state of rules/ already has:

- workflow.md Fix-Forward section (lines 58-60): already a 3-line reference to bash-failures.md — **proposal 2E already done**
- review-protocol.md line 58-60: "Typical paths by change type → Tier definitions and full pipeline routes: see CLAUDE.md." — **proposal 2D already done**
- review-protocol.md line 74: essential eight already reads "(6 applicable to BuildOS — see CLAUDE.md for applicability)" — **proposal 1D already done**
- session-discipline.md: no "Review requirement" paragraph to cut — **proposal 2B for session-discipline already done or never existed**

The proposal describes a "current state" that is largely stale. Many Phase 1 and Phase 2 items are already applied. Token recovery estimates are correspondingly inflated. I can't verify CLAUDE.md itself (not in rules/ file_set and not in allowed dirs for snippet reading), but every rules/-side claim I've checked describes already-completed work as if pending.

## Challenges

1. **ASSUMPTION [MATERIAL] [COST:SMALL]**: The proposal's "current state" is stale for multiple rules/ files. Verified against the live tree:
   - Proposal 1C (review-protocol.md should reference CLAUDE.md for skip conditions) — **already done**. review-protocol.md line 26 reads: "Skip conditions: Defined authoritatively in CLAUDE.md. Do not maintain a separate list here." EVIDENCED.
   - Proposal 1D (review-protocol.md should say "6 applicable to BuildOS — see CLAUDE.md") — **already done**. Line 74 reads exactly that. EVIDENCED.
   - Proposal 2C (workflow.md "Verify before done" should reference review-protocol.md) — **already done**. Line 19 reads: "Verify before done — see review-protocol.md Definition of Done." EVIDENCED.
   - Proposal 2D (workflow.md tier table + review-protocol.md "Typical paths" should point to CLAUDE.md) — **already done**. workflow.md line 9: "Pipeline tiers: see CLAUDE.md." review-protocol.md line 60: "Tier definitions and full pipeline routes: see CLAUDE.md." EVIDENCED.
   - Proposal 2E (workflow.md Fix-Forward should be a 1-line reference to bash-failures.md) — **already done**. workflow.md lines 58-60 are exactly the proposed 1-line reference form. EVIDENCED.
   - Proposal 2G (workflow.md "Document first, execute second" should reference session-discipline.md) — **already done**. Line 18. EVIDENCED.
   
   Fix: re-baseline the proposal against HEAD before executing; the pending surface is much smaller than 1,200–1,500 tokens.

2. **ASSUMPTION [MATERIAL] [COST:TRIVIAL]**: The claimed contradiction in 1A is misquoted. session-discipline.md line 9 actually reads "Persist corrections and decisions **after deciding on them and before implementing them**" — not "Every correction must be persisted BEFORE implementation" as the proposal states. EVIDENCED. The rules/-side text is already consistent with "before implementing." The only remaining question is the CLAUDE.md "after material decisions" wording, which I cannot verify with available tools (CLAUDE.md is outside the rules/ file_set). Scope shrinks to a single-line CLAUDE.md edit — if that wording even exists as quoted.

3. **ASSUMPTION [MATERIAL] [COST:TRIVIAL]**: The proposal quotes review-protocol.md as saying `/plan --skip-challenge`. A substring search for `skip-challenge` returns zero matches in rules/. EVIDENCED. Either the quote is fabricated or it lives in CLAUDE.md. Verify the source before editing.

4. **RISK [ADVISORY]**: Token-recovery claim "~1,200-1,500 tokens (~10-12%)" is SPECULATIVE now that roughly half the Phase 1+2 items are already applied. The remaining work is mostly Phase 3 tightening (origin tags, preambles, verbose rule expansions), which the proposal itself sizes at roughly 50+100+150+40+35+30 ≈ 405 tokens. Plus whatever remains in CLAUDE.md itself. Real recoverable tokens are likely in the 400–700 range, not 1,200–1,500. This doesn't change whether to do the work, but it changes how to sell it.

5. **RISK [ADVISORY]**: Phase 3A deletes "Origin:" tags globally. Substring search for `Origin:` in rules/ returns zero matches. EVIDENCED. The tags may live only in docs/reference files outside the rules/ file_set. Confirm they still exist at the claimed locations (code-quality-detail.md is referenced 1× but may itself be under docs/reference/ based on the "reference/" hits — not in the rules/ manifest listing). Risk is trivial wasted effort, not governance damage.

6. **UNDER-ENGINEERED [ADVISORY]**: No mechanism is proposed to prevent future drift back into duplication. Given that the codebase already went through one round of deduplication (evident from current state) and the proposal is reporting on a pre-dedup snapshot, there's clearly a drift pattern. A lightweight cross-file duplication linter (or a pre-commit check that flags when canonical-marked sections appear verbatim in other rules files) would protect the compression. Not required for this proposal to proceed, but worth a 1-line follow-up in the refined spec.

## Concessions

1. The **principle** is sound: canonical-plus-reference beats copy-paste across rule files, and the proposal correctly identifies the canonical file in each case. Where the work remains undone (Phase 3, Phase 2A/B/F), the assignments are defensible.
2. The constraint framing ("same governance, same enforcement, zero rules removed") is the right frame for a compression pass and makes review cheap.
3. Phase 3 verbosity fixes (origin tags, preambles, security allowlist/CSV one-liners, compaction protocol, How-to-Route) are genuinely high-signal — these read like rules after the edit rather than prose about rules, which is what you want in an always-loaded context.

## Verdict

**REVISE** — the proposal is directionally correct but operating on a stale snapshot: at least 6 of the Phase 1/2 edits it prescribes are already in the tree. Re-baseline against HEAD, drop the completed items, verify the 1A/1C source quotes against CLAUDE.md (not rules/), and rescope the token-recovery claim to what actually remains (likely ~400–700 tokens, dominated by Phase 3). Once re-baselined, the remaining work is SMALL and safe to ship.

---

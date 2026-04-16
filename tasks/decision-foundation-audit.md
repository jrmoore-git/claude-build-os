---
topic: decision-foundation-audit
created: 2026-04-15
method: 21 parallel agents, each building own context from raw files, 3-model review panel + independent judge per decision
models: claude-opus-4-6, gemini-3.1-pro, gpt-5.4 (review), gpt-5.4 (judge)
trigger: Discovery of two structural bugs — insufficient context to external models (L28) and conservative/recency bias without judge (L29)
---

# Decision Foundation Audit — Full Results

## Summary

| Verdict | Count | Decisions |
|---------|-------|-----------|
| **HOLDS** | 13 | D1, D2, D3, D7, D11, D12, D13, D14, D15, D16, D17, D19, D21 |
| **REVIEW** | 7 | D4, D5, D8, D9, D10, D18, D20 |
| **REVERSE** | 1 | D6 (records hygiene — already superseded by D11) |

**Bottom line:** No decisions need to be reversed on architectural grounds. The two bugs produced conservative bias (under-building) not reckless bias (building the wrong thing). 7 decisions need targeted follow-up — mostly deferred work that should no longer be deferred, or claims that need empirical validation.

---

## HOLDS (13 decisions) — No Action Required

### D1: Python + Shell default, TypeScript allowed
The revised version (2026-04-15) already corrected for conservative bias — the original Python-only ban was the conservative outcome.

### D2: LiteLLM proxy for cross-model calls
Direct developer decision from project init. Load-bearing for D5, D13, D18. Not pipeline-dependent.

### D3: Skills are SKILL.md prompt documents
Correct and lightweight. Minor: skills growing large (/review at 770 lines). Monitor for attention-degradation.

### D7: Adaptive pre-flight questioning
Well-evidenced (4.8-5.0/5, v7 iteration). Conservative bias would have pushed against this, not for it.

### D11: Domain-agnostic explore with adaptive dimensions
Evidenced by 3.4→4.4+ across 8 domains. Expanded capability against conservative pressure.

### D12: Rip-and-replace skill renames, no aliases
Proven by D14's 193-reference rename. Correct for solo dev.

### D13: Parallel review-panel, not serial calls
Pure efficiency. Verified ThreadPoolExecutor in code. Orthogonal to bias bugs.

### D14: /check renamed to /review
Restored correct name. Load-bearing for D15.

### D15: /review auto-detects content type
Expanded capability. Evaluate/improve distinction reinforced by D17.

### D16: Natural language routing via hooks
Correct structural response to L25 (advisory rules fail under context pressure). Enhancement-level gaps only.

### D17: Refine critique mode
Data-justified with A/B evidence. Neither bug applies — adds capability.

### D19: compactPrompt is not a valid settings.json field
Empirical fact. Conservative bias doesn't apply to schema validation.

### D21: Judge step in /challenge
The fix itself. Unanimous: correct root cause, correct countermeasure. Monitor for judge permissiveness.

---

## REVIEW (7 decisions) — Targeted Follow-Up Required

### D4: Security posture flag
**Before:** Security posture is a user choice via --security-posture (1-5).
**After audit:** Decision may be over-engineering if D21's judge step already corrects the security over-rotation that motivated it.
**Action:** A/B test judge-only vs judge + posture control. If judge-only matches, D4 is redundant complexity. Also: add minimum posture floors for credentials/auth/destructive ops regardless of user setting.
**Risk:** Low either way. Flag is optional, defaults sensibly.

### D5: Thinking modes are single-model
**Before:** explore, pressure-test, pre-mortem use single-model. Multi-model for review/refine only.
**After audit:** Holds for explore (generative/ideation). Does NOT hold for pressure-test — adversarial critique needs reasoning independence a single model can't provide. Original benchmark may have been context-corrupted.
**Action:** A/B test single-model vs multi-model specifically for pressure-test on real plans. Implementation cost is low (debate.py already supports --models).
**Risk:** Medium. If pressure-test has been systematically missing risks due to single-model blind spots, past pressure-tests may have been less thorough than believed.

### D8: Upgrade /status with smart routing instead of /next
**Before:** Hooks rejected as "binary block/allow" and "annoying."
**After audit:** Core routing holds. Hook rejection rationale is obsolete — D16 proved hooks can inject non-blocking advisory suggestions.
**Action:** Annotate D8 rationale so it's not cited as precedent against advisory hooks. No architecture change needed (D16 already patched the gap).
**Risk:** None. Records hygiene only.

### D9: Consolidate exploration guidance into "Inspect before acting"
**Before:** Advisory rule ships now. Pre-edit hook deferred because "PreToolUse hook infrastructure doesn't exist yet."
**After audit:** Deferral rationale is obsolete. 17 hooks now exist including hook-pre-edit-gate.sh. The read-before-edit enforcement is now buildable.
**Action:** Build the read-before-edit hook. The blocker cited in D9 no longer exists. Conservative bias kept this deferred when it shouldn't have been.
**Risk:** Low to build. The hook pattern is proven.

### D10: /think discover generates the PRD interactively
**Before:** PRD generation embedded in /think discover as Phase 6.5.
**After audit:** PRD-as-conversation-byproduct holds. But /think discover is 1036 lines + ~200 for Phase 6.5. Multiple models flagged attention-degradation risk.
**Action:** Run /simulate quality-eval on 5+ sessions to check Phase 6.5 reliability. If >10% step dropout, extract to companion /prd skill.
**Risk:** Medium. Silent step dropout means PRDs get partially generated with no error signal.

### D18: Keep Gemini 3.1 Pro with timeout hardening
**Before:** Automatic fallback to next model on timeout.
**After audit:** Keeping Gemini holds. But the claimed fallback is **not wired for challenger calls**. `_call_with_model_fallback` only exists in the refine command. Challenger calls use `_call_litellm` directly — ~6.4% of challenge runs silently lose one voice.
**Action:** Wire `_call_with_model_fallback` in `_run_challenger`. This is a real bug, not a design question.
**Risk:** Medium. Silent voice loss in challenges degrades the very pipeline these bugs were about.

### D20: Keep sim infrastructure, generalize eval_intake.py
**Before:** Keep all V2 scripts. No external tool meets requirements.
**After audit:** Direction holds (keep sim, reject external tools). But "keep ALL V2 scripts" overclaims — sim_persona_gen.py and sim_rubric_gen.py have 0 tests, never reviewed. Sim-generalization hasn't been /challenge gated (L27 violation).
**Action:** /review V2 scripts → /challenge sim-generalization → validate on second skill → document cost (~500K-800K tokens/run) → evaluate Inspect AI hybrid.
**Risk:** Medium. Committing to ungated, unreviewed code violates the project's own governance.

---

## REVERSE (1 decision) — Records Hygiene

### D6: Explore presents 3 bets with fork-first format
**Before:** Hardcoded product-market dimensions, 150-word descriptions, comparison table.
**After audit:** Every specific implementation element was superseded by D11 one day later. The core principle (multiple directions, not one) carried forward. The codebase already reflects D11.
**Action:** Mark D6 as superseded by D11 in decisions.md. No code changes.
**Risk:** None.

---

## Cross-Cutting Findings

1. **Conservative bias produced under-building, not wrong-building.** The most common damage pattern: work deferred when it should have proceeded (D9's hook, D5's multi-model pressure-test). No decision built the wrong thing.

2. **Several agents couldn't run the judge step** because `debate.py judge` requires challenge-format frontmatter. The review panel output doesn't have this format. This is a gap in debate.py — the judge should accept any structured findings input, not just challenge artifacts.

3. **D18's fallback bug is the highest-priority finding.** It's a real code bug that silently degrades the challenge pipeline — the same pipeline these bugs were about fixing.

4. **D5 and D4 may interact.** If D21's judge already fixes the security over-rotation, and multi-model pressure-test fixes the adversarial blind spots, the security posture flag may be unnecessary complexity. Worth testing together.

5. **Skill size is an emerging concern.** D3 holds but D10's 1036-line /think discover is near an attention ceiling. Multiple agents independently flagged this across different decisions.

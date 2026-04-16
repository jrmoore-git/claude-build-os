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
| **REVIEW → RESOLVED** | 7 | D4, D5, D8, D9, D10, D18, D20 |
| **REVERSE → RESOLVED** | 1 | D6 (records hygiene — superseded by D11) |

**Bottom line:** All 21 decisions audited, all action items resolved. No decisions reversed on architectural grounds. The two bugs (L28 context gap, L29 conservative bias) produced under-building, not wrong-building. Remediation shipped across sessions 15-18 + this session (D4 posture floors).

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

## REVIEW (7 decisions) — All Resolved

### D4: Security posture flag — RESOLVED
**Before:** Security posture is a user choice via --security-posture (1-5).
**After audit:** Decision may be over-engineering if D21's judge step already corrects the security over-rotation that motivated it.
**Action:** ~~A/B test judge-only vs judge + posture control.~~ Analysis: D4 and D21 are orthogonal — D21 fixes pipeline structure, D4 communicates user intent. A/B unnecessary. ~~Also: add minimum posture floors.~~ **Shipped:** `_apply_posture_floor()` in debate.py enforces posture >= 3 on content matching credentials/auth/destructive patterns. Wired in challenge, judge, review. 32 tests.
**Risk:** Resolved.

### D5: Thinking modes are single-model — RESOLVED
**Before:** explore, pressure-test, pre-mortem use single-model. Multi-model for review/refine only.
**After audit:** Holds for explore (generative/ideation). Does NOT hold for pressure-test — adversarial critique needs reasoning independence a single model can't provide. Original benchmark may have been context-corrupted.
**Action:** ~~A/B test single-model vs multi-model specifically for pressure-test.~~ **Shipped:** `--models` flag added to pressure-test (session 18). A/B on context-packet-anchors doc: multi-model found 3 unique insights single missed, synthesis adjudicated disagreements. See `tasks/d4-d5-ab-analysis.md`.
**Risk:** Resolved.

### D8: Upgrade /status with smart routing instead of /next — RESOLVED
**Before:** Hooks rejected as "binary block/allow" and "annoying."
**After audit:** Core routing holds. Hook rejection rationale is obsolete — D16 proved hooks can inject non-blocking advisory suggestions.
**Action:** ~~Annotate D8 rationale.~~ **Done (session 15).** Rationale update added to D8 in decisions.md noting hook-rejection precedent is obsolete.
**Risk:** Resolved.

### D9: Consolidate exploration guidance into "Inspect before acting" — RESOLVED
**Before:** Advisory rule ships now. Pre-edit hook deferred because "PreToolUse hook infrastructure doesn't exist yet."
**After audit:** Deferral rationale is obsolete. 17 hooks now exist including hook-pre-edit-gate.sh. The read-before-edit enforcement is now buildable.
**Action:** ~~Build the read-before-edit hook.~~ **Shipped (session 16).** `hook-read-before-edit.py` — dual-phase PostToolUse:Read + PreToolUse:Write|Edit. 41 tests, 944 total suite. CLAUDE.md hook count 17→18.
**Risk:** Resolved.

### D10: /think discover generates the PRD interactively — RESOLVED
**Before:** PRD generation embedded in /think discover as Phase 6.5.
**After audit:** PRD-as-conversation-byproduct holds. But /think discover is 1036 lines + ~200 for Phase 6.5. Multiple models flagged attention-degradation risk.
**Action:** ~~Run /simulate quality-eval.~~ Result: 100% step dropout confirmed. ~~Extract to /prd.~~ **Shipped (session 18).** `/prd` skill extracted. Phase 6.5 replaced with lightweight handoff suggesting `/prd`. See D10 implementation update in decisions.md.
**Risk:** Resolved.

### D18: Keep Gemini 3.1 Pro with timeout hardening
**Before:** Automatic fallback to next model on timeout.
**After audit:** Keeping Gemini holds. But the claimed fallback is **not wired for challenger calls**. `_call_with_model_fallback` only exists in the refine command. Challenger calls use `_call_litellm` directly — ~6.4% of challenge runs silently lose one voice.
**Action:** ~~Wire `_call_with_model_fallback` in `_run_challenger`.~~ **FIXED (session 15).** All 11 unprotected call sites now use `_call_with_model_fallback` with `_get_fallback_model` helper. 903 tests pass, cross-model review confirmed.
**Risk:** ~~Medium.~~ Resolved.

### D20: Keep sim infrastructure, generalize eval_intake.py — RESOLVED (superseded by D22)
**Before:** Keep all V2 scripts. No external tool meets requirements.
**After audit:** Direction holds (keep sim, reject external tools). But "keep ALL V2 scripts" overclaims — sim_persona_gen.py and sim_rubric_gen.py have 0 tests, never reviewed. Sim-generalization hasn't been /challenge gated (L27 violation).
**Action:** /challenge sim-generalization ran (v2, with operational evidence). Judge verdict: SPIKE. Spike ran (session 17): turn_hooks achieved 3.70/5 vs 4.73 baseline — partial pass, missed all 3 success criteria. **D22 supersedes:** V2 pipeline archived, pivot to iterative critique loop. IR compiler + rubric gen kept as standalone tools. Remaining D20 actions (full /review, second-skill validation, Inspect AI eval) mooted by pipeline retirement.
**Risk:** Resolved.

---

## REVERSE (1 decision) — Resolved

### D6: Explore presents 3 bets with fork-first format — RESOLVED
**Before:** Hardcoded product-market dimensions, 150-word descriptions, comparison table.
**After audit:** Every specific implementation element was superseded by D11 one day later. The core principle (multiple directions, not one) carried forward. The codebase already reflects D11.
**Action:** ~~Mark D6 as superseded by D11.~~ **Done (session 15).** D6 annotated `SUPERSEDED by D11` in decisions.md.
**Risk:** Resolved.

---

## Cross-Cutting Findings

1. **Conservative bias produced under-building, not wrong-building.** The most common damage pattern: work deferred when it should have proceeded (D9's hook, D5's multi-model pressure-test). No decision built the wrong thing.

2. **~~Several agents couldn't run the judge step~~** ~~because `debate.py judge` requires challenge-format frontmatter.~~ **FIXED (session 18).** `_auto_generate_mapping()` auto-generates mapping from challenger sections when frontmatter lacks it.

3. **~~D18's fallback bug is the highest-priority finding.~~** Fixed in session 15. All 11 call sites wired with `_call_with_model_fallback`.

4. **~~D5 and D4 may interact.~~** Resolved: D4 and D21 are orthogonal (D21 = pipeline structure, D4 = user intent). D5 multi-model PT shipped and validated. Posture floors enforce minimum security regardless of user setting. No redundancy found.

5. **Skill size is an emerging concern.** D3 holds but D10's 1036-line /think discover is near an attention ceiling. Multiple agents independently flagged this across different decisions.

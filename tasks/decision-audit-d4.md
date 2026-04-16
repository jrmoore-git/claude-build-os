---
decision: D4
original: "Security posture is a user choice via --security-posture flag, not a pipeline default"
verdict: REVIEW
audit_date: 2026-04-15
models_used: claude-opus-4-6, gemini-3.1-pro, gpt-5.4
---
# D4 Audit

## Original Decision

`--security-posture` (1–5) added to `debate.py`. At 1–2, security findings are advisory-only, PM is final arbiter. At 4–5, security can block. Default: 3 (balanced). Skills prompt the user before running.

## Original Rationale

A velocity-focused analysis spent pipeline capacity injecting security controls (egress policies, approval gates, credential rotation) into a speed-focused recommendation. Security was over-rotating as de facto final arbiter when PM should have been. *Date: 2026-04-10.*

## Audit Findings

**2 HOLDS, 1 REVIEW across three models.**

- **Gemini (REVIEW):** D4 predates D21 by five days. D21 fixed the structural "challengers get the last word" bias that may have been the root cause of security over-rotation. The two decisions may be complementary or redundant — an A/B test is required before knowing which.
- **Claude (HOLDS):** Problem was empirically observed (L10). Implementation is proportional. D21/L29 address the same class of problem and reinforce rather than undermine D4. Risk of reverting is medium.
- **GPT-5.4 (HOLDS):** Rationale fits project context (solo, CLI, no external surface). D21 makes D4 safer. Context gaps: L10 original content unavailable; no documented minimum-posture floors for high-risk actions (credentials, network egress, destructive ops).

**Judge verdict: SPIKE.** Challenge 1 (D4 may be over-engineering given D21) classified MATERIAL/SPIKE. The judge did not dismiss it because D4 predating D21 is a real architectural gap, not generic skepticism. Whether the two are additive or redundant is an empirical question, not resolvable by argument alone.

## Verdict

**REVIEW** — D4 holds as implemented but the relationship with D21 is unresolved. D21 (judge step) may already suppress the security over-rotation that motivated D4. If it does, D4 adds prompt complexity for no benefit. If it does not, D4 is independently necessary. Current state: both are active and appear complementary.

## Risk Assessment

**Risk of keeping:** Low. The flag is optional, defaults to 3 (balanced), and does not remove security from the pipeline. Downside is added prompt complexity and a cognitive overhead for the user to remember to adjust posture.

**Risk of changing (reverting to always-balanced):** Medium. Reintroduces the original failure mode from L10. Per L28, irrelevant security noise in context can also degrade recommendation quality by displacing more relevant evidence.

**Spike required (non-blocking for now):** Run A/B test comparing D21 judge-only vs D21 + posture control on a sample of low-security/velocity tasks and high-risk tasks. If judge-only matches posture-controlled runs on security-dominance rate and missed-risk rate, D4 may be removable. If posture control materially improves alignment, D4 holds and should be documented more prominently.

**One concrete gap:** No minimum-posture floors exist for actions involving credentials, network egress, destructive filesystem operations, or auth changes. These should enforce posture >= 3 regardless of user setting.

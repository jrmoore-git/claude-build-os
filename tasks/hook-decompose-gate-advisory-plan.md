---
scope: "Flip hook-decompose-gate.py from blocking (permissionDecision: deny) to advisory (allow + additionalContext). Gate becomes silent to the user — the agent receives the decomposition nudge as a prompt hint and decides whether to fan out. Threshold confirmed at ≥2 (cumulative-file trigger already behaved this way)."
surfaces_affected: "hooks/hook-decompose-gate.py, .claude/rules/orchestration.md, tests/test_hook_decompose_gate.py (new)"
verification_commands: "python3.11 -m py_compile hooks/hook-decompose-gate.py && python3.11 -m pytest tests/test_hook_decompose_gate.py -v && bash tests/run_all.sh"
rollback: "git revert <commit> — three-file revert (hook, rule doc, test file)"
review_tier: "Tier 2"
verification_evidence: "8/8 new tests pass (silent-allow: 5, nudge: 2, corrupt-flag: 1). Full suite 923/923 pass (up from 915 — gained 8 tests, no regressions). Advisory posture asserted explicitly in TestNudge._assert_advisory (allow + additionalContext, 'deny' string absent from output)."
---

# Plan: Decomposition gate — advisory posture

## Problem
Post-#2 (message translation, commit 416004d), the decomposition gate still rendered its `permissionDecisionReason` to the user on every fire because `permissionDecision: "deny"` forces Claude Code to surface the reason. The translation made the message readable; it didn't make it silent. Users saw framework-internal reasoning — "decomposition nudge" — on every session's 2nd-unique-file Write|Edit.

## Insight
The gate's job is to make the agent think about fan-out. That's agent-scoped reasoning, not user-scoped approval. Rendering the message to the user on every fire is the wrong posture — the user hasn't asked a question and doesn't need to answer one.

## Change
Flip the gate from blocking to advisory at all fire points:
- Return `permissionDecision: "allow"` (never deny)
- Carry the nudge in `additionalContext` (seen only by the agent's next turn)
- Keep the once-per-session dedup (nudge marker files) so repeated writes don't spam the additional context

Specific hook changes:
1. `NUDGE_MESSAGES` dict replaces `USER_MESSAGES` — two scenarios kept (escalated, plan_declared), two dropped (missing_reason, corrupt) because advisory posture has nothing meaningful to enforce for corrupt flags or missing bypass reasons.
2. `_with_context(kind)` helper replaces `_reason(kind, flag_path)` — returns allow + additionalContext.
3. Corrupt flag → silent allow (don't nag, let the next clean write reset state).
4. `plan_submitted` in main session → nudge once via `.plan-nudged` sentinel, then silent.
5. 2nd unique file → nudge once via `.nudged` sentinel, then silent.

## Orchestration.md update
Section "Decomposition Gate (Hook-Enforced)" → "Decomposition Gate (Hook-Enforced, Advisory)". Documents the new behavior, the ≥2 threshold (confirmed by empirical review of 15 historical plans), and notes that the flag-file mechanic is kept for backward compatibility but rarely needed under advisory posture.

## Threshold rationale
Audit of 15 `tasks/*-plan.md` showed: 6 plans at 1 component, 1 plan at exactly 2, 8 plans at 3+. The ≥2 threshold catches one marginal case more than ≥3 would (healthcheck-style: new skill + wiring). Under advisory posture, the cost of the extra fire is an ignored prompt hint — negligible. ≥2 is net-positive because the cost of false-negative (missed fan-out) is larger than false-positive (ignored nudge).

## Out of scope
- **Plan-driven trigger** (read `components:` from plan frontmatter instead of tracking writes_log). Separate change. Requires `.claude/skills/plan/SKILL.md` update to emit the field first. Scheduled as a follow-up.

## Verification
- `python3.11 -m py_compile hooks/hook-decompose-gate.py` → OK
- `python3.11 -m pytest tests/test_hook_decompose_gate.py -v` → 8/8 pass
- `bash tests/run_all.sh` → 923/923 pass (up from 915; gained 8, regressed 0)
- Assertion `'deny' not in json.dumps(out).lower()` in `TestNudge._assert_advisory` locks the advisory invariant

## Rollback
Three files. `git revert <commit>` restores prior behavior.

---
scope: "Rework hook-decompose-gate.py trigger: read `components:` from newest recent plan frontmatter instead of tracking cumulative file writes per session. Nudge only when a plan declares ≥2 independent components AND is fresh (<24h) AND session is in main repo."
surfaces_affected: "hooks/hook-decompose-gate.py, .claude/skills/plan/SKILL.md, tests/test_hook_decompose_gate.py"
verification_commands: "python3.11 -m py_compile hooks/hook-decompose-gate.py && python3.11 -m pytest tests/test_hook_decompose_gate.py -v && bash tests/run_all.sh"
rollback: "git revert <commit> — three-file revert"
review_tier: "Tier 2"
verification_evidence: "16/16 new tests pass (silent: 8, nudge: 6, edge: 2). Full suite 931/931 (up from 923; gained 8, regressed 0). Tests cover: no plan, 1-component plan, absent components field, stale plan (>24h), bypass flag, worktree agent, malformed frontmatter, newest-wins across multiple qualifying plans, inline+block list forms, once-per-session dedup, legacy plan_submitted flag, corrupt flag, missing tasks/ dir."
components:
  - Rewrite hook to parse plan frontmatter and fire on components ≥ 2
  - Update plan skill to emit components list after decomposition analysis
  - Rewrite tests for plan-driven trigger
---

# Plan: Decomposition gate — plan-driven trigger

## Problem
Prior trigger (cumulative-file tracking) fires on any 2+ file session, including bugfixes that touch multiple unrelated files. That's a proxy for the real signal — "plan declares multiple independent components" — and it produces false positives on sequential multi-file work. Under advisory posture the cost is small (an ignored hint), but the noise isn't zero and the precision is available.

## Change

**Hook rewrite** (`hooks/hook-decompose-gate.py`):
- Drop cumulative-file tracking (`writes_log` file, `.nudged` sentinel for file-count).
- Add `_extract_components(plan_path)` — stdlib-only frontmatter parser handling both block (`components:\n  - a\n  - b`) and inline (`components: [a, b]`) forms.
- Add `find_recent_plan_with_components(repo_root)` — returns newest `tasks/*-plan.md` within 24h whose components list has ≥2 entries.
- Fire nudge when such a plan exists, session is in main repo, and hasn't nudged yet (`.components-nudged` sentinel).
- Keep legacy `plan_submitted` flag path; keep `bypass` short-circuit; silent on corrupt flag.

**Plan skill update** (`.claude/skills/plan/SKILL.md`):
- Step 3b: after decomposition analysis identifies ≥2 independent components, emit them as a `components:` list in frontmatter. Name each by deliverable, not file. Omit the field for 1-component plans.
- Step 4: frontmatter template now documents `components:` as an optional block list.
- Output Format section: mention `components:` is optional and consumed by the decompose-gate hook.

**Tests** (`tests/test_hook_decompose_gate.py` — full rewrite):
- 8 silent-case tests (no plan, 1 component, absent field, stale, bypass, worktree, malformed, non-Write tool)
- 6 nudge-case tests (2 components, >3 with preview+count, inline form, once-per-session dedup, newest-wins, plan_submitted flag)
- 2 edge cases (corrupt flag, missing tasks/ dir)
- All assert advisory invariant (`permissionDecision: "allow"` + `additionalContext`; `"deny"` absent from output)

## Why 24h recency window
An old plan sitting in tasks/ from a previous task shouldn't trigger the nudge in an unrelated current session. 24h matches the `pre-edit-gate` recency window documented in docs/hooks.md. Session → plan correlation by mtime + window is the simplest heuristic; more precise (plan-per-branch, plan-per-topic) adds state without obvious payoff.

## Why ≥2 threshold
Empirical audit of 15 historical plans (see 6e65a51 commit message): 6 at 1 component, 1 at exactly 2, 8 at 3+. Under advisory posture the cost of firing on a sequential 2-component plan is one ignored hint; the cost of sequentializing genuine parallel work is a long session that should have been two short ones. ≥2 is net-positive.

## Migration
No migration needed. Existing plans without `components:` → silent (no nudge). Future plans emitted by `/plan` will have the field when decomposition analysis identifies ≥2 components. The cumulative-file fallback is not restored.

## Rollback
Three files. `git revert <commit>` restores prior behavior (cumulative-file trigger from 6e65a51).

---
scope: "Translate hook-decompose-gate.py deny messages to plain language; move JSON bypass mechanic behind a trailing [agent: ...] line. No trigger change, no behavior change."
surfaces_affected: "hooks/hook-decompose-gate.py"
verification_commands: "python3.11 -m py_compile hooks/hook-decompose-gate.py && python3.11 -c \"import importlib.util; s=importlib.util.spec_from_file_location('h', 'hooks/hook-decompose-gate.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); [print(m._reason(k, '/tmp/x')) for k in ('escalated','plan_declared','missing_reason','corrupt')]\""
rollback: "git revert <commit> — pure text change to one file, no data migration, no config changes"
review_tier: "Tier 2"
verification_evidence: "py_compile: OK. Live render via importlib shows plain-English lead + single [agent: ...] trailing line for all 4 message kinds (escalated, plan_declared, missing_reason, corrupt). Live confirmation: the new message fired on the plan-file write during this very commit session — behaved exactly as designed."
---

# Plan: Hook decompose-gate message translation

## Problem
`hooks/hook-decompose-gate.py` deny messages surfaced raw wire format to the user: `/tmp/claude-decompose-17242.json` paths, `echo '{"bypass": true, "reason": "<why>"}' > ...` JSON blobs, and `Bash:` prefixes. Violates `.claude/rules/skill-authoring.md` ("User-Facing Output — No Framework Plumbing"), produces visible noise in sessions where the gate fires correctly, and gives the user a mechanic they can't act on directly.

## Change
Replace the 4 inline deny-reason strings in `hook-decompose-gate.py` with a `USER_MESSAGES` dict keyed by scenario (escalated, plan_declared, missing_reason, corrupt) + a `_reason()` helper that appends a single `[agent: bypass via Bash → ...]` trailing line.

**No trigger change.** Same deny conditions, same allow conditions, same flag-file mechanic. Presentation-layer fix only.

## Out of scope
- **Plan-driven trigger swap** (cumulative-file → plan-artifact check). Separate change. Blocked on updating `.claude/skills/plan/SKILL.md` to emit a `components:` list in plan frontmatter when work fans into ≥3 independent subtasks. Without that, swapping the trigger today would silently disable the gate.
- **Extending skill-authoring.md to explicitly cover hooks.** The existing rule is narrow to skills. Promote to rule if this pattern recurs in another hook.

## Verification
- `python3.11 -m py_compile hooks/hook-decompose-gate.py` → OK
- Render all 4 message kinds via `importlib.util` — confirm plain-English lead + single `[agent: ...]` trailing line, no `/tmp/` or JSON blob in the lead
- Live: the new gate message fired on this plan-file write; lead was plain-English, mechanic was in the trailing `[agent: ...]` line

## Rollback
Pure text change to one file. `git revert <commit>` restores prior messages.

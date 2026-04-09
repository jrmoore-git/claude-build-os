# Operating Reference

A quick-reference guide for day-to-day session management, planning discipline, and operational rules.

## Session Discipline

### Document First, Execute Second

Every correction, decision, or process change must be persisted to the correct document BEFORE implementation. If the session ends after documenting but before implementing, nothing is lost. Instructions given in chat but not written to docs get lost between sessions.

**The document is the deliverable.**

### What Goes Where

| Change type | Document |
|---|---|
| Bug, gotcha, platform surprise | `tasks/lessons.md` |
| How Claude Code should behave | `.claude/rules/*.md` |
| Build specs / PRD discrepancies | Build plan (flag to user if PRD) |
| Phase status | `tasks/handoff.md` |
| Decision with rationale | `tasks/decisions.md` |
| Session summary | `tasks/session-log.md` |

### Session Close Protocol

When context reaches ~60%, write to `tasks/session-log.md` FIRST:
- Decided: [bullets]
- Documented: [file + what changed]
- Implemented: [bullets]
- NOT Finished: [what remains, blockers]
- Next Session Should: [first thing to do, files to read]

Priority when context is low: 1. Session summary -> 2. Phase review -> 3. Implementation

## Plan Mode

Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions). If something goes sideways, STOP and re-plan immediately. Decompose work into focused tracks -- context window limits kill long sessions.

### When to Enter Plan Mode

- Task touches >3 files
- Task affects state or security
- Task adds a new integration
- Task involves architectural decisions

### When to Skip Plan Mode

- One-line fixes
- Copy edits
- Obvious single-file changes

## Context Budget

- Use `/compact` at 50% context usage -- don't wait for automatic compression
- At 60% context: STOP and run review if not done
- At 75% context: run review NOW
- Every LLM call must log the actual model that responded, not the model that was requested (fallback detection)

### Large-Task Execution

The context window is expensive RAM; the filesystem is free storage. For complex multi-track work:
- Write the plan to disk and execute against the file, not the conversation
- Write plans, reviews, and state to files -- read selectively
- Process items in batches to avoid quadratic context growth
- Anti-pattern: loading 312K tokens "just in case" when 50K suffices

## Fix-Forward Rule

When a command fails due to missing environment variables, bad paths, stale config, or other infrastructure issues:

1. **Diagnose root cause** -- don't just retry with an inline workaround
2. **Apply a permanent fix** -- update the script, config, or shell profile so the error cannot recur next session
3. **Log to lessons.md** if the fix reveals a pattern others should know

If a permanent fix is not feasible within the current task scope, apply the workaround AND log the root cause to `tasks/lessons.md` so the next session fixes it. Never silently work around the same infrastructure failure twice.

## Root Cause First -- No Bandaids

When a data quality or behavior problem is reported:

1. **STOP. Do not touch the data.** No UPDATE statements. No backfill scripts. No row-level fixes.
2. **Trace the insertion path.** Read the code that creates/stores the data. Identify exactly why the wrong value is produced.
3. **Fix the insertion path.** The fix goes in the code that creates data -- the skill, the toolbelt, the gate. Not downstream.
4. **Verify on NEW data.** Run the extraction on a real example. Confirm the structural fix produces correct output.
5. **Only THEN backfill** existing data as a one-time cleanup, using the same code path -- not a separate script.

**The test:** "If I delete this patch, will the problem recur for new data?" If yes, you haven't fixed anything -- you've created maintenance debt.

**Banned anti-patterns:**
- Writing UPDATE/backfill SQL before reading the insertion code
- Adding UI-side filtering to hide bad data instead of fixing the source
- Writing a "backfill script" as the primary deliverable
- Fixing N rows manually when the Nth+1 row will have the same problem

## Verification

- Never mark a task complete without proving it works
- Run tests, check logs, demonstrate correctness
- Ask: "Would a staff engineer approve this?"
- Sanity-check data volumes, not just success codes -- a pipeline can return valid JSON with no errors and still be wrong

## Three-Strikes Escalation

If the same behavior has been corrected three times at the same level, escalate immediately.

**Promotion ladder:** lesson -> rule -> hook -> architecture

Do not keep rewriting advisory text for a behavior that needs structural enforcement.

## Shipping Discipline

**Priority stack:** broken > product > reliable > secure > elegant

**Remediation order:** broken now -> breaks when enabled -> breaks on reboot -> security controls -> everything else (by user value, not architectural purity)

## Commit Doc Update Rule

Every commit must include updates to ALL relevant tracking docs. Before committing, check:

- **tasks/decisions.md**: Any new decision? Add numbered entry with rationale.
- **tasks/session-log.md**: Focus, result, decisions, next steps, commit hash.
- **tasks/lessons.md**: Any surprise or gotcha? Add numbered entry.
- **PRD**: Any scope/integration/schedule change? Update the relevant section.

If none apply, state "No doc updates needed" in the commit message.

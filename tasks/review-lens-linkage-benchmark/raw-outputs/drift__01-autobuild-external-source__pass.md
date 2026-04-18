---
debate_id: drift__01-autobuild-external-source__pass
created: 2026-04-18T13:20:41-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# drift__01-autobuild-external-source__pass — Challenger Reviews

## Challenger A (pm) — Challenges
### PM/Acceptance Review

**Negative Compliance (MUST NOT, EXCEPTION, EXPLICITLY EXCLUDED)**
Extracted clauses from the spec:
1. **EXPLICITLY EXCLUDED:** Parallel execution across worktrees is explicitly out of scope for this version.
2. **MUST NOT:** Autobuild must not silently expand file scope during iteration, even when a fix appears obvious.
3. **MUST NOT:** Do not add a new skill, new scripts, or new hooks.
4. **MUST NOT:** Do not attempt parallel agent orchestration.
5. **MUST NOT:** Do not auto-merge or auto-ship.

*Status:* The diff successfully avoids all forbidden behaviors. It explicitly requires sequential execution, bounds edits to `surfaces_affected`, avoids adding new files, and states that merge/ship remains human-approved.

**Positive Compliance (Completeness and Scope)**

* **[MATERIAL] Missing Spec Requirement - Decision Classification:** The spec explicitly requires autobuild to "Classify decisions during build" by reusing `/plan --auto`'s 3-tier classification (Mechanical, Taste, User Challenge). The diff completely omits instructions for the agent to classify decisions during the build phase, which risks the agent silently making architectural or user-challenge decisions without escalation.
* **[MATERIAL] Missing Spec Requirement - Self-Learning Context:** The spec requires that "The build phase reads `tasks/lessons.md` for the relevant domain before implementation." This critical instruction is missing from the diff, breaking the only learning mechanism specified for the build phase.
* **[ADVISORY] Escalation Protocol Coverage:** The diff calls out escalation triggers #4 and #5, but the spec states "The 7 escalation triggers in `workflow.md` remain active throughout the build phase." While implied, explicitly instructing the agent to keep all 7 triggers active would reduce the risk of the agent ignoring the other 5 during a long build loop.

**Value & Scope Sizing**
* **[ADVISORY] Scope containment friction:** Bounding edits strictly to `surfaces_affected` under trigger #4 is correctly implemented per spec, but carries high adoption friction. If a developer runs an autobuild that legitimately needs to update a localized snapshot test not listed in the plan, it will pause. The strictness is correct per spec, but we should monitor if this creates too many low-value interruptions in practice.

---

---
debate_id: new_defect__01-autobuild-hardcoded-3strike__pass
created: 2026-04-18T13:21:22-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# new_defect__01-autobuild-hardcoded-3strike__pass — Challenger Reviews

## Challenger A (pm) — Challenges
### Spec Compliance: Exclusions & Constraints

**Extracted Clauses:**
- **MUST NOT:** "The system should not continue to the next step on a failing step." (Diff complies: specifies pausing under trigger #5 after retry limit).
- **MUST NOT:** "It does not authorize the agent to reinterpret the task when the task itself becomes unclear." (Diff omits mention of this constraint and related escalation triggers).
- **EXPLICITLY EXCLUDED:** "Rely on existing infrastructure rather than adding new runtime components... No new scripts or hooks required." (Diff violates by introducing `config/autobuild.json`).
- **MUST NOT:** "Autobuild stops without review handoff if verification cannot be restored within the allowed retry limit or if execution leaves the approved scope without human approval." (Diff complies).

---

### PM / Acceptance

- **[MATERIAL] SPEC VIOLATION: Scope Creep via New Configuration**
  The spec explicitly mandates relying on existing infrastructure with "no new scripts or hooks required" and right-sizes the effort to just editing `plan/SKILL.md`. The diff introduces a new `config/autobuild.json` file to manage heuristics (verified absent from the current `config/` manifest). This is textbook over-engineering that introduces adoption friction by requiring users to manage new config files for standard pipeline execution. 

- **[MATERIAL] SPEC VIOLATION: Ignored Context Mitigation**
  The spec provides a specific mitigation for token cost and context limits: "clear the conversational context buffer after plan approval and carry forward only the approved plan artifact..." The diff completely ignores this mechanism and instead invents a new `context_exhausted` halt state tied to a `context_soft_limit_tokens` heuristic. This fails to implement the required positive compliance and introduces an unnecessary failure state for the user.

- **[MATERIAL] Incomplete Escalation Implementation**
  The spec requires that "The 7 escalation triggers in `workflow.md` remain in force throughout autobuild" and specifically mandates in the implementation section to "apply all 7 existing escalation triggers during build, not just repeated failures." The diff only explicitly mentions trigger #5 (failures) and trigger #4 (scope). It fails to instruct the agent on the other five triggers (ambiguity, architecture, security, side effects, constraints), risking autonomous drift.

### Architecture

- **[ADVISORY] Incomplete State Handoff**
  The diff instructs the agent to "call `/review`, then generate the `/ship` Step 6 summary." It fails to mention loading `tasks/lessons.md` at the start of the build phase, which the spec explicitly required as the mechanism for context and learning ("the build phase reads `tasks/lessons.md` for the relevant domain before implementing").

### Security

- **[ADVISORY] Missing Security Escalation Trigger**
  By omitting the explicit requirement to enforce all 7 escalation triggers, the diff drops the specific instruction to halt on security-sensitive changes during autonomous execution. While scope containment (trigger #4) is present, the agent needs explicit reminders of the security boundary when operating without step-by-step human oversight.

---

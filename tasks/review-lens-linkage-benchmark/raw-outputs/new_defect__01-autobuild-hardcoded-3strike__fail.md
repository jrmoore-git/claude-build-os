---
debate_id: new_defect__01-autobuild-hardcoded-3strike__fail
created: 2026-04-18T13:21:06-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# new_defect__01-autobuild-hardcoded-3strike__fail — Challenger Reviews

## Challenger A (pm) — Challenges
### PM/Acceptance

**[MATERIAL] SPEC VIOLATION: Incomplete Escalation & Decision Implementation**
The refined spec explicitly requires:
- *"Mandatory stop conditions: The agent must stop and ask the human whenever an escalation trigger fires or a user-challenge decision appears."*
- *"apply all 7 existing escalation triggers during build, not just repeated failures."*
- *"Reuse the existing decision classification... Mechanical, Taste, User Challenge."*

The diff only implements triggers #4 (scope) and #5 (retries) and completely omits the decision classification (Mechanical/Taste/User Challenge) and the other 5 escalation triggers. It fails to implement the required negative compliance (stopping for user challenges).

**[MATERIAL] SPEC VIOLATION: Context Management Mechanism**
The spec identifies context limits as a risk and prescribes a specific mitigation: *"clear the conversational context buffer after plan approval and carry forward only the approved plan artifact..."*
The diff ignores this mitigation entirely and instead introduces a hard halt: *"When the session's context hits 120000 tokens... Immediately halt with status `context_exhausted`."* This leaves the root problem unfixed (context bloat will still happen) and introduces a brittle failure mode not authorized by the spec.

**[MATERIAL] False Quantitative Claim**
The diff claims: *"CONTEXT_HARD_LIMIT = 120000 # tokens; above this no model can continue"*. This is a **[SPECULATIVE]** claim that contradicts both the spec and reality (modern models routinely support 200k+ tokens). By enforcing this artificial limit without evidence, the implementation introduces unnecessary adoption friction and workflow failures. 

**[ADVISORY] Incorrect File Path**
The diff targets `.claude/skills/plan/SKILL.md`. The repository manifest confirms the skills are located at `skills/<name>` (e.g., `skills/plan`), not in `.claude/skills/` with a `.md` extension.

### Architecture

**[MATERIAL] Incomplete Entry and Handoff Conditions**
The spec requires explicit entry and handoff conditions:
- *"Autobuild starts only after `/plan --auto` completes and the human explicitly approves the generated plan."*
- *"Autobuild completes only when... `/review` runs, and the ship summary is generated."* (The diff mentions calling `/review`, but doesn't define the entry condition or input dependencies like `tasks/lessons.md`).

By omitting the input dependencies (`tasks/lessons.md`), the implementation fails to meet the Architecture requirement for "Context & Learning" specified in the proposal.

---

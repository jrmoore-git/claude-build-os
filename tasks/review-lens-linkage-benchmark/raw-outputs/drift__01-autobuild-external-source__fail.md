---
debate_id: drift__01-autobuild-external-source__fail
created: 2026-04-18T13:20:44-0700
mapping:
  A: gemini-3.1-pro
personas:
  A: pm
---
# drift__01-autobuild-external-source__fail — Challenger Reviews

## Challenger A (pm) — Challenges
### PM/Acceptance Review

**Spec Clauses Extraction & Compliance Check:**
- **EXPLICITLY EXCLUDED**: "Parallel execution across worktrees is explicitly out of scope for this version." (Diff complies: "No parallel agents.")
- **MUST NOT**: "Autobuild must not silently expand file scope during iteration, even when a fix appears obvious." ([MATERIAL] SPEC VIOLATION: The diff completely omits this critical constraint and the associated escalation trigger #4 instruction).
- **DO NOT**: "Do not add a new skill, new scripts, or new hooks." (Diff complies).
- **DO NOT**: "Do not attempt parallel agent orchestration." (Diff complies).
- **DO NOT**: "Do not auto-merge or auto-ship." (Diff complies).
- **REJECTED INFRASTRUCTURE**: "resisting the urge to build heavy new infrastructure (like gstack's JSONL store)" ([MATERIAL] SPEC VIOLATION: The diff explicitly instructs the agent to log to `stores/cloudzero-gap-events.jsonl` and defines a JSON schema for it, directly violating the refine phase's rejection of this infrastructure).

#### PM/Acceptance Findings

**[MATERIAL] SPEC VIOLATION: Scope Creep & Hallucinated Infrastructure**
The diff mandates logging telemetry to `stores/cloudzero-gap-events.jsonl` and defines a "CloudZero Telemetry Schema". This is a direct violation of the spec, which explicitly praised the proposal for "resisting the urge to build heavy new infrastructure (like gstack's JSONL store)" and noted that the CloudZero reference was merely external framing. Baking this into the prompt distracts the agent from its primary job (building code) and wastes tokens on dead-end telemetry [SPECULATIVE: assuming token waste based on schema size, needs measurement].

**[MATERIAL] SPEC VIOLATION: Missing Scope Containment**
The spec requires that `surfaces_affected` be treated as a hard boundary and any edits outside it must trigger escalation #4. The diff fails to include this instruction, which opens the door for runaway agent edits during the iteration phase. 

**[MATERIAL] Missing Pre-requisite Check**
The spec requires that the agent must stop and not enter build mode if the plan is missing explicit build steps, `surfaces_affected`, or `verification_commands`. The diff says "Parse the plan" but fails to instruct the agent to halt if these elements are missing.

**[ADVISORY] Risk Assessment (Both Directions)**
- **Risk of the proposed change:** By including the CloudZero JSONL telemetry instructions, we risk the agent prioritizing logging over actual code generation, or failing because the `stores/` directory or file structure isn't set up as expected. Furthermore, missing the scope containment boundary risks the agent silently editing unrelated files during failed test loops.
- **Risk of NOT changing:** If we reject autobuild entirely, the operator remains stuck manually executing build steps, copying test outputs back into the chat, and babysitting the loop—which is the highest friction point currently in the Build OS workflow. We need this feature, but without the telemetry cruft and with the required safety boundaries.

---

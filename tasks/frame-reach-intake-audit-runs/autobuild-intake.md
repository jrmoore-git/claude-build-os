---
debate_id: autobuild-intake
created: 2026-04-17T16:16:56-0700
mapping:
  A: claude-sonnet-4-6
  B: gpt-5.4
personas:
  A: frame-structural
  B: frame-factual
---
# autobuild-intake — Challenger Reviews

## Challenger A (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL] [COST:MEDIUM]:** The proposal treats "add ~60-80 lines to plan/SKILL.md" as the full implementation scope, but the actual complexity lives in the runtime behavior, not the skill description. The skill file describes *what to do*; the agent executing it must parse plan artifacts, track per-step state across tool calls, manage the 3-attempt counter per step, conditionally spawn worktree agents, and invoke `/review` — all without a coordinator script. This is a behavioral specification gap, not a documentation gap. The 60-80 line estimate is SPECULATIVE and likely understates the real surface by an order of magnitude once you account for the state machine that needs to exist somewhere.

2. **ALTERNATIVE [MATERIAL] [COST:SMALL]:** The proposal frames the choice as "manual build" vs. "full autobuild loop." A missing middle candidate is **semi-autonomous build with explicit checkpoints**: the agent implements one plan step, runs its verification command, reports pass/fail, and waits for a lightweight human acknowledgment ("continue / fix / abort") before the next step. This captures most of the value (no manual implementation, no manual test-running) while dramatically reducing the risk of a multi-step failure cascade. The proposal's own "Why Not" section acknowledges that iteration quality degrades and that plans may miss context — a step-gated variant directly addresses both without requiring the full escalation-protocol machinery to work reliably in autonomous mode.

3. **ASSUMPTION [MATERIAL] [COST:LARGE]:** The proposal assumes the existing escalation protocol (7 triggers in workflow.md) is sufficient to catch the judgment calls that arise during implementation. But escalation triggers are defined for *planning* contexts where the agent is reasoning about what to do. During *implementation*, the agent is in a tool-use loop (Edit/Write/Bash) where it may not surface ambiguity as a natural pause point — it may just make a choice and continue. There is no existing mechanism that forces the agent to re-evaluate escalation criteria mid-tool-loop. This is an unstated load-bearing assumption: that a skill description saying "apply escalation triggers" translates into reliable mid-build pauses.

4. **ASSUMPTION [ADVISORY]:** The proposal cites the CloudZero velocity analysis (Appendix C, Gap #2) and gstack's roadmap as external validation. These are treated as independent corroboration, but the proposal text provides no access to these sources — they may be internal documents that share the same author's framing. The "both frameworks identify this as the key missing capability" claim is SPECULATIVE as evidence basis. This doesn't change the recommendation but inflates the "Why Now" section's persuasive weight.

5. **OVER-ENGINEERED [ADVISORY]:** The proposal pre-wires parallel agent spawning via worktree isolation for "parallel tracks identified by the decompose gate." This is a Phase 2 capability being specified before the single-agent sequential path has been validated. The decompose gate exists for human-initiated parallel work; whether it correctly identifies parallelizable tracks in an autonomous build context is unverified. Parallel agent coordination is the highest-risk element of the design and should be explicitly deferred, not included in the initial scope.

6. **ALTERNATIVE [ADVISORY]:** The proposal doesn't consider **build-only mode without the iterate loop** as a candidate: the agent implements all steps once, runs the full test suite, and stops — reporting results to the human rather than attempting autonomous repair. This is strictly simpler, eliminates the "attempt 3 is often flailing" problem the proposal itself names, and still eliminates the largest manual burden (writing the code). The human handles failures, which is already their current role. This variant is absent from the candidate set despite being a natural decomposition.

---

## Concessions

1. The proposal correctly identifies that all surrounding infrastructure (plan artifacts, escalation protocol, decompose gate, `/review`, `/ship`) already exists, making the integration surface real rather than speculative.
2. The self-learning dependency analysis is honest: it correctly argues that `tasks/lessons.md` may be sufficient for a solo-dev context and explicitly defers structured learning investment to when evidence demands it.
3. The approval gate preservation is the right instinct — keeping the human in the loop at plan approval before autonomous execution begins is a meaningful risk control.

---

## Verdict

**REVISE** — The candidate set is missing the step-gated and build-without-iterate variants, and the proposal's central implementation claim (60-80 lines, no new scripts) rests on an unverified assumption that a skill description can reliably drive a stateful multi-step autonomous loop without a coordinator. The frame should be redrawn around "what is the minimal autonomous build that delivers value while the iteration/escalation machinery is validated" before committing to the full loop.

---

## Challenger B (frame-factual) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal says “the full post-build pipeline (`/review` → `/ship`)” already exists, but the repo evidence only shows a review stage in the plan/progress pipeline, not a shipped `/ship` stage or “new Step 6 in `/ship`.” `scripts/verify-plan-progress.py` enumerates pipeline artifacts only through `review` (`design`, `think`, `elevate`, `challenge`, `plan`, `review`) with no `ship` artifact stage, and the exported functions / files manifest contains no `ship` script or hook implementation. This makes the “auto-invoke ... ship-summary” part of the recommendation rely on an unverified/likely absent surface.  
2. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The proposal claims “decompose gate behavior” provides parallel agent spawning, but the actual hook is advisory-only. `hooks/hook-decompose-gate.py` explicitly says it “nudges” toward worktree fan-out, “Advisory, not blocking,” and “the agent receives the nudge and decides.” So using it as if it already supplies deterministic parallel build orchestration overstates current capability.  
3. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal says “scope containment” can be enforced with “No new hook needed — the escalation protocol covers it,” but the current hooks do not enforce plan-declared `surfaces_affected` during edits. `hook-pre-edit-gate.sh` blocks protected-file edits without a recent plan/proposal, and `hook-post-build-review.py` only counts edits to trigger review reminders after 10 edits; neither checks whether edited files are inside a plan’s allowed file list. So the key containment guarantee in the proposal is not implemented today.  
4. [UNDER-ENGINEERED] [MATERIAL] [COST:MEDIUM]: “Add ~60–80 lines to plan/SKILL.md, no new scripts” is too small for the behaviors promised. The proposed mode requires parsing plan artifacts, tracking per-step attempts, deciding when to stop after failed verification, possibly dispatching isolated agents, and auto-invoking downstream review. The repo’s deterministic behavior for these kinds of checks today lives in code/hooks (`verify-plan-progress.py`, `hook-post-build-review.py`, `hook-agent-isolation.py`), not just prose. Encoding autobuild solely in SKILL instructions would leave the most important guarantees non-deterministic and unenforced.  
5. [ALTERNATIVE] [ADVISORY]: The proposal overlooks existing code that could reduce implementation risk: `scripts/verify-plan-progress.py` already parses plan-related artifacts and session state, and `hooks/hook-post-build-review.py` already maintains session-scoped state around active plans and edit counts. If autobuild proceeds, anchoring it in one small script that reuses these patterns is more realistic than treating the feature as pure skill text.  
6. [ASSUMPTION] [ADVISORY]: The motivation leans on external claims (“neither framework has solved it,” “planned `/autoship` in v0.17”) that are not verifiable from this repo and therefore should not drive the recommendation. By contrast, repo-local evidence already shows recent autonomous-build adjacent work (`6a3fb0b` added the structural post-build review gate), which weakens the premise that the area is untouched.

## Concessions
- The proposal is right that substantial surrounding infrastructure already exists around planning, review, and agent isolation: `/plan --auto` is documented in `docs/changelog-april-2026.md`, and there are real hooks for decomposition and agent isolation.
- It is correct that there is a real build-phase governance gap between planning artifacts and implementation enforcement; current code has review nudges and commit/test gates, but not a deterministic build loop.
- Reusing existing infrastructure rather than introducing a large new subsystem is directionally sensible.

## Verdict
REVISE — the core idea is plausible, but the proposal overstates what the current repo already guarantees and underestimates how much deterministic code is needed beyond a small SKILL.md edit.

---

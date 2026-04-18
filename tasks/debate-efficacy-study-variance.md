---
debate_id: debate-efficacy-study-variance
created: 2026-04-17T13:33:02-0700
mapping:
  A: claude-opus-4-7
  B: gpt-5.4
  C: gemini-3.1-pro
  D: claude-sonnet-4-6
  E: gpt-5.4
personas:
  A: architect
  B: security
  C: pm
  D: frame-structural
  E: frame-factual
---
# debate-efficacy-study-variance — Challenger Reviews

## Challenger A (architect) — Challenges
I have enough to evaluate. Key findings:

- All claimed primitives exist: escalation protocol (7 triggers in workflow.md), `surfaces_affected` in plan frontmatter, decompose gate with worktree nudge, `--auto` on plan, 3-tier classification (Mechanical/Taste/User Challenge terms present).
- The hook-pre-edit-gate only checks for "recent plan artifact within 24h" — it does NOT enforce that edits stay inside `surfaces_affected`. The proposal's claim "Agent edits are checked against the plan's file list" is not backed by existing infrastructure.
- No existing hook cross-references edits to a plan's declared scope; scope policing is purely behavioral/advisory.
- No test-failure iteration loop exists anywhere in the codebase.

## Challenges

1. **ASSUMPTION** **MATERIAL** **[COST:SMALL]**: The proposal claims "Agent edits are checked against the plan's file list" and "no new hook needed." Verified: `hook-pre-edit-gate.sh` only checks for a recent plan/proposal artifact existing within 24h — it does not parse `surfaces_affected` and does not block edits outside declared scope. Decompose-gate is explicitly `advisory`, not enforcement. So scope containment during an autonomous loop is enforced only by the agent's own judgment — the exact component most likely to drift under iteration pressure. For a human-in-the-loop workflow that's fine; for an autonomous loop it's the critical gap. Fix is small (~40-80 lines extending pre-edit-gate to parse the active plan's `surfaces_affected` and block or warn on out-of-scope writes), but it is a real prerequisite, not "reuse existing infrastructure."

2. **UNDER-ENGINEERED** **MATERIAL** **[COST:MEDIUM]**: No iteration-loop primitive exists. Grep found zero "3-strike," "retry," or build-iterate logic in hooks or scripts. The proposal leans on "escalation trigger #5 (3 failures)" from workflow.md — but that's a prose instruction to a human-driven agent, not a mechanism. An autonomous loop needs: a per-step attempt counter persisted somewhere, a definition of "same problem" (identical failing test? identical diff? identical error signature?), and a stop-and-report path. None of this exists. Without it, "3 attempts" is aspirational — the loop will either give up too early on transient failures or flail indefinitely because the agent classifies each new attempt as a "different problem." This is not add-a-skill-section scope; it needs state and a signature function similar to `hook-error-tracker.py`'s `make_signature` (which already exists and could be reused — worth citing).

3. **OVER-ENGINEERED** **ADVISORY**: Putting autobuild as a `--build` flag inside `.claude/skills/plan/SKILL.md` conflates three very different concerns: planning (synthesis), approval gating (human), and execution (action). Every other skill in the repo is single-purpose (22 skills, each ~one verb). The existing pattern would be a separate `build` or `autobuild` skill invoked after `/plan --auto` approval, keeping plan/SKILL.md focused. "60-80 lines added to plan/SKILL.md" is a smell — the file will now describe both "how to produce a plan" and "how to execute arbitrary code and iterate on test failures," which are unrelated responsibilities.

4. **RISK** **MATERIAL** **[COST:SMALL]**: Token/context exhaustion is handwaved ("may hit context limits"). For a loop that reads the plan, edits N files, runs tests, reads failures, re-edits, re-runs — the window fills deterministically, not "maybe." There's no proposed budget check, no compaction strategy, no handoff-to-fresh-session mechanism. Cost of a check is trivial (sample input-token count, abort-with-checkpoint above threshold); cost of not having it is a half-built refactor with no clean resume point. ESTIMATED: a 3-step plan with 3 iterations/step and ~2KB plan + ~5KB diffs/turn plausibly hits 100K+ tokens before review runs; not EVIDENCED because no measurement is offered in the proposal.

5. **ALTERNATIVE** **ADVISORY**: The proposal dismisses structured learning as "not a prerequisite" and leans on unstructured `tasks/lessons.md` + domain filtering. But `scripts/lesson_events.py` with `log_event`, `compute_metrics`, `seed_from_lessons` already exists — there is structured lesson infrastructure in the repo. Reading `tasks/lessons.md` as a text blob when an events API exists is a wrong-abstraction choice. Worth at least citing why the prose file is the right input for the build loop specifically.

6. **RISK** **ADVISORY**: "Auto-invoke `/review` if tests pass" — tests passing is necessary but not sufficient. Existing `/review` skill and review-protocol.md are tiered; an autonomous loop that treats green CI as the approval signal will happily ship well-factored code that solves the wrong problem. The human-at-review-gate is load-bearing and should be spelled out as a hard stop, not "reviews the `/review` output."

## Concessions

1. Correctly identifies that the planning and post-build pipelines exist and the build phase is the actual gap — this is accurate; the repo has `/plan --auto`, `/review`, `/ship`, decompose-gate, and escalation protocol as claimed.
2. Right to dogfood on Build OS itself with human PR review as the safety net — low-blast-radius first venue.
3. Reusing the 3-tier decision classification (Mechanical/Taste/User Challenge terms are present in the skills corpus) is coherent with existing conventions rather than inventing new vocabulary.

## Verdict

**REVISE** — The gap is real and the reuse strategy is largely sound, but two MATERIAL gaps (scope-enforcement hook, iteration-loop state machine) are misrepresented as "already exists" when verification shows they don't; proposal should name them as prerequisites with their small-to-medium cost before shipping as a skill edit.

---

## Challenger B (security) — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:MEDIUM]: The proposal treats autonomous build execution as “just add instructions to `plan/SKILL.md`,” but the main trust boundary here is between a human-approved plan artifact and untrusted runtime outputs from tests, shell commands, repo contents, and external tools. There is no described enforcement for sanitizing or constraining execution of plan-derived `verification_commands`, step text, or tool output before feeding them back into the model loop. That creates real shell/prompt-injection risk during the build-test-iterate cycle, especially because the system would execute commands and then let model reasoning consume their output. “Existing escalation” is not a substitute for a command allowlist, repo-root confinement, output truncation/redaction, and explicit rules against following instructions found in test output.

2. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: Scope containment is asserted but not actually enforced for build execution. The proposal says edits outside `surfaces_affected` “trigger escalation” and “no new hook needed,” but the existing pre-edit gate only checks for the presence of a recent plan/proposal artifact on protected paths, not whether a write matches the approved plan scope (`hooks/hook-pre-edit-gate.sh`, lines 3-18). That means a lower-trust source — the autonomous builder reacting to failures — could expand writes beyond the human-approved file set before any reliable block occurs. If `--build` is added, plan-scope enforcement needs to be implemented as an actual gate, not a convention.

3. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal assumes existing agent isolation is sufficient for parallel build tracks, but the current isolation hook only enforces worktree isolation for write-capable agent dispatches when a “parallel plan” flag is active and warns about absolute repo paths in prompts (`hooks/hook-agent-isolation.py`, lines 4-15). It does not guarantee that the build instructions themselves won’t leak absolute paths, secrets, or full repo context into subagent prompts. For an autonomous build loop, prompt construction becomes a credential/exfiltration boundary; the design should specify what context is passed to subagents, how secrets are excluded, and how test/log outputs are scoped per worktree.

4. [RISK] [MATERIAL] [COST:SMALL]: “Zero-risk — the human reviews every PR” understates the risk of the proposed change and ignores pre-PR side effects. An autonomous build loop can still exfiltrate code or secrets to external providers before review, especially because this repo already includes outbound integrations for LLMs and research APIs (`scripts/llm_client.py` routes model calls through LiteLLM; `scripts/research.py` loads `PERPLEXITY_API_KEY` and performs external requests). Human PR review mitigates bad merges, not bad transmissions. The design needs an explicit policy for whether autobuild may call external services during build, what data can be sent, and whether secrets/env are stripped from subprocesses and prompts.

5. [UNDER-ENGINEERED] [ADVISORY]: The proposal says the 7 escalation triggers apply during build, but does not define how ambiguous security-sensitive cases will be detected mechanically. For autonomous execution, “security-sensitive changes” should be tied to concrete signals like touching auth, secrets, network egress, shelling out, or protected paths; otherwise the model is grading its own homework.

6. [ALTERNATIVE] [ADVISORY]: A safer rollout path would be a constrained “autobuild-light” mode first: single worktree only, no parallel agents, no networked research, repo-root-only verification commands, and mandatory dry-run review of planned shell commands before first execution. That would reduce the risk of the change while still addressing the “manual build loop” gap.

## Concessions
- It correctly identifies the risk of not changing: the manual build/test/iterate phase is still the biggest human-time sink between planning and review.
- Reusing the existing approval gate and review protocol is directionally sound; human approval before build and human review after build are good control points.
- The proposal is appropriately skeptical about autonomy quality degradation and calls out repeated-failure stopping conditions rather than claiming full reliability.

## Verdict
REVISE — the goal is valid, but autonomous build execution needs real enforcement around command execution, plan-scope writes, and outbound data handling before it is safe to ship as “just a skill-doc change.”

---

## Challenger C (pm) — Challenges
## Challenges

1. **[RISK] [MATERIAL] [COST:MEDIUM]**: Relying on prompt instructions to enforce scope boundaries is unsafe. The proposal claims "No new hook needed — the escalation protocol covers it" and expects the LLM to police its own edits against `surfaces_affected` during a long autonomous loop. LLMs frequently drift or rationalize scope expansion during implementation. If restricting edits to the approved plan is a hard requirement, it must be enforced by a runtime hook (e.g., in a pre-edit or pre-commit hook), not just skill prompt text.
2. **[ASSUMPTION] [MATERIAL] [COST:MEDIUM]**: The proposal assumes adding ~[SPECULATIVE] 60-80 lines of markdown to a skill file will reliably produce a robust build-test-iterate while-loop. Unbounded LLM loops are prone to getting stuck in failure cycles or hallucinating test successes. To enforce the "max 3 attempts per step" rule, you need state tracking (likely modifying `scripts/managed_agent.py` or adding a new tracking script), as relying on the LLM to count its own failures accurately over a long context window is an architectural anti-pattern.
3. **[OVER-ENGINEERED] [ADVISORY]**: Spawning worktree-isolated agents for parallel tracks during a standard `autobuild` introduces significant complexity (merge conflicts, state reconciliation) that most solo developers don't need for sequential feature implementation. 

## Concessions
1. Correctly identifies the largest friction point in the current workflow (the manual execution of approved plans).
2. Excellent reuse of the existing 3-tier decision classification framework to minimize unnecessary human interruptions.
3. Requiring an explicit approval gate *before* autonomous execution begins keeps the human safely in the loop for architectural decisions.

## Verdict
**REVISE**: The proposal solves a critical user problem but relies too heavily on prompt instructions to enforce scope bounds and loop termination; it requires actual system-level enforcement (scripts/hooks) to be reliable.

---

## Challenger D (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL] [COST:SMALL]:** The proposal assumes the plan artifact (`tasks/<topic>-plan.md`) is machine-parseable with sufficient fidelity to drive autonomous execution — that `build steps`, `file scopes`, and `verification_commands` are structured fields an agent can reliably extract and execute. The proposal text never verifies this. If the plan artifact is primarily prose (as most markdown plans are), the "read the plan" step is itself an LLM inference task with its own failure modes, not a deterministic parse. This assumption is load-bearing: the entire autobuild loop depends on it. The fix is either to verify the plan schema is structured enough, or to add a plan-normalization step before build begins.

2. **ASSUMPTION [MATERIAL] [COST:MEDIUM]:** The proposal treats the 7 escalation triggers as sufficient guardrails for autonomous build, but those triggers were designed for a human-in-the-loop session, not an autonomous loop. In a manual session, the human passively observes and can interrupt at any time. In autobuild, the agent runs until it hits a trigger — meaning the human only sees output at escalation points or completion. The proposal doesn't address: (a) how the human monitors a long-running build, (b) what happens if the agent makes a sequence of individually-below-threshold decisions that collectively constitute a bad architectural choice, or (c) whether the escalation triggers fire correctly when the agent is both the executor and the evaluator of "is this ambiguous?"

3. **ALTERNATIVE [MATERIAL] [COST:SMALL]:** The candidate set is binary: manual build (status quo) vs. full autobuild loop. A missing middle option is **step-confirm mode**: the agent implements one plan step, shows the diff and test result, waits for human approval, then proceeds to the next step. This captures most of the value (no manual implementation, no manual test-running) while keeping the human in the loop at each step boundary. It's strictly cheaper to build (no iteration logic, no escalation-during-build complexity), and it's a natural stepping stone. The proposal doesn't consider this option at all, jumping straight to the fully autonomous variant.

4. **ALTERNATIVE [ADVISORY] [COST:TRIVIAL]:** A dry-run or plan-execution-preview mode — where the agent shows what commands it *would* run and what files it *would* edit before doing anything — is absent from the candidate set. This would let the human validate the agent's interpretation of the plan before committing to execution, catching the "follows the plan literally but misses context" failure mode the proposal itself names in "Why Not" #1.

5. **OVER-ENGINEERED [ADVISORY] [COST:SMALL]:** The proposal pre-wires the self-learning dependency discussion (gstack's JSONL store vs. lessons.md) before there's any evidence autobuild produces recurring mistakes that need structured capture. The proposal correctly concludes "not a prerequisite," but the framing suggests this is a known gap to revisit. This is a Phase 2 concern being pre-loaded into a Phase 1 proposal — it adds scope anxiety without adding value.

6. **ASSUMPTION [ADVISORY] [COST:TRIVIAL]:** The "Why Now" rationale cites gstack's roadmap and the CloudZero velocity analysis as external validation. This is a source-driven framing pattern: the proposal inherits the framing that "autonomous build loop" is the right next step because two external sources say so, rather than from direct measurement of where human time is actually spent in this repo's workflow. The claim that "the gap between plan and code is where the most human time is spent" is SPECULATIVE — no data from this repo's telemetry is cited. The session telemetry infrastructure (`hook-session-telemetry.py`, `session_telemetry_query.py`) exists and could answer this question.

7. **RISK [MATERIAL] [COST:SMALL]:** The 3-attempt iteration limit per step is stated but the failure mode after limit exhaustion is underspecified. The proposal says "escalation protocol trigger #5" fires, but doesn't describe what state the repo is in at that point: are partial edits committed? Is the test suite in a broken state? Is the human handed a half-built feature with failing tests? The recovery path from mid-build escalation is a real operational concern that the proposal defers entirely.

---

## Concessions

1. The proposal correctly identifies that all surrounding infrastructure exists and autobuild is genuinely the missing link — this isn't premature abstraction, it's filling a real gap in an otherwise complete pipeline.
2. The implementation scope estimate (~60-80 lines to plan/SKILL.md, no new scripts or hooks) is appropriately minimal and the reasoning for reusing existing infrastructure is sound.
3. The "Why Not" section is unusually honest for a proposal — naming the judgment-quality degradation and context-limit risks directly rather than burying them.

---

## Verdict

**REVISE** — The proposal's frame is too binary. The missing step-confirm mode (implement one step → show diff+test → wait for approval → continue) is a cheaper, lower-risk candidate that captures most of the stated value and directly addresses the proposal's own "Why Not" concerns about judgment quality and mid-build escalation recovery. The current candidate set forces a choice between "fully manual" and "fully autonomous" when the real design space has a valuable middle option. Additionally, the plan-parseability assumption is load-bearing and unverified.

---

## Challenger E (frame-factual) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal says “all surrounding pieces exist” and that adding `--build` requires only ~60–80 lines in `plan/SKILL.md`, but the repo does not expose any plan/build skill files through the allowed source tree, while the existing implementation-heavy behaviors it wants to rely on live in Python hooks/scripts, not prompt text. Concretely, there is already real code for post-build review state tracking in `hooks/hook-post-build-review.py` (threshold/re-fire logic, active-plan detection, review freshness checks at lines 50–149) and managed multi-agent dispatch in `scripts/managed_agent.py` plus integration in `scripts/debate.py` (e.g. MA consolidation path at `scripts/debate.py:1478–1519`). That makes the “no new scripts, no new hooks” / “just add a skill section” premise unverified at best and likely understated: the proposed build loop includes step parsing, retry accounting, escalation state, and optional parallel fan-out, none of which is shown as existing executable orchestration in the verified code.

2. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The claim that parallel tracks can be handled by “spawn worktree-isolated agents” because this is “existing decompose gate behavior” overstates what exists. `hooks/hook-decompose-gate.py` is explicitly advisory only: it “nudges toward worktree fan-out,” “does not deny,” and “the agent receives the nudge and decides” (`hooks/hook-decompose-gate.py:4–18`). I did not find verified code here that actually spawns worktrees/agents from plan components. So using that as justification for autonomous parallel execution is a wrong premise.

3. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The proposal’s “No new hook needed — the escalation protocol covers it” ignores that scope containment against planned surfaces is not currently enforced by the cited mechanism. The only verified edit-safety hook here is `hooks/hook-read-before-edit.py`, which warns on protected paths/read-before-edit and explicitly exempts broad paths like `tasks/`, `docs/`, `tests/`, `config/`, `stores/` (`hooks/hook-read-before-edit.py:3–12`), while `hook-post-build-review.py` counts edits and nudges review after thresholds; neither checks edits against a plan’s `surfaces_affected`. So the proposal is missing real enforcement/work to support its stated scope-containment behavior.

4. [ASSUMPTION] [ADVISORY]: The motivation says the build gap is manual while surrounding phases are automated, but the repository already contains some implementation-phase automation beyond pure manual flow: `hooks/hook-post-build-review.py` tracks ongoing implementation activity against active plans and review freshness, and `scripts/verify-plan-progress.py` verifies plan progress/artifacts against memory and sessions. This does not invalidate autobuild as a direction, but it weakens the framing that “the build phase itself” is wholly uninstrumented/manual.

## Concessions
- The repo does support the proposal’s broader motivation that planning/review automation exists: `scripts/debate.py` is a large, active orchestration surface for challenge/judge/refine/review.
- The proposal is right that decompose-gate and post-build review infrastructure exist; it just overclaims what they already do.
- The proposal’s concern about iteration quality and context/cost is directionally reasonable, though no quantitative support is provided in the proposal text.

## Verdict
REVISE — the core idea is plausible, but the proposal materially overstates how much of the autonomous build loop already exists and understates the implementation work needed beyond prompt/skill text.

---

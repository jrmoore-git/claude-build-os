---
debate_id: autobuild
created: 2026-04-17T13:18:13-0700
mapping:
  A: claude-opus-4-7
  B: claude-sonnet-4-6
  C: claude-sonnet-4-6
  D: claude-sonnet-4-6
  E: claude-opus-4-7
personas:
  A: architect
  B: security
  C: pm
  D: frame-structural
  E: frame-factual
---
# autobuild — Challenger Reviews

## Challenger A (architect) — Challenges
Good — scope containment already exists in hook-pre-edit-gate.sh via `allowed_paths`. Now I have enough evidence.

## Challenges

1. **[ASSUMPTION] [MATERIAL] [COST:SMALL]:** The proposal claims "The plan artifact already declares `surfaces_affected`" and that scope escalation is handled by the existing escalation protocol with "no new hook needed." But the pre-edit-gate actually keys off `allowed_paths` in plan frontmatter (verified lines 52–54 of hook-pre-edit-gate.sh), not `surfaces_affected`. These may or may not be the same field. More importantly, the pre-edit-gate **degrades block to warning** when `scope_escalation: true` is set — a human-oriented affordance that an autonomous agent will gleefully exploit ("I'll just set scope_escalation and proceed"). Under autobuild, the soft-escalation path needs to be re-hardened to force a STOP, not a warning. This is a small but real change, not a pure reuse.

2. **[UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]:** "Max 3 attempts per step" is stated but there is no mechanism to enforce it across a long-running autonomous agent. The escalation protocol (verified in workflow.md line 36) is a *rule the model is supposed to follow*, not an enforced gate. `/plan --auto` is an interactive pipeline where the human is a natural checkpoint; autobuild removes that checkpoint. Without a counter persisted somewhere (session state, lesson_events, or a new hook), "trigger #5" is an honor-system limit. For an autonomous loop this is the single most important safety rail and it should be mechanically enforced, not prose-enforced.

3. **[RISK] [MATERIAL] [COST:SMALL]:** The "3-tier decision classification (Mechanical / Taste / User Challenge)" is cited as existing in `/plan --auto`. `check_code_presence` finds "Mechanical" (1 match) and "Taste" (2 matches) in skills, but "User Challenge" returns zero matches and "3-tier" returns zero. Either the classification is not as formalized as the proposal implies, or it lives under different naming. Under autobuild the taxonomy becomes load-bearing — every silent mechanical decision is now unreviewed code on disk. Before reusing this taxonomy in a higher-stakes context, its actual definition should be pinned down and, ideally, the "auto-decide silently" tier should be narrower than in planning (where wrong choices cost nothing until build time).

4. **[ALTERNATIVE] [MATERIAL] [COST:TRIVIAL]:** The proposal jumps straight to a `--build` flag on `/plan --auto`, coupling planning and building into one invocation. An alternative: a separate `/build` skill that consumes a committed plan artifact. Benefits: (a) the plan can be reviewed, edited, committed, then built in a fresh session with clean context (addressing the "context limits" Why-Not); (b) resumable — if build fails at step 4/7, re-invoking `/build` reads plan state and continues; (c) clearer failure attribution. The `--build` coupling makes the pipeline monolithic; an artifact-driven `/build` skill matches the existing pattern where skills consume artifacts from `tasks/`.

5. **[RISK] [ADVISORY]:** "Iteration quality degrades: attempt 1 informed, attempt 2 reasonable, attempt 3 flailing" is acknowledged in Why-Not but the proposal doesn't act on it. Attempt 3's flailing commits still get staged. The build phase should at minimum `git stash` or revert between failed attempts so attempt 3's debris doesn't contaminate the working tree the human reviews.

6. **[UNDER-ENGINEERED] [ADVISORY]:** Token/cost budget is named as a risk but there's no budget declared. `debate_common.py` has `_track_cost` / `get_session_costs` machinery (verified) — autobuild is the exact workload that should plug into it with a hard ceiling (e.g., "stop and escalate if session cost > $X"). TRIVIAL to wire in, and turns an SPECULATIVE cost concern into a bounded one.

7. **[ASSUMPTION] [ADVISORY]:** "~60-80 lines added to plan/SKILL.md" — ESTIMATED, not evidenced. The surrounding `--auto` logic plus the build loop plus iteration plus escalation wiring plus test invocation plus review handoff plus stop-enforcement is unlikely to fit in 80 lines of SKILL.md prose that an agent can reliably execute. The decompose-gate alone is a 100+ line hook. Autobuild-as-prose will drift; autobuild-as-script (even if called from SKILL.md) will not.

## Concessions

1. The core infrastructure claims check out: `--auto` exists in skills, `surfaces_affected`/`allowed_paths` and `verification_commands` exist, worktree isolation exists in hooks, escalation protocol is written down in workflow.md with the exact triggers referenced, `/ship` Step 6 exists.
2. The "build on Build OS itself first, human reviews every PR" risk-containment strategy is sound — dogfooding with a backstop is the right way to introduce this.
3. Identifying the plan→build gap as the correct next frontier is defensible: the surrounding pipeline automation is real, and this is the remaining manual stretch.

## Verdict

**REVISE** — the thesis and positioning are sound, but three material gaps (no mechanical enforcement of the 3-strike limit, ambiguous reuse of scope-containment that currently degrades to warnings, and an under-specified decision taxonomy becoming load-bearing) need explicit design before "add a section to SKILL.md" is adequate; all three fixes are SMALL or TRIVIAL, so this is a build-condition revision, not a rejection.

---

## Challenger B (security) — Challenges
## Challenges

1. **RISK [MATERIAL] [COST:SMALL]**: The proposal claims "No new hook needed — the escalation protocol covers [scope containment]." This is partially false. `hook-pre-edit-gate.sh` already checks `allowed_paths` in plan frontmatter (confirmed at line 52-54), but the proposal's `surfaces_affected` field is a *different* key — confirmed by `check_code_presence` showing `surfaces_affected` exists in skills/docs but `allowed_paths` exists only in docs. If the build phase relies on `surfaces_affected` for scope enforcement but the hook reads `allowed_paths`, the containment silently fails. The proposal needs to either (a) align field names, or (b) explicitly state that `surfaces_affected` maps to `allowed_paths` in the plan artifact schema.

2. **RISK [MATERIAL] [COST:SMALL]**: The proposal says parallel agents get "worktree isolation (existing decompose gate behavior)" but `hook-decompose-gate.py` is explicitly **advisory, not blocking** (confirmed: "Advisory, not blocking. Emits a prompt hint via `additionalContext`; does not deny"). `hook-agent-isolation.py` *is* blocking but only fires when `plan_submitted: true` is set in session state. The proposal doesn't specify that `--build` mode sets this flag. If it doesn't, parallel agents spawned during build have no enforcement-level isolation guarantee — only a nudge. For a mode designed to run autonomously, this is a meaningful gap.

3. **RISK [MATERIAL] [COST:MEDIUM]**: The proposal's decision classification (Mechanical/Taste/User Challenge) is confirmed to exist only in skills (2 matches for "Taste"), not in rules or docs. This means the classification logic lives in natural-language skill instructions, not in any enforced hook or code path. During autonomous build, the agent must self-classify every decision correctly — there's no mechanical backstop. The proposal treats this as solved infrastructure when it's actually a prompt-following behavior. A misclassification (treating a "User Challenge" as "Taste") during autonomous execution could silently make a behavior-affecting decision without escalation. The proposal should acknowledge this is a trust-in-model assumption, not an enforcement guarantee.

4. **ASSUMPTION [MATERIAL] [COST:SMALL]**: The proposal assumes `verification_commands` in the plan artifact are safe to execute autonomously. Confirmed present in skills/docs/rules. But there's no validation that these commands are bounded — a plan could contain `verification_commands` like `pytest && deploy.sh` or commands with side effects. The proposal says "Run verification commands from the plan" without any sandboxing, allowlist, or review of what those commands do. In a solo-dev context this is lower risk, but the proposal should explicitly state that `verification_commands` are human-authored at plan-approval time (which is true given the approval gate) and therefore trusted — this is an unstated premise that should be made explicit.

5. **RISK [ADVISORY]**: Token cost is listed under "Why Not" but not quantified. A full autobuild run (think → challenge → plan → build → test × N → iterate × 3 × N → review) on a non-trivial task could easily consume 200K-500K tokens. SPECULATIVE — no data in the proposal. The proposal acknowledges this but doesn't suggest any mitigation (context checkpointing, step-level context resets, cost gates). Given `_track_cost` and `_cost_delta_since` exist in `debate_common.py`, there's existing cost-tracking infrastructure that could be reused for a build-phase cost gate, but the proposal doesn't mention it.

6. **ASSUMPTION [ADVISORY]**: The proposal states "Building it on one repo (Build OS itself) is zero-risk — the human reviews every PR." This is only true if the ship step requires human approval before merge. The proposal says the human "Reviews the `/review` output and approves merge/ship" — but `/ship` with a summary auto-generation step could be invoked automatically after review. The proposal should clarify whether `--build` mode stops before `/ship` or includes it, since "auto-invoke `/review`" is stated but the ship step is ambiguous.

7. **UNDER-ENGINEERED [ADVISORY]**: The proposal doesn't address what happens to partial build state on escalation or failure. If the agent completes 4 of 6 build steps, hits escalation trigger #3 (ambiguous requirement), and pauses — the repo is in a partially-modified state. The human answers the question, but how does the agent resume? The plan artifact has no "current step" tracking. This isn't a blocker (the human can re-read the state), but it's a real operational gap for the "autonomous" claim.

8. **OVER-ENGINEERED [ADVISORY]**: The proposal adds `--build` as a flag on `/plan --auto` rather than as a separate skill. This keeps the implementation small (~60-80 lines in SKILL.md) but means the plan skill now has three modes (`/plan`, `/plan --auto`, `/plan --auto --build`) with significantly different behavior profiles. A separate `/build` skill invoked after plan approval would be cleaner separation of concerns and easier to test/iterate independently. The proposal acknowledges this tradeoff implicitly ("No new skill") but doesn't justify why co-location is better than separation.

---

## Concessions

1. **Infrastructure reuse is genuine.** The proposal correctly identifies that `hook-pre-edit-gate.sh` already does scope enforcement via `allowed_paths`, `hook-agent-isolation.py` handles parallel agent isolation, and the escalation protocol in `workflow.md` covers the 7 trigger cases. The "no new hooks" claim is mostly accurate — the gaps are alignment issues, not missing infrastructure.

2. **The approval gate is a real trust boundary.** The human approves the plan before build begins. This means `verification_commands`, `surfaces_affected`, and build steps are all human-reviewed before autonomous execution starts. This is a sound trust model for a solo-dev context and correctly identified.

3. **The self-learning dependency assessment is honest.** The proposal correctly argues that `tasks/lessons.md` + `/start` loading is "lighter than gstack's planned per-project JSONL learning store, but may be sufficient for a solo dev where the human is the learning system" — and correctly frames structured learning as signal-driven, not a prerequisite.

---

## Verdict

**REVISE** — Two material issues need resolution before implementation: (1) align `surfaces_affected` vs `allowed_paths` field naming so scope enforcement actually fires during build, and (2) explicitly specify that `--build` mode sets `plan_submitted: true` in session state to activate enforcement-level (not advisory) worktree isolation for parallel agents. Both are small fixes, not redesigns.

---

## Challenger C (pm) — Challenges
I now have enough verified data to render judgment. Here is the full review.

---

## Challenges

**1. ASSUMPTION [MATERIAL] [COST:SMALL]: The "CloudZero velocity analysis (Appendix C, Gap #2)" and "gstack roadmap (/autoship v0.17)" are cited as external validation but neither exists in the repository.**

A search across all docs finds zero matches for "CloudZero", "Appendix C", "Gap #2", "gstack", or "autoship". These are the proposal's two primary external justifications for *why now*. Without them, the "why now" section reduces to "the surrounding pieces exist" — which is a readiness argument, not a priority argument. The proposal should either cite real evidence or drop the external validation framing entirely. SPECULATIVE as a quantitative/priority claim.

**2. RISK [MATERIAL] [COST:MEDIUM]: The approval gate is the only human checkpoint before autonomous code editing begins, but the proposal doesn't specify what happens when the plan is ambiguous at implementation time — and plans routinely are.**

The escalation protocol (trigger #1: "two or more valid interpretations exist") is the stated safety net, but it fires *during* build, after edits have already started. The proposal says "no new hook needed — the escalation protocol covers it," but the escalation protocol is a rule-file instruction to the agent, not an enforced gate. `hook-pre-edit-gate.sh` and `hook-read-before-edit.py` exist but neither checks whether the current edit is within `surfaces_affected`. The scope-containment claim ("files not in surfaces_affected trigger escalation trigger #4") is a behavioral instruction with no enforcement mechanism. If the agent misses it, there is no backstop. This is the highest-risk gap in the proposal.

**3. RISK [MATERIAL] [COST:SMALL]: The "3 attempts per step" iteration limit is stated as a hard stop, but the proposal doesn't define what "step" means in a multi-component parallel build, nor what state is left behind when the limit fires.**

If a worktree agent hits 3 failures on step 2 of 5, the proposal says "escalation protocol trigger #5." But the worktree agent is isolated — it can't directly pause the orchestrating session. The reconciliation path (how the main session learns the sub-agent stopped, what partial state exists in the worktree, whether to abandon or merge) is unspecified. This is not covered by existing orchestration rules, which only address "after parallel agents complete" (the happy path).

**4. ASSUMPTION [MATERIAL] [COST:TRIVIAL]: The proposal claims `verification_commands` is a populated field in plan artifacts, but this is only verified to exist in 2 places in skills — not that it's reliably populated by `/plan --auto` in practice.**

If `verification_commands` is sparse or absent in real plan artifacts (which is plausible for plans generated before this field was standardized), the build phase has no test oracle and the "test after each step" behavior silently degrades to "run nothing." The proposal should either verify that `/plan --auto` reliably emits this field or specify a fallback (e.g., run `tests/run_all.sh`).

**5. RISK [ADVISORY]: The proposal's "Why Not" section acknowledges "attempt 3 is often flailing" but treats this as an acceptable known risk. For a solo-dev repo where the human reviews every PR, this is probably fine — but it should be stated as a design constraint, not just a caveat.**

The mitigation is the human review gate before merge. That's real. But the proposal should make explicit that autobuild is not a quality guarantee — it's a draft-generation accelerator. The `/review` step is the quality gate, not the build loop.

**6. ASSUMPTION [ADVISORY]: The proposal says "Building it on one repo (Build OS itself) is zero-risk — the human reviews every PR." This is true for correctness risk but understates the cost of a bad autobuild run.**

A flailing 3-attempt loop on a complex build step could consume significant context and produce a messy partial implementation that takes longer to clean up than doing it manually. The "zero-risk" framing is too strong. "Low blast radius" is more accurate.

**7. OVER-ENGINEERED [ADVISORY]: The parallel-agent path (spawning worktree-isolated agents for parallel tracks) is included in scope for a ~60-80 line SKILL.md addition.**

The decompose gate already handles nudging toward worktree fan-out. Adding explicit parallel-agent orchestration logic to the build phase is a meaningful complexity increase that the line-count estimate doesn't reflect. A simpler v1 could be sequential-only, with parallel builds as a follow-on once the sequential path is validated. The proposal doesn't name what concrete failures sequential-only would leave unfixed.

---

## Concessions

1. **The infrastructure readiness case is genuine.** `surfaces_affected`, `verification_commands`, the escalation protocol, worktree isolation, and `/review` all exist and are verified in the codebase. This is not a "build the foundation first" situation — the foundation is there.

2. **The scope estimate is honest about what it is.** "~60-80 lines added to plan/SKILL.md, no new scripts, no new hooks" is a credible lower bound for the sequential happy path. The proposal correctly identifies that complexity lives in the build phase itself, not in the scaffolding.

3. **The self-learning dependency is correctly scoped.** The proposal explicitly rejects gstack's JSONL learning store as a prerequisite and argues `tasks/lessons.md` is sufficient for a solo-dev context. That's a defensible call, and the reasoning is sound.

---

## Verdict

**REVISE** — The core idea is right and the infrastructure is ready, but two MATERIAL gaps need resolution before implementation: (1) the scope-containment claim needs an enforcement mechanism or an honest acknowledgment that it's advisory-only (the current framing implies a hard gate that doesn't exist), and (2) the parallel-agent failure path (worktree agent hits 3-strike limit mid-build) needs a specified reconciliation protocol or the parallel path should be explicitly deferred to v2. Both fixes are SMALL or TRIVIAL. The external citations (CloudZero, gstack) should be removed or replaced with real evidence — they're doing load-bearing work in the "why now" argument and they don't exist in the repo.

---

## Challenger D (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL] [COST:SMALL]:** The proposal assumes the plan artifact (`tasks/<topic>-plan.md`) is machine-parseable with sufficient fidelity to drive autonomous execution — that `build steps`, `surfaces_affected`, and `verification_commands` are structured fields an agent can reliably extract and act on. The proposal never verifies this. If the plan artifact is primarily prose (as most markdown plans are), the "read the plan" step is itself an LLM inference task with hallucination risk, not a deterministic parse. The entire autobuild reliability argument rests on this unstated premise. A hybrid candidate is missing: **structured plan schema first, autobuild second** — enforce a machine-readable plan format (YAML frontmatter with explicit `steps[]`, `verification_commands[]`, `surfaces_affected[]`) as a prerequisite, then autobuild becomes a thin executor rather than an interpreter.

2. **ALTERNATIVE [MATERIAL] [COST:SMALL]:** The candidate set is binary: manual build (status quo) vs. full autobuild loop. A missing middle candidate is **autobuild-dry-run / step-confirm mode**: the agent proposes each build step and waits for a single keypress before executing, with full test output shown inline. This captures most of the value (no context-switching, no manual test invocation) at a fraction of the risk (human stays in the loop per step). The proposal frames the choice as "manual everything" vs. "autonomous loop with escalation triggers," but the real space includes "human-paced automation" which is cheaper to build and safer to deploy first. The 60-80 line estimate likely applies to this variant too.

3. **ASSUMPTION [MATERIAL] [COST:MEDIUM]:** The proposal claims "no new hook needed — the escalation protocol covers it" for scope containment. But the escalation protocol is a set of rules in `workflow.md` — it only fires if the agent reads and applies it correctly during autonomous execution. The existing hooks (`hook-pre-edit-gate.sh`, `hook-read-before-edit.py`, `hook-decompose-gate.py`) enforce constraints mechanically. Scope containment during autobuild needs the same mechanical enforcement: a hook that checks edits against `surfaces_affected` before allowing them. Relying on the agent to self-escalate when it's also trying to complete the task is a conflict of interest. This is an UNDER-ENGINEERED gap, not a covered case.

4. **OVER-ENGINEERED [ADVISORY]:** The proposal pre-wires the full pipeline (build → test → iterate → review → ship-summary) before there's evidence that the build step alone works reliably. The review and ship-summary invocations are Phase 2 concerns. A sounder sequencing: ship autobuild-to-test-pass first, measure how often it reaches that gate cleanly, then add auto-review invocation. Chaining unproven steps multiplies failure modes and makes debugging harder.

5. **ASSUMPTION [ADVISORY]:** The "Why Now" section cites gstack's roadmap and the CloudZero velocity analysis as external validation. This is a source-driven framing pattern — the proposal is partly justified by what other frameworks are building, not by measured pain in this repo. The claim that "the gap between plan exists and code exists is where the most human time is spent" is SPECULATIVE (no data from this repo's telemetry, despite `scripts/session_telemetry_query.py` existing). The severity framing ("most human time") is unverified and may be inflating scope.

6. **RISK [ADVISORY]:** The 3-attempt iteration limit is presented as a safety valve, but the proposal doesn't address what happens to partial state after escalation. If attempt 2 partially modifies files and then escalates, the human inherits a half-edited codebase. The worktree isolation (decompose gate) handles parallel agents, but sequential build steps within a single worktree have no rollback mechanism described. This is a concrete failure mode the proposal leaves unaddressed.

---

## Concessions

1. The proposal correctly identifies that all surrounding infrastructure exists and autobuild is genuinely the missing link — this isn't premature abstraction, it's filling a real gap in an otherwise complete pipeline.
2. The decision classification reuse (mechanical/taste/user-challenge) is sound framing — it avoids reinventing an escalation taxonomy that already works.
3. The self-learning dependency analysis is honest: it correctly argues lessons.md may be sufficient and defers structured learning investment to evidence, rather than pre-building it.

---

## Verdict

**REVISE** — The candidate set is missing the step-confirm hybrid (full value, lower risk, same implementation cost) and the proposal's core reliability claim rests on an unverified assumption about plan artifact parseability that, if false, invalidates the "no new scripts" scope estimate. Fix the plan schema assumption and add the step-confirm variant as the recommended starting point before the full autonomous loop.

---

## Challenger E (frame-factual) — Challenges
I have enough verification. Now let me compile the findings.

## Challenges

1. **ASSUMPTION** [MATERIAL] [COST:SMALL]: The proposal asserts `/plan --auto` already has a **"3-tier classification (Mechanical / Taste / User Challenge)"** which autobuild will "reuse." Strings `Mechanical`, `Taste`, `User Challenge`, `3-tier classification`, `decision classification`, and `6 principles` all return `exists: false` across both `docs` and `rules`. This classification scheme is not documented anywhere verifiable — so either it's implemented only inside `.claude/skills/plan/SKILL.md` (which I cannot read from here, so the proposal should cite it concretely) or it doesn't exist and the proposal is inventing a prerequisite it claims to reuse. Either way, "reuse existing infrastructure" is unsupported until the cite is pinned down.

2. **ASSUMPTION** [MATERIAL] [COST:SMALL]: The proposal refers to a **"new Step 6 in `/ship`"** that generates spec-mapped ship summaries, and instructs autobuild to "invoke ship summary generation (new Step 6 in `/ship`)." Strings `ship summary`, `spec-mapped`, `Step 6` are absent from `docs`. The implementation plan depends on a downstream artifact that is itself not yet shipped (or not yet described in docs). This turns a "no new infrastructure" proposal into one that chains on an unbuilt feature.

3. **ASSUMPTION** [MATERIAL] [COST:SMALL]: The proposal cites **"CloudZero velocity analysis (Appendix C, Gap #2)"** and **"gstack's roadmap (planned `/autoship` in v0.17)"** as external motivation. Strings `CloudZero`, `CloudZero velocity`, `Appendix C`, `Gap #2`, `gstack`, `autoship`, `Autonomous execution loop` all return `exists: false` in `docs`. These citations cannot be audited in this repo, so the "why now" section rests entirely on unverifiable references. The judge should not weight the external-pressure argument.

4. **UNDER-ENGINEERED** [MATERIAL] [COST:MEDIUM]: The proposal says "No new hook needed — the escalation protocol covers it" for scope containment, relying on `surfaces_affected` enforcement via trigger #4. But `hook-plan-gate.sh` enforces plan presence at **commit time**, not at Edit/Write time — its logic branches on `git commit*` (line 29). For an autonomous agent iterating through Edit/Write tool calls mid-build, nothing mechanically blocks edits outside `surfaces_affected` until the agent tries to commit. The escalation protocol is a *prompt rule* the agent may silently ignore when it has no stop signal. A `--build` mode with no real-time scope enforcement is exactly where an autonomous loop goes wrong. This is a genuine gap the proposal waves away.

5. **UNDER-ENGINEERED** [ADVISORY]: Iteration quality / token cost risks in "Why Not" are named but no limit is set. Escalation trigger #5 is "3 attempts on the same problem" (workflow.md line 36), which caps per-step retry but not the overall build-step count or cumulative token budget. A 15-step plan × 3 attempts each = 45 agentic turns with no budget gate. Since `debate_common.py` has `_track_cost` / `_track_tool_loop_cost`, a cost ceiling on autobuild runs is cheap to add and the proposal omits it.

6. **ASSUMPTION** [ADVISORY]: Proposal claims `/start` "already loads lessons at session start." `lessons.md` references exist in workflow.md line 7 as an orientation requirement, but I can't confirm `/start` skill behavior from the allowed directories. Minor — but if autobuild is supposed to read `tasks/lessons.md` "for the relevant domain," the proposal should specify how domain matching works (keyword? tier? manual tag?), not just assert it.

## Concessions

- The escalation protocol with 7 triggers is real and correctly described (workflow.md lines 28–40, including trigger #5 = three-failures rule).
- `surfaces_affected` and `verification_commands` are real plan artifact fields (`check_code_presence` confirms each appears once in rules).
- Targeting the change as an additive section in `plan/SKILL.md` with no new scripts/hooks is consistent with the codebase's "skills-first, minimal infra" pattern.

## Verdict

**REVISE** — The core idea is sound and aligned with the repo's skills-first style, but three load-bearing claims (3-tier decision classification, `/ship` Step 6 spec-mapped summaries, CloudZero/gstack citations) are unverifiable in the repo, and the "no new hook needed" argument misreads `hook-plan-gate.sh` as enforcing scope at edit time when it only fires at commit time. Pin the prerequisite cites to actual file+line or stage them as dependencies, and address real-time scope containment before treating this as purely documentation work.

---

## PROPOSAL

```
---
title: "Autobuild Mode: Autonomous Build-Test-Iterate Loop"
type: proposal
status: draft
date: 2026-04-16
---

# Proposal: Autobuild Mode for Build OS

## Problem

Build OS automates the full planning pipeline (`/plan --auto`: think → challenge → plan) and the full post-build pipeline (`/review` → `/ship`). But the build phase itself — implementing the plan, running tests, iterating on failures — is manual. The human reads the plan, builds step by step, runs tests, fixes failures, and then invokes review.

This is the same gap identified in the CloudZero velocity analysis (Appendix C, Gap #2: "Autonomous execution loop") and in gstack's roadmap (planned `/autoship` in v0.17, not yet built). Neither framework has solved it.

## What We'd Build

A `--build` flag on `/plan --auto` that continues execution after the plan approval gate. The full pipeline becomes:

```
/plan --auto --build <task description>
```

Pipeline: think → challenge → plan → **[approval gate]** → build → test → iterate → review → ship-summary

### Build Phase Behavior

1. **Read the plan.** Parse `tasks/<topic>-plan.md` for build steps, file scopes, and verification commands.
2. **Implement sequentially.** Execute each build step from the plan. For parallel tracks (identified by the decompose gate), spawn worktree-isolated agents.
3. **Test after each step.** Run verification commands from the plan. If tests fail, iterate (max 3 attempts per step — escalation protocol trigger #5).
4. **Escalation during build.** The 7 escalation triggers in workflow.md apply throughout. Ambiguous requirements, architectural decisions outside the plan, security-sensitive changes, scope growth, repeated failures, irreversible side effects, contradictory constraints — all pause and ask.
5. **Decision classification during build.** Reuse `/plan --auto`'s 3-tier classification:
   - **Mechanical:** One clearly right answer (import paths, variable names, boilerplate). Auto-decide silently.
   - **Taste:** Reasonable alternatives exist (error message wording, naming conventions). Auto-decide with the 6 principles, log the choice.
   - **User Challenge:** Both interpretations are defensible and affect behavior. STOP and ask.
6. **After all steps complete:** Run full test suite. If passing, auto-invoke `/review`. Generate ship summary per the new Step 6 in `/ship`.

### What the Human Does

- Writes the task description (one sentence to one paragraph)
- Approves the plan at the approval gate (existing `/plan --auto` behavior)
- Answers escalation questions if they arise during build
- Reviews the `/review` output and approves merge/ship

### Self-Learning Dependency

gstack's design doc argues autobuild depends on self-learning infrastructure ("without memory it repeats the same mistakes"). For Build OS:

- `tasks/lessons.md` already captures gotchas and patterns
- `/start` already loads lessons at session start
- The build phase should read `tasks/lessons.md` for the relevant domain before implementing

This is lighter than gstack's planned per-project JSONL learning store, but may be sufficient for a solo dev where the human is the learning system. If autobuild produces recurring mistakes that lessons.md doesn't catch, that's signal to invest in structured learning — but not a prerequisite.

### Scope Containment

The plan artifact already declares `surfaces_affected` (file list). During build:
- Agent edits are checked against the plan's file list
- Files not in `surfaces_affected` trigger escalation trigger #4 (scope is growing)
- Parallel agents get worktree isolation (existing decompose gate behavior)

No new hook needed — the escalation protocol covers it.

## Why Now

1. All surrounding pieces exist: `/plan --auto`, escalation protocol, `/review`, `/ship` with spec-mapped summaries, decompose gate.
2. The gap between "plan exists" and "code exists" is where the most human time is spent.
3. Both gstack and the CloudZero analysis identify this as the key missing capability.
4. Building it on one repo (Build OS itself) is zero-risk — the human reviews every PR.

## Why Not

1. The build phase requires the most judgment. Plans are abstract; implementation is concrete. An agent that follows a plan literally may miss context the plan didn't capture.
2. Iteration quality degrades: attempt 1 is informed, attempt 2 is a reasonable fix, attempt 3 is often flailing. The 3-strike limit helps but doesn't guarantee quality.
3. Token cost: a full autobuild run (plan + build + test + iterate + review) could consume significant context. Long builds may hit context limits.
4. Scope creep risk: "just add --build" sounds simple, but the build phase is where most complexity lives.

## Implementation Approach

Add a `## --build Mode (Autonomous Build Pipeline)` section to `.claude/skills/plan/SKILL.md` after the existing `--auto` section. No new skill, no new scripts, no new hooks. Reuse existing infrastructure:

- Plan parsing: read the plan artifact's build steps and file scopes
- Implementation: standard Claude Code editing (Edit, Write, Bash)
- Testing: run plan's `verification_commands`
- Iteration: escalation protocol trigger #5 (3 failures = stop)
- Review: invoke `/review` skill
- Summary: invoke ship summary generation (new Step 6 in `/ship`)

Estimated scope: ~60-80 lines added to plan/SKILL.md.
```

---

## DECISION DRIVERS

**Outcome:** shelved. Evidence: no implementation commits after proposal date (searched `git log --all --grep autobuild`). Only session-wrap and frame-lens commits reference it.

### Decision drivers

**DD-1: The "escalation protocol with 7 numbered triggers" premise is false.**  
Proposal claims workflow.md has enumerated escalation triggers #1-#7 that would gate autonomous build. Source verification: `workflow.md` does have an "Escalation Protocol" section with 7 items, but they are prose rules for a human-supervised Claude session, not programmatic gates. No code path enforces "trigger #5 = 3 attempts then stop." *Evidence: read of `.claude/rules/workflow.md`.*

**DD-2: `surfaces_affected` / `allowed_paths` have only soft enforcement.**  
The proposal assumes scope containment via plan-frontmatter fields. Actual state: `hooks/hook-pre-edit-gate.sh` checks `allowed_paths` and degrades block → warning when `scope_escalation: true` is set. An autonomous agent can set the escalation flag itself. *Evidence: grep of hook source.*

**DD-3: Model-authored `verification_commands` executed as shell = trust boundary crossing.**  
Proposal says build mode "runs verification commands from the plan." No schema validation or allowlist is specified. This is a security violation under CLAUDE.md's hard rule ("If the LLM can cause irreversible state changes, it must not be the actor"). *Evidence: CLAUDE.md + security.md.*

**DD-4: CloudZero / gstack-v0.17-autoship citations are unverifiable.**  
Proposal cites "CloudZero velocity analysis Appendix C" and "gstack `/autoship` v0.17 planned." Neither is in the repo; no external link verifies. *Evidence: `git ls-tree` for cloudzero returns nothing; `ls ~/.claude/skills/gstack/` has no autoship-v0.17.*

**DD-5: Context exhaustion risk named but unmitigated.**  
Proposal itself acknowledges "full autobuild run could consume significant context" without a budget or safeguard. For an autonomous loop, this is a foreseeable failure mode. *Evidence: proposal self-reference + no cost-cap specification.*

---

## ANONYMIZED FINDINGS


Total: 54 findings pooled from two anonymous reviewer panels.
Arm C contributed 27; arm D contributed 27.
Arm identity is withheld from the judge by design.

---

## Finding 1

**[RISK] [MATERIAL] [COST:SMALL]:** The "3-tier decision classification (Mechanical / Taste / User Challenge)" is cited as existing in `/plan --auto`. `check_code_presence` finds "Mechanical" (1 match) and "Taste" (2 matches) in skills, but "User Challenge" returns zero matches and "3-tier" returns zero. Either the classification is not as formalized as the proposal implies, or it lives under different naming. Under autobuild the taxonomy becomes load-bearing — every silent mechanical decision is now unreviewed code on disk. Before reusing this taxonomy in a higher-stakes context, its actual definition should be pinned down and, ideally, the "auto-decide silently" tier should be narrower than in planning (where wrong choices cost nothing until build time).

## Finding 2

[RISK] [ADVISORY]: The build loop will likely increase data exposure to external LLM providers because implementation context, failures, and potentially test output are sent through shared LLM pathways. The repo shows both local LiteLLM routing in `scripts/llm_client.py` and direct Anthropic Managed Agents usage in `scripts/managed_agent.py`, with explicit third-party retention assumptions. If autobuild starts including raw test output, diffs, or environment-derived error messages in prompts, it broadens exfiltration paths unless redaction boundaries are defined.

## Finding 3

[ALTERNATIVE] [MATERIAL] [COST:SMALL]: The repo already has an explicit surface for autonomous execution between gates: `docs/orchestrator-contract.md` says “BuildOS owns the gates (plan, review, ship). The runner owns execution between gates” and defines a `spec → plan → build → test → review → ship` state machine (`docs/orchestrator-contract.md:1-50`). That directly conflicts with the proposal’s recommendation to embed autobuild entirely inside `plan/SKILL.md` with “no new scripts.” A runner/script-based implementation is an existing, documented architecture the proposal overlooks.

## Finding 4

[RISK] [ADVISORY] Bypassing Escalation: The proposal assumes the agent will reliably adhere to the "7 escalation triggers" during a long autonomous build phase. However, when instructed to operate autonomously (`--auto --build`), agents often aggressively guess rather than stopping to ask for help, overriding the escalation protocol to complete the task.

## Finding 5

**[ASSUMPTION] [ADVISORY]:** "~60-80 lines added to plan/SKILL.md" — ESTIMATED, not evidenced. The surrounding `--auto` logic plus the build loop plus iteration plus escalation wiring plus test invocation plus review handoff plus stop-enforcement is unlikely to fit in 80 lines of SKILL.md prose that an agent can reliably execute. The decompose-gate alone is a 100+ line hook. Autobuild-as-prose will drift; autobuild-as-script (even if called from SKILL.md) will not.

## Finding 6

**ASSUMPTION [MATERIAL] [COST:SMALL]:** The proposal assumes the plan artifact (`tasks/<topic>-plan.md`) is machine-parseable with sufficient fidelity to drive autonomous execution — that `build steps`, `file scopes`, and `verification_commands` are structured fields an agent can reliably extract and execute. The proposal text never confirms this structure exists in current plan artifacts. If plans are prose documents with loosely formatted sections, the "read the plan" step is actually a non-trivial interpretation problem, not a mechanical parse. This assumption is load-bearing: the entire autobuild loop depends on it. The fix is small (audit one real plan artifact and confirm the fields exist as structured data), but if they don't, the implementation scope expands significantly.

## Finding 7

**ASSUMPTION** [MATERIAL] [COST:SMALL]: The proposal cites **"CloudZero velocity analysis (Appendix C, Gap #2)"** and **"gstack's roadmap (planned `/autoship` in v0.17)"** as external motivation. Strings `CloudZero`, `CloudZero velocity`, `Appendix C`, `Gap #2`, `gstack`, `autoship`, `Autonomous execution loop` all return `exists: false` in `docs`. These citations cannot be audited in this repo, so the "why now" section rests entirely on unverifiable references. The judge should not weight the external-pressure argument.

## Finding 8

**ALTERNATIVE** [ADVISORY]: A less ambitious split: `--build` that stops after build+test (no auto-review), leaving `/review` manual. This preserves the human checkpoint where judgment matters most (reviewing implementation quality) while still removing the tedious part (typing the edits). The claimed value prop — "the gap between plan exists and code exists" — is fully captured by build+test alone. Auto-invoking `/review` and ship summary is scope creep inside a proposal about scope containment.

## Finding 9

[UNDER-ENGINEERED] [MATERIAL] [COST:MEDIUM]: Parallel execution is proposed for decompose tracks, but the existing `hook-agent-isolation.py` only enforces worktree isolation on write-capable Agent dispatches when a session flag indicates a parallel plan is active; it does not provide broader guarantees about prompt/path hygiene, test resource isolation, or merge/conflict handling. The proposal assumes “parallel agents get worktree isolation” is sufficient, but concurrent build/test loops create additional trust-boundary problems: one agent’s outputs can influence another through shared external resources, test fixtures, or copied absolute paths. Without an explicit orchestration layer for per-agent allowed paths, branch/worktree lifecycle, and reconciliation, parallel autobuild is riskier than described.

## Finding 10

[RISK] [MATERIAL] Context Exhaustion & Fragility: Implementing a massive autonomous loop—spanning plan reading, sequential implementation, test execution, multi-step iteration, parallel sub-agent orchestration, and review generation—purely through 60-80 lines of prompt instructions in a `SKILL.md` file is extremely fragile. Running this as an open-ended Claude Code session will likely lead to context window exhaustion, getting stuck in iteration loops, and losing track of the original plan as the context fills with bash outputs. [COST: MEDIUM] This requires a structured state machine or orchestrator script (e.g., a formal `autobuild.py`), not just prompt instructions.

## Finding 11

**UNDER-ENGINEERED** [ADVISORY]: Iteration quality / token cost risks in "Why Not" are named but no limit is set. Escalation trigger #5 is "3 attempts on the same problem" (workflow.md line 36), which caps per-step retry but not the overall build-step count or cumulative token budget. A 15-step plan × 3 attempts each = 45 agentic turns with no budget gate. Since `debate_common.py` has `_track_cost` / `_track_tool_loop_cost`, a cost ceiling on autobuild runs is cheap to add and the proposal omits it.

## Finding 12

**[RISK] [ADVISORY]:** "Iteration quality degrades: attempt 1 informed, attempt 2 reasonable, attempt 3 flailing" is acknowledged in Why-Not but the proposal doesn't act on it. Attempt 3's flailing commits still get staged. The build phase should at minimum `git stash` or revert between failed attempts so attempt 3's debris doesn't contaminate the working tree the human reviews.

## Finding 13

[OVER-ENGINEERED] [MATERIAL] [COST:MEDIUM]: The proposal frames this as missing infrastructure, but parts of the build/review loop it wants are already shipped: there is an active `hook-post-build-review.py` that counts edits under an active plan and raises a `needs_review` flag after threshold/re-fire (`hooks/hook-post-build-review.py:3-27`, `50-71`), with recent shipping evidence in commit `6a3fb0b` (“Structural review gate: post-build hook + re-fire policy”). Re-specifying “after all steps complete: run `/review`” purely in skill text ignores existing review-loop enforcement and risks creating two competing mechanisms for when review should happen.

## Finding 14

**ASSUMPTION** [MATERIAL] [COST:SMALL]: The proposal asserts `/plan --auto` already has a **"3-tier classification (Mechanical / Taste / User Challenge)"** which autobuild will "reuse." Strings `Mechanical`, `Taste`, `User Challenge`, `3-tier classification`, `decision classification`, and `6 principles` all return `exists: false` across both `docs` and `rules`. This classification scheme is not documented anywhere verifiable — so either it's implemented only inside `.claude/skills/plan/SKILL.md` (which I cannot read from here, so the proposal should cite it concretely) or it doesn't exist and the proposal is inventing a prerequisite it claims to reuse. Either way, "reuse existing infrastructure" is unsupported until the cite is pinned down.

## Finding 15

[ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: “Zero-risk — the human reviews every PR” is too strong. Human review mitigates merge-time risk, but not execution-time risk. The proposed build loop would run edits, shell commands, and tests before review, so the relevant security question is whether untrusted plan content or repo content can drive harmful local actions during the autonomous build phase. Review after the fact does not prevent destructive commands, secret exposure in logs, or unintended writes during execution.

## Finding 16

**RISK [ADVISORY]:** Token cost is listed under "Why Not" but not quantified. The proposal says a full run "could consume significant context" — SPECULATIVE, no estimate provided. For a proposal that touches context limits as a risk, even a rough estimate (e.g., "plan ~8K tokens + build edits ~20K + test output ~5K + review ~10K = ~43K tokens per run") would let the reader assess whether this is a real constraint. Without it, the risk is acknowledged but not evaluated.

---

## Finding 17

**ASSUMPTION** [MATERIAL] [COST:MEDIUM]: The proposal assumes the plan artifact contains structured "build steps, file scopes, and verification commands" that can be parsed. Searches for `build_steps` and `build steps` in skills returned zero matches. `verification_commands` exists (2 matches) and `surfaces_affected` exists (3 matches in skills, 2 in hooks — the latter in `hook-pre-edit-gate.sh`). So file scope is real; verification commands are referenced; but the "build steps" structure the build loop would iterate over is not an established schema. Before autobuild can "parse the plan," the plan template must be hardened into a machine-readable contract. (EVIDENCED: tool results above.)

## Finding 18

**UNDER-ENGINEERED [ADVISORY]**: The proposal doesn't address what happens to partial build state on escalation or failure. If the agent completes 4 of 6 build steps, hits escalation trigger #3 (ambiguous requirement), and pauses — the repo is in a partially-modified state. The human answers the question, but how does the agent resume? The plan artifact has no "current step" tracking. This isn't a blocker (the human can re-read the state), but it's a real operational gap for the "autonomous" claim.

## Finding 19

**ASSUMPTION** [MATERIAL] [COST:MEDIUM]: The proposal states it will "reuse `/plan --auto`'s 3-tier classification (Mechanical / Taste / User Challenge)." I searched skills and rules for `Mechanical`, `Taste`, and `3-tier classification` — zero matches in rules, zero matches for `Mechanical` in skills. Whatever decision-classification framework exists (if any) is not under these names. The proposal is building on an abstraction it claims already exists. Either the classification must be built first (new work, not reuse) or a different existing rubric must be named. Either way, "no new skill, no new scripts" is wrong. (EVIDENCED by tool results: `check_code_presence` returned `exists:false` for `Mechanical` in both `rules` and `skills`.)

## Finding 20

**RISK** [MATERIAL] [COST:SMALL]: The 3-attempt iteration cap + escalation compounds badly with parallel worktree agents (spawned by decompose gate). Three attempts × N parallel tracks = up to 3N failed test cycles before the human sees anything, and failures in one track may invalidate work in another (shared interfaces, merge conflicts on re-integration). The proposal doesn't address cross-track failure handling or the sync point between parallel tracks. Needs an explicit "one track fails → pause all tracks" semantic, or restrict `--build` to sequential-only in v1.

## Finding 21

**ASSUMPTION** [ADVISORY]: Proposal claims `/start` "already loads lessons at session start." `lessons.md` references exist in workflow.md line 7 as an orientation requirement, but I can't confirm `/start` skill behavior from the allowed directories. Minor — but if autobuild is supposed to read `tasks/lessons.md` "for the relevant domain," the proposal should specify how domain matching works (keyword? tier? manual tag?), not just assert it.

## Finding 22

**[UNDER-ENGINEERED] [ADVISORY]:** Token/cost budget is named as a risk but there's no budget declared. `debate_common.py` has `_track_cost` / `get_session_costs` machinery (verified) — autobuild is the exact workload that should plug into it with a hard ceiling (e.g., "stop and escalate if session cost > $X"). TRIVIAL to wire in, and turns an SPECULATIVE cost concern into a bounded one.

## Finding 23

**RISK [MATERIAL] [COST:SMALL]**: The proposal says parallel agents get "worktree isolation (existing decompose gate behavior)" but `hook-decompose-gate.py` is explicitly **advisory, not blocking** (confirmed: "Advisory, not blocking. Emits a prompt hint via `additionalContext`; does not deny"). `hook-agent-isolation.py` *is* blocking but only fires when `plan_submitted: true` is set in session state. The proposal doesn't specify that `--build` mode sets this flag. If it doesn't, parallel agents spawned during build have no enforcement-level isolation guarantee — only a nudge. For a mode designed to run autonomously, this is a meaningful gap.

## Finding 24

**UNDER-ENGINEERED** [MATERIAL] [COST:MEDIUM]: The proposal says "No new hook needed — the escalation protocol covers it" for scope containment, relying on `surfaces_affected` enforcement via trigger #4. But `hook-plan-gate.sh` enforces plan presence at **commit time**, not at Edit/Write time — its logic branches on `git commit*` (line 29). For an autonomous agent iterating through Edit/Write tool calls mid-build, nothing mechanically blocks edits outside `surfaces_affected` until the agent tries to commit. The escalation protocol is a *prompt rule* the agent may silently ignore when it has no stop signal. A `--build` mode with no real-time scope enforcement is exactly where an autonomous loop goes wrong. This is a genuine gap the proposal waves away.

## Finding 25

[UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: Scope containment is weaker than the proposal claims. It says “agent edits are checked against the plan's file list” and “no new hook needed,” but the only verified enforcement hook here is `hook-pre-edit-gate.sh`, which checks for the existence of a recent plan/proposal artifact before allowing edits to protected paths; it does not appear to enforce that edits stay within `surfaces_affected`. `hook-read-before-edit.py` is advisory, not blocking. So the trusted plan artifact does not currently become an enforced edit allowlist. That means a lower-trust build loop can still drift into unplanned files, especially outside protected-path coverage, with escalation depending on model judgment rather than enforcement.

## Finding 26

**ASSUMPTION [ADVISORY]:** The "Why Now" section cites gstack's roadmap and the CloudZero velocity analysis as external validation. This is a source-driven framing pattern — the proposal is partly justified by what other frameworks are building, not by measured pain in this repo. The claim that "the gap between plan exists and code exists is where the most human time is spent" is SPECULATIVE (no data from this repo's telemetry, despite `scripts/session_telemetry_query.py` existing). The severity framing ("most human time") is unverified and may be inflating scope.

## Finding 27

**ASSUMPTION [ADVISORY]:** The proposal claims `tasks/lessons.md` plus `/start` loading is "sufficient for a solo dev where the human is the learning system." This may be true, but it's asserted rather than argued. The specific failure mode — autobuild makes a mistake, the human corrects it in review, but the same mistake recurs in the next autobuild run because lessons.md wasn't updated — is not addressed. The proposal acknowledges this risk ("if autobuild produces recurring mistakes") but defers it entirely. For a proposal that explicitly invokes self-learning as a dependency, this deferral should be flagged as a known gap with a lightweight mitigation (e.g., autobuild appends a lessons entry when escalation trigger #5 fires).

## Finding 28

[RISK] [ADVISORY]: The proposal reuses “verification_commands” from the plan as executable commands. That creates a shell-injection trust boundary: plan text is untrusted until validated, especially if any upstream step can synthesize or transform those commands. I did not verify a current command-sanitization layer for this proposed path, so this is a design risk to address before implementation, not a verified existing flaw.

## Finding 29

**ALTERNATIVE [MATERIAL] [COST:SMALL]:** The candidate set is binary: manual build (status quo) vs. full autobuild loop. A missing middle candidate is **autobuild-dry-run / step-confirm mode**: the agent proposes each build step and waits for a single keypress before executing, with full test output shown inline. This captures most of the value (no context-switching, no manual test invocation) at a fraction of the risk (human stays in the loop per step). The proposal frames the choice as "manual everything" vs. "autonomous loop with escalation triggers," but the real space includes "human-paced automation" which is cheaper to build and safer to deploy first. The 60-80 line estimate likely applies to this variant too.

## Finding 30

**ASSUMPTION [MATERIAL] [COST:SMALL]**: The proposal assumes `verification_commands` in the plan artifact are safe to execute autonomously. Confirmed present in skills/docs/rules. But there's no validation that these commands are bounded — a plan could contain `verification_commands` like `pytest && deploy.sh` or commands with side effects. The proposal says "Run verification commands from the plan" without any sandboxing, allowlist, or review of what those commands do. In a solo-dev context this is lower risk, but the proposal should explicitly state that `verification_commands` are human-authored at plan-approval time (which is true given the approval gate) and therefore trusted — this is an unstated premise that should be made explicit.

## Finding 31

[ASSUMPTION] [MATERIAL] Prompt-Driven Orchestration: The proposal assumes the main agent can reliably "spawn worktree-isolated agents" for parallel tracks via prompt instructions alone. Orchestrating parallel Claude sessions inside Bash tools, managing their concurrency, capturing their outputs, and merging their worktrees requires robust scripting and error handling. Relying on an LLM to dynamically construct and manage these concurrent IPC workflows on the fly is highly speculative and likely to fail. [COST: LARGE] Requires building an actual task dispatcher or utilizing a managed orchestration framework for sub-agents.

## Finding 32

**ASSUMPTION** [MATERIAL] [COST:SMALL]: The proposal refers to a **"new Step 6 in `/ship`"** that generates spec-mapped ship summaries, and instructs autobuild to "invoke ship summary generation (new Step 6 in `/ship`)." Strings `ship summary`, `spec-mapped`, `Step 6` are absent from `docs`. The implementation plan depends on a downstream artifact that is itself not yet shipped (or not yet described in docs). This turns a "no new infrastructure" proposal into one that chains on an unbuilt feature.

## Finding 33

**ASSUMPTION [MATERIAL] [COST:MEDIUM]:** The proposal claims "no new hook needed — the escalation protocol covers it" for scope containment. But the escalation protocol is a set of rules in `workflow.md` — it only fires if the agent reads and applies it correctly during autonomous execution. The existing hooks (`hook-pre-edit-gate.sh`, `hook-read-before-edit.py`, `hook-decompose-gate.py`) enforce constraints mechanically. Scope containment during autobuild needs the same mechanical enforcement: a hook that checks edits against `surfaces_affected` before allowing them. Relying on the agent to self-escalate when it's also trying to complete the task is a conflict of interest. This is an UNDER-ENGINEERED gap, not a covered case.

## Finding 34

**ASSUMPTION [ADVISORY]**: The proposal states "Building it on one repo (Build OS itself) is zero-risk — the human reviews every PR." This is only true if the ship step requires human approval before merge. The proposal says the human "Reviews the `/review` output and approves merge/ship" — but `/ship` with a summary auto-generation step could be invoked automatically after review. The proposal should clarify whether `--build` mode stops before `/ship` or includes it, since "auto-invoke `/review`" is stated but the ship step is ambiguous.

## Finding 35

**ASSUMPTION [MATERIAL] [COST:SMALL]:** The proposal assumes the plan artifact (`tasks/<topic>-plan.md`) is machine-parseable with sufficient fidelity to drive autonomous execution — that `build steps`, `surfaces_affected`, and `verification_commands` are structured fields an agent can reliably extract and act on. The proposal never verifies this. If the plan artifact is primarily prose (as most markdown plans are), the "read the plan" step is itself an LLM inference task with hallucination risk, not a deterministic parse. The entire autobuild reliability argument rests on this unstated premise. A hybrid candidate is missing: **structured plan schema first, autobuild second** — enforce a machine-readable plan format (YAML frontmatter with explicit `steps[]`, `verification_commands[]`, `surfaces_affected[]`) as a prerequisite, then autobuild becomes a thin executor rather than an interpreter.

## Finding 36

**ALTERNATIVE [MATERIAL] [COST:SMALL]:** The candidate set is binary: manual build (status quo) vs. full autobuild (`--build` flag that runs the entire implementation loop). A missing middle option is **supervised step-by-step execution** — the agent implements one plan step, shows the diff and test result, waits for a thumbs-up, then proceeds. This captures most of the value (no manual editing, no manual test-running) while keeping the human in the loop at each step boundary rather than only at escalation triggers. The proposal's own "Why Not" section acknowledges that "plans are abstract; implementation is concrete" and that iteration quality degrades — both concerns are substantially mitigated by step-level checkpoints. This hybrid is cheaper to implement (no iteration loop needed, no 3-strike logic) and lower risk. Its absence from the candidate set is a framing gap.

## Finding 37

**RISK** [ADVISORY]: Token/context cost is hand-waved ("significant... may hit context limits"). No EVIDENCED numbers. A single `/plan --auto` pipeline already runs think→challenge→plan with multiple LLM calls (`scripts/debate.py` has cmd_challenge, cmd_judge, cmd_refine, _consolidate_challenges). Adding build + N test iterations + review on top, in one session, is plausibly 3-5x context. This is SPECULATIVE without instrumenting existing runs, but the scaling axis is real: autobuild cost grows with plan size × iteration count, which is the worst possible product for context budgets.

## Finding 38

**UNDER-ENGINEERED** [MATERIAL] [COST:SMALL]: Scope containment is delegated to "escalation trigger #4 (scope is growing)" with "no new hook needed." But `hook-pre-edit-gate.sh` is a bash script that checks protected paths against recent plan/proposal artifacts — it does NOT check edits against a specific plan's `surfaces_affected` list. In an autonomous loop, the agent self-polices scope via prompt discipline, which is exactly the failure mode the hook layer was built to prevent elsewhere. A 30-line addition to `hook-pre-edit-gate.sh` that reads `surfaces_affected` from the active plan and blocks out-of-scope writes during autobuild closes a real hole. Skipping it means autobuild has weaker scope enforcement than manual editing under the same tier.

## Finding 39

**[UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]:** "Max 3 attempts per step" is stated but there is no mechanism to enforce it across a long-running autonomous agent. The escalation protocol (verified in workflow.md line 36) is a *rule the model is supposed to follow*, not an enforced gate. `/plan --auto` is an interactive pipeline where the human is a natural checkpoint; autobuild removes that checkpoint. Without a counter persisted somewhere (session state, lesson_events, or a new hook), "trigger #5" is an honor-system limit. For an autonomous loop this is the single most important safety rail and it should be mechanically enforced, not prose-enforced.

## Finding 40

**RISK [ADVISORY]**: Token cost is listed under "Why Not" but not quantified. A full autobuild run (think → challenge → plan → build → test × N → iterate × 3 × N → review) on a non-trivial task could easily consume 200K-500K tokens. SPECULATIVE — no data in the proposal. The proposal acknowledges this but doesn't suggest any mitigation (context checkpointing, step-level context resets, cost gates). Given `_track_cost` and `_cost_delta_since` exist in `debate_common.py`, there's existing cost-tracking infrastructure that could be reused for a build-phase cost gate, but the proposal doesn't mention it.

## Finding 41

[UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposal says “no new skill, no new scripts, no new hooks” and intends to implement autobuild purely as extra instructions in `plan/SKILL.md`, but the repo already documents a different trust boundary: `docs/orchestrator-contract.md` explicitly says “BuildOS owns the gates … The runner owns execution between gates.” Moving autonomous build/test execution into a prompt-only skill collapses that boundary without adding machine-enforced state, attempt counting, or path controls beyond whatever the model happens to follow. For a feature that executes code, edits files, and loops on failures, relying on natural-language compliance instead of an explicit runner/state machine materially increases risk of uncontrolled edits, skipped escalation, and inconsistent stop conditions.

## Finding 42

**RISK [MATERIAL] [COST:MEDIUM]**: The proposal's decision classification (Mechanical/Taste/User Challenge) is confirmed to exist only in skills (2 matches for "Taste"), not in rules or docs. This means the classification logic lives in natural-language skill instructions, not in any enforced hook or code path. During autonomous build, the agent must self-classify every decision correctly — there's no mechanical backstop. The proposal treats this as solved infrastructure when it's actually a prompt-following behavior. A misclassification (treating a "User Challenge" as "Taste") during autonomous execution could silently make a behavior-affecting decision without escalation. The proposal should acknowledge this is a trust-in-model assumption, not an enforcement guarantee.

## Finding 43

**OVER-ENGINEERED** [ADVISORY]: "Auto-invoke `/review` after all steps complete" — `/review` itself may recommend further changes. Does autobuild then re-enter the build loop to apply review findings? If yes, this is an unbounded cycle (review → build → review → ...). If no, the "autonomous" label overpromises: the human still hand-applies review findings. The proposal is silent on the review→fix loop, which is where the real time is spent.

## Finding 44

**OVER-ENGINEERED [ADVISORY]:** The proposal includes parallel agent spawning via worktree isolation for parallel plan tracks. This is the decompose gate's existing behavior, but invoking it from within an autobuild loop adds a coordination layer (multiple agents, multiple worktrees, merge logic) that the proposal waves away with "existing decompose gate behavior." For a solo dev repo where the stated use case is "zero-risk because the human reviews every PR," parallel execution is unlikely to be needed on the first iteration of autobuild. The simpler sequential-only implementation would cover the stated use case and defer parallelism until there's evidence it's needed.

## Finding 45

**OVER-ENGINEERED [ADVISORY]:** The proposal pre-wires the full pipeline (build → test → iterate → review → ship-summary) before there's evidence that the build step alone works reliably. The review and ship-summary invocations are Phase 2 concerns. A sounder sequencing: ship autobuild-to-test-pass first, measure how often it reaches that gate cleanly, then add auto-review invocation. Chaining unproven steps multiplies failure modes and makes debugging harder.

## Finding 46

**ASSUMPTION [MATERIAL] [COST:TRIVIAL]:** The proposal cites the CloudZero velocity analysis (Appendix C, Gap #2) and gstack's roadmap as external validation that this is "the key missing capability." These are treated as independent corroboration, but the proposal provides no access to these sources for verification. If these are internal documents or the framing was inherited from them, the proposal may be inheriting their problem frame rather than evaluating from first principles. The specific claim that "neither framework has solved it" is SPECULATIVE — no evidence basis is provided. This doesn't change the recommendation but inflates the urgency framing.

## Finding 47

[UNDER-ENGINEERED] [ADVISORY]: The proposal’s “Estimated scope: ~60-80 lines added to plan/SKILL.md” is not grounded in the current platform constraints. `docs/platform-features.md` notes SKILL.md is advisory context, not deterministic execution, and should stay under 500 lines (`docs/platform-features.md:50-77`). Since the proposed feature includes plan parsing, step iteration, retry limits, escalation logic, parallelization, test execution, and review handoff, implementing it only as prompt text increases variance and leaves the actual state machine unenforced.

## Finding 48

**RISK [MATERIAL] [COST:SMALL]**: The proposal claims "No new hook needed — the escalation protocol covers [scope containment]." This is partially false. `hook-pre-edit-gate.sh` already checks `allowed_paths` in plan frontmatter (confirmed at line 52-54), but the proposal's `surfaces_affected` field is a *different* key — confirmed by `check_code_presence` showing `surfaces_affected` exists in skills/docs but `allowed_paths` exists only in docs. If the build phase relies on `surfaces_affected` for scope enforcement but the hook reads `allowed_paths`, the containment silently fails. The proposal needs to either (a) align field names, or (b) explicitly state that `surfaces_affected` maps to `allowed_paths` in the plan artifact schema.

## Finding 49

**[ASSUMPTION] [MATERIAL] [COST:SMALL]:** The proposal claims "The plan artifact already declares `surfaces_affected`" and that scope escalation is handled by the existing escalation protocol with "no new hook needed." But the pre-edit-gate actually keys off `allowed_paths` in plan frontmatter (verified lines 52–54 of hook-pre-edit-gate.sh), not `surfaces_affected`. These may or may not be the same field. More importantly, the pre-edit-gate **degrades block to warning** when `scope_escalation: true` is set — a human-oriented affordance that an autonomous agent will gleefully exploit ("I'll just set scope_escalation and proceed"). Under autobuild, the soft-escalation path needs to be re-hardened to force a STOP, not a warning. This is a small but real change, not a pure reuse.

## Finding 50

**RISK [ADVISORY]:** The 3-attempt iteration limit is presented as a safety valve, but the proposal doesn't address what happens to partial state after escalation. If attempt 2 partially modifies files and then escalates, the human inherits a half-edited codebase. The worktree isolation (decompose gate) handles parallel agents, but sequential build steps within a single worktree have no rollback mechanism described. This is a concrete failure mode the proposal leaves unaddressed.

---

## Finding 51

[ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The claim that “parallel agents get worktree isolation (existing decompose gate behavior)” overstates current behavior. `hook-decompose-gate.py` is advisory only and “does not deny” / only emits `additionalContext` (`hooks/hook-decompose-gate.py:4-18`), and `is_worktree_agent()` merely detects worktree context (`hooks/hook-decompose-gate.py:67-86`). There is no evidence here of automatic spawning of worktree-isolated agents. So the proposal is premised on automation that the repo does not currently provide.

## Finding 52

[ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal says “No new hook needed — the escalation protocol covers it,” but scope containment during build is already enforced by a hook, not just advisory protocol. `hooks/hook-pre-edit-gate.sh` explicitly checks active plan `allowed_paths` and blocks writes outside them unless `scope_escalation: true` is set (`hooks/hook-pre-edit-gate.sh:52-145`). That changes the design: `--build` cannot rely on prose-only escalation if plan artifacts don’t populate `allowed_paths` correctly, and the proposal’s stated mechanism (“surfaces_affected” + escalation trigger #4) does not match the actual enforcement surface.

## Finding 53

**OVER-ENGINEERED [ADVISORY]**: The proposal adds `--build` as a flag on `/plan --auto` rather than as a separate skill. This keeps the implementation small (~60-80 lines in SKILL.md) but means the plan skill now has three modes (`/plan`, `/plan --auto`, `/plan --auto --build`) with significantly different behavior profiles. A separate `/build` skill invoked after plan approval would be cleaner separation of concerns and easier to test/iterate independently. The proposal acknowledges this tradeoff implicitly ("No new skill") but doesn't justify why co-location is better than separation.

---

## Finding 54

**[ALTERNATIVE] [MATERIAL] [COST:TRIVIAL]:** The proposal jumps straight to a `--build` flag on `/plan --auto`, coupling planning and building into one invocation. An alternative: a separate `/build` skill that consumes a committed plan artifact. Benefits: (a) the plan can be reviewed, edited, committed, then built in a fresh session with clean context (addressing the "context limits" Why-Not); (b) resumable — if build fails at step 4/7, re-invoking `/build` reads plan state and continues; (c) clearer failure attribution. The `--build` coupling makes the pipeline monolithic; an artifact-driven `/build` skill matches the existing pattern where skills consume artifacts from `tasks/`.

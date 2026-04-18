---
debate_id: autobuild
created: 2026-04-17T13:27:10-0700
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
# autobuild — Challenger Reviews

## Challenger A (architect) — Challenges
Key finding: the proposal claims "3-tier classification (Mechanical/Taste/User Challenge)" is reused from `/plan --auto` — but `Mechanical`/`Taste` are absent from rules and skills. This is a material misrepresentation of existing infrastructure.

## Challenges

1. **ASSUMPTION** [MATERIAL] [COST:MEDIUM]: The proposal states it will "reuse `/plan --auto`'s 3-tier classification (Mechanical / Taste / User Challenge)." I searched skills and rules for `Mechanical`, `Taste`, and `3-tier classification` — zero matches in rules, zero matches for `Mechanical` in skills. Whatever decision-classification framework exists (if any) is not under these names. The proposal is building on an abstraction it claims already exists. Either the classification must be built first (new work, not reuse) or a different existing rubric must be named. Either way, "no new skill, no new scripts" is wrong. (EVIDENCED by tool results: `check_code_presence` returned `exists:false` for `Mechanical` in both `rules` and `skills`.)

2. **ASSUMPTION** [MATERIAL] [COST:MEDIUM]: The proposal assumes the plan artifact contains structured "build steps, file scopes, and verification commands" that can be parsed. Searches for `build_steps` and `build steps` in skills returned zero matches. `verification_commands` exists (2 matches) and `surfaces_affected` exists (3 matches in skills, 2 in hooks — the latter in `hook-pre-edit-gate.sh`). So file scope is real; verification commands are referenced; but the "build steps" structure the build loop would iterate over is not an established schema. Before autobuild can "parse the plan," the plan template must be hardened into a machine-readable contract. (EVIDENCED: tool results above.)

3. **UNDER-ENGINEERED** [MATERIAL] [COST:SMALL]: Scope containment is delegated to "escalation trigger #4 (scope is growing)" with "no new hook needed." But `hook-pre-edit-gate.sh` is a bash script that checks protected paths against recent plan/proposal artifacts — it does NOT check edits against a specific plan's `surfaces_affected` list. In an autonomous loop, the agent self-polices scope via prompt discipline, which is exactly the failure mode the hook layer was built to prevent elsewhere. A 30-line addition to `hook-pre-edit-gate.sh` that reads `surfaces_affected` from the active plan and blocks out-of-scope writes during autobuild closes a real hole. Skipping it means autobuild has weaker scope enforcement than manual editing under the same tier.

4. **RISK** [MATERIAL] [COST:SMALL]: The 3-attempt iteration cap + escalation compounds badly with parallel worktree agents (spawned by decompose gate). Three attempts × N parallel tracks = up to 3N failed test cycles before the human sees anything, and failures in one track may invalidate work in another (shared interfaces, merge conflicts on re-integration). The proposal doesn't address cross-track failure handling or the sync point between parallel tracks. Needs an explicit "one track fails → pause all tracks" semantic, or restrict `--build` to sequential-only in v1.

5. **OVER-ENGINEERED** [ADVISORY]: "Auto-invoke `/review` after all steps complete" — `/review` itself may recommend further changes. Does autobuild then re-enter the build loop to apply review findings? If yes, this is an unbounded cycle (review → build → review → ...). If no, the "autonomous" label overpromises: the human still hand-applies review findings. The proposal is silent on the review→fix loop, which is where the real time is spent.

6. **RISK** [ADVISORY]: Token/context cost is hand-waved ("significant... may hit context limits"). No EVIDENCED numbers. A single `/plan --auto` pipeline already runs think→challenge→plan with multiple LLM calls (`scripts/debate.py` has cmd_challenge, cmd_judge, cmd_refine, _consolidate_challenges). Adding build + N test iterations + review on top, in one session, is plausibly 3-5x context. This is SPECULATIVE without instrumenting existing runs, but the scaling axis is real: autobuild cost grows with plan size × iteration count, which is the worst possible product for context budgets.

7. **ALTERNATIVE** [ADVISORY]: A less ambitious split: `--build` that stops after build+test (no auto-review), leaving `/review` manual. This preserves the human checkpoint where judgment matters most (reviewing implementation quality) while still removing the tedious part (typing the edits). The claimed value prop — "the gap between plan exists and code exists" — is fully captured by build+test alone. Auto-invoking `/review` and ship summary is scope creep inside a proposal about scope containment.

## Concessions
1. Correctly identifies that surrounding infrastructure (decompose gate with `is_worktree_agent`, escalation protocol in workflow.md, `verification_commands`, `surfaces_affected` in plan frontmatter) exists and is non-trivial — verified via tool calls.
2. Scoping to Build OS itself as the pilot repo is genuinely low-risk: every PR is human-reviewed and the blast radius is bounded.
3. The "why not" section honestly names the hard parts (judgment, iteration quality degradation, context cost) rather than hiding them.

## Verdict
**REVISE** — The gap being addressed is real, but the proposal materially overstates reuse: the claimed 3-tier decision classification does not exist in the repo, the plan artifact lacks a machine-readable "build steps" schema, and scope containment leans on a hook that doesn't actually check plan-specific file scope. Fix those three (add the classification rubric or drop the claim; define the plan's build-step contract; extend `hook-pre-edit-gate.sh` to read `surfaces_affected`) and the "60-80 lines in plan/SKILL.md" estimate becomes credible. As written, it's closer to a small subsystem than a skill-doc addition.

---

## Challenger B (security) — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposal says “no new skill, no new scripts, no new hooks” and intends to implement autobuild purely as extra instructions in `plan/SKILL.md`, but the repo already documents a different trust boundary: `docs/orchestrator-contract.md` explicitly says “BuildOS owns the gates … The runner owns execution between gates.” Moving autonomous build/test execution into a prompt-only skill collapses that boundary without adding machine-enforced state, attempt counting, or path controls beyond whatever the model happens to follow. For a feature that executes code, edits files, and loops on failures, relying on natural-language compliance instead of an explicit runner/state machine materially increases risk of uncontrolled edits, skipped escalation, and inconsistent stop conditions.

2. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: Scope containment is weaker than the proposal claims. It says “agent edits are checked against the plan's file list” and “no new hook needed,” but the only verified enforcement hook here is `hook-pre-edit-gate.sh`, which checks for the existence of a recent plan/proposal artifact before allowing edits to protected paths; it does not appear to enforce that edits stay within `surfaces_affected`. `hook-read-before-edit.py` is advisory, not blocking. So the trusted plan artifact does not currently become an enforced edit allowlist. That means a lower-trust build loop can still drift into unplanned files, especially outside protected-path coverage, with escalation depending on model judgment rather than enforcement.

3. [UNDER-ENGINEERED] [MATERIAL] [COST:MEDIUM]: Parallel execution is proposed for decompose tracks, but the existing `hook-agent-isolation.py` only enforces worktree isolation on write-capable Agent dispatches when a session flag indicates a parallel plan is active; it does not provide broader guarantees about prompt/path hygiene, test resource isolation, or merge/conflict handling. The proposal assumes “parallel agents get worktree isolation” is sufficient, but concurrent build/test loops create additional trust-boundary problems: one agent’s outputs can influence another through shared external resources, test fixtures, or copied absolute paths. Without an explicit orchestration layer for per-agent allowed paths, branch/worktree lifecycle, and reconciliation, parallel autobuild is riskier than described.

4. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: “Zero-risk — the human reviews every PR” is too strong. Human review mitigates merge-time risk, but not execution-time risk. The proposed build loop would run edits, shell commands, and tests before review, so the relevant security question is whether untrusted plan content or repo content can drive harmful local actions during the autonomous build phase. Review after the fact does not prevent destructive commands, secret exposure in logs, or unintended writes during execution.

5. [RISK] [ADVISORY]: The proposal reuses “verification_commands” from the plan as executable commands. That creates a shell-injection trust boundary: plan text is untrusted until validated, especially if any upstream step can synthesize or transform those commands. I did not verify a current command-sanitization layer for this proposed path, so this is a design risk to address before implementation, not a verified existing flaw.

6. [RISK] [ADVISORY]: The build loop will likely increase data exposure to external LLM providers because implementation context, failures, and potentially test output are sent through shared LLM pathways. The repo shows both local LiteLLM routing in `scripts/llm_client.py` and direct Anthropic Managed Agents usage in `scripts/managed_agent.py`, with explicit third-party retention assumptions. If autobuild starts including raw test output, diffs, or environment-derived error messages in prompts, it broadens exfiltration paths unless redaction boundaries are defined.

## Concessions
- The proposal correctly identifies the main operational gap between plan generation and post-build review/shipping.
- Reusing existing escalation triggers and review gates is directionally sound; it avoids inventing a second policy system.
- The repo already shows some security-conscious patterns around credentials and logging, e.g. retry logging in `managed_agent.py` avoids printing exception messages that may contain key fragments.

## Verdict
REVISE — the idea is sound, but implementing autonomous build/test execution as prompt-only skill text without enforced state, path boundaries, and execution controls is not yet security-robust enough.

---

## Challenger C (pm) — Challenges
## Challenges
1. [RISK] [MATERIAL] Context Exhaustion & Fragility: Implementing a massive autonomous loop—spanning plan reading, sequential implementation, test execution, multi-step iteration, parallel sub-agent orchestration, and review generation—purely through 60-80 lines of prompt instructions in a `SKILL.md` file is extremely fragile. Running this as an open-ended Claude Code session will likely lead to context window exhaustion, getting stuck in iteration loops, and losing track of the original plan as the context fills with bash outputs. [COST: MEDIUM] This requires a structured state machine or orchestrator script (e.g., a formal `autobuild.py`), not just prompt instructions.

2. [ASSUMPTION] [MATERIAL] Prompt-Driven Orchestration: The proposal assumes the main agent can reliably "spawn worktree-isolated agents" for parallel tracks via prompt instructions alone. Orchestrating parallel Claude sessions inside Bash tools, managing their concurrency, capturing their outputs, and merging their worktrees requires robust scripting and error handling. Relying on an LLM to dynamically construct and manage these concurrent IPC workflows on the fly is highly speculative and likely to fail. [COST: LARGE] Requires building an actual task dispatcher or utilizing a managed orchestration framework for sub-agents.

3. [RISK] [ADVISORY] Bypassing Escalation: The proposal assumes the agent will reliably adhere to the "7 escalation triggers" during a long autonomous build phase. However, when instructed to operate autonomously (`--auto --build`), agents often aggressively guess rather than stopping to ask for help, overriding the escalation protocol to complete the task.

## Concessions
1. The user value is undeniable: bridging the gap between plan and review is the primary bottleneck in the current workflow.
2. Relying on existing `tasks/lessons.md` instead of building a complex per-project JSONL learning store is a smart, pragmatic scope containment.
3. Hooking into the existing `surfaces_affected` to detect scope creep is an excellent reuse of existing guardrails.

## Verdict
REVISE: The feature addresses a critical user need, but attempting to drive long-running, multi-agent parallel build loops purely through markdown prompt additions is structurally unsound and requires a dedicated orchestrator script.

---

## Challenger D (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL] [COST:SMALL]:** The proposal assumes the plan artifact (`tasks/<topic>-plan.md`) is machine-parseable with sufficient fidelity to drive autonomous execution — that `build steps`, `file scopes`, and `verification_commands` are structured fields an agent can reliably extract and execute. The proposal text never confirms this structure exists in current plan artifacts. If plans are prose documents with loosely formatted sections, the "read the plan" step is actually a non-trivial interpretation problem, not a mechanical parse. This assumption is load-bearing: the entire autobuild loop depends on it. The fix is small (audit one real plan artifact and confirm the fields exist as structured data), but if they don't, the implementation scope expands significantly.

2. **ALTERNATIVE [MATERIAL] [COST:SMALL]:** The candidate set is binary: manual build (status quo) vs. full autobuild (`--build` flag that runs the entire implementation loop). A missing middle option is **supervised step-by-step execution** — the agent implements one plan step, shows the diff and test result, waits for a thumbs-up, then proceeds. This captures most of the value (no manual editing, no manual test-running) while keeping the human in the loop at each step boundary rather than only at escalation triggers. The proposal's own "Why Not" section acknowledges that "plans are abstract; implementation is concrete" and that iteration quality degrades — both concerns are substantially mitigated by step-level checkpoints. This hybrid is cheaper to implement (no iteration loop needed, no 3-strike logic) and lower risk. Its absence from the candidate set is a framing gap.

3. **ASSUMPTION [MATERIAL] [COST:TRIVIAL]:** The proposal cites the CloudZero velocity analysis (Appendix C, Gap #2) and gstack's roadmap as external validation that this is "the key missing capability." These are treated as independent corroboration, but the proposal provides no access to these sources for verification. If these are internal documents or the framing was inherited from them, the proposal may be inheriting their problem frame rather than evaluating from first principles. The specific claim that "neither framework has solved it" is SPECULATIVE — no evidence basis is provided. This doesn't change the recommendation but inflates the urgency framing.

4. **OVER-ENGINEERED [ADVISORY]:** The proposal includes parallel agent spawning via worktree isolation for parallel plan tracks. This is the decompose gate's existing behavior, but invoking it from within an autobuild loop adds a coordination layer (multiple agents, multiple worktrees, merge logic) that the proposal waves away with "existing decompose gate behavior." For a solo dev repo where the stated use case is "zero-risk because the human reviews every PR," parallel execution is unlikely to be needed on the first iteration of autobuild. The simpler sequential-only implementation would cover the stated use case and defer parallelism until there's evidence it's needed.

5. **ASSUMPTION [ADVISORY]:** The proposal claims `tasks/lessons.md` plus `/start` loading is "sufficient for a solo dev where the human is the learning system." This may be true, but it's asserted rather than argued. The specific failure mode — autobuild makes a mistake, the human corrects it in review, but the same mistake recurs in the next autobuild run because lessons.md wasn't updated — is not addressed. The proposal acknowledges this risk ("if autobuild produces recurring mistakes") but defers it entirely. For a proposal that explicitly invokes self-learning as a dependency, this deferral should be flagged as a known gap with a lightweight mitigation (e.g., autobuild appends a lessons entry when escalation trigger #5 fires).

6. **RISK [ADVISORY]:** Token cost is listed under "Why Not" but not quantified. The proposal says a full run "could consume significant context" — SPECULATIVE, no estimate provided. For a proposal that touches context limits as a risk, even a rough estimate (e.g., "plan ~8K tokens + build edits ~20K + test output ~5K + review ~10K = ~43K tokens per run") would let the reader assess whether this is a real constraint. Without it, the risk is acknowledged but not evaluated.

---

## Concessions

1. **The implementation scope is correctly bounded.** ~60-80 lines to `plan/SKILL.md`, reusing existing escalation protocol, hooks, and review infrastructure — this is genuinely lean for what it proposes.
2. **The approval gate preservation is correct.** Keeping the human checkpoint between plan and build is the right safety valve, and the proposal doesn't try to automate it away.
3. **The "Why Not" section is honest.** Listing iteration quality degradation and scope creep risk as real concerns, rather than dismissing them, is good epistemic hygiene.

---

## Verdict

**REVISE** — The binary framing (manual vs. full autobuild) omits the supervised step-by-step variant that addresses the proposal's own stated risks at lower implementation cost, and the machine-parseability of plan artifacts is an unverified load-bearing assumption that should be confirmed before committing to the implementation approach.

---

## Challenger E (frame-factual) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal says “No new hook needed — the escalation protocol covers it,” but scope containment during build is already enforced by a hook, not just advisory protocol. `hooks/hook-pre-edit-gate.sh` explicitly checks active plan `allowed_paths` and blocks writes outside them unless `scope_escalation: true` is set (`hooks/hook-pre-edit-gate.sh:52-145`). That changes the design: `--build` cannot rely on prose-only escalation if plan artifacts don’t populate `allowed_paths` correctly, and the proposal’s stated mechanism (“surfaces_affected” + escalation trigger #4) does not match the actual enforcement surface.

2. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The claim that “parallel agents get worktree isolation (existing decompose gate behavior)” overstates current behavior. `hook-decompose-gate.py` is advisory only and “does not deny” / only emits `additionalContext` (`hooks/hook-decompose-gate.py:4-18`), and `is_worktree_agent()` merely detects worktree context (`hooks/hook-decompose-gate.py:67-86`). There is no evidence here of automatic spawning of worktree-isolated agents. So the proposal is premised on automation that the repo does not currently provide.

3. [ALTERNATIVE] [MATERIAL] [COST:SMALL]: The repo already has an explicit surface for autonomous execution between gates: `docs/orchestrator-contract.md` says “BuildOS owns the gates (plan, review, ship). The runner owns execution between gates” and defines a `spec → plan → build → test → review → ship` state machine (`docs/orchestrator-contract.md:1-50`). That directly conflicts with the proposal’s recommendation to embed autobuild entirely inside `plan/SKILL.md` with “no new scripts.” A runner/script-based implementation is an existing, documented architecture the proposal overlooks.

4. [OVER-ENGINEERED] [MATERIAL] [COST:MEDIUM]: The proposal frames this as missing infrastructure, but parts of the build/review loop it wants are already shipped: there is an active `hook-post-build-review.py` that counts edits under an active plan and raises a `needs_review` flag after threshold/re-fire (`hooks/hook-post-build-review.py:3-27`, `50-71`), with recent shipping evidence in commit `6a3fb0b` (“Structural review gate: post-build hook + re-fire policy”). Re-specifying “after all steps complete: run `/review`” purely in skill text ignores existing review-loop enforcement and risks creating two competing mechanisms for when review should happen.

5. [UNDER-ENGINEERED] [ADVISORY]: The proposal’s “Estimated scope: ~60-80 lines added to plan/SKILL.md” is not grounded in the current platform constraints. `docs/platform-features.md` notes SKILL.md is advisory context, not deterministic execution, and should stay under 500 lines (`docs/platform-features.md:50-77`). Since the proposed feature includes plan parsing, step iteration, retry limits, escalation logic, parallelization, test execution, and review handoff, implementing it only as prompt text increases variance and leaves the actual state machine unenforced.

## Concessions
- It’s right that the repo has substantial surrounding pieces already: plan artifacts, decompose signal, review infrastructure, and ship/review docs/hooks are present.
- It’s right that lessons infrastructure already exists in lighter form (`scripts/lesson_events.py` + `tasks/lessons.md` usage), so a separate learning subsystem is not obviously prerequisite.
- It correctly identifies a real gap between planning and review; the repo’s own `orchestrator-contract.md` also models build/test as a distinct phase.

## Verdict
REVISE — the proposal’s core goal is plausible, but it misstates key current behavior (scope enforcement, worktree automation) and overlooks the repo’s existing runner/orchestrator architecture for autonomous execution.

---

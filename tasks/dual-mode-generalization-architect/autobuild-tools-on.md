---
debate_id: autobuild-tools-on
created: 2026-04-17T14:43:39-0700
mapping:
  A: claude-opus-4-7
personas:
  A: architect
---
# autobuild-tools-on — Challenger Reviews

## Challenger A (architect) — Challenges
The evidence is decisive: **the orchestrator contract explicitly externalizes the build loop**. It says:

- "BuildOS owns the gates (plan, review, ship). The runner owns execution between gates."
- "**Things BuildOS does NOT do**: Test execution. Git operations."
- "BuildOS gates on results but doesn't run tests itself."

The proposal inverts this by adding build/test/iterate inside `/plan --auto --build`. That is an architectural reversal, not a ~60-line skill addition. I have enough to review.

## Challenges

1. **OVER-ENGINEERED / ALTERNATIVE** [MATERIAL] [COST:MEDIUM]: The proposal reinvents infrastructure that already exists as a documented contract. `docs/orchestrator-contract.md` (178 lines) already specifies the exact state machine — `spec → plan → build → test → review → ship` with `test → build` loop gated by `max_attempts`, the 7 escalation triggers verbatim, `allowed_paths`/`surfaces_affected`/`verification_commands` in plan frontmatter, and explicit gate/runner boundaries. It explicitly states: *"BuildOS owns the gates (plan, review, ship). The runner owns execution between gates."* and *"Things BuildOS does NOT do: Test execution. Git operations."* The proposal inverts this — putting build/test/iterate inside the `/plan` skill makes BuildOS the runner, collapsing a deliberate separation. **If the team wants autobuild, the architecturally consistent move is to build the external runner that the contract already describes, or to formally retire the orchestrator contract. Pick one; don't quietly contradict it in a skill body.**

2. **ASSUMPTION** [MATERIAL] [COST:TRIVIAL to detect, SMALL to fix]: "No new hook needed — the escalation protocol covers it." The pre-edit gate (`hooks/hook-pre-edit-gate.sh` line 52+) already performs scope containment against `allowed_paths`, so this is partly true — but only for `Edit`/`Write` on protected tiers. The proposal interchangeably uses `surfaces_affected` (the frontmatter field) and "file list"; the actual enforcement field is `allowed_paths`. Verified both exist in docs, but only `allowed_paths` is enforced. In an autonomous loop, an agent that doesn't understand which field gates what will produce plans that pass `/plan` but don't constrain build. Before shipping, name the enforced field in the skill text and verify `/plan --auto` always emits it.

3. **UNDER-ENGINEERED** [MATERIAL] [COST:SMALL]: The proposal describes a "3-tier classification (Mechanical/Taste/User Challenge)" as if it already exists in the rules — `check_code_presence` for both `Mechanical` and `Taste` in `rules/` returns zero matches. It apparently lives only in the `plan` skill body. Reusing a decision framework across an autonomous build loop needs that framework to be durably specified somewhere a drifting skill edit can't delete. Either promote it to `.claude/rules/` or admit this is new surface, not reuse.

4. **RISK** [MATERIAL] [COST:SMALL]: The decompose gate is **advisory** (`hook-class: advisory`, emits `additionalContext`, does not deny). The proposal says parallel tracks "get worktree isolation (existing decompose gate behavior)" — but the gate only *nudges*; nothing forces worktrees. In a human-in-the-loop flow that's fine; in autonomous build with parallel tracks, two agents editing overlapping files without worktree isolation is a concrete corruption risk. Either (a) make worktree isolation mandatory in `--build` mode, or (b) forbid parallel tracks in v1 autobuild and make them sequential.

5. **RISK** [ADVISORY]: "Auto-invoke `/review`" — skills are invoked by the user in Claude Code, not programmatically by other skills. Search for `invoke /review` returns zero matches in skills. The handoff between `--build` completing and `/review` running needs a concrete mechanism (write a marker artifact? emit a prompt instructing the orchestrator?). Today the ship/review chain is explicit human-in-the-loop. Worth naming the mechanism, not hand-waving it.

6. **ASSUMPTION** [ADVISORY] [SPECULATIVE]: "Token cost: a full autobuild run could consume significant context." No data. The cost tracking exists (`_track_cost`, `get_session_costs` in `debate_common.py`) — instrument a dry-run against a small Build OS task first and publish the number before scoping v1. A $0.30 run and a $15 run justify very different guardrails.

7. **OVER-ENGINEERED** [ADVISORY]: "Estimated scope: ~60-80 lines added to plan/SKILL.md." This is the single biggest behavioral change in the system's history — taking ownership of the build loop — yet the delivery mechanism is a doc-edit to one skill. That estimate is credible only if you literally do nothing new and lean entirely on existing infra. Any of (worktree forcing, review handoff, autobuild cost caps, iteration state tracking) pushes this to SMALL/MEDIUM.

## Concessions

1. The diagnosis is right: the build phase *is* the gap, and the existing Escalation Protocol #5 ("three failures → stop") is a genuinely good fit for the iteration ceiling.
2. The "build it on Build OS itself, human reviews every PR" rollout plan is appropriately low-risk.
3. Acknowledging the gstack/CloudZero dependency on self-learning and then making it non-blocking ("human is the learning system") is a sound scope-reduction call.

## Verdict

**REVISE.** The proposal solves a real gap, but it silently contradicts `docs/orchestrator-contract.md` — which already defines this exact pipeline as external-runner territory. Before any code is written, the team needs to decide: *extend the orchestrator contract with a reference runner*, or *formally fold the runner role into BuildOS and rewrite the contract*. Until that choice is made and documented, a `--build` flag in `plan/SKILL.md` is architectural drift, not reuse.

Risk of NOT changing: the build phase stays manual — the diagnosed, genuine gap persists. That cost is real. But the fix should respect the contract that already exists, not bypass it via a skill edit.

---

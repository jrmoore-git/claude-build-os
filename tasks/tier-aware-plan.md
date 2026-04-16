---
scope: "Add tier-aware governance, scope containment, and orchestrator contract to BuildOS"
surfaces_affected:
  - CLAUDE.md
  - hooks/hook-*
  - .claude/skills/setup/SKILL.md
  - .claude/rules/orchestration.md
  - config/protected-paths.json
  - docs/orchestrator-contract.md
  - scripts/tier_classify.py
verification_commands:
  - "python3.11 -m pytest tests/ -x"
  - "grep 'buildos-tier' CLAUDE.md"
verification_evidence: "PENDING"
rollback: "git revert HEAD~N to the commit before this work"
review_tier: "tier1"
---

# Plan: Tier-Aware BuildOS

## Background

Cross-model explore (4 directions, unanimous) identified three changes BuildOS should make based on external feedback from CloudZero's velocity analysis. All four directions agreed on scope.

## Track 1: Tier field in CLAUDE.md + tier-aware hooks

**Problem:** Nothing prevents deploying T2 governance (21 hooks, 22 skills, session docs) to a team that only needs T0 (CLAUDE.md only). This caused the C9 engineer rejection at CloudZero.

**Change:**

1. Add a `tier:` field to CLAUDE.md. Since CLAUDE.md doesn't use YAML frontmatter (it's pure markdown), use a structured HTML comment at the top:
   ```
   <!-- buildos-tier: 0 -->
   ```
   Parseable by hooks but invisible to Claude's context loading.

2. Create a shared helper `scripts/read_tier.py` that reads the declared tier from CLAUDE.md. Every tier-gated hook calls this. Returns 0/1/2/3 (default: 3 if no declaration — fail closed to maximum governance).

3. Modify hooks to self-disable when above declared tier:
   - **T0 hooks (always active):** hook-guard-env.sh, hook-read-before-edit.py, hook-syntax-check-python.sh, hook-ruff-check.sh — basic safety, not governance.
   - **T1 hooks (tier >= 1):** hook-intent-router.py, hook-spec-status-check.py, hook-prd-drift-check.sh, hook-stop-autocommit.py
   - **T2 hooks (tier >= 2):** hook-tier-gate.sh, hook-review-gate.sh, hook-pre-edit-gate.sh, hook-plan-gate.sh, hook-pre-commit-tests.sh, hook-post-tool-test.sh, hook-decompose-gate.py, hook-agent-isolation.py, hook-memory-size-gate.py, hook-skill-lint.py, hook-error-tracker.py, hook-bash-fix-forward.py

4. Update `/setup` (Step 2) to write the tier declaration into CLAUDE.md after the user picks a tier.

**Verification:** Set tier to 0, attempt a commit without debate artifacts — should not block. Set tier to 2, same attempt — should block.

## Track 2: Scope field + enforcement hook

**Problem:** `hook-agent-isolation.py` enforces worktree isolation (agents can't collide) but nothing enforces "this agent may only modify files within declared paths."

**Change:**

1. Add `allowed_paths` as an optional field in plan frontmatter (alongside existing `surfaces_affected`). If present, the pre-edit hook denies writes outside these paths.

2. Modify `hook-pre-edit-gate.sh` to check `allowed_paths` in the active plan. If the plan has `allowed_paths` and the target file doesn't match any entry, block.

3. Allow explicit override: `scope_escalation: true` in frontmatter makes the hook warn instead of block. Audit trail for when an agent needed to go outside scope.

**Verification:** Create a plan with `allowed_paths: ["src/analytics/*"]`, attempt to edit `src/billing/foo.py` — should block.

## Track 3: Orchestrator contract doc

**Problem:** BuildOS skill chain requires a human to drive transitions. For autonomous agents, an external runner drives the loop. BuildOS should define what that runner must satisfy, without building the runner itself.

**Change:**

Write `docs/orchestrator-contract.md` defining:
- **Input:** Task spec format (required fields, what the runner reads)
- **Gates:** What artifacts must exist before each skill accepts work
- **Outputs:** What each skill produces (plan.md, review.md, ship-summary.md)
- **State transitions:** plan -> build -> review -> ship, with allowed loops
- **Escalation points:** When the runner must stop and hand to a human (the 7 triggers from workflow.md)
- **Success/failure signals:** Exit codes, artifact presence, frontmatter fields

Doc only. No code, no hooks, no enforcement.

## Execution order

Track 3 is independent. Track 2 depends on Track 1 (scope hook should be tier-aware).

1. Track 3 (orchestrator doc)
2. Track 1 (tier field + hook changes)
3. Track 2 (scope enforcement)

## Out of scope

- Autonomous execution loop (all models agreed: not BuildOS's job)
- Conformance tests (second-order — get primitives first)
- Mode-based packaging splits (later)

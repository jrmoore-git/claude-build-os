# Review Protocol

A 3-stage quality assurance process that uses cross-model evaluation to catch issues before they reach production. Each stage answers a different question, and the user chooses which stages to run based on the nature of the change.

## The 3-Stage Skill Chain

### Stage 1: `/challenge` -- Should we build this?

A cross-model gate that runs BEFORE planning. Three models independently evaluate whether the proposed work is necessary and appropriately scoped.

**Purpose:** Prevent unnecessary features, over-engineered abstractions, and scope creep before any code is written.

**When to run:**
- New features or capabilities
- New abstractions or architectural layers
- Scope expansion of existing features
- Adding new dependencies

**When to skip:**
- Bugfixes, test additions, documentation updates
- Trivial refactors with obvious scope
- Use `/plan --skip-challenge` to bypass

**Output:** `tasks/<topic>-challenge.md` containing each model's independent evaluation and a recommendation: proceed, simplify, pause, or reject.

### Stage 2: `/debate` -- How should we build it?

A full adversarial pipeline that produces a refined specification. The flow is: challenge -> judge -> refine.

**Purpose:** Force architectural decisions through multi-perspective scrutiny before implementation begins.

**When to run:**
- Architectural decisions with multiple valid approaches
- PRD or schema changes
- Design uncertainty where reasonable people disagree

**When to skip:**
- Simple features where the approach is obvious
- Changes that don't involve architectural choices

**Output:** Three artifacts:
- `tasks/<topic>-debate.md` -- the adversarial arguments
- `tasks/<topic>-judgment.md` -- the judge's ruling with rationale
- `tasks/<topic>-refined.md` -- the refined spec incorporating the judgment

### Stage 3: `/review` -- Is the implementation correct?

Cross-model code review where three models examine the diff through independent lenses: PM (does it match the spec?), Security (does it introduce vulnerabilities?), and Architecture (is it well-structured?).

**Special behavior:** If `tasks/<topic>-refined.md` exists from a prior debate, the PM lens escalates to strict spec compliance -- every requirement in the refined spec must be addressed.

**When to run:** Every non-trivial change, before commit.

**Output:** `tasks/<topic>-review.md` with findings categorized as BLOCKING (max 5), CONCERNS (max 5), and VERIFIED (bullet list).

## Typical Paths by Change Type

| Change type | Path |
|---|---|
| Bugfix | `/plan --skip-challenge` -> build -> `/review` -> `/ship` |
| Small feature | `/challenge` -> `/plan` -> build -> `/review` -> `/ship` |
| Architectural change | `/challenge` -> `/plan` -> `/debate` -> build -> `/review` -> `/ship` |

## The Cross-Model Debate Engine

The engine (`scripts/debate.py`) powers all three stages. It sends the same prompt to multiple models from different model families and synthesizes their responses.

### Model Selection Principles

- **Use at least three models from different families.** This prevents self-preference bias where a model rates its own output higher.
- **Assign the judge role to a different family than the author.** The judge should be the empirically strictest reviewer.
- **Rotate all models through refinement.** Each model contributes to the final refined spec.
- **Always include a PM challenger.** Product perspective catches scope drift and spec violations that technical reviewers miss.

### Security Veto

Security has a BLOCKING VETO on external code changes. This veto is not subject to PM override or any other tiebreaker. When external code wants access to user data, security paranoia is the correct posture.

## Contract Tests

Every change must preserve the essential eight invariants:

1. **Idempotency** -- same operation twice = same result
2. **Approval gating** -- no unauthorized external actions
3. **Audit completeness** -- every state change is logged
4. **Degraded mode visible** -- failures are surfaced, not hidden
5. **State machine validation** -- only valid transitions allowed
6. **Rollback path exists** -- every change can be undone
7. **Version pinning enforced** -- no floating dependencies
8. **Exactly-once scheduling** -- no missed or double executions

See `docs/contract-tests.md` for test patterns and implementation details.

## Definition of Done

A change is done when:
- Behavior matches the spec
- Tests pass (`tests/run_all.sh`)
- Audit log shows expected events
- Rollback plan exists and has been documented
- Negative tests have been run (what should NOT happen)
- Review completed via `/review`

## Rule Enforcement

Rules that aren't enforced are suggestions. After writing a rule:

1. **Test it.** Deliberately try to violate it. If Claude doesn't catch the violation, the rule needs to be stronger.
2. **Escalate if needed.** Move the rule closer to the action point, add a commit hook, or make it architectural. A rule that depends on the LLM remembering it across a long context window will eventually be forgotten.
3. **Self-checking hooks.** Any enforcement hook must include its own file path in the set of files it checks -- a hook that doesn't check itself can be silently bypassed.

## Context Checkpoints

- At 60% context: STOP and run review if not done
- At 75%: run review NOW -- do not continue building

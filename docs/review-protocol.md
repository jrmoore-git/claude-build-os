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

### Stage 2: `/challenge --deep` -- How should we build it?

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

### Stage 3: `/check` -- Is the implementation correct?

Cross-model code review where three models examine the diff through independent lenses, each with a specific focus:
- **Architecture:** System design, component boundaries, data flow, scaling, integration risks
- **Security:** Trust boundaries, injection vectors (SQL, shell, prompt, XSS, SSRF), credential handling, exfiltration paths
- **PM/Acceptance:** User value, over-engineering, scope sizing, spec compliance (positive and negative)

Each reviewer tags quantitative claims with an evidence basis: **EVIDENCED** (cite specific data), **ESTIMATED** (state assumptions), or **SPECULATIVE** (no data — needs verification). Speculative claims alone cannot drive a material verdict. Reviewers evaluate **both directions of risk** — what could go wrong with the change AND what continues to fail without it.

**Spec compliance:** If `tasks/<topic>-refined.md` exists from a prior debate, the PM lens escalates to strict spec compliance. This includes **negative compliance** — extracting all EXCEPTION, MUST NOT, and EXPLICITLY EXCLUDED clauses from the spec and verifying the diff does not contradict them. Violations are tagged `[MATERIAL] SPEC VIOLATION:`.

**Modes:**
- `/check` — read-only findings report
- `/check --fix` — after review, auto-fix mechanical issues and present judgment calls for approval
- `/check --fix-loop` — automated fix → re-review cycle (max 3 iterations). Each iteration: apply fixes, re-run cross-model review. Stops when no material findings remain or after 3 iterations (whichever comes first). Escalates to manual review if findings persist.

**When to run:** Every non-trivial change, before commit.

**Output:** `tasks/<topic>-review.md` with findings categorized as MATERIAL (must fix) or ADVISORY (worth noting), grouped by lens.

## Typical Paths by Change Type

| Change type | Path |
|---|---|
| Bugfix | `/plan --skip-challenge` -> build -> `/check` -> `/ship` |
| Small feature | `/challenge` -> `/plan` -> build -> `/check` -> `/ship` |
| Architectural change | `/challenge` -> `/plan` -> `/challenge --deep` -> build -> `/check` -> `/ship` |

## The Cross-Model Debate Engine

The engine (`scripts/debate.py`) powers all three stages. It sends the same prompt to multiple models from different model families and synthesizes their responses.

### Automatic Challenge Consolidation

Before judging, multi-challenger findings are automatically consolidated. Overlapping findings from different challengers are deduplicated and merged into a unified list with corroboration notes (e.g., "Raised by 2/3 challengers"). This reduces redundancy and gives the judge cleaner input. Use `--no-consolidate` to skip this step and judge raw challenges individually (with position-bias shuffling applied instead).

### Model Selection Principles

- **Use all three model families as challengers.** This prevents self-preference bias where a model rates its own output higher. The default mapping assigns each family at least one persona: Claude Opus (architect), Gemini (staff + PM), GPT (security).
- **Assign the judge role to a different family than the author.** The judge (GPT by default) should be the empirically strictest reviewer. Since Claude is typically the code author, having Claude also judge its own work produces sycophantic results.
- **Avoid self-review bias.** Claude serves as architect (systems reasoning) while Gemini handles PM and staff roles. The judge (GPT) is always a different family from the typical Claude author.
- **Rotate all models through refinement.** Each model contributes to the final refined spec (gemini → gpt → claude rotation).
- **Always include a PM challenger.** Product perspective catches scope drift and spec violations that technical reviewers miss.

Model-to-persona assignments are configured in `config/debate-models.json` and can be changed without code modifications.

### Verifier Tools (--enable-tools)

When `--enable-tools` is passed to `debate.py challenge`, challengers get access to read-only verifier tools that let them check claims against the actual codebase:

- **check_function_exists** — Verify a function/class/subcommand exists at the stated location
- **check_test_coverage** — Find test files for a given source file
- **count_records** — Count rows in a SQLite table (no content access)
- **get_recent_costs** — Query API cost data from audit logs

These tools convert speculative claims into evidenced ones. A challenger saying "this function might not exist" can verify it directly. Tools are read-only — they cannot modify files or data.

### Proposal Quality Requirements

Debate proposals grounded in abstract risk analysis instead of empirical evidence produce wrong recommendations. Proposals must include:

1. **3+ concrete failure examples** from the current system (not hypothetical)
2. **Measured cost estimates** using actual operational parameters (frequency, batch size, rate limits)
3. **Tested baseline performance** of the "simpler alternative" before recommending it

The `/challenge` skill enforces a structured proposal template with sections for Current System Failures, Operational Context, and Baseline Performance. `debate.py` warns when these sections are missing.

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
- Review completed via `/check`

## Rule Enforcement

Rules that aren't enforced are suggestions. After writing a rule:

1. **Test it.** Deliberately try to violate it. If Claude doesn't catch the violation, the rule needs to be stronger.
2. **Escalate if needed.** Move the rule closer to the action point, add a commit hook, or make it architectural. A rule that depends on the LLM remembering it across a long context window will eventually be forgotten.
3. **Self-checking hooks.** Any enforcement hook must include its own file path in the set of files it checks -- a hook that doesn't check itself can be silently bypassed.

## Context Checkpoints

- At 60% context: STOP and run review if not done
- At 75%: run review NOW -- do not continue building

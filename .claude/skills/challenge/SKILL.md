---
name: challenge
description: "Cross-model challenge that pressure-tests whether proposed work is necessary and appropriately scoped before /plan. Use when proposing new abstractions, dependencies, infrastructure, or scope expansion."
version: 1.0.0
user-invocable: true
---

# /challenge — Should We Build This?

Question the premise, scope, and complexity of proposed work before committing to a plan. Runs a cross-model challenge via `debate.py` when available, produces durable artifacts on disk, and acts as a gate that `/plan` relies on.

## `--deep` Mode (Full Adversarial Pipeline)

`/challenge --deep` runs the full adversarial pipeline: challenge → judge → refine. This is the old `/debate --validate` mode. Use when you need a scored verdict with independent judgment, not just a gate check.

```bash
# Step 1: Challenge (same as standard /challenge Step 7)
python3.11 scripts/debate.py --security-posture $POSTURE challenge \
  --proposal tasks/<slug>-proposal.md \
  --personas architect,security,pm \
  --enable-tools \
  --output tasks/<slug>-debate.md

# Step 2: Judge (independent evaluation)
python3.11 scripts/debate.py --security-posture $POSTURE judge \
  --proposal tasks/<slug>-proposal.md \
  --challenge tasks/<slug>-debate.md \
  --model gpt-5.4 \
  --verify-claims \
  --output tasks/<slug>-judgment.md

# Step 3: Refine (iterative cross-model improvement)
python3.11 scripts/debate.py refine \
  --document tasks/<slug>-proposal.md \
  --judgment tasks/<slug>-judgment.md \
  --rounds 3 \
  --output tasks/<slug>-refined.md
```

Each stage is independently valuable — stop at the step that fails. Partial artifacts are valid.

After `--deep`, suggest: "Build the implementation, then run `/review`"

## When to run

Run `/challenge` before `/plan` for any non-trivial change, especially when the proposal introduces:

- New abstractions: class, module, service, wrapper, adapter, plugin
- New dependencies: package, API, service, vendor integration
- New infrastructure: config, feature flag, schema, migration, routing
- Generalization: "reusable," "generic," "extensible," "future-proof"
- Scope expansion beyond the ask: cleanup, migration, speculative refactor

Line count and file count are not triggers. New concepts and irreversible scope are.

## Bypass rules

Skip `/challenge` entirely for:

- Bugfixes that restore intended behavior without adding new behavior
- Test-only changes
- Documentation or copy changes
- Refactors that reduce abstractions more than they add
- Tasks classified as `[TRIVIAL]` (2 or fewer files, no new abstraction/dependency, describable in one sentence)

If uncertain, do not bypass.

Log all bypasses: `[CHALLENGE-SKIPPED] <date> <topic> reason: <classification>`

## Phase 0: Context Assessment

Before starting the procedure, scan the conversation for context already established.

**Check each:**

| Signal | Look for | If found |
|--------|----------|----------|
| Topic | A proposal, design, or feature discussed in conversation | Use as topic — skip topic inference in Step 1. |
| Security posture | User mentioned risk level, production-grade, move-fast, etc. | Map to posture 1-5 — skip posture question in Step 1. |
| Proposal content | A plan, design doc, or detailed feature description already in conversation | Use as proposal source in Step 3 instead of asking user to write one. |

**Routing:**
- Topic + posture clear → skip Step 1 questions, proceed to Step 2 with inferred values.
- Proposal already in conversation → reference it in Step 3 instead of asking user to produce one.
- Nothing clear → full procedure as normal.

## Procedure

### Step 1: Resolve the topic and security posture

If the user supplied a topic, use it. Otherwise infer:

1. Most recent `tasks/*-design.md` or `tasks/*-think.md`
2. Most recent `tasks/*-elevate.md`
3. Current git branch name with common prefixes stripped

Only ask if all inference fails.

Convert the topic to a slug: lowercase, alphanumeric and hyphens only, matching `^[a-z0-9]+(-[a-z0-9]+)*$`. Reject slugs containing `/`, `\`, `..`, spaces, or absolute paths.

Ask: "Security posture? (1=move-fast, 2=speed-with-guardrails, 3=balanced, 4=production-grade, 5=critical). Default: 3"

Store the answer as `POSTURE` (default 3). Pass `--security-posture $POSTURE` to all `debate.py` commands.

**Shell safety:** Never interpolate user-provided topic text into shell commands. Pass file paths as direct arguments, never through string interpolation.

### Step 2: Check for prior context

Look for prior `/think` output:
- `tasks/<slug>-design.md`
- `tasks/<slug>-think.md`

If found, read for problem framing, constraints, and prior decisions.

### Step 3: Ensure a proposal exists

Check for `tasks/<slug>-proposal.md`.

If missing:
- If prior context exists from Step 2, synthesize from it.
- Otherwise ask the user to describe: what they want to build, why it matters, the proposed approach, and what they are not building.

The proposal must be self-contained. A challenger with no prior context should understand why this work matters, what already exists, and what is being proposed — without needing to read other files. The proposal is the challengers' primary input; everything they learn from tool calls is supplementary.

Write to `tasks/<slug>-proposal.md` using this standard template:

```markdown
---
topic: <slug>
created: <YYYY-MM-DD>
---
# <Title>

## Project Context
What the project is and what problem it solves (1-2 sentences). Key system components relevant to this proposal — not an exhaustive architecture doc, just what challengers need to evaluate the proposal.

## Recent Context
What led to this proposal: the last 2-3 sessions of relevant work, decisions made, pivots taken. Pull from session-log.md, decisions.md, or conversation history. This gives challengers the arc — why now, what was tried, what changed.

## Problem
What is broken or missing, who it affects, and why it matters now.

## Proposed Approach
What to build and how. Non-goals: what this deliberately excludes.

## Simplest Version
The cheapest test or MVP that validates the idea before full build.

### Current System Failures
3+ concrete examples of the problem occurring. Include dates, error messages, or user reports where available. If no failures exist yet (greenfield), state that explicitly.

### Operational Context
Real numbers from the running system relevant to this proposal. Pull from debate-log.jsonl, cron schedules, cost data, or metrics.db as applicable. Examples: "debate.py runs ~5-10 times/day, 95 entries in debate-log.jsonl" or "email-triage processes ~40 emails/day, 3 errors in last 7 days." If the proposal doesn't touch operational systems, state "N/A — greenfield."

### Operational Evidence
Has any version of this approach been tried before? Include: what was tried, what happened, what data exists (eval results, metrics, session log entries), and the before/after on the dimension this proposal changes. If no prior attempt exists (net-new idea), state "No prior attempts." If a bespoke or manual version already delivered results, this is the strongest evidence for the proposal — omitting it causes challengers to evaluate in a vacuum.

### Baseline Performance
How the current system performs on the dimension this proposal changes. Include: current behavior, current cost, current error rate. Required when the proposal replaces or modifies an existing system. If greenfield, state "No existing system."
```

Every proposal should include all sections. `debate.py` will warn on missing `Current System Failures`, `Operational Context`, or `Baseline Performance` sections — these provide the grounding that prevents challengers from fabricating numbers.

### Step 4: Enrich context (optional)

If `scripts/enrich_context.py` exists, run it to pull relevant decisions and lessons:

```bash
python3.11 scripts/enrich_context.py --proposal tasks/<slug>-proposal.md --scope challenge
```

If the script is missing, errors, or returns nothing, continue with the raw proposal. Do not mutate `tasks/<slug>-proposal.md`. If enrichment succeeds, append a `## Prior Context` section to a working copy used as debate input.

### Step 5: Determine review mode

**Local-only mode:** User explicitly requests it, or proposal contains secrets. Skip multi-model review. Proceed to Step 6, then Step 8. Mark artifact `review_backend: local-only`. This is an operator choice, not degraded.

**Standard mode:** `debate.py` is available. Proceed to Step 6, then Step 7, then Step 9.

**Degraded fallback:** `debate.py` unavailable or fails. Classify proposal risk from content:
- **Tier 1 (fail closed):** Security, auth, schema, infrastructure, unclear risk. Stop and report.
- **Tier 2/3 (degrade allowed):** Bounded features, local refactors, clear rollback. Proceed to Step 6, then Step 8 with `[DEGRADED]` banner.

When risk cannot be classified confidently, default to Tier 1.

### Step 6: Select personas

Always: **architect**, **security**, **pm**.

Add dynamically based on proposal content:
- **product** if the proposal changes user-facing behavior or workflows
- **design** if the proposal affects UI or frontend experience

### Step 7: Run cross-model challenge

```bash
python3.11 scripts/debate.py --security-posture $POSTURE challenge \
  --proposal <enriched or raw proposal> \
  --personas architect,security,pm[,product][,design] \
  --enable-tools \
  --output tasks/<slug>-findings.md
```

Write raw output to `tasks/<slug>-findings.md`. Do not write to `-challenge.md` — that is synthesized in Step 9.

**Minimum coverage:** At least 2 responders must return usable findings. If fewer than 2: Tier 1 stops, Tier 2/3 degrades to Step 8.

If `debate.py` fails entirely, apply fallback from Step 5.

### Step 8: Single-model review

Runs for local-only mode or degraded fallback. Review the proposal skeptically through Step 6 personas. Focus on: whether the problem is real, whether the approach is oversized, simpler alternatives, non-goals, deletion cost, evidence gaps.

Write findings to `tasks/<slug>-findings.md`. If degraded (not local-only), mark with `[DEGRADED: single-model fallback]`.

### Step 9: Synthesize the challenge artifact

Read the proposal, prior context, enrichment, and findings.

**For each MATERIAL finding, assess implementation cost:**

| Cost | Criteria | Effect on recommendation |
|---|---|---|
| **Trivial** (<20 lines, no new deps) | Fix is mechanical, any senior engineer would apply without discussion | Finding becomes an inline fix, not a blocker |
| **Small** (20-100 lines, contained) | Fix requires thought but is bounded to existing patterns | Finding is a condition on PROCEED, not a reason to SIMPLIFY |
| **Medium** (100+ lines or new concept) | Fix introduces new patterns, abstractions, or dependencies | Finding may justify SIMPLIFY if it outweighs the feature value |
| **Large** (new subsystem or infrastructure) | Fix requires work that doesn't exist yet | Finding justifies PAUSE or phased approach |

**Weigh both directions of risk:** What happens if we build this (challenger findings) AND
what continues to fail if we don't (cost of inaction from the proposal's "Current System
Failures" section). A recommendation to defer must name what stays broken.

Write `tasks/<slug>-challenge.md` following the structure in `templates/challenge-artifact.md`.

Artifact roles must stay separate:
- `-proposal.md` = input
- `-findings.md` = raw challenge output
- `-challenge.md` = synthesized gate artifact for `/plan`

### Step 10: Report result

Display:

```text
## Challenge Result: <PROCEED|PROCEED-WITH-FIXES|SIMPLIFY|PAUSE|REJECT>

<1-3 sentence summary>

[If PROCEED-WITH-FIXES:]
Inline fixes to include in build:
1. [finding] → [fix, ~N lines]
2. [finding] → [fix, ~N lines]

Artifacts:
- tasks/<slug>-challenge.md
- tasks/<slug>-findings.md

Next:
- /plan <topic>     (if proceed or proceed-with-fixes)
- revise scope, then /plan <topic>   (if simplify)
- address findings first   (if pause/reject)
```


## Recommendation guidance

- **proceed** — no material objections, or all material findings have trivial inline fixes
- **proceed-with-fixes** — material findings exist but each fix is under ~20 lines of code.
  List the fixes to include in the build. Do NOT defer to a later phase — if the fix is
  trivial, it ships with the feature.
- **simplify** — valid idea, but the approach is fundamentally oversized. The core feature
  should be smaller, not just patched.
- **pause** — missing evidence or unresolved prerequisite that can't be fixed inline
- **reject** — should not be built as proposed

**Anti-pattern: conservative deferral.** If a MATERIAL finding's fix is straightforward
(under ~20 lines, no new dependencies, no architectural change), the correct recommendation
is PROCEED-WITH-FIXES, not SIMPLIFY. Deferring trivially-fixable work behind "Phase 2"
gates produces busywork phases with no real payoff.

If findings conflict across personas, surface the tension explicitly.

## Complexity score

Derive from concepts and reversibility, not line count:
- **low** — existing patterns, little new surface
- **medium** — one new concept with clear justification
- **high** — multiple new concepts, high deletion cost, speculative need

## Rules

- Write artifacts to disk, not just conversation.
- **Challenge the premise, but weigh both sides.** Skepticism about building is useful.
  Skepticism that ignores the cost of NOT building is incomplete. Every deferral must
  name what stays broken.
- **Prefer the smallest reversible step** — but don't confuse "smallest" with "none."
  If the smallest step is a 50-line script that closes a real gap, that's the right scope.
  Deferring it to a hypothetical Phase 2 is not simpler — it's slower.
- **MATERIAL ≠ blocker.** A MATERIAL finding with a trivial fix is a build condition,
  not a reason to downgrade the recommendation. Only findings that require substantial
  new work (new subsystems, missing infrastructure, architectural changes) justify
  SIMPLIFY or PAUSE.
- Do not embed operational shell recipes; scripts own execution details.
- Preserve the distinction between local-only (operator choice) and degraded (backend failure).
- If risk or coverage is unclear, choose the safer path.

## Safety Rules

- NEVER skip challenge findings to proceed faster.
- NEVER auto-approve proposals — all gate decisions require explicit recommendation with evidence.
- Do not suppress minority viewpoints from challengers.
- **Output silence** — Do not emit text between tool calls. Single formatted output at the end only.

## Output Format

The primary output is `tasks/<slug>-challenge.md` containing the synthesized gate artifact. The conversation output follows the format in Step 10: recommendation (PROCEED/PROCEED-WITH-FIXES/SIMPLIFY/PAUSE/REJECT), summary, inline fixes if applicable, artifact paths, and next steps.

## Completion

Report status:
- **DONE** — All steps completed successfully.
- **DONE_WITH_CONCERNS** — Completed with issues to note.
- **BLOCKED** — Cannot proceed. State the blocker.
- **NEEDS_CONTEXT** — Missing information needed to continue.

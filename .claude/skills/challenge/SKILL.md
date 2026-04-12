---
name: challenge
description: "Cross-model challenge that pressure-tests whether proposed work is necessary and appropriately scoped before /plan."
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

After `--deep`, suggest: "Build the implementation, then run `/check`"

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

Write to `tasks/<slug>-proposal.md` using this standard template:

```markdown
---
topic: <slug>
created: <YYYY-MM-DD>
---
# <Title>

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

Read the proposal, prior context, enrichment, and findings. Write `tasks/<slug>-challenge.md` following the structure in `templates/challenge-artifact.md`.

Artifact roles must stay separate:
- `-proposal.md` = input
- `-findings.md` = raw challenge output
- `-challenge.md` = synthesized gate artifact for `/plan`

### Step 10: Report result

Display:

```text
## Challenge Result: <PROCEED|SIMPLIFY|PAUSE|REJECT>

<1-3 sentence summary>

Artifacts:
- tasks/<slug>-challenge.md
- tasks/<slug>-findings.md

Next:
- /plan <topic>     (if proceed)
- revise scope, then /plan <topic>   (if simplify)
- address findings first   (if pause/reject)
```

After displaying the result, update the pipeline manifest:

```bash
python3.11 scripts/pipeline_manifest.py add <slug> --skill challenge --artifact tasks/<slug>-challenge.md --status complete --recommendation <PROCEED|SIMPLIFY|PAUSE|REJECT>
```

## Recommendation guidance

- **proceed** — no material objections from any persona
- **simplify** — valid idea, oversized approach; plan the simpler alternative
- **pause** — missing evidence or unresolved prerequisite
- **reject** — should not be built as proposed

If findings conflict across personas, surface the tension explicitly.

## Complexity score

Derive from concepts and reversibility, not line count:
- **low** — existing patterns, little new surface
- **medium** — one new concept with clear justification
- **high** — multiple new concepts, high deletion cost, speculative need

## Rules

- Write artifacts to disk, not just conversation.
- Be skeptical by default — challenge the premise before endorsing.
- Prefer the smallest reversible step.
- Do not embed operational shell recipes; scripts own execution details.
- Preserve the distinction between local-only (operator choice) and degraded (backend failure).
- If risk or coverage is unclear, choose the safer path.

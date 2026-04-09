---
name: challenge
description: Challenge whether proposed work is necessary and appropriately scoped before planning
user-invocable: true
---

# Challenge Before Building

Question the premise, scope, and complexity of proposed work before committing to a plan. Produces a written artifact that `/plan` checks as a dependency.

## When this runs

### Automatically (as a /plan dependency)
`/plan` invokes `/challenge` when the proposed work includes **any** of:
- **New abstractions**: new class, module, service, base class, wrapper, adapter, or plugin
- **New dependencies**: new package, external API, or service integration
- **New infrastructure**: new config surface (env vars, feature flags), schema change, or routing change
- **Generalization**: plan aims to make something "generic," "reusable," "extensible," or "future-proof"
- **Scope expansion**: work beyond the stated ask — cleanup, migration, speculative refactor

A single trigger is enough. One new external dependency is sufficient reason to challenge.

Line count and file count are **not triggers**. Complexity accretes through new concepts, not through editing existing code.

### Manually (standalone)
Run `/challenge` anytime to pressure-test an idea before investing in planning. Standalone invocations produce the same artifact with the same authority — there is no "advisory-only" mode.

## Procedure

### Step 1: Identify what's being proposed
Read the user's request. Understand what they're asking for and what scope the implementation implies.

### Step 2: Answer these questions (exactly these, in order)

**Product challenge (should we build this?):**
1. What problem are we solving? For whom?
2. What evidence exists that this matters?
3. What is the cheapest test of whether this works?
4. What should we explicitly NOT build?

**Complexity challenge (is the approach too heavy?):**
5. What is the simplest version that doesn't introduce new abstractions? Describe it concretely — this becomes the fallback if recommendation is `simplify`.
6. What new concepts are being introduced, and why can't existing patterns handle it?
7. What does this cost to delete if it turns out to be wrong?
8. Is this solving a problem we have, or a problem we might have?

### Step 3: Write the artifact

Create `tasks/<topic-slug>-challenge.md`:

```markdown
---
topic: [topic name]
topic_slug: [lowercase-hyphenated — must match plan filename slug]
date: [ISO 8601]
type: challenge-preflight
triggers_fired: [list what triggered — e.g., "new module, new dependency"]
recommendation: proceed | simplify | pause | reject
complexity_score: low | medium | high
---

# Challenge: [topic]

## Product
1. Problem/user: [answer]
2. Evidence: [answer]
3. Cheapest test: [answer]
4. Non-goals: [answer]

## Complexity
5. Simplest version: [answer]
6. New concepts and justification: [answer]
7. Deletion cost: [answer]
8. Real vs speculative need: [answer]

## Simpler alternative
[Concrete description of the simplest implementation from Q5. This is what /plan must use if recommendation is "simplify". Not a vague gesture — specific enough to plan against.]

## Recommendation
[proceed | simplify | pause | reject] — [one sentence rationale]

## Override
[Blank unless user overrides a non-proceed recommendation.]
- Justification: [required — why override is warranted]
- Logged to decisions.md: [yes/no — must be yes before /plan proceeds]
```

### Step 4: State the recommendation

- **proceed** — work is justified, scope is appropriate
- **simplify** — the goal is valid but the approach is overengineered. The "Simpler alternative" section becomes the plan's scope.
- **pause** — insufficient evidence this matters. Define what evidence would change the answer.
- **reject** — this shouldn't be built. Explain why.

**Complexity score** (derived from answers, not line count):
- **low** — editing existing patterns, no new concepts
- **medium** — one new abstraction with clear justification
- **high** — multiple new concepts, speculative need, or high deletion cost

## How /plan uses this

When `/plan` detects work that meets any trigger:
1. Check for `tasks/<topic-slug>-challenge.md`
2. Verify the artifact is **less than 7 days old**
3. Verify `topic_slug` matches the plan's topic slug **exactly** (no fuzzy matching)
4. Read the recommendation:
   - `proceed` → continue planning
   - `simplify` → plan must implement the "Simpler alternative" section, not the original scope
   - `pause` → hard stop. Surface what evidence is needed.
   - `reject` → hard stop. Do not plan.
5. If artifact is missing, stale, or slug-mismatched → run `/challenge` first
6. If artifact has missing required sections → run `/challenge` again

Override: user provides justification in the artifact's Override section AND it is logged to `decisions.md` before `/plan` proceeds. Override is allowed for `simplify` and `pause`. Override for `reject` requires explicit acknowledgment that the rejection rationale was considered.

## Bypass rules

Skip `/challenge` entirely for:
- Bugfixes (fixing broken behavior, not adding new behavior)
- Test-only changes
- Documentation and copy changes
- Refactors that **reduce** abstractions (deleting > adding)
- Tasks marked `[TRIVIAL]`

**`[TRIVIAL]` defined:** changes to 2 or fewer files, introduces no new abstractions or dependencies, and can be fully described in one sentence. If you can't describe it in one sentence, it's not trivial.

All bypasses are logged: `[CHALLENGE-SKIPPED] <date> <topic> reason: <classification>`

## Rules
- The artifact goes to disk, not conversation. It must survive session compaction.
- No free-form strategy memos. Answer the 8 questions, write the simpler alternative, state the recommendation.
- Anti-sycophancy: the default posture is skepticism, not agreement. Challenge the premise before accepting it.
- When answers are contradictory (strong evidence + high deletion cost + speculative need), surface the tension explicitly rather than forcing a single recommendation.

# Resolution: Build OS 48-Hour Lessons

## Response to Challenges

### Challenge A1 (staff): E2E test not always feasible — nondeterministic deps, async, flakiness
**Concede.** The integration gate should acknowledge that not all systems can run a deterministic E2E test at deploy time. Add guidance: "If a full end-to-end test isn't feasible (async pipelines, third-party APIs, eventual consistency), document a manual verification checklist with specific checkpoints. The principle is: verify at the integration boundary, using whatever mechanism fits your architecture."

### Challenge A2 (staff): Deploy script needs rollback/cleanup/timeout guidance
**Concede.** The pattern section should note: "The script must be idempotent (safe to re-run), clean up synthetic fixtures, and have a clear failure message that tells you where to look. If partial restart leaves the system in a bad state, the script should include a rollback step or at minimum stop before making things worse."

### Challenge A3 (staff): "Skip to architecture" is too aggressive after one incident
**Compromise.** The challenger is right that "someone forgot" can have multiple root causes. But the core insight holds: procedural steps that are purely mechanical should be automated, not governed by advisory rules. Revised language: "For failures that are purely procedural (restart a service, run a test suite), automation is the correct response — not stronger advisory language. The three-strikes rule applies to judgment calls. Procedural steps should be automated on first failure if they're cheap to automate."

### Challenge A4 (staff): CI/CD is more portable than "deploy script"
**Compromise.** The principle is correct — "enforce integrated verification at the system boundary" is more portable than "write a deploy script." But for the Build OS audience (many of whom are solo or small-team, not running CI/CD), the deploy script is the most accessible instantiation. Revised: frame the principle first ("enforce integrated verification at the system boundary"), then offer the deploy script as one concrete implementation.

### Challenge A5 (staff): Shared constants increase coupling
**Concede.** Drop Change 4 entirely. This is standard DRY advice, and as Challenger B also noted, it dilutes the Build OS's unique value. The Build OS should teach LLM governance and verification, not basic software engineering.

### Challenge A6 (staff): Integration gate + C9 are duplicative
**Concede.** Drop C9 (Change 6). Keep the Definition of Done checklist item (Change 1). Both challengers agree.

### Challenge A7 (staff): Session-log trigger needs better thresholds
**Compromise.** Keep the concrete triggers ("lost context for the first time" and "~10 sessions") but add the challenger's observable symptoms as additional signals: "You also need it when handoff reconstruction takes more than a few minutes, or when prior decisions get relitigated because nobody can find when they were made."

### Challenge B1 (PM): C9 dilutes contract tests
**Concede.** Already dropped per A6 agreement.

### Challenge B2 (PM): Enforcement ladder doesn't need branching logic
**Concede.** Instead of adding "skip levels" branching to the ladder, add a single clarifying sentence: "Procedural steps (restart, rebuild, run tests) should be automated immediately — they are not judgment calls and do not need the three-strikes progression." This is simpler than branching logic and communicates the same insight.

### Challenge B3 (PM): Shared constants is basic DRY
**Concede.** Already dropped per A5 agreement.

---

## Revised Change List

After concessions:

| # | Change | Status |
|---|--------|--------|
| 1 | Integration gate in Definition of Done | KEEP — with feasibility caveat (A1) |
| 2 | Enforcement ladder "skip levels" | REVISE — single sentence clarification, not branching logic (B2) |
| 3 | Deploy script as enforcement pattern | KEEP — reframe as principle first, script as one implementation (A4) |
| 4 | Shared query constants | DROP — basic DRY, not Build OS scope (A5, B3) |
| 5 | Session-log trigger | KEEP — with additional observable symptoms (A7) |
| 6 | C9 contract test | DROP — redundant with DoD item (A6, B1) |

**Net: 4 changes survive (1, 2, 3, 5), 2 dropped (4, 6).**

---

## Revised Content for Each Surviving Change

### Change 1 (revised): Integration gate

Add to the-build-os.md Part VII, after contract tests:

```markdown
### Integration gate

A feature is not done until data flows through every process in the
production path and a deterministic test proves it. Component tests
validate assumptions. Integration tests validate reality.

For features that touch multiple processes:

1. Write at least one test that injects a fixture at the input boundary
   and verifies it at the final output surface
2. Run this test as part of the deploy/ship process — not as a separate
   manual step
3. If a full end-to-end test isn't feasible (async pipelines, third-party
   APIs, eventual consistency), document a manual verification checklist
   with specific checkpoints at each integration boundary

The test must be idempotent, clean up its fixtures, and produce a clear
pass/fail signal.
```

Add to Definition of Done checklist:

```markdown
- [ ] Integration test verifies data flows end-to-end (or manual checklist exists)
```

### Change 2 (revised): Enforcement ladder clarification

Add one sentence to Part V after the three-strikes rule paragraph:

```markdown
Procedural steps (restart a service, rebuild, run a test suite) should
be automated immediately — they are not judgment calls and do not benefit
from the three-strikes progression. Reserve three-strikes for failures
that involve discretion.
```

### Change 3 (revised): Verification at the system boundary

Add to Part IX (Patterns Worth Knowing):

```markdown
### Enforce verification at the system boundary

When a system has multiple processes that must coordinate (API + database +
frontend, pipeline + model + output), wrap the deploy/ship sequence in a
single executable path that stops on first failure.

The principle: the deploy process IS the definition of done. If you can
declare "done" without the verification passing, the verification is
advisory — Level 1 on the enforcement ladder.

One concrete implementation: a deploy script that restarts each component
in dependency order, health-checks each one, then runs integration tests
against the running system. But the same principle applies to CI/CD
pipelines, Makefiles, or any executable gate. What matters is that
verification runs automatically and blocks the "done" declaration.

The script should be idempotent (safe to re-run), clean up synthetic
fixtures, and produce clear failure messages. If partial restart can leave
the system in a bad state, include a rollback step.
```

### Change 5 (revised): Session-log trigger

Replace "add when complexity demands" in Part VIII Bootstrap with:

```markdown
- `tasks/session-log.md` — add when you've lost context between sessions
  for the first time, when you have more than ~10 sessions and find
  yourself re-explaining prior decisions, or when handoff reconstruction
  takes more than a few minutes. Until then, handoff.md + current-state.md
  + lessons.md covers the same ground more precisely. Session-log becomes
  valuable when you need temporal search — before that, it's just growing
  text.
```

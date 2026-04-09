# Proposal: Build OS Updates from 48-Hour Integration Lessons

## Context

Over 48 hours, 4 incidents shared a root cause: features passed component-level tests but no integration test verified data flowed through all processes end-to-end. The fixes were:

1. `deploy_all.sh` — single command: restarts all services + runs 22 verification checks. Stops on first failure.
2. Pipeline canary test — synthetic fixture injected through full pipeline, verified at API layer.
3. Health daemon expanded to monitor 14 services (added MCP server + frontend app).
4. Shared query constants prevent schema-query drift across API endpoints.
5. CLAUDE.md hard rule — deploy_all.sh is the only path to "done."

The enforcement ladder played out exactly as documented:
- Level 1 (advisory rules) → ~50% compliance (gateway restart was documented but forgotten)
- Level 2 (hooks) → dropped per debate (wrong enforcement point for this class of failure)
- Level 3 (architecture) → 100% enforcement (deploy script + canary test)

A colleague also noted: session-log is in the Build OS file structure template but the recall skill doesn't reference it. Should there be a concrete trigger for when to add it?

---

## Proposed Changes

### Change 1: Add "Integration gate" to the Build OS Definition of Done

**Where:** `docs/the-build-os.md` Part VII (Review and Testing), and `templates/review-protocol.md`

**Current state:** The Definition of Done says "Tests pass" but doesn't distinguish component tests from integration tests. The Testing Layers section (advanced-patterns.md §3) documents smoke tests as a concept but doesn't tie them to the deploy/done gate.

**Proposed addition to the-build-os.md, Part VII, after the contract tests section:**

```markdown
### Integration gate

A feature is not done until data flows through every process in the production
path and a deterministic test proves it. Component tests and contract tests are
necessary but insufficient — they validate assumptions, which may be wrong.

For any feature that touches multiple processes (API → database → frontend,
or pipeline → model → output):

1. Write at least one end-to-end test that injects a synthetic fixture and
   verifies it at the final output surface
2. Run this test as part of the deploy/ship process, not as a separate manual step
3. If the test can't run automatically, the feature requires a documented
   manual verification checklist

The deploy script is the enforcement mechanism, not documentation. If you skip
the script, the test hasn't passed.
```

**Proposed addition to Definition of Done checklist:**

```markdown
- [ ] Integration test verifies data flows through all processes end-to-end
```

**Rationale:** This is generally applicable. Any multi-process system (not just OpenClaw) can pass unit tests while the integration is broken. The "mocks that validated the bug" story in the README already tells this exact lesson — but the Definition of Done doesn't require the fix.

---

### Change 2: Add "Enforcement ladder shortcut" guidance

**Where:** `docs/the-build-os.md` Part V (The Enforcement Ladder), as a new subsection

**Proposed addition:**

```markdown
### When to skip levels

The ladder is a diagnostic tool, not a mandatory progression. For failures
where compliance genuinely matters and the blast radius is material:

- **Skip straight to architecture (Level 4)** when the failure mode is
  "someone forgot" rather than "someone disagreed." Forgetting to restart
  a service is not a judgment call — it's a checklist item. Embed it in a
  script. Advisory rules don't fix forgetfulness.

- **Skip hooks (Level 3)** when the enforcement point is wrong. A pre-commit
  hook can't verify that a service restarted correctly. A deploy script can.
  Match the enforcement mechanism to the failure mode.

The three-strikes rule still applies for judgment-based failures (code style,
review quality, documentation discipline). But for procedural compliance,
one strike at Level 1 is enough evidence to escalate to Level 3 or 4.
```

**Rationale:** The published Build OS says "three-strikes rule" for escalation. Our experience shows that for procedural steps (restart service, run integration test), even one failure at Level 1 justifies immediate escalation. The three-strikes rule is right for judgment calls, wrong for checklists.

---

### Change 3: Add "Deploy script as enforcement" pattern

**Where:** `docs/the-build-os.md` Part IX (Patterns Worth Knowing), as a new pattern

**Proposed addition:**

```markdown
### The deploy script as enforcement mechanism

When a system has multiple processes that must be restarted, rebuilt, or
verified together, wrap the entire sequence in a single script that stops
on first failure. This is Level 4 enforcement — the developer (human or
Claude) cannot declare "done" without the script passing.

The pattern:
1. Restart/rebuild each component in dependency order
2. Health-check each component after restart
3. Run integration tests against the running system
4. Stop on first failure with a clear error message

What makes this work: the script IS the definition of done. Documentation
that says "remember to restart the MCP server" is Level 1. A script that
restarts it, health-checks it, and runs a canary test is Level 4.

This pattern emerged from 4 incidents in 48 hours where features passed
component tests but failed in production because a downstream process
wasn't restarted or wasn't tested end-to-end.
```

**Rationale:** Generally applicable to any multi-service project. The pattern is simple, concrete, and directly actionable.

---

### Change 4: Add "Shared constants prevent drift" pattern

**Where:** `docs/advanced-patterns.md`, in the Testing Layers section or as a new Patterns section

**Proposed addition:**

```markdown
### Shared query constants

When the same database query or data shape is used across multiple
processes (API server, frontend, test suite), extract the query/shape
into a shared constant. Schema changes then propagate automatically
instead of requiring manual updates to each consumer.

This prevents a specific failure class: the schema evolves, the API
query is updated, but the frontend or test suite still uses the old
shape. Tests pass (they test their own assumptions) while the live
system fails silently.

This is the same lesson as "the mocks that validated the bug" — but
applied to query definitions rather than API response shapes.
```

**Rationale:** Generally applicable. Any system with multiple consumers of the same data benefits from DRY query definitions.

---

### Change 5: Add session-log trigger to the Build OS

**Where:** `docs/the-build-os.md` Part VIII (Bootstrap), in the "Add when complexity demands" list

**Current state:** Session-log is in the template directory but listed vaguely under "add when complexity demands."

**Proposed change:** Replace the vague guidance with a concrete trigger:

```markdown
- `tasks/session-log.md` — add when you've lost context between sessions
  for the first time, or when you have more than ~10 sessions and find
  yourself re-explaining prior decisions. Until then, handoff.md +
  current-state.md + lessons.md covers the same ground more precisely.
  Session-log becomes valuable when you need temporal search ("what did
  we do last Tuesday?") — before that, it's just growing text.
```

**Rationale:** Direct user feedback from a colleague. The current guidance is too vague. This gives a concrete "you need this when..." trigger, consistent with how governance tiers have upgrade triggers.

---

### Change 6: Add 9th contract test — "End-to-end data flow"

**Where:** `docs/the-build-os.md` Part VII, `templates/contract-tests.md`, and `docs/advanced-patterns.md` §3

**Proposed addition to the essential contract tests:**

```markdown
### C9: End-to-end data flow verified
**What it means:** Data injected at the input boundary arrives correctly
at the output boundary, through all intermediate processes.
**Why it matters:** Component tests validate logic in isolation. Integration
boundaries — serialization, process restarts, schema alignment — are where
production failures actually happen.
**How it's tested:** Inject a synthetic fixture at the earliest input point.
Verify it appears correctly at the final output surface (API, UI, notification).
**What failure looks like:** "Unit tests pass, but the feature doesn't work
in production." The mocks validated the bug.
```

**Rationale:** This is the single lesson from all 4 incidents. It belongs in the essential contract tests because it applies to any multi-process system, not just agent systems.

---

## Changes NOT Proposed (and why)

1. **Health daemon monitoring expansion** — Too project-specific. The Build OS already covers "degraded mode visible" as a contract test. Individual projects decide what to monitor.

2. **CLAUDE.md hard rule about deploy scripts** — Too project-specific. The Build OS shouldn't mandate a specific deploy script pattern. The "deploy script as enforcement" pattern (Change 3) is the generalizable version.

3. **Pipeline canary test specifics** — Too implementation-specific. The "integration gate" concept (Change 1) and the C9 contract test (Change 6) are the generalizable versions.

---

## Questions for Debate

1. Is C9 (end-to-end data flow) genuinely distinct from C4 (degraded mode visible) and the existing smoke test guidance? Or does adding it create redundancy?
2. Should the "skip levels" guidance modify the three-strikes rule, or should it be a separate concept entirely?
3. Is "deploy script as enforcement" a pattern worth documenting, or is it obvious enough that it doesn't need a section?
4. Does the session-log trigger belong in the Build OS, or is it too opinionated about a specific workflow?

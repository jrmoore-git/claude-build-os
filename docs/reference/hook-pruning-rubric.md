# Hook Pruning Rubric

Rules for deciding which hooks can be safely pruned based on session telemetry.

## Why two classes

The naive metric — "prune hooks with low `fire_rate × block_rate`" — breaks for
advisory and injection hooks. These hooks are designed to never block
(`block_rate = 0` by construction). A volume-based metric would wrongly flag
them all as dead weight.

High-stakes enforcement hooks have the opposite failure mode: a zero fire rate
may mean the guard is working (no one tried to do the bad thing) rather than
that the guard is useless. Pruning them on low fire rate would remove
load-bearing safety nets.

The rubric below splits hooks into three classes and applies different pruning
criteria to each.

## The three classes

### advisory / injection

Hooks that emit `decision=warn` or never fire a `hook_fire` event at all.
They inject context, route intent, or observe — they never block.

Examples: `hook-context-inject.py`, `hook-intent-router.py`,
`hook-decompose-gate.py`, `hook-read-before-edit.py`, `hook-error-tracker.py`,
`hook-session-telemetry.py`, `hook-post-build-review.py`.

**Pruning criterion:** qualitative. Ask "does this change observable agent
behavior?" Not volume-based. A zero-volume advisory hook may still be valuable
if the behavior it would inject matters when it does fire.

Decision: keep unless behavior review confirms it has no effect on outcomes.

### enforcement-low

Hooks that can emit `decision=block` but only on low-stakes paths — style,
syntax, lint, docs. A false negative here costs a correction, not a data-loss
incident.

Examples: `hook-skill-lint.py`, `hook-syntax-check-python.sh`,
`hook-ruff-check.sh`, `hook-pre-commit-tests.sh`, `pre-commit-banned-terms.sh`,
`hook-post-tool-test.sh`, `hook-prd-drift-check.sh`, `hook-spec-status-check.py`.

**Pruning criterion:** `fire_count < 5` in 30+ sessions AND `block_rate < 10%`.
Both conditions must hold. Low fire count alone is not enough — a hook that
fires rarely but blocks every time is still doing work.

Decision: candidate for pruning if both thresholds are met. Review before
removing.

### enforcement-high

Hooks that block on high-stakes paths — credentials, protected files,
destructive commands, cross-worktree writes, memory limits.

Examples: `hook-guard-env.sh`, `hook-plan-gate.sh`, `hook-review-gate.sh`,
`hook-pre-edit-gate.sh`, `hook-agent-isolation.py`, `hook-memory-size-gate.py`,
`hook-bash-fix-forward.py`, `hook-tier-gate.sh`.

**Pruning criterion:** exempt from volume-based pruning regardless of fire
rate. A zero-fire rate on a high-stakes enforcement hook means the guard is
working, not that it's dead weight.

Decision: never prune based on telemetry volume. Removal requires an
architectural review that confirms the guarded behavior is impossible through
other means.

## Session-count gate

Do not attempt pruning until ≥30 sessions have been observed in telemetry.

A session is counted if it has a `session_start` event in `stores/session-telemetry.jsonl`.
Fewer than 30 sessions is insufficient statistical signal for volume-based
decisions.

`scripts/session_telemetry_query.py prune-candidates` enforces this gate — it
prints an "insufficient data" message and exits early when the session count
is below the threshold.

## Classification source of truth

Each hook file carries its class as a comment on a top line, placed right
after the shebang:

```
#!/usr/bin/env python3.11
# hook-class: enforcement-high
"""..."""
```

For shell files, same syntax:

```
#!/bin/bash
# hook-class: enforcement-low
```

`scripts/session_telemetry_query.py` reads these tags directly from the hook
files at startup. There is no separate registry — the comment in the hook file
is the single source of truth. This avoids drift between a central list and
the actual hooks on disk.

A hook without a `# hook-class:` tag shows up as `unknown` in telemetry
output. `prune-candidates` flags untagged hooks as "classify before pruning"
rather than treating them as candidates.

## Adding new hooks

When creating a new hook file:

1. Classify it against the three classes above.
2. Add `# hook-class: <class>` as a comment line at the top (after shebang,
   before docstring).
3. No registry update needed — the query script picks it up automatically.

If the hook is genuinely borderline (e.g., a mostly-advisory hook that can
block in edge cases), err toward the more protective class. Misclassifying
enforcement as advisory risks pruning something load-bearing; the reverse
only wastes a qualitative review cycle.

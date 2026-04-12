---
topic: evaluation-routing
created: 2026-04-11
recommendation: PROCEED
complexity: low
review_backend: cross-model
challengers: 3
unanimous: true
security_posture: 1
---
# Challenge Result: PROCEED

3/3 challengers approve. No material objections to the approach. Two implementation details flagged:

## Findings

### MATERIAL: Audit log schema for --models mode
When `--models` is used, the `"personas"` field in the audit log currently expects persona names. Decision: use model names directly in the `"personas"` field and add a `"mode": "direct-models"` flag so downstream consumers can distinguish. Synthetic labels ("model-1") add indirection for no benefit.

### ADVISORY: Argparse mutual exclusion
Use `add_mutually_exclusive_group(required=True)` for `--personas` and `--models`. Current `--personas` is `required=True` — that needs to move to the group level.

### ADVISORY: No test coverage for debate.py
Add a minimal smoke test for the new arg parsing.

## Validated by challengers
- Personas in review-panel are already just model selectors (no PERSONA_PROMPTS injected)
- Content-type routing belongs in the skill layer, not debate.py
- `--models` is consistent with existing patterns (challenge and refine already support it)
- Scope is appropriately minimal

## Next
`/plan evaluation-routing` then build.

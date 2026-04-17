---
topic: opus-47-temperature
review_tier: single-model-trivial
status: passed
git_head: 92d2e3e
producer: claude-opus-4-7
created_at: 2026-04-16T22:01:00-07:00
scope: scripts/llm_client.py
findings_count: 0
spec_compliance: false
---

# /review — opus-47-temperature

[TRIVIAL]-tagged 8-line change patches `_sdk_call` and `_legacy_call` to
omit `temperature` for `claude-opus-4-7`. Cross-model debate bypassed
per `.claude/rules/review-protocol.md` skip conditions; single-model
self-review through PM / Security / Architecture lenses below.

## PM / Acceptance
- [PASS] Solves a real, verified problem (HTTP 400 from Opus 4.7 on any explicit temperature). Smoke test confirmed across temps 0.0/0.7/0.8/1.0.
- [PASS] Right-sized: minimal inline conditional. No new abstraction, no helper extraction (consistent with code-quality.md guidance against premature helpers for 2 call sites).
- [PASS] No spec to comply against; no scope creep.

## Security
- [PASS] Model name is developer/config-controlled, never user input. No injection vector via the conditional check.
- [PASS] No changes to credential handling, trust boundaries, or auth paths.
- [ADVISORY] `model.startswith("claude-opus-4-7")` is case-sensitive. If a future caller passes `Claude-Opus-4-7` the guard misses. Mitigation: model names are conventionally lowercase across the codebase; no live caller violates this.

## Architecture
- [PASS] Two-place inline duplication is acceptable for a one-line check; helper extraction would be premature.
- [PASS] Comment in `_sdk_call` explains the why (proxy `drop_params` does not strip this param for opus-4-7 on the current image); `_legacy_call` cross-references it.
- [ADVISORY] `_anthropic_call` not patched. Currently unreachable with opus-4-7 because `_FALLBACK_MODEL` is hardcoded to `claude-sonnet-4-20250514`. If `ANTHROPIC_FALLBACK_MODEL` env override is ever set to an opus-4-7 variant, the fallback path will 400. Out of scope for this fix.
- [ADVISORY] `litellm/claude-opus-4-7` prefix variant (referenced defensively in `debate.py:1257`) would not match `startswith("claude-opus-4-7")`. No live caller passes this prefixed form to `llm_call` as of HEAD; `_get_model_family` strips the prefix before family checks but the actual API model string sent through `llm_call(model=...)` is always bare. Real risk only if a caller starts using the prefixed form.
- [ADVISORY] Temporary workaround. Revert path: when LiteLLM proxy gains `drop_params` support for opus-4-7 (likely via image bump from 2026-04-08 SHA `59a2736ac848`), both conditionals + comments should be removed. The "yet" in the comment hints at the temporary nature; consider adding a TODO with a tracking link if/when one exists.

## Verdict
**PASSED** — 0 MATERIAL, 3 ADVISORY findings. All advisories are documented gaps with no current-day failure mode.

## Suggested next action
`/wrap` to capture session state, then push.

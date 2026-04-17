---
topic: buildos-improvements-bundle-1
review_tier: cross-model
status: revise
git_head: 6a3fb0b
producer: claude-opus-4-7
created_at: 2026-04-16T22:20:00-07:00
scope: "hooks/hook-post-build-review.py, hooks/hook-intent-router.py, .claude/settings.json, docs/reference/hook-pruning-rubric.md, scripts/session_telemetry_query.py, .claude/skills/review/SKILL.md, .claude/rules/review-protocol.md, 22 hook class-tag additions, tests/test_hook_post_build_review.py"
findings_count: 1
spec_compliance: true
spec_artifacts: [tasks/buildos-improvements-bundle-1-plan.md, tasks/buildos-improvements-challenge.md]
challengers_reached: 2
challenger_failure: "claude-opus-4-7 (temperature-deprecation bug in debate.py — pre-existing, tracked separately)"
---

# Review — buildos-improvements-bundle-1

**Verdict: REVISE — 1 MATERIAL finding, 5 ADVISORY findings**

Coverage met with 2 of 3 challengers (gpt-5.4, gemini-3.1-pro). Opus 4.7 hit a pre-existing `temperature` deprecation bug in debate.py's challenge path — orthogonal to this diff. Spec-compliance lens applied against plan + challenge. All 5 challenge-accepted fixes verified except one partial implementation.

## PM / Acceptance

- **[MATERIAL] SPEC VIOLATION: Fix 4 only partially implemented.** The challenge's accepted Fix 4 required: *"Gate pruning on 30 sessions minimum OR 4 calendar weeks, whichever is later."* Implementation in `scripts/session_telemetry_query.py:42` and `docs/reference/hook-pruning-rubric.md` only gates on session count; the calendar-time "whichever is later" half is absent. Impact: a burst of 30 sessions in 24 hours would unlock pruning, which is exactly the "insufficient stability" failure mode the challenge accepted. Evidence: rubric doc reads "Do not attempt pruning until ≥30 sessions have been observed"; script has `SESSION_COUNT_GATE = 30` with no timestamp check. **Fix cost: trivial.** Add `FIRST_SESSION_AGE_DAYS = 28` constant, compute first session_start ts, require `session_count >= 30 AND (now - first_ts) >= 28*86400`. ~6 lines in script, 1 sentence in rubric.

- **[ADVISORY] Rubric doc framing inconsistency.** `docs/reference/hook-pruning-rubric.md` titled "two-class rubric" but defines three classes (advisory, enforcement-low, enforcement-high). Accurate in substance — the split is advisory-vs-enforcement with severity sub-bands — but the framing will confuse future readers. Suggested fix: rename to "two-tier rubric with severity split" or note up-front that enforcement is subdivided. 1-line doc fix.

- **[ADVISORY] review-protocol.md language overstates current wiring.** New section says "Future `/review` runs read this section and treat these as patterns to not re-flag." The plan explicitly scopes wiring to a future bundle. Current text implies shipped behavior. Suggested fix: "When wired (future bundle), `/review` runs will read this section..." 1-word edit.

## Security

- **[ADVISORY] State file at predictable path, no atomic write.** `/tmp/claude-review-<session_id>.json` is written by `hooks/hook-post-build-review.py:91-95` with default umask, non-atomic. Any local process could spoof or wipe the flag. Challenge synthesis explicitly dismissed this under single-developer threat model (D12). Noted for provenance — no action required. If framework expands to multi-user in future, revisit.

- **[ADVISORY] Intent router trusts state file without signature.** `hooks/hook-intent-router.py` reads the same file and injects a non-suppressible prompt. Same threat model applies — single-developer, negligible risk. Add a one-line comment documenting the trust contract.

## Architecture

- **[ADVISORY] Test hardcodes `/opt/homebrew/bin/python3.11`.** `tests/test_hook_post_build_review.py:71,236` invokes subprocess with the homebrew path. Aligned with CLAUDE.md platform rules (macOS/homebrew is the declared platform) but fragile if the framework ever runs in CI or under a different Python install. Suggested fix: use `sys.executable` and pass `env` to preserve test isolation. ~2 lines.

- **[ADVISORY] Telemetry test writes to real `stores/session-telemetry.jsonl`.** `tests/test_hook_post_build_review.py:200` constructs the store path from `Path(__file__).parent.parent / "stores"` — the real repo store. Test pollution risk for future runs. Suggested fix: monkeypatch `hook-post-build-review.py`'s telemetry store constant, or parameterize via env var. ~3 lines.

- **[ADVISORY] /tmp path is an implicit contract between two hooks.** `hook-post-build-review.py` and `hook-intent-router.py` both reference `/tmp/claude-review-{session_id}.json` as a hardcoded string. Coupling is intentional (shared state without a message bus) but undocumented. Suggested fix: define the path as a constant in a shared helper (e.g., `scripts/telemetry.py` or a new `scripts/review_flag_path.py`) imported by both. ~5 lines for the refactor, OR just a comment naming the contract.

## Dismissed challenger claims (with rationale)

- **Claim:** Fix 1 (generic PostToolUse + JSON filter) not met — settings.json ambiguous.
  **Dismissed:** Verified. settings.json registers under `matcher: "Write|Edit"` on generic `PostToolUse` event. That is Claude Code's canonical "generic event + matcher filter" pattern. Hook also does defense-in-depth internal JSON filtering (`tool_name in {"Write", "Edit"}`). Both halves of Fix 1 satisfied. The challenger marked this SPECULATIVE due to not verifying from snippets — ground truth check confirms compliance.

- **Claim:** Telemetry hook-name derivation is a brittle implicit contract (MATERIAL architecture).
  **Dismissed:** Verified. All 7 currently-emitting hooks (plan-gate, pre-edit-gate, review-gate, bash-fix-forward, decompose-gate, memory-size-gate, post-build-review) use exactly the names `_load_hook_classes()` derives. No drift. Marked SPECULATIVE by challenger — ground truth confirms no violation.

- **Claim:** Telemetry import via `sys.path` is fragile (MATERIAL architecture).
  **Dismissed:** Identical pattern to stable `hook-session-telemetry.py`. Defensive try/except fallback to no-op means worst-case is lost telemetry, not a broken session. Not material.

## Symmetric risk assessment

- **Risk of shipping as-is:** 1 spec violation (Fix 4 half-implemented). Operational impact: low for several weeks (session-count gate alone will hold for a while at current single-developer rate), but the second guardrail is why the challenge accepted both — bursts defeat session-count alone. Fix is trivial.
- **Risk of not shipping:** L25 stays open. Current telemetry already captures fires for 6 enforcement hooks; without the rubric + tags, that data stays unclassified.

Shipping after the M1 fix is the right call. Advisories can land inline with the fix commit or as a follow-up.

## Next action

Fix M1 (add calendar-time gate) + quick-win advisories A1 (rubric doc framing) and A2 (review-protocol wording). Then `/review --qa` to validate.

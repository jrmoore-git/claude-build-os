---
debate_id: buildos-improvements-bundle-1-review-debate
created: 2026-04-16T22:16:10-0700
mapping:
  A: claude-opus-4-7
  B: gpt-5.4
  C: gemini-3.1-pro
---
# buildos-improvements-bundle-1-review-debate — Challenger Reviews

## Challenger A — Challenges
[ERROR: Challenger A (claude-opus-4-7): LLM call failed (BadRequestError): Error code: 400 - {'error': {'message': 'litellm.BadRequestError: AnthropicException - {"type":"error","error":{"type":"invalid_request_error","message":"`temperature` is deprecated for this model."},"request_id":"req_011Ca8mpa6Z9Pqgvo5NGgPDm"}. Received Model Group=claude-opus-4-7\nAvailable Model Group Fallbacks=None', 'type': None, 'param': None, 'code': '400'}}]

---

## Challenger B — Challenges
## PM/Acceptance

- [MATERIAL] **SPEC VIOLATION: Fix 4 was implemented incorrectly.** The accepted challenge finding requires a pruning gate of **“30 sessions minimum OR 4 calendar weeks, whichever is later”** in the challenge artifact, and your review instructions explicitly say to extract all accepted findings from that artifact and verify the inline fixes they required. The implementation hard-codes only `SESSION_COUNT_GATE = 30` and `cmd_prune_candidates()` checks only `_session_count(events)` with no calendar-time gate at all in `scripts/session_telemetry_query.py:42-45` and `:284-299`. This leaves pruning eligible earlier than the accepted finding allowed. Risk of what was built: premature pruning decisions from insufficiently mature telemetry. Risk of what stays unfixed: the exact stability concern the challenge accepted remains open.

- [MATERIAL] **SPEC VIOLATION: the new hook is not registered on a generic PostToolUse handler with internal JSON filtering, as required by accepted Fix 1.** The hook code itself correctly filters `tool_name in ("Write", "Edit")` in `hooks/hook-post-build-review.py:176-180`, but the plan’s required inline fix was specifically “generic PostToolUse + JSON filter.” The `.claude/settings.json` diff adds the command under an existing event block, but the provided snippet does not show that this block is the generic `PostToolUse` registration, and the plan text for A3 still describes “PostToolUse.Write|Edit handler entry.” Because the accepted fix was about avoiding non-platform event specificity, this should be made unambiguous in the registration itself/documentation, not only in the hook body. Status: **SPECULATIVE** on exact runtime breakage because the event key wasn’t visible in the snippet, but the compliance gap in the delivered spec text is clear.

- [ADVISORY] The pruning rubric doc says “Why two classes” but then defines **three** classes (`advisory`, `enforcement-low`, `enforcement-high`) in `docs/reference/hook-pruning-rubric.md:5-18,20-69`. That mirrors the underlying accepted finding, but the framing is inconsistent and likely to confuse future operators about whether severity split is part of the model or not.

- [ADVISORY] The review-protocol addition states “Future `/review` runs read this section” in `.claude/rules/review-protocol.md`, but the plan explicitly says that wiring is out of scope for this bundle. Since no `scripts/debate.py` changes are in scope here, this reads as shipped behavior rather than convention. That is acceptance-doc drift, not a code bug.

## Security

- [ADVISORY] The new trust boundary on `/tmp/claude-review-<session>.json` is still unauthenticated and world-discoverable by naming convention in `hooks/hook-post-build-review.py:59-93`, and `hooks/hook-intent-router.py:557-572` trusts it enough to inject a non-suppressible review reminder. Per the single-developer internal-tooling threat model, this is likely acceptable, but the implementation makes a stronger assumption than it documents: any local process that can write that path can force or clear reminders. Risk of what was built: local state-file spoofing can distort routing behavior. Risk of what stays unfixed: low in the current deployment model, but it becomes material if this tooling ever moves beyond single-user workstations.

- [ADVISORY] `_save_state()` writes the state file with default process umask and no atomic replace in `hooks/hook-post-build-review.py:91-95`. In this threat model that is probably fine, but it leaves a failure mode where partial writes or concurrent invocations can produce malformed JSON and silently reset state via `_load_state()`. That is more integrity/reliability than security, but it crosses the same state-file boundary.

## Architecture

- [MATERIAL] The telemetry query and rubric integration encode a repository-name assumption that is not demonstrated to match emitted telemetry names for all hooks. `_load_hook_classes()` derives names from filenames by stripping only the `hook-` prefix (`hook-plan-gate.sh` → `plan-gate`, `pre-commit-banned-terms.sh` stays `pre-commit-banned-terms`) in `scripts/session_telemetry_query.py:87-121`, and then joins those against `hook_fire` event `hook_name`s in `cmd_hook_fires()` / `cmd_prune_candidates()`. I verified one emitter (`hook-session-telemetry.py`) but not the rest; there is no compatibility shim or test proving all existing hook emitters use exactly these derived names. Status of the mismatch risk: **SPECULATIVE**, but architecturally this is a brittle implicit contract between filenames and telemetry payloads. If even one hook emits `hook_name="hook-plan-gate"` or another variant, it silently falls into `unknown`, degrading the new rubric/reporting.

- [ADVISORY] `tests/test_hook_post_build_review.py` is architecture-fragile because it hard-codes `/opt/homebrew/bin/python3.11` in subprocess invocations at `:71` and `:224`. This couples the feature’s verification surface to a specific local interpreter layout rather than the project runtime contract. Risk of what was built: tests fail or get skipped in non-Homebrew CI/dev environments even if the hook is correct. Risk of what stays unfixed: reduced portability and lower confidence in the new hook.

- [ADVISORY] The telemetry test writes against the real repo store rather than an isolated fixture in `tests/test_hook_post_build_review.py:181-219`, and the inline comment admits the intended isolation wasn’t achieved. That creates cross-test coupling with existing telemetry state and makes the test outcome dependent on ambient repository mutation. Architecturally, that is a poor fit for observer-hook testing and weakens confidence in the new telemetry integration.

- [ADVISORY] `hook-post-build-review.py` imports telemetry from the hook repo root while plan discovery is taken from `PROJECT_ROOT` override (`_HOOK_REPO_ROOT` vs `REPO_ROOT`) in `hooks/hook-post-build-review.py:37-48`. That split is intentional for tests, but it means the hook can read plans from one tree and emit telemetry into another tree’s `scripts/telemetry.py` behavior. In current usage this is probably harmless; still, it is a cross-root integration assumption worth documenting because it can surprise future test harnesses or worktree setups.

---

## Challenger C — Challenges
# Code Review: BuildOS Improvements Bundle 1

## PM / Acceptance
The diff closely aligns with the plan and the required inline fixes from the Challenge Gate Synthesis. 

**Positive Compliance (Findings Accepted):**
- **Fix 1 (Generic PostToolUse + JSON filter):** [EVIDENCED] The `hook-post-build-review.py` hook uses generic `sys.stdin.read()` to parse the payload and filters for `tool_name in ("Write", "Edit")` (Lines ~166-168).
- **Fix 2 (Re-fire policy):** [EVIDENCED] The hook tracks `re_fire_count` and appropriately re-fires every 5 edits past the 10-edit threshold, passing the correct suggestion to the intent router.
- **Fix 3 (Two-class rubric replacing fire_rate × block_rate):** [EVIDENCED] The rubric doc and hook file `# hook-class:` tags properly partition the hooks into `advisory`, `enforcement-low`, and `enforcement-high`.
- **Fix 4 (30-session gate):** [EVIDENCED] `session_telemetry_query.py` enforces a hard `SESSION_COUNT_GATE = 30` before presenting pruning candidates.
- **Fix 5 (Descope #3 to manual annotation):** [EVIDENCED] Automation tools (`review_feedback.py`, etc.) were avoided. Instead, `review-protocol.md` and `SKILL.md` contain the required negative examples section and instructional prompt.

**Negative Compliance (Findings Dismissed):**
- [EVIDENCED] The implementation actively avoids implementing session-state flag trust boundary enforcement (like `O_EXCL` or restricted permissions on the state file) in alignment with the challenge explicitly dismissing it based on the single-developer threat model.

## Security
- **[ADVISORY] State File Integrity / Parsing:** The hook `hook-intent-router.py` loads the `/tmp/claude-review-pid.json` file. While the challenge synthesis correctly dismissed the local trust boundary threat model, it is worth noting that parsing unbounded `/tmp` files with `json.load()` can technically be a vector for resource exhaustion. The current `try/except` correctly traps `JSONDecodeError`, which handles malformed inputs well enough for this tier.
- **[ADVISORY] Path Interpolation in Settings:** The `.claude/settings.json` changes inject the `python3` command securely without shell interpolation vulnerabilities, which is well-aligned with the security spec.

## Architecture
- **[MATERIAL] Telemetry Import Fragility:** `hook-post-build-review.py` alters `sys.path` to inject the parent `scripts` directory for telemetry imports. If this hook is executed from an unexpected working directory or environment (e.g. from within a nested `tests/` directory during an unexpected test pipeline invocation), the path resolution might fallback silently, dropping telemetry. 
- **[ADVISORY] Single Source of Truth for Hook Classes:** The decision to embed `# hook-class:` metadata directly inside the target hook files rather than in a centralized `.json` manifest is architecturally sound. It eliminates drift. `scripts/session_telemetry_query.py` correctly handles parsing this inline without running the scripts.
- **[ADVISORY] Intent Router Integration:** The `hook-intent-router.py` hook leverages a hardcoded shared file path (`/tmp/claude-review-{SESSION_ID}.json`) to communicate with `hook-post-build-review.py`. While effective, these components are now implicitly coupled by this `/tmp` path convention. If the naming schema changes in one, the other will silently fail to inject the reminder.

---

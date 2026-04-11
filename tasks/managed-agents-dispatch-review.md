---
topic: managed-agents-dispatch
review_tier: cross-model
status: passed
git_head: 5712e21
producer: claude-opus-4-6
created_at: 2026-04-10T19:45:00-0700
scope: scripts/managed_agent.py, scripts/debate.py, tests/test_managed_agent.py
findings_count: 0
spec_compliance: true
review_iterations: 4
---

## PM / Acceptance

- [ADVISORY] No integration-level test for `debate.py` MA fallback path end-to-end. Unit tests cover `managed_agent.py` in isolation; `cmd_judge` MA path (fallback logging, event-log fields) is not exercised in tests. Phase 2 candidate. (B)
- [ADVISORY] Lifecycle metrics surfacing is implicit — relies on `run_consolidation` stats shape rather than normalized at the call site. Acceptable for Phase 1. (B)
- [ADVISORY] Scope and completeness confirmed — diff aligns with MVP checklist, targets `_consolidate_challenges` only, respects `challenge_body` boundary. (C, corroborated A#16)
- [ADVISORY] Fallback tracking correctly surfaces `ma_fallback` and `consolidation_source` in structured log. Operator visibility requirement met. (A#12, C)
- [ADVISORY] Cost accounting works via prefix matching (`"claude-sonnet-4"` matches `"claude-sonnet-4-6"`). Fragile if model naming changes but correct today. (A#10)
- [ADVISORY] Provider security assumptions documented in module docstring — rollout gate met. (A#11)

## Security

- [ADVISORY] Environment resources can be orphaned if `sessions.create` or `events.send` fails within `dispatch_task` after environment creation, since `_cleanup_environment` only runs in `run_consolidation`'s `finally` block. Bounded risk: envs are ephemeral, and the success-path cleanup works correctly. Phase 2 hardening candidate. (B)
- [ADVISORY] Sensitive-content gating (default-deny for secrets/PII before remote dispatch) is documented in spec but not enforced in code. Acceptable for narrow internal rollout; Phase 2 gate. (B)
- [ADVISORY] Credential leak prevention correctly implemented — `type(e).__name__` only logging, traceback removed, API key passed as parameter not env var. Spec "No Secret Logging" clause satisfied. (A#6, C)
- [ADVISORY] `_ma_exc` fallback tuple is narrow but correctly handles all import failure scenarios. (A#7)
- [ADVISORY] No ambient context egress — payload is explicitly constructed from `challenge_body` only. Spec "No Ambient Context" clause satisfied. (A#8, C)
- [ADVISORY] Credential subprocess isolation — API key passed as function parameter, never written to `os.environ`. Spec compliant. (A#9, C)

## Architecture

- [ADVISORY] Module-level `_cached_agent` global is single-threaded; no lock protection. Safe for Phase 1 (consolidation is single-threaded) but should be documented/hardened before any concurrency expansion. (A#2, B, C)
- [ADVISORY] `dispatch_task` return signature `(client, session_id, lifecycle)` diverges from spec's `-> job_id`. Pragmatically correct; spec should be updated to match. (A#5)
- [ADVISORY] Usage tracking only captures `assistant.message` events — may miss usage reported on other event types. Recommend defensive log when tokens are zero after non-empty response. (A#1)
- [ADVISORY] Environment/session separation correctly prevents orphaned environments on session-creation retry. (A#3)
- [ADVISORY] Usage/cost parity is estimated from token counts, not provider-billed cost. Spec explicitly allows this. (B)
- [ADVISORY] `_retry_transient` return signature `(result, attempt)` is a breaking change for any future external caller; acceptable since function is `_`-prefixed and module is new. (A#4)

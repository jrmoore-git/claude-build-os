---
topic: tier-aware
review_tier: degraded
status: passed
git_head: 61d19d0
producer: claude-opus-4-6
created_at: 2026-04-16T08:30:00-07:00
scope: CLAUDE.md, hooks/hook-agent-isolation.py, hooks/hook-bash-fix-forward.py, hooks/hook-decompose-gate.py, hooks/hook-error-tracker.py, hooks/hook-intent-router.py, hooks/hook-memory-size-gate.py, hooks/hook-plan-gate.sh, hooks/hook-post-tool-test.sh, hooks/hook-prd-drift-check.sh, hooks/hook-pre-commit-tests.sh, hooks/hook-pre-edit-gate.sh, hooks/hook-review-gate.sh, hooks/hook-skill-lint.py, hooks/hook-spec-status-check.py, hooks/hook-stop-autocommit.py, hooks/hook-tier-gate.sh, scripts/read_tier.py, tests/test_read_tier.py, tests/test_hook_pre_edit_gate.py, docs/orchestrator-contract.md, .claude/skills/setup/SKILL.md, .claude/rules/session-discipline.md
findings_count: 0
spec_compliance: false
open_material_findings: 0
---

# Review: tier-aware (degraded — Gemini 503)

Cross-model review attempted with claude-opus-4-6, gpt-5.4, gemini-3.1-pro. Gemini returned 503 (high demand). Claude and GPT completed but output not persisted before process killed. Self-review through 3 lenses below.

## PM / Acceptance

- [ADVISORY] The `parse_frontmatter` function is duplicated in hook-pre-edit-gate.sh (scope check block and plan matching block). Both live inside bash heredocs so they can't easily share code. The test file has the extracted version which serves as the single source of truth. Accepted tradeoff.
- [ADVISORY] Python hooks add ~50ms overhead per invocation from the subprocess call to read_tier.py. This is negligible for hooks that gate writes/commits but worth noting.

## Security

- No findings. The tier declaration is an HTML comment (not executable). read_tier.py reads only the first 5 lines via regex — no injection vector. Scope containment uses fnmatch against declared paths — no shell injection. The scope_escalation flag creates an audit trail (warning printed) rather than silent bypass.

## Architecture

- [ADVISORY] Consistent 8-line tier check pattern across all hooks (Python: subprocess to read_tier.py; bash: 2-line check). Could be further reduced to a 1-line helper function in a shared shell library, but current pattern is explicit and greppable.
- No MATERIAL findings. The design is correct: T0 hooks (safety) always fire, T1 hooks (workflow) fire at tier >= 1, T2 hooks (enforcement) fire at tier >= 2. Default tier = 3 (fail closed) is the right safety posture.

## Summary

| Lens         | Material | Advisory |
|--------------|----------|----------|
| PM           | 0        | 2        |
| Security     | 0        | 0        |
| Architecture | 0        | 1        |

Spec compliance: no spec found
Status: PASSED (degraded — 1 of 3 external models unavailable)

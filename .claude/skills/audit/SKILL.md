---
name: audit
description: Run a two-phase audit — blind discovery, then targeted questions
user-invocable: true
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# Project Audit

Two-phase audit protocol: discover what exists, then ask targeted questions about what you found.

## When to use

- Before a major release or milestone review
- After inheriting an unfamiliar codebase
- When you suspect implementation has drifted from the PRD
- Periodically (weekly or monthly) for production systems

## Procedure

### Phase 1: Blind discovery

Do not consult the PRD, decisions.md, or conversation history. Start with direct inspection only.

1. **Code structure:** `find . -name "*.py" -o -name "*.ts" -o -name "*.js" | head -100` — what exists?
2. **Recent changes:** `git log --oneline -30` — what changed recently?
3. **Data stores:** look for `.db`, `.sqlite`, `.json` stores — what state is persisted?
4. **Configuration:** check for `.env`, config files, settings — what's configurable?
5. **Dependencies:** check package files (requirements.txt, package.json) — what's pulled in?
6. **Entry points:** find main files, CLI entry points, cron configs — how does it run?

Record what you find. Do not interpret yet.

### Phase 2: Targeted questions

Now read the PRD and compare against Phase 1 findings. For each discrepancy, write a finding.

Check:
1. **Spec drift** — does the implementation match the PRD? What's built but not spec'd? What's spec'd but not built?
2. **Dead code** — are there files, functions, or tables with no callers?
3. **Dependency health** — are versions pinned? Any known vulnerabilities? Any unused dependencies?
4. **Contract tests** — do the Essential Eight invariants hold? (idempotency, approval gating, audit completeness, degraded mode visible, state machine validation, rollback, version pinning, exactly-once scheduling)
5. **Security surface** — any hardcoded secrets, unvalidated inputs, or missing auth checks?
6. **Governance state** — are decisions.md, lessons.md, and handoff.md current?

### Phase 3: Write findings

Create `tasks/audit-[date].md`:

```markdown
# Audit: [date]

## Findings

### [Finding title — assertion style]
- **Severity:** critical | warning | info
- **Evidence:** [specific file, line, command output]
- **Not checked:** [known blind spots]
- **Recommendation:** [what to do]

## Summary
- Critical: [count]
- Warning: [count]
- Info: [count]
- Contract test status: [pass/fail per invariant]
```

## Rules
- Phase 1 must complete before Phase 2. Do not skip blind discovery.
- Every finding must cite specific evidence (file path, command output, line number). No findings from memory or conversation history.
- Label each finding's source: **inspected** (direct evidence) or **inferred** (reasoning from indirect evidence). Only inspected findings can be critical severity.
- Check `docs/audit-corrections.md` if it exists — do not repeat previously corrected false findings.

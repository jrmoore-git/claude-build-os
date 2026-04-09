# Contract Tests

Contract tests verify that your system's essential invariants hold across every change. They are not unit tests for individual functions -- they are structural checks that catch violations of system-wide guarantees.

## The Essential Eight Invariants

Every change to the system must preserve these eight invariants. They apply regardless of what feature you are building.

### 1. Idempotency

Running the same operation twice produces the same result as running it once. No duplicate records, no double-sends, no repeated side effects.

**Test pattern:** Execute the operation, record the state. Execute it again with the same input. Assert state is unchanged.

### 2. Approval Gating

No action with external consequences (sending emails, modifying records, calling APIs) executes without explicit user approval unless the operation is pre-approved by policy.

**Test pattern:** Trigger the operation. Assert it enters a "pending approval" state rather than executing immediately. Approve it. Assert it executes exactly once.

### 3. Audit Completeness

Every state-changing operation writes an audit log entry BEFORE executing. The audit trail must be sufficient to reconstruct what happened, when, and why -- without containing sensitive content (raw message text, PII).

**Test pattern:** Execute an operation. Query the audit log. Assert an entry exists with the correct action_type, timestamp, and metadata. Assert no raw content in the summary field.

### 4. Degraded Mode Visible

When a dependency fails (API down, auth expired, database locked), the system must surface the failure visibly -- not silently return empty results or stale data.

**Test pattern:** Mock a dependency failure. Assert the system either: (a) returns an explicit error, (b) logs the failure to the audit trail, or (c) sets a visible status indicator. Assert it does NOT return success with empty/stale data.

### 5. State Machine Validation

Records that transition through states (pending -> approved -> sent, draft -> review -> published) must follow the defined state machine. Invalid transitions are rejected.

**Test pattern:** Attempt an invalid state transition (e.g., "sent" -> "pending"). Assert the operation fails with a clear error. Assert the record's state is unchanged.

### 6. Rollback Path Exists

Every deployment, migration, and configuration change must have a documented rollback procedure. The rollback must be tested -- not just theorized.

**Test pattern:** Apply a change. Execute the rollback procedure. Assert the system returns to its previous state. Assert no data was lost in the round-trip.

### 7. Version Pinning Enforced

All external dependencies (Docker images, packages, API versions) must be pinned to specific versions. No `:latest` tags, no unpinned installs, no auto-update flags.

**Test pattern:** Scan dependency files (requirements.txt, package.json, docker-compose.yml). Assert every dependency has an explicit version. Flag any that use floating versions.

### 8. Exactly-Once Scheduling

Scheduled operations (cron jobs, periodic tasks) must execute exactly once per scheduled interval. Neither missed executions nor double-executions are acceptable.

**Test pattern:** Trigger a scheduled operation. Assert it executes once. Trigger it again within the same interval. Assert it does NOT execute again (dedup check). Advance past the interval. Assert it executes for the new interval.

## Writing Contract Tests

Contract tests live in `tests/contracts/`. Each test file corresponds to one invariant.

### Structure

```python
#!/usr/bin/env python3
"""Contract test: [invariant name]"""

import subprocess
import json
import sqlite3

def test_[invariant]_[scenario]():
    """[What this test verifies]"""
    # Setup: prepare the precondition
    # Act: execute the operation
    # Assert: verify the invariant holds
    pass

if __name__ == "__main__":
    # Run all test functions
    failures = []
    for name, func in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                func()
                print(f"  PASS: {name}")
            except AssertionError as e:
                print(f"  FAIL: {name} -- {e}")
                failures.append(name)
    if failures:
        print(f"\n{len(failures)} contract test(s) FAILED")
        exit(1)
    print("\nAll contract tests passed")
```

### Adding Domain-Specific Invariants

The essential eight are universal. Your project will have additional invariants specific to your domain. Add them as new test files in `tests/contracts/` following the same pattern.

Examples of domain-specific invariants:
- **No raw message text in databases** -- personal message content is never stored verbatim
- **Owner filtering** -- multi-tenant data is always filtered to the current user
- **Financial threshold gating** -- operations above a dollar threshold require explicit approval
- **Contact privacy tiers** -- restricted contacts' data is excluded at the query level, not post-processing

## Running Contract Tests

```bash
# Run all contract tests
bash tests/contracts/run_all.sh

# Run a specific invariant
python3 tests/contracts/test_idempotency.py
```

Contract tests should run as part of your CI pipeline and before every deployment.

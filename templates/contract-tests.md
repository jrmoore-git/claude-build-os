# Contract Tests

Behavioral invariants that must not break. Each test defines what the system MUST do regardless of implementation details.

Add domain-specific invariants on top of the essential eight.

---

## The Essential Eight

### C1: Idempotency
**What it means:** Duplicate inputs never produce duplicate outputs.
**Why it matters:** Retries, network flakes, and user double-clicks should not create duplicate records, sends, or side effects.
**How it's tested:** [Add your test: submit the same input twice, verify only one output exists]
**What failure looks like:** Duplicate emails sent, duplicate database entries, duplicate API calls.

### C2: Approval Gating
**What it means:** No high-stakes action executes without explicit approval.
**Why it matters:** The model can draft, classify, and recommend. It must not send, delete, or commit without a human in the loop.
**How it's tested:** [Add your test: attempt a high-stakes action, verify it blocks without approval]
**What failure looks like:** Email sent without review, record deleted without confirmation, code deployed without approval.

### C3: Audit Completeness
**What it means:** Every operation is logged before AND after, including failures.
**Why it matters:** Silent failures are invisible failures. If something breaks and there's no log, debugging is guesswork.
**How it's tested:** [Add your test: trigger an operation, verify log entries exist for both attempt and result]
**What failure looks like:** "It was working yesterday but I don't know what changed."

### C4: Degraded Mode Visible
**What it means:** When something breaks, the system tells you — it never silently degrades.
**Why it matters:** The most dangerous failure is the one nobody notices. Quality drops, outputs become unreliable, but the system keeps running.
**How it's tested:** [Add your test: disable a dependency, verify the system surfaces the degradation]
**What failure looks like:** Model silently falls back to a weaker version. API returns partial data. Cache serves stale results. Nobody notices.

### C5: State Machine Validation
**What it means:** No invalid state transitions.
**Why it matters:** A record that goes from "draft" to "sent" without passing through "approved" has bypassed the governance model.
**How it's tested:** [Add your test: attempt an invalid transition, verify it's blocked]
**What failure looks like:** Records in impossible states. Approvals bypassed. Workflow steps skipped.

### C6: Rollback Path Exists
**What it means:** Every change can be reverted within a defined window.
**Why it matters:** Confidence to ship comes from knowing you can undo.
**How it's tested:** [Add your test: make a change, revert it, verify the system is back to prior state]
**What failure looks like:** "We can't undo that." Data loss. Unrevertable deployments.

### C7: Version Pinning Enforced
**What it means:** No unreviewed dependency or model version changes.
**Why it matters:** An untested dependency upgrade is an unreviewed code change with unknown blast radius.
**How it's tested:** [Add your test: verify all dependencies are pinned, verify upgrade requires review]
**What failure looks like:** "It worked yesterday." Silent behavior change from auto-updated dependency.

### C8: Exactly-Once Scheduling
**What it means:** Scheduled jobs fire once per window, not zero times or N times.
**Why it matters:** A daily report that fires twice is noise. A daily report that fires zero times is a silent failure.
**How it's tested:** [Add your test: run the scheduler, verify exactly one execution per window]
**What failure looks like:** Duplicate alerts. Missing reports. Timer drift.

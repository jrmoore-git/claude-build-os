# Proposal: Close Build OS Compliance Gaps in OpenClaw/Jarvis

## Context

A full Build OS compliance audit (2026-03-15) found 6 gaps. 3 are actionable (Gaps 1–3), 3 are acceptable/deferred (Gaps 4–6). This proposal addresses the 3 actionable gaps.

---

## Gap 1: Wire Contract Tests into deploy_all.sh

**Problem:** The 8 essential behavioral contract tests (tests/contracts/test_*.sh) exist and pass, but are never invoked during `deploy_all.sh`. A commit could pass app-level smoke tests but violate idempotency, state machine, or approval gating invariants.

**Proposed fix:** Add a Step 5 to `scripts/deploy_all.sh` that runs `tests/run_all.sh` (the root-level test runner, which already invokes both pytest and contract tests).

```bash
# Step 5: Contract tests (behavioral invariants)
STEP=5
echo ""
echo "──── Step 5/5: Contract tests ────"
bash "$PROJECT_DIR/tests/run_all.sh"
```

Update step count labels from "Step N/4" to "Step N/5" throughout the script.

**Blast radius:** Low. Adds ~30s to deploy. Fail-fast behavior preserved (set -e + trap ERR). No changes to existing tests — just wiring them into the deploy pipeline.

**Rollback:** Revert the single file change to deploy_all.sh.

---

## Gap 2: Add Granola Owner Filter to outbox_tool.py Direct Parse

**Problem:** `outbox_tool.py` lines 117–127 parse the Granola cache directly (fallback when verified_emails_cache table is empty). This direct parse does NOT filter by GRANOLA_OWNER_EMAILS. If the MCP filter fails or the direct parse path is used, colleagues' meeting attendees could appear in the verified email cache, allowing drafts to them without explicit approval.

**Proposed fix:** Add owner filter to the `_parse_granola_cache_emails()` function in outbox_tool.py. Read `GRANOLA_OWNER_EMAILS` from environment, filter meetings to only those where Justin is creator or attendee before extracting attendee emails.

```python
def _parse_granola_cache_emails():
    """Parse Granola cache directly — fallback when verified_emails_cache empty."""
    owner_emails_raw = os.environ.get("GRANOLA_OWNER_EMAILS", "")
    owner_emails = {e.strip().lower() for e in owner_emails_raw.split(",") if e.strip()}

    # ... existing cache load logic ...

    for meeting in meetings:
        # Filter: only meetings where an owner email is creator or attendee
        creator_email = (meeting.get("creator", {}).get("email") or "").lower()
        attendee_emails_raw = [
            (a.get("email") or "").lower()
            for a in meeting.get("attendees", [])
        ]
        if not owner_emails & ({creator_email} | set(attendee_emails_raw)):
            continue  # Skip — not Justin's meeting

        # Extract attendee emails from this meeting
        for email in attendee_emails_raw:
            if email and email not in owner_emails:
                verified.add(email)

    return verified
```

**Blast radius:** Low. Only affects the fallback path (direct Granola cache parse). The primary path (verified_emails_cache table populated by email-cache-refresh) is unchanged. Fail-safe: if GRANOLA_OWNER_EMAILS is empty, no meetings pass the filter (fail-closed).

**Rollback:** Revert the single function change.

---

## Gap 3: Add SKILL.md Change Warning Hook

**Problem:** Editing a SKILL.md and committing without running `deploy_skills.sh` leaves the gateway serving stale skill content. CLAUDE.md says to run the script, but no hook enforces it.

**Proposed fix:** Add a PostToolUse hook for Write/Edit operations on SKILL.md files that prints a reminder:

In `.claude/settings.json`, add to the PostToolUse Write/Edit array:

```json
{
  "matcher": "SKILL.md",
  "command": "echo '⚠️  SKILL.md changed — run: bash scripts/deploy_skills.sh before verifying'",
  "timeout": 5000
}
```

This is advisory (exit 0), not blocking. It matches the enforcement ladder: Level 1 (CLAUDE.md instruction) failed → Level 2 (hook warning). If this still gets ignored, escalate to Level 3 (auto-deploy in hook).

**Blast radius:** Minimal. Echo-only hook, 5s timeout, non-blocking. Worst case: extra reminder line in output.

**Rollback:** Remove the hook entry from settings.json.

---

## Changes NOT Proposed (and why)

1. **Recall skill enforcement (Gap 4)** — Current scale (single operator, Stop hook maintains handoff) makes this low-priority. Would matter with multiple operators.

2. **Review-gate blocking (Gap 5)** — Intentional decision (D78). Tier 2 changes don't require debate. Advisory warning is the correct level.

3. **Pre-DB parse audit logging (Gap 6)** — Known deferred gap (Phase 6F Arch-C1). Low risk — errors caught at API validation layer.

---

## Questions for Debate

1. Should contract tests run BEFORE or AFTER the Jarvis app tests in deploy_all.sh? Before means faster failure on invariant violations. After means the app is verified working first (contract tests assume a running system for some checks).

2. Is the Granola owner filter the right fix, or should the direct parse fallback be removed entirely (force reliance on the MCP-populated cache)?

3. Is a PostToolUse echo hook the right enforcement level for SKILL.md changes, or should it auto-run deploy_skills.sh?

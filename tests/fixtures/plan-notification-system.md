---
scope: "Build notification routing system for multi-channel delivery"
surfaces_affected: "scripts/notify.py, config/notification-rules.json, tests/test_notify.py"
verification_commands: "python3.11 -m pytest tests/test_notify.py -v"
rollback: "git revert <sha>"
review_tier: "Tier 1.5"
verification_evidence: "PENDING"
---

# Notification Routing System Plan

## Build Order

1. Define notification schema (event_type, severity, channel, template)
2. Build rule engine that matches events to channels based on config
3. Implement channel adapters: Slack, email, stderr
4. Add rate limiting (max 5 notifications/minute/channel)
5. Wire into existing pipeline error handlers
6. Write tests for rule matching, rate limiting, and channel dispatch

## Files

| File | Action | Scope |
|------|--------|-------|
| scripts/notify.py | Create | Core routing engine + channel adapters |
| config/notification-rules.json | Create | Event-to-channel mapping rules |
| tests/test_notify.py | Create | Unit tests for routing and rate limiting |
| scripts/debate.py | Modify | Add notification hooks to error paths |

## Verification

- `python3.11 -m pytest tests/test_notify.py -v` passes
- Manual test: trigger a pipeline error, verify Slack message received
- Rate limit test: send 10 events in 1 second, verify only 5 delivered

## Risks

- Slack API rate limits could cause notification drops during incidents
- Rule engine complexity could make debugging notification routing difficult
- Adding notification hooks to debate.py increases coupling

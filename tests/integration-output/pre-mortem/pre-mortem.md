---
mode: pre-mortem
created: 2026-04-10T19:48:37-0700
model: gpt-5.4
prompt_version: 1
---
# Pre-Mortem

## 1. Slack never delivered in production because the plan assumes networked credentials/config that don’t exist in the current runtime
**Type:** Execution failure

**Concrete failure:** Six months later, pipeline errors were “successfully routed” in code, but Slack notifications never appeared outside local manual tests because `scripts/notify.py` depended on a webhook/token env var and outbound network access that the actual pipeline environment didn’t have. The team only verified unit tests and one manual trigger in a developer environment.

**Warning sign visible today:** The plan names `scripts/notify.py`, config JSON, and tests, but does not mention:
- where Slack credentials live,
- how secrets are provisioned,
- whether the runtime can reach Slack,
- what happens on adapter failure.
Also, verification only runs `pytest tests/test_notify.py`; there is no staging/integration check in the real execution environment.

**What would have prevented it:** Before starting, require an end-to-end staging test in the same runtime as `debate.py`: inject a synthetic error, confirm Slack receipt, and fail the rollout if the webhook/env var/network path is missing. Also define a fallback path (stderr or local log) on adapter failure.

**Would prevention have changed the plan?** No, but it would have added an integration gate and likely delayed shipping until runtime constraints were solved.

---

## 2. The rate limiter suppressed the only alerts that mattered during real incidents
**Type:** Strategy failure

**Concrete failure:** A burst of pipeline failures produced hundreds of identical errors; the “max 5 notifications/minute/channel” rule dropped almost all of them, including severity-critical alerts. Operators saw a few early messages, assumed the issue was minor, and missed escalation because the limiter operated per channel, not by severity or deduped incident state.

**Warning sign visible today:** The plan hardcodes `max 5 notifications/minute/channel` with no mention of:
- severity-aware bypass,
- aggregation/deduplication,
- summary notifications,
- incident state transitions.
The schema includes `severity`, but build order never uses it for rate-limit policy.

**What would have prevented it:** At planning time, define alert semantics before implementation: critical events bypass limits, repeated identical events are aggregated into one incident with count updates, and rate limiting applies only to low/medium-noise classes.

**Would prevention have changed the plan?** Yes. The plan should have changed materially. “Simple rate limiting” is the wrong design for operational alerts; the team should not have implemented this exact limiter as specified.

---

## 3. Notification hooks in `scripts/debate.py` caused recursive failures and masked the original pipeline error
**Type:** Execution failure

**Concrete failure:** An exception path in `scripts/debate.py` called the notifier; the notifier itself threw (bad config, import error, Slack timeout, JSON parse issue), which either replaced the original exception or triggered repeated error handling. During incidents, logs showed notification failures instead of the real root cause, and in some cases the pipeline aborted earlier than before.

**Warning sign visible today:** The plan explicitly says “wire into existing pipeline error handlers” and already identifies “increases coupling” as a risk, but does not specify:
- fire-and-forget behavior,
- exception swallowing in notifier paths,
- timeout budgets,
- isolation of notification code from core pipeline execution.

**What would have prevented it:** Make notification emission non-blocking and non-fatal by contract: all notifier exceptions must be caught, logged locally, and never alter the original control flow or exception. Add a test that forces each adapter to fail while asserting the original pipeline error still propagates unchanged.

**Would prevention have changed the plan?** No, but it would have changed the implementation contract and added failure-mode tests before rollout.

---

## 4. The rule engine became unmaintainable because `notification-rules.json` could not express real routing needs without ad hoc logic in code
**Type:** Timing failure

**Concrete failure:** After a few months, teams wanted routing by environment, repo, customer, severity overrides, and temporary suppressions. The initial schema (`event_type, severity, channel, template`) was too small, so logic leaked into `notify.py` as special cases. Rules became inconsistent, tests only covered toy examples, and people stopped trusting where notifications would go.

**Warning sign visible today:** The plan starts with a minimal schema and a JSON rules file, but there is no stated source of real routing requirements, no examples of 10–20 actual events, and no validation/linting strategy for config evolution. The only noted risk is “complexity could make debugging difficult,” which is already a clue the model is underspecified.

**What would have prevented it:** Before implementation, collect a concrete rule corpus from expected users: at least 15 real event examples and desired destinations. If those examples require dimensions beyond the schema, redesign the config model first or deliberately narrow scope to one or two fixed event classes.

**Would prevention have changed the plan?** Possibly yes. If realistic rules exceeded the schema, the team should have either reduced scope or redesigned before coding. Starting with the current generic engine was likely premature.

---

## The Structural Pattern
These failures share one assumption: that a “small notification layer” is an isolated plumbing task. The plan assumes delivery channels are reachable, alert semantics are obvious, error-hook integration is safe, and routing complexity can be abstracted into a tiny schema. Those assumptions show this is mainly a sequencing problem with some strategy risk: the team is trying to generalize before validating operational reality. The plan should change: first prove one end-to-end notification path in the real runtime, then define alert policy, then add config-driven routing. Add monitoring for adapter failures, dropped events, and notifier latency; otherwise kill the “generic rule engine” part for now.

## The One Test
Run a **real-runtime incident drill** next week: deploy a minimal notifier wired only to one critical error path in `scripts/debate.py`, with Slack + stderr fallback, in the same environment where the pipeline actually runs. Trigger 20 synthetic failures over 60 seconds: 10 low severity, 10 critical. Measure:
1. Did Slack receive messages?
2. Did critical alerts bypass suppression?
3. Did notifier failures alter pipeline behavior?
4. Were dropped/suppressed events counted and logged?

If this single drill fails, do not proceed with the full config-driven routing system.
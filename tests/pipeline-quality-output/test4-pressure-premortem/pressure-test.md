---
mode: pressure-test
created: 2026-04-10T20:32:51-0700
model: gpt-5.4
prompt_version: 1
---
# Pressure-Test

## The Premise Is Wrong Because...

The main risk is that you may be treating this as a “retry infrastructure” problem when it is really a “delivery guarantee and customer trust” problem. If customers experience webhook loss as product unreliability, then the right question is not “should we add retries?” but “what minimum delivery contract do we need to be credible?”

In that framing, the answer is almost certainly yes, you need automatic retries. A manual resend script is not a serious alternative once webhook delivery is part of customers’ production workflows. The strongest version of “you’re solving the wrong problem” is this: retries alone may not solve customer pain if the real issue is lack of observability and recovery. If customers still can’t see delivery status, replay events, or trust eventual consistency, you’ve improved plumbing without fixing the trust gap.

So the proposal is directionally right, but the deeper product is “reliable event delivery,” not just “a retry queue.”

## Core Assumptions

First, this only works if most failures are actually transient. Your data suggests that: timeouts, DNS, TLS, maintenance windows. The failure case is if a meaningful share of failures are permanent misconfigurations, bad auth, malformed payload handling, or endpoints that consistently return 4xx/5xx. In that world, retries mostly add noise and delayed failure. The signal today is your 2.1% failure rate paired with incident descriptions that are overwhelmingly transient. That supports the assumption.

Second, this works if eventual delivery is good enough for customers. The design explicitly skips ordering guarantees and caps retries at 24 hours. That is fine if webhook consumers are already built to handle out-of-order, duplicate, delayed events. It fails if customers depend on near-real-time sequencing for correctness, like create-before-update flows. The signal today is whether support tickets complain about “missing” events more than “late” or “out of order” events. Your examples are about loss, not latency, which suggests eventual delivery is the real pain.

Third, this works if you can safely make retries automatic without creating downstream damage. Idempotency keys help, but only if customers use them and your event semantics are retry-safe. This fails when customer endpoints trigger non-idempotent side effects and retries cause duplicate orders, emails, or provisioning. The signal today is whether your current webhook docs already tell customers to handle duplicate delivery. If not, you are introducing a behavior change that may surprise some integrations.

## Demand-Side Forces

The push is obvious: customers hate silent data loss. Their systems drift, they discover it late, and recovery is manual and expensive. That is a strong reason to abandon the current state.

The pull is moderate but real: automatic retries turn webhook delivery from best-effort to something closer to reliable eventual delivery. The dead-letter queue and admin visibility also give customers and support a concrete recovery path.

The anxiety is stronger than the proposal acknowledges. Customers will worry about duplicate processing, delayed retries causing stale actions, and not knowing whether they should trust webhook-driven state. Internally, your team will worry about queue growth, poison messages, and replay storms after outages.

The habit is that many teams already built compensating workflows around unreliability: periodic polling, manual resync scripts, support escalations, reconciliation jobs. Even if they complain, those habits reduce urgency to switch unless reliability improves materially and is visible.

The proposal is mostly ignoring anxiety. Idempotency keys are necessary, but they do not by themselves create confidence. You need clear delivery visibility and documented semantics around duplicates and retry timing.

## Competitive Response

If this works, the platform vendors do essentially nothing, because this is not a platform-level wedge. OpenAI, Anthropic, and Google are not your real competitive constraint here. They are infrastructure enablers, not the incumbent in webhook delivery for your customers.

The nearer competitive response is from any product in your category that already offers reliable webhooks, replay, and event logs. If they see you closing the gap, they will emphasize their more complete delivery contract: replay APIs, per-endpoint observability, customer-configurable policies, maybe ordering by stream. Their move is not to copy retries; they already have them or can add them quickly. Their sales message becomes: “we don’t just retry; we make event delivery operable.”

Does your thesis survive that? Yes, if your goal is table stakes and churn prevention. No, if your goal is differentiation. A retry queue is defensive parity, not a moat.

## Counter-Thesis

The best alternative is: don’t start with a generic retry system; start with an event delivery ledger plus replay capability.

In practice that means persisting every outbound webhook attempt and exposing a way for support, or ideally customers, to replay failed events over a bounded window. You may still add retries, but the primary asset is the durable event record and recovery tooling.

Why this direction is better: it solves both transient failure and trust. Automatic retries reduce loss, but replay and visibility reduce uncertainty. If I had to choose one foundation, I’d rather build the ledger that enables retries, dead letters, dashboards, and manual replay than build a narrow queue mechanic first.

## Timing

This should happen now. A 2.1% permanent loss rate is already too high for production webhooks, and the incident examples show repeated customer-facing failures. At 8,000 deliveries/day, that’s not edge-case territory.

What I would wait on: customer-configurable retry policies and ordering guarantees. Those are complexity multipliers and you do not yet need them.

The window closing is customer trust. Every additional lost event teaches customers to build around you or not depend on you. The window that has not fully opened yet is advanced workflow semantics: ordering, per-tenant tuning, long retention replay. Don’t overbuild for that now.

## My Honest Take

If this were my decision, I would absolutely build automatic retries now, and I would not ship the “log to file + manual resend” version except as a temporary emergency patch measured in days.

But I would slightly reframe the implementation: persist every webhook delivery attempt in Postgres, use Sidekiq for scheduled retries with exponential backoff, classify retryable vs non-retryable failures, add idempotency keys, and make dead-lettered events visible in an internal dashboard from day one. That gives you the retry queue, plus the beginnings of a delivery ledger.

The two things that matter most are: stop silent permanent loss, and make failures visible and recoverable. If you do only those two, this is a strong move. If you treat it as just “background retries,” you’ll fix the symptom but leave the trust problem half-solved.
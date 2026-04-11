---
mode: pressure-test
created: 2026-04-10T19:48:37-0700
model: gpt-5.4
prompt_version: 1
---
# Pressure-Test

## The Premise Is Wrong Because...

The proposal is probably solving the symptom, not the full problem. The real issue is not “we need retries.” It’s “customers need a reliable event delivery contract they can operationally trust.”

Retries are the obvious first fix, but if the product promise becomes “webhooks usually arrive after some retries,” that still leaves customers exposed to ambiguity: Was it delivered? In what order? Can I replay? How do I detect gaps? If customers use webhooks for sync-critical workflows, silent loss is only one failure mode.

So the stronger framing is: should you build a minimal reliability layer now, or invest in a proper event delivery product surface? For your scale, the answer is likely the former. But it matters because you should design this as the first step toward delivery visibility and replay, not as a narrow queue patch.

## Core Assumptions

First assumption: most failures are transient and retries will recover a large share of them.  
This fails if a meaningful chunk of failures are actually permanent misconfiguration problems: bad URLs, expired certs, auth mismatches, customer endpoints that consistently time out. In that world, retries just turn permanent failures into delayed permanent failures.  
A signal visible today: your incident examples are mostly transient-looking, and the 2.1% failure rate is described as mostly timeouts, DNS, TLS. That supports the assumption, but you should verify what percentage of failures would have succeeded within 24 hours.

Second assumption: a database-backed queue plus periodic worker is operationally sufficient at your scale.  
This fails if retries create bursts, duplicate load, or stuck queue behavior that affect primary DB health or delay delivery enough to create customer-facing lag. It’s not likely at 8,000 deliveries/day, but it matters if volume or endpoint count rises fast.  
A signal visible today: your volume is tiny for Postgres + Sidekiq. The proposed architecture is more than enough now.

Third assumption: customers value “eventually delivered” enough that this meaningfully improves retention/trust, even without ordering guarantees or self-serve replay.  
This fails if your most important customers care less about transient recovery than about observability and control. Then they’ll still see the system as unreliable because they can’t inspect, replay, or reconcile confidently.  
A signal visible today: customers are discovering problems hours later and needing manual resync. That suggests visibility/replay is nearly as important as retries.

## Demand-Side Forces

The push is strong: customers hate silent loss. Their systems drift, they lose trust, and they burn support time reconciling data after endpoint blips.

The pull is moderate but real: automatic retries plus a dead-letter view gives them a much more credible reliability story. Idempotency keys also reduce fear of duplicates.

The anxiety is what the proposal underweights. Customers will worry about duplicate side effects, delayed delivery causing stale downstream actions, and lack of clarity on whether an event is still pending, failed, or permanently lost. “We retry” is helpful, but buyers often need “we can see exactly what happened.”

Habit favors the status quo more than it appears. Internally, teams tolerate bad webhook reliability because manual fixes exist and because changing delivery semantics can create downstream surprises. Externally, customers already built compensating processes around polling, reconciliation, and support escalation.

The force being most ignored is anxiety. Not “will retries work technically,” but “can I trust this system enough to automate against it?”

## Competitive Response

If this works, platform vendors won’t care directly; this is table stakes, not a wedge against OpenAI, Anthropic, or Google. But if your thesis is “reliable webhook delivery becomes strategic differentiation,” the response from adjacent competitors is easy: they add retries, delivery logs, and replay quickly because these are expected features.

The nearest competitor response is specific: they won’t just match retry logic; they’ll package reliability as a customer-facing feature set — webhook history, per-endpoint health, replay, alerting, maybe ordering by key. That can neutralize your move if you stop at infrastructure.

Does the thesis survive? Yes, if the thesis is “we must reach baseline reliability fast.” No, if the thesis is “retry queue alone creates durable advantage.”

## Counter-Thesis

The better alternative direction is: build a customer-visible delivery ledger and replay capability, with basic retries as a byproduct.

Why? Because the painful part for customers is not only missed delivery; it’s loss of control when delivery fails. A ledger gives supportability, trust, and a path to self-serve recovery. Even a simple endpoint activity page with statuses and manual replay can outperform a pure backend retry system in customer value.

If I had to choose one strategic direction, I’d choose “observable event delivery” over “retry mechanism.” Retries should exist, but as part of that surface, not as the whole bet.

## Timing

Yes, this is the right move now, but only if kept tightly scoped.

The window that is closing: the ability to treat dropped webhooks as an acceptable ops issue. At 2.1% permanent loss, you already have a product trust problem, not an engineering cleanup task.

What I would not wait for: higher scale, configurable policies, signature rotation, or ordering guarantees. Those are distractions right now.

What hasn’t opened yet: a more complex delivery platform with per-customer policy controls or guaranteed ordering. Your volume and maturity don’t justify that.

What I would wait for before overbuilding: evidence that customers actually need replay, ordering by entity, or custom retry behavior beyond a standard policy.

## My Honest Take

If this were my decision, I would absolutely build automatic retries now. The simplest version with file logs and manual resend is not defensible given you already know failures are frequent and customer-visible.

But I would slightly change the scope: build the persistent retry queue and dead-letter handling, and make sure every delivery attempt is queryable in an internal or lightweight customer-facing log. That gives you both reliability improvement and operational visibility.

I would not spend time right now on configurable retry schedules or ordering guarantees. I would spend a little extra to ensure this is framed as the first version of a delivery reliability layer, not a one-off queue.

So: yes to the proposal, no to the manual resend stopgap, and add minimal delivery history because trust, not just retries, is the real product problem.
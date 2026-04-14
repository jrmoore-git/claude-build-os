---
mode: pressure-test
created: 2026-04-13T17:18:07-0700
model: gpt-5.4
prompt_version: 1
---
# Pressure-Test

## The Premise Is Wrong Because...

You may be solving “which model should answer?” when the real problem is “how do we increase decision quality and consistency at the lowest latency/cost?”

Those are not the same. Model routing is only one lever, and maybe not the most important one. The strongest version of the objection is: the observed differences between models are not stable enough to encode into a routing layer; they may mostly reflect prompt framing, sample variance, and the fact that different review goals need different output structures more than different base models. If that’s true, a routing system adds ceremony around an illusion.

The better question might be: when should the system use one model, a panel, or external research, and what evidence should trigger each mode? That reframes the problem from static model preferences to decision policy. “Auto” should ideally choose the review mode, not just the vendor.

## Core Assumptions

First, this only works if model strengths are durable enough to operationalize. The failure case is obvious: GPT catches blockers this week, Gemini next month after a silent update, and Claude varies by context length or prompt style. Then your routing table becomes stale folklore. The signal today is weak but real: you already have anecdotal repeatability across sessions, but not a benchmark with enough tasks to prove stability.

Second, task type must be inferable cheaply from artifacts like frontmatter, file names, and prompt wording. This fails when real requests are mixed: “review this proposal for strategic coherence and implementation risk, and flag missing external facts.” That’s not one task type. Heuristics will map messy work into neat buckets and lose the reason the user asked. The signal today is your own examples: “implementability,” “strategy,” “diff,” “proposal” are clean toy cases, but actual review prompts often bundle two or three intents.

Third, misrouting has to be low-cost enough that users still trust auto. This fails if the wrong model doesn’t just produce a slightly worse answer, but a misleadingly confident one—especially for external-knowledge cases where not using Perplexity matters. The signal today is that you’re treating misclassification as merely “suboptimal,” but for research-sensitive tasks it can be qualitatively wrong, not marginally worse.

## Demand-Side Forces

The push is real: users are frustrated by having to remember which model is good at what, and ad-hoc selection creates inconsistent outputs. That’s a workflow tax.

The pull is also strong: “review --model auto” is elegant. It makes the tool feel opinionated and mature. The best attraction is not intelligence; it’s removing a choice.

The anxiety is bigger than the draft admits: users will fear losing control and not knowing why a weaker model was picked, especially when they already have model preferences. They’ll worry that “auto” optimizes convenience over quality.

The habit is the current mental shortcut: people already know “for code review use X, for strategy use Y,” and they’ll keep doing that because explicit model choice is legible and blame-free.

The proposal is mostly ignoring anxiety. Logging to stderr helps, but it doesn’t solve the core fear: can I trust this when the task is ambiguous or high-stakes?

## Competitive Response

If this works, the platform vendors don’t need to copy your exact feature; they collapse the value by improving general-purpose routing primitives inside their APIs. OpenAI, Anthropic, and Google are all moving toward bundled model families, tool use, reasoning modes, and agentic orchestration. They can make “auto” a native capability: classify intent, escalate model depth, call search when needed. If that becomes standard, your routing logic is not a moat.

The nearer competitor response is more immediate: a rival debate/review tool won’t build a static routing map; they’ll build adaptive evaluation loops—run a cheap first pass, escalate if uncertainty is high, trigger web research only when claims appear unverifiable. That beats hand-authored routing tables because it optimizes for answer quality, not presumed model specialty.

Does your thesis survive? Partially, if you treat this as a UX feature, not a strategic differentiator. It probably does not survive as a core long-term architecture.

## Counter-Thesis

I’d pursue confidence-based orchestration instead of task-type routing.

The alternative is: default to a strong, cheap-enough generalist for first pass; then escalate based on uncertainty, detected claim types, or explicit user goals. For example: if the review contains factual claims or references unknown dependencies, trigger research; if the output confidence is low or the task mixes strategy + implementation, call a second model; if the artifact is a diff, maybe panel it.

Why this is better: it matches how users actually switch—based on risk and ambiguity, not artifact category. It also ages better as models converge. The policy becomes “when to spend more” rather than “Claude for strategy, GPT for implementation,” which is likely to rot.

## Timing

There is a good reason to do something now: the window for simplifying the interface is open, and “auto” is a meaningful product improvement today.

But it’s too early to harden vendor-strength beliefs into the core abstraction. What I would wait for is even a lightweight internal benchmark across a few dozen tasks showing repeatable deltas by task family. Without that, your routing map is intuition encoded as config.

The window that is closing: users’ tolerance for manual model-picking. “Auto” is becoming table stakes.

The window that hasn’t opened yet: durable long-term model specialization. The vendors are converging fast, and external search/tool use is being integrated into baseline offerings.

## My Honest Take

If this were my decision, I would ship `auto` now, but I would narrow the claim and change the design center.

I would not position it as “intelligent model routing based on stable model strengths.” I would position it as “opinionated default selection with transparent override.” Start with explicit, high-confidence cases only: diff/code review, proposal/strategy review, and explicit web-research triggers. Keep Perplexity opt-in or triggered only by very clear signals. Log the routing reason. Make manual override first-class.

At the same time, I’d instrument every auto decision and collect outcomes so you can learn whether the routing is actually improving quality. And I’d design the next version around escalation policy, not taxonomy classification.

So: yes to shipping a small heuristic `auto`; no to believing the main value is static model-task matching. The useful thing here is reducing user choice friction, not discovering a durable routing advantage.
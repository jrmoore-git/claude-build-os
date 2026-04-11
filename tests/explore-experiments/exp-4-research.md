---
mode: explore
created: 2026-04-10T23:40:23-0700
model: gpt-5.4
directions: 3
prompt_versions: explore=2, diverge=3, synthesis=3
---
# Explore: What is the right approach to evaluating LLM output quality for a production sys

## Direction 1

## Brainstorm
1. Stand up a conventional offline gold-set evaluation: build a few hundred labeled summaries, score every model/prompt change against them, and gate releases on aggregate quality.
2. Expand manual QA into a statistically designed sampling program with daily stratified human review, control charts, and explicit incident thresholds.
3. Build a lightweight real-time canary monitor using LLM-as-judge on a small live sample of outputs, alerting on drift in factuality, completeness, and policy violations within minutes.
4. Reframe evaluation away from “average summary quality” and toward “failure-mode surveillance,” with detectors specifically for blank outputs, truncation, hallucinated entities, missing key facts, and formatting regressions.
5. Use user behavior as the ground truth: instrument downstream actions like regenerate, complaint rate, abandonment, and copy/share patterns to infer summary usefulness without labeling every output.
6. Do the uncomfortable thing and stop trying to score all outputs; instead, route only uncertain or high-risk summaries to expensive review and treat evaluation as selective auditing rather than universal measurement.
7. Adopt a third-party observability/evals platform immediately, accepting some lock-in, because the real bottleneck is operational discipline rather than metric design.
8. Try a weird “shadow model tribunal”: run two cheap alternative summarizers plus the production model, and alert when the production summary meaningfully disagrees with the ensemble.
9. Use no ground truth at all: define structural invariants from the source document—coverage of named entities, numbers, sections, and claims—and treat violations as likely quality failures.
10. The question is wrong: the primary issue is not evaluation but blast radius, so the system should shift to safe deployment mechanics—canaries, rollback, traffic splitting, and model version kill-switches—with eval only as a support function.

## Direction: Failure-Mode Surveillance, Not “Quality Scoring”

## The Argument
The right approach is to stop treating evaluation as a single scorecard problem and build a lightweight, real-time failure-mode surveillance system for production summaries. Your incidents were not “the average quality dropped from 4.3 to 4.1.” They were operational failures that shipped for hours. The job is early detection of bad regimes, not academic measurement of summary quality.

This differs sharply from the obvious approaches: it uses a **hybrid method** (automated checks plus LLM-as-judge), focuses on **failure modes rather than per-output or aggregate scoring**, runs in **real time**, uses **no traditional ground-truth labels for the live monitor**, and starts with **lightweight scripts instead of a full platform**.

### 1. Why now?
Two things changed. First, LLMs are now good enough at critique to reliably flag narrow defects—hallucinated numbers, omitted critical facts, malformed output—especially when judging against the source text. Two years ago, using an LLM to monitor another LLM in production would have been too noisy and too expensive. Second, your system’s scale makes manual detection non-credible: 10k summaries/day with incidents lasting hours means your current review loop is structurally too slow. The requirement today is operational observability, not better spot-checking.

### 2. What’s the workaround?
Teams today do one of three things: manual spot checks, offline benchmark sets, or waiting for user complaints. Those workarounds prove the demand: everyone wants confidence before and after deployment. But they also reveal the constraint: small teams cannot maintain full eval infrastructure, and customer-facing systems cannot tolerate hours-long blind spots. Your own setup—50 manual checks/day and three incidents in two months—is exactly the workaround failing in the wild.

### 3. Moment of abandonment
People abandon the current approach at the moment they realize the review process is answering the wrong question too late. Specifically: a model or prompt regression goes live at 10:00 AM, summaries subtly start dropping key findings or inventing entities, no one notices until support tickets or an engineer happens to sample the right outputs in the afternoon. That is the failure point to design backward from. You need minute-scale warning on concrete failure signatures, not end-of-day averages.

### 4. 10x on which axis?
This is 10x better on **time-to-detection**. That is the single axis that matters because your main business problem is incident duration. If you can cut detection from hours to 10–15 minutes, you massively reduce blast radius. On other axes, this is merely good enough: it won’t perfectly measure nuanced summary quality, and it may miss some subtle degradations. That weakness does not kill adoption because the current pain is production incidents, not leaderboard precision.

### 5. Adjacent analogy
This is how fraud detection beat manual audit in payments. Banks did not solve fraud by assigning every transaction a perfect human-verified “legitimacy score.” They built layered detectors for suspicious patterns, prioritized fast alerts, and escalated uncertain cases. The mechanism transfers directly: production summaries are high-volume outputs where a small class of failures causes disproportionate damage, so anomaly/failure detection creates more value than universal grading.

The system should watch a live sample of summaries and score them against a handful of explicit failure modes:
- unsupported claims / hallucinated entities or numbers
- omission of key findings
- truncation / empty / malformed outputs
- instruction non-compliance / formatting regressions
- abnormal drift in length, reading level, or citation patterns

For each sampled summary, run:
1. deterministic checks (length, parseability, banned patterns, truncation),
2. source-to-summary invariants (entity/number consistency),
3. LLM judge prompts for a few narrow questions, not a holistic “is this good?”

Aggregate by model version, prompt version, customer segment, and document type. Alert on spikes, not single failures.

## First Move
Next week, one engineer should implement a monitor on a **200-summary/day live sample** plus all canary traffic. Define **5 failure modes**, write **3 deterministic checks** and **2 LLM-judge prompts** per mode, and log results to a simple dashboard in SQL + Grafana or even a daily notebook. Add alerts when any failure rate doubles versus the 7-day baseline or exceeds an absolute threshold. Tie alerts to an immediate rollback playbook.

## Why This Beats the Alternatives
**Offline gold set:** useful for pre-release regression testing, but it does nothing for live incidents and will miss distribution shifts or integration bugs.

**More human review:** better than today, but still too slow and too expensive for 10k/day; it improves measurement coverage, not detection latency.

**Single aggregate LLM score:** seductive but weak operationally. When the score moves, you won’t know why, and broad quality scores are noisier than narrow defect checks.

## Biggest Risk
The biggest risk is judge unreliability: if the LLM monitor is too noisy, engineers will ignore alerts. The fix is to keep the scope narrow—judge specific defects, calibrate on a small manually reviewed set, and measure alert precision before turning on paging.

---

## Direction 2

## Brainstorm
- **Canary prompts + rule-based drift alarms** *(automated metrics; aggregate/system-level; real-time monitoring; reference outputs + invariants; lightweight scripts)*  
- **User-friction telemetry as quality proxy** *(user behavior; aggregate; user-signal-driven; no explicit labels; lightweight-to-medium)*  
- **Shadow-model disagreement monitor** *(hybrid automated; per-output triage; real-time; none/reference-free; medium investment)*  
- **LLM failure taxonomy classifier on every summary** *(LLM-as-judge; failure-mode detection; real-time; no ground truth; lightweight scripts)*  
- **Input-distribution sentry with risk-triggered review** *(automated; upstream risk detection not output scoring; real-time; none; lightweight)*  
- **Weekly adversarial “red team packet” gate** *(human + automated; batch; failure-mode stress testing; expert-designed probes; lightweight)*  
- **Customer-visible inline “wrong/misleading” capture loop** *(user-signal-driven + human verification; per-output incidents; continuous; user reports; medium)*  
- **Contrarian: SLOs on incident detection time, not quality score** *(operational metrics; aggregate reliability; real-time; none; lightweight)*

## Direction: LLM Failure-Taxonomy Classifier on Every Summary

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| The assumption that quality evaluation requires human spot-checking as the primary mechanism | Manual review volume from random sampling to targeted audit only | Coverage, speed of detection, and explicit failure-mode visibility | A production “summary safety monitor” that classifies likely failure types on 100% of outputs and pages on spikes |

## The Argument
The right approach is **not quality scoring**. It is **real-time failure-mode surveillance** across every summary.

You have 10k summaries/day and incidents that lasted hours. The problem is not “we can’t estimate average quality precisely.” The problem is “we cannot detect bad states fast enough.” So build a monitor that runs on every output and asks a narrow set of questions:

- Is the summary unsupported by the source?
- Does it omit critical findings?
- Does it overstate confidence or novelty?
- Does it contradict the source?
- Is it malformed, incomplete, or off-format?

Use an LLM judge with a strict rubric to assign **binary/ternary flags by failure mode**, not a single score. Aggregate those flags by hour, model version, customer segment, document type, and prompt version. Alert when rates spike above baseline. Then send only flagged examples to humans.

This differs structurally from spot-checking and from generic eval sets:
- **Evaluation method:** LLM-as-judge, not primary human review
- **Granularity:** failure-mode detection, not overall quality score
- **Feedback loop:** real-time monitoring, not offline batch
- **Ground truth:** no labeled dataset required to start
- **Investment:** lightweight service/scripts, not a heavy eval platform

### Why now?
Two things changed. First, your incident profile: three degradations in two months means you have an operations problem, not just a research problem. Second, LLM judges are now good enough for **narrow rubric classification** even when they are weak at broad “is this good?” scoring. You do not need perfect judgment; you need a stable detector for relative spikes.

### What’s the workaround?
Today teams do one of three weak substitutes:
1. random manual spot checks,
2. offline benchmark sets that miss production drift,
3. waiting for customers or PMs to notice.

All three are too slow for an always-on customer-facing summarization system.

### 10x on which axis?
**Time-to-detection.**  
Move from “hours until someone notices” to “minutes until the failure-rate dashboard and alert trip.”

### Adjacent analogy
This pattern already won in **fraud detection** and **site reliability engineering**. Banks do not manually inspect random transactions to estimate fraud quality; they run classifiers on all traffic and investigate flagged clusters. SRE teams do not read random logs; they monitor error budgets and anomaly spikes.

## First Move
This week, have one ML engineer define a **5-category failure taxonomy** and a judge prompt with yes/no outputs plus evidence spans from the source text.

Then:
1. Sample 500 recent summaries.
2. Run the judge over them.
3. Have the team manually review 100 judged examples to calibrate the rubric.
4. Set baseline failure rates.
5. Put the judge in the production pipeline asynchronously.
6. Alert in Slack when any failure mode exceeds, say, 2x trailing 7-day baseline for 15 minutes.

Affected team: all 4 ML engineers. Change: manual review becomes targeted review of flagged outputs, not random sampling.

## Why This Beats the Alternatives
**Manual spot-checking** is dead on arrival at 0.5% coverage. It cannot catch hour-scale incidents reliably.

**Reference-set benchmarking** is useful for releases but blind to production shifts, novel documents, prompt regressions, and downstream formatting bugs.

**User feedback loops** arrive too late and are sparse for summarization; many users consume bad summaries without reporting them.

**Shadow-model disagreement** detects instability, not correctness. Two models can agree on the same hallucination.

**Input-distribution monitoring** helps, but it watches causes, not the customer-visible failure itself.

And it beats the previous “quality scoring” mindset because a single score hides the operational truth. You need to know *what is breaking* and *whether it is spiking now*.

## Biggest Risk
The judge may be noisy or systematically biased, causing false alarms or missed incidents. If the taxonomy is vague, the system collapses into unreliable pseudo-scoring. The fix is to keep categories narrow, require evidence extraction, and calibrate weekly against a small human-reviewed set.

---

## Direction 3

## Brainstorm
- **Canary benchmark replay gate** — maintain a fixed, versioned set of representative docs + gold/reference summaries; every model/prompt change must beat baseline before rollout. **[Eval: automated + human signoff; Granularity: aggregate release-level; Loop: offline pre-release; Ground truth: reference outputs/expert set; Investment: lightweight-to-mid]**
- **Shadow A/B with user-behavior proxies** — send a slice of traffic to challenger summaries invisibly, compare downstream user actions like copy rate, open time, regenerate rate, complaint rate. **[Eval: automated; Granularity: aggregate cohort-level; Loop: real-time/user-signal-driven; Ground truth: user behavior; Investment: mid]**
- **Inline reviewer workflow for high-value summaries** — route only summaries on important accounts/topics to analyst review before delivery; use acceptance/edit distance as the metric. **[Eval: human-in-the-loop; Granularity: per-output on selected tier; Loop: real-time; Ground truth: reviewer actions; Investment: operational process]**
- **Edit-based quality measurement** — expose lightweight “edit summary” UI internally or to trusted users; measure how much humans rewrite before accepting. **[Eval: human behavior metric; Granularity: per-output + aggregate; Loop: user-signal-driven; Ground truth: edits; Investment: product instrumentation]**
- **Synthetic perturbation stress suite** — automatically mutate source docs (length, contradictions, tables, jargon) and verify summary invariance/sensitivity properties before deployment. **[Eval: automated property tests; Granularity: aggregate robustness; Loop: offline CI; Ground truth: generated perturbation expectations; Investment: lightweight scripts]**
- **Backtest against business outcomes** — link summary exposure to later ticket escalations, analyst trust scores, or customer churn signals to evaluate models monthly. **[Eval: automated analytics; Granularity: aggregate outcome-level; Loop: delayed feedback; Ground truth: business outcomes; Investment: mid/high]**
- **Contrarian: Deliberate low-rate friction prompt** — randomly ask end users “Was this summary sufficient to act?” before they proceed; optimize for verified usefulness, not textual quality. **[Eval: user survey; Granularity: per-output sampled; Loop: real-time user-driven; Ground truth: explicit user judgment; Investment: low/mid]**
- **Contrarian: Escalation-by-uncertainty product design** — stop trying to score every summary; redesign delivery so uncertain cases are shown with source highlights and “verify before use,” then measure reduction in bad decisions. **[Eval: hybrid product/outcome metric; Granularity: risk-tier aggregate; Loop: real-time; Ground truth: user behavior + outcomes; Investment: product/process]**

## Direction: Shadow A/B with user-behavior proxies

## ERRC Grid
| Eliminate | Reduce | Raise | Create |
|-----------|--------|-------|--------|
| The assumption that quality must be judged primarily by reading summaries one by one | Manual spot-checking to a small calibration sample instead of the main measurement system | Continuous, production-side evidence of whether summaries are actually useful and trusted | A live “quality telemetry” layer that evaluates summaries by how users behave after seeing them |

## The Argument
The right approach is to instrument **live user-behavior evaluation** and use it as the primary quality signal for production, with a small manual calibration set as backup.

Your current problem is not just “we don’t know if the text looks good.” It’s that degraded summaries can ship for hours and no one notices. That is a **detection latency** problem. Manual review of 50/day cannot solve it. Nor will a taxonomy classifier on every summary; that tells you what the model might be doing wrong, not whether users are getting less value.

Instead, run a shadow or low-risk A/B evaluation in production and measure behavior that reveals quality:
- regenerate/click-to-expand-source rate
- copy/export/share rate
- time-to-first-action after reading
- abandonment after summary view
- thumbs-down / complaint / support-contact rate
- human edit rate if summaries are editable internally

These are aggregate metrics by model version, customer segment, document type, and hour. If a new prompt/model causes users to expand the source much more and regenerate more, quality dropped even if the summary still “looks fluent.”

**Why now?** Two reasons. First, you already have enough volume: 10k summaries/day is plenty to detect shifts fast. Second, the incidents prove pre-release intuition is insufficient; you need production observability, not more artisanal review.

**What’s the workaround today?** Teams do spot checks, ad hoc Slack reports, and wait for customers to complain. That is exactly why degraded quality ships for hours.

**10x on which axis?** **Time-to-detection.** This cuts detection from hours or days to near-real-time because it uses every interaction, not 0.5% sampled reading.

**Adjacent analogy:** This is how search and recommendation systems are evaluated in practice. They do not rely mainly on humans judging every result; they watch CTR, dwell time, reformulation, abandonment, and downstream task completion. Summaries should be treated the same way: as a product component whose quality is revealed by user behavior.

This is structurally different from the obvious approaches. It is not per-output grading, not failure-mode classification, not an offline benchmark. It is **live aggregate outcome measurement** using **user behavior as ground truth**.

## First Move
Instrument three events this week for every summary impression: **summary shown**, **source expanded**, and **regenerate/complaint action**. Then assign 5–10% of traffic to a shadow challenger or holdout prompt/model and build a daily dashboard by version and document type. The PM and one ML engineer own metric definitions; one product engineer adds the events; one ML engineer runs the experiment analysis.

## Why This Beats the Alternatives
The obvious approach is to scale up manual review. That improves confidence but not detection speed, and it does not scale with 10k/day. Another obvious approach is an offline benchmark. Useful for release gating, but it still misses production drift, odd customer mixes, and prompt regressions after deployment.

And it beats the previous directions because:
- **Not failure-mode surveillance:** this is not watching for predefined error classes; it measures whether users succeed.
- **Not an LLM judge on every summary:** no synthetic textual grader is the source of truth here; users are.

In short: the previous directions ask, “Did the summary appear wrong?” This direction asks, **“Did the summary help the user do the job?”** That is the metric that matters in production.

## Biggest Risk
The proxy metrics can be noisy or misleading if the product instrumentation is weak. For example, high source-expand rate could mean curiosity, not bad summaries. If you choose poor proxies, you’ll optimize the wrong thing. The fix is to start with a small manual calibration study and validate which behaviors actually correlate with summary usefulness before making them operational gates.

---

## Synthesis

## The Fork

The real choice is Bet A: Failure-Mode Surveillance vs Bet B: User-Behavior Telemetry vs Bet C: Offline Gold-Set Release Gate.

## Bet A: Failure-Mode Surveillance
Build a real-time monitor for production summaries that flags specific failure modes: hallucinated entities/numbers, missing key facts, truncation, malformed output, and policy/format regressions. This fits your actual pain: incidents lasting hours. Use hybrid checks—deterministic rules plus narrow LLM-as-judge prompts against the source text—on live samples or all canary traffic. Aggregate by model, prompt, segment, and doc type; page on spikes. This differs from “quality scoring” because it optimizes time-to-detection, not average score precision.
**First move:** Next week, define 5 failure modes, implement 3 deterministic checks and 2 judge prompts per mode, run on 200 live summaries/day plus canaries, and alert on 2x baseline spikes.
**Sacrifice:** You give up a single clean quality number and deeper insight into whether summaries are broadly useful, not just visibly broken.

## Bet B: User-Behavior Telemetry
Treat users as the ground truth. Instrument production so summary quality is inferred from behaviors like regenerate rate, source-expand rate, complaint rate, abandonment, copy/share, and time-to-action. Run shadow A/Bs or low-rate challenger traffic and compare cohorts by model, prompt, and document type. This bet says the right question is not “Did a judge dislike the text?” but “Did the summary help the user?” It is strongest if you care about real utility over textual correctness and have enough volume to detect shifts quickly.
**First move:** Ship events for summary shown, source expanded, regenerate, and complaint; route 5–10% of traffic to a challenger; build a daily dashboard by version and segment.
**Sacrifice:** You give up fast diagnosis of *what* broke. Behavior tells you usefulness changed, but not the failure mode causing it.

## Bet C: Offline Gold-Set Release Gate
Stand up a conventional pre-release eval: a few hundred representative documents with expert-labeled or reference summaries, scored on every model/prompt change. Gate rollouts on aggregate quality plus targeted human signoff on risky slices. This is the direct, obvious answer if your main need is disciplined release management rather than live observability. It gives a stable benchmark, clearer before/after comparisons, and a shared language for model changes. It is best when regressions mostly come from releases, not runtime drift.
**First move:** Curate 300 representative documents across key segments, create reference labels/rubrics, baseline the current system, and require every change to beat baseline before rollout.
**Sacrifice:** You give up rapid detection of production-only issues—distribution shift, integration bugs, and post-release regressions can still run for hours before anyone notices.

## Comparison

| | Timeline | Risk | What you learn | Strategic sacrifice |
|---|----------|------|----------------|---------------------|
| **Bet A** | 1–2 weeks to first useful alerts | Judge noise causes false alarms or alert fatigue | Which failure modes spike in production, where, and how fast you can catch them | A unified quality benchmark and direct measurement of user value |
| **Bet B** | 2–4 weeks once instrumentation and traffic split are live | Proxy metrics may be confounded or too noisy to trust | Whether summaries actually improve user success and which variants help or hurt | Fine-grained diagnosis of textual failure modes and pre-release certainty |
| **Bet C** | 2–6 weeks to build a reliable set and gating process | Dataset becomes stale or unrepresentative; humans disagree on labels | Whether new models/prompts beat baseline before launch | Production observability and fast response to live incidents |
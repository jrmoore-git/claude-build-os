---
debate_id: learning-velocity-findings-v2
created: 2026-04-11T22:20:07-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# learning-velocity-findings-v2 — Challenger Reviews

## Challenger A — Challenges
## Challenges

1. **UNDER-ENGINEERED** [MATERIAL] [COST:MEDIUM]: **Hook "fired in last 30 days" check has no data source.** The proposal says pruning should check "has this hook fired in the last 30 days?" but there is no hook firing log anywhere in the system. Searches for `hook_log`, `hook_audit`, `hook_fire`, `HOOK_BLOCKED`, and `hook_blocked` across both scripts and skills returned zero matches. The `audit_log` reference in scripts appears to be a single mention, not a hook-tracking system. Without a hook execution log, this pruning criterion is unimplementable. You'd need to either (a) add logging to all 17 hooks first, or (b) use git log as a proxy for hook-triggered changes, which is lossy and unreliable. This is the one part of the proposal that requires new infrastructure the proposal claims it doesn't need.

2. **ASSUMPTION** [MATERIAL] [COST:SMALL]: **Rule-hook redundancy detection assumes semantic comparison is tractable.** The proposal says "for each rule: does a hook already enforce this?" No existing code performs this comparison — searches for "hook already enforce" and "does a hook" returned zero matches in skills. Determining whether a hook enforces the same thing as a rule requires either (a) manual annotation of rule-hook pairs, or (b) LLM-based semantic comparison, which adds cost and non-determinism to `/healthcheck`. The proposal doesn't specify which approach, and the "simplest version" section wisely defers this — but the main proposal presents it as a concrete capability without acknowledging the implementation gap.

3. **RISK** [ADVISORY]: **Auto-triggering `/investigate --claim` from `/healthcheck` couples two skills with different cost profiles.** The proposal acknowledges investigate costs ~$0.05-0.10 per call (EVIDENCED from proposal text). Running 2-3 during a healthcheck full scan adds $0.10-0.30 per scan. At current low frequency this is fine, but if healthcheck trigger conditions change (e.g., lessons count rises toward 25), this could fire more often than expected. The proposal's "top 2-3 stalest" cap is a reasonable guard, but the coupling means healthcheck's cost profile becomes unpredictable to users who don't know investigate is being called underneath.

4. **OVER-ENGINEERED** [ADVISORY]: **4 velocity metrics may be premature given the data volume.** With ~12 active lessons and commits concentrated on a single day (2026-04-11 based on the 10 most recent commits to lessons.md all being from that date — EVIDENCED), git log math will produce noisy, low-N metrics for weeks. The proposal's "simplest version" section already handles this correctly by suggesting to evaluate after 2-3 sessions, but the main proposal presents all 4 metrics as the measurement capability rather than starting with 1-2 that would be meaningful at current scale (e.g., just "lessons resolved per week" and "mean time to promotion").

5. **ALTERNATIVE** [ADVISORY]: **Hook pruning could use static analysis instead of runtime logs.** Rather than tracking hook firings (which requires new infrastructure per challenge #1), you could check whether the *conditions* a hook guards against still exist in the codebase. For example, if a hook validates a file format, check whether that file format is still in use. This is a static check that requires no new logging infrastructure and aligns with the "no new infrastructure" constraint.

## Concessions

1. **The phased approach is exactly right.** The "simplest version" section (git log metrics only, ~15 lines, evaluate before expanding) is disciplined and avoids the trap of building all three capabilities at once. This is good engineering judgment.

2. **The problem is real and well-evidenced.** 3 of 4 lessons having stale/wrong information (EVIDENCED from the 2026-04-11 investigation) is a concrete failure that justifies action. The system genuinely accumulates governance without measuring or pruning it.

3. **Extending `/healthcheck` rather than creating a new skill is the right structural choice.** It keeps the component boundary clean — healthcheck already owns system-state assessment, and these are all system-state assessments.

## Verdict

**REVISE** — The measurement (velocity metrics) and verification (auto-investigate) capabilities are sound and should proceed as described in the "simplest version" section. The pruning capability needs revision: rule-hook redundancy detection needs a specified mechanism, and hook-firing tracking requires infrastructure that doesn't exist. Recommend implementing pruning as a second phase after adding hook execution logging (COST:MEDIUM) or switching to the static-analysis alternative. The two MATERIAL findings are both in the pruning capability; the rest of the proposal is solid.

---

## Challenger B — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The scheduled verification step crosses a trust boundary from local repo state into an LLM-driven investigation without any explicit guardrail on what lesson content is passed through. Since lessons can contain arbitrary text, auto-running `/investigate --claim` on selected entries creates a prompt-injection and data-exfiltration path to external models unless the implementation constrains inputs to specific claim fields and strips unrelated context. This matters because the proposal makes the trigger automatic rather than operator-initiated. Risk of changing: unintended disclosure or manipulated investigations; risk of not changing: stale lessons continue poisoning sessions.  
2. [ASSUMPTION] [ADVISORY]: The proposal assumes `git log` on `tasks/lessons.md` is a meaningful proxy for “learning velocity,” but commits to a single file can reflect formatting, archival churn, or bulk edits rather than validated improvement. That does not invalidate shipping the metrics, but the metrics should be labeled directional, not authoritative.

3. [UNDER-ENGINEERED] [ADVISORY]: The hook-pruning heuristic “has this fired in the last 30 days?” assumes reliable hook firing telemetry exists and is attributable per hook. I verified `scripts/debate.py` exists and references logging, but I did not verify a hook-specific usage log or jobs config for `/healthcheck`; the job schedule lookup failed because `config/jobs-config.json` was missing. Without verified telemetry, this pruning signal is SPECULATIVE and may misclassify low-frequency but high-value protections.

4. [ALTERNATIVE] [ADVISORY]: The “simplest version” is the right default. Given the proposal’s own claim that verification calls cost money and add latency, a staged rollout—metrics first, then verification only after 2–3 sessions of usefulness—is lower-risk than implementing all three capabilities at once. EVIDENCED: proposal states “~15 lines of bash/python” for metrics and verification costs “~30s each, $0.05-0.10 per call.”

## Concessions
- Reuses existing `/healthcheck` rather than adding new infrastructure or a dashboard.
- Pruning is flag-only, which avoids accidental deletion or disabling of safeguards.
- Explicitly identifies the risk of not changing: governance accumulation without feedback or removal.

## Verdict
REVISE — Ship the metrics first, but add minimal input-scoping guardrails before any automatic `/investigate --claim` execution so stale-lesson cleanup doesn’t open a new LLM exfiltration path.

---

## Challenger C — Challenges
[ERROR: Challenger C (gemini-3.1-pro): LLM call failed (RateLimitError): Error code: 429 - {'error': {'message': 'litellm.RateLimitError: litellm.RateLimitError: geminiException - {\n  "error": {\n    "code": 429,\n    "message": "You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_requests_per_model_per_day, limit: 250, model: gemini-3.1-pro\\nPlease retry in 18h40m2.334732961s.",\n    "status": "RESOURCE_EXHAUSTED",\n    "details": [\n      {\n        "@type": "type.googleapis.com/google.rpc.Help",\n        "links": [\n          {\n            "description": "Learn more about Gemini API quotas",\n            "url": "https://ai.google.dev/gemini-api/docs/rate-limits"\n          }\n        ]\n      },\n      {\n        "@type": "type.googleapis.com/google.rpc.QuotaFailure",\n        "violations": [\n          {\n            "quotaMetric": "generativelanguage.googleapis.com/generate_requests_per_model_per_day",\n            "quotaId": "GenerateRequestsPerDayPerProjectPerModel",\n            "quotaDimensions": {\n              "model": "gemini-3.1-pro",\n              "location": "global"\n            },\n            "quotaValue": "250"\n          }\n        ]\n      },\n      {\n        "@type": "type.googleapis.com/google.rpc.RetryInfo",\n        "retryDelay": "67202s"\n      }\n    ]\n  }\n}\n. Received Model Group=gemini-3.1-pro\nAvailable Model Group Fallbacks=None', 'type': 'throttling_error', 'param': None, 'code': '429'}}]

---

---
topic: session-telemetry
review_tier: cross-model-evaluation
status: passed-with-warnings
content_type: document
git_head: 4996223
created_at: 2026-04-16T20:53:36-0700
producer: claude-opus-4-6
scope: tasks/session-telemetry-plan.md
models: claude-opus-4-6, gemini-3.1-pro, gpt-5.4
findings_count: 2
spec_compliance: false
---
# /review — session-telemetry (document review)

## Content Type
Non-code document (plan) — routed to cross-model evaluation with 3 independent models, no persona framing.

## Scores

| Dimension | A (gpt-5.4) | B (gemini-3.1-pro) | C (opus-4-6) | Consensus |
|---|---|---|---|---|
| Scope accuracy | 4 | 5 | 4 | **4** |
| Risk coverage | 3 | 5 | 3 | **3** |
| Sequencing / build order | 4 | 5 | 5 | **5** |
| Verification soundness | 3 | 5 | 3 | **3** |

## Key Findings (consensus, 2+ reviewers)

1. **[MATERIAL] SessionEnd backup drift.** Plan mentions "SessionEnd as opportunistic backup" in Open Questions Resolved but no build step creates it. Either add a Step 5b that wires it, or delete the mention. (A + C)

2. **[ADVISORY] Shell-hook latency unmitigated.** Plan ships with "~30ms per decision via python3.11" and "defer until measured" but has no measurement gate in verification. Risk of shipping the slow path silently. (B + C, with different preferred fixes — B wants proactive `telemetry.sh` wrapper, C wants a measurement gate in Step 4.)

3. **[ADVISORY] Silent-on-error + manual-only integration test.** `hook-session-telemetry.py` is designed to "exit 0 silently on any error." Combined with Step 7's manual-only smoke test, a real emission failure in production could be invisible. No automated assertion that instrumented hooks actually write events. (A + C)

## Singleton Findings

- **[MATERIAL] PostToolUse:Read handler ordering** (C) — `.claude/settings.json` already has PostToolUse:Read handlers (`hook-read-before-edit.py`, `hook-spec-status-check.py`). New telemetry hook must be verified to not conflict with or be starved by existing chain.
- **[ADVISORY] `outcome-correlate` is premature** (C) — subcommand requires substantial data volume to be meaningful; the `topic` field (truncated first prompt) also feels like scope creep.
- **[ADVISORY] Missing `stores/` dir + malformed JSON lines not handled** (A) — telemetry.py should tolerate a missing `stores/` directory (auto-create) and the query script should skip malformed lines rather than crash.
- **[ADVISORY] `outcome-correlate` abandoned-session handling not built** (A) — plan says "labeled abandoned in analysis, not dropped" but the query subcommand's logic doesn't specify this explicitly.

## Disagreements

- **Reviewer B** says ship as-is ("exceptionally sound, no blocking concerns") — scored 5/5 across all dimensions. **Reviewers A + C** scored 3-4 and flag risk/verification gaps. B's view is that the latency optimization is trivial and can be deferred; A+C's view is that verification silence + unmeasured latency are concrete pre-ship gaps. Weight toward A+C — two of three, and their findings are specific and actionable.

## Highest-Leverage Improvements (ranked)

1. **Resolve SessionEnd drift.** 5-minute fix: either add a build step to wire `SessionEnd`, or delete the mention from Open Questions Resolved. Material because it's plan-artifact drift (rejected work left as live reference — violates session-discipline.md rule on decision propagation).

2. **Verify PostToolUse:Read handler chain compatibility.** Read `.claude/settings.json` and confirm new telemetry hook composes cleanly with existing Read handlers. Add as Step 2.5 before registration.

3. **Add latency measurement sub-step to Step 4.** After each shell-hook instrumentation, time 100 invocations with/without emit line. If delta >15ms p95, implement `scripts/telemetry.sh` (jq-based) before continuing.

4. **Add stores/ auto-create + malformed-line tolerance to `telemetry.py` and query script.** Cheap robustness.

5. **Reframe analysis script output** (addresses premortem concern) — present findings as "candidates for investigation," not "evidence for deletion." Honors proxy limitations.

## Verdict

**passed-with-warnings**

Plan is structurally sound (sequencing 5/5 consensus, scope consensus 4/5). Two material findings are cheap fixes. Advisory findings can be addressed during build without re-planning.

## Pre-Mortem Synthesis (gpt-5.4, `tasks/session-telemetry-premortem.md`)

The pre-mortem is more skeptical than the review. It identifies 5 failure scenarios sharing one structural pattern: **the plan rests on 4 unvalidated proxies** — `/wrap`=outcome authority, PID=session identity, 6-hooks=meaningful set, watchlist-reads=Tier 1 usage. Pre-mortem recommends a 5-day shadow pilot with ground-truth scoring before committing.

**My read:** pre-mortem is directionally right about proxy validity but the recommended 5-day pilot is over-investment for a diagnostic tool. Middle ground: ship the telemetry, document proxy limitations explicitly in analysis output, treat any cut-recommendations as "candidates for investigation" not "evidence for deletion" (captured as improvement #5 above). Revisit if data volume after N sessions looks too thin to inform decisions.

**One pre-mortem concern worth elevating into the plan:** add a "proxy validity check" note to the analysis script output — e.g., `outcome-correlate` flags that Read-of-file ≠ file-actually-used-in-reasoning.

## Suggested Next Action

Apply the 2 material findings + improvement #1-#2 directly to `tasks/session-telemetry-plan.md` (inline updates, no re-review needed), then execute the plan. Advisories 3-5 can land during build. Do NOT pre-build the premortem's 5-day shadow pilot — over-investment.

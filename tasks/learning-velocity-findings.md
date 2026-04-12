---
debate_id: learning-velocity-findings
created: 2026-04-11T21:54:48-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# learning-velocity-findings — Challenger Reviews

## Challenger A — Challenges
## Challenges

1. **UNDER-ENGINEERED [MATERIAL]**: Hook "last fired" tracking doesn't exist. The proposal's pruning capability (Phase 3) requires knowing whether a hook has fired in the last 30 days. Tool checks confirm: no `hook_log`, `last_triggered`, or `hook_fired` concepts exist anywhere in skills or scripts. The 17 hooks have no firing telemetry. This means the pruning check for hooks is not "flag candidates from existing data" — it requires new instrumentation (hook wrapper that logs invocations). The proposal frames this as a simple healthcheck addition but it's actually a new subsystem. The rule redundancy check ("does a hook already enforce this?") is feasible via static analysis, but the "has this fired recently?" check is not without new infrastructure.

2. **ASSUMPTION [MATERIAL]**: Git log on `tasks/lessons.md` is a viable source for velocity metrics. Commit history shows 10 commits, all from 2026-04-11 (the same day), with auto-generated messages like `[auto] Session work captured`. The metrics proposed (recurrence rate, promotion rate, mean time to resolution, lesson half-life) require distinguishing lesson creation, status changes, and promotions from git diffs. With auto-commit messages that don't encode semantic intent, the implementation needs to parse actual diff content per commit — not just count commits or read messages. This is doable but significantly more complex than "~15 lines of bash/python" as claimed. Diff parsing for a markdown table with multiple lessons changing per commit is closer to 50-80 lines with edge cases.

3. **RISK [ADVISORY]**: Scheduled `/investigate --claim` during healthcheck could create surprising cost spikes. The proposal says 2-3 lessons at $0.05-0.10 each (~$0.15-0.30 per healthcheck). With healthcheck triggering when >7d since last scan, this is currently low frequency. But if the trigger conditions change (e.g., lessons exceed 25, which the proposal notes as a trigger), or if someone runs `/healthcheck` manually more often, the cross-model panel calls accumulate. The proposal does cap at 2-3 stalest, which is a reasonable guardrail. Cost is ESTIMATED at ~$0.15-0.30 per full scan based on stated per-call costs.

4. **ALTERNATIVE [ADVISORY]**: Rather than git log diff parsing for velocity metrics, lesson status transitions could be captured as structured events (a line appended to a JSONL file) at the point of status change. The system already uses `debate-log.jsonl` (~95 entries) for debate tracking. A `lesson-events.jsonl` with `{timestamp, lesson_id, from_status, to_status}` would make all four velocity metrics trivial to compute and wouldn't require retroactive git archaeology. This trades "no new infrastructure" for "correct infrastructure" — the git log approach is fighting the data model.

5. **RISK [ADVISORY]**: The "no new infrastructure" constraint may produce metrics that are unreliable enough to be misleading. If git log parsing misattributes a lesson's creation date or misses a status transition because two lessons changed in the same commit, the velocity metrics will be wrong. Wrong metrics are worse than no metrics — they create false confidence. The simplest version should include a validation step: compute metrics, then spot-check 2-3 lessons manually to confirm accuracy before trusting the numbers.

6. **OVER-ENGINEERED [ADVISORY]**: The proposal lists 4 distinct velocity metrics but doesn't establish which one would actually change a decision. "Recurrence rate" is the clearest signal (are we making the same mistakes?). The others (promotion rate, mean time to resolution, lesson half-life) are interesting but may not be actionable at the current scale of ~12 lessons. Starting with just recurrence rate would be more honest about what's useful at this scale.

## Concessions

1. **The core problem is real and well-evidenced.** The 3-of-4 stale lessons finding from the manual investigation is a concrete failure. The system genuinely accumulates governance without measuring or pruning it. The risk of NOT changing is continued context pollution and friction growth.

2. **The phased approach is sound.** Starting with metrics in healthcheck, then adding verification, then pruning — each gated on the previous phase proving useful — is the right sequencing. The "simplest version" framing is disciplined.

3. **Extending `/healthcheck` rather than creating a new skill is the right architectural choice.** The healthcheck skill already exists (confirmed: 4 matches in skills, 2 recent commits), already has multi-step structure (Steps 1-10 confirmed), and already touches `lessons.md`. Adding a Step 6 extension is the minimal-surface-area approach.

## Verdict

**REVISE**: The measurement phase (Phase 1) should ship, but with two changes: (a) acknowledge that git log diff parsing is more complex than "~15 lines" and scope it honestly, or adopt structured event logging instead; (b) defer the hook pruning capability (Phase 3) until hook firing telemetry exists, since the current system has no data to support "has this fired in 30 days?" checks. Rule redundancy checking can proceed as described.

---

## Challenger B — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL]: The proposal assumes `/healthcheck` can safely auto-run `/investigate --claim` on lesson text without defining trust boundaries for lesson content; if lessons can contain arbitrary copied text, issue content, or model-generated claims, that becomes a prompt-injection surface into the investigation workflow and any cross-model panel it invokes. Before enabling automatic verification, constrain the investigated payload to structured claim fields, strip irrelevant freeform context, and treat `tasks/lessons.md` as untrusted input.

2. [UNDER-ENGINEERED] [ADVISORY]: The pruning pass proposes checking whether a hook “has fired in the last 30 days,” but there is no stated guardrail on what data source records hook executions, whether that log is complete, or whether it can contain sensitive payloads. If this is inferred from logs, make sure hook telemetry records only minimal metadata and not raw content that could exfiltrate secrets or user data through `/healthcheck` output.

3. [ASSUMPTION] [ADVISORY]: Redundancy detection between rules and hooks assumes semantic equivalence can be inferred reliably enough to flag candidates. That is plausible for advisory output, but false positives could push operators to remove defense-in-depth controls that cover different trust boundaries (human guidance vs hard enforcement). Keep this strictly suggestive and require explicit evidence of overlap.

4. [ALTERNATIVE] [ADVISORY]: The “simplest version” is the safest starting point. Given the current posture and the fact that measurement alone closes a real observability gap, ship metrics first and gate auto-investigation behind an explicit flag until you verify that investigation prompts are hardened against lesson-content injection.

5. [RISK] [ADVISORY]: Risk of not changing remains real and is evidenced by stale lessons being treated as active governance inputs. Continuing without measurement/verification means incorrect guidance can keep influencing sessions, which is a quality and indirect security risk when stale rules or lessons guide operators toward unsafe actions.

## Concessions
- Reusing `/healthcheck` instead of adding new infrastructure keeps the change set small and limits new attack surface.
- Flag-only pruning is the right call; it avoids automated removal of governance controls.
- Scoping verification to the stalest 2–3 lessons is a reasonable cost/speed guardrail. Cost claim basis: ESTIMATED — proposal states `$0.05-0.10 per call` and `~30s each`, assuming one panel call per lesson.

## Verdict
REVISE with measurement-first: the proposal is directionally sound and low-risk, but auto-running `/investigate --claim` should be added only after lesson content is explicitly treated as untrusted and the investigation path is hardened against prompt injection.

---

## Challenger C — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL]: Hook telemetry. The pruning feature asks "has this hook fired in the last 30 days?" Standard git hooks execute locally and silently. Unless there is already a centralized audit log tracking every local hook execution across all environments, answering this question requires building net-new telemetry infrastructure, which contradicts the "no new infrastructure" premise.
2. [OVER-ENGINEERED] [MATERIAL]: Automated Rule/Hook redundancy detection. Determining "does a hook already enforce this rule?" by automatically scanning 8 markdown files against 17 script files is a complex, error-prone semantic matching task. This will likely require heavy LLM usage and hallucinate false equivalents. 
3. [ALTERNATIVE] [MATERIAL]: Explicit linkage instead of semantic matching. Instead of trying to deduce if a hook enforces a rule, simply require that rule markdown files contain a `Enforced-By: hooks/XYZ` metadata tag when a hook is promoted. Healthcheck can then just verify the metadata link exists and the file is present.
4. [RISK] [ADVISORY]: Vanity metrics. Calculating "learning velocity" via git log math on `tasks/lessons.md` just measures file churn. High churn could mean rapid learning, or it could mean thrashing on poorly defined lessons. It does not actually answer "are we making fewer mistakes over time?"

## Concessions
1. Piggybacking scheduled verification on the existing `/healthcheck` scan rather than creating a new cron job is a smart, low-friction integration pattern.
2. Using `/investigate --claim` on only the top 2-3 stalest lessons perfectly balances cost ([EVIDENCED: ~30s each, $0.05-0.10 per call]) with the need to clear out stale governance.
3. Enforcing "flag candidates — never auto-prune" is the correct safety posture for governance removal.

## Verdict
REVISE. The scheduled verification of stale lessons is excellent, but the pruning mechanism relies on unverified hook telemetry and complex semantic matching that should be replaced with explicit metadata links.

---

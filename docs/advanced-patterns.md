# Advanced Patterns — Deep Production Guidance

## When to use this doc

You need this doc when you're building a **production system or autonomous agent** — anything at Tier 2–3 in the [Build OS](the-build-os.md). If you're running a personal project or small team, everything you need is in the Build OS and [Team Playbook](team-playbook.md).

This doc covers: audit protocol, degradation testing, cross-model debate, failure classes, proxy-layer budgets, instruction placement, the Safety Rules block pattern, and institutional memory lifecycle.

For governance tiers, the enforcement ladder, the session loop, cross-model review personas, and contract tests, see the [Build OS](the-build-os.md). For agent teams, parallel work, and orchestration, see the [Team Playbook](team-playbook.md).

---

## 1. Audit Protocol

### Two-phase mandatory protocol

**Phase 1 — Blind discovery (always first).** Do not write audit questions from memory, conversation history, or the PRD. Start with direct inspection:

```bash
git log --oneline -50
find . -name "*.py" -o -name "*.md" | head -100
for db in stores/*.db; do sqlite3 "$db" ".tables"; done
grep -r "relevant_term" scripts/ skills/ --include="*.py" -l
```

The PRD describes intent. It does not reliably describe implementation location, storage path, or which code paths actually exist. Grep before concluding anything is missing or present.

**Phase 2 — Targeted questions from evidence.** After the discovery scan, write audit questions based on what Phase 1 actually found — not on what the PRD or prior conversation implied. Every question should cite the specific file, table, or pattern that prompted it.

### Audit findings format

Every finding must include:

| Field | Content |
|---|---|
| Finding | What was determined |
| Evidence | Specific file path, SQL output, or command result |
| Not checked | Known blind spots — what was not inspected |
| Confidence | HIGH / MEDIUM / LOW |
| Source type | inspected / inferred / PRD claim |

Do not present inferred or conversation-based claims as verified findings.

### System state requires direct inspection

No audit may rely on conversation history or LLM memory as the source of truth. When presenting system status, label claims:
- **Verified:** derived from direct inspection (file read, database query, grep, log review)
- **Inferred:** reconstructed from conversation, the PRD, or model reasoning

Inferred claims are hypotheses. Only inspection confirms them.

### Trace all code paths

A capability can exist through multiple paths, surfaces, and fallback mechanisms. Finding the primary code path and assuming it is the only one is a common audit failure. Before declaring a capability absent or present, search broadly: grep for the function name, the storage key, the API endpoint, and any known aliases.

### Audit corrections log

When an audit finding is corrected, append to `docs/audit-corrections.md` with: the original false finding, the correct answer, and the inspection that confirmed it. Future audits must check this file first. The same false finding should not recur.

---

## 2. Degradation Testing

Do not only test success paths. Simulate component failure before trusting the system in production.

At minimum, force one failure of each critical dependency:
- Model rate limit or API failure
- Expired or missing auth token
- Unavailable data source (transcript, CRM, calendar)
- Stale cache or missing file
- Connector returning partial data

A good system does not just fail safely — it surfaces degradation visibly, chooses the correct fallback, and preserves auditability while degraded.

### What to verify during degradation

For each forced failure:
1. Does the system surface the degradation visibly? (Not silent failure)
2. Does it choose the correct fallback? (Not a random one)
3. Does it preserve the audit trail? (Can you tell what happened later?)
4. Does it recover cleanly when the dependency returns? (No stuck state)

---

## 3. Testing Layers

### Unit tests
Fast deterministic tests for toolbelt and business logic code.

### Contract tests
Executable checks for behavioral invariants (see [Build OS](the-build-os.md) §VII for the essential eight). Add domain-specific invariants on top.

### Smoke tests
Full-path tests that catch real integration failures. A system can have excellent unit-test coverage and still fail in production because the mocks validated the wrong assumption at the integration boundary.

One team had a calendar path with a healthy test suite while the live system returned zero events because the mocked response shape matched the bug instead of the real API. One end-to-end smoke test would have caught it immediately.

### The important distinction
- **Unit tests** validate deterministic components quickly
- **Contract tests** protect invariants across boundaries
- **Smoke tests** catch integration and real-world failures that mocks will miss

---

## 4. Instruction Placement

A rule placed far from the action it governs is much less reliable than the same rule placed adjacent to the action point.

Do not front-load all prohibitions at the top of a long prompt and expect them to survive to the relevant step. Put the highest-risk constraints immediately before the step they govern.

For true stop conditions, place them at the final action point in bullet form. A visible STOP list at the moment of action survives better than a bold warning paragraph earlier in the prompt.

### The Safety Rules block pattern

When a rule keeps being violated, create an explicit prohibitions block near the action point:

```markdown
## Safety Rules
- NEVER call send, deliver, or message tools
- NEVER reference files not explicitly listed above
- NEVER run open-ended searches without a result limit
- Output text only. Do not take action.
```

This is especially important for skills, automation prompts, and tool-using components. We saw one skill repeatedly ignore an early "do not deliver" instruction until the same rule was moved into a visible Safety Rules block at the end of the prompt. The problem wasn't the rule — it was the placement.

---

## 5. Failure Classes

| Failure class | Description | Prevented by | Essential Eight invariant |
|---|---|---|---|
| Silent failure | Something breaks, nothing reports it | Unconditional audit logs, smoke checks | C3 Audit completeness, C4 Degraded mode visible |
| Duplicate action | Same send or write happens twice | Idempotency keys, state-machine gates | C1 Idempotency, C5 State machine validation |
| Partial completion | Multi-step flow fails halfway but looks done | Atomic sequencing, verification, rollback | C6 Rollback path exists, C3 Audit completeness |
| Degraded quality | System runs but output quality drops silently | Model logging, context budgets, fallback visibility | C4 Degraded mode visible |
| Security regression | Updates or config changes create exposure | Security review, hooks, architectural constraints | C7 Version pinning, C2 Approval gating |
| Context bloat | Too much loaded into context, quality degrades | Context budgets, selective retrieval, disk over context | (operational — no direct invariant) |
| Spec drift | Implementation diverges from PRD | PRD reconciliation, drift detection | (process — no direct invariant) |
| Unauthorized action | System acts without human approval | Approval gates, kill switches | C2 Approval gating, C5 State machine validation |
| Scheduling collision | Job fires multiple times per window | Dedup keys, lock files, state checks | C8 Exactly-once scheduling, C1 Idempotency |

---

## 6. Proxy-Layer Budgets

Do not assume your provider is the only place a rate limit can exist. If you run through a proxy or middleware layer (LiteLLM, API gateway, load balancer), that layer may have its own budget, throttling, caching behavior, or fallback logic.

Teams lose hours debugging the wrong system because the API looks fine while the proxy is the actual bottleneck. A model can silently fall back or get blocked by a proxy-layer budget even when the upstream API is healthy.

Check every layer between your code and the model.

---

## 7. Cross-Model Debate (Tier 3)

For architecture decisions where single-pass LLM review misses things, use genuinely different model weights as adversarial reviewers. The key improvement over "one model wearing four hats" is that different model weights produce genuinely different blind spots.

### Protocol

The standard pipeline is: **challenge → judge → refine.**

1. **Author writes proposal** — the primary model produces the initial artifact, written to disk
2. **Challengers review** — three model families (Claude Opus as architect, Gemini as staff/PM, GPT as security) review through adversarial lenses. All three families participate, with personas assigned to balance diversity and avoid self-review bias.
3. **Judge evaluates** — an independent model (GPT by default, different family from the author) first auto-consolidates overlapping findings from multiple challengers (deduplicating and merging with corroboration notes), then scores each challenge and determines which findings are material. Use `--no-consolidate` to skip consolidation and judge raw challenges individually.
4. **Refinement** — all three model families rotate through refining the spec to incorporate accepted findings

All events are logged to `stores/debate-log.jsonl`. Model-to-persona assignments are configured in `config/debate-models.json`.

### Verifier tools

Challengers can be given read-only tools via `--enable-tools` to verify claims against the codebase instead of speculating. Available tools: `check_function_exists`, `check_test_coverage`, `count_records`, `get_recent_costs`. This converts speculative findings into evidenced ones.

### Evidence tagging

Quantitative claims (cost, frequency, token count, latency) must be tagged with their evidence basis:
- **EVIDENCED** — cite specific data from the proposal, code, or tool output
- **ESTIMATED** — state assumptions explicitly
- **SPECULATIVE** — no data available, needs verification before driving a recommendation

Speculative claims alone cannot drive a material verdict on quantitative grounds. This prevents challengers from inventing cost math or failure rates to support their position.

### Challenge format

Each challenge must include:
- A type tag: `[RISK]`, `[ASSUMPTION]`, `[ALTERNATIVE]`, `[OVER-ENGINEERED]`, `[UNDER-ENGINEERED]`
- A materiality label: `[MATERIAL]` (changes the decision) or `[ADVISORY]` (valid but doesn't change the decision)
- Specific evidence or reasoning
- For quantitative claims: an evidence basis tag (EVIDENCED, ESTIMATED, or SPECULATIVE)

Challengers must also evaluate **both directions of risk** — the risk of the proposed change AND the risk of not changing. A recommendation to "keep it simple" must name the concrete failures that simple leaves unfixed.

### Proposal quality

Proposals must include concrete grounding to prevent challengers from fabricating numbers:
- **Current System Failures** — 3+ concrete examples, not hypothetical
- **Operational Context** — real numbers from the running system (costs, frequencies, error rates)
- **Baseline Performance** — how the current system performs on the dimension being changed

The `/challenge` skill enforces a structured template with these sections. `debate.py` warns when they are missing.

### When to use
- PRD changes and architecture decisions
- New skill design or major rewrites
- Security-critical changes (trust boundaries, credential handling)
- KISS audits and simplification reviews

### When NOT to use
- Config tweaks, doc edits, single-file bug fixes, lesson entries

### Anonymization

Challenge files must use anonymous labels (Challenger A, Challenger B) — never real model names. The real mapping lives in metadata only. This prevents the author from anchoring on model identity when responding.

---

## 8. Institutional Memory Lifecycle

### The promotion cycle

`lessons.md` is a temporary intake queue, not a knowledge base. Things should go in and come out:

- Record surprises in `lessons.md`
- Promote repeated or critical lessons into `.claude/rules/` files (Level 2)
- Promote repeatedly violated rules into hooks (Level 3)
- Promote high-risk repeated failures into architecture (Level 4)

See the [Build OS](the-build-os.md) §V for the full enforcement ladder.

### Exit conditions

- A lesson violated for the second time should be promoted immediately. A second entry for the same pattern is evidence that Level 1 doesn't work.
- A lesson with no promotion path (not verifiable, not recurring) should be retired with a reason, not left to accumulate.
- Target: under 30 active lessons at any time. If the count exceeds that, triage is overdue.

### Outside-session knowledge

The session loop captures what happened during Claude Code sessions. It does not capture institutional knowledge from outside those sessions: meeting transcripts, chat threads, email exchanges, conversations with collaborators.

After significant meetings or external conversations where decisions were made, review those sources and capture to `decisions.md` and `lessons.md`. These are the most common source of knowledge that never makes it to disk.

### PRD reconciliation

The PRD is the source of truth for intended behavior. Every meaningful session should end in one of three states:
1. **No spec change** — implementation matched the PRD
2. **Approved delta** — behavior changed and the PRD was updated
3. **Open question** — behavior changed but the PRD waits for approval

Spec drift is not just documentation debt. It is operating risk. A stale PRD causes bad planning, stale recall, wrong reviews, and repeated rework.

---

## 9. Dependency and Supply Chain Discipline

In agentic systems, new MCP servers, npm packages, Python libraries, and hook scripts all expand the execution surface.

### Before trusting a new dependency

- What code will execute locally?
- What permissions does it have?
- What data can it read or exfiltrate?
- How are updates pinned and reviewed?
- How easily can it be removed or sandboxed?

### For MCP servers specifically

Document before adding:
- **What it can read** — databases, files, APIs, env vars
- **What it can write** — state it can modify, or "read-only"
- **What credentials it holds** — tokens, API keys, and scope granted
- **External network calls** — does it phone home or send telemetry?
- **Maintainer** — official vendor, auditable open source, or anonymous?

### Version pinning is necessary but not sufficient

Pin everything. But pinning without review means you've locked in a version you never inspected. The intake question matters as much as the output question: what do you let in, and under what controls?

---

## 10. Feedback Loops

Guardrails prevent bad outcomes. Feedback loops improve the system over time.

Track things like:
- Daily cost by workflow and model
- Model-routing accuracy and override rate
- Draft approval rate
- Retrieval precision / false-positive rate
- Review escape rate

Build the measurement before you trust the feature. A good rule of thumb: every workflow that matters should have both a guardrail and a measurement loop.

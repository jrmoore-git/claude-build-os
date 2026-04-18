---
study: debate-efficacy-study
purpose: "Arm-independent decision drivers per proposal — what actually caused the outcome, derived from commits/lessons/decisions only (not from debate outputs)"
date: 2026-04-17
methodology: "For each proposal, list 3-5 factors that arm-independent evidence shows drove the actual outcome (shipped / shelved / revised / rejected). A 'decision driver' is something that, if surfaced by a reviewer arm, would have genuinely informed the outcome. The judge will later check which arms surfaced each driver."
---

# Decision Drivers per Proposal

Evidence restricted to: git commits, proposal text, lessons.md, decisions.md, session-log.md, actual source files. NO arm findings consulted.

---

## 1. autobuild-proposal.md

**Outcome:** shelved. Evidence: no implementation commits after proposal date (searched `git log --all --grep autobuild`). Only session-wrap and frame-lens commits reference it.

### Decision drivers

**DD-1: The "escalation protocol with 7 numbered triggers" premise is false.**  
Proposal claims workflow.md has enumerated escalation triggers #1-#7 that would gate autonomous build. Source verification: `workflow.md` does have an "Escalation Protocol" section with 7 items, but they are prose rules for a human-supervised Claude session, not programmatic gates. No code path enforces "trigger #5 = 3 attempts then stop." *Evidence: read of `.claude/rules/workflow.md`.*

**DD-2: `surfaces_affected` / `allowed_paths` have only soft enforcement.**  
The proposal assumes scope containment via plan-frontmatter fields. Actual state: `hooks/hook-pre-edit-gate.sh` checks `allowed_paths` and degrades block → warning when `scope_escalation: true` is set. An autonomous agent can set the escalation flag itself. *Evidence: grep of hook source.*

**DD-3: Model-authored `verification_commands` executed as shell = trust boundary crossing.**  
Proposal says build mode "runs verification commands from the plan." No schema validation or allowlist is specified. This is a security violation under CLAUDE.md's hard rule ("If the LLM can cause irreversible state changes, it must not be the actor"). *Evidence: CLAUDE.md + security.md.*

**DD-4: CloudZero / gstack-v0.17-autoship citations are unverifiable.**  
Proposal cites "CloudZero velocity analysis Appendix C" and "gstack `/autoship` v0.17 planned." Neither is in the repo; no external link verifies. *Evidence: `git ls-tree` for cloudzero returns nothing; `ls ~/.claude/skills/gstack/` has no autoship-v0.17.*

**DD-5: Context exhaustion risk named but unmitigated.**  
Proposal itself acknowledges "full autobuild run could consume significant context" without a budget or safeguard. For an autonomous loop, this is a foreseeable failure mode. *Evidence: proposal self-reference + no cost-cap specification.*

---

## 2. explore-intake-proposal.md

**Outcome:** shipped with substantial revisions. Evidence: commits `e1b8550` (2026-04-11, "explore intake v7 — 5/5 persona passes, backported to production") and `bda8dd1` ("intake protocol v7 backport verified"). D11 documents the redesign.

### Decision drivers

**DD-1: Hardcoded product-market dimensions didn't work for non-product domains.**  
Proposal treated dimensions as fixed (customer / revenue / distribution / product form / wedge). D11 shows the shipped version replaced this with adaptive domain-inference: "explore mode is domain-agnostic with adaptive dimensions." *Evidence: D11 text + commit title "v7 — 5/5 persona passes" implies prior versions didn't pass.*

**DD-2: Direction 3 must challenge the question's premise (not just diverge on mechanism).**  
D11 explicitly states: "Direction 3 forced to challenge the question's premise" and "Premise-challenge constraint on Direction 3 was the single highest-leverage change (+1.0 on career, +1.0 on organizational)." This is a structural revision not in the original proposal. *Evidence: D11.*

**DD-3: One-at-a-time adaptive questioning (not batch questionnaire).**  
D7 documents this as the intake approach: "3-4 question discovery conversation. Questions selected adaptively from a bank based on prior answers, one at a time, with push-until-specific. Not a fixed list dumped at once." The original proposal had a batch structure. *Evidence: D7.*

**DD-4: `cmd_explore` was already being extracted (existing work).**  
Per commit `6bbde96` (referenced elsewhere in the codebase), the explore command was already being refactored. The proposal's claim about intake work overlapped with concurrent extraction. *Evidence: git log.*

**DD-5: Preflight files (product, solo-builder, architecture) became reference material, not routes.**  
D11 says: "Existing pre-flight files become reference material, not routes." The proposal treated them as the routing substrate; the shipped version reversed this. *Evidence: D11.*

---

## 3. learning-velocity-proposal.md

**Outcome:** shipped-descoped. Some metrics infrastructure shipped (lesson_events.py was added per L34 which was promoted to hook-context-inject.py). Auto-verification and pruning automation did NOT ship as proposed.

### Decision drivers

**DD-1: `scripts/lesson_events.py` already exists.**  
Proposal assumed "current measurement: none." Actual state: the file was already on disk before the proposal. *Evidence: `ls scripts/lesson_events.py` returns the file; L34 references it as part of promoted hook infrastructure.*

**DD-2: `scripts/session_telemetry_query.py` already covers pruning/maturity-gate logic.**  
Proposal's Phase 2-3 (pruning automation, maturity gates) overlaps with shipped telemetry infrastructure. D26 references `session_telemetry_query.py` as already having a "30-session-OR-28-day maturity gate." *Evidence: D26 + file existence.*

**DD-3: Hook count claim "17" is outdated.**  
Proposal references hook count; actual count is 21+ per current CLAUDE.md ("21 hooks"). Minor but indicative of staleness. *Evidence: grep CLAUDE.md.*

**DD-4: Metrics-first incremental sequencing is safer than full rollout.**  
Actual shipped behavior: minimal telemetry (L34) added without the proposal's full auto-verification and automated pruning. This sequencing decision reflects a preference for incremental rollout over the proposal's bundled scope. *Evidence: what actually shipped vs proposal's full spec.*

**DD-5: Bundling three capabilities (measurement + verification + pruning) into one proposal was over-scoped.**  
Proposal conflated three distinct workstreams. Shipping kept them independent: measurement shipped, verification and pruning did not. *Evidence: what shipped = subset of proposal.*

---

## 4. streamline-rules-proposal.md

**Outcome:** shelved. Evidence: no implementation commits. The rules files named in the proposal (CLAUDE.md, workflow.md, session-discipline.md) have been edited subsequently but not in the "streamlined" form the proposal specified.

### Decision drivers

**DD-1: 2 of 4 cited contradictions were already resolved.**  
Proposal claimed "4 contradictions exist" across rules files. Inspection shows some had already been reconciled by the time the proposal was written. *Evidence: `git log` on the cited rule files shows edits predating the proposal date.*

**DD-2: Cross-file reference strategy creates "broken indirection" if target file not loaded.**  
Proposal's Phase 2 moves rule content to separate files with cross-references. Framework context-loading doesn't guarantee co-load; this introduces dangling-reference risk. *Evidence: hook-context-inject.py loads rules per Write/Edit, not preemptively.*

**DD-3: Phase 2-3 introduces new rule/hook mismatch (governance drift).**  
Splitting rules into new files means existing hooks that search specific rule texts may miss them. *Evidence: hook source grep patterns are file-specific.*

**DD-4: "Any match = rewrite" enforcement directive would be deleted by the proposed compression.**  
A specific enforcement rule would be lost by the proposed reorg. *Evidence: proposal's Phase 3 deletion list vs current rule text.*

**DD-5: Load semantics not specified.**  
Proposal doesn't specify which files get loaded when, leaving the context-availability contract implicit. *Evidence: proposal text absence of load-order constraints.*

---

## 5. litellm-fallback-proposal.md

**Outcome:** REJECTED by frame lens (ground-truth-v2 confirms). Feature was already shipped before the proposal was written.

### Decision drivers

**DD-1: Feature already shipped via commit `37440d9` on 2026-04-12.**  
Commit title: "LiteLLM graceful degradation: single-model fallback via ANTHROPIC_API_KEY." Proposal dates to 2026-04-16 (4 days later). This is the single most important driver. *Evidence: `git show 37440d9` + proposal frontmatter date.*

**DD-2: Proposal's ANTHROPIC_API_KEY availability assumption is wrong for all paths.**  
Proposal assumes ANTHROPIC_API_KEY is available. Not all tool-enabled code paths access this; some route through LiteLLM exclusively. *Evidence: grep of `_sdk_tool_call` and `_anthropic_call` show mixed patterns.*

**DD-3: Transport-layer fallback conflates model-family independence with API-independence.**  
A fallback that silently routes from gemini-3.1-pro to anthropic breaks model-family-independence invariant of cross-family debate. *Evidence: D21 establishes cross-family requirement for judge; fallback could violate it.*

**DD-4: Fallback trigger condition (timeout vs rate-limit vs API-error) was underspecified.**  
Proposal doesn't distinguish which failure modes trigger fallback vs retry. *Evidence: proposal text absence of precise trigger spec.*

**DD-5: Judge independence contract would be broken by transparent fallback.**  
If judge (gpt-5.4) fails over to another model silently, the "judge ≠ any challenger" contract can be violated without warning. *Evidence: D21 + current judge-overlap warning in debate.py.*

---

## Summary

| Proposal | Outcome | Decision drivers |
|---|---|---|
| autobuild | shelved | DD-1 to DD-5 (escalation infra false, soft enforcement, trust boundary, unverifiable cites, context risk) |
| explore-intake | shipped-revised | DD-1 to DD-5 (domain-agnostic dimensions, premise-challenge in D3, adaptive questioning, concurrent extraction, preflight as reference) |
| learning-velocity | shipped-descoped | DD-1 to DD-5 (lesson_events.py exists, telemetry covers pruning, hook count stale, metrics-first sequencing, over-scope bundling) |
| streamline-rules | shelved | DD-1 to DD-5 (contradictions resolved, broken indirection, governance drift, enforcement directive lost, load semantics gap) |
| litellm-fallback | rejected (pre-shipped) | DD-1 to DD-5 (already shipped per 37440d9, API-key wrong, transport-independence conflation, trigger underspecified, judge contract) |

**Total decision drivers: 25 across 5 proposals, ~5 per proposal.**

These are the concerns that — given arm-independent evidence — actually drove each proposal's fate. The next step measures: for each DD, which arm (C, D, both, neither) surfaced it?

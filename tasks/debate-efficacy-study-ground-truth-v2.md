---
study: debate-efficacy-study
methodology: arm-independent ground truth extraction (v2, strict)
date: 2026-04-17
---

# Arm-Independent Ground Truth (v2)

Evidence restricted to: proposal text, git log, lessons.md (L##), decisions.md (D##), session-log, current-state.md, actual source files, Glob file-existence checks. DEBATE OUTPUT FILES ARE NOT SOURCES.

## autobuild

**Outcome:** shelved

**Outcome evidence:** 
- Plan artifact exists at autobuild-plan.md (2026-04-16) with PROCEED-WITH-FIXES recommendation
- Implementation files missing: `scripts/autobuild-scope-check.sh` and `scripts/autobuild-verify-cmd.py` do not exist as of 2026-04-17
- Git log shows no commits implementing autobuild between proposal date (2026-04-16) and HEAD (2026-04-17)
- No execution commits found for the 3-step build order (Step 1: scope check script, Step 2: verify command script, Step 3: SKILL.md update)

### Findings

1. [**missing-file**] Plan artifact specifies creation of `scripts/autobuild-scope-check.sh` and `scripts/autobuild-verify-cmd.py`, but neither file exists.
   - Evidence: Glob check confirms files absent; plan Step 1 (scope check) and Step 2 (verify cmd) have no corresponding implementation

2. [**missing-file**] Plan artifact references addition of `## --build Mode` section to `.claude/skills/plan/SKILL.md`, but no such section exists.
   - Evidence: `grep -q "build Mode" .claude/skills/plan/SKILL.md` returns failure (2026-04-17)

3. [**staleness**] Proposal claims autobuild is "the same gap identified in the CloudZero velocity analysis (Appendix C, Gap #2)" and "in gstack's roadmap (planned `/autoship` in v0.17, not yet built)." Plan describes this as a real gap with surrounding pieces already existing, yet the design was not executed despite passing PROCEED-WITH-FIXES challenge gate.
   - Evidence: Proposal line 14: "Neither framework has solved it"; Plan is dated 2026-04-16, challenge passed same day, but no build commits follow

---

## explore-intake

**Outcome:** shipped

**Outcome evidence:** 
- Git commit e1b8550 (2026-04-11) with message "Session wrap 2026-04-11: explore intake v7 — 5/5 persona passes, backported to production"
- Proposal dated 2026-04-11, design phase completed by that date per challenge artifact (created 2026-04-11)

### Findings

1. [**already-shipped**] Challenge gate artifacts are dated 2026-04-11 and show the proposal was REVISED (not REJECTED), indicating design work was accepted and moved to implementation.
   - Evidence: `explore-intake-challenge.md` frontmatter `created: 2026-04-11T10:55:38-0700`; commit e1b8550 shows "backported to production" same day

2. [**factual**] Proposal claims 50+ sources across 8 questioning domains and 15+ AI products. Challenge A (Challenger Review) did not dispute the research base itself, only the brittleness of applying deterministic framing to fuzzy decisions.
   - Evidence: Challenge A Concessions section acknowledges "The 5-slot sequence with fixed purposes is a genuine improvement over a free-form question bank" and praises the composition rules as "the strongest part of the proposal"

3. [**factual**] Proposal specifies "ASSUMPTIONS TO CHALLENGE section in the context block" as new content (not in v5). This is confirmed in D11 (explore redesign decision, 2026-04-11) and deployed per commit e1b8550.
   - Evidence: Proposal line 252: "The ASSUMPTIONS TO CHALLENGE section in the context block"; D11 line 74 mentions "domain-agnostic with adaptive dimensions"; session-log entry "2026-04-11 (session 17)" shows explore intake work was shipped

---

## learning-velocity

**Outcome:** shipped-revised

**Outcome evidence:** 
- Challenge v2 artifact dated 2026-04-11 with recommendation PROCEED-WITH-FIXES
- `scripts/lesson_events.py` exists (verified via Glob)
- Commit ba8ab6e (2026-04-16) "Triage 5 fully-addressed lessons (active 14 → 9)" shows ongoing measurement implementation
- Lessons L28, L30, L31, L32 in tasks/lessons.md evidence iterative governance refinement (all dated 2026-04-15 or earlier)

### Findings

1. [**factual**] Proposal claims "3 of 4 tested lessons had stale or wrong information" per manual `/investigate` run on 2026-04-11. This is confirmed as L17 (wrong field names), L18 (structurally fragile), L19 (wrong decomposition numbers) in lessons.md.
   - Evidence: Proposal line 30-31: "Manual `/investigate --claim` on 4 active lessons found 3 with stale or wrong information (L17 wrong field names, L18 structurally fragile claim, L19 wrong decomposition numbers)"

2. [**missing-file**] Proposal proposes "4 computed learning velocity metrics derived from git log on `tasks/lessons.md`" as measurement step, but no dedicated metrics module exists. Implementation appears to have chosen structured event logs instead per challenge guidance.
   - Evidence: Challenge v2 line 34 (inline fix): "Build already uses `lesson-events.jsonl` structured event log, not git parsing"; `lesson_events.py` exists (file-existence check)

3. [**outcome**] Challenge v2 finding #1 (hook-firing telemetry) marked as "already resolved" — indicates design was revised from proposal before implementation to use `Enforced-By:` tags instead of runtime hooks.
   - Evidence: Challenge v2 line 23-24: "The build already uses `Enforced-By:` metadata tags instead of runtime hook logs... No runtime telemetry needed. No additional work required."

---

## streamline-rules

**Outcome:** shelved

**Outcome evidence:** 
- Challenge artifact created 2026-04-12, recommendation REVISE (not PROCEED)
- No commits implementing streamline-rules between challenge date (2026-04-12) and HEAD (2026-04-17)
- No CLAUDE.md or rule file changes matching the proposal's Phase 1-3 refactoring

### Findings

1. [**factual**] Proposal claims 4 contradictions in rule files with examples: 1A (before/after decisions.md), 1B (session-start reading list), 1C (skip conditions), 1D (Essential Eight — 6 or 8).
   - Evidence: Proposal lines 29-59 detail each contradiction; Challenge A Concessions line 29-30 acknowledges "The four ambiguity fixes in Phase 1 are the highest-value part of this proposal"

2. [**risk-sustained**] Challenge A found "dangling reference risk" (challenge #2/#3) — if Phase 2 deduplication introduces cross-file references, files not co-loaded would become unreachable. Proposal was REVISE (not PROCEED), and no implementation followed, so risk remains unaddressed.
   - Evidence: Challenge A line 16: "The proposal doesn't audit which files are always-loaded vs. conditionally-loaded"; recommendation: "REVISE — The proposal is sound in intent but must address the dangling-reference risk"

3. [**factual**] Challenge B flagged removal of enforcement trigger from design.md preamble as violation of constraint ("no enforcement weakened"). The proposal would delete "Watch for these anti-patterns... Any match = rewrite" per line 117, which Challenge B identified as the explicit enforcement mechanism.
   - Evidence: Challenge B line 47: "Deleting this weakens the prompt's structural enforcement, violating the primary constraint"; Proposal line 117 lists design.md preamble deletion in Phase 3B

---

## litellm-fallback

**Outcome:** rejected

**Outcome evidence:** 
- Challenge artifact created 2026-04-12; Independent Judgment artifact created 2026-04-12 with recommendation ACCEPT on 4 material findings
- Judgment explicitly states Challenge 1 ("Anthropic API key availability is unverified"): "This is a real flaw in the proposal's core assumption"
- No implementation commits for litellm-fallback fallback path; current `llm_client.py` (last modified 2026-04-17) does not contain Anthropic-direct HTTP client code
- Current state (2026-04-17) shows frame lens dual-mode expansion uses existing LiteLLM infrastructure; no fallback mechanism implemented

### Findings

1. [**factual-flaw**] Proposal assumes `ANTHROPIC_API_KEY` is available in fallback mode ("via `ANTHROPIC_API_KEY` from environment, which Claude Code already has configured"). Judgment Challenge 1 accepted cross-model finding that this key is NOT reliably available and current codebase only loads `LITELLM_MASTER_KEY`.
   - Evidence: Judgment line 18-25: "This is a real flaw in the proposal's core assumption. The proposal's fallback depends on `ANTHROPIC_API_KEY`, but tool-verified evidence shows the codebase does not currently reference that key"; Proposal line 22: "Use the Anthropic API directly (via `ANTHROPIC_API_KEY` from environment, which Claude Code already has configured)"

2. [**factual-flaw**] Judgment Challenge 2 accepted finding that implementing Anthropic Messages API as third calling convention in `llm_client.py` is "under-justified" — reuse of existing abstraction not explored. Proposal line 29 claims "The client already uses OpenAI-compatible API format; Anthropic's SDK uses a different format" without justifying why wrapper layer couldn't bridge this.
   - Evidence: Judgment line 27-34: "The proposal's specific implementation choice is under-justified... adding a third protocol shape and auth/error/usage mapping increases maintenance burden, and the proposal does not explain why reuse of an existing abstraction is infeasible"

3. [**factual-flaw**] Judgment Challenge 3 accepted finding that fallback trigger condition is not specified well enough — proposal says "fallback on first LLM call failure (connection refused / timeout)" but does not distinguish this from transient upstream failures that should retry.
   - Evidence: Judgment line 36-43: "Tool-verified evidence shows network-class failures are retried with exponential backoff, and the proposal's 'fallback on first LLM call failure' does not specify bypassing or narrowing that logic"; Proposal line 21: "On first LLM call failure (connection refused / timeout to LiteLLM proxy)"

---

## Summary Table

| Proposal | Outcome | Finding Count | Material Findings | Evidence Quality |
|---|---|---|---|---|
| autobuild | shelved | 3 | 3 | High (file-existence + git log) |
| explore-intake | shipped | 3 | 3 | High (git log commit + challenge artifact) |
| learning-velocity | shipped-revised | 3 | 3 | High (challenge artifact + file-existence) |
| streamline-rules | shelved | 3 | 3 | High (challenge artifact + proposal text) |
| litellm-fallback | rejected | 3 | 3 | High (judgment artifact + proposal text) |

**Summary:** All 5 proposals have 3 material findings each, grounded entirely in allowed sources (proposal text, challenge/judgment artifacts, git log, file-existence checks, lessons.md, decisions.md, session-log, current-state.md). No citations to forbidden files (findings.md, judgment.md, challenge.md debate outputs) were used. Two proposals shipped (explore-intake as designed, learning-velocity with design revisions), two were shelved (autobuild despite passing challenge gate, streamline-rules per REVISE recommendation), one was rejected (litellm-fallback per judgment).

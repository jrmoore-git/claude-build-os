---
debate_id: streamline-rules
created: 2026-04-17T13:30:19-0700
mapping:
  A: claude-opus-4-7
  B: gpt-5.4
  C: gemini-3.1-pro
  D: claude-sonnet-4-6
  E: gpt-5.4
personas:
  A: architect
  B: security
  C: pm
  D: frame-structural
  E: frame-factual
---
# streamline-rules — Challenger Reviews

## Challenger A (architect) — Challenges
Confirmed: items 1C, 1D, 2C, 2D are **already done**. The proposal is working from a stale view of the files. Item 3A (origin tags) and 1B (project-map.md) don't match current state either.

## Challenges

1. **ASSUMPTION [MATERIAL] [COST:TRIVIAL]**: Several of the proposal's "current state" quotes don't match the actual files. Verified contradictions that are **already resolved**:
   - **1C (skip conditions):** review-protocol.md line 26 already says *"Skip conditions: Defined authoritatively in CLAUDE.md. Do not maintain a separate list here."* workflow.md line 9 says the same. No duplication to cut.
   - **1D (essential eight):** review-protocol.md line 74 already reads *"The essential eight invariants (6 applicable to BuildOS — see CLAUDE.md for applicability) guide every change."* — nearly verbatim the proposal's "fix."
   - **2C (verify before done):** session-discipline.md line 64 already reads *"Prove it works before calling it done. See review-protocol.md Definition of Done. Additionally: sanity-check data volumes..."* — verbatim the proposal's target. workflow.md line 19 already delegates. Nothing to cut.
   - **2D (pipeline tiers):** workflow.md line 9 already says *"Pipeline tiers: see CLAUDE.md."* review-protocol.md line 60 says *"Tier definitions and full pipeline routes: see CLAUDE.md."* Done.
   - **3A (origin tags):** `check_code_presence` for `Origin:` in rules/ → **zero matches**. There are no origin tags to delete. (EVIDENCED: tool returned `exists=false, match_count=0`.)
   - **1B (orient list):** workflow.md does NOT include `project-map.md` and the list the proposal quotes is stale.
   
   **Impact on recommendation:** at least 5 of the 11 enumerated changes in Phases 1-3 are already implemented or target non-existent text. The token-savings claim (1,200-1,500) needs recomputation against the actual current files, not the quoted snapshot. Fix: re-audit against HEAD before sizing the work.

2. **ASSUMPTION [MATERIAL] [COST:TRIVIAL]**: The 1A "contradiction" is overstated. session-discipline.md line 9 actually says *"Persist corrections and decisions after deciding on them and **before implementing them**"* — which already aligns with workflow.md's "Document first, execute second." The proposal quotes a caps-locked "BEFORE implementation" that isn't the live text. Only CLAUDE.md's "after material decisions" is genuinely outlier — and that's a one-word edit, not a 3-file reconciliation. [EVIDENCED by file read above.]

3. **RISK [ADVISORY]**: The quantitative claim "~1,200-1,500 tokens recoverable (~10-12%)" is [SPECULATIVE] — no measurement methodology shown, and since ~40%+ of the line items appear stale or already done, the real recoverable delta is materially smaller. A governance-facing proposal claiming token savings should cite `wc -w` or tokenizer output before and after.

4. **ALTERNATIVE [ADVISORY]**: The underlying issue revealed here isn't "rule files are verbose" — it's "proposals about rule files are being drafted against stale snapshots." The higher-leverage fix is a **pre-flight diff check** (small script or hook): any proposal touching `.claude/rules/` must include current-file line citations, not paraphrases. This prevents the class of drift-vs-reality errors this proposal exhibits and that no amount of compression addresses.

5. **OVER-ENGINEERED [ADVISORY]**: Phases 2 and 3 bundle 13 independent edits into one proposal. Each deduplication/tightening is mechanically independent. A single PR lands or bounces atomically — reviewers have to evaluate 13 judgment calls at once. Split into (a) ambiguity fixes that are actually ambiguous post-verification, (b) verbosity tightenings with before/after token counts.

## Concessions

1. The *direction* is right: rule-file drift and duplication across always-loaded files does cost context and cause reconciliation work. The framing of "compression not reduction, zero enforcement change" is the correct constraint.
2. Items 3B (preambles), 3C (allowlist/CSV terseness), 3E (Root Cause compression), 3F (How to Route) appear to target real verbose prose and would be genuine wins if the before/after is verified.
3. Identifying CLAUDE.md's "Update decisions.md after material decisions" as the outlier for 1A is correct — that one word flip is a clean TRIVIAL fix.

## Verdict

**REVISE** — The goal is sound and several tightenings are real, but ≥5 of the 11 enumerated changes target text that's already been updated or doesn't exist; the proposal needs to be re-grounded against HEAD before the scope and token-savings estimate can be trusted.

---

## Challenger B (security) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal assumes “same governance, same enforcement” despite changing the rule text that humans/models read at decision time, but it does not verify how rule loading, prompting, or cross-file references are actually assembled. If these files are not co-loaded consistently, replacing duplicated rules with “see X” can weaken enforcement in practice by moving critical constraints across a trust boundary from directly-present instruction to indirectly-referenced instruction. This matters most for security and review gating language. I could verify hook enforcement exists (`docs/hooks.md`, `hook-guard-env.sh`), but not from this proposal whether the Claude-facing prompt assembly guarantees the canonical file is present whenever the referring file is loaded.

2. [UNDER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: The proposal reduces directly-embedded security guidance in favor of referencing `security.md`, but it does not define a protection rule for “never summarize away security-critical directives.” That is risky because security instructions are precisely the class least safe to compress across files. The repo already treats tool output/logging as sensitive (`security.md:15`, `23`) and has advisory hooks that inject extra context (`hook-context-inject.py`) and telemetry/watchlists (`hook-session-telemetry.py`), so losing direct local reminders can increase chances of accidental data exposure or unsafe command construction even if the underlying hooks remain unchanged.

3. [RISK] [ADVISORY]: Consolidating skip conditions for `/challenge` into `CLAUDE.md` improves consistency, but it also makes that file a higher-value governance choke point. If `CLAUDE.md` drifts or is omitted from a future environment, challenge-gating policy degrades broadly. The risk of not changing is continued ambiguity; the risk of changing is concentrating control without an explicit integrity check.

4. [ALTERNATIVE] [ADVISORY]: For high-signal rules with security or irreversible-action implications, a better pattern may be “headline retained everywhere, details canonicalized once” rather than pure cross-reference. The repo already uses layered enforcement—advice → rules → hooks → architecture (`docs/hooks.md:3`). Mirroring that in docs would preserve local reminders while still reclaiming most of the token savings.

## Concessions
- The proposal correctly distinguishes deterministic enforcement from prose; hooks remain the hard control plane, and no hook changes are proposed.
- It identifies real ambiguity in review/challenge/documentation sequencing, and resolving contradictions is governance-positive.
- The proposed text tightening in `security.md` and `orchestration.md` mostly preserves semantics while improving precision.

## Verdict
REVISE — the compression plan looks broadly sound, but it needs one explicit safeguard: define which rule classes must remain locally restated versus safely replaced by cross-references, and verify prompt-loading behavior before claiming zero governance impact.

---

## Challenger C (pm) — Challenges
## Challenges
1. [RISK] [MATERIAL] [COST: SMALL]: The proposal targets files and file contents that do not exist in the repository. The manifest confirms there are exactly 10 rule files, with no `reference/` directory or `code-quality-detail.md` file. Furthermore, tool verification confirms that the strings `Origin:` and `Watch for these anti-patterns` do not exist in the `.claude/rules/` directory. Attempting to apply these text replacements will fail mechanically. 
2. [ASSUMPTION] [MATERIAL] [COST: MEDIUM]: The proposal assumes that moving rules out of `CLAUDE.md` and replacing them with cross-references (e.g., "See code-quality.md") will maintain the "same governance" and "same enforcement." This assumes the agent infrastructure automatically reads all referenced files or that the LLM will reliably pause to fetch them before acting. If the LLM relies only on the eagerly loaded `CLAUDE.md` context, removing the inline rules will actively weaken enforcement. This must be tested before adoption.
3. [ALTERNATIVE] [ADVISORY]: Instead of forcing cross-references for everything, a "tiered context" approach might work better: keep critical invariants (like security boundaries and plan gates) fully expanded in the always-loaded `CLAUDE.md`, while offloading only deep-dive domain specifics (like bash diagnostic steps) to supplementary files.

## Concessions
1. Fixing the 4 identified contradictions (Phase 1) is a clear win for agent consistency and reduces confusing prompt collisions.
2. The overarching goal of reducing LLM context bloat to improve instruction adherence is well-supported by current LLM behavior research.
3. Tightening verbose, narrative explanations into terse, directive rules (Phase 3C-3F) is an excellent pattern for system prompts.

## Verdict
REVISE because the proposal targets non-existent files and text strings, and relies on an unverified assumption [SPECULATIVE: ~1,200-1,500 tokens recoverable with zero governance impact] that the agent will perfectly traverse cross-references without dropping compliance.

---

## Challenger D (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL] [COST:SMALL]:** The proposal treats all 15 files as equally loaded per session ("Claude-facing files"), but the repository structure shows a `hooks/hook-context-inject.py` and `hooks/hook-intent-router.py` that selectively inject context. If rule files are conditionally loaded (not all 15 per session), then the token-savings math is wrong and the deduplication strategy may be solving the wrong problem. A file that's only loaded in specific contexts *should* restate its rules locally — a cross-reference to a file that isn't loaded is worse than duplication. The proposal never establishes which files are always-loaded vs. conditionally-loaded, which is load-bearing for every Phase 2 decision.

2. **ASSUMPTION [MATERIAL] [COST:SMALL]:** The "~1,200-1,500 tokens recoverable" claim is SPECULATIVE — no token counts per file are provided, no methodology for the estimate is shown, and the 10-12% figure is derived from an unverified 12,810 total. If the always-loaded subset is smaller (e.g., only CLAUDE.md + 2-3 rules), the recoverable tokens from that subset could be far less than claimed, potentially making Phase 2 and 3 not worth the cross-reference maintenance burden they introduce.

3. **ALTERNATIVE [MATERIAL] [COST:SMALL]:** The proposal frames the choice as "deduplicate via cross-references" vs. "status quo." A missing candidate is **consolidation into fewer files** rather than cross-referencing between many files. If duplication is the problem, merging session-discipline.md + workflow.md into a single `execution.md` eliminates the cross-reference maintenance problem entirely and produces a smaller always-loaded surface. Cross-references between files that may or may not be loaded is a weaker solution than reducing file count.

4. **ASSUMPTION [ADVISORY]:** Phase 1 (fix contradictions) and Phase 2/3 (deduplication/verbosity) are bundled as a single proposal but have completely different risk profiles. Phase 1 fixes genuine correctness bugs (contradictory instructions). Phase 2-3 are optimization. Bundling them means a reviewer who approves Phase 1 implicitly approves the optimization work, and a reviewer who questions Phase 2 may block Phase 1. These should be separable decisions.

5. **OVER-ENGINEERED [ADVISORY]:** Phase 2's cross-reference strategy introduces a new maintenance invariant: "when you update the canonical file, you must remember which files reference it." The proposal doesn't address how this invariant is enforced. The current duplication, while wasteful, is at least self-contained — each file is independently correct. Cross-references create a dependency graph that can silently break (canonical file updated, reference file not updated, Claude gets inconsistent instructions again). The proposal trades one failure mode for another without acknowledging the tradeoff.

6. **ASSUMPTION [ADVISORY]:** The claim that "instruction compliance decreases as instruction count grows" is cited as research but no source is given. This is the primary justification for the entire proposal. If the effect size is small at the scale of 1,200-1,500 tokens (vs. a typical 200K context window), the compliance improvement may be negligible. SPECULATIVE claim driving a MATERIAL recommendation.

7. **ALTERNATIVE [ADVISORY]:** A missing candidate for Phase 3 verbosity reduction is **automated linting** — a script that flags files exceeding a token budget, similar to `hook-memory-size-gate.py` which already exists for memory files. This would prevent verbosity from re-accumulating without requiring manual compression passes, addressing the root cause rather than the symptom.

---

## Concessions

1. **Phase 1 is unambiguously correct.** The four contradictions identified (before/after documentation, session-start reading lists, skip conditions, essential-eight count) are genuine ambiguities that force Claude to make arbitrary reconciliation choices. Fixing these has near-zero risk and clear benefit regardless of whether the rest of the proposal is sound.

2. **The proposal correctly identifies CLAUDE.md as the always-loaded anchor.** Designating it as canonical for pipeline tiers and skip conditions (2C, 2D) is architecturally sound — the always-loaded file should be the source of truth for frequently-referenced rules.

3. **Phase 3A (origin tags) is a clean win.** Origin tags are metadata about rule history, not directives. Removing ~50 tokens of historical annotation has no governance impact and no cross-reference risk.

---

## Verdict

**REVISE** — Phase 1 should be approved immediately as a standalone fix; Phase 2-3 require the proposal to first establish which files are always-loaded vs. conditionally-loaded, because the entire deduplication strategy is invalid if cross-referenced files aren't co-loaded, and the token-savings claim is unverified without that analysis.

---

## Challenger E (frame-factual) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal’s contradiction count is stale on at least two headline items. `.claude/rules/review-protocol.md` already says “**Skip conditions: Defined authoritatively in CLAUDE.md. Do not maintain a separate list here**” (lines 25-27), so Phase 1C is already shipped. `.claude/rules/workflow.md` already says “**Pipeline tiers: see CLAUDE.md. Skip conditions for /challenge: defined authoritatively in CLAUDE.md**” and “**Document first, execute second — See session-discipline.md**” plus “**Verify before done — see review-protocol.md**” (lines 9, 18-19), so parts of Phases 2C, 2D, and 2G are also already done. Recent commits on these files include `e60e35b` and `bfdf4ff`, confirming active recent edits rather than ancient docs drift.

2. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The proposal claims “BuildOS rule files (CLAUDE.md + 10 rule files + 4 reference files)” and targets `.claude/rules/reference/*.md`, but the repository manifest shows no `.claude/rules/reference/` directory at all. The nearest referenced material is `docs/reference/code-quality-detail.md` from `.claude/rules/code-quality.md` line 50, so the stated surface area is factually wrong and the token-savings estimate is built on an incorrect file set.

3. [ASSUMPTION] [MATERIAL] [COST:SMALL]: Phase 1D misstates current governance: the codebase no longer appears to enforce the proposal’s “6 of 8 apply” framing as the live rule source. `docs/hooks.md` describes `.claude/rules/` as the authoritative rule layer above hooks (line 3), and the actual loaded `.claude/rules/review-protocol.md` in the repo does not contain the claimed contradictory “essential eight invariants apply to every change” text in its first 97 lines. Without verifying CLAUDE.md content, this proposal over-anchors on a contradiction that may already be resolved or may exist only in a different doc layer. As written, it treats an unverified premise as a core ambiguity.

4. [UNDER-ENGINEERED] [ADVISORY]: The proposal says “No hooks changed, no enforcement weakened,” but it doesn’t assess whether shortening rule text would reduce clarity for hook-mediated behavior that is advisory rather than blocking. For example, `hook-decompose-gate.py` is explicitly advisory and currently nudges at **≥2** components, not the proposal’s suggested “3+ decompose” simplification (`.claude/rules/orchestration.md` lines 21-29; hook source lines 4-12). If the docs are compressed carelessly here, the documented threshold can drift from the hook behavior again.

## Concessions
- The repo does support the general motivation that rule text should cross-reference canonical sources; `.claude/rules/workflow.md` and `.claude/rules/review-protocol.md` already use that pattern.
- The tightened language proposed for `security.md` and `natural-language-routing.md` is directionally aligned with current file contents; those sections are already fairly concise.
- The proposal correctly avoids changing hooks first; enforcement behavior is largely in deterministic hook code such as `hook-plan-gate.sh`, `hook-review-gate.sh`, and `hook-decompose-gate.py`.

## Verdict
REVISE — the streamlining goal is plausible, but the proposal overstates current contradictions and targets non-existent/already-cleaned surfaces, so it needs a fresh diff against the actual current rule files before it can guide work.

---

---
debate_id: streamline-rules
created: 2026-04-17T13:23:48-0700
mapping:
  A: claude-opus-4-7
  B: claude-sonnet-4-6
  C: claude-sonnet-4-6
  D: claude-sonnet-4-6
  E: claude-opus-4-7
personas:
  A: architect
  B: security
  C: pm
  D: frame-structural
  E: frame-factual
---
# streamline-rules — Challenger Reviews

## Challenger A (architect) — Challenges
Critical finding. The proposal claims to delete "Origin:" tags, "Don't wait for the user to ask..." preamble, "Watch for these anti-patterns..." — none of these strings exist in the rules directory. The proposal is targeting text that isn't there.

Also: CLAUDE.md isn't in the `rules` file_set (it's at repo root), so I can't verify its claims — but many of the contradictions claimed between CLAUDE.md and rules files have already been resolved in the rules files themselves.

## Challenges

1. **ASSUMPTION** [MATERIAL] [COST:SMALL]: The proposal asserts four live contradictions, but tool verification shows at least three are **already resolved** in the current rule files:
   - **1B (orient list):** workflow.md line 7 already reads "read `docs/project-prd.md` (if filled in) + `docs/current-state.md` + `tasks/lessons.md` + `tasks/session-log.md`" — it does **not** reference `project-map.md` (substring not found) as the proposal quotes.
   - **1C (skip conditions):** review-protocol.md line 26 already says "Skip conditions: Defined authoritatively in CLAUDE.md. Do not maintain a separate list here." The proposed fix is already in place.
   - **1D (essential eight):** review-protocol.md line 74 already reads "The essential eight invariants (6 applicable to BuildOS — see CLAUDE.md for applicability) guide every change." This is almost verbatim the proposed fix.
   - **1A (document before/after):** session-discipline.md line 9 says "Persist corrections and decisions after deciding on them and before implementing them." The "BEFORE implementation" caps phrasing the proposal quotes does not appear in the rules directory (substring not found).
   
   EVIDENCED: 4/4 quoted contradictions in Phase 1 do not match current file contents as retrieved. The proposal appears to be written against a stale snapshot of the repo.

2. **ASSUMPTION** [MATERIAL] [COST:SMALL]: Phase 3A targets "Origin:" tags in code-quality.md, bash-failures.md, code-quality-detail.md, skill-authoring.md. Substring search across the rules directory returns zero matches for "Origin" or "Origin:". Phase 3B targets "Watch for these anti-patterns" and "Don't wait for the user to ask" — both return zero matches. These deletions would be no-ops. SPECULATIVE: a previous cleanup may have removed them already; either way the proposal's premise is stale.

3. **ASSUMPTION** [MATERIAL] [COST:TRIVIAL]: Phase 2D claims workflow.md contains a "full tier table" to cut. Reading workflow.md shows it already says "Pipeline tiers: see CLAUDE.md. Skip conditions for `/challenge`: defined authoritatively in CLAUDE.md" (line 9). No tier table to remove.

4. **ASSUMPTION** [ADVISORY]: Phase 2C says workflow.md line 3 is a Verify-before-done block to replace. Actual workflow.md line 19 already reads "**Verify before done** — see review-protocol.md Definition of Done." Already done.

5. **RISK** [MATERIAL] [COST:TRIVIAL]: The token-savings estimate ("~1,200-1,500 tokens, ~10-12%") is built on line counts of text that largely no longer exists in the canonical form the proposal describes. ESTIMATED: actual realized savings are likely a fraction of the claimed figure — perhaps 300-500 tokens from the Phase 3 tightening steps that do have real targets (compaction protocol, Root Cause First in workflow.md, orchestration.md tightening, security.md allowlist/CSV formulas) once those are re-verified against current file contents. SPECULATIVE on exact numbers, but directionally: the ROI case collapses if most Phase 1 and Phase 2 edits are no-ops.

6. **UNDER-ENGINEERED** [ADVISORY]: The proposal has no "re-baseline first" step. Given that many targets have already been addressed, the correct opening move is: diff the current rules against the proposal's quoted excerpts, strike the no-op items, and re-scope to what's actually still duplicated or ambiguous. Without this, a reviewer approving this proposal would be authorizing edits that silently do nothing or (worse) re-introduce churn into already-settled text.

7. **ALTERNATIVE** [ADVISORY]: If the goal is token efficiency, the higher-leverage target is CLAUDE.md itself (always loaded) vs. on-demand rules files. The proposal conflates the two — cutting tokens from review-protocol.md that loads only when gated saves nothing on a typical session. A budget per always-loaded file + a measurement plan (e.g., count bytes actually injected by hook-context-inject.py for N real sessions) would focus the effort.

## Concessions

1. The governance principle is sound: single-sourcing rules with cross-references beats duplication, and aligning verb tense on "before vs. after" for decision-logging is the right call.
2. Phase 3 tightening targets that are still live (compaction protocol thresholds, Root Cause First, orchestration decomposition gate explanation, security allowlist one-liner) are legitimate verbosity and the compressions proposed read cleanly.
3. The "zero rules removed, zero hooks changed" constraint is well-framed — it's an edit, not a policy change, and that's the right envelope for this kind of work.

## Verdict

**REVISE** — the intent is sound and a subset of Phase 3 is worth doing, but the proposal's factual premise (which contradictions exist, which verbose passages exist) is substantially stale. Re-baseline against the current rule files, drop the no-op edits from Phase 1 and 2, and re-estimate savings before merging.

---

## Challenger B (security) — Challenges
## Challenges

1. **ASSUMPTION [ADVISORY]**: The proposal claims ~12,810 total tokens across 15 Claude-facing files and ~1,200-1,500 tokens recoverable (~10-12%). These figures are SPECULATIVE — no token-counting methodology is cited, no per-file breakdown is provided, and the tool calls confirm the rule files exist but cannot verify their current sizes. The 10-12% recovery estimate cannot be validated from the proposal alone.

2. **ASSUMPTION [MATERIAL] [COST:SMALL]**: Several specific contradictions cited in Phase 1 are not verified by the tool calls. Specifically:
   - `check_code_presence("Update decisions.md after material decisions")` → **not found** (0 matches). The "after" wording in CLAUDE.md that 1A proposes to fix may not exist in the current files.
   - `check_code_presence("Every correction must be persisted")` → **not found** (0 matches). The session-discipline.md "BEFORE implementation" wording cited in 1A may not exist.
   - `check_code_presence("6 of 8")` → **not found** (0 matches). The CLAUDE.md "6 of 8 apply" phrasing cited in 1D may not exist verbatim.
   - `check_code_presence("approval gating")` → **not found** (0 matches). The strikethrough items cited in 1D may not exist.
   - `check_code_presence("skip both for")` → **not found** (0 matches). The CLAUDE.md skip-condition wording cited in 1C may not exist verbatim.
   - `check_code_presence("skip-challenge")` → **not found** (0 matches). The review-protocol.md `/plan --skip-challenge` cited in 1C may not exist.
   
   The proposal is built on specific textual contradictions that cannot be confirmed to exist in the current rule files. If the contradictions don't exist as described, Phase 1 fixes are solving phantom problems — or worse, introducing new inconsistencies. **Before any edits, the actual current text of each affected file must be read and the contradictions confirmed.**

3. **ASSUMPTION [MATERIAL] [COST:TRIVIAL]**: Phase 3A proposes removing "Origin:" tags (~50 tokens), but `check_code_presence("Origin:", file_set="rules")` and `check_code_presence("*Origin", file_set="rules")` both return **0 matches**. These tags don't exist in the rules directory. The proposal is targeting content that isn't there. Similarly, Phase 3B's specific preamble strings ("Watch for these anti-patterns", "Don't wait for the user to ask") return 0 matches. The verbosity targets in Phase 3 may be stale or located in files outside the rules directory.

4. **RISK [ADVISORY]**: The "canonical file" designation pattern (Phase 2) creates a new failure mode: if the canonical file is ever edited or reorganized, the referencing files silently become stale pointers. The proposal doesn't address how to keep cross-file references from drifting — there's no lint rule or hook that validates "see X.md" references resolve to actual content. The existing `hook-skill-lint.py` and `scripts/lint_skills.py` cover skill files, not rule files.

5. **ASSUMPTION [ADVISORY]**: The claim that "instruction compliance decreases as instruction count grows" is cited as research but no source is provided. This is the core justification for the entire proposal. It's plausible but SPECULATIVE as stated. The proposal would be stronger with a citation or an empirical observation from this specific system's behavior.

6. **RISK [ADVISORY]**: Phase 2D proposes making CLAUDE.md canonical for the pipeline tier table and having workflow.md and review-protocol.md reference it. CLAUDE.md is described as "always-loaded" — but if CLAUDE.md is ever restructured or the tier table moves within it, the references in workflow.md and review-protocol.md become broken without any automated detection. The proposal trades duplication risk for reference-staleness risk without acknowledging the tradeoff.

7. **OVER-ENGINEERED [ADVISORY]**: The proposal is structured as a 3-phase plan with 16 sub-items. For what is essentially a text editing task on ~15 markdown files, this level of decomposition may be harder to execute correctly than a simpler "read each file, edit in place, verify" approach. The phase structure implies sequencing dependencies (fix contradictions before deduplicating) that are sound, but the sub-item granularity creates coordination overhead without enforcement.

8. **UNDER-ENGINEERED [ADVISORY]**: There's no proposed verification step. After applying ~16 changes across 10+ files, how does the author confirm the result is correct? The proposal has no "Definition of Done" — no diff review, no token recount, no test that the rules still parse correctly. Given that the proposal's own contradiction claims are partially unverified (see finding #2), a verification pass is not optional.

---

## Concessions

1. **The deduplication logic is sound in principle.** Having one canonical location per rule and referencing elsewhere is a legitimate governance pattern. The "canonical file" designations in Phase 2 are well-reasoned (e.g., bash-failures.md for fix-forward, security.md for LLM boundary).

2. **Phase 1 ambiguity fixes are the highest-value work.** Even if the exact wording differs from what's described, resolving genuine contradictions between files (document before vs. after, which docs to read at session start) is worth doing regardless of token savings. The tool calls confirm `decisions.md`, `handoff.md`, `orient-before-planning`, and `TRIVIAL` all exist in the rules, suggesting the underlying concepts are present even if the exact quoted strings aren't.

3. **The constraint is correctly scoped.** Explicitly stating "no rules removed, no hooks changed, no enforcement weakened" is the right framing for a compression proposal. This prevents scope creep and makes the proposal auditable.

---

## Verdict

**REVISE** — The proposal's Phase 1 contradiction fixes are built on specific quoted text that tool verification cannot confirm exists in the current files (multiple 0-match results for the exact strings cited). Phase 3's verbosity targets also show 0 matches for several specific strings. The proposal must be grounded in the actual current file contents before any edits are made; otherwise it risks introducing new inconsistencies while "fixing" ones that don't exist. Read the actual files first, then restate the contradictions with verified quotes.

---

## Challenger C (pm) — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL] [COST:SMALL]**: The proposal's central quantitative claim — "~12,810 tokens across 15 Claude-facing files, ~1,200-1,500 tokens recoverable (~10-12%)" — is SPECULATIVE. No token counts are shown per file, no methodology is given for the estimate, and the proposal doesn't demonstrate that the identified cuts actually sum to 1,200-1,500 tokens. The tool calls confirm the files exist and have the stated content, but the token arithmetic is unverified. If the actual recovery is 300-400 tokens (plausible given the actual file sizes observed — e.g., `review-protocol.md` is 97 lines, `workflow.md` is 70 lines), the ROI case weakens substantially. The proposal should show a per-file token count before claiming a 10-12% recovery.

2. **ASSUMPTION [MATERIAL] [COST:TRIVIAL]**: The proposal asserts "Origin:" tags exist in `code-quality.md`, `bash-failures.md`, `code-quality-detail.md`, and `skill-authoring.md` (Phase 3A, ~50 tokens). Tool verification found **zero matches** for "Origin:" across all rule files and docs. This is a phantom cut — Phase 3A removes nothing because the content doesn't exist. This undermines confidence in the token recovery estimate.

3. **ASSUMPTION [MATERIAL] [COST:SMALL]**: The "1A — Document before or after" contradiction is partially overstated. Tool verification confirms `session-discipline.md` does say "Persist corrections and decisions after deciding on them and before implementing" — which is consistent with "before implementation." The proposal characterizes CLAUDE.md as saying "after material decisions" (implying after implementation), but the actual CLAUDE.md text wasn't verified in the tool results. If CLAUDE.md's "after" refers to "after deciding" (not "after implementing"), there may be no contradiction — just imprecise phrasing. The fix may be a clarification, not a contradiction resolution.

4. **RISK [MATERIAL] [COST:MEDIUM]**: The "canonical file + reference" pattern for 7 deduplications (Phase 2) introduces a new failure mode: **reference chains during context loading**. Claude's context injection is file-scoped. If `session-discipline.md` says "see review-protocol.md for Definition of Done" but `review-protocol.md` isn't loaded in that session's context (it has glob restrictions: `tasks/phase*-review*`, `tasks/*-proposal*`, etc.), the reference is a dead link at runtime. The proposal doesn't audit which files are always-loaded vs. glob-gated before creating cross-references. This could silently degrade governance for sessions that don't match the glob patterns.

5. **RISK [ADVISORY]**: Phase 3B proposes removing preambles from `design.md` ("Watch for these anti-patterns...") and `natural-language-routing.md`. Tool verification shows `design.md` already has "**Any listed anti-pattern detected => rewrite.**" at line 11 — the preamble the proposal wants to cut may already be the tighter version. Cutting further risks removing the imperative framing that makes the checklist actionable rather than advisory.

6. **OVER-ENGINEERED [ADVISORY]**: The proposal is structured as a 3-phase, 16-sub-item project with named canonicals, cross-reference rewrites, and verbosity tightening. For a ~70-100 line total change across 10 files, this level of project structure is disproportionate. The 4 contradiction fixes (Phase 1) are the only changes with clear, verifiable governance value. Phases 2 and 3 are optimization work that could be done incrementally without a formal proposal.

7. **UNDER-ENGINEERED [MATERIAL] [COST:SMALL]**: The proposal doesn't address **validation**. After 16 sub-changes across 10 files, how does the team verify that no rule was accidentally dropped, weakened, or made unreachable? There's no proposed diff review process, no "before/after rule inventory," and no test that cross-references resolve correctly. Given that `hook-skill-lint.py` and `hook-spec-status-check.py` exist, it's worth checking whether any lint hook validates rule file integrity — if not, this refactor has no safety net.

8. **ASSUMPTION [ADVISORY]**: The claim that "instruction compliance decreases as instruction count grows" is cited as research motivation but no source is given. This is SPECULATIVE as stated. It's a plausible hypothesis, but the actual compliance impact of removing ~1,200 tokens from a ~12,800-token rule set (assuming the estimate is correct) is not demonstrated. The proposal would be stronger if it cited a specific study or BuildOS-internal telemetry showing compliance degradation correlated with rule file size.

---

## Concessions

1. **The 4 contradiction fixes (Phase 1) are genuinely valuable.** Tool verification confirms the "essential eight" contradiction exists (1 match in rules vs. 5 in docs with different framing), and the "before/after implementation" ambiguity in session-discipline.md is real. Contradictions in always-loaded governance files are a concrete failure mode, not a theoretical one.

2. **The glob-gated canonicalization concern aside, the deduplication logic is sound in principle.** Designating one file as canonical and replacing duplicates with references is the right architectural pattern — the execution risk (dead references in non-matching sessions) is fixable with an audit step, not a reason to abandon the approach.

3. **Phase 3 verbosity cuts are low-risk.** The orchestration.md and security.md tightening proposals preserve the rule content while reducing noise. Even if the token savings are smaller than estimated, these changes don't introduce new failure modes.

---

## Verdict

**REVISE** — Fix the phantom Phase 3A cut (Origin: tags don't exist), audit cross-references against glob-gated loading before executing Phase 2, and verify the CLAUDE.md "after" wording before claiming contradiction 1A. The Phase 1 contradiction fixes are approvable as-is; Phases 2-3 need the reference-chain loading audit before execution.

---

## Challenger D (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL] [COST:SMALL]:** The proposal treats "same governance, same enforcement" as a constraint, but the actual risk of cross-file references is that they create *load-order dependencies* that didn't exist before. When CLAUDE.md says "see code-quality.md" and code-quality.md is not guaranteed to be in context at the moment Claude needs the rule, the reference is a dead link. The proposal never establishes which files are always-loaded vs. conditionally-loaded. If code-quality.md, bash-failures.md, or session-discipline.md are not always in context, then replacing inline rules with references *does* weaken enforcement — it just does so silently. The proposal asserts "CLAUDE.md is always loaded" but makes no equivalent claim for the target files of its references. This is load-bearing and unverified.

2. **ASSUMPTION [MATERIAL] [COST:SMALL]:** The token savings claim (~1,200-1,500 tokens, ~10-12%) is SPECULATIVE — no word counts or token counts per file are provided, only a total estimate for the 15-file corpus. The proposal doesn't show which specific cuts produce which token savings, making it impossible to verify whether Phase 3 micro-compressions (35 tokens here, 40 tokens there) are worth the editorial risk of introducing new ambiguity through over-tightening. The 10-12% figure is doing load-bearing work in the justification but has no evidenced basis.

3. **ALTERNATIVE [MATERIAL] [COST:SMALL]:** The candidate set is binary: either (A) deduplicate by cross-referencing, or (B) status quo. A missing option is **single-source consolidation** — move all rules into CLAUDE.md (or one canonical file) and eliminate the satellite files entirely for the duplicated sections, rather than creating a web of "see X" pointers. Cross-references add a new failure mode (stale pointer, file not in context) that the current duplication doesn't have. Duplication is robust to partial context; references are not. The proposal never considers whether the reference graph it's creating is more fragile than the duplication it's replacing.

4. **ASSUMPTION [ADVISORY]:** The claim that "instruction compliance decreases as instruction count grows" is cited as research motivation but no source is given. This is SPECULATIVE as stated. More importantly, it conflates *total token count* with *instruction count* — the proposal's fixes reduce tokens but may not reduce the number of distinct directives Claude must track. Replacing 6 lines with "see code-quality.md" doesn't reduce instruction count; it adds an indirection step.

5. **OVER-ENGINEERED [ADVISORY]:** Phase 3 micro-compressions (3A through 3F) are individually trivial but collectively introduce editorial risk disproportionate to their yield. Removing "Watch for these anti-patterns in generated UI" as a "preamble" may actually be load-bearing context that helps Claude recognize when the rule applies. The proposal treats all preamble as waste, but some preamble is scope-delimiting. The 30-150 token savings per item don't justify the risk of a rule becoming ambiguous in its application domain.

6. **ALTERNATIVE [ADVISORY]:** The proposal never considers a **linting/validation approach** as an alternative to manual deduplication — e.g., a script that detects when the same rule appears in multiple files and flags it, without restructuring the files. This would address the maintenance problem (new duplications accumulating) without creating reference dependencies. Given that the repo already has `scripts/lint_skills.py`, `hook-skill-lint.py`, and a `hook-spec-status-check.py`, the infrastructure for automated governance checks exists. A duplication-detector would be more durable than a one-time editorial pass.

7. **RISK [MATERIAL] [COST:MEDIUM]:** Fix 1A ("document before or after implementation") changes the semantics of when decisions.md is updated. The proposal asserts CLAUDE.md's "after" is "the outlier" and should be changed to "before," but doesn't verify whether the current "after" behavior is intentional — perhaps decisions.md is updated *after* because the decision isn't final until implementation confirms it's viable. Changing this without understanding why the divergence exists could introduce a new behavioral error (Claude documents a decision it then reverses, leaving a stale record). The proposal treats this as a simple typo fix when it may be a deliberate design choice.

---

## Concessions

1. **The four contradictions in Phase 1 are genuine.** Conflicting instructions about when to document, which files to read at session start, skip conditions for /challenge, and the essential-eight count are real ambiguities that force Claude to make arbitrary choices. Resolving these has clear value independent of any token savings argument.

2. **The canonical-file designation approach in Phase 2 is sound in principle.** Identifying one authoritative location per rule and having others reference it is a standard documentation architecture. The execution risk (load-order dependencies) is real but fixable.

3. **The proposal correctly scopes itself to compression, not reduction.** The constraint "no rules removed, no hooks changed" is well-stated and prevents scope creep into governance changes.

---

## Verdict

**REVISE** — The frame has a load-bearing unverified assumption: that the target files of cross-references are always in Claude's context when needed. If they're not, Phase 2's deduplication silently weakens enforcement rather than preserving it. The proposal should either (a) establish which files are always-loaded and restrict references to those targets only, or (b) consider single-source consolidation into CLAUDE.md for the duplicated content rather than a reference web. Phase 1 (contradiction fixes) is independently approvable and should proceed regardless.

---

## Challenger E (frame-factual) — Challenges
So workflow.md's "Fix-Forward Rule" is already just 2 lines referring to bash-failures.md — proposal 2E claims to cut "8-line section" that isn't there.

I have enough evidence. The proposal's factual basis is substantially wrong — many of the "contradictions" and duplications it promises to fix have already been resolved, and several quoted strings don't exist in the files.

## Challenges

1. **ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 1D claims review-protocol.md says *"The essential eight invariants apply to every change"* with all 8 listed. The actual file (line 74) reads: *"The essential eight invariants (6 applicable to BuildOS — see CLAUDE.md for applicability) guide every change."* The "fix" is already shipped. Proposing to change wording that already matches the proposed wording is noise.

2. **ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 1C claims review-protocol.md restates skip conditions. The actual file (line 26) already says: *"Defined authoritatively in CLAUDE.md. Do not maintain a separate list here."* Already canonicalized.

3. **ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 2D claims workflow.md contains a full tier table and review-protocol.md contains "Typical paths by change type." Actual workflow.md line 9: *"Pipeline tiers: see CLAUDE.md. Skip conditions for `/challenge`: defined authoritatively in CLAUDE.md."* Actual review-protocol.md line 60: *"Tier definitions and full pipeline routes: see CLAUDE.md."* Both cuts already done.

4. **ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 2C and 2G claim workflow.md has a verbose "Verify before done" line and a full "Document first, execute second" bullet to replace. Actual workflow.md line 18: *"Document first, execute second — decide, then document, then implement. See session-discipline.md for destination rules."* Line 19: *"Verify before done — see review-protocol.md Definition of Done."* Both are already one-liners referencing canonical sources.

5. **ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 2E claims workflow.md has an "8-line Fix-Forward Rule section" to compress. Actual content (lines 58-60) is already 2 lines: *"Never silently work around the same infrastructure failure twice. See bash-failures.md for the full fix-forward protocol."* Already compressed.

6. **ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 3A says to "Delete lines matching `*Origin: ...*`" from four rule files. `check_code_presence` for `"Origin:"` and `"Origin"` in the rules file set returns `exists: false` and `match_count: 0`. The tags don't exist. Token savings of "~50 tokens" are not recoverable because the tokens aren't there.

7. **ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 3B claims specific preambles exist to delete. design.md does NOT contain *"Watch for these anti-patterns in generated UI and content. Any match = rewrite."* — it says *"Any listed anti-pattern detected => rewrite."* inline as the checklist intro. natural-language-routing.md does NOT contain *"Don't wait for the user to ask..."* — it opens with a routing table. The quoted preambles appear fabricated.

8. **ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 1A frames a contradiction by quoting session-discipline.md as *"Every correction must be persisted BEFORE implementation."* That exact string does not appear in the file (`match_count: 0`). The actual line 9 reads: *"Persist corrections and decisions after deciding on them and before implementing them."* This is semantically consistent with workflow.md's "document first, execute second" — there is no contradiction to fix. The alleged CLAUDE.md "after material decisions" outlier cannot be verified from the tools available here but the premise of a three-way conflict collapses once session-discipline.md is read accurately.

9. **ASSUMPTION [ADVISORY]**: Phase 1B quotes workflow.md as requiring *"docs/project-prd.md + docs/project-map.md + docs/current-state.md + tasks/lessons.md + tasks/session-log.md."* The actual line 7 omits `docs/project-map.md` entirely (search confirms `project-map.md` does not appear anywhere in rules). Quote is inaccurate; the divergence between CLAUDE.md and workflow.md may be smaller than claimed.

10. **OVER-ENGINEERED [MATERIAL] [COST:N/A]**: The ~1,200–1,500-token savings estimate is SPECULATIVE and inflated — a large fraction of the itemized cuts (2C, 2D, 2E, 2G, 1C, 1D, 3A) target text that is already a one-liner or absent. If half the line items are no-ops, realistic savings are a fraction of the claim, well under the noise floor of a single prompt iteration. Running `/challenge → refine` on a proposal whose diff is largely empty is negative-value work.

11. **RISK [MATERIAL] [COST:SMALL]**: Because the proposal's quoted "current state" is stale or fabricated in many places, applying its edits as-written risks *regressing* already-canonicalized pointers (e.g., rewriting review-protocol.md line 74 from the correct "(6 applicable to BuildOS…)" to the proposed wording could drop "for applicability" nuance, or re-introduce deleted text if an editor takes the proposal's `Current state` quote as authoritative). A revise pass must reread the files line-numbered before any edit.

## Concessions

1. The underlying intent — canonical-source-per-rule with one-line references elsewhere — is the right model, and the repo has clearly been moving that direction already (commits "Apply review findings M1+A1+A2 to bundle-1," review-protocol.md lines 26/60/74). So the proposal's *direction* matches the codebase's trajectory.
2. The verbosity tightening targets that DO exist (security.md allowlist/CSV, orchestration.md decomposition gate/file references, session-discipline.md compaction thresholds, workflow.md Root Cause First) are legitimate compression candidates worth evaluating on their own merits.
3. The observation that instruction-following degrades with instruction count and duplication is well-supported and a valid motivator.

## Verdict

**REJECT** — The proposal's "Current state" quotations are wrong or stale for at least 6 of its 11 itemized cuts (1C, 1D, 2C, 2D, 2E, 2G, 3A, plus partial defects in 1A/1B/3B). The majority of Phase 1 and Phase 2 describes fixes that have already shipped. The token-savings number is therefore unsupported. The proposal should be rebuilt from a fresh line-numbered read of each rule file, keeping only the verbosity targets in Phase 3 that survive verification (security.md, orchestration.md, session-discipline.md compaction, workflow.md Root Cause First).

---

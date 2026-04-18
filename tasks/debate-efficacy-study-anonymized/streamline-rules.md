# Anonymized Findings — streamline-rules

Total: 64 findings pooled from two anonymous reviewer panels.
Arm C contributed 41; arm D contributed 23.
Arm identity is withheld from the judge by design.

---

## Finding 1

**ASSUMPTION [MATERIAL] [COST:TRIVIAL]**: The 1A "contradiction" is overstated. session-discipline.md line 9 actually says *"Persist corrections and decisions after deciding on them and **before implementing them**"* — which already aligns with workflow.md's "Document first, execute second." The proposal quotes a caps-locked "BEFORE implementation" that isn't the live text. Only CLAUDE.md's "after material decisions" is genuinely outlier — and that's a one-word edit, not a 3-file reconciliation. [EVIDENCED by file read above.]

## Finding 2

[UNDER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: The proposal reduces directly-embedded security guidance in favor of referencing `security.md`, but it does not define a protection rule for “never summarize away security-critical directives.” That is risky because security instructions are precisely the class least safe to compress across files. The repo already treats tool output/logging as sensitive (`security.md:15`, `23`) and has advisory hooks that inject extra context (`hook-context-inject.py`) and telemetry/watchlists (`hook-session-telemetry.py`), so losing direct local reminders can increase chances of accidental data exposure or unsafe command construction even if the underlying hooks remain unchanged.

## Finding 3

[RISK] [MATERIAL] [COST: SMALL]: The proposal targets files and file contents that do not exist in the repository. The manifest confirms there are exactly 10 rule files, with no `reference/` directory or `code-quality-detail.md` file. Furthermore, tool verification confirms that the strings `Origin:` and `Watch for these anti-patterns` do not exist in the `.claude/rules/` directory. Attempting to apply these text replacements will fail mechanically.

## Finding 4

**ALTERNATIVE [ADVISORY]:** A missing candidate for Phase 3 verbosity reduction is **automated linting** — a script that flags files exceeding a token budget, similar to `hook-memory-size-gate.py` which already exists for memory files. This would prevent verbosity from re-accumulating without requiring manual compression passes, addressing the root cause rather than the symptom.

---

## Finding 5

[ALTERNATIVE] [ADVISORY]: For high-signal rules with security or irreversible-action implications, a better pattern may be “headline retained everywhere, details canonicalized once” rather than pure cross-reference. The repo already uses layered enforcement—advice → rules → hooks → architecture (`docs/hooks.md:3`). Mirroring that in docs would preserve local reminders while still reclaiming most of the token savings.

## Finding 6

[ASSUMPTION] [MATERIAL] [COST: MEDIUM]: The proposal assumes that moving rules out of `CLAUDE.md` and replacing them with cross-references (e.g., "See code-quality.md") will maintain the "same governance" and "same enforcement." This assumes the agent infrastructure automatically reads all referenced files or that the LLM will reliably pause to fetch them before acting. If the LLM relies only on the eagerly loaded `CLAUDE.md` context, removing the inline rules will actively weaken enforcement. This must be tested before adoption.

## Finding 7

**UNDER-ENGINEERED** [ADVISORY]: The proposal has no "re-baseline first" step. Given that many targets have already been addressed, the correct opening move is: diff the current rules against the proposal's quoted excerpts, strike the no-op items, and re-scope to what's actually still duplicated or ambiguous. Without this, a reviewer approving this proposal would be authorizing edits that silently do nothing or (worse) re-introduce churn into already-settled text.

## Finding 8

**UNDER-ENGINEERED [MATERIAL] [COST:SMALL]**: The proposal doesn't address **validation**. After 16 sub-changes across 10 files, how does the team verify that no rule was accidentally dropped, weakened, or made unreachable? There's no proposed diff review process, no "before/after rule inventory," and no test that cross-references resolve correctly. Given that `hook-skill-lint.py` and `hook-spec-status-check.py` exist, it's worth checking whether any lint hook validates rule file integrity — if not, this refactor has no safety net.

## Finding 9

[ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal’s contradiction count is stale on at least two headline items. `.claude/rules/review-protocol.md` already says “**Skip conditions: Defined authoritatively in CLAUDE.md. Do not maintain a separate list here**” (lines 25-27), so Phase 1C is already shipped. `.claude/rules/workflow.md` already says “**Pipeline tiers: see CLAUDE.md. Skip conditions for /challenge: defined authoritatively in CLAUDE.md**” and “**Document first, execute second — See session-discipline.md**” plus “**Verify before done — see review-protocol.md**” (lines 9, 18-19), so parts of Phases 2C, 2D, and 2G are also already done. Recent commits on these files include `e60e35b` and `bfdf4ff`, confirming active recent edits rather than ancient docs drift.

## Finding 10

**RISK [MATERIAL] [COST:MEDIUM]**: The "canonical file + reference" pattern for 7 deduplications (Phase 2) introduces a new failure mode: **reference chains during context loading**. Claude's context injection is file-scoped. If `session-discipline.md` says "see review-protocol.md for Definition of Done" but `review-protocol.md` isn't loaded in that session's context (it has glob restrictions: `tasks/phase*-review*`, `tasks/*-proposal*`, etc.), the reference is a dead link at runtime. The proposal doesn't audit which files are always-loaded vs. glob-gated before creating cross-references. This could silently degrade governance for sessions that don't match the glob patterns.

## Finding 11

**ASSUMPTION [MATERIAL] [COST:TRIVIAL]**: Phase 3A proposes removing "Origin:" tags (~50 tokens), but `check_code_presence("Origin:", file_set="rules")` and `check_code_presence("*Origin", file_set="rules")` both return **0 matches**. These tags don't exist in the rules directory. The proposal is targeting content that isn't there. Similarly, Phase 3B's specific preamble strings ("Watch for these anti-patterns", "Don't wait for the user to ask") return 0 matches. The verbosity targets in Phase 3 may be stale or located in files outside the rules directory.

## Finding 12

**OVER-ENGINEERED [ADVISORY]**: The proposal is structured as a 3-phase, 16-sub-item project with named canonicals, cross-reference rewrites, and verbosity tightening. For a ~70-100 line total change across 10 files, this level of project structure is disproportionate. The 4 contradiction fixes (Phase 1) are the only changes with clear, verifiable governance value. Phases 2 and 3 are optimization work that could be done incrementally without a formal proposal.

## Finding 13

**ALTERNATIVE [ADVISORY]**: The underlying issue revealed here isn't "rule files are verbose" — it's "proposals about rule files are being drafted against stale snapshots." The higher-leverage fix is a **pre-flight diff check** (small script or hook): any proposal touching `.claude/rules/` must include current-file line citations, not paraphrases. This prevents the class of drift-vs-reality errors this proposal exhibits and that no amount of compression addresses.

## Finding 14

**OVER-ENGINEERED [ADVISORY]**: Phases 2 and 3 bundle 13 independent edits into one proposal. Each deduplication/tightening is mechanically independent. A single PR lands or bounces atomically — reviewers have to evaluate 13 judgment calls at once. Split into (a) ambiguity fixes that are actually ambiguous post-verification, (b) verbosity tightenings with before/after token counts.

## Finding 15

**RISK [ADVISORY]**: The "canonical file" designation pattern (Phase 2) creates a new failure mode: if the canonical file is ever edited or reorganized, the referencing files silently become stale pointers. The proposal doesn't address how to keep cross-file references from drifting — there's no lint rule or hook that validates "see X.md" references resolve to actual content. The existing `hook-skill-lint.py` and `scripts/lint_skills.py` cover skill files, not rule files.

## Finding 16

**ASSUMPTION [MATERIAL] [COST:TRIVIAL]**: Several of the proposal's "current state" quotes don't match the actual files. Verified contradictions that are **already resolved**:
   - **1C (skip conditions):** review-protocol.md line 26 already says *"Skip conditions: Defined authoritatively in CLAUDE.md. Do not maintain a separate list here."* workflow.md line 9 says the same. No duplication to cut.
   - **1D (essential eight):** review-protocol.md line 74 already reads *"The essential eight invariants (6 applicable to BuildOS — see CLAUDE.md for applicability) guide every change."* — nearly verbatim the proposal's "fix."
   - **2C (verify before done):** session-discipline.md line 64 already reads *"Prove it works before calling it done. See review-protocol.md Definition of Done. Additionally: sanity-check data volumes..."* — verbatim the proposal's target. workflow.md line 19 already delegates. Nothing to cut.
   - **2D (pipeline tiers):** workflow.md line 9 already says *"Pipeline tiers: see CLAUDE.md."* review-protocol.md line 60 says *"Tier definitions and full pipeline routes: see CLAUDE.md."* Done.
   - **3A (origin tags):** `check_code_presence` for `Origin:` in rules/ → **zero matches**. There are no origin tags to delete. (EVIDENCED: tool returned `exists=false, match_count=0`.)
   - **1B (orient list):** workflow.md does NOT include `project-map.md` and the list the proposal quotes is stale.
   
   **Impact on recommendation:** at least 5 of the 11 enumerated changes in Phases 1-3 are already implemented or target non-existent text. The token-savings claim (1,200-1,500) needs recomputation against the actual current files, not the quoted snapshot. Fix: re-audit against HEAD before sizing the work.

## Finding 17

[ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal assumes “same governance, same enforcement” despite changing the rule text that humans/models read at decision time, but it does not verify how rule loading, prompting, or cross-file references are actually assembled. If these files are not co-loaded consistently, replacing duplicated rules with “see X” can weaken enforcement in practice by moving critical constraints across a trust boundary from directly-present instruction to indirectly-referenced instruction. This matters most for security and review gating language. I could verify hook enforcement exists (`docs/hooks.md`, `hook-guard-env.sh`), but not from this proposal whether the Claude-facing prompt assembly guarantees the canonical file is present whenever the referring file is loaded.

## Finding 18

**ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 1A frames a contradiction by quoting session-discipline.md as *"Every correction must be persisted BEFORE implementation."* That exact string does not appear in the file (`match_count: 0`). The actual line 9 reads: *"Persist corrections and decisions after deciding on them and before implementing them."* This is semantically consistent with workflow.md's "document first, execute second" — there is no contradiction to fix. The alleged CLAUDE.md "after material decisions" outlier cannot be verified from the tools available here but the premise of a three-way conflict collapses once session-discipline.md is read accurately.

## Finding 19

[UNDER-ENGINEERED] [ADVISORY]: The proposal says “No hooks changed, no enforcement weakened,” but it doesn’t assess whether shortening rule text would reduce clarity for hook-mediated behavior that is advisory rather than blocking. For example, `hook-decompose-gate.py` is explicitly advisory and currently nudges at **≥2** components, not the proposal’s suggested “3+ decompose” simplification (`.claude/rules/orchestration.md` lines 21-29; hook source lines 4-12). If the docs are compressed carelessly here, the documented threshold can drift from the hook behavior again.

## Finding 20

**RISK [ADVISORY]**: Phase 2D proposes making CLAUDE.md canonical for the pipeline tier table and having workflow.md and review-protocol.md reference it. CLAUDE.md is described as "always-loaded" — but if CLAUDE.md is ever restructured or the tier table moves within it, the references in workflow.md and review-protocol.md become broken without any automated detection. The proposal trades duplication risk for reference-staleness risk without acknowledging the tradeoff.

## Finding 21

**OVER-ENGINEERED [ADVISORY]**: The proposal is structured as a 3-phase plan with 16 sub-items. For what is essentially a text editing task on ~15 markdown files, this level of decomposition may be harder to execute correctly than a simpler "read each file, edit in place, verify" approach. The phase structure implies sequencing dependencies (fix contradictions before deduplicating) that are sound, but the sub-item granularity creates coordination overhead without enforcement.

## Finding 22

**OVER-ENGINEERED [ADVISORY]:** Phase 3 micro-compressions (3A through 3F) are individually trivial but collectively introduce editorial risk disproportionate to their yield. Removing "Watch for these anti-patterns in generated UI" as a "preamble" may actually be load-bearing context that helps Claude recognize when the rule applies. The proposal treats all preamble as waste, but some preamble is scope-delimiting. The 30-150 token savings per item don't justify the risk of a rule becoming ambiguous in its application domain.

## Finding 23

**ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 1D claims review-protocol.md says *"The essential eight invariants apply to every change"* with all 8 listed. The actual file (line 74) reads: *"The essential eight invariants (6 applicable to BuildOS — see CLAUDE.md for applicability) guide every change."* The "fix" is already shipped. Proposing to change wording that already matches the proposed wording is noise.

## Finding 24

**ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 3A says to "Delete lines matching `*Origin: ...*`" from four rule files. `check_code_presence` for `"Origin:"` and `"Origin"` in the rules file set returns `exists: false` and `match_count: 0`. The tags don't exist. Token savings of "~50 tokens" are not recoverable because the tokens aren't there.

## Finding 25

**ASSUMPTION [ADVISORY]**: Phase 1B quotes workflow.md as requiring *"docs/project-prd.md + docs/project-map.md + docs/current-state.md + tasks/lessons.md + tasks/session-log.md."* The actual line 7 omits `docs/project-map.md` entirely (search confirms `project-map.md` does not appear anywhere in rules). Quote is inaccurate; the divergence between CLAUDE.md and workflow.md may be smaller than claimed.

## Finding 26

**ASSUMPTION** [ADVISORY]: Phase 2C says workflow.md line 3 is a Verify-before-done block to replace. Actual workflow.md line 19 already reads "**Verify before done** — see review-protocol.md Definition of Done." Already done.

## Finding 27

**UNDER-ENGINEERED [ADVISORY]**: There's no proposed verification step. After applying ~16 changes across 10+ files, how does the author confirm the result is correct? The proposal has no "Definition of Done" — no diff review, no token recount, no test that the rules still parse correctly. Given that the proposal's own contradiction claims are partially unverified (see finding #2), a verification pass is not optional.

---

## Finding 28

**ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 3B claims specific preambles exist to delete. design.md does NOT contain *"Watch for these anti-patterns in generated UI and content. Any match = rewrite."* — it says *"Any listed anti-pattern detected => rewrite."* inline as the checklist intro. natural-language-routing.md does NOT contain *"Don't wait for the user to ask..."* — it opens with a routing table. The quoted preambles appear fabricated.

## Finding 29

**ASSUMPTION [MATERIAL] [COST:SMALL]:** The token savings claim (~1,200-1,500 tokens, ~10-12%) is SPECULATIVE — no word counts or token counts per file are provided, only a total estimate for the 15-file corpus. The proposal doesn't show which specific cuts produce which token savings, making it impossible to verify whether Phase 3 micro-compressions (35 tokens here, 40 tokens there) are worth the editorial risk of introducing new ambiguity through over-tightening. The 10-12% figure is doing load-bearing work in the justification but has no evidenced basis.

## Finding 30

**ASSUMPTION [ADVISORY]**: The claim that "instruction compliance decreases as instruction count grows" is cited as research motivation but no source is given. This is SPECULATIVE as stated. It's a plausible hypothesis, but the actual compliance impact of removing ~1,200 tokens from a ~12,800-token rule set (assuming the estimate is correct) is not demonstrated. The proposal would be stronger if it cited a specific study or BuildOS-internal telemetry showing compliance degradation correlated with rule file size.

---

## Finding 31

**ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 2E claims workflow.md has an "8-line Fix-Forward Rule section" to compress. Actual content (lines 58-60) is already 2 lines: *"Never silently work around the same infrastructure failure twice. See bash-failures.md for the full fix-forward protocol."* Already compressed.

## Finding 32

**OVER-ENGINEERED [MATERIAL] [COST:N/A]**: The ~1,200–1,500-token savings estimate is SPECULATIVE and inflated — a large fraction of the itemized cuts (2C, 2D, 2E, 2G, 1C, 1D, 3A) target text that is already a one-liner or absent. If half the line items are no-ops, realistic savings are a fraction of the claim, well under the noise floor of a single prompt iteration. Running `/challenge → refine` on a proposal whose diff is largely empty is negative-value work.

## Finding 33

**ALTERNATIVE** [ADVISORY]: If the goal is token efficiency, the higher-leverage target is CLAUDE.md itself (always loaded) vs. on-demand rules files. The proposal conflates the two — cutting tokens from review-protocol.md that loads only when gated saves nothing on a typical session. A budget per always-loaded file + a measurement plan (e.g., count bytes actually injected by hook-context-inject.py for N real sessions) would focus the effort.

## Finding 34

**ASSUMPTION [ADVISORY]:** The claim that "instruction compliance decreases as instruction count grows" is cited as research but no source is given. This is the primary justification for the entire proposal. If the effect size is small at the scale of 1,200-1,500 tokens (vs. a typical 200K context window), the compliance improvement may be negligible. SPECULATIVE claim driving a MATERIAL recommendation.

## Finding 35

**ASSUMPTION [MATERIAL] [COST:SMALL]**: The "1A — Document before or after" contradiction is partially overstated. Tool verification confirms `session-discipline.md` does say "Persist corrections and decisions after deciding on them and before implementing" — which is consistent with "before implementation." The proposal characterizes CLAUDE.md as saying "after material decisions" (implying after implementation), but the actual CLAUDE.md text wasn't verified in the tool results. If CLAUDE.md's "after" refers to "after deciding" (not "after implementing"), there may be no contradiction — just imprecise phrasing. The fix may be a clarification, not a contradiction resolution.

## Finding 36

**RISK [ADVISORY]**: Phase 3B proposes removing preambles from `design.md` ("Watch for these anti-patterns...") and `natural-language-routing.md`. Tool verification shows `design.md` already has "**Any listed anti-pattern detected => rewrite.**" at line 11 — the preamble the proposal wants to cut may already be the tighter version. Cutting further risks removing the imperative framing that makes the checklist actionable rather than advisory.

## Finding 37

**ASSUMPTION [MATERIAL] [COST:SMALL]:** The "~1,200-1,500 tokens recoverable" claim is SPECULATIVE — no token counts per file are provided, no methodology for the estimate is shown, and the 10-12% figure is derived from an unverified 12,810 total. If the always-loaded subset is smaller (e.g., only CLAUDE.md + 2-3 rules), the recoverable tokens from that subset could be far less than claimed, potentially making Phase 2 and 3 not worth the cross-reference maintenance burden they introduce.

## Finding 38

**ASSUMPTION** [MATERIAL] [COST:TRIVIAL]: Phase 2D claims workflow.md contains a "full tier table" to cut. Reading workflow.md shows it already says "Pipeline tiers: see CLAUDE.md. Skip conditions for `/challenge`: defined authoritatively in CLAUDE.md" (line 9). No tier table to remove.

## Finding 39

**ASSUMPTION [ADVISORY]:** Phase 1 (fix contradictions) and Phase 2/3 (deduplication/verbosity) are bundled as a single proposal but have completely different risk profiles. Phase 1 fixes genuine correctness bugs (contradictory instructions). Phase 2-3 are optimization. Bundling them means a reviewer who approves Phase 1 implicitly approves the optimization work, and a reviewer who questions Phase 2 may block Phase 1. These should be separable decisions.

## Finding 40

**RISK [ADVISORY]**: The quantitative claim "~1,200-1,500 tokens recoverable (~10-12%)" is [SPECULATIVE] — no measurement methodology shown, and since ~40%+ of the line items appear stale or already done, the real recoverable delta is materially smaller. A governance-facing proposal claiming token savings should cite `wc -w` or tokenizer output before and after.

## Finding 41

**ASSUMPTION [ADVISORY]**: The claim that "instruction compliance decreases as instruction count grows" is cited as research but no source is provided. This is the core justification for the entire proposal. It's plausible but SPECULATIVE as stated. The proposal would be stronger with a citation or an empirical observation from this specific system's behavior.

## Finding 42

**ASSUMPTION [MATERIAL] [COST:SMALL]:** The proposal treats "same governance, same enforcement" as a constraint, but the actual risk of cross-file references is that they create *load-order dependencies* that didn't exist before. When CLAUDE.md says "see code-quality.md" and code-quality.md is not guaranteed to be in context at the moment Claude needs the rule, the reference is a dead link. The proposal never establishes which files are always-loaded vs. conditionally-loaded. If code-quality.md, bash-failures.md, or session-discipline.md are not always in context, then replacing inline rules with references *does* weaken enforcement — it just does so silently. The proposal asserts "CLAUDE.md is always loaded" but makes no equivalent claim for the target files of its references. This is load-bearing and unverified.

## Finding 43

[RISK] [ADVISORY]: Consolidating skip conditions for `/challenge` into `CLAUDE.md` improves consistency, but it also makes that file a higher-value governance choke point. If `CLAUDE.md` drifts or is omitted from a future environment, challenge-gating policy degrades broadly. The risk of not changing is continued ambiguity; the risk of changing is concentrating control without an explicit integrity check.

## Finding 44

**ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 2C and 2G claim workflow.md has a verbose "Verify before done" line and a full "Document first, execute second" bullet to replace. Actual workflow.md line 18: *"Document first, execute second — decide, then document, then implement. See session-discipline.md for destination rules."* Line 19: *"Verify before done — see review-protocol.md Definition of Done."* Both are already one-liners referencing canonical sources.

## Finding 45

**ASSUMPTION [MATERIAL] [COST:SMALL]:** The proposal treats all 15 files as equally loaded per session ("Claude-facing files"), but the repository structure shows a `hooks/hook-context-inject.py` and `hooks/hook-intent-router.py` that selectively inject context. If rule files are conditionally loaded (not all 15 per session), then the token-savings math is wrong and the deduplication strategy may be solving the wrong problem. A file that's only loaded in specific contexts *should* restate its rules locally — a cross-reference to a file that isn't loaded is worse than duplication. The proposal never establishes which files are always-loaded vs. conditionally-loaded, which is load-bearing for every Phase 2 decision.

## Finding 46

**ASSUMPTION** [MATERIAL] [COST:SMALL]: The proposal asserts four live contradictions, but tool verification shows at least three are **already resolved** in the current rule files:
   - **1B (orient list):** workflow.md line 7 already reads "read `docs/project-prd.md` (if filled in) + `docs/current-state.md` + `tasks/lessons.md` + `tasks/session-log.md`" — it does **not** reference `project-map.md` (substring not found) as the proposal quotes.
   - **1C (skip conditions):** review-protocol.md line 26 already says "Skip conditions: Defined authoritatively in CLAUDE.md. Do not maintain a separate list here." The proposed fix is already in place.
   - **1D (essential eight):** review-protocol.md line 74 already reads "The essential eight invariants (6 applicable to BuildOS — see CLAUDE.md for applicability) guide every change." This is almost verbatim the proposed fix.
   - **1A (document before/after):** session-discipline.md line 9 says "Persist corrections and decisions after deciding on them and before implementing them." The "BEFORE implementation" caps phrasing the proposal quotes does not appear in the rules directory (substring not found).
   
   EVIDENCED: 4/4 quoted contradictions in Phase 1 do not match current file contents as retrieved. The proposal appears to be written against a stale snapshot of the repo.

## Finding 47

**OVER-ENGINEERED [ADVISORY]:** Phase 2's cross-reference strategy introduces a new maintenance invariant: "when you update the canonical file, you must remember which files reference it." The proposal doesn't address how this invariant is enforced. The current duplication, while wasteful, is at least self-contained — each file is independently correct. Cross-references create a dependency graph that can silently break (canonical file updated, reference file not updated, Claude gets inconsistent instructions again). The proposal trades one failure mode for another without acknowledging the tradeoff.

## Finding 48

[ALTERNATIVE] [ADVISORY]: Instead of forcing cross-references for everything, a "tiered context" approach might work better: keep critical invariants (like security boundaries and plan gates) fully expanded in the always-loaded `CLAUDE.md`, while offloading only deep-dive domain specifics (like bash diagnostic steps) to supplementary files.

## Finding 49

**ASSUMPTION [MATERIAL] [COST:TRIVIAL]**: The proposal asserts "Origin:" tags exist in `code-quality.md`, `bash-failures.md`, `code-quality-detail.md`, and `skill-authoring.md` (Phase 3A, ~50 tokens). Tool verification found **zero matches** for "Origin:" across all rule files and docs. This is a phantom cut — Phase 3A removes nothing because the content doesn't exist. This undermines confidence in the token recovery estimate.

## Finding 50

**ALTERNATIVE [ADVISORY]:** The proposal never considers a **linting/validation approach** as an alternative to manual deduplication — e.g., a script that detects when the same rule appears in multiple files and flags it, without restructuring the files. This would address the maintenance problem (new duplications accumulating) without creating reference dependencies. Given that the repo already has `scripts/lint_skills.py`, `hook-skill-lint.py`, and a `hook-spec-status-check.py`, the infrastructure for automated governance checks exists. A duplication-detector would be more durable than a one-time editorial pass.

## Finding 51

**ASSUMPTION [ADVISORY]**: The proposal claims ~12,810 total tokens across 15 Claude-facing files and ~1,200-1,500 tokens recoverable (~10-12%). These figures are SPECULATIVE — no token-counting methodology is cited, no per-file breakdown is provided, and the tool calls confirm the rule files exist but cannot verify their current sizes. The 10-12% recovery estimate cannot be validated from the proposal alone.

## Finding 52

**ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 2D claims workflow.md contains a full tier table and review-protocol.md contains "Typical paths by change type." Actual workflow.md line 9: *"Pipeline tiers: see CLAUDE.md. Skip conditions for `/challenge`: defined authoritatively in CLAUDE.md."* Actual review-protocol.md line 60: *"Tier definitions and full pipeline routes: see CLAUDE.md."* Both cuts already done.

## Finding 53

[ASSUMPTION] [MATERIAL] [COST:SMALL]: Phase 1D misstates current governance: the codebase no longer appears to enforce the proposal’s “6 of 8 apply” framing as the live rule source. `docs/hooks.md` describes `.claude/rules/` as the authoritative rule layer above hooks (line 3), and the actual loaded `.claude/rules/review-protocol.md` in the repo does not contain the claimed contradictory “essential eight invariants apply to every change” text in its first 97 lines. Without verifying CLAUDE.md content, this proposal over-anchors on a contradiction that may already be resolved or may exist only in a different doc layer. As written, it treats an unverified premise as a core ambiguity.

## Finding 54

**ASSUMPTION [MATERIAL] [COST:SMALL]**: Several specific contradictions cited in Phase 1 are not verified by the tool calls. Specifically:
   - `check_code_presence("Update decisions.md after material decisions")` → **not found** (0 matches). The "after" wording in CLAUDE.md that 1A proposes to fix may not exist in the current files.
   - `check_code_presence("Every correction must be persisted")` → **not found** (0 matches). The session-discipline.md "BEFORE implementation" wording cited in 1A may not exist.
   - `check_code_presence("6 of 8")` → **not found** (0 matches). The CLAUDE.md "6 of 8 apply" phrasing cited in 1D may not exist verbatim.
   - `check_code_presence("approval gating")` → **not found** (0 matches). The strikethrough items cited in 1D may not exist.
   - `check_code_presence("skip both for")` → **not found** (0 matches). The CLAUDE.md skip-condition wording cited in 1C may not exist verbatim.
   - `check_code_presence("skip-challenge")` → **not found** (0 matches). The review-protocol.md `/plan --skip-challenge` cited in 1C may not exist.
   
   The proposal is built on specific textual contradictions that cannot be confirmed to exist in the current rule files. If the contradictions don't exist as described, Phase 1 fixes are solving phantom problems — or worse, introducing new inconsistencies. **Before any edits, the actual current text of each affected file must be read and the contradictions confirmed.**

## Finding 55

[ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The proposal claims “BuildOS rule files (CLAUDE.md + 10 rule files + 4 reference files)” and targets `.claude/rules/reference/*.md`, but the repository manifest shows no `.claude/rules/reference/` directory at all. The nearest referenced material is `docs/reference/code-quality-detail.md` from `.claude/rules/code-quality.md` line 50, so the stated surface area is factually wrong and the token-savings estimate is built on an incorrect file set.

## Finding 56

**ASSUMPTION [MATERIAL] [COST:SMALL]**: The proposal's central quantitative claim — "~12,810 tokens across 15 Claude-facing files, ~1,200-1,500 tokens recoverable (~10-12%)" — is SPECULATIVE. No token counts are shown per file, no methodology is given for the estimate, and the proposal doesn't demonstrate that the identified cuts actually sum to 1,200-1,500 tokens. The tool calls confirm the files exist and have the stated content, but the token arithmetic is unverified. If the actual recovery is 300-400 tokens (plausible given the actual file sizes observed — e.g., `review-protocol.md` is 97 lines, `workflow.md` is 70 lines), the ROI case weakens substantially. The proposal should show a per-file token count before claiming a 10-12% recovery.

## Finding 57

**RISK** [MATERIAL] [COST:TRIVIAL]: The token-savings estimate ("~1,200-1,500 tokens, ~10-12%") is built on line counts of text that largely no longer exists in the canonical form the proposal describes. ESTIMATED: actual realized savings are likely a fraction of the claimed figure — perhaps 300-500 tokens from the Phase 3 tightening steps that do have real targets (compaction protocol, Root Cause First in workflow.md, orchestration.md tightening, security.md allowlist/CSV formulas) once those are re-verified against current file contents. SPECULATIVE on exact numbers, but directionally: the ROI case collapses if most Phase 1 and Phase 2 edits are no-ops.

## Finding 58

**ALTERNATIVE [MATERIAL] [COST:SMALL]:** The proposal frames the choice as "deduplicate via cross-references" vs. "status quo." A missing candidate is **consolidation into fewer files** rather than cross-referencing between many files. If duplication is the problem, merging session-discipline.md + workflow.md into a single `execution.md` eliminates the cross-reference maintenance problem entirely and produces a smaller always-loaded surface. Cross-references between files that may or may not be loaded is a weaker solution than reducing file count.

## Finding 59

**RISK [MATERIAL] [COST:SMALL]**: Because the proposal's quoted "current state" is stale or fabricated in many places, applying its edits as-written risks *regressing* already-canonicalized pointers (e.g., rewriting review-protocol.md line 74 from the correct "(6 applicable to BuildOS…)" to the proposed wording could drop "for applicability" nuance, or re-introduce deleted text if an editor takes the proposal's `Current state` quote as authoritative). A revise pass must reread the files line-numbered before any edit.

## Finding 60

**ASSUMPTION** [MATERIAL] [COST:SMALL]: Phase 3A targets "Origin:" tags in code-quality.md, bash-failures.md, code-quality-detail.md, skill-authoring.md. Substring search across the rules directory returns zero matches for "Origin" or "Origin:". Phase 3B targets "Watch for these anti-patterns" and "Don't wait for the user to ask" — both return zero matches. These deletions would be no-ops. SPECULATIVE: a previous cleanup may have removed them already; either way the proposal's premise is stale.

## Finding 61

**ALTERNATIVE [MATERIAL] [COST:SMALL]:** The candidate set is binary: either (A) deduplicate by cross-referencing, or (B) status quo. A missing option is **single-source consolidation** — move all rules into CLAUDE.md (or one canonical file) and eliminate the satellite files entirely for the duplicated sections, rather than creating a web of "see X" pointers. Cross-references add a new failure mode (stale pointer, file not in context) that the current duplication doesn't have. Duplication is robust to partial context; references are not. The proposal never considers whether the reference graph it's creating is more fragile than the duplication it's replacing.

## Finding 62

**RISK [MATERIAL] [COST:MEDIUM]:** Fix 1A ("document before or after implementation") changes the semantics of when decisions.md is updated. The proposal asserts CLAUDE.md's "after" is "the outlier" and should be changed to "before," but doesn't verify whether the current "after" behavior is intentional — perhaps decisions.md is updated *after* because the decision isn't final until implementation confirms it's viable. Changing this without understanding why the divergence exists could introduce a new behavioral error (Claude documents a decision it then reverses, leaving a stale record). The proposal treats this as a simple typo fix when it may be a deliberate design choice.

---

## Finding 63

**ASSUMPTION [ADVISORY]:** The claim that "instruction compliance decreases as instruction count grows" is cited as research motivation but no source is given. This is SPECULATIVE as stated. More importantly, it conflates *total token count* with *instruction count* — the proposal's fixes reduce tokens but may not reduce the number of distinct directives Claude must track. Replacing 6 lines with "see code-quality.md" doesn't reduce instruction count; it adds an indirection step.

## Finding 64

**ASSUMPTION [MATERIAL] [COST:TRIVIAL to withdraw]**: Phase 1C claims review-protocol.md restates skip conditions. The actual file (line 26) already says: *"Defined authoritatively in CLAUDE.md. Do not maintain a separate list here."* Already canonicalized.

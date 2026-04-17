---
debate_id: buildos-improvements-findings
created: 2026-04-16T21:33:08-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# buildos-improvements-findings — Challenger Reviews

## Challenger A — Challenges


## Challenges

1. **RISK** [MATERIAL] [COST:SMALL]: **Change #1's PostToolUse:Write|Edit hook type doesn't exist in the current codebase.** I verified that neither `PostToolUse:Write` nor `PostToolUse:Edit` appear anywhere in hooks or config. The existing PostToolUse hooks (8 matches) use generic `PostToolUse` and then filter on tool name internally (e.g., `hook-post-tool-test.sh` reads the input JSON to check the file path). The proposal assumes a granular hook event type that Claude Code may not emit. If the platform only fires `PostToolUse` generically, the hook needs to parse the tool input to distinguish writes from reads — feasible but changes the implementation shape. The proposal's "~60 lines" estimate (SPECULATIVE) may undercount if it needs to handle the JSON parsing and filtering that `hook-post-tool-test.sh` already demonstrates.

2. **ASSUMPTION** [MATERIAL] [COST:SMALL]: **Change #1's edit counter assumes a reliable signal for "build activity."** The intent router already has a review-proactive path (lines 504-506) that fires when `has_plan=True + uncommitted changes + no review artifact`. This was documented as the L25 failure — it fires once, gets suppressed by `already_suggested()`, and doesn't fire again. The proposed counter-based hook has the same suppression risk: once the threshold fires and the suggestion is injected, if the user ignores it, the counter either keeps firing every edit (annoying) or gets suppressed (same failure). The proposal doesn't specify the re-fire policy. This is the core design question for #1 and it's unaddressed.

3. **RISK** [ADVISORY]: **Change #3's dismissed-finding feedback loop has no existing infrastructure to build on.** `review-log.jsonl` doesn't exist yet (verified: no `review-log` references in scripts or skills). `finding_tracker.py` exists and tracks findings through `open → addressed | waived | obsolete`, but it operates on debate findings imported from judge output, not review findings. The proposal's `review_feedback.py` would need to either extend `finding_tracker.py`'s schema or create a parallel tracking system. The proposal says "one JSONL store and one script" but the integration surface with `cmd_review` in `debate.py` (which generates review findings) is non-trivial — `cmd_review` would need to emit structured finding IDs, and the dismiss flow needs a UI surface.

4. **ALTERNATIVE** [MATERIAL] [COST:TRIVIAL]: **Change #1 could be simpler: make the existing intent-router review suggestion non-suppressible.** Lines 504-510 of `hook-intent-router.py` already detect the exact condition (plan exists + dirty tree + no review). The `already_suggested()` guard prevents re-fire. Removing or weakening that guard for the `review-proactive` key — e.g., allowing it to re-fire every N prompts instead of once-per-session — would close L25 with a 5-line change instead of a new hook file. The proposal doesn't explain why a new PostToolUse hook is better than fixing the existing UserPromptSubmit hook that already detects the right state.

5. **UNDER-ENGINEERED** [ADVISORY]: **Change #2 says "prune hooks whose (fire_rate × block_rate) falls below a threshold" but this metric is wrong for advisory hooks.** Many hooks (intent-router, context-inject, session-telemetry) fire on every prompt and never "block" — they inject context. Their `block_rate` is 0 by design. The metric needs to distinguish enforcement hooks (where block_rate matters) from advisory/injection hooks (where value is measured differently). The telemetry plan may already handle this, but the pruning criterion as stated would incorrectly flag high-value advisory hooks for removal.

6. **OVER-ENGINEERED** [ADVISORY]: **Change #7 (model-tier-aware hook activation) is correctly flagged as speculative, but its inclusion in a "seven changes" bundle creates scope creep pressure.** The proposal already says "hold separately" — it should be removed from the numbered list entirely. A 7-item proposal with one explicitly held item is a 6-item proposal with a footnote.

7. **RISK** [ADVISORY]: **Change #4 (tiered install) has no test coverage path.** The current `/setup` skill has no test file in the manifest. Splitting templates into three tiers introduces a combinatorial surface (3 tiers × N template files) with no automated verification that each tier's file set is correct and complete. Given L36's finding that refactors are safe when the test suite is fast, this change should ship with a test.

8. **ASSUMPTION** [ADVISORY]: **The "2 weeks of telemetry then prune" timeline in #2 assumes sufficient session volume.** The proposal states this is primarily a single-developer framework with one external pilot. Two weeks of single-developer sessions may not produce statistically meaningful fire_rate distributions for 21 hooks. The proposal should define a minimum session count (not calendar time) as the pruning gate.

## Concessions

1. **The prioritization is correct.** #1 and #2 as the "simplest version" is well-reasoned — #1 closes the most-documented failure, #2 generates evidence for everything else. The proposal's own "even smaller version: just #1" shows good instinct for incremental delivery.

2. **The non-goals are load-bearing.** Explicitly ruling out debate.py rewrites, new skills, multi-player, and store format changes prevents the most likely scope explosions. This is a calibration pass, not a redesign, and the proposal stays disciplined about that.

3. **The operational evidence section is unusually honest.** Documenting that review-after-build rate, hook fire rate, and finding dismissal rate are all unmeasured — and that this unmeasured state is itself the problem — is the right framing. Most proposals would claim the metrics support the change; this one correctly identifies the absence of metrics as the motivation.

## Verdict

**REVISE** — The core proposal is sound, but Change #1 (the highest-priority item) has an unresolved design question: the re-fire policy after the user ignores the review suggestion. Before building a new PostToolUse hook, the author should evaluate whether fixing the existing intent-router's `already_suggested()` suppression for the `review-proactive` key (a TRIVIAL change) closes L25 adequately. If it doesn't, the new hook's re-fire behavior needs to be specified explicitly. Everything else is either well-scoped (#2, #4, #5) or correctly deferred (#3, #6, #7).

---

## Challenger B — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: Change #3 introduces a new prompt-injection path from low-trust review artifacts into future `/review` prompts. The proposal says dismissed findings from `stores/review-log.jsonl` will be retrieved and injected as negative examples, but it does not define any sanitization, schema validation, or quoting boundary for that content. Because findings originate from model output and later human annotations, they are untrusted input; if stored verbatim, a malicious or malformed finding could smuggle instructions like “ignore security findings” into subsequent review prompts and systematically suppress review quality. Fix by storing structured fields only (category, lens, normalized rationale), capping length, stripping imperative/meta-instructional text, and injecting as quoted data rather than freeform prompt prose.

2. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: Change #1 adds session-scoped state and intent-router consumption, but the trust boundary around that state is not specified. Existing hooks already use predictable `/tmp/claude-…-{session}.json` files in the intent router path, and the proposal’s new “state flag read by the intent router” sounds likely to follow the same pattern. If the new flag is writable by other local processes or guessed session IDs, a lower-trust actor on the same machine could spoof “review completed” or force noisy review suggestions. Use a repo-local state dir with `0700` permissions or securely created temp files, and validate ownership before trusting the flag.

3. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The proposal assumes “10 edits within an active plan” is a safe trigger for non-advisory review nudging, but there is no evidence yet that this threshold correlates with meaningful review boundaries. EVIDENCED: the proposal explicitly says review-after-build rate and hook fire rate are currently unmeasured. As written, this could create alert fatigue and train the user to bypass the mechanism the same way `[TRIVIAL]` bypasses commit-time review today; conversely, setting it too high leaves L25 unfixed. Ship #1 only if the threshold is explicitly provisional, logged, and reviewed against telemetry after rollout.

4. [UNDER-ENGINEERED] [ADVISORY]: Change #2 proposes pruning hooks on `(fire_rate × block_rate)` alone, which is a weak safety metric for security- or trust-boundary hooks. A hook that rarely fires may still protect a high-severity path such as credential leakage or protected-file edits. The risk of changing is removing a low-frequency/high-impact control; the risk of not changing is continued operator overhead. Add severity/coverage class to the pruning rubric so “rare but critical” hooks are not cut on volume grounds alone.

5. [ASSUMPTION] [ADVISORY]: Change #4 is framed as an install-footprint improvement, but it assumes reducing the default surface will not weaken baseline protections for inexperienced users. Given the repo already contains hooks that guard reading before editing and commit-time tests, the concrete risk of not changing is onboarding friction, while the concrete risk of changing is more sessions proceeding without protections that catch common mistakes. Make the security/usability trade explicit in `/setup` and default conservatively for first-time users.

## Concessions
- The proposal correctly prioritizes the risk of not changing: L25 remains structurally unfixed today, and advisory-only routing is a demonstrated failure mode.
- Deferring #7 as speculative is sound; silent false negatives from model-tier-based hook skipping would be expensive and should not be bundled into the first tranche.
- The telemetry-first mindset in #2 is directionally right; the repository already has append-only local telemetry patterns, so this continues an existing architecture rather than introducing an external data-exfiltration dependency.

## Verdict
REVISE — the core direction is good, but #3 needs explicit prompt-injection defenses and #1 needs a securely specified state mechanism before this is safe to implement.

---

## Challenger C — Challenges
## Challenges

1. **[OVER-ENGINEERED] [MATERIAL] [COST:MEDIUM]**: The automated learning loop for `/review` (#3) introduces a dynamic prompt injection system (writing to `stores/review-log.jsonl`, adding a `--dismiss-finding` CLI command, and using `scripts/review_feedback.py` to auto-retrieve negative examples). For a single-developer framework, this is unjustified complexity. The simpler alternative is to manually append the concrete failure as a negative example directly into the relevant rule file in `.claude/rules/`. The proposal already cites L32 stating that "improvements must modify the artifact (the prompt), not runtime context" — an automated retrieval system violates the spirit of that lesson by over-complicating the context assembly.

2. **[UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]**: The heuristic for pruning hooks in #2 (`fire_rate × block_rate`) completely ignores the *severity* or *tier* of the hook's purpose. A hook that guards against major drift or syntax errors might have a very low block rate because the LLM is generally competent, but the cost of the failure passing through is high. Pruning based solely on frequency metrics without an explicit exemption for high-severity structural boundaries risks deleting the framework's safety net.

3. **[ASSUMPTION] [ADVISORY]**: Proposal #1 assumes there is a clean, reliable way to trigger a counter specifically on `PostToolUse:Write|Edit` mid-session without intercepting all CLI I/O. If this relies on polling file `mtime` in the background or parsing shell logs, it may introduce latency or race conditions. 

## Concessions

1. The "Simplest Version" fallback (shipping only #1 and #2 first) is an excellent, pragmatic approach to validating assumptions before committing to the full scope.
2. Deleting the anti-slop word list (#6) correctly identifies that the cost of false positives on legitimate technical writing outweighs the minor benefit of catching stylistic tics.
3. Right-sizing the Tier 0 install footprint (#4) directly addresses the adoption friction for new users (like Scott) without removing capabilities for the primary author.

## Verdict

REVISE. The prioritization of #1 and #2 is correct, but change #3 introduces unjustified architectural complexity for a single user, and the pruning heuristic in #2 requires a severity/criticality override before execution.

---

---
debate_id: buildos-agent-gaps-debate
created: 2026-04-05T14:57:28-0700
mapping:
  A: gemini-3.1-pro
  B: gpt-5.4
  C: claude-opus-4-6
---
# buildos-agent-gaps-debate — Challenger Reviews

## Challenger A — Challenges
## Challenges

1. **[RISK] [MATERIAL]: Documenting hallucinated features violates D115**
The proposal treats Claude Desktop's claims about `TeammateIdle`, `/plugin`, and `~/.claude/agent-memory/` as items needing verification, but Decision D115 (2026-04-02) already explicitly quarantined these exact claims as unverified/hallucinated. Investigating or documenting them wastes time and risks polluting the framework with fake features.

2. **[ASSUMPTION] [MATERIAL]: Gap 1 is "Completely Absent"**
The author's initial assessment agrees that Gap 1 (custom subagent definitions in `.claude/agents/`) is "Likely real and worth documenting." This is demonstrably false. Appendix A2 (`docs/platform-features.md §7`) explicitly documents `.claude/agents/`, provides a YAML example, and explains tool restrictions, model overrides, and worktree isolation. 

3. **[ALTERNATIVE] [ADVISORY]: Review Swarm vs. Debate.py**
Gap 6 suggests replacing `debate.py` with parallel subagents. However, D79 established Debate system v2 with an independent judge. Subagents cannot communicate with each other (as stated in `docs/team-playbook.md`), making them structurally unsuited for a debate format where personas must respond to each other's arguments.

4. **[OVER-ENGINEERED] [ADVISORY]: Treating all 10 gaps as equal weight**
The proposal correctly notes that the grading critique is flawed ("grades everything absent as 'F' regardless of importance"), but still structures the analysis around all 10 gaps. Gaps 7, 8, and 9 are either hallucinations or irrelevant to the core BuildOS mission of safe, parallel agent orchestration.

## Concessions
1. Correctly identifies that the grading system used by Claude Desktop is flawed and lacks prioritization.
2. Correctly flags Gap 6 (Review Swarm) as having questionable priority compared to the existing cross-model debate approach.
3. Accurately recognizes that documenting non-existent features is the most dangerous outcome.

## Verdict
**REVISE** to immediately discard the hallucinated features already quarantined in D115, strike Gap 1 as it is already documented, and focus solely on verifying and prioritizing the remaining potentially real operational controls (like headless mode and background tasks).

---

## Challenger B — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL]: The proposal’s “likely real” items rely on human recollection rather than verified product evidence, but the stated primary risk is documenting non-existent features. Gap 2 (“built-in subagents”), Gap 3 (“background agents” with Ctrl+B and /tasks), and Gap 8 (“claude -p”) are not evidenced in the provided BuildOS docs or governance appendix. Given D115 explicitly records prior unverified Claude Desktop claims, treating these as likely real without vendor/source verification crosses the trust boundary from trusted project docs into untrusted model assertions.

2. [RISK] [MATERIAL]: Gap 4 and Gap 5 bundle many feature claims together, which creates an injection path for hallucinations into framework docs if accepted piecemeal without per-claim verification. The appendix directly falsifies at least one claim: `TeammateIdle` is not listed as a hook event, while `SubagentStart` is. That makes the burden of proof higher for the other bundled claims (direct teammate messaging, task list mechanics, per-subagent hooks, `~/.claude/agent-memory/`, etc.) before any documentation work proceeds.

3. [RISK] [MATERIAL]: Gap 7 and Gap 9 are especially dangerous to document because they describe command surfaces (`/loop`, `/schedule`, `/plugin`, Channels) that, if wrong, would cause users to execute unsupported commands and erode trust in the framework. There is no evidence in the provided material that these are native Claude Code features, and D115 already flags similar claims as previously unverified. These should remain quarantined unless verified from authoritative product docs.

4. [ASSUMPTION] [MATERIAL]: Gap 10’s “project tree is stale because it omits `.claude/agents/`” assumes the docs are intended to mirror a concrete repository tree rather than present an illustrative or minimal tree. The supplied docs already document `.claude/agents/` in both `team-playbook.md` and `platform-features.md`, so even if a tree omits it, that is a presentation nit, not evidence of an operational documentation gap.

5. [ALTERNATIVE] [MATERIAL]: The review should separate two questions that are currently blurred: “feature exists” vs. “feature deserves framework-level documentation.” Gap 6 is the clearest example. Even if subagent-based parallel review is possible, the risk of changing away from `debate.py` is non-trivial: reduced model-family diversity could weaken independent review, and added orchestration complexity could increase token cost and failure modes. The risk of not changing is smaller: current review already works via cross-model debate. So this should be framed as an optional experiment, not a documentation gap.

6. [UNDER-ENGINEERED] [MATERIAL]: The proposal lacks an explicit verification standard for accepting or rejecting each claimed gap. Given the known hallucination risk, each claim should require: authoritative source, exact feature name/surface, stability status, and whether BuildOS already covers the user need through another mechanism. Without that rubric, the team may still import speculative platform details into trusted docs.

7. [RISK] [ADVISORY]: The “graded operational layer as mostly F across the board” framing overstates the risk of not changing. The current docs already cover several operational controls: subagents, `.claude/agents/`, tool restrictions, model override, worktree isolation, hooks, decomposition gates, and agent isolation. Overstating absence could push unnecessary doc churn and increase the chance of introducing inaccurate platform claims.

## Concessions
- The proposal correctly identifies the core security/documentation risk: false platform claims are worse than omitted optional features.
- The appendix provides enough trusted evidence to dismiss at least some claims, especially `TeammateIdle` and the assertion that `.claude/agents/` is completely absent.
- The priority critique is sound: missing support for custom agents is more material than minor tree staleness or speculative plugin ecosystems.

## Verdict
REVISE — the review direction is good, but several “likely real” claims are still unverified, and the proposal needs a stricter evidence rubric before any gap is accepted into trusted framework docs.

---

## Challenger C — Challenges
Now I have a clear picture. Let me render the review.

---

## Challenges

1. **ASSUMPTION [MATERIAL]:** The gap analysis claims `.claude/agents/` is "Completely Absent" from BuildOS docs — this is factually wrong. The provided Appendix A2 shows `docs/platform-features.md §7` documents custom subagents with a YAML example, tool restrictions, model override, worktree isolation, and skills access. The team-playbook.md §2 explicitly references `.claude/agents/` and links to Platform Features. Gap 1 is a false finding. Grading it "F" when it's already documented (with a concrete YAML example) undermines the credibility of the entire analysis.

2. **RISK [MATERIAL]:** At least 4 of the 10 claimed gaps reference features with no evidence of existence in this codebase. Specifically:
   - **TeammateIdle hook** (Gap 4): Not in the hooks table (Appendix A3 lists 8 hook events; TeammateIdle is absent). Not found in scripts.
   - **`~/.claude/agent-memory/`** (Gap 5): Not found in config or anywhere in the codebase.
   - **`/plugin` system** (Gap 9): Not found in skills or config. The author's own assessment flags this as "likely hallucinated" — I agree.
   - **`/loop` and `/schedule` as native features** (Gap 7): Not found in skills or config.
   
   This is exactly the failure mode D115 already quarantined. Acting on this analysis without verification would mean documenting phantom features — the single worst outcome the proposal itself identifies.

3. **OVER-ENGINEERED [MATERIAL]:** The gap analysis proposes documenting a "review swarm" pattern (Gap 6) using parallel read-only subagents for review personas. The current debate.py system already uses genuinely different model families (Gemini 3.1 Pro for architect/staff, GPT-5.4 for security, Claude Opus for PM — confirmed via `persona_model_map`). Replacing cross-model diversity with same-model subagents would *reduce* review quality by eliminating the independent reasoning that different model architectures provide. This isn't a gap — it's a suggestion to regress.

4. **ASSUMPTION [MATERIAL]:** The "F" grading methodology is intellectually dishonest. It treats "not mentioned" as equivalent to "critically missing" regardless of whether the feature (a) exists, (b) is stable, or (c) matters to the audience. A framework doc that correctly documents the features it covers and omits unstable/unverified ones is doing its job. Grading it "F" for not documenting `/plugin` (which likely doesn't exist) is not a gap analysis — it's a hallucination audit failure.

5. **UNDER-ENGINEERED [ADVISORY]:** Despite the noise, there are 2-3 legitimate documentation improvements buried in here. Gap 8 (headless mode / `claude -p`) is a real feature not mentioned in the docs. Gap 3 (background subagents) may be real. Gap 4's mention of display modes (tmux/iTerm2 split panes) for agent teams is plausible operational guidance. These are worth investigating but should be verified against actual Claude Code release notes before documenting.

6. **ALTERNATIVE [ADVISORY]:** Rather than working through this 10-point list (which is ~60% noise), the more productive path is: (a) check Claude Code's actual changelog/docs for features added since the last BuildOS doc update (2 commits ago per recent history), (b) document only what's verified and stable, (c) ignore everything else. This avoids the trap of treating an LLM's feature wishlist as a requirements document.

7. **RISK [ADVISORY]:** The proposal notes hooks `hook-agent-isolation.py` and `hook-decompose-gate.py` are referenced in README.md documentation, but neither function exists in the scripts file set. This could mean they're in a different location, or the README is documenting aspirational hooks. Either way, this is a real doc-code consistency issue that the gap analysis completely missed — suggesting it was pattern-matching on feature names rather than doing actual verification.

## Concessions

1. **The proposal's own skepticism is well-calibrated.** The author's "Skeptical — needs verification" bucket correctly flags almost exactly the items I found to be unverifiable. D115's quarantine decision was the right call and this review confirms it.

2. **The framing question is exactly right.** "The most dangerous outcome is documenting features that don't exist" is the correct threat model for reviewing LLM-generated gap analyses. This proposal demonstrates good institutional awareness of hallucination risk.

3. **Gaps 2, 3, and 8 are plausibly real and worth a small investigation spike.** Built-in subagents (Explore, Plan), background execution, and headless mode are known Claude Code capabilities. If verified, they'd be genuinely useful additions to the docs — particularly headless mode for CI/CD users.

## Verdict

**REVISE** — The gap analysis is ~40% valid signal buried in ~60% hallucinated or already-documented noise. The proposal should be revised to: (1) close Gap 1 as a false finding (already documented in platform-features.md §7 and team-playbook.md §2), (2) permanently reject Gaps 5/7/9 per D115 quarantine, (3) reject Gap 6 as a regression from the current cross-model debate architecture, and (4) scope a small verification spike for Gaps 2/3/8 only, gated on confirmation against actual Claude Code documentation before any BuildOS doc changes are made.

---

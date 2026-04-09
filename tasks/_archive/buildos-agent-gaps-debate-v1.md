---
debate_id: buildos-agent-gaps-debate
created: 2026-04-02T11:45:47-0700
mapping:
  A: gemini-3.1-pro
  B: gpt-5.4
  C: gemini-3.1-pro
---
# buildos-agent-gaps-debate — Challenger Reviews

## Challenger A — Challenges
## Challenges

1. [RISK] [MATERIAL]: Hallucinated platform features. Gaps 3 (Background Subagents with Ctrl+B/`/tasks`), 4 (TeammateIdle hook, native tmux splits), 5 (`~/.claude/agent-memory/`), 7 (`/loop`, `/schedule`, Channels), and 9 (`/plugin` ecosystem) describe features that do not exist in Claude Code. Documenting these will destroy the framework's credibility and cause immediate user failure.
2. [ASSUMPTION] [MATERIAL]: False premise on existing documentation. Gap 1 claims custom subagent definitions (`.claude/agents/`) are "completely absent," but Appendix A2 (`docs/platform-features.md` §7) explicitly documents this exact feature, including the YAML schema, tool restrictions, and model overrides.
3. [OVER-ENGINEERED] [ADVISORY]: Gap 6 (Review Swarm) suggests replacing the sequential cross-model `debate.py` pattern with parallel read-only subagents. This introduces coordination overhead and context duplication for a task (review) that is inherently sequential and consensus-driven, likely degrading review quality while increasing token costs.

## Concessions
1. The author correctly identifies that the documentation leans heavily on strategic doctrine (when/why) rather than tactical execution (exactly what commands to type).
2. Gap 8 (Headless/Programmatic mode) is a valid operational gap, as running `claude -p` or piping inputs is critical for CI/CD integrations and is currently under-documented.
3. Gap 10 (Stale project tree) is a valid, if minor, housekeeping catch.

## Verdict
REJECT because the analysis is heavily contaminated with hallucinated Claude Code features and misses existing documentation, making it unsafe to use as a roadmap for updates.

---

## Challenger B — Challenges
## Challenges
1. [RISK] [MATERIAL]: The biggest security/documentation risk here is feature hallucination leading to unsafe or broken guidance. Several claimed gaps reference capabilities not evidenced in the supplied docs and, in at least one case, directly conflict with them: `TeammateIdle` is not a listed hook event, while the documented hook surface includes `SubagentStart` instead. Claims about `/plugin`, `/loop`, `/schedule`, Channels, direct teammate messaging, tmux/iTerm2 pane controls, and `~/.claude/agent-memory/` are unverified from the provided corpus and should not be incorporated without product-source verification.

2. [ASSUMPTION] [MATERIAL]: Gap 1 is overstated. The proposal frames custom subagent definitions in `.claude/agents/` as “completely absent,” but the current docs already mention them in two places: `docs/team-playbook.md` explicitly says Claude Code supports custom subagent definitions in `.claude/agents/`, and `docs/platform-features.md` §7 provides a concrete YAML example plus tool restrictions, model override, worktree isolation, and skills access. That materially changes the recommendation: this is not an absence problem, at most a depth/operational-example problem.

3. [ASSUMPTION] [MATERIAL]: Gap 4 bundles real and speculative controls together without separating trust levels. The docs already cover some operational controls indirectly through governance hooks (`hook-agent-isolation.py`, decomposition gating, worktree isolation) and explicitly distinguish subagents from agent teams. But the claim adds unverified operational features—plan approval for teammates, direct teammate messaging mechanics, shutdown/cleanup protocol semantics, and `TeammateIdle`—without evidence. Treating that whole cluster as a single “thin coverage” gap risks importing nonexistent control surfaces into framework docs.

4. [ASSUMPTION] [MATERIAL]: Gap 5 similarly mixes documented and undocumented subagent properties. Documented: tool restrictions, model override, worktree isolation, skills access. Undocumented/unverified from supplied material: scoped MCP servers, permission modes, persistent memory directory `~/.claude/agent-memory/`, preloaded skills beyond ordinary skills access, and per-subagent hooks in frontmatter. The analysis should be split so only verified capabilities are candidates for framework docs.

5. [ALTERNATIVE] [MATERIAL]: The right remediation is not “document all operational features Claude Desktop named,” but “reframe the docs around verified stable primitives.” Concretely: document the operational surfaces already evidenced here—`.claude/agents/` schema examples, when to use subagents vs agent teams, worktree isolation, `SubagentStart` hook relevance, and headless mode only if separately verified. This reduces injection of false platform claims and keeps trust boundaries clear between BuildOS abstractions and upstream product behavior.

6. [UNDER-ENGINEERED] [ADVISORY]: The current evaluation rubric is too binary. Rating missing items as “F” regardless of impact ignores security and usability priority. Framework docs should prioritize features that, if misunderstood, create unsafe execution or privilege-boundary failures: write-capable agent isolation, hook enforcement, file ownership boundaries, and context non-inheritance. Cosmetic or low-frequency features should rank lower even if real.

7. [ALTERNATIVE] [ADVISORY]: Gap 6 (“review swarm”) should not be treated as a documentation gap by default. Sequential `debate.py` across model families may preserve stronger independence and reduce correlated failure compared with parallel subagents sharing one product/runtime. For adversarial review, independence across trust domains is often preferable to same-system parallelism. This is a workflow design choice, not clearly a missing platform-doc issue.

8. [ASSUMPTION] [ADVISORY]: Gap 10 (“project tree is stale”) is minor unless the annotated tree is presented as normative configuration guidance. Missing `.claude/agents/` from a tree view is only worth fixing if it misleads users about required repository structure; otherwise it should not drive roadmap priority.

## Concessions
- The proposal correctly identifies the primary failure mode: documenting nonexistent Claude Code features would degrade the framework more than leaving some advanced features undocumented.
- The supplied BuildOS docs already do a good job on trust-boundary-relevant operational guidance: subagents vs agent teams, prompt context non-inheritance, worktree isolation, and governance hooks.
- The author’s skepticism is well placed: `/plugin` is likely hallucinated, and `TeammateIdle` is directly unsupported by the provided hook reference.

## Verdict
REVISE — the cross-model review should explicitly separate verified features from speculative ones, because several claimed “gaps” are either already documented or insufficiently evidenced to safely include.

---

## Challenger C — Challenges
## Challenges

1. [RISK] [MATERIAL]: The gap analysis is heavily contaminated with hallucinations of features that do not exist in Claude Code. Gaps 2 (Explore/Plan subagents), 3 (Ctrl+B backgrounding and `/tasks`), 4 (`TeammateIdle` hook, tmux pane management), 5 (`~/.claude/agent-memory/`), 7 (`/loop`, `/schedule`), and 9 (`/plugin` ecosystem) appear to be conflations with other agent frameworks (like LangChain or AutoGPT). Documenting these would destroy the framework's credibility and severely confuse users.

2. [ASSUMPTION] [MATERIAL]: Gap 1 claims that custom subagent definitions (`.claude/agents/`) are "completely absent." This is demonstrably false based on the provided text. Appendix A2 (`docs/platform-features.md §7`) explicitly documents this directory, provides a YAML example, and lists capabilities like tool restrictions and worktree isolation. 

3. [OVER-ENGINEERED] [ADVISORY]: Gap 6 recommends replacing the existing `debate.py` cross-model review pattern with a "Review Swarm" of parallel subagents. Since subagents run within the same model family context, this removes the cognitive diversity of using different models (e.g., Claude vs. GPT-4o) for review, adding orchestration complexity for a worse architectural outcome.

4. [ASSUMPTION] [MATERIAL]: The grading methodology is fundamentally flawed. Assigning an "F" for failing to document non-existent features, or treating the omission of edge-case CLI flags (like `claude -p`) with the same severity as core workflow documentation, demonstrates a lack of product prioritization.

## Concessions
1. Gap 8 correctly identifies that headless/programmatic execution (`claude -p`) is a real feature that could be useful for CI/CD integration.
2. Gap 10 is a valid, albeit minor, housekeeping observation if the project tree in the docs is indeed missing newly established directories.
3. The author's initial skepticism was entirely justified and correctly identified the risk of hallucinated features.

## Verdict
REJECT because the gap analysis is predominantly based on hallucinated platform features that would mislead users and degrade the documentation's accuracy.

---

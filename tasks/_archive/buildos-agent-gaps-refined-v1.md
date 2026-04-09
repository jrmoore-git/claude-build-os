---
debate_id: buildos-agent-gaps
created: 2026-04-02T11:48:31-0700
phase: refine
rounds: 3
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: yes
---
# buildos-agent-gaps — Refined Document

## Round 1 (gemini-3.1-pro)
The original proposal correctly identified that Claude Desktop's gap analysis needed critical review, but it didn't go far enough in filtering out AI hallucinations. The most significant improvement in this revision is the introduction of a strict verification gate. Many of the features Claude Desktop claimed were missing (like `TeammateIdle`, `/plugin`, or `~/.claude/agent-memory/`) simply do not exist in the provided product documentation and are highly likely to be hallucinations. 

Additionally, the revised document corrects the assessment of Gap 1, Gap 4, and Gap 5. The original analysis claimed `.claude/agents/` was completely undocumented, which is demonstrably false based on existing BuildOS docs. We have split mixed gaps into "verified" vs. "speculative" components and replaced the binary "F" grading system with a nuanced priority-weighting rubric. Finally, the roadmap has been refocused exclusively on verified, stable platform primitives.

## Round 2 (gpt-5.4)
The current revision is a strong improvement over the original gap analysis. It correctly introduces a verification gate, separates verified product behavior from speculative claims, and avoids converting hallucinated features into roadmap commitments. That substantially improves safety and credibility.

Remaining issues and improvements:
- The document is generally clear, but the title and framing still read a bit like a proposal while the body functions more like a validated review and triage memo. Tightening that positioning would improve coherence.
- Several sections use terse labels like “FALSE” or “Hallucinated” appropriately, but the distinction between “already documented,” “verified but under-documented,” and “unverified” can be made more systematic for easier scanning.
- Gap 4 and Gap 5 are correctly split as mixed, but the accepted portions could be stated more concretely so readers know exactly what is and is not being proposed.
- Gap 6 is good, but its status should be framed explicitly as a workflow recommendation rather than a documentation gap in platform capability.
- The roadmap is solid, though it would benefit from slightly clearer prioritization language: what is highest priority vs. optional/future work.
- Minor style issue: “Build OS” and “BuildOS” appear inconsistently. Standardizing on one form improves polish.

## Round 3 (claude-opus-4-6)
The previous revision is a strong, well-structured document. It correctly identifies the core problem (hallucinated features contaminating a gap analysis) and applies a rigorous verification methodology. The writing is clear, the logic is sound, and the roadmap is actionable.

Remaining issues I identified:

1. **Title ambiguity.** "Verified Triage Proposal" undersells what this document actually is — it's both a triage *and* a corrected action plan. The title could be more precise.
2. **Context section buries the lede.** The most important sentence — the verification gate rule — is preceded by two paragraphs of backstory. A reader scanning quickly might miss the governing principle.
3. **Inconsistent depth across the 10 gaps.** Some entries (e.g., Gap 4, Gap 5) are thorough and well-split; others (e.g., Gap 7, Gap 9) are terse. The terse ones are fine given their quarantined status, but Gap 8 (Headless Mode) is verified and important yet gets less treatment than several quarantined items.
4. **"What Actually Remains" section partially duplicates the Roadmap.** Items 1–7 in the narrative list map almost directly to the roadmap's 7 items. This creates redundancy — a reader encounters the same information twice in slightly different form. One of these should be cut or the two should be merged.
5. **Gap 6 (Review Swarm) drops out of the roadmap entirely.** It's correctly reclassified as workflow advice, but then receives no placement in the action plan. If it's worth retaining as advisory guidance, it should appear somewhere in the roadmap, even as a low-priority or "appendix" item.
6. **Minor wording issues.** A few phrases are slightly bureaucratic ("materially benefit," "framework relevance") where plainer language would serve better. The conclusion repeats points already well-established, which slightly weakens the ending.
7. **No explicit quarantine list.** The document repeatedly says claims are "quarantined" but never consolidates them into a single reference list. A reader wanting to know "what exactly is off-limits?" has to re-scan all 10 gaps.

My revision addresses these by: merging the "What Actually Remains" narrative into the Roadmap to eliminate redundancy, adding a consolidated quarantine list, tightening the Context section, giving Gap 8 proportional treatment, placing Gap 6 in the roadmap, and making minor clarity edits throughout.

## Final Refined Document

# BuildOS Agent Parallelization Gap Analysis — Verified Triage and Action Plan

## Governing Principle

**No claimed platform feature may be treated as a documentation gap unless it is supported by authoritative product sources or the provided corpus.**

This rule exists because the original gap analysis is significantly contaminated by hallucinated platform features — capabilities described as native product behavior without support in any authoritative source. Documenting non-existent features damages framework credibility and can create operational and safety risks.

## Background

Claude Desktop produced a 10-point gap analysis arguing that BuildOS documentation is strong on strategic doctrine — when and why to parallelize — but has material gaps in operational guidance for configuring and running agent-based workflows.

A strict verification review found that several claimed gaps depend on fabricated or unverifiable product features. The original analysis also treated nearly every absent item as an "F," regardless of whether the claim was real, important, or relevant.

This document applies the verification gate above, filters the 10 claims into verified and unverified categories, and produces a credible documentation roadmap from what survives.

## Grading and Prioritization Rubric

Gaps that pass verification are evaluated on three axes:

1. **User Impact** — How many BuildOS users would benefit from this documentation?
2. **Failure Severity** — How badly do users fail without this guidance?
3. **Framework Relevance** — Is this appropriate for framework-level documentation, or is it project-specific workflow advice?

Gaps that fail verification are quarantined regardless of their apparent importance.

## The 10 Claimed Gaps — Verified and Corrected

### Gap 1: Custom Subagent Definitions (`.claude/agents/`) — Partially Documented

**Claim:** BuildOS never mentions `.claude/agents/`.

**Verification: False.** Existing documentation (`docs/team-playbook.md` and `docs/platform-features.md`) explicitly mentions this directory, provides a YAML example, and describes tool restrictions, model overrides, worktree isolation, and skills access.

**Corrected Status:** Not a missing primitive. The capability is documented but could benefit from additional operational examples.

---

### Gap 2: Built-in Subagents — Quarantined

**Claim:** Claude Code ships with built-in subagents such as Explore, Plan, or a general-purpose agent.

**Verification: Unverified.** The corpus does not confirm these as native built-in features.

**Corrected Status:** Quarantined pending authoritative confirmation.

---

### Gap 3: Background Subagents — Quarantined

**Claim:** Subagents can run in the background via `Ctrl+B`, with progress tracked through `/tasks`.

**Verification: Unverified.** The corpus contains no evidence for these controls or mechanics.

**Corrected Status:** Quarantined.

---

### Gap 4: Agent Team Operational Controls — Split

**Claim:** Missing display modes, direct messaging, task list mechanics, and `TeammateIdle` hook support.

**Verification: Mixed.**

Verified topics that may need stronger documentation:
- Decomposition gating
- Worktree isolation
- Subagents vs. agent teams
- Dispatch and orchestration enforcement

Unverified or contradictory claims (quarantined):
- `TeammateIdle` hook — conflicts with the verified hooks list, which includes `SubagentStart`, not `TeammateIdle`
- tmux/iTerm split-pane mechanics
- Direct messaging mechanics
- Task-list UI/CLI behavior

**Corrected Status:** Carry forward only verified operational topics. Quarantine speculative controls.

---

### Gap 5: Subagent Capabilities and Restrictions — Split

**Claim:** Subagents support scoped MCP servers, permission modes, persistent memory at `~/.claude/agent-memory/`, and per-subagent hooks.

**Verification: Mixed.**

Already documented:
- Tool restrictions
- Model overrides
- Worktree isolation
- Skills access

Unverified (quarantined):
- Scoped MCP servers
- Persistent memory at `~/.claude/agent-memory/`
- Per-subagent hooks

**Corrected Status:** No action needed for documented features. Unverified capabilities quarantined.

---

### Gap 6: Review Swarm Pattern — Workflow Advice, Not a Platform Gap

**Claim:** Review personas could run in parallel with read-only subagents rather than sequentially via `debate.py`.

**Verification:** This is a workflow design suggestion, not a platform feature claim.

**Corrected Status:** Retain as advisory workflow guidance. Note that cross-model independence via `debate.py` may remain preferable to same-system parallelization for adversarial review scenarios.

---

### Gap 7: Scheduled Tasks and Channels — Quarantined

**Claim:** Claude Code supports `/loop`, `/schedule`, and Channels.

**Verification: Unverified.** These are likely hallucinations or project-specific skills, not confirmed native features.

**Corrected Status:** Quarantined.

---

### Gap 8: Headless / Programmatic Mode — Verified

**Claim:** Claude Code can run headless for CI/CD integration.

**Verification: Verified** as a real primitive. This is a meaningful capability for automation workflows, and BuildOS documentation does not currently cover it in operational depth.

**Corrected Status:** Accepted for roadmap consideration. Priority depends on how many BuildOS users have CI/CD or automation use cases.

---

### Gap 9: Plugin Ecosystem — Quarantined

**Claim:** A `/plugin` system allows installation of pre-built agent configurations.

**Verification: Unverified.** The corpus does not support this claim. It strongly resembles hallucinated product behavior.

**Corrected Status:** Quarantined.

---

### Gap 10: Annotated Project Tree Is Stale — Valid Minor Fix

**Claim:** The project tree should include `.claude/agents/`.

**Verification: Valid.**

**Corrected Status:** Accept as a minor documentation maintenance fix.

---

## Quarantined Claims — Consolidated Reference

The following claims from the original analysis are **not supported by the corpus or authoritative product sources** and must not be documented as platform capabilities without independent verification:

| Claim | Source Gap | Reason |
|---|---|---|
| Built-in subagents (Explore, Plan, etc.) | Gap 2 | No corpus evidence |
| Background subagents via `Ctrl+B` / `/tasks` | Gap 3 | No corpus evidence |
| `TeammateIdle` hook | Gap 4 | Contradicts verified hooks list |
| tmux/iTerm split-pane display modes | Gap 4 | No corpus evidence |
| Direct messaging between agents | Gap 4 | No corpus evidence |
| Task-list UI/CLI behavior | Gap 4 | No corpus evidence |
| Scoped MCP servers per subagent | Gap 5 | No corpus evidence |
| Persistent memory at `~/.claude/agent-memory/` | Gap 5 | No corpus evidence |
| Per-subagent hooks | Gap 5 | No corpus evidence |
| `/loop`, `/schedule`, Channels | Gap 7 | No corpus evidence; likely hallucinated |
| `/plugin` system | Gap 9 | No corpus evidence; likely hallucinated |

If any of these are later confirmed by authoritative sources, they can be removed from quarantine and added to the documentation roadmap.

## Documentation Roadmap

After verification, the original 10 claimed gaps reduce to seven legitimate documentation opportunities. These are ordered by priority.

### High Priority

**1. Clarify subagents vs. agent teams**
*(From Gaps 4, 5)*

This is a real area of user confusion and a core framework-level topic. Documentation should explain when to use single-session subagents vs. multi-session agent teams, and the tradeoffs in coordination, isolation, and oversight. High user impact; high failure severity when misunderstood.

**2. Strengthen worktree isolation guidance**
*(From Gaps 4, 5)*

Worktree isolation is a verified concept that affects correctness and safety in multi-agent workflows. Documentation should cover when to use `isolation: worktree`, how isolation changes execution boundaries, and practical usage of `hook-agent-isolation.py`.

**3. Improve context-management guidance for agent dispatch**
*(New — implicit across multiple gaps)*

Spawned agents do not automatically inherit all useful context and therefore require strong task prompts. Documentation should address what context must be restated, how much task decomposition is enough, and how to avoid ambiguous subagent instructions. This directly affects whether delegated tasks succeed or fail.

### Medium Priority

**4. Expand operational examples for `.claude/agents/`**
*(From Gap 1)*

The primitive is already documented, but additional examples would improve adoption and reduce confusion. Useful additions include: varied tool restriction patterns, model override scenarios, and concrete agent definition walkthroughs.

**5. Document verified hook surfaces in operational workflows**
*(From Gap 4)*

Where hooks are verified — such as `SubagentStart` and decomposition-related controls — they should be documented not only as primitives but as parts of actual operational workflows. Tie examples to real usage patterns rather than listing them abstractly.

**6. Document headless/programmatic mode**
*(From Gap 8)*

This is a verified capability relevant to CI/CD and automation use cases. Priority depends on actual audience demand among BuildOS users. If the target audience includes teams running automated pipelines, this moves to high priority.

### Low Priority

**7. Add advisory guidance on parallel review patterns**
*(From Gap 6)*

The review swarm concept is a legitimate workflow design idea, not a platform feature. It can be included as advisory guidance — for example, a brief note in existing review documentation about when parallel read-only subagents might complement or replace sequential `debate.py` review. This should be clearly framed as a design option, not a platform capability.

**8. Refresh the annotated project tree**
*(From Gap 10)*

Ensure `.claude/agents/` appears in the project tree and related orientation materials. Low-cost maintenance fix.

## Conclusion

The original 10-point gap analysis should not be accepted at face value. After applying a strict verification gate:

- **5 of 10 gaps** were fully or partially quarantined due to unverified platform claims.
- **8 actionable documentation items** survive, focused on verified primitives already present in the corpus.
- **11 specific claims** are quarantined and must not be documented without independent confirmation.

The path forward is to expand operational guidance around what BuildOS already covers — decomposition, isolation, context management, and orchestration — rather than to document capabilities that may not exist.

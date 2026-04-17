---
debate_id: explore-intake-tools-on
created: 2026-04-17T14:51:21-0700
mapping:
  A: claude-opus-4-7
personas:
  A: architect
---
# explore-intake-tools-on — Challenger Reviews

## Challenger A (architect) — Challenges
Confirmed: the explore pipeline uses `{context}` and `{dimensions}` as template placeholders — everything else in the proposed context block would just be text inside the `context_block` string. The new sections (PROBLEM/SITUATION/CONSTRAINTS/THE TENSION/ASSUMPTIONS TO CHALLENGE) are not parsed as discrete fields by any code. Now I have enough to review.

## Challenges

1. **[ASSUMPTION] [MATERIAL] [COST:SMALL]:** The proposal's "How Context Block Maps to Explore Prompts" table implies the prompts selectively consume individual sections (e.g., "ASSUMPTIONS TO CHALLENGE → Direction 3", "THE TENSION → synthesis comparison table"). Verified against `scripts/debate_explore.py`: only `{context}` and `{dimensions}` are template-substituted. Everything else is passed as one opaque blob into `{context}`. Unless `explore-diverge.md` and `explore-synthesis.md` are updated to explicitly reference the new section headers by name (and/or code is added to split them like `DIMENSIONS:` is split today), the new structure is aesthetic — the model receives the whole block for every direction with no guarantee that Direction 3 actually attends to ASSUMPTIONS TO CHALLENGE. The implementation plan lists rewriting `preflight-adaptive.md` and `SKILL.md` but does NOT list updating `config/prompts/explore-diverge.md` or `explore-synthesis.md`. That's the load-bearing gap.

2. **[RISK] [MATERIAL] [COST:TRIVIAL]:** The rollback line says "Revert preflight-adaptive.md to v5, remove preflight-tracks.md." I could not find either file in the `config/` manifest, nor a `config/prompts/` directory, nor any string `preflight` in config or scripts. The `surfaces_affected` header lists `config/prompts/preflight-adaptive.md` as if it exists. Either (a) the file lives somewhere the manifest doesn't enumerate (e.g., `.claude/` or `stores/`), or (b) "v5" is aspirational and no prior version exists to revert to. The proposal should state the actual path and whether a v5 baseline exists to roll back to, or the rollback clause is non-executable.

3. **[OVER-ENGINEERED] [ADVISORY]:** Eight delivery rules + five slots + four-row clarity table + nine composition rules + eight failure modes is a lot of doctrine for a pre-flight intake. Much of it is enforced by LLM instruction-following, which the research section itself notes "decays" (arXiv 2507.11538 cited in the proposal). There's no mechanism described for verifying the LLM actually followed Rule 2 ("reflect before asking") or Rule 5 ("don't solve") in a given session. Given the proposal cites RLHF Righting Reflex as the #1 risk, a textual rule in a prompt is a weak defense — worth acknowledging that this is a soft guarantee, not a structural one.

4. **[UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]:** The context composition step is described as "a 3:1-5:1 compression that extracts, structures, and surfaces implicit intent" — but no component is named as the owner. Who composes? Is it a second LLM call, the intake LLM's final turn, or a deterministic template-fill? The distinction matters for cost, latency, and failure modes. A second LLM compression call means the intake cost roughly doubles; a template-fill can't "resolve contradictions" as claimed. The verification command (`debate.py explore --help`) will not exercise this translation step at all.

5. **[ASSUMPTION] [ADVISORY]:** "200-500 tokens" for the context block is presented as a composition rule derived from context-rot research. The cited research (Chroma, Lost in the Middle) shows degradation on much longer contexts than 500 tokens; the 200-500 number is ESTIMATED — a reasonable heuristic but not directly evidenced. Fine as a target; just don't claim it's load-bearing.

6. **[ALTERNATIVE] [ADVISORY]:** The proposal discards the 5-track fixed-question design on three good grounds, but doesn't consider a hybrid: domain-inferred *question bank bias* rather than domain-inferred *track*. I.e., keep the slot structure, but have the LLM bias its Slot 3/4 candidate selection based on inferred domain. This is arguably what the proposal already implies, but it's worth making explicit — the current framing reads as "tracks bad, slots good" when the real finding is "fixed sequences bad, adaptive selection good."

7. **[RISK] [ADVISORY]:** The proposal measures success via "a real /explore run" (step 6 of the implementation plan). That's a single N=1 eyeball test. Given the proposal rests on claims about divergence quality, a regression comparison against v5 on 3-5 prompts of varying clarity would catch the failure mode where the new structure produces *more polished* intake but *less divergent* downstream directions (possible if the Tension section collapses the space prematurely).

## Concessions

1. **The 2:1 reflection-to-question ratio and "offer a frame, invite correction" are genuine upgrades** over a free-form question bank — both are well-evidenced in the cited MI and elicitation research, and both are implementable in prompt text.
2. **Adaptive question count tied to input clarity** is the right call and directly addresses a real failure in fixed-5 designs; the clarity table is operational.
3. **Separating CONSTRAINTS from SITUATION** in the context block is grounded in the cited research about models under-weighting constraints when mixed with facts — this is a concrete, testable improvement over the current context-as-blob approach.

## Verdict

**REVISE** — The intake-protocol half is sound and well-evidenced; the context-composition half promises section-level prompt consumption that the explore pipeline does not currently implement, and the rollback path references files not visible in the repo manifest. Fix those two gaps (update `explore-diverge.md`/`explore-synthesis.md` to reference the new sections by name, and confirm/state the actual path + baseline of `preflight-adaptive.md`) and this is an APPROVE.

---

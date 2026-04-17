---
debate_id: explore-intake-tools-off
created: 2026-04-17T14:50:53-0700
mapping:
  A: claude-opus-4-7
personas:
  A: architect
---
# explore-intake-tools-off — Challenger Reviews

## Challenger A (architect) — Challenges
## Challenges

1. [RISK] [MATERIAL] [COST:SMALL]: The protocol is a 6-page prose specification to be consumed by an LLM at runtime. "Reflect before every question," "use their exact words," "push once if vague," "invite thinking time," "progress cues after Q2+," "one push max per question" — this is a lot of conditional behavior that must be followed turn-by-turn. The Righting Reflex research cited (Google 2025) is precisely the evidence that RLHF-tuned models will drift from these rules under conversational pressure. Without a runtime check or per-turn scaffold (e.g., a required "REFLECTION: ... QUESTION: ..." output format), adherence will decay across turns. Fix: add a mandatory per-turn output structure to preflight-adaptive.md that makes violations visible rather than relying on the model to self-police 8 delivery rules + 5 slot rules + adaptation logic simultaneously.

2. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The adaptive question count table claims a well-specified question gets "1-2 (Slots 1+4 or just 4)" — but Slot 4 is the assumption challenge, which structurally requires prior answers to challenge. Starting with Slot 4 on a clear question means challenging an assumption the user hasn't articulated in this session. Either (a) Slot 4 needs a cold-start variant, or (b) the minimum path is Slot 1 → Slot 4, never "just 4." Clarify in the table.

3. [RISK] [MATERIAL] [COST:TRIVIAL]: The classification step ("Is this question clear enough to act on?") is the linchpin of the adaptive count, but there's no rubric. "Well-specified / Moderate / Ambiguous" has examples but no decision procedure. Given the Righting Reflex finding, the model will systematically classify questions as "clearer than they are" to skip intake. Needs an explicit conservative bias rule: "when in doubt, classify as Moderate, not Well-specified."

4. [OVER-ENGINEERED] [ADVISORY]: Six context block sections (PROBLEM, SITUATION, CONSTRAINTS, TENSION, ASSUMPTIONS TO CHALLENGE, DIMENSIONS) in a 200-500 token budget is tight. TENSION alone is supposed to "earn the most tokens" and use the user's exact words. In practice 500 tokens / 6 sections ≈ 80 tokens/section, and the structured bullets will crowd out the narrative tension. Consider: is ASSUMPTIONS TO CHALLENGE distinct enough from CONSTRAINTS and TENSION to justify its own section, or can it be a sub-bullet under TENSION? The proposal justifies it ("feeds Direction 3") but that coupling could be handled by a tag in the tension itself.

5. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: No verification that the composed context block actually produces more divergent directions than the v5 baseline. The verification command is just `--help`. The entire value proposition ("makes the LLM generate meaningfully different directions") is untested. Before rollout: run N=5-10 real prompts through v5 and v6, compare direction divergence on a rubric (e.g., do the three directions share premises? do they cluster on the same dimension?). Without this, you're swapping one unvalidated intake design for another, more complex one.

6. [ALTERNATIVE] [ADVISORY]: An interesting middle path between "5-track fixed" (rejected) and "5-slot adaptive" (proposed): keep the slot *purposes* as the spec, but ship the system prompt with 2-3 worked example conversations rather than rules. Few-shot conversational examples tend to transfer delivery style (reflection ratio, short questions, no hypotheticals) more reliably than rule lists, per the same prompting research cited. Not necessarily better, but worth considering given the rule-density concern in #1.

7. [RISK] [ADVISORY]: "Preserve the user's exact words for The Tension" + "Compress facts freely" is a subtle instruction for a model. Models routinely paraphrase even when told not to. If the tension's exact-wording property is load-bearing for downstream divergence (as the proposal claims), this needs either a verification step or quotation marks as a structural cue in the template.

## Concessions

1. The research-to-design traceability is unusually strong — each design choice cites specific findings, and the "what stays / what changes" diff against v5 is honest.
2. Identifying the Righting Reflex as the #1 AI failure mode and building explicit structural defense is the right framing; most intake designs miss this.
3. The Tension as the anchor for divergence is a genuine insight and the right thing to optimize the context block around.

## Verdict

REVISE — the design is sound in substance but under-specified at two operational seams: (a) runtime adherence to 13+ conditional rules needs a per-turn output scaffold, not just prose instruction (Challenge 1), and (b) the claim that v6 produces more divergent directions than v5 is unverified and the stated verification command doesn't test it (Challenge 5). Both fixes are small. Challenges 2 and 3 are trivial clarifications. Approve after these four.

---

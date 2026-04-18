---
debate_id: explore-intake
created: 2026-04-17T13:28:22-0700
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
# explore-intake — Challenger Reviews

## Challenger A (architect) — Challenges
## Challenges

1. [RISK] [MATERIAL] [COST:SMALL]: **The context block format breaks the existing parser contract.** `scripts/debate_explore.py` (lines 40-63) splits context on literal strings `DIMENSIONS:`, `PRE-FLIGHT CONTEXT:`, or `CONTEXT:` — everything before `DIMENSIONS:` becomes opaque `narrative_context`, everything after becomes dimension bullets. The proposal's six sections (PROBLEM / SITUATION / CONSTRAINTS / THE TENSION / ASSUMPTIONS TO CHALLENGE / DIMENSIONS) are not parsed. `THE TENSION` and `ASSUMPTIONS TO CHALLENGE` will be swallowed into `narrative_context` with no routing, even though the "How Context Block Maps to Explore Prompts" table claims TENSION goes to both `explore-diverge.md` and `explore-synthesis.md` and ASSUMPTIONS feeds Direction 3 specifically. EVIDENCED: `check_code_presence` returned 0 hits for `THE TENSION`, `ASSUMPTIONS TO CHALLENGE`, `PROBLEM:`, and `SITUATION:` in scripts/. The mapping table is aspirational, not wired. Fix requires either (a) new parser sections + new `{tension}`, `{assumptions}` template variables in the three prompt files, or (b) explicitly scoping this proposal to "context is concatenated into narrative_context, dimensions still extracted" and dropping the per-section routing claims.

2. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: **The "current adaptive protocol (v5)" and the file `config/prompts/preflight-adaptive.md` are not verifiable in this repo.** The manifest shows 6 files in `config/` and none is under a `prompts/` subdirectory; `check_code_presence` for `preflight-adaptive` and `preflight` in config/ returns 0 matches. The skills directory has 2 matches for `PRE-FLIGHT` and 2 for `adaptive` — so the protocol likely lives inside `.claude/skills/explore/SKILL.md`, not in a config prompt file. EVIDENCED above. This matters because the frontmatter lists `config/prompts/preflight-adaptive.md` and `config/prompts/preflight-tracks.md` as surfaces and the rollback plan is "revert preflight-adaptive.md to v5" — if those files don't exist, rollback is a no-op and the real surface (SKILL.md) isn't listed. Fix: correct the surfaces_affected list to the actual file path, or state explicitly "creates config/prompts/ directory as new surface."

3. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: **No test strategy for a protocol change that the LLM, not code, executes.** This proposal changes behavioral rules ("reflect before every question," "one question per message," "don't solve during intake") that live entirely in prompt text interpreted by the agent. There is no deterministic unit test that can assert "the agent reflected before Q2" or "the context block stayed under 500 tokens." The manifest shows `tests/test_debate_commands.py` and related tests exercise `debate.py explore` mechanics, but none assert anything about intake quality. Without at least (a) a golden-output test on the context-block composition step (given fixture answers → expected structured block) or (b) a token-budget assertion, regressions will only surface in live use. Fix: add a pure function `compose_context_block(answers: dict) -> str` in `debate_explore.py` or a sibling module so composition is testable independent of the conversation.

4. [OVER-ENGINEERED] [ADVISORY]: **Eight delivery rules + five slot purposes + four adaptation rules per slot + eight composition rules = ~25 behavioral constraints the agent must hold simultaneously.** Instruction-following research the proposal itself cites (arXiv 2507.11538, threshold/linear/exponential decay) argues against long rule stacks. The most-cited findings ("one at a time," "reflect before asking," "past not hypothetical," "don't solve") would likely carry 80% of the lift at 20% of the prompt length. Risk: the prompt becomes a compliance checklist the model partially ignores, defeating its own research base. ADVISORY because the proposal's research depth justifies ambition, but consider shipping a v6a "tight" variant (top 5 rules) and measuring before adding the long tail.

5. [ALTERNATIVE] [ADVISORY]: **The proposal rejects fixed tracks but doesn't consider a two-tier fallback: slot-based for ambiguous inputs, direct dimension elicitation for well-specified ones.** The "Adaptive Question Count" table already admits well-specified inputs need 1-2 questions (Slot 1+4). That's effectively a different protocol — acknowledge it as such and let clarity classification route to a short-path composer that skips reflection/meta entirely. Same outcome, simpler mental model, testable as two code paths.

6. [RISK] [ADVISORY]: **"Preserve the user's exact words for The Tension" conflicts with "3:1-5:1 compression" and "resolve contradictions."** Compression and fidelity-to-source are in tension. When the user's articulation of the tradeoff is 4 sentences of hedged language, the composer must choose. The rule as written gives no precedence. In practice the LLM will compress and claim it preserved — undetectable without eval.

## Concessions

1. The research base is unusually thorough for an intake-design change and the citation specificity (OR=1.55, 82% preference, 3.06 avg queries) is better than typical proposals.
2. The failure-mode enumeration with ranked likelihood and named defenses is the right structure — Righting Reflex is correctly identified as the dominant AI-specific risk.
3. Separating CONSTRAINTS from SITUATION is a genuinely strong call, backed by the cited under-weighting research, and a concrete improvement over a free-form narrative context.

## Verdict

**REVISE** — the intake protocol design is defensible but the context-block schema ships sections (`THE TENSION`, `ASSUMPTIONS TO CHALLENGE`, `PROBLEM`, `SITUATION`, `CONSTRAINTS`) that the existing `debate_explore.py` parser does not route anywhere, so the claimed mapping to explore prompts is not real without a parser + template change (Challenge 1, SMALL), and the surfaces_affected list names files that cannot be verified to exist (Challenge 2, TRIVIAL). Both are cheap fixes; hence REVISE, not REJECT.

---

## Challenger B (security) — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The proposal expands intake to collect richer subjective and organizational context, but it does not define any trust-boundary or redaction rules before that content is inserted into model prompts and written to output artifacts. In this repo, `debate.py explore` accepts raw `--question` and `--context`, and `scripts/debate_explore.py` passes them straight into model prompts and persists the question prefix plus generated output to disk and event logs. That creates a concrete prompt-injection and data-exfiltration surface: user-supplied intake text can contain instructions to override the explore prompt, secrets, or third-party private data, and the proposed redesign increases the volume and sensitivity of that text without adding sanitization, tagging, or “treat intake as untrusted data” handling.

2. [UNDER-ENGINEERED] [MATERIAL] [COST:TRIVIAL]: The proposal introduces a new “compose, don’t concatenate” translation step, but it never specifies that this step must remain deterministic code rather than an LLM-generated transformation. The repo’s security rule explicitly says LLM outputs must be structured, validated, and applied by deterministic code for anything that influences stateful behavior. If the new context-block composer is implemented as a prompt-driven summarizer, it becomes a prompt-injection choke point: malicious intake can steer the summarization itself, suppress constraints, or manufacture assumptions that then bias all downstream explore directions.

3. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal assumes the cited research justifies operational changes like mandatory Slot 4, 2:1 reflection ratio, and 200–500 token context targets, but there is no repo-local validation plan showing these changes improve output quality without increasing leakage or failure modes. Because `scripts/debate_explore.py` currently consumes `--context` as opaque text and parses only simple `DIMENSIONS:` markers, this redesign changes both prompt structure and effective control surface. The material risk of changing is degraded exploration quality or easier prompt steering; the material risk of not changing is keeping today’s weaker, less structured intake. You need an A/B evaluation plan on representative prompts before hard-coding these rules into the skill.

4. [UNDER-ENGINEERED] [ADVISORY]: The proposal says “preserve the user’s exact words for The Tension,” which is good for fidelity but risky for prompt hygiene. Exact user phrasing is also the most likely place to carry adversarial instructions, quoted credentials, or defamatory/private text into the final context block. A safer rule is “preserve exact words selectively, after redaction and bounded quoting.”

5. [ALTERNATIVE] [ADVISORY]: Instead of replacing fixed tracks entirely, consider retaining tracks only as internal routing heuristics, not user-facing classification. That would preserve adaptive questioning while reducing the chance that one generic slot sequence misses domain-specific safety checks for areas like vendor evaluation, org politics, or technical architecture.

## Concessions
- The proposal correctly identifies the main product risk of **not** changing: current intake is too unstructured to consistently extract constraints, tension, and dimensions that drive materially different explore outputs.
- The proposed slot sequence reduces one real failure mode in LLM UX: premature solving before the system understands the user’s actual intent.
- The repo already has a strong security posture around credentials and deterministic boundaries, and the proposal is directionally compatible with that posture if the composition step is implemented carefully.

## Verdict
REVISE — the redesign is promising, but it needs explicit untrusted-input handling and a deterministic, validated composition path before it is safe to adopt.

---

## Challenger C (pm) — Challenges
## Challenges
1. [OVER-ENGINEERED] [MATERIAL] [COST:LARGE]: Strict sequential multi-turn interrogation is hostile UX for a developer tool. The rule "One question per message. Never batch" forces up to 4-5 sequential round trips before the LLM does any actual work. Translating survey research (Typeform) to chat interfaces ignores latency and user expectations. An [ESTIMATED] 3-5 conversational turns means minutes of typing and waiting just to start the core `/explore` task. Users will abandon the flow. To fix the failure of "acting on vague inputs without clarity," the system should eagerly generate *provisional* exploratory directions while asking 1-2 clarifying questions in parallel (show, don't just ask). 
2. [ASSUMPTION] [MATERIAL] [COST:MEDIUM]: The proposal assumes the LLM can simultaneously juggle an enormous set of psychological frameworks and constraints in a single system prompt. Implementing 5 slot purposes, 8 delivery rules (no hypotheticals, don't solve, push once), Motivational Interviewing, CBT downward arrows, and Clean Language will overwhelm the LLM's instruction-following capacity. The model will either drop rules or hallucinate. 
3. [RISK] [MATERIAL] [COST:SMALL]: The implementation plan targets files that do not exist in the repository structure. A tool check verifies that `config/prompts/preflight-adaptive.md` and `config/prompts/preflight-tracks.md` do not exist (the string `preflight-adaptive` only exists within the `skills` directory files, likely `skills/explore`). The implementation must be scoped to the actual file structure (e.g., `skills/explore`).
4. [RISK] [ADVISORY]: Extreme domain mismatch in the research application. Applying FBI elicitation techniques, Clean Language, and CBT therapeutic frameworks to standard software engineering questions ("How should we think about our data layer?") risks generating a tone that is off-putting, overly dramatic, or inappropriately probing for a technical CLI tool.

## Concessions
1. The structured context composition template (Problem, Situation, Constraints, Tension, Dimensions) is highly rigorous and effectively addresses context rot.
2. Isolating "The Tension" as the anchor for generating genuinely divergent directions is an excellent, high-leverage insight.
3. Abandoning the user-facing self-classification "tracks" in favor of system-side dynamic inference removes unnecessary user cognitive load.

## Verdict
REVISE because while the context formatting rules are phenomenal, the strict 5-turn Socratic interrogation protocol will create massive UX friction and needs to be condensed into a single "eager" exploration turn.

---

## Challenger D (frame-structural) — Challenges
## Challenges

1. **ASSUMPTION [MATERIAL] [COST:MEDIUM]**: The proposal assumes the primary failure mode is *question design* — that better intake questions will produce meaningfully different explore outputs. But the proposal never demonstrates that the current v5 protocol's outputs are actually bad, or that the gap between v5 and this design is attributable to question sequencing rather than the downstream explore prompts themselves. The context block composition rules and the explore-diverge.md prompt templates are the actual translation layer between intake and output quality. If those prompts are weak, a perfect intake protocol produces nothing. The proposal treats the intake as the bottleneck without evidence. SPECULATIVE claim: no before/after output comparison is provided.

2. **ASSUMPTION [MATERIAL] [COST:SMALL]**: The entire research base is drawn from *human-to-human* or *human-to-form* interaction contexts (Typeform completion rates, MI therapy sessions, journalism interviews, FBI elicitation). The proposal applies these findings to an LLM-mediated intake where the "interviewer" is also the downstream executor. This is a category difference: in MI or journalism, the interviewer is a separate agent with genuine uncertainty. Here, the LLM is performing intake *for itself*. The Righting Reflex finding (Google Research 2025) actually suggests the model will structurally resist the protocol regardless of how it's written. The proposal names this as a failure mode but treats it as solvable by a rule ("do not offer solutions during intake") — which is precisely the behavior RLHF training undermines. No evidence that a written rule overrides RLHF bias.

3. **ALTERNATIVE [MATERIAL] [COST:SMALL]**: A missing candidate: **single-pass structured intake form** rather than a conversational multi-turn protocol. The proposal dismisses fixed question sets because "they can't adapt to what the user actually says," but the research it cites (Typeform, TurboTax) is about *form completion*, not conversational depth. A structured one-shot intake — "Answer these 3 questions in one message: (1) what are you trying to decide, (2) what have you tried, (3) what's the constraint" — would be faster, more predictable, and easier to test. The proposal never considers this hybrid. The conversational multi-turn approach is assumed without evaluating the tradeoff against single-pass structured intake.

4. **OVER-ENGINEERED [MATERIAL] [COST:MEDIUM]**: The proposal introduces a 5-slot adaptive sequence, 8 delivery rules, a 6-section context block template, composition rules, slot adaptation rules, and a question count calibration table — all as a *prompt rewrite* of preflight-adaptive.md. This is a large behavioral specification being encoded in natural language instructions to an LLM. The implementation plan (step 1: "rewrite preflight-adaptive.md") treats this as a single file change, but the actual complexity is in whether an LLM will reliably execute a 5-slot adaptive protocol with reflection ratios, Clean Language constraints, and anti-Righting-Reflex rules in a live conversation. There is no evaluation plan, no A/B test, no rubric for whether the protocol is being followed. The proposal jumps from research synthesis to full implementation without a validation step.

5. **ASSUMPTION [ADVISORY]**: The 200-500 token context block target is cited as derived from "context rot research" and Anthropic best practices. SPECULATIVE: no evidence is provided that the *explore-specific* downstream prompts degrade at >500 tokens, or that the current context blocks exceed this. The target may be correct but is applied without measuring the current baseline.

6. **ALTERNATIVE [ADVISORY]**: The proposal removes `preflight-tracks.md` (the 5-track fixed design from the prior session) entirely, framing it as superseded. A missing hybrid: **tracks as slot-selection heuristics** rather than fixed question sets. The track classification could determine *which* Slot 4 variant to use (premise challenge vs. the unsaid vs. action test) without requiring full conversational adaptation. This would preserve the predictability benefit of tracks while adding the flexibility the proposal values. The either/or framing (tracks vs. adaptive slots) may be a false dichotomy.

7. **RISK [ADVISORY]**: The proposal's scope statement lists `scripts/debate.py` as a surface affected, but the implementation plan (steps 1-6) makes no mention of changes to debate.py. If the context block format changes (adding ASSUMPTIONS TO CHALLENGE), any code in debate.py that parses or passes the context block may need updating. This is an untracked dependency.

8. **ASSUMPTION [ADVISORY]**: The "2:1 reflection-to-question ratio" from MI is cited as "the single most actionable finding for chat-based intake." SPECULATIVE: MI evidence (PMC8200683, OR=1.55) is for *behavior change* outcomes in therapy, not for *information elicitation quality* in AI-assisted research. The transfer assumption is doing significant load-bearing work and is not validated for this context.

---

## Concessions

1. **The failure mode taxonomy is genuinely useful.** Naming the Righting Reflex, Interrogation Trap, and Premature Specificity as distinct failure modes with specific defenses is more rigorous than most prompt design proposals. Even if the full protocol is over-specified, these categories are worth preserving.

2. **The context block composition rules address a real gap.** The distinction between concatenation and compression (3:1-5:1), separating constraints from facts, and anchoring on The Tension are structurally sound improvements over free-form context assembly. This section is the most defensible part of the proposal.

3. **Removing preflight-tracks.md is correct.** The prior session's 5-track fixed design had the classification burden problem the proposal identifies. The adaptive slot approach is a genuine improvement in framing, even if the implementation is over-specified.

---

## Verdict

**REVISE** — The proposal's research synthesis is thorough and the context block design is sound, but it skips the critical validation step: there is no evidence that v5's *outputs* are deficient, no plan to test whether an LLM will reliably execute this protocol, and no consideration of a simpler single-pass intake alternative. The implementation plan should be preceded by a lightweight evaluation of current explore output quality and a pilot of the context block format change alone before committing to the full 5-slot conversational protocol.

---

## Challenger E (frame-factual) — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL] [COST:SMALL]: The proposal treats `/explore` as if its intake flow currently lives in `scripts/debate.py`, but the actual `cmd_explore` implementation has already been extracted to `scripts/debate_explore.py` (`scripts/debate.py` imports `from debate_explore import cmd_explore` at lines 3320-3324). That changes the implementation surface and next steps: updating `scripts/debate.py` would not affect explore behavior unless `_load_prompt` plumbing is the only intended change. Verified in `scripts/debate.py:3320-3324` and `scripts/debate_explore.py:16-92`.

2. [ASSUMPTION] [MATERIAL] [COST:MEDIUM]: The proposal frames the current system as lacking “composition rules for the context block,” but the shipped code already implements a structured composition contract for explore context: it parses a `DIMENSIONS:` section and separates it from `PRE-FLIGHT CONTEXT:` / `CONTEXT:`, then injects dimensions and narrative context into distinct prompt slots (`scripts/debate_explore.py:40-92`). So “no composition rules” is too strong; the real gap is that current composition is limited/coarse, not absent. This matters because the recommendation should be an iteration on the existing format rather than a greenfield redesign.

3. [ASSUMPTION] [MATERIAL] [COST:TRIVIAL]: The proposal says it is “replacing the 5-track fixed questions (from last session's design)” and plans to “remove the planned `config/prompts/preflight-tracks.md`,” but there is no evidence in the code/docs surfaces that such a shipped track file or code path exists now. String search found no `preflight-tracks` references in scripts or skills, and no docs references either. This makes part of the motivation stale: the repo state does not show an active fixed-track implementation that needs removal. Tool evidence: `check_code_presence("preflight-tracks", scripts|skills)` returned no matches.

4. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: The implementation plan proposes prompt/skill changes only, but the repo has command-level tests for `cmd_explore` and already asserts structured context handling (`tests/test_debate_commands.py:658-672` passes `DIMENSIONS:` + `PRE-FLIGHT CONTEXT:`). If the context schema changes to add `ASSUMPTIONS TO CHALLENGE` or new intake formatting rules, those tests need updating/expanding; otherwise the redesign risks drifting from the exercised contract. The current plan mentions only “test end-to-end with a real /explore run,” which is weaker than the repo’s existing automated test posture.

## Concessions
- The proposal is directionally right that `/explore` already consumes structured dimensions plus a narrative pre-flight context, so improving that interface is a meaningful lever (`scripts/debate_explore.py:40-92`).
- The proposal is also right that one-question-at-a-time adaptive intake would be prompt-driven work more than deep code work, since explore prompt loading is already file-based (`scripts/debate_explore.py:84-91`).
- The claimed implementation surface does include skill/prompt-level guidance, which aligns with the current architecture’s prompt-centric explore behavior.

## Verdict
REVISE — the redesign may be valuable, but the proposal overstates gaps in the current system and targets the wrong code surface in places, so it should be rewritten as an iteration on existing explore context plumbing rather than a replacement of non-shipped infrastructure.

---

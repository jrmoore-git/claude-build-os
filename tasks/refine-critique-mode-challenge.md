---
debate_id: refine-critique-mode
created: 2026-04-13T21:35:03-0700
mapping:
  A: claude-opus-4-6
  B: gemini-3.1-pro
  C: gpt-5.4
---
# refine-critique-mode — Challenger Reviews

## Challenger A — Challenges
## Challenges

1. **ASSUMPTION** [ADVISORY]: The proposal assumes frontmatter regex parsing is robust enough without specifying edge cases. What happens if the input has `---` delimiters but the content between them isn't YAML-like (e.g., a markdown document with horizontal rules)? The suggested regex `^mode:\s*(pressure-test|premortem)\s*$` scoped to the frontmatter block is fine, but the brief doesn't specify how to identify the frontmatter block itself (first `---` must be line 1, second `---` terminates it). A naive implementation could match `mode: pressure-test` anywhere in the document. The brief says "between the first two `---` lines" which is sufficient guidance — an implementer who reads carefully will get this right, but it's worth noting.

2. **RISK** [MATERIAL] [COST:TRIVIAL]: The argparse default for `--mode` is specified as `None` in the prose (Change 1), but the "Current CLI parser" section at the bottom says `default="proposal"`. These contradict each other. The prose is correct (and explains why — argparse can't distinguish explicit default from omitted), but an implementer skimming the code reference section could wire it wrong and silently break auto-detection. The code reference section should be corrected or the implementer should be explicitly warned that the code reference section contains the *current* state, not the target state. Reading more carefully, the code reference says "Add `--mode` argument here with choices `["proposal", "critique"]` and default `"proposal"`" — this is actively wrong per the design. Fix: change that line to `default=None` in the brief before handing to an implementer.

3. **UNDER-ENGINEERED** [ADVISORY]: The length heuristic ("<= 110% of input length") is described as a desired tendency, not a hard gate, which is the right call. But there's no mechanism to surface this signal. If an implementer or future operator wants to detect prompt failure (output grew 2x), they'd need to add their own check. A one-line stderr warning when output exceeds 120% of input would cost nothing and provide useful signal. Not blocking, but a missed opportunity.

4. **RISK** [ADVISORY]: The `--judgment` flag behavior change in critique mode (from "MUST be addressed" to "optional context") is described but the mechanism isn't specified. If the current prompts inject judgment context with language like "You MUST address each of the following issues," then critique mode needs to use different injection language. The brief says to keep `{judgment_context}` as a template variable but doesn't specify what wrapper text surrounds it in critique mode. An implementer could easily keep the "MUST address" framing and defeat the purpose. This is covered by "the implementer may draft the full prompt strings based on the constraints below" but the constraint on judgment framing is buried in a sub-bullet and easy to miss.

5. **ALTERNATIVE** [ADVISORY]: The brief prescribes two modes (`proposal` / `critique`). A third mode — `review` or `analysis` — could cover documents that are neither proposals nor critiques (e.g., technical analyses, comparisons, research summaries). The current design falls through to `proposal` for anything that isn't a critique, which may cause the same over-specification problem on analytical documents. However, this is speculative — there's no evidence of this failure mode today, and adding a third mode without a concrete use case would be premature. The two-mode design is correct for the diagnosed problem.

6. **OVER-ENGINEERED** [ADVISORY]: The three-tier mode resolution (explicit flag → frontmatter detection → default) is well-designed but the stderr notice on auto-detection is a minor UX detail that the brief elevates to a verification criterion. This is fine — it's trivial to implement and useful for debugging — but it's not load-bearing.

7. **ASSUMPTION** [MATERIAL] [COST:SMALL]: The brief assumes the critique-mode prompts will reliably prevent models from drifting into solutioning. This is the core bet of the entire change. The forbidden-additions list is comprehensive, but LLMs are notoriously difficult to constrain via negative instructions ("do NOT add X"). The brief mitigates this with both positive framing ("your job is to make this critique sharper") and negative constraints, which is the right approach. However, there's no fallback if the prompts don't work — no structural enforcement (like post-processing or output validation). Given that this is a prompt-engineering change and the failure mode is "output quality degrades gracefully" rather than "system breaks," this is acceptable risk. But the team should expect to iterate on prompt wording after the first few real runs. The verification step (item 2) is the right gate.

## Concessions

1. **The diagnosis is precise and well-evidenced.** The root cause analysis correctly identifies the two specific rules (`REFINE_STRATEGIC_POSTURE_RULE` and `REFINE_RECOMMENDATION_PRESERVATION_RULE`) that drive the wrong behavior, and the degradation pattern (sharp critique → consulting deliverable) is a real and common failure mode with iterative LLM refinement.

2. **The scope is disciplined.** Limiting changes to the refine subcommand, preserving proposal-mode byte-identical behavior, and not touching pressure-test or other subcommands is the right call. The change surface is minimal for the problem being solved.

3. **The default-to-`None` pattern for both `--mode` and `--rounds`** is a clean design that correctly separates "user intent" from "system default" and enables auto-detection without ambiguity. The resolution order is well-specified.

## Verdict

**APPROVE** — The proposal is a well-scoped, correctly diagnosed fix with clean component boundaries, no new dependencies, and a solid verification plan. The one material issue (contradictory default value in the code reference section) is a TRIVIAL documentation fix that should be corrected before handing to an implementer to avoid a silent auto-detection bug.

---

## Challenger B — Challenges
## Challenges

1. [RISK] [MATERIAL] [COST:SMALL]: **Fragile YAML Regex Parsing**
The proposal specifies using the regex `^mode:\s*(pressure-test|premortem)\s*$` to parse the frontmatter without PyYAML. This regex is too brittle for LLM-generated frontmatter. If the pressure-test output slightly varies the YAML formatting by adding quotes (e.g., `mode: "pressure-test"`, `mode: 'premortem'`) or trailing comments, the regex will fail to match. Because the failure mode is a silent fall-through to `proposal` mode, this brittleness will intermittently reintroduce the exact degradation this spec aims to fix. The regex must account for optional quotes and use `re.MULTILINE` (`re.M`) to ensure `^` matches the start of lines within the document string.

2. [UNDER-ENGINEERED] [ADVISORY]: **Stdin Buffer Exhaustion**
The spec notes the frontmatter detection should work "regardless of whether it came from file or stdin." If the script currently streams `stdin` directly into the model API or a subsequent processor, intercepting it to read frontmatter with a regex will consume the buffer. The implementer needs to ensure the `stdin` input is fully read into memory (e.g., `sys.stdin.read()`) before running the regex, and that this cached string is passed down the pipeline, rather than attempting to read from the exhausted `stdin` file descriptor again.

## Concessions
1. Mandating `None` as the argparse default to allow for layered, intelligent resolution logic later in the script is exactly the right way to build CLI tools.
2. Dropping the default round count to 2 for critiques is an elegant, structural safeguard against LLM "process theater" that doesn't rely solely on prompt engineering. 
3. Scoping the changes strictly to the `refine` subcommand prevents unnecessary regression testing across the `pressure-test` and `judge` modes.

## Verdict
APPROVE with minor implementation care required for the regex to handle quoted YAML values.

---

## Challenger C — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: Frontmatter auto-detection uses a simple regex over the top block, but the proposal does not specify a strict trust boundary for when frontmatter is considered authoritative versus attacker-controlled input. If `refine` is used on arbitrary external content, a user-supplied `mode: pressure-test` header can silently change model instructions and round defaults. That is not a privilege escalation by itself, but it is a control-plane input affecting behavior. Mitigation: treat frontmatter as advisory only when `--mode` is omitted (as proposed), emit the stderr notice, and keep explicit override precedence exactly as written. This does not block the change, but should be implemented carefully to avoid surprising mode shifts.
2. [ASSUMPTION] [ADVISORY]: The regex approach assumes the first two `---` lines unambiguously delimit YAML frontmatter and that documents will not begin with unrelated markdown horizontal rules or content that incidentally matches. That can cause false auto-detection or missed detection. Given the “no new dependencies” constraint and narrow matching (`mode: pressure-test|premortem`), this is acceptable, but the helper should be conservative: only inspect an initial frontmatter block starting at byte 0.
3. [UNDER-ENGINEERED] [ADVISORY]: The success criterion about output length (<=110%) is explicitly non-binding, but the change relies entirely on prompt steering to prevent elaboration. There is no mechanical guardrail against critique-mode bloat, so regressions may still occur with some models. This is not enough to reject the proposal because the requested scope is prompt/mode handling only, but it should be recognized as an unresolved residual risk.
4. [ALTERNATIVE] [ADVISORY]: For verification, comparing constructed proposal-mode prompts byte-for-byte to pre-change behavior is the right regression test. To reduce accidental drift further, the proposal-mode branch could literally reuse the existing prompt constants and rule concatenation path rather than duplicating strings. This is an implementation preference, not a flaw in the proposal.

## Concessions
- The proposal preserves proposal-mode behavior and scopes changes tightly to `refine`, which limits blast radius.
- It explicitly keeps evidence-tagging and output-format requirements in critique mode, which helps avoid unsupported claims rather than weakening review quality.
- The explicit precedence order for `--mode` and `--rounds` is clear and avoids ambiguity, especially the important `argparse default=None` detail.

## Verdict
APPROVE — the change is narrowly scoped, security impact is low, and the main behavioral risks are acknowledged and manageable with conservative implementation.

---

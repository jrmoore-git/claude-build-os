---
debate_id: challenge-pipeline-enriched-findings
created: 2026-04-15T15:19:31-0700
mapping:
  A: claude-opus-4-6
  B: gpt-5.4
  C: gemini-3.1-pro
---
# challenge-pipeline-enriched-findings — Challenger Reviews

## Challenger A — Challenges


## Challenges

1. **ASSUMPTION [MATERIAL] [COST:TRIVIAL]:** The proposal claims `--verify-claims` "exists on `debate.py judge`" but tool results show only 1 match for `verify-claims` and 0 matches for `def verify_claims` across scripts. The `add_argument("--verify` pattern also returned no matches. This means the flag is likely referenced in a comment, help text, or a string literal — not actually wired as a functional argument with implementation logic. The proposal's Layer 3 is described as "wire into `debate.py judge --verify-claims`" as if extending existing functionality, but it may be building from scratch. This changes the cost estimate from MEDIUM to potentially LARGE if there's no verification infrastructure to hook into.

2. **RISK [MATERIAL] [COST:MEDIUM]:** Layer 4 (dissent requirement on unanimous kill) introduces a second round of LLM calls that doubles latency and cost for unanimous-reject cases. The proposal doesn't specify: (a) which model switches to advocate (random? the weakest dissenter?), (b) whether the advocate round uses the same context or enriched context, (c) how the judge weighs advocate findings vs. the original three challengers, or (d) what happens if the advocate produces a compelling case — does it trigger a full re-evaluation? Without these decisions, implementation will either stall or produce ad-hoc choices that become load-bearing. The `advocate` and `unanimous` patterns don't exist anywhere in the codebase today (confirmed: 0 matches each), so this is genuinely new machinery.

3. **UNDER-ENGINEERED [MATERIAL] [COST:SMALL]:** The proposal has no feedback loop to measure whether these fixes actually work. The "false kill rate" is acknowledged as "at least 1 confirmed, unknown total — no tracking exists." After implementing Layers 1-4, how do you know the false kill rate improved? Without a lightweight tracking mechanism (even just a field in `debate-log.jsonl` for post-hoc verdict accuracy), you'll ship four layers of fixes and have no way to validate them. This is especially important because Layer 4 adds cost — you need evidence it's earning its keep.

4. **RISK [ADVISORY]:** `debate.py` at 4,136 lines has no direct test file (confirmed: `check_test_coverage` returned no test files for `debate.py` or `debate_helpers.py`). The proposal mentions "106 debate.py pure-function tests" from sessions 7-10, but these don't appear to be in a discoverable test file. Adding Layer 3 (claim extraction + verification injection into judge context) and Layer 4 (advocate round) to a 4K-line file with no test coverage is risky for regression. The proposal doesn't mention testing strategy for the new code.

5. **ALTERNATIVE [ADVISORY]:** Layer 3 proposes running Perplexity queries to verify "commodity" claims. An alternative that's cheaper and more deterministic: require challengers to cite specific feature comparisons when making build-vs-buy claims (prompt engineering), and have the judge downweight unsubstantiated "tool X already does this" claims. This is a prompt-level fix (TRIVIAL) vs. a new verification subsystem (MEDIUM). It won't catch all cases but addresses the 80% at 10% of the cost.

6. **OVER-ENGINEERED [ADVISORY]:** The proposal frames this as "four structural bugs" but Bugs 1 and 4 are the same root cause (insufficient context in proposals). Bug 1 is "proposals don't include operational evidence" and Bug 4 is "thin context packets across 6 skills." Both are solved by enriching what goes into the debate. Framing them as separate bugs is fine for diagnosis but the fix is one thing: better context assembly. Layers 1 and 2 together are the real fix; Layers 3 and 4 are separate concerns (verification and dissent).

## Concessions

1. **Layer 1 is a clear win.** Adding `## Operational Evidence` to the proposal template is zero-code, zero-risk, and directly addresses the confirmed sim-compiler false kill. The "Operational Evidence" string already has 1 match in skills (confirmed), suggesting this may already be partially landed.

2. **The A/B test evidence is compelling.** The thin-vs-enriched proposal comparison (tool calls dropping from 29→22 for Claude, 14→9 for GPT; divergence→convergence) is concrete operational data, not speculation. Layer 2 is well-motivated.

3. **The layered ordering is correct.** Trivial→Small→Medium→Deferred is the right sequencing. The proposal explicitly identifies the simplest version (Layer 1 alone) and defers the phase split. This is disciplined prioritization.

## Verdict

**APPROVE with conditions**: Layers 1-2 should ship immediately — they're well-evidenced and low-risk. Layer 3 needs a design spike to confirm `--verify-claims` actually has implementation scaffolding (tool results suggest it doesn't). Layer 4 needs a brief design doc specifying advocate selection, judge weighting, and a tracking mechanism for false-kill rate before implementation. Don't block Layers 1-2 on Layers 3-4.

---

## Challenger B — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:SMALL]: Layer 3 introduces an external verification step (“run a focused Perplexity query”) but the proposal does not define trust boundaries or sanitization for model-generated claims before sending them to a third-party service. The inputs here are untrusted challenger output plus proposal requirements, and without explicit redaction rules you risk exfiltrating sensitive proposal details, internal evaluation data, or proprietary requirements to an external provider. This matters because the whole point of Layer 1 is to add more operational evidence; Layer 3 could then leak that richer context outward unless constrained.

2. [UNDER-ENGINEERED] [ADVISORY]: The proposal assumes build-vs-buy verification is safe to automate, but “tool X already does this” is a prompt-injection-adjacent input source: challenger text can name arbitrary products, URLs, or capabilities. If the verifier later grows beyond search/query into URL fetching, this becomes an SSRF or untrusted-content ingestion surface. Put differently: the current design is fine if verification remains a bounded search against a known provider, but that boundary should be stated now.

3. [ASSUMPTION] [ADVISORY]: The dissent round assumes “one model switches to advocate” improves correctness rather than just adding cost and more synthetic argumentation. That may still be worth it, but the proposal does not define when advocate output is authoritative versus merely informational. Without that, unanimous correlated error may be reduced, but so may signal quality if the advocate is forced to invent defenses unsupported by evidence.

4. [UNDER-ENGINEERED] [ADVISORY]: The proposal strengthens context everywhere, which is directionally right, but it does not mention log/data-retention implications. `debate.py` exists and the proposal states `debate-log.jsonl` tracks all runs; adding richer operational evidence and context packets may increase the amount of sensitive historical data persisted in logs and artifacts. This is not a blocker in a speed-with-guardrails posture, but it should be bounded.

5. [ALTERNATIVE] [ADVISORY]: For Layer 3, a lower-risk first step would be to require challengers to express commodity claims in a structured format (“tool, claimed capability, requirement matched, evidence needed”) and only verify those fields, rather than free-text extracting arbitrary claims from findings. That reduces parsing ambiguity and narrows injection/exfiltration surface while still shipping fast.

## Concessions
- The proposal correctly identifies correlated model error as a trust problem, not just a prompt-quality problem.
- Layer 1 is a high-leverage, low-cost fix that directly addresses a demonstrated failure mode without adding infrastructure.
- The proposal is grounded in real system structure: `scripts/debate.py` exists with a `judge` subcommand and `--verify-claims` support present in code, while `scripts/enrich_context.py` exists and already has tests.

## Verdict
REVISE with one narrow security condition: proceed with Layers 1, 2, and likely 4, but specify redaction/bounding rules for Layer 3’s external claim verification so richer internal evidence is not leaked to third-party services.

---

## Challenger C — Challenges
## Challenges

1. **[OVER-ENGINEERED] [MATERIAL] [COST:MEDIUM]:** Layer 3 (Build-vs-buy claim verification) requires extracting specific "commodity" claims from unstructured model findings to programmatically trigger focused Perplexity queries. This adds brittle NLP extraction logic. Since the `--verify-claims` flag already exists, it would be much simpler to instruct the human to run it manually when they suspect a false kill, or to add a prompt instruction to the judge to critically evaluate build-vs-buy claims using its existing tools.
2. **[RISK] [MATERIAL] [COST:MEDIUM]:** Layer 4 (Dissent requirement) automatically doubles the token cost, tool usage, and latency for any unanimously rejected proposal. Furthermore, forcing a model to play "advocate" for a genuinely terrible proposal will likely generate hallucinated or extremely weak arguments, wasting the user's time reviewing a manufactured debate instead of just moving on from a bad idea. 
3. **[ASSUMPTION] [ADVISORY]:** Layer 1 assumes that an empty `## Operational Evidence` section will be treated neutrally by the models for greenfield projects. There is a risk that models will inherently penalize proposals that leave this blank, introducing a bias against genuinely new ideas that lack prior track records.

## Concessions
- Adding operational evidence to the `/challenge` template perfectly isolates the root cause of the sim-compiler false kill. 
- Layer 2 is strongly justified by the A/B test data [EVIDENCED: reduced Claude tool calls from 29→22 and improved convergence].
- The proposal correctly acknowledges that splitting the value/build-buy phases should be deferred as it fundamentally changes the skill's architecture.

## Verdict
REVISE: Proceed with Layers 1 and 2, but drop Layers 3 and 4 which introduce brittle extraction logic and double the cost of rejections for marginal gain.

---

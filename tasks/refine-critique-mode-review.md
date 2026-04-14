Calling architect...
Calling security...
Calling pm...
## Reviewer A

Here’s a production-readiness review focused on the four areas you asked about.

## Overall
This is a good change and directionally correct. The split between proposal refinement and critique refinement is necessary, and the new prompts are materially better aligned to critique artifacts than the old “make it more executable” posture.

That said, I would **not ship this unchanged**. Main concerns:

1. **Mode detection is useful but brittle**
   - likely misses valid critique docs due to narrow regexes
   - can false-positive on proposal docs with overlapping section names
   - frontmatter parsing is too strict

2. **The anti-solutioning prompts help, but won’t reliably prevent drift on their own**
   - especially in first round
   - they constrain style, but not enough on structure and allowed transformations

3. **Content heuristic has meaningful edge-case risk**
   - challenge headings are too generic
   - matching is case-sensitive and format-sensitive
   - not anchored enough to actual debate artifacts

4. **Potential regression to proposal mode is low but nonzero**
   - default behavior remains proposal, good
   - but auto-detection false positives could silently switch a proposal doc into critique mode
   - critique-mode truncation threshold may accept over-compressed outputs that are actually bad

## 1. Correctness of mode detection logic

### What’s good
The precedence order is right:

- explicit `--mode`
- frontmatter
- content heuristic
- default proposal

That’s a sane and production-friendly stack.

The round default depending on resolved mode is also correct and improves UX.

### Main problems

#### A. Frontmatter regex is too strict
```python
fm_match = re.match(r'^---\s*\n(.*?)\n---', document, re.DOTALL)
```

This only matches if:
- frontmatter starts at byte 0
- line endings are `\n`, not `\r\n`
- closing `---` is exactly newline-bounded in this way

This will miss:
- files with BOM
- leading whitespace/newlines
- Windows line endings
- frontmatter with trailing spaces around delimiters in unexpected ways

**Recommendation:** normalize or use a more tolerant regex, e.g. conceptually:
- allow optional BOM / leading whitespace
- support `\r?\n`

Example:
```python
fm_match = re.match(r'^\ufeff?\s*---\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)', document, re.DOTALL)
```

#### B. Frontmatter key matching is too narrow
```python
r'^mode:\s*["\']?(pressure-test|premortem)["\']?\s*$'
```
This misses likely real variants:
- `pre-mortem`
- `pressure test`
- case variants
- whitespace variants

Likewise:
```python
r'^phase:\s*["\']?(challenge|judge|judgment)["\']?\s*$'
```
This misses:
- `challenger`
- `judgement` spelling
- case variants

And:
```python
r'^debate_id:\s*.*(?:challenge|judgment|pressure-test|premortem)'
```
This is:
- case-sensitive
- not word-bounded
- doesn’t include `pre-mortem`, `pressure test`, `judge`, `judgement`

**Recommendation:** use `re.IGNORECASE` and normalize accepted aliases.

#### C. Challenge heading heuristic is too generic
```python
challenge_headings = [
    r'##\s+Challenger\s+[A-Z]\s+—\s+Challenges',
    r'##\s+Challenges\b',
    r'##\s+Concessions\b',
    r'##\s+Verdict\b',
]
```

This is the biggest correctness risk.

A normal proposal or decision memo could easily contain:
- `## Challenges`
- `## Concessions`
- `## Verdict`

Requiring 3/4 helps, but is still not enough if proposal templates happen to use those sections. Also `Verdict` is generic enough that some recommendation docs use it.

The first pattern is specific, but the other three are broad. This can cause false positives that switch refinement into critique mode and degrade proposal refinement badly.

**Recommendation:** tighten challenge-mode detection by requiring either:
- a strong frontmatter signal, or
- at least one debate-unique heading plus another supporting marker

For example, only count challenge structure if one of these appears:
- `## Challenger X — Challenges`
- `## Judge`
- `## Judgment`
- `## Concessions`
combined with another debate-specific marker.

Even better: weight markers rather than simple count.

#### D. Premortem/pressure-test headings are also fragile
```python
r'##\s+The Premise Is Wrong',
r'##\s+Counter-Thesis',
r'##\s+Core Assumptions',
r'##\s+My Honest Take',
r'##\s+Blind Spots',
r'##\s+The Real Question',
```

This is highly format-specific:
- case-sensitive
- exact punctuation/spacing dependent
- only H2 headings
- misses slightly edited section names

It may under-detect valid critique docs after one or two refinement passes if headings get normalized or altered.

**Recommendation:** make heading matching case-insensitive and more tolerant:
- anchor to line start with multiline
- support optional punctuation
- perhaps normalize headings before matching

#### E. `if not effective_mode` is okay but semantically mixed
Since `effective_mode` is only ever `None`, `"proposal"`, or `"critique"`, this works. But using `is None` would be clearer and safer if modes ever expand.

### Verdict on mode detection
**Not fully production-ready.** The control flow is good, but the regexes and heuristic markers need hardening before relying on this in mixed document populations.

---

## 2. Will the critique prompts reliably prevent solutioning drift?

### What’s good
The new posture rule is strong and directly addresses the failure mode:

- “Refinement means more precise, not more elaborate”
- explicit “DO NOT add” list
- “failure mode is a critique that becomes a consulting deliverable”

This is much better than generic refinement guidance.

The subsequent-round prompt is especially useful because it explicitly tells the reviewer to remove implementation details if introduced.

### Where it will still fail

#### A. First-round prompt still invites additive behavior
The first-round prompt says:
- strengthen evidence
- add a concrete example or remove it
- make claims specific and testable

That’s reasonable, but models often operationalize “specific and testable” by adding:
- implied recommendations
- metrics
- pilot suggestions
- decision rules

The “do not add” list helps, but there’s still a tension between “specific” and “non-solutioning.” Some models will drift anyway.

#### B. “Preserve the critique’s register” is good but insufficient
Register is not the same as function. A document can keep a critique tone while smuggling in:
- “the company should”
- phased mitigations
- team ownership
- pilot design

The prompt blocks this conceptually, but not structurally.

#### C. No hard negative on imperative recommendation language
The posture bans certain content classes, but not direct recommendation syntax broadly:
- “should”
- “needs to”
- “must now”
- “the next step is”
- “management should”

Some of those are valid inside a critique, but they are also common drift vectors.

#### D. Subsequent-round prompt is stronger than first-round prompt
That’s fine, but it means drift introduced in round 1 may survive if not obvious. Given default critique rounds is 2, there is limited recovery opportunity.

### What would improve reliability
Add a sharper structural rule such as:

- “You may sharpen diagnosis and verdict, but may not introduce new sections whose purpose is recommendation, implementation, sequencing, or ownership.”
- “If a sentence answers ‘what should we do next?’, delete or rewrite it unless it merely sharpens the critique’s conclusion.”
- “Allowed transformations: tighten wording, remove redundancy, sharpen claims, improve causal explanation, strengthen verdict. Disallowed transformations: adding plans, metrics, owners, phases, pilots, governance, or operational next steps.”

That kind of allowed/disallowed transformation framing tends to work better than only examples.

### Verdict on prompt reliability
**Improved but not reliable enough by prompt alone.** The prompts reduce drift substantially, but I would not assume they “reliably prevent” it. The stderr drift warning is a useful backstop, but it’s only observational.

---

## 3. Edge cases in the content heuristic

### False positives

#### Proposal docs with generic headings
As noted, these can trigger critique mode:
- `## Challenges`
- `## Concessions`
- `## Verdict`

Especially in strategy docs, investment memos, or decision records.

#### Documents discussing critique formats
A proposal doc that references debate structure in examples or appendices could accidentally match `debate_id` or section headings.

#### Embedded artifacts
If the document includes pasted excerpts from challenge/judgment docs, the heading count may trigger even though the top-level document is a proposal.

### False negatives

#### Variant heading styles
Will miss:
- H3 instead of H2
- title case differences
- hyphen variants: `Counter Thesis`, `Pre-mortem`, etc.
- numbering: `## 1. Core Assumptions`
- slight wording changes: `My take`, `Honest assessment`, `Real issue`

#### Frontmatter variants
Will miss:
- uppercase keys
- quoted values with different punctuation
- YAML indentation patterns
- `mode: pre-mortem`

#### CRLF and BOM
As above.

### Heuristic quality issue
The current heuristic is a binary threshold:
- `pt_hits >= 3`
- `ch_hits >= 3`

This is simple, but weak for production because all hits are treated equally. Some headings are much more diagnostic than others.

### Better approach
Use a small score-based classifier:

- strong signals:
  - frontmatter mode/phase exact matches
  - `Challenger X — Challenges`
  - `Judge` / `Judgment`
- medium:
  - `Counter-Thesis`
  - `My Honest Take`
  - `Core Assumptions`
- weak:
  - `Challenges`
  - `Verdict`

Then classify as critique only above a score threshold.

If you want minimal code change, at least:
- make regexes case-insensitive
- require one strong signal for challenge mode
- make generic headings weak/non-sufficient

### Verdict on heuristic edge cases
**Current heuristic is too brittle and somewhat too eager on challenge docs.** It needs tuning to avoid proposal-mode regressions.

---

## 4. Regressions to proposal mode

### Good news
Proposal path is mostly preserved:
- explicit `--mode proposal` overrides all detection
- default remains proposal when no signal found
- prompts for proposal mode unchanged
- rounds default still effectively 6 for proposal

So the baseline proposal behavior is mostly intact.

### Main regression risk: false auto-detection
If a proposal doc is misclassified as critique:
- rounds drop from 6 to 2
- prompts shift from “make executable” to “sharpen critique”
- recommendation-preservation logic still runs, but the model is being told not to add operating details
- output quality for proposal docs could degrade significantly

This is the main regression vector.

### Truncation threshold change
```python
truncation_threshold = 0.40 if effective_mode == "critique" else REFINE_TRUNCATION_RATIO
```

This makes sense in principle because critiques may tighten aggressively.

But 40% is permissive. A model could collapse a nuanced critique into a compressed summary and still pass. Since the prompt says “same length or shorter,” a severe compression is often a quality failure even if not a truncation artifact.

This is not a proposal regression directly, but it does lower safety for critique mode.

I’d consider:
- a slightly higher threshold, or
- only using 40% when headings are preserved / structure is intact, or
- warning on very large shrinkage even if not treated as truncation

### Drift detector regression risk
The new drift detector only warns in critique mode, so it shouldn’t affect proposal mode behavior. Good.

### Verdict on proposal regressions
**Low-to-moderate risk, mostly via false critique auto-detection.** Proposal mode itself is not regressed much; detection quality is the gating issue.

---

## Specific code-level concerns

### 1. Frontmatter `if` chain should probably be `elif` semantically
Current code:
```python
if mode_match:
    ...
if not effective_mode:
    phase_match = ...
if not effective_mode:
    debate_id_match = ...
```
This works, but `elif` would better express precedence and reduce mental load.

### 2. Regexes should use `re.IGNORECASE`
Especially for:
- mode
- phase
- debate_id
- headings
- drift detection already does this, which is good

### 3. Heading matches should be multiline anchored
Current patterns can match anywhere. For headings, use `(?m)^##\s+...`
That reduces accidental matches in code blocks or quoted text.

### 4. Debate ID regex should be bounded
Current:
```python
.*(?:challenge|judgment|pressure-test|premortem)
```
Can match substrings accidentally. Add boundaries/normalized aliases.

### 5. Critique default rounds = 2 is reasonable but maybe too low
If round 1 drifts and round 2 only partially corrects, you’re done. Consider 3 if latency/cost allows. Not a blocker, but worth discussing.

---

## Suggested minimal fixes before shipping

### Must-fix
1. **Harden frontmatter parsing**
   - support BOM and CRLF
   - case-insensitive key/value matching
   - include common aliases like `pre-mortem`, `judgement`

2. **Reduce false positives in challenge heuristic**
   - do not let `Challenges + Concessions + Verdict` alone trigger critique mode
   - require at least one debate-specific heading/signal

3. **Anchor heading regexes to actual headings**
   - multiline line-start anchors
   - case-insensitive

4. **Strengthen critique prompt with allowed/disallowed transformation rule**
   - explicitly ban new recommendation/implementation sections
   - explicitly ban sentences that answer “what should we do next?”

### Should-fix
5. **Log when defaulting to proposal after failed/no detection**
   - useful for debugging surprising behavior

6. **Add tests for representative fixtures**
   At minimum:
   - proposal doc with `## Challenges`, `## Concessions`, `## Verdict` → should stay proposal
   - pressure-test doc with frontmatter `mode: pre-mortem` → critique
   - challenge doc with `phase: judgment` → critique
   - critique doc with CRLF frontmatter → critique
   - critique doc with lowercase/variant headings → critique if enough signals
   - explicit `--mode proposal` on critique doc → proposal

7. **Consider warning on large non-truncated shrinkage in critique mode**
   - e.g. below 60% warn, below 40% treat as truncation

---

## Bottom line
**Recommendation: not quite production-ready yet.**

The architectural move is right, and the prompt split is a strong improvement. But I’d want at least one more pass on detection robustness before rollout, because the primary regression risk is silent misclassification of proposal docs into critique mode.

If you want a concise go/no-go:

- **Prompt design:** mostly good, but not sufficient alone
- **Mode detection:** promising, but too brittle/eager for prod
- **Heuristic edge cases:** needs tightening
- **Proposal regressions:** acceptable only if detection false positives are reduced

If useful, I can turn this into a concrete patch suggestion with revised regexes and a safer scoring heuristic.

---
{"status": "ok", "reviewers": 3, "mapping": {"A": "gpt-5.4", "B": "claude-opus-4-6", "C": "gemini-3.1-pro"}}

## Reviewer B

# Production Readiness Review

## Overall Assessment

This is a well-structured addition that addresses a real problem (critique documents drifting into consulting deliverables during refinement). The layered detection, dedicated prompts, and drift monitoring are thoughtfully designed. There are several issues worth addressing before shipping.

---

## Mode Detection Logic

### Frontmatter parsing is fragile

The regex `r'^---\s*\n(.*?)\n---'` only matches frontmatter at the very start of the file. This is correct for YAML frontmatter convention, but:

1. **No tolerance for leading whitespace or BOM.** A UTF-8 BOM (`\xef\xbb\xbf`) or a single blank line before `---` will cause the match to fail silently, falling through to the content heuristic. Consider stripping or `.lstrip('\ufeff')` before matching.

2. **No tolerance for `---\n` vs `---\r\n`.** On Windows-origin files, `\r\n` line endings will leave `\r` in the captured group, potentially breaking the inner `re.MULTILINE` matches since `$` won't match before `\r`. Consider normalizing line endings or using `\r?\n` in the patterns.

3. **The frontmatter value regex doesn't handle trailing comments or extra whitespace robustly.** `mode: pressure-test # generated by debate` would fail to match because the regex expects end-of-line after the optional quote. This is probably fine for machine-generated frontmatter, but worth documenting.

### Content heuristic thresholds

The threshold of `>= 3` hits is reasonable but has an edge case worth considering:

- **A proposal document that discusses pressure-testing** could contain headings like `## Core Assumptions`, `## Blind Spots`, and `## My Honest Take` as sections within a proposal. Three matches out of six is a 50% hit rate on a fairly generic heading list. `"## Core Assumptions"` in particular is common in proposal documents.

- **Mitigation:** The auto-detection prints a `NOTE` to stderr, and `--mode proposal` overrides it. This is acceptable, but I'd consider either (a) raising the threshold to 4, or (b) requiring at least one "strong signal" heading (e.g., `Counter-Thesis` or `The Premise Is Wrong`) alongside the weaker ones.

### The `debate_id` heuristic is very loose

```python
r'^debate_id:\s*.*(?:challenge|judgment|pressure-test|premortem)'
```

This matches `debate_id: my-proposal-challenge-response` or `debate_id: judgment-day-proposal`. The substring match on `challenge` and `judgment` could false-positive on debate IDs that happen to contain these common English words. Consider requiring these as delimited tokens (e.g., `(?:^|[-_])(?:challenge|judgment)(?:$|[-_])`).

---

## Critique Prompts and Solutioning Drift Prevention

### The prompts are strong

The `DO NOT` list is specific and actionable. The meta-instruction ("The failure mode is a critique that becomes a consulting deliverable") is the kind of concrete framing that LLMs respond well to. The subsequent-round prompt explicitly instructs removal of drift introduced by previous rounds — this is a good feedback loop.

### Potential gap: the prompts don't address length creep explicitly

The `CRITIQUE_REFINE_POSTURE_RULE` says "Same length or shorter" in the output format section, but the posture rule itself doesn't state a length constraint. Models tend to follow the last instruction they see, so this is probably fine, but consider reinforcing in the posture rule: "If the revised critique is longer than the input, something has gone wrong."

### The drift detection is advisory-only

The drift patterns check is non-blocking (prints a NOTE). This is the right call for v1 — blocking would be too aggressive. But consider: should there be a `--strict` flag that fails the round (similar to truncation handling) if drift is detected? This would be useful in CI pipelines.

---

## Truncation Threshold Change

```python
truncation_threshold = 0.40 if effective_mode == "critique" else REFINE_TRUNCATION_RATIO
```

This is a significant change — dropping from whatever `REFINE_TRUNCATION_RATIO` is (presumably ~0.6-0.7) to 0.40. The rationale ("critique mode expects shorter output") makes sense, but:

- **A critique that shrinks to 40% of its input in a single round is a large change.** If the input is already tight, this could mask genuine truncation. Consider whether 0.50 is a safer threshold.
- **The threshold is per-round, not cumulative.** Two rounds each shrinking to 45% would produce a document at ~20% of original size without triggering any warning. Is that intended?

---

## Regressions to Proposal Mode

### `--rounds` default change

```python
rf.add_argument("--rounds", type=int, default=None, ...)
```

Previously `default=6`. Now `default=None`, resolved later:

```python
if rounds is None:
    rounds = 2 if effective_mode == "critique" else 6
```

This preserves the proposal-mode default of 6. **No regression here**, but any code that previously relied on `args.rounds` being non-None before mode detection would break. I don't see such code in the diff, but worth verifying in the full codebase.

### Prompt selection is correctly gated

```python
if effective_mode == "critique":
    ...
else:
    ...  # existing proposal prompts
```

The `else` branch is identical to the previous code. **No regression.**

### Recommendation slot preservation

The existing recommendation slot preservation logic (visible at the bottom of the diff) runs after the new drift detection block. Since it's not gated on mode, it will still run for critique mode. This is probably harmless (critiques likely don't have recommendation slots to preserve), but it's wasted computation. Consider gating it:

```python
if effective_mode == "proposal":
    # recommendation slot preservation logic
```

---

## Minor Issues

1. **The `effective_mode` variable is used before the `if effective_mode is None: effective_mode = "proposal"` fallback in the print statement.** Specifically:
   ```python
   if effective_mode and detection_reason:
       print(f"NOTE: Auto-detected critique mode ...")
   if effective_mode is None:
       effective_mode = "proposal"
   ```
   This is correct — if `effective_mode` is set, it's always `"critique"` at that point, and the print only fires when both are truthy. But the logic would be clearer if the fallback were in an `else` block.

2. **No test coverage is visible in this diff.** The mode detection logic has enough branches (frontmatter × 3 paths, content heuristic × 2 heading sets, debate_id, fallback) that unit tests would be valuable. At minimum: test that a plain proposal document doesn't trigger critique mode, and that each frontmatter signal correctly triggers it.

3. **The drift pattern for timelines** — `r'\b\d+[\s-]*day\s+(?:pilot|timeline|plan|window)\b'` — won't match "90-day" because `\b` before `\d` requires a non-word character, and the hyphen in "90-day" is fine, but it won't match "a 3-month pilot" or "Q2 timeline". Consider whether these are worth catching.

---

## Summary

| Area | Verdict |
|------|---------|
| Mode detection correctness | Good with caveats (BOM, line endings, loose `debate_id` match) |
| Critique prompts | Strong; well-designed anti-drift instructions |
| Drift detection | Appropriate for v1; advisory-only is correct |
| Truncation threshold | 0.40 may be too aggressive; consider 0.50 |
| Proposal mode regressions | None found |
| Test coverage | Missing; should block merge |

**Recommendation:** Address the BOM/line-ending fragility, tighten the `debate_id` regex, add unit tests for mode detection, and consider bumping the truncation threshold to 0.50. The rest is ship-ready.

---

## Reviewer C

This diff looks solid overall and successfully introduces a dedicated "critique" refinement mode to handle strategic reviews without drifting into solutioning. 

Here is a review focusing on your specific areas of interest:

### 1. Correctness of Mode Detection Logic
- **Execution Order:** Checking `if effective_mode is None:` at each layer correctly prioritizes the explicit CLI flag, then frontmatter, then content heuristics.
- **Frontmatter regex:** The regex `r'^---\s*\n(.*?)\n---'` correctly anchors to the start of the document and handles multiline YAML safely via `re.DOTALL`.
- **Default fallback:** The fallback `if effective_mode is None: effective_mode = "proposal"` correctly ensures existing behaviors remain intact if detection fails.

### 2. Critique Prompts & Solutioning Drift
- **Guardrails:** The `CRITIQUE_REFINE_POSTURE_RULE` is highly explicit. By listing exact anti-patterns (owner assignments, timelines, frameworks, matrices, consulting deliverables) and hedge words, it sets a very strong boundary against solutioning drift.
- **Subsequent rounds:** `CRITIQUE_REFINE_SUBSEQUENT_ROUND_PROMPT` explicitly instructs the model to strip out any implementation details or operating recommendations introduced by the previous reviewer. This is an excellent failsafe for LLM "creeping helpfulness".
- **Drift logging:** Surfacing a warning when drift patterns (e.g., `Owner assignment`, `Phased plan`) are found in the output is a great non-blocking observability feature.

### 3. Edge Cases in Content Heuristics
- **Heading Regex:** The heuristic searches for headings like `r'##\s+Counter-Thesis'`. Since it lacks the `^` anchor, it will match anywhere on a line. This is generally safe and avoids issues with leading whitespace/markdown formatting.
- **Thresholds:** Requiring 3 out of 6 (`pt_hits`) or 3 out of 4 (`ch_hits`) is a strict enough threshold that regular proposals are highly unlikely to trigger a false positive. 
- *Minor edge case:* If a standard proposal mentions these phrases *in the body text* preceded by `## ` (e.g., inside a code block or quote), it could theoretically trip the heuristic, but the 3-hit threshold mitigates this significantly.

### 4. Regressions to Proposal Mode
- **No regressions spotted:** When `effective_mode == "proposal"` (which defaults cleanly), the script accurately routes back to the original `REFINE_FIRST_ROUND_PROMPT`, the original 6-round default, and the original truncation thresholds. 
- **Truncation thresholds:** Splitting `truncation_threshold = 0.40 if effective_mode == "critique" else REFINE_TRUNCATION_RATIO` ensures that critiques (which naturally tighten and shorten) don't repeatedly trip the truncation circuit breaker meant for expanding proposals.

**Conclusion:** Production ready. The guardrails against solutioning drift are robust, the detection logic degrades gracefully, and existing proposal pathways are well protected.

---


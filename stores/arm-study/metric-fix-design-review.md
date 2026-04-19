Calling model-1...
Calling model-2...
  model-2 (gemini-3.1-pro): 18.6s
  model-1 (gpt-5.4): 70.9s
## Reviewer A

Here is the pressure-test analysis of your design choices, categorized by severity (Structural vs. Minor) and rated accordingly.

### 1. Quality weights (judge-graded substantive score)
**Rating: TUNE**
*   **Problem Type:** Minor (Calibration / Prompting)
*   **Analysis:** The 3:1:0.5 ratio encourages high-volume "marginal" generation. More critically, a -1 penalty for "harmful" does not reflect the asymmetric cost of destructive advice; it should be heavily penalized (e.g., -3 or -5). The empirical observation that 100% of items land in substantive/marginal indicates a rubric failure—the judge LLM likely lacks clear, strict definitions for "superficial" or "harmful," essentially turning a 4-point scale into a binary one.

### 2. FALSIFIED source classifier (post-hoc regex)
**Rating: REDESIGN**
*   **Problem Type:** Structural (Systematic Bias / False Positives)
*   **Analysis:** The "mixed source → caught_misquote" heuristic is a massive vulnerability. If a challenger uncritically repeats a false premise from the proposal, the verifier will cite both sources, and your classifier will incorrectly reward the arm for a "caught misquote." The extreme empirical discrepancy (62.2% vs 97.4% accuracy) strongly suggests this regex is systematically failing to capture true hallucination/misattribution dynamics. You need an LLM judge to classify *why* both sources are cited (critique vs. blind repetition), not a regex.

### 3. Token-coverage matcher (miss_rate)
**Rating: REDESIGN**
*   **Problem Type:** Structural (Systematic Bias)
*   **Analysis:** Token overlap heavily penalizes paraphrasing. Because Arm B uses models like GPT-5.4 and Gemini, they will naturally use different vocabulary than the Claude-generated reference tokens, leading to a high false-negative rate for Arm B. Furthermore, Claude-Sonnet generating the tokens inherently gives Arm A (Claude-Opus) a home-field advantage due to shared pre-training and tokenization distributions. You must replace this with a semantic similarity matcher (e.g., LLM cross-encoder or embeddings).

### 4. Retrospective landing-rate formula
**Rating: TUNE**
*   **Problem Type:** Minor (Data Comparability)
*   **Analysis:** 0.5 for partial is standard and defensible. However, calculating aggregates when only 1-in-3 proposals has a real `plan.md` introduces severe noise. A `plan.md` represents a high-bar commitment, whereas a `judgment.md` is a lower-bar acknowledgement. Mixing these denominators makes the aggregate score heavily skewed by the specific proposals rather than the arms. Consider standardizing the target artifact or reporting landing rates separately by artifact type.

### 5. Verdict promotion thresholds
**Rating: TUNE**
*   **Problem Type:** Minor (Scaling / Calibration)
*   **Analysis:** Absolute thresholds (5.0 substantive points, 2 absolute harmful items) are mathematically brittle. An arm that is simply more verbose will easily hit the 5.0 delta, and any arm will inevitably trip the 2-item harmful cap as `n` scales to 10. These *must* be converted to rates or percentages (e.g., Substantive-score delta ≥ 15% of baseline; Harmful regression ≤ 5% of total items) so the statistical logic holds regardless of sample size or output volume.

### 6. Overall verdict composition
**Rating: TUNE**
*   **Problem Type:** Minor (Signal Loss)
*   **Analysis:** Requiring unanimous agreement among voting dims to avoid a "mixed-directional" label is too strict, especially with small `n`. A 3-to-1 vote is a clear signal, not a mixed one. Additionally, treating judge-graded subjective nuance equal to ground-truthed catch rates risks letting LLM-as-a-judge biases overrule objective accuracy. Implement a weighted supermajority system (e.g., verifier-backed dimensions get 1.5x votes, requires 75% vote-share to declare a directional win).

### 7. Independent issue-discoverer model choice
**Rating: REDESIGN**
*   **Problem Type:** Structural (Systematic Bias)
*   **Analysis:** Using a Claude model to define the "ground truth" reference issues while testing a Claude-only arm against a multi-model arm introduces severe bias. Claude-Sonnet will focus on the exact types of structural/logical gaps that Claude-Opus is fine-tuned to care about, implicitly penalizing Arm B for focusing on things Claude doesn't prioritize. To fix this, the reference issue generator must either be an ensemble of different models (Claude + GPT + Gemini) or a completely neutral third-party model not heavily represented in either arm.

---

## Reviewer B

## 1. Quality weights  
**Rating: TUNE**  
**Problem type: mostly MINOR, with one structural risk if used as a primary winner signal**

### What’s defensible
The basic ordinal intent is reasonable: substantive > marginal > superficial > harmful. A weighted sum is a practical reduction.

### Main concerns

#### A. The current weights reward volume more than concentration
Yes, `3:1:0.5:-1` can favor an arm that emits many marginal points over one that emits fewer but better points.

Example:
- Arm X: 4 substantive = 12
- Arm Y: 2 substantive + 8 marginal = 14

If judges are somewhat generous with “marginal,” Y can win despite being less useful in practice. That is a real bias toward verbosity / shotgun reviewing.

This becomes more pronounced if one arm naturally decomposes critiques into many small items.

**Why this matters structurally:** if itemization style differs systematically by arm, the metric is not just noisy; it is partly measuring segmentation strategy rather than quality.

#### B. Harmful = -1 likely underprices downside
If harmful really means misleading, fabricated, or decision-degrading content, then `-1` is weak relative to `+3` for substantive. One substantive can cancel three harmful items under your current scheme only partially; but operationally, a few harmful items may dominate user trust and downstream risk.

That said, making harmful `-3` inside the same linear score may overcorrect if harmful is rare and separately guardrailed. Better to:
- keep a quality score for usefulness, and
- treat harmful as a separate safety gate/guardrail.

#### C. Rubric usage looks suspect
If in n=3, **0% superficial and 0% harmful**, I would not assume the outputs are truly that clean. More likely:
1. the rubric definitions are too vague,
2. judges are reluctant to use negative categories,
3. the prompt implicitly frames all extracted items as plausible critiques, or
4. the task setup filters low-quality items before judging.

This is a calibration warning. A category never used is not contributing information.

### Recommendations
1. **Normalize by item count as a companion metric**  
   Report:
   - total weighted score
   - weighted score per item
   - substantive share  
   This reduces style bias.

2. **Collapse or sharpen the low-end categories**
   If judges do not reliably distinguish superficial from marginal, either:
   - remove superficial, or
   - provide anchored examples that make it behaviorally distinct.

3. **Separate harmful from utility**
   Don’t rely on `-1` inside the same sum to handle safety. Use:
   - utility score excluding harmful, plus
   - harmful-rate guardrail.

4. **Run a category-use audit**
   On a sample, manually relabel 50–100 judged items and inspect confusion:
   - marginal vs superficial
   - marginal vs harmful

### Direct answers
- **Is 3:1:0.5:-1 defensible?** Barely, as a first pass; but it has a verbosity bias and should not be trusted alone.
- **Should harmful be more negative?** Probably not only by changing the weight; better as a separate blocker/guardrail. If kept in-score, `-2` is more plausible than `-1`.
- **Are judges using superficial/harmful?** Current evidence suggests rubric failure or prompt-induced compression.

---

## 2. FALSIFIED source classifier  
**Rating: REDESIGN**  
**Problem type: STRUCTURAL**

This is the biggest structural problem in the setup.

### Why
You are inferring a semantic distinction from a coarse source field that was not designed for this classifier. The mapping:

- Challenger only → hallucination
- Proposal only or mixed → caught misquote

is too aggressive and likely systematically biased.

### Core failure modes

#### A. “Mixed source” is ambiguous, not automatically good
`Proposal + Challenger` could mean at least four different things:
1. challenger correctly identified and quoted a false proposal claim,
2. challenger repeated the false claim while critiquing it,
3. challenger independently made the same false claim,
4. verifier cited both because lexical overlap made attribution messy.

Only (1) is clearly “caught_misquote.” The heuristic collapses all four into “good.”

#### B. “Challenger only” is not always hallucination
A claim can be sourced only to Challenger because:
- the verifier failed retrieval on the proposal span,
- the challenger paraphrased a proposal error in transformed language,
- the proposal support exists but source extraction missed it,
- the challenger made a legitimate inferential claim not explicitly textual in the proposal.

So “Challenger only” is not a clean hallucination label.

#### C. Differential attribution bias across arms is very plausible
The empirical gap—Arm A `17 hallucinations + 6 caught-misquotes` vs Arm B `1 + 7`—is suspicious enough to treat as likely classifier artifact until manually validated.

A likely mechanism:
- Arm A may paraphrase/transform critique more aggressively, causing verifier attribution to land on Challenger-only.
- Arm B may use more extractive phrasing or quote proposal text, causing mixed sourcing and thus a “good” label.

That is a **systematic bias tied to style**, not truth.

### What to do instead

#### Preferred redesign
Have the verifier output an explicit per-claim label:
- **proposal-error-correctly-identified**
- **challenger-fabrication**
- **ambiguous/insufficient-evidence**
- **challenger-inference-not-text-grounded**
- optionally: **proposal claim repeated without clear challenge**

Then score from that direct label, not post-hoc regex.

#### Minimal salvage if you cannot redesign fully
Treat **mixed source as ambiguous**, not good.
Recode:
- Proposal only → caught_misquote
- Challenger only → probable hallucination
- Mixed → unclear/needs adjudication

This will reduce false-good inflation.

#### Calibration audit
Manually review a stratified sample of:
- 20 Challenger-only
- 20 Mixed
for each arm. Estimate confusion matrix against human labels.

If mixed cases are <80% true caught-misquotes, the current heuristic is not defensible.

### Direct answers
- **Is mixed→caught_misquote defensible?** Not as a default. Too much semantic compression.
- **What fraction of mixed cases are misclassified?** Unknown, but plausibly large enough to matter materially.
- **Is the 62.2% vs 97.4% split suspicious?** Yes. Very suspicious. Especially with n=3.

---

## 3. Token-coverage matcher (miss_rate)  
**Rating: TUNE, bordering on REDESIGN if used heavily**  
**Problem type: mix of STRUCTURAL and MINOR**

### What works
For a cheap, transparent matcher, token coverage is understandable and reproducible. Good as a weak proxy.

### Main concerns

#### A. It is recall-hostile to paraphrase
This metric is much more a lexical recall test than a semantic coverage test. It will miss:
- synonyms,
- abstraction shifts,
- causal reframings,
- negated restatements,
- longer-form explanations with different vocabulary.

So yes, false negatives can be substantial.

#### B. Substring matching is brittle and can create false positives
Case-insensitive substring can spuriously match:
- partial morphemes,
- unrelated compounds,
- contextless mentions.

That can inflate catches for generic tokens.

#### C. Token choice can align with one arm’s style
Yes, if Sonnet generates the reference issues and token sets, there is some risk those key tokens reflect Claude-family phrasing. Since Arm A is Claude-only, this could inflate its apparent coverage.

This is a real structural concern, though likely smaller than section 2 unless token phrasing is very model-specific.

### 60% threshold
60% is arbitrary. With 2-token issue lists, 60% effectively means both tokens if rounded up one way, or 1/2 if rounded another depending on implementation. With 5-token lists, it means 3/5. So the threshold behaves inconsistently across issue lengths.

That is an underappreciated edge case.

### Recommendations

#### Better rule
Use an issue-level matcher with:
- exact token match,
- stem/lemma match,
- synonym list / manually expanded aliases,
- and a short LLM semantic adjudication only for borderline cases.

Even a two-stage pipeline would be much better:
1. lexical candidate retrieval,
2. LLM binary “same issue?” decision with blinded arm text snippets.

#### At minimum
1. Fix token-list length to a constant size, or
2. define required matches explicitly:
   - 2-token issue: 2/2
   - 3-token issue: 2/3
   - 4–5-token issue: 3/4 or 3/5
3. avoid substring; use tokenized word-boundary matching
4. add aliases for obvious paraphrases

### Sensitivity
You should absolutely run 50% / 60% / 75% sensitivity. But more important is whether **per-dimension verdicts** flip, not just raw catches.

### Estimating false-negative rate without semantic matcher
You can estimate it with human audit:
- sample all “missed” reference issues for each arm,
- have a blinded rater check whether the issue was actually caught semantically,
- compute FN rate by arm.

That will also test style bias.

### Direct answers
- **Would 50% or 75% flip verdicts?** Must be checked empirically; likely yes if issue token counts are short.
- **False-negative rate?** Potentially high; cannot be trusted without audit.
- **Could Sonnet token choices align with Arm A?** Yes, plausible.

---

## 4. Retrospective landing-rate formula  
**Rating: TUNE**  
**Problem type: mostly MINOR, with comparability concerns**

### What’s reasonable
`(landed + 0.5 * partial) / total` is a conventional placeholder if you need a scalar. The bigger issue is not 0.5 itself; it is heterogeneity in what “landed” means across artifacts.

### Main concerns

#### A. PARTIAL = 0.5 is arbitrary but not fatal
There is little strong prior that 0.5 is “correct.” In review-effectiveness settings, partial adoption is often treated ordinally, not cardinally. So 0.5 is a convenience choice, not an evidence-backed constant.

This is tunable, not a deep flaw.

#### B. Artifact priority creates construct drift
Scoring against `plan > refined > judgment` is not measuring one thing consistently.

- **plan** measures operational commitment
- **refined** measures textual incorporation
- **judgment** measures acceptance/decision-level acknowledgment

These are related but not equivalent. An item can:
- land in judgment but not plan because it changed decision boundaries,
- land in refined but not judgment because it was folded in silently,
- land in plan because of workflow requirements rather than genuine influence.

So aggregating them as one landing-rate introduces comparability noise.

#### C. Cross-proposal comparability is weak with fallback artifacts
If only 1/3 proposals has a real plan, your landing metric is not apples-to-apples across proposals. Proposal-level rates may reflect artifact availability more than challenge effectiveness.

This is the biggest issue in this section.

### Recommendations
1. **Split the measure**
   Report separately:
   - decision landing (judgment)
   - artifact incorporation (refined)
   - execution commitment (plan)

2. **Only aggregate within the same artifact type**, or at least stratify by artifact type.

3. **Sensitivity on PARTIAL**
   Recompute with 0.25 / 0.5 / 0.75 and see if verdicts flip.

4. **Consider proposal-level normalization**
   Average landing-rate within proposal first, then across proposals, so proposals with richer artifact structures do not dominate.

### Direct answers
- **Is 0.5 defensible?** As a placeholder, yes; not evidence-based.
- **Is plan > refined > judgment defensible?** Only if you explicitly define “landing” as highest-evidence operational uptake. But it changes the construct.
- **Comparable across proposals?** Not fully, given fallback heterogeneity.

---

## 5. Verdict promotion thresholds  
**Rating: REDESIGN**  
**Problem type: STRUCTURAL**

The thresholds do not scale coherently with sample size, item volume, or uncertainty.

### Main concerns

#### A. Fixed pp thresholds ignore variance and n
A 5pp delta means very different things at:
- n=3 proposals,
- n=10 proposals,
- 40 total claims,
- 300 total claims.

This can produce both false positives and false negatives depending on denominator size.

#### B. Absolute substantive-score delta is exposure-dependent
A 5-point weighted-score delta is easier to achieve when an arm emits more items. Since item count itself varies by arm, this threshold structurally advantages higher-output arms.

This is a real design problem.

#### C. Harmful cap as absolute count is not scale-free
A cap of 2 harmful items means:
- huge at low volume,
- lenient at high volume.

This is not coherent across n=3 to n=10, as you note.

### What to do instead

#### Replace fixed thresholds with uncertainty-aware rules
Use one of:
- confidence intervals / bootstrap intervals on arm deltas,
- Bayesian posterior probability of superiority,
- permutation test on paired proposal-level differences.

Since proposals are shared across arms, a **paired bootstrap/permutation** is especially suitable.

#### Define effect-size floors separately from confidence
Example:
- directional if paired delta > practical floor and uncertainty excludes 0 weakly
- confident if stronger floor and tighter interval

This is better than MIN_SAMPLE fixed cutoffs alone.

#### Make score thresholds relative or normalized
For substantive score:
- use average weighted score per judged item, or
- substantive-score density per 1k tokens / per challenge item, or
- proposal-level mean delta.

#### Harmful should be rate-based + absolute safety stop
Use both:
- harmful rate regression ≤ X pp
- and absolute count ceiling only as an emergency stop for very small studies

### Direct answers
- **Should thresholds scale with sample size?** Yes, absolutely.
- **Should 5.0 score delta be relative?** Yes, or normalized per item/proposal.
- **Is harmful cap of 2 absolute items defensible?** Not as the sole rule.

---

## 6. Overall verdict composition  
**Rating: TUNE**  
**Problem type: one structural concern, otherwise policy choice**

### What’s good
The abstention logic is conservative. That is a feature in a noisy early study.

### Main concerns

#### A. Equal vote weight ignores evidence quality
Yes, verifier-grounded catch_rate and judge-graded nuance_caught should not automatically count equally if one is materially more reliable.

If reliability differs, equal voting can let noisier dimensions veto cleaner ones.

This is a structural concern if the judged dimensions are known to be less calibrated.

#### B. Requiring unanimity among voting dims is too brittle
If 3 dimensions strongly favor Arm B and 1 weak dimension favors Arm A, “mixed-directional” may understate the practical result. That rule has a strong anti-conclusion bias.

That may be acceptable if your goal is extreme caution, but it should be named as such.

#### C. Low voting resolution at n=3
With only ~4 active voting dimensions and high proposal noise, the final vote is coarse. One flaky dimension can swing the label to mixed.

### Recommendations
1. **Weight dimensions by evidential strength**
   For example:
   - verifier-grounded dims: weight 2
   - judge-only dims: weight 1  
   Or more formally, weight by validated inter-rater/model reliability.

2. **Use a majority rule with veto only for safety**
   Example:
   - overall directional if weighted majority favors one arm and no hard guardrail trips
   - mixed only if evidence is genuinely split or uncertainty overlaps heavily

3. **Report scorecard, not just label**
   The textual summary should say:
   - “3 dimensions favor B, 1 favors A, strongest evidence from catch_rate”
   even if headline remains mixed.

### Direct answers
- **Should ground-truthed dims be weighted higher?** Yes.
- **Is mixed-directional right for 3 strong vs 1 weak?** Usually no; that is overly brittle.
- **Is voting resolution sufficient at n=3?** Barely.

---

## 7. Independent issue-discoverer model choice  
**Rating: TUNE**  
**Problem type: plausible STRUCTURAL bias, but empirically testable**

### Main concern
The reference issue set is not ground truth; it is model-generated ground truth proxy. Since Sonnet is both:
- issue discoverer, and
- verifier family-adjacent,
and Arm A is Claude-only, there is a plausible family-style alignment risk.

### How serious?
Less severe than the source-classifier problem, because:
- the reference model is only generating issues, not directly assigning arm labels,
- tool access may anchor it to proposal reality.

But yes, if issue framing/tokens are Claude-like, Arm A may match them more naturally.

### Additional concern
Any model with tool access may produce a somewhat different issue frontier. So the issue set is model-dependent. That does not make it useless, but it means you should not overclaim objectivity.

### Recommendations
1. **Use multiple discoverers**
   Generate reference issues with:
   - Sonnet
   - GPT-5.4
   - maybe one additional non-Claude model  
   Then dedupe/union/intersect with human adjudication.

2. **Blind tokenization / canonicalization**
   Have a separate process convert issue descriptions into model-neutral canonical issue labels and alias sets.

3. **Measure discoverer sensitivity**
   Recompute miss_rate using different issue generators and see if arm ranking flips.

If the winner depends on discoverer family, that dimension is not stable enough for promotion decisions.

### Direct answers
- **Is Claude-family issue generation independent enough?** Not fully.
- **Would non-Claude change the issue list?** Quite possibly, especially at margins.
- **Does tool access make issue set model-dependent?** Yes; tools reduce hallucination, not model dependence.

---

# Bottom-line summary

## ACCEPT / TUNE / REDESIGN
1. **Quality weights** — **TUNE**  
2. **FALSIFIED source classifier** — **REDESIGN**  
3. **Token-coverage matcher** — **TUNE**  
4. **Retrospective landing-rate formula** — **TUNE**  
5. **Verdict promotion thresholds** — **REDESIGN**  
6. **Overall verdict composition** — **TUNE**  
7. **Independent issue-discoverer choice** — **TUNE**

## Structural problems most likely to bias verdicts
The highest-risk structural issues are:

1. **Section 2: FALSIFIED source classifier**  
   Very likely to confound style/attribution with hallucination vs caught-misquote.

2. **Section 5: Fixed promotion thresholds**  
   Not scale-aware; mixes absolute and rate thresholds inconsistently.

3. **Section 3 / 7 combination: miss_rate reference generation + lexical matching**  
   Model-family issue framing plus token overlap can create subtle alignment bias.

## Minor/tunable problems
- exact quality weights,
- PARTIAL = 0.5,
- unanimity-vs-majority overall voting,
- artifact priority order.

## If you only change three things before trusting results
1. **Redesign the FALSIFIED classifier with explicit verifier labels.**
2. **Replace fixed thresholds with paired uncertainty-aware decision rules.**
3. **Audit miss_rate with semantic/manual checks and multi-model issue generation.**

If you want, I can turn this into a tighter “study-risk memo” with:
- must-fix before any arm promotion,
- should-fix before publication,
- nice-to-have calibration analyses.

---
{"status": "ok", "reviewers": 2, "mapping": {"A": "gemini-3.1-pro", "B": "gpt-5.4"}}


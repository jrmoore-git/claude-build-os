Calling model-1...
Calling model-2...
  model-2 (gemini-3.1-pro): 38.6s
  model-1 (gpt-5.4): 44.8s
## Reviewer A

Overall stack: REVISE

1. Category: contract-bug
   Severity: MATERIAL
   Location: scripts/arm_study_verdict.py:_aggregate_judge_dim / _per_dim_verdict_judge_graded
   What's wrong: The harmful-item guardrail is implemented with the wrong threshold semantics and only blocks when the winner’s absolute harmful count is at least 2, instead of blocking any regression greater than 2 harmful items.
   Evidence: `HARMFUL_REGRESSION_ABSOLUTE_MAX = 2` and `if winner_agg["harmful_total"] > loser_agg["harmful_total"] and winner_agg["harmful_total"] >= HARMFUL_REGRESSION_ABSOLUTE_MAX:`
   Suggested fix: Compare the difference `winner_harmful_total - loser_harmful_total` to the preregistered cap and block only when that regression exceeds 2, e.g. `> 2` if “may not exceed 2” is the rule.

2. Category: contract-bug
   Severity: MATERIAL
   Location: scripts/arm_study_retrospective.py:score_run
   What's wrong: Top-level retrospective status is always written as `"scored"` even when both arms failed or no arm has usable scoring output, which violates the consumer contract and can mislead the verdict layer.
   Evidence: After per-arm loop, the code unconditionally does `out["status"] = "scored"; out["per_arm"] = per_arm` regardless of whether any `per_arm[*]["status"] == "scored"`.
   Suggested fix: Set top-level status based on actual arm outcomes, e.g. `"scored"` only if at least one arm is scored, otherwise `"not-scorable"`/`"failed"` with a reason.

3. Category: silent-failure
   Severity: MATERIAL
   Location: scripts/arm_study_verdict.py:_per_dim_verdict_plan_quality
   What's wrong: The plan-quality aggregator can silently declare a directional result when only one arm contributed data on a proposal, because it pools arm totals independently instead of requiring paired arm scoring per run.
   Evidence: In the per-run loop, each arm is accumulated independently with `if arm_retro.get("status") != "scored": continue`, and `any_scored = True` is set if either arm scores; there is no requirement that both arms are scored for the same retrospective artifact.
   Suggested fix: Aggregate only runs where both arms have `status == "scored"` so the comparison remains paired and unbiased.

4. Category: silent-failure
   Severity: MATERIAL
   Location: scripts/arm_study_verdict.py:_per_dim_verdict_miss_rate
   What's wrong: The miss-rate verdict can silently compare unpaired proposal coverage because totals are pooled independently by arm even when reference coverage exists for only one arm on a run.
   Evidence: The code loops `for arm in ("arm-a", "arm-b")` and accumulates any arm with `reference_coverage.status == "scored"`; there is no per-proposal pairing check before adding counts.
   Suggested fix: Only include proposals where both arms have scored `reference_coverage`, or track and surface asymmetric availability as not-scorable.

5. Category: methodology-leak
   Severity: MATERIAL
   Location: scripts/arm_study_verdict.py:_aggregate_verifier / _per_dim_verdict_verifier
   What's wrong: The catch_rate primary verdict is still thresholded on raw/classified accuracy delta rather than the preregistered quality-weighted accuracy delta, so quality weighting only acts as a tie-break/mixedness check instead of the actual primary metric.
   Evidence: `delta = b["accuracy"] - a["accuracy"]` and `if abs(delta) < PRIMARY_ACCURACY_DELTA_PP:` are used for winner selection, while `weighted_accuracy` is checked only later for alignment.
   Suggested fix: Use `weighted_accuracy` as the primary catch_rate metric and apply the 5pp threshold to the weighted metric, while surfacing raw/classified accuracy as diagnostics and guardrails.

6. Category: methodology-leak
   Severity: MATERIAL
   Location: scripts/arm_study_verdict.py:_aggregate_judge_dim / _per_dim_verdict_judge_graded
   What's wrong: Judge-graded dimensions are thresholded on total weighted score summed across proposals, which scales mechanically with sample count and proposal verbosity rather than on a normalized per-proposal/per-judge substantive signal.
   Evidence: `weighted_score_total = sum(weighted_scores)` and verdict uses `delta = b["weighted_score_total"] - a["weighted_score_total"]` against fixed threshold `SUBSTANTIVE_DELTA_MIN = 5.0`.
   Suggested fix: Use a normalized metric such as mean paired per-proposal delta or mean-per-proposal weighted score, then apply the preregistered 5.0 threshold to that normalized quantity.

7. Category: methodology-leak
   Severity: MATERIAL
   Location: scripts/arm_study_miss_discoverer.py:match_reference_issues
   What's wrong: The token matcher uses raw substring containment, which structurally favors arms that reuse discoverer phrasing and produces false positives on short tokens/path fragments.
   Evidence: `matches = [t for t in tokens if t in lower]` with `TOKEN_MATCH_THRESHOLD = 0.6`.
   Suggested fix: Tokenize both sides and match on normalized token or n-gram boundaries, or use a semantic/alias-aware matcher with audited precision/recall on fixtures.

8. Category: methodology-leak
   Severity: MATERIAL
   Location: scripts/arm_study_miss_discoverer.py:match_reference_issues
   What's wrong: The 0.6 overlap rule is vulnerable to synonym-heavy or paraphrastic arms scoring artificially low because coverage is defined only by discoverer-specified `key_tokens`.
   Evidence: Issue coverage is “caught when ≥threshold fraction of its key_tokens appear in challenge_text,” and those tokens are authored by the discoverer model.
   Suggested fix: Add a second-pass semantic adjudication for near-misses or require one anchor token plus semantic similarity on description, rather than pure overlap.

9. Category: silent-failure
   Severity: MATERIAL
   Location: scripts/arm_study_scorer.py:_attach_miss_rate_coverage
   What's wrong: A discoverer parse failure that yields `issues: []` is downgraded to `reference-empty`, which makes an LLM/tool failure look like a valid zero-issue proposal unless downstream readers inspect hidden parse metadata.
   Evidence: The loader only checks `issues = ref.get("issues") or []` then emits `status: "reference-empty"` / `reason: "discoverer returned zero issues"` and ignores `parse_error`.
   Suggested fix: Propagate `parse_error` and any explicit zero-issue note into `reference_coverage.status`, distinguishing `parse-error`, `llm-empty`, and genuinely `trivially-clean`.

10. Category: silent-failure
    Severity: MATERIAL
    Location: scripts/arm_study_verdict.py:_aggregate_verifier
    What's wrong: Classified falsified totals that disagree with verifier stats are neither validated nor corrected despite the docstring claiming proportional scaling, so silent undercount/overcount can change the chosen signal source.
    Evidence: Comment says “Trust stats.falsified ... and scale classification proportionally if parsed total < stats.falsified,” but implementation only copies counts and stores `classified_parsed_total` / `classified_stats_total`; no scaling or fallback occurs.
    Suggested fix: Either implement the stated reconciliation logic or, safer, disable classified mode when parsed totals differ materially from verifier stats and surface a warning.

11. Category: spec-drift
    Severity: MATERIAL
    Location: scripts/arm_study_verdict.py:_aggregate_verifier / render_markdown
    What's wrong: Classified catch_rate excludes `caught_misquote` from the accuracy denominator but leaves `claims_checked` unchanged for hallucination-rate normalization, creating a hybrid metric not clearly aligned with the preregistered “hallucination rate” guardrail.
    Evidence: `accuracy_cls = verified / (verified + hallucination)` while `hallucination_cls = hallucination / claims_checked` and `caught_misquote_rate = caught_misquote / claims_checked`.
    Suggested fix: Document this as an intentional hybrid and pre-register it explicitly, or keep the guardrail on raw falsified/claims_checked while using classified accuracy only for challenger-responsibility analysis.

12. Category: silent-failure
    Severity: MINOR
    Location: scripts/arm_study_orchestrator.py:labels.json loading
    What's wrong: A malformed or partial `labels.json` in parallel mode can crash via `json.loads`/`next(...)` without a targeted error message.
    Evidence: `labels_map = json.loads(labels_path.read_text())` followed by `next(k for k, v in labels_map.items() if v == "arm-a")`.
    Suggested fix: Validate the labels file shape explicitly and emit a clear error if either mapping is missing or duplicated.

13. Category: silent-failure
    Severity: MINOR
    Location: scripts/arm_study_orchestrator.py:manifest merge
    What's wrong: Concurrent arm-only sessions can race on `manifest.json`, causing one session to overwrite the other’s `per_label` or metadata without detection.
    Evidence: Existing manifest is read opportunistically, merged in memory, then written back with no locking or compare-and-swap.
    Suggested fix: Use atomic file locking or write per-arm manifests and merge in a later single-process finalize step.

14. Category: spec-drift
    Severity: MINOR
    Location: scripts/arm_study_verdict.py:_compose_overall_verdict
    What's wrong: Overall confidence is determined solely by total proposal count `n`, not by the number of proposals actually scorable for each dimension, so a dimension with sparse availability can cast a “confident” vote.
    Evidence: `_compose_overall_verdict(per_dim, n)` uses only global `n`, while dims like plan_quality_delta internally may have lower effective sample.
    Suggested fix: Require each dimension’s own verdict label to encode its effective sample confidence and have overall composition respect that per-dim confidence basis.

15. Category: methodology-leak
    Severity: MINOR
    Location: scripts/arm_study_scorer.py:classify_falsified_claims
    What's wrong: The heuristic “mixed source → caught_misquote” may systematically benefit an arm whose challengers quote-and-assert in the same sentence, because any Proposal mention suppresses hallucination attribution.
    Evidence: `elif has_prop: out["caught_misquote"] += 1` treats both proposal-only and mixed-source identically.
    Suggested fix: Split mixed-source into its own bucket and exclude it from winner-affecting classified metrics unless manually spot-checked or disambiguated.

16. Category: minor
    Severity: MINOR
    Location: scripts/arm_study_miss_discoverer.py:main
    What's wrong: The script writes output to both the requested file and stdout, which is fine operationally but can surprise shell pipelines that expect stdout-only JSON or quiet file mode.
    Evidence: After writing `args.output.write_text(serialized)`, it still calls `sys.stdout.write(serialized)`.
    Suggested fix: Add a `--quiet` option or suppress stdout when `--output` is provided unless explicitly requested.

17. Category: minor
    Severity: MINOR
    Location: scripts/arm_study_retrospective.py:main
    What's wrong: Exit code 2 is returned for any status other than `"scored"`, including the intentional `"no-downstream-artifact"` non-scorable case described as exiting 0 in the module docstring.
    Evidence: Docstring says “If none exists, emits "no-downstream-artifact" and exits 0,” but main returns `0 if out["status"] == "scored" else 2`.
    Suggested fix: Return 0 for `"no-downstream-artifact"` and reserve nonzero exits for actual execution/parsing failures.

18. Category: contract-bug
    Severity: MINOR
    Location: scripts/arm_study_retrospective.py module docstring vs main
    What's wrong: The documented exit contract for no downstream artifact disagrees with the implementation.
    Evidence: Header says `emits "no-downstream-artifact" and exits 0`, implementation returns 2 unless status is `"scored"`.
    Suggested fix: Align code and docstring; preferably keep no-artifact as successful non-scorable exit 0.

The main blockers are not syntax-level but measurement-contract issues: unpaired pooling in miss_rate/retrospective, wrong harmful-regression semantics, and catch_rate using raw accuracy instead of the preregistered quality-weighted primary metric. Those can materially change winners or mask data quality problems, so I would not accept this stack until they are fixed.

---
{"status": "ok", "reviewers": 2, "mapping": {"A": "gpt-5.4", "B": "gemini-3.1-pro"}}

## Reviewer B

Here is the review of the arm-comparison stack, prioritized by severity.

### 1. Unpaired aggregation silently skews sums and ratios (MATERIAL)
*   **Category**: silent-failure / methodology-leak
*   **Severity**: MATERIAL
*   **Location**: `arm_study_verdict.py` (loops in `_aggregate_judge_dim`, `_per_dim_verdict_plan_quality`, and `_per_dim_verdict_miss_rate`)
*   **What's wrong**: The verdict script aggregates counts and sums independently for `arm-a` and `arm-b`, meaning if one arm is missing data (e.g. LLM failure, `ws is None`, or parse error) for a single proposal, it silently skips it for that arm but includes the other arm. For judge-graded dims, this directly deflates the `weighted_score_total` (sum across proposals) of the failing arm. For ratio-based metrics, it compares averages taken over different sets of proposals.
*   **Evidence**: 
    ```python
    if arm_retro.get("status") != "scored":
        continue
    # Proceeds to pool landed/total for this arm independently of the other arm
    ```
*   **Suggested fix**: Enforce paired comparison: loop over proposals, and only include a proposal in the pooled totals if *both* arms are successfully scorable for that dimension.

### 2. `has_classification` flag mixes old/new data shapes (MINOR)
*   **Category**: silent-failure
*   **Severity**: MINOR
*   **Location**: `arm_study_verdict.py` in `_aggregate_verifier`
*   **What's wrong**: The boolean `has_classification` is set to `True` if *any* proposal has hallucination classification data. If you pool an older proposal (no classification) with a newer one, the older proposal's data gets implicitly added with `hallucination: 0`, heavily skewing the `accuracy_classified` rate.
*   **Evidence**: `if "hallucination" in stats: has_classification[arm] = True` (sets the flag globally for the arm based on a single proposal).
*   **Suggested fix**: Only set `use_classified = True` if *all* pooled proposals for both arms have the classification keys, or compute the classified accuracy strictly on the subset of paired proposals that possess it.

### 3. `plan_quality_delta` penalizes verbosity structuraly (MINOR)
*   **Category**: methodology-leak
*   **Severity**: MINOR
*   **Location**: `arm_study_verdict.py` in `_per_dim_verdict_plan_quality`
*   **What's wrong**: Landing rate is defined as `(landed + 0.5 * partial) / total_challenger_items`. If Arm A makes 10 points and 5 land (50%), and Arm B makes 100 points and 20 land (20%), Arm B is judged as losing despite contributing 4x more usable substance to the downstream artifact.
*   **Evidence**: `pooled[arm]["landing_rate"] = ((pooled[arm]["landed"] + 0.5 * pooled[arm]["partial"]) / total if total > 0 else None)`
*   **Suggested fix**: Compare the absolute count of landed items (similar to the substantive count metric) rather than the percentage, or evaluate both precision (landing rate) and recall (absolute volume).

### Rating

**REVISE**

The pipeline is well-designed, but the unpaired aggregation bug (Finding 1) is a critical statistical flaw that will silently and unfairly penalize whichever arm experiences transient LLM parse/evaluation failures by subtracting those proposals from its cumulative sums. Fix the aggregation loops to strictly require both arms before accumulating a proposal's stats.

---


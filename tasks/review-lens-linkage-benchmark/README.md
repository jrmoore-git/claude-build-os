# review-lens-linkage benchmark

Baseline measurement of how well the current `/review` PM-lens catches Frame Check defects that leak into implementation diffs. Built per Approach C from `tasks/review-lens-linkage-design.md`.

**Purpose:** answer the question "does the existing spec-compliance path already detect Frame-defective diffs at an acceptable rate, or do we need a dedicated enforcement directive?" Per L47, the benchmark precedes any directive iteration.

## Failure Mode Taxonomy

Each fixture tests one of four failure modes plus frame-sound negative controls.

### DRIFT — Spec drift during implementation

The refined spec's `### Frame Check` subsection lists an unfixed concern (status-list variant (a)). The implementer either misread the status or scope-crept; the diff implements what the Frame Check flagged.

- **Concern keywords:** `already-shipped`, `inflated-problem`, `false-binary`, `inherited-frame`, `load-bearing-assumption`
- **Fail diff:** implements the flagged concern
- **Pass diff:** addresses the same scope while respecting the constraint

### RESURRECT — Resurrection of rejected alternatives

Judge rejected Approach B as frame-defective. Refine polished the rejection language out of the prose but preserved it in Frame Check. Implementer picks B from memory / an earlier draft.

- **Concern keywords:** same as DRIFT; additionally `rejected-alternative`
- **Fail diff:** implements the rejected approach
- **Pass diff:** implements the accepted alternative

### NEW_DEFECT — New frame defects at implementation

Spec was frame-sound (Frame Check = (c)). Implementation introduces hardcoded assumptions, rare-case handling treated as common, or flag names that embed shipped premises. Judge and refine never saw the code.

- **Concern keywords:** `spec-drift`, `hardcoded-threshold`, `shipped-premise`, `rare-case-as-common`
- **Fail diff:** introduces the defect (hardcoded threshold / shipped-premise flag name / etc.)
- **Pass diff:** parameterizes or uses neutral naming

### SCOPE — Silent scope expansion

Spec said "minimum viable wedge X." Diff adds Y and Z "while in there." Current PM lens should catch this via generic compliance — included to measure whether it does.

- **Concern keywords:** `scope-expansion`, `out-of-scope`, `wedge-violation`
- **Fail diff:** adds out-of-scope features
- **Pass diff:** implements only the wedge

## Scoring Rules

For each fixture evaluation:

- **Detection (positive case — fail diff):** review output contains a finding tagged `[MATERIAL]` that explicitly names the Frame Check concern via the "explicitly names" test below. Partial credit if surfaced as `[ADVISORY]` instead.
- **False positive (negative control):** any `[MATERIAL]` frame-related finding on a frame-sound diff counts as FP.
- **Miss:** review passes silently on a fail diff, or surfaces only non-frame findings.
- **True negative:** pass diff produces no frame-related MATERIAL finding.

### "Explicitly names" test

A finding qualifies as detection if its text contains at least one of:

1. A category keyword from the list for that failure mode (case-insensitive substring), OR
2. A ≥3-word contiguous phrase verbatim from the Frame Check subsection of the spec.

The test is implemented as a deterministic substring matcher in `scripts/review_frame_benchmark.py`. No LLM judge in the scoring path — per L31, the scorer measures outcome directly, not LLM-assessed style.

### Metrics

- **Per-mode:** precision = TP / (TP + FP), recall = TP / (TP + FN), F1 = harmonic mean.
- **Overall:** macro-average F1 across 4 modes + FP rate on negative controls.
- **Pareto criterion for any future directive:** ≥ baseline recall AND ≤ baseline FP rate. Directive that improves detection at the cost of FP regression is rejected (L47 refine v2 cautionary tale).

## Fixture Layout

```
tasks/review-lens-linkage-benchmark/
├── README.md                    # this file
├── source-inventory.md          # audit of which real specs can seed which modes
└── fixtures/
    ├── drift/NN-<slug>/
    │   ├── spec.md              # refined spec (real from validation artifacts, or synthetic)
    │   ├── fail-diff.patch      # diff violating the Frame Check concern
    │   ├── pass-diff.patch      # diff addressing same scope, respecting concern
    │   └── expected.json        # {mode, concern_keyword, concern_phrase, fail_file, pass_file}
    ├── resurrect/...            # same schema
    ├── new_defect/...           # same schema
    ├── scope/...                # same schema
    └── negative_control/NN-<slug>/
        ├── spec.md              # frame-sound spec
        ├── pass-diff.patch      # matched-scope diff (no frame defects)
        └── expected.json        # {mode: negative_control, concern_keyword: null, ...}
```

### expected.json schema

```json
{
  "mode": "drift|resurrect|new_defect|scope|negative_control",
  "concern_keywords": ["load-bearing-assumption", "..."],
  "concern_phrase": "verbatim substring from the spec's Frame Check subsection",
  "fail_file": "fail-diff.patch",
  "pass_file": "pass-diff.patch",
  "notes": "one-liner describing what the fail diff does wrong"
}
```

For negative controls, `fail_file` is omitted; scoring runs only on `pass_file` and counts any frame-MATERIAL finding as FP.

## Fixture Count

| Mode | Pairs | Review invocations (fail + pass) |
|------|-------|----------------------------------|
| DRIFT | 5 | 10 |
| RESURRECT | 5 | 10 |
| NEW_DEFECT | 5 | 10 |
| SCOPE | 5 | 10 |
| Negative controls | 2 | 2 |
| **Total** | **22 fixtures** | **42 invocations** |

## Harness Invocation

Harness: `scripts/review_frame_benchmark.py`. Runs the current PM-lens prompt unchanged (no `/review` or `debate.py` edits). Per-fixture: constructs a temp diff input, invokes `debate.py challenge --personas pm --enable-tools` with the current `/review` Step 5 system-prompt, parses output for `[MATERIAL]` and `[ADVISORY]` findings, applies the substring matcher, records the per-fixture verdict.

```bash
# Dry-run (2 fixtures)
python3.11 scripts/review_frame_benchmark.py --baseline --limit 2

# Full baseline
python3.11 scripts/review_frame_benchmark.py --baseline
```

Output: `tasks/review-lens-linkage-benchmark-results.md` with per-mode precision/recall/F1, overall macro-F1, FP rate, per-fixture audit appendix.

## Verdict Rule

After the baseline run:

- **Macro-F1 ≥ 0.8 AND FP rate = 0** → document linkage in `/review` SKILL.md. Close the design. No directive needed — existing spec compliance is adequate.
- **Gap in any single mode** → proceed to Approach A (Extended PM lens + Frame Check parser) with benchmark as calibration target. Directive is accepted only if it is Pareto-dominant on this benchmark.
- **Harness or scoring defect found** → fix the benchmark before interpreting numbers.

## Change control

Fixtures are versioned with the repo. Changes to scoring rules or expected.json must be called out in the corresponding results doc and re-run against any prior baselines for comparability.

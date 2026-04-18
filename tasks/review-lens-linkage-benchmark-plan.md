---
scope: "Build benchmark harness + paired-diff fixtures + baseline measurement for review-stage Frame Check enforcement. No /review or debate.py edits."
surfaces_affected: "scripts/review_frame_benchmark.py, tasks/review-lens-linkage-benchmark/, tasks/review-lens-linkage-benchmark-results.md"
verification_commands: "python3.11 scripts/review_frame_benchmark.py --baseline && test -f tasks/review-lens-linkage-benchmark-results.md"
rollback: "rm -rf scripts/review_frame_benchmark.py tasks/review-lens-linkage-benchmark* (nothing depends on these yet)"
review_tier: "Tier 2 — Log only"
verification_evidence: "PENDING"
challenge_skipped: true
challenge_skip_reason: "Evaluation infra, not production abstraction. Design doc (tasks/review-lens-linkage-design.md) gated the decision by selecting Approach C over A/B."
design_doc: "tasks/review-lens-linkage-design.md"
---

# Plan: review-lens-linkage Frame Check benchmark

## Purpose

Implement Approach C from the design doc: build the benchmark before any `/review` or `debate.py` edits. Measure current detection rate of Frame-defective diffs via the existing PM-lens spec-compliance path. Decide from evidence whether a directive is needed.

## Taxonomy: Failure Modes

Each failure mode maps to one axis of the benchmark. Each gets ≥5 paired fixtures (fail diff + pass diff against the same spec) for 20 paired cases total, plus 2 negative controls.

1. **Spec drift during implementation (DRIFT).** Refined spec's Frame Check said "don't build X because [frame defect]." Diff builds X anyway — implementer misread status or scope-crept. Fail diff: implements the flagged concern. Pass diff: respects the constraint.

2. **Resurrection of rejected alternatives (RESURRECT).** Judge rejected Approach B as frame-defective. Refine sanded rejection language in prose. Implementer picks B from memory. Fail diff: implements B. Pass diff: implements the accepted alternative.

3. **New frame defects at implementation (NEW_DEFECT).** Spec was frame-sound. Implementation introduces hardcoded assumptions, rare-case handling treated as common, or flag names embedding shipped premises. Judge/refine never saw code. Fail diff: introduces hardcoded threshold / shipped-premise flag name. Pass diff: parameterizes or uses neutral naming.

4. **Silent scope expansion (SCOPE).** Spec said "minimum viable wedge X." Diff adds Y and Z. Current PM lens should catch this — included to measure whether it does in practice. Fail diff: adds out-of-scope features. Pass diff: implements only the wedge.

## Scoring Rules

For each fixture evaluated:

- **Detection (positive case):** review output contains a finding tagged `[MATERIAL]` that explicitly names the Frame Check concern (by category or by verbatim phrase from the Frame Check subsection). Partial credit if the concern is surfaced as `[ADVISORY]`.
- **False positive (negative control):** any `[MATERIAL]` finding referencing a frame concern on a frame-sound diff counts as FP.
- **Null result:** review passes silently on a fail diff → miss.

Per-mode metrics: precision, recall, F1. Overall: macro-average across modes + negative-control FP rate. Pareto goal for any future directive: ≥ baseline recall AND ≤ baseline FP rate.

**"Explicitly names" test:** finding text must contain at least one of (a) the category keyword (already-shipped, inflated-problem, false-binary, inherited-frame, load-bearing-assumption, spec-drift, scope-expansion), or (b) a ≥3-word phrase verbatim from the Frame Check subsection. Automated substring matcher — no LLM judge in scoring path (per L31: measure outcome, not style).

## Fixture Construction

### Data sources

- **Specs with unfixed Frame Check concerns:** `tasks/refine-frame-directive-validation/*-v5.md` (11 files; ≥1 confirmed with unfixed load-bearing concern — `streamline-rules-v5.md`).
- **Specs with frame-sound verdict:** same directory, filter for `### Frame Check\n- Frame check: document's frame is sound.` pattern (≥1 confirmed — `autobuild-v5.md`).
- **Judge-stage Frame findings:** `tasks/judge-frame-directive-validation/*.md` — parseable INVESTIGATE blocks identify candidates for RESURRECT mode.

### Construction protocol per mode

DRIFT and RESURRECT source from existing artifacts. NEW_DEFECT and SCOPE require synthetic diffs (authored to violate/respect a known-good refined spec).

For each fixture:
1. Pick a refined spec. Copy to `tasks/review-lens-linkage-benchmark/specs/<slug>.md`.
2. Identify the target Frame Check concern (for DRIFT/RESURRECT) or the specific frame rule being synthetically violated (for NEW_DEFECT/SCOPE).
3. Author `fail-diff.patch` — a `git diff`-formatted patch that violates the concern.
4. Author `pass-diff.patch` — a patch that addresses the same scope while respecting the concern.
5. Annotate `expected.json` with `{mode, concern_keyword, concern_phrase, fail_file, pass_file}`.

Paired diffs edit minimal fictional code — the point is the prompt input to review, not buildable software. Target: ~20 lines per patch, one function / one config block.

### Fixture count

- DRIFT: 5 pairs
- RESURRECT: 5 pairs
- NEW_DEFECT: 5 pairs
- SCOPE: 5 pairs
- Negative controls: 2 frame-sound specs × 1 matched-scope diff each = 2 fixtures

Total: 20 pairs + 2 controls = 42 review invocations for one baseline measurement.

## Harness: scripts/review_frame_benchmark.py

### Interface

```
python3.11 scripts/review_frame_benchmark.py --baseline [--fixture-dir PATH] [--output PATH] [--limit N]
```

- `--baseline` runs the current `/review` path against all fixtures; no directive changes.
- `--fixture-dir` defaults to `tasks/review-lens-linkage-benchmark/fixtures/`.
- `--output` defaults to `tasks/review-lens-linkage-benchmark-results.md`.
- `--limit N` for dev runs on a subset.

### Flow (per fixture)

1. Construct the temp diff input from spec + patch (write spec to temp + patch to temp; emit `git diff`-style combined input that `/review` Step 3 would see).
2. Invoke the PM-lens-only review directly via `debate.py challenge --personas pm --enable-tools --system-prompt <current review system-prompt>` with the diff as proposal. (Avoids running the full 3-lens panel — we only measure the lens that reads the spec.)
3. Parse output — search for `[MATERIAL]` and `[ADVISORY]` findings. Apply the "explicitly names" substring matcher against concern_keyword + concern_phrase.
4. Record: `{fixture_id, mode, diff_type (fail/pass), detected (true/false), severity (MATERIAL/ADVISORY/none), raw_output_path}`.

### Parallelism

Fan-out: all 42 review invocations are independent. Use a thread pool (4-8 workers) to run them concurrently. Debate.py handles its own rate limiting per L38/D29.

### Output

Write `tasks/review-lens-linkage-benchmark-results.md` with:
- Per-mode precision/recall/F1 table
- Overall macro-average + FP rate
- Failure-mode breakdown: which modes current PM lens catches, which it misses
- Per-fixture record in appendix for audit
- Pareto verdict against the null baseline (any detection > 0 is "non-zero; beats null"; target for future directive: ≥ baseline AND zero FP regression)

## Build Order

1. **Taxonomy + scoring doc (`tasks/review-lens-linkage-benchmark/README.md`).** Encode the Failure Modes + Scoring Rules sections above as the single source of truth for fixture construction. Must be in place before any fixture is authored.

2. **Source-data inventory.** Run `grep` + manual review over `tasks/refine-frame-directive-validation/*-v5.md` and `tasks/judge-frame-directive-validation/*.md`. Write `tasks/review-lens-linkage-benchmark/source-inventory.md` listing which real specs are candidates for DRIFT / RESURRECT vs. which modes need synthetic specs.

3. **Fixture construction** — 4 modes × 5 pairs + 2 negative controls. Each pair = spec copy + fail-diff.patch + pass-diff.patch + expected.json. Write under `tasks/review-lens-linkage-benchmark/fixtures/<mode>/<NN>-<slug>/`.

4. **Harness script** `scripts/review_frame_benchmark.py`. Single file, stdlib + subprocess to debate.py. No new dependencies.

5. **Dry-run (--limit 2).** Validate end-to-end on 2 fixtures before committing to the full 42-invocation run.

6. **Baseline run.** Full sweep. Write `tasks/review-lens-linkage-benchmark-results.md`.

7. **Verdict.** Read results. If macro-F1 ≥ 0.8 AND FP rate = 0 → document linkage in `/review` SKILL.md, close design doc. Else → proceed to Approach A (Extended PM lens + Frame Check parser) with benchmark as calibration target.

## Files

| Path | Create/Modify | Scope |
|------|---------------|-------|
| `tasks/review-lens-linkage-benchmark/README.md` | Create | Taxonomy + scoring rules |
| `tasks/review-lens-linkage-benchmark/source-inventory.md` | Create | Audit of available real specs |
| `tasks/review-lens-linkage-benchmark/fixtures/drift/*/{spec.md,fail-diff.patch,pass-diff.patch,expected.json}` | Create | 5 DRIFT pairs |
| `tasks/review-lens-linkage-benchmark/fixtures/resurrect/*/*` | Create | 5 RESURRECT pairs |
| `tasks/review-lens-linkage-benchmark/fixtures/new_defect/*/*` | Create | 5 NEW_DEFECT pairs |
| `tasks/review-lens-linkage-benchmark/fixtures/scope/*/*` | Create | 5 SCOPE pairs |
| `tasks/review-lens-linkage-benchmark/fixtures/negative_control/*/*` | Create | 2 controls |
| `scripts/review_frame_benchmark.py` | Create | Harness |
| `tasks/review-lens-linkage-benchmark-results.md` | Create | Results doc |

## Execution Strategy

**Decision:** hybrid
**Pattern:** pipeline with fan-out at fixture-construction stage
**Reason:** Taxonomy doc must exist before fixtures can be authored (pipeline dependency). Within fixture construction, the 4 modes are independent (fan-out candidate). Harness script depends on fixture format stabilizing. Baseline run fans out internally across 42 invocations but is a single process.

| Subtask | Files | Depends On | Isolation |
|---------|-------|------------|-----------|
| 1. Taxonomy doc | `tasks/.../benchmark/README.md` | — | main session |
| 2. Source inventory | `tasks/.../benchmark/source-inventory.md` | 1 | main session |
| 3a. DRIFT fixtures | `tasks/.../fixtures/drift/**` | 1,2 | worktree (parallel) |
| 3b. RESURRECT fixtures | `tasks/.../fixtures/resurrect/**` | 1,2 | worktree (parallel) |
| 3c. NEW_DEFECT fixtures | `tasks/.../fixtures/new_defect/**` | 1 | worktree (parallel) |
| 3d. SCOPE fixtures | `tasks/.../fixtures/scope/**` | 1 | worktree (parallel) |
| 3e. Negative controls | `tasks/.../fixtures/negative_control/**` | 2 | worktree (parallel) |
| 4. Harness | `scripts/review_frame_benchmark.py` | 1 | main session |
| 5. Dry-run | — | 3a-e, 4 | main session |
| 6. Baseline | `tasks/...benchmark-results.md` | 5 | main session |

**Synthesis:** Main session writes taxonomy + inventory first. Fixture construction (3a-e) may fan out to worktree agents in parallel, each authoring 5 pairs for its assigned mode. Main session reconciles fixture format compliance before harness runs.

**Pragmatic deferral:** Start sequentially for fixtures 3a-3d in the main session (first iteration of fixture format will teach us what the schema should be). Parallelize only after the first mode's fixtures are stable. Build harness after ≥1 complete mode is on disk so we can test harness end-to-end.

## Verification

**Commands:**
```bash
# Inventory check
test -f tasks/review-lens-linkage-benchmark/README.md
ls tasks/review-lens-linkage-benchmark/fixtures/*/*/expected.json | wc -l  # expect ≥22

# Dry-run
python3.11 scripts/review_frame_benchmark.py --baseline --limit 2

# Full baseline
python3.11 scripts/review_frame_benchmark.py --baseline
test -f tasks/review-lens-linkage-benchmark-results.md
```

**Evidence to capture:**
- Per-mode detection matrix in results doc
- Macro-F1 and FP rate
- Verdict line: "directive needed" or "linkage via existing compliance is adequate"

## Rollback

`rm -rf scripts/review_frame_benchmark.py tasks/review-lens-linkage-benchmark*`. Nothing depends on these yet.

## Out of scope (explicitly deferred)

- Any edit to `/review` SKILL.md or `scripts/debate.py`. Phase 2 only, and only if benchmark shows a gap.
- Frame Check parser implementation. Phase 2.
- Benchmark reuse for premortem / explore-synthesis / think-discover directives. Evaluate reusability after this run, not before.
- Cross-model review (3 lenses). Benchmark runs PM-only to isolate the signal path that reads the spec.

## Success Criteria

- 20+2 fixtures on disk, all passing format validation (required files + parseable expected.json).
- Harness runs end-to-end on full benchmark without crashes.
- Results doc has per-mode + overall metrics.
- Verdict is evidence-based: either "no gap, close design" or "gap here → Approach A with calibration target X."

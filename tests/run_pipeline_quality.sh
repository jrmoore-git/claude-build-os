#!/bin/bash
# Pipeline quality tests: 5 end-to-end pipeline runs measuring output quality.
#
# Each test runs a full or partial pipeline and scores the output on:
#   - Completeness: required sections present
#   - Specificity: evidence-tagged claims, numeric thresholds
#   - Cross-model signal: independent models converging on same findings
#   - Pipeline integrity: artifacts chain correctly (challenge → judge → refine)
#
# Usage:
#   ./tests/run_pipeline_quality.sh              # run all 5 tests
#   ./tests/run_pipeline_quality.sh 2 4          # run tests 2 and 4
#
# Prerequisites:
#   - LiteLLM proxy running
#   - python3.11 available

set -eo pipefail
cd "$(git rev-parse --show-toplevel)"

OUTDIR="tests/pipeline-quality-output"
FIXTURES="tests/fixtures"
RESULTS="$OUTDIR/results.json"
TIMING="$OUTDIR/timing.log"
PASS=0
FAIL=0
TOTAL_SCORE=0
MAX_SCORE=0

mkdir -p "$OUTDIR"
echo "[]" > "$RESULTS"
echo "=== Pipeline Quality Run: $(date -Iseconds) ===" > "$TIMING"

# Parse requested test numbers
REQUESTED=()
for arg in "$@"; do
    REQUESTED+=("$arg")
done

should_run() {
    local num="$1"
    if [ ${#REQUESTED[@]} -eq 0 ]; then return 0; fi
    for r in "${REQUESTED[@]}"; do
        [ "$r" = "$num" ] && return 0
    done
    return 1
}

# ── Quality scoring functions ──────────────────────────────────────────────

score_section_presence() {
    # Check if required sections exist in a file. Returns count of found sections.
    local file="$1"
    shift
    local found=0
    local total=0
    for section in "$@"; do
        total=$((total + 1))
        if grep -qi "$section" "$file" 2>/dev/null; then
            found=$((found + 1))
        fi
    done
    echo "$found/$total"
}

count_evidence_tags() {
    # Count EVIDENCED/ESTIMATED/SPECULATIVE tags in a file
    local file="$1"
    local evidenced speculative estimated
    evidenced=$(grep -oi 'EVIDENCED' "$file" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    speculative=$(grep -oi 'SPECULATIVE' "$file" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    estimated=$(grep -oi 'ESTIMATED' "$file" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    echo "evidenced=$evidenced speculative=$speculative estimated=$estimated"
}

count_material_findings() {
    local file="$1"
    grep -oi '\[MATERIAL\]\|MATERIAL' "$file" 2>/dev/null | wc -l | tr -d ' ' || echo "0"
}

count_advisory_findings() {
    local file="$1"
    grep -oi '\[ADVISORY\]\|ADVISORY' "$file" 2>/dev/null | wc -l | tr -d ' ' || echo "0"
}

# Write a test result entry to the JSON results array
write_result() {
    local test_num="$1" test_name="$2" status="$3" score="$4" max="$5" duration="$6"
    shift 6
    local details="$*"

    # Append to results file using python for proper JSON
    python3.11 -c "
import json, sys
with open('$RESULTS', 'r') as f:
    results = json.load(f)
results.append({
    'test': $test_num,
    'name': '$test_name',
    'status': '$status',
    'score': $score,
    'max_score': $max,
    'duration_s': $duration,
    'details': '$details'
})
with open('$RESULTS', 'w') as f:
    json.dump(results, f, indent=2)
"
    TOTAL_SCORE=$((TOTAL_SCORE + score))
    MAX_SCORE=$((MAX_SCORE + max))
    if [ "$status" = "PASS" ]; then
        PASS=$((PASS + 1))
    else
        FAIL=$((FAIL + 1))
    fi
}

# ── Pre-flight ─────────────────────────────────────────────────────────────

echo "Pre-flight: checking model availability..."
if ! python3.11 scripts/debate.py check-models 2>&1 | grep -q "claude-opus-4-7"; then
    echo "FATAL: LiteLLM models not available."
    exit 1
fi
echo "Pre-flight: models OK"

echo ""
echo "Pre-flight: running unit tests..."
if ! python3.11 -m pytest tests/ -x -q 2>&1 | tail -3; then
    echo "FATAL: unit tests failed"
    exit 1
fi
echo "Pre-flight: unit tests PASS"

# ══════════════════════════════════════════════════════════════════════════
# TEST 1: Full pipeline (challenge → judge w/ verify → refine w/ early-stop)
#         Measures: end-to-end quality, early-stop behavior, pipeline integrity
# ══════════════════════════════════════════════════════════════════════════

if should_run 1; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  TEST 1: Full pipeline with early-stop on rate-limiter proposal"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    testdir="$OUTDIR/test1-full-pipeline"
    mkdir -p "$testdir"
    t1_start=$(date +%s)
    t1_score=0
    t1_max=10

    echo "  Step 1/3: challenge..."
    if python3.11 scripts/debate.py challenge \
        --proposal "$FIXTURES/proposal-rate-limiter.md" \
        --personas architect,security,pm \
        --enable-tools \
        --output "$testdir/challenge.md" \
        >"$testdir/challenge-stdout.log" \
        2>"$testdir/challenge-stderr.log"; then

        # Score: 3 challengers responded? (JSON status goes to stdout)
        challengers=$(grep -o '"successful_responders": [0-9]*' "$testdir/challenge-stdout.log" | grep -o '[0-9]*' || echo "0")
        if [ "${challengers:-0}" -ge 3 ]; then
            t1_score=$((t1_score + 2))
            echo "    ✓ 3/3 challengers responded"
        else
            echo "    ✗ Only ${challengers:-0} challengers responded"
        fi

        # Score: evidence tags present?
        ev_tags=$(count_evidence_tags "$testdir/challenge.md")
        evidenced_count=$(echo "$ev_tags" | grep -o 'evidenced=[0-9]*' | grep -o '[0-9]*')
        if [ "${evidenced_count:-0}" -ge 2 ]; then
            t1_score=$((t1_score + 1))
            echo "    ✓ Evidence tags: $ev_tags"
        else
            echo "    ✗ Low evidence tagging: $ev_tags"
        fi
    else
        echo "    ✗ Challenge step failed"
    fi

    echo "  Step 2/3: judge with claim verification..."
    if python3.11 scripts/debate.py judge \
        --proposal "$FIXTURES/proposal-rate-limiter.md" \
        --challenge "$testdir/challenge.md" \
        --verify-claims \
        --output "$testdir/judgment.md" \
        >"$testdir/judge-stdout.log" \
        2>"$testdir/judge-stderr.log"; then

        # Score: consolidation happened?
        if grep -q "Consolidated:" "$testdir/judge-stderr.log"; then
            t1_score=$((t1_score + 1))
            consol=$(grep "Consolidated:" "$testdir/judge-stderr.log")
            echo "    ✓ $consol"
        fi

        # Score: verifier ran in parallel with consolidation?
        if grep -q "Verifier:" "$testdir/judge-stderr.log"; then
            t1_score=$((t1_score + 1))
            verifier=$(grep "Verifier:" "$testdir/judge-stderr.log")
            echo "    ✓ $verifier"
        fi

        # Score: accepted findings > 0?
        accepted=$(python3.11 -c "
import json, sys
for line in open('$testdir/judge-stderr.log'):
    pass
# last line of stdout from judge is JSON
with open('$testdir/judgment.md') as f:
    text = f.read()
import re
accepted = len(re.findall(r'Decision:\s*ACCEPT', text, re.IGNORECASE))
print(accepted)
")
        if [ "${accepted:-0}" -ge 1 ]; then
            t1_score=$((t1_score + 1))
            echo "    ✓ $accepted findings accepted by judge"
        else
            echo "    ✗ No findings accepted"
        fi
    else
        echo "    ✗ Judge step failed"
    fi

    echo "  Step 3/3: refine with early-stop..."
    if python3.11 scripts/debate.py refine \
        --document "$FIXTURES/proposal-rate-limiter.md" \
        --judgment "$testdir/judgment.md" \
        --enable-tools \
        --early-stop \
        --output "$testdir/refined.md" \
        >"$testdir/refine-stdout.log" \
        2>"$testdir/refine-stderr.log"; then

        # Score: refined doc has required sections?
        sections=$(score_section_presence "$testdir/refined.md" \
            "Problem" "Proposed Approach" "Simplest Version" \
            "Current System Failures" "Recommendations")
        found=$(echo "$sections" | cut -d/ -f1)
        if [ "$found" -ge 4 ]; then
            t1_score=$((t1_score + 2))
            echo "    ✓ Refined doc sections: $sections"
        else
            echo "    ✗ Missing sections: $sections"
        fi

        # Score: early-stop triggered or all 6 rounds completed?
        if grep -q "Early-stop" "$testdir/refine-stderr.log"; then
            rounds_run=$(grep -c "Refine round" "$testdir/refine-stderr.log" || echo "0")
            t1_score=$((t1_score + 1))
            echo "    ✓ Early-stop triggered after $rounds_run rounds"
        else
            rounds_run=$(grep -c "Refine round" "$testdir/refine-stderr.log" || echo "0")
            echo "    ○ No early-stop — ran all $rounds_run rounds"
        fi

        # Score: refined doc longer than original (enriched, not truncated)?
        orig_len=$(wc -c < "$FIXTURES/proposal-rate-limiter.md" | tr -d ' ')
        refined_len=$(wc -c < "$testdir/refined.md" | tr -d ' ')
        if [ "$refined_len" -gt "$orig_len" ]; then
            t1_score=$((t1_score + 1))
            echo "    ✓ Refined doc enriched: ${orig_len}→${refined_len} chars"
        else
            echo "    ✗ Refined doc shorter than original: ${orig_len}→${refined_len}"
        fi
    else
        echo "    ✗ Refine step failed"
    fi

    t1_end=$(date +%s)
    t1_dur=$((t1_end - t1_start))
    echo "$t1_dur" >> "$TIMING"
    status="PASS"
    [ "$t1_score" -lt 6 ] && status="FAIL"
    write_result 1 "full-pipeline-earlystop" "$status" "$t1_score" "$t1_max" "$t1_dur" \
        "challenge→judge(verify)→refine(early-stop)"
    echo ""
    echo "  Score: $t1_score/$t1_max | ${t1_dur}s | $status"
fi

# ══════════════════════════════════════════════════════════════════════════
# TEST 2: Parallel review-panel speed + quality benchmark
#         Measures: wall-clock time, reviewer independence, finding density
# ══════════════════════════════════════════════════════════════════════════

if should_run 2; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  TEST 2: Parallel review-panel (4 personas) on search rewrite"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    testdir="$OUTDIR/test2-review-panel"
    mkdir -p "$testdir"
    t2_start=$(date +%s)
    t2_score=0
    t2_max=8

    if python3.11 scripts/debate.py review-panel \
        --personas architect,security,pm,staff \
        --prompt "You are a code reviewer. Review this proposal through your assigned lens. Tag each finding as [MATERIAL] or [ADVISORY]. For QUANTITATIVE CLAIMS: tag as EVIDENCED, ESTIMATED, or SPECULATIVE." \
        --input "$FIXTURES/proposal-search-rewrite.md" \
        --enable-tools \
        > "$testdir/review-panel.md" \
        2>"$testdir/stderr.log"; then

        t2_end=$(date +%s)
        t2_dur=$((t2_end - t2_start))

        # Score: all 4 reviewers responded?
        reviewer_count=$(grep -c "^## Reviewer" "$testdir/review-panel.md" || echo "0")
        if [ "$reviewer_count" -ge 4 ]; then
            t2_score=$((t2_score + 2))
            echo "    ✓ $reviewer_count reviewers responded"
        else
            echo "    ✗ Only $reviewer_count reviewers"
        fi

        # Score: wall-clock under 120s? (parallel should be <90s)
        if [ "$t2_dur" -lt 120 ]; then
            t2_score=$((t2_score + 2))
            echo "    ✓ Completed in ${t2_dur}s (parallel target: <120s)"
        else
            echo "    ✗ Took ${t2_dur}s (expected <120s with parallelization)"
        fi

        # Score: material findings from multiple reviewers?
        material_count=$(count_material_findings "$testdir/review-panel.md")
        if [ "$material_count" -ge 3 ]; then
            t2_score=$((t2_score + 2))
            echo "    ✓ $material_count material findings"
        elif [ "$material_count" -ge 1 ]; then
            t2_score=$((t2_score + 1))
            echo "    ○ Only $material_count material findings"
        else
            echo "    ✗ No material findings"
        fi

        # Score: evidence tagging?
        ev_tags=$(count_evidence_tags "$testdir/review-panel.md")
        evidenced_count=$(echo "$ev_tags" | grep -o 'evidenced=[0-9]*' | grep -o '[0-9]*')
        if [ "${evidenced_count:-0}" -ge 3 ]; then
            t2_score=$((t2_score + 2))
            echo "    ✓ Evidence tags: $ev_tags"
        elif [ "${evidenced_count:-0}" -ge 1 ]; then
            t2_score=$((t2_score + 1))
            echo "    ○ Some evidence tags: $ev_tags"
        else
            echo "    ✗ No evidence tagging: $ev_tags"
        fi
    else
        t2_end=$(date +%s)
        t2_dur=$((t2_end - t2_start))
        echo "    ✗ Review-panel failed"
    fi

    echo "$t2_dur" >> "$TIMING"
    status="PASS"
    [ "$t2_score" -lt 5 ] && status="FAIL"
    write_result 2 "review-panel-parallel" "$status" "$t2_score" "$t2_max" "$t2_dur" \
        "4-persona parallel review with tool use"
    echo ""
    echo "  Score: $t2_score/$t2_max | ${t2_dur}s | $status"
fi

# ══════════════════════════════════════════════════════════════════════════
# TEST 3: Explore divergent directions + quality of synthesis
#         Measures: direction diversity, synthesis coherence, actionability
# ══════════════════════════════════════════════════════════════════════════

if should_run 3; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  TEST 3: Explore (3 directions) on build-vs-buy decision"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    testdir="$OUTDIR/test3-explore"
    mkdir -p "$testdir"
    t3_start=$(date +%s)
    t3_score=0
    t3_max=8

    if python3.11 scripts/debate.py explore \
        --question 'We have 15 microservices and deployment takes 45 minutes. Should we build a custom deployment platform, adopt ArgoCD, or stay with our bash scripts and optimize them?' \
        --directions 3 \
        --context 'Team of 6 engineers, 50 deployments/week, 3 production incidents last quarter caused by deployment issues. Current bash scripts are 2000 lines. Monthly AWS bill is $12k.' \
        --output "$testdir/explore.md" \
        >"$testdir/stdout.log" \
        2>"$testdir/stderr.log"; then

        t3_end=$(date +%s)
        t3_dur=$((t3_end - t3_start))

        # Score: 3 directions generated?
        dir_count=$(grep -c "^## Direction" "$testdir/explore.md")
        if [ "$dir_count" -ge 3 ]; then
            t3_score=$((t3_score + 2))
            echo "    ✓ $dir_count directions generated"
        else
            echo "    ✗ Only $dir_count directions"
        fi

        # Score: synthesis section exists with comparison?
        if grep -qi "Synthesis\|Comparison\|Fork" "$testdir/explore.md"; then
            t3_score=$((t3_score + 2))
            echo "    ✓ Synthesis section present"
        else
            echo "    ✗ No synthesis section"
        fi

        # Score: directions are genuinely diverse (different direction names)?
        dir_names=$(grep "^## Direction:" "$testdir/explore.md" | head -3)
        unique_words=$(echo "$dir_names" | tr '[:upper:]' '[:lower:]' | tr -s ' ' '\n' | sort -u | wc -l | tr -d ' ')
        if [ "$unique_words" -ge 8 ]; then
            t3_score=$((t3_score + 2))
            echo "    ✓ Directions appear diverse ($unique_words unique words in titles)"
        else
            echo "    ○ Directions may overlap ($unique_words unique words)"
            t3_score=$((t3_score + 1))
        fi

        # Score: actionable first moves?
        first_moves=$(grep -ci "first move\|next week\|this week\|start with\|begin by" "$testdir/explore.md" || echo "0")
        if [ "$first_moves" -ge 2 ]; then
            t3_score=$((t3_score + 2))
            echo "    ✓ $first_moves actionable first-move references"
        elif [ "$first_moves" -ge 1 ]; then
            t3_score=$((t3_score + 1))
            echo "    ○ $first_moves actionable reference"
        else
            echo "    ✗ No actionable first moves"
        fi
    else
        t3_end=$(date +%s)
        t3_dur=$((t3_end - t3_start))
        echo "    ✗ Explore failed"
    fi

    echo "$t3_dur" >> "$TIMING"
    status="PASS"
    [ "$t3_score" -lt 5 ] && status="FAIL"
    write_result 3 "explore-divergent" "$status" "$t3_score" "$t3_max" "$t3_dur" \
        "3 divergent directions + synthesis"
    echo ""
    echo "  Score: $t3_score/$t3_max | ${t3_dur}s | $status"
fi

# ══════════════════════════════════════════════════════════════════════════
# TEST 4: Pressure-test + pre-mortem combo on webhook proposal
#         Measures: counter-thesis quality, failure specificity, structural pattern
# ══════════════════════════════════════════════════════════════════════════

if should_run 4; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  TEST 4: Pressure-test + pre-mortem on webhook retry proposal"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    testdir="$OUTDIR/test4-pressure-premortem"
    mkdir -p "$testdir"
    t4_start=$(date +%s)
    t4_score=0
    t4_max=10

    # Run both in parallel (they're independent)
    echo "  Running pressure-test and pre-mortem in parallel..."

    python3.11 scripts/debate.py pressure-test \
        --proposal "$FIXTURES/proposal-webhook-retry.md" \
        --frame challenge \
        --output "$testdir/pressure-test.md" \
        >"$testdir/pt-stdout.log" \
        2>"$testdir/pt-stderr.log" &
    pt_pid=$!

    python3.11 scripts/debate.py pre-mortem \
        --plan "$FIXTURES/proposal-webhook-retry.md" \
        --context 'Team of 4 engineers. Last 3 production incidents were webhook-related. SLA commitment to customers: 99.9% delivery within 1 hour.' \
        --output "$testdir/premortem.md" \
        >"$testdir/pm-stdout.log" \
        2>"$testdir/pm-stderr.log" &
    pm_pid=$!

    pt_ok=0
    pm_ok=0
    wait $pt_pid && pt_ok=1
    wait $pm_pid && pm_ok=1

    t4_end=$(date +%s)
    t4_dur=$((t4_end - t4_start))

    if [ "$pt_ok" -eq 1 ]; then
        # Score: counter-thesis exists?
        if grep -qi "counter.thesis\|better alternative\|alternative direction" "$testdir/pressure-test.md"; then
            t4_score=$((t4_score + 2))
            echo "    ✓ Counter-thesis present in pressure-test"
        else
            echo "    ✗ No counter-thesis"
        fi

        # Score: demand-side forces analyzed?
        if grep -qi "push\|pull\|anxiety\|habit\|force" "$testdir/pressure-test.md"; then
            t4_score=$((t4_score + 1))
            echo "    ✓ Demand-side forces analyzed"
        fi

        # Score: timing analysis?
        if grep -qi "timing\|window\|wait for\|right move now" "$testdir/pressure-test.md"; then
            t4_score=$((t4_score + 1))
            echo "    ✓ Timing analysis present"
        fi
    else
        echo "    ✗ Pressure-test failed"
    fi

    if [ "$pm_ok" -eq 1 ]; then
        # Score: 3+ specific failure scenarios?
        failure_count=$(grep -ci "failure\|what happened\|type:" "$testdir/premortem.md" || echo "0")
        if [ "$failure_count" -ge 6 ]; then
            t4_score=$((t4_score + 2))
            echo "    ✓ $failure_count failure-related markers in pre-mortem"
        elif [ "$failure_count" -ge 3 ]; then
            t4_score=$((t4_score + 1))
            echo "    ○ $failure_count failure markers (expected ≥6)"
        else
            echo "    ✗ Only $failure_count failure markers"
        fi

        # Score: structural pattern identified?
        if grep -qi "pattern\|structural\|common thread" "$testdir/premortem.md"; then
            t4_score=$((t4_score + 2))
            echo "    ✓ Structural pattern identified"
        else
            echo "    ✗ No structural pattern"
        fi

        # Score: "the one test" recommendation?
        if grep -qi "one test\|the test\|pilot\|instrument\|measure" "$testdir/premortem.md"; then
            t4_score=$((t4_score + 2))
            echo "    ✓ Concrete test recommendation present"
        else
            echo "    ✗ No concrete test recommendation"
        fi
    else
        echo "    ✗ Pre-mortem failed"
    fi

    echo "$t4_dur" >> "$TIMING"
    status="PASS"
    [ "$t4_score" -lt 6 ] && status="FAIL"
    write_result 4 "pressure-premortem" "$status" "$t4_score" "$t4_max" "$t4_dur" \
        "pressure-test + pre-mortem parallel"
    echo ""
    echo "  Score: $t4_score/$t4_max | ${t4_dur}s | $status"
fi

# ══════════════════════════════════════════════════════════════════════════
# TEST 5: Cross-model convergence test
#         Run challenge on same proposal with 2 different persona sets,
#         then measure whether material findings overlap (convergence signal)
# ══════════════════════════════════════════════════════════════════════════

if should_run 5; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  TEST 5: Cross-model convergence (2 independent challenge runs)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    testdir="$OUTDIR/test5-convergence"
    mkdir -p "$testdir"
    t5_start=$(date +%s)
    t5_score=0
    t5_max=8

    echo "  Running two independent challenge passes in parallel..."

    # Run A: architect + security
    python3.11 scripts/debate.py challenge \
        --proposal "$FIXTURES/proposal-email-pipeline.md" \
        --personas architect,security \
        --enable-tools \
        --output "$testdir/challenge-A.md" \
        >"$testdir/A-stdout.log" \
        2>"$testdir/A-stderr.log" &
    a_pid=$!

    # Run B: pm + staff
    python3.11 scripts/debate.py challenge \
        --proposal "$FIXTURES/proposal-email-pipeline.md" \
        --personas pm,staff \
        --enable-tools \
        --output "$testdir/challenge-B.md" \
        >"$testdir/B-stdout.log" \
        2>"$testdir/B-stderr.log" &
    b_pid=$!

    a_ok=0
    b_ok=0
    wait $a_pid && a_ok=1
    wait $b_pid && b_ok=1

    t5_end=$(date +%s)
    t5_dur=$((t5_end - t5_start))

    if [ "$a_ok" -eq 1 ] && [ "$b_ok" -eq 1 ]; then
        # Score: both runs produced findings?
        a_material=$(count_material_findings "$testdir/challenge-A.md")
        b_material=$(count_material_findings "$testdir/challenge-B.md")
        echo "    Run A (architect,security): $a_material material findings"
        echo "    Run B (pm,staff): $b_material material findings"

        if [ "$a_material" -ge 2 ] && [ "$b_material" -ge 2 ]; then
            t5_score=$((t5_score + 2))
            echo "    ✓ Both runs found material issues"
        elif [ "$a_material" -ge 1 ] || [ "$b_material" -ge 1 ]; then
            t5_score=$((t5_score + 1))
            echo "    ○ Only one run found material issues"
        fi

        # Score: convergence — do they flag similar themes?
        # Extract key concern words from each
        a_themes=$(grep -oi 'idempoten\|concurren\|dedup\|review\|safety\|security\|lock\|queue\|race\|overlap\|injection\|prompt' "$testdir/challenge-A.md" | tr '[:upper:]' '[:lower:]' | sort -u || true)
        b_themes=$(grep -oi 'idempoten\|concurren\|dedup\|review\|safety\|security\|lock\|queue\|race\|overlap\|injection\|prompt' "$testdir/challenge-B.md" | tr '[:upper:]' '[:lower:]' | sort -u || true)

        overlap=0
        for theme in $a_themes; do
            if echo "$b_themes" | grep -q "$theme"; then overlap=$((overlap + 1)); fi
        done

        if [ "$overlap" -ge 3 ]; then
            t5_score=$((t5_score + 3))
            echo "    ✓ Strong convergence: $overlap shared themes across independent runs"
        elif [ "$overlap" -ge 1 ]; then
            t5_score=$((t5_score + 2))
            echo "    ○ Moderate convergence: $overlap shared themes"
        else
            echo "    ✗ No convergence — independent runs found unrelated issues"
            t5_score=$((t5_score + 1))
        fi

        # Score: both ran in parallel (wall-clock < sum of individual)?
        if [ "$t5_dur" -lt 180 ]; then
            t5_score=$((t5_score + 2))
            echo "    ✓ Parallel execution: ${t5_dur}s"
        else
            t5_score=$((t5_score + 1))
            echo "    ○ Slow: ${t5_dur}s"
        fi

        # Score: concessions present (not just attacks)?
        a_concessions=$(grep -ci "concession" "$testdir/challenge-A.md" || echo "0")
        b_concessions=$(grep -ci "concession" "$testdir/challenge-B.md" || echo "0")
        if [ "$((a_concessions + b_concessions))" -ge 2 ]; then
            t5_score=$((t5_score + 1))
            echo "    ✓ Both runs include concessions (balanced review)"
        fi
    else
        echo "    ✗ One or both challenge runs failed (A=$a_ok B=$b_ok)"
    fi

    echo "$t5_dur" >> "$TIMING"
    status="PASS"
    [ "$t5_score" -lt 5 ] && status="FAIL"
    write_result 5 "cross-model-convergence" "$status" "$t5_score" "$t5_max" "$t5_dur" \
        "2 independent challenge runs, convergence measurement"
    echo ""
    echo "  Score: $t5_score/$t5_max | ${t5_dur}s | $status"
fi

# ── Summary ────────────────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PIPELINE QUALITY SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

total_tests=$((PASS + FAIL))
pct=0
if [ "$MAX_SCORE" -gt 0 ]; then
    pct=$((TOTAL_SCORE * 100 / MAX_SCORE))
fi

echo "  Tests: $PASS passed, $FAIL failed (of $total_tests)"
echo "  Quality Score: $TOTAL_SCORE / $MAX_SCORE ($pct%)"
echo ""

# Print per-test results
python3.11 -c "
import json
with open('$RESULTS') as f:
    results = json.load(f)
print('  | Test | Name                    | Score  | Time  | Status |')
print('  |------|-------------------------|--------|-------|--------|')
for r in results:
    name = r['name'][:23].ljust(23)
    score = f\"{r['score']}/{r['max_score']}\".ljust(6)
    time = f\"{r['duration_s']}s\".ljust(5)
    print(f\"  | {r['test']}    | {name} | {score} | {time} | {r['status']}   |\")
print()

total_time = sum(r['duration_s'] for r in results)
print(f'  Total wall-clock: {total_time}s')
"

echo ""
echo "  Results: $RESULTS"
echo "  Output:  $OUTDIR/"
echo ""

# Dump debate log count for the day
debate_count=$(python3.11 -c "
import json, os
log = os.path.expanduser('stores/debate-log.jsonl')
if os.path.exists(log):
    with open(log) as f:
        today = __import__('datetime').date.today().isoformat()
        count = sum(1 for line in f if today in line)
    print(f'Debate log entries today: {count}')
else:
    print('No debate log found')
" 2>/dev/null || echo "Could not read debate log")
echo "  $debate_count"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo "  Some tests FAILED — check output files for details."
    exit 1
else
    echo "  All tests PASSED."
fi

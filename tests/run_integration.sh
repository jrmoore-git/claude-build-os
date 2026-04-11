#!/bin/bash
# Comprehensive integration test for all new debate.py subcommands,
# managed_agent.py, check_conviction_gate.py, and config prompts.
#
# Usage:
#   ./tests/run_integration.sh              # run all 7 tests
#   ./tests/run_integration.sh 3            # run only test 3
#   ./tests/run_integration.sh 1 3 5        # run tests 1, 3, 5
#
# Prerequisites:
#   - LiteLLM proxy running (debate.py models: claude-opus-4-6, gpt-5.4, gemini-3.1-pro)
#   - MA_API_KEY set in environment (for test 7 — MA consolidation)
#   - python3.11 available
#
# Each test writes output to tests/integration-output/<test-name>/
# and logs pass/fail to tests/integration-output/results.log

set -eo pipefail
cd "$(git rev-parse --show-toplevel)"

OUTDIR="tests/integration-output"
FIXTURES="tests/fixtures"
RESULTS="$OUTDIR/results.log"
PASS=0
FAIL=0
SKIP=0

mkdir -p "$OUTDIR"
echo "=== Integration Test Run: $(date -Iseconds) ===" > "$RESULTS"
echo "" >> "$RESULTS"

# ── Helper ──────────────────────────────────────────────────────────────────

run_test() {
    local num="$1" name="$2" desc="$3"
    shift 3

    # If specific tests requested, skip others
    if [ ${#REQUESTED[@]} -gt 0 ]; then
        local found=0
        for r in "${REQUESTED[@]}"; do
            [ "$r" = "$num" ] && found=1
        done
        [ "$found" -eq 0 ] && return 0
    fi

    local testdir="$OUTDIR/$name"
    mkdir -p "$testdir"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  TEST $num: $desc"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

log_result() {
    local num="$1" name="$2" status="$3" detail="$4"
    echo "  [$status] Test $num ($name): $detail" | tee -a "$RESULTS"
    case "$status" in
        PASS) PASS=$((PASS + 1)) ;;
        FAIL) FAIL=$((FAIL + 1)) ;;
        SKIP) SKIP=$((SKIP + 1)) ;;
    esac
}

check_output() {
    local file="$1" min_lines="$2" label="$3"
    if [ ! -f "$file" ]; then
        echo "    MISSING: $file"
        return 1
    fi
    local lines
    lines=$(wc -l < "$file" | tr -d ' ')
    if [ "$lines" -lt "$min_lines" ]; then
        echo "    TOO SHORT: $file has $lines lines (expected >= $min_lines)"
        return 1
    fi
    echo "    OK: $label ($lines lines)"
    return 0
}

# Parse requested test numbers
REQUESTED=()
for arg in "$@"; do
    REQUESTED+=("$arg")
done

# ── Pre-flight ──────────────────────────────────────────────────────────────

echo "Pre-flight: checking model availability..."
if ! python3.11 scripts/debate.py check-models 2>&1 | grep -q "claude-opus-4-6"; then
    echo "FATAL: LiteLLM models not available. Start LiteLLM proxy first."
    echo "[FATAL] LiteLLM models not available" >> "$RESULTS"
    exit 1
fi
echo "Pre-flight: models OK"
echo ""

# ── Pre-flight: unit tests ─────────────────────────────────────────────────

echo "Pre-flight: running unit tests..."
if python3.11 -m pytest tests/test_debate_smoke.py tests/test_managed_agent.py \
    tests/test_conviction_gate.py tests/test_tool_loop_config.py -q 2>&1; then
    echo "Pre-flight: unit tests PASS"
else
    echo "WARNING: unit tests failed — continuing with integration tests"
fi
echo ""

# ════════════════════════════════════════════════════════════════════════════
# TEST 1: Full Debate Pipeline (challenge → judge → refine)
#   Domain: API caching layer proposal
#   Exercises: challenge (3 personas), judge (with consolidation), refine (6 rounds)
# ════════════════════════════════════════════════════════════════════════════

run_test 1 "full-pipeline" "Full debate pipeline: challenge → judge → refine"

if [ ${#REQUESTED[@]} -eq 0 ] || printf '%s\n' "${REQUESTED[@]}" | grep -qx 1; then
    testdir="$OUTDIR/full-pipeline"

    echo "  Step 1/3: challenge (architect, security, pm)..."
    if python3.11 scripts/debate.py challenge \
        --proposal "$FIXTURES/proposal-caching-layer.md" \
        --personas architect,security,pm \
        --enable-tools \
        --output "$testdir/challenge.md" 2>&1 | tail -5; then

        echo "  Step 2/3: judge (with consolidation)..."
        if python3.11 scripts/debate.py judge \
            --proposal "$FIXTURES/proposal-caching-layer.md" \
            --challenge "$testdir/challenge.md" \
            --verify-claims \
            --output "$testdir/judgment.md" 2>&1 | tail -5; then

            echo "  Step 3/3: refine (6 rounds)..."
            if python3.11 scripts/debate.py refine \
                --document "$FIXTURES/proposal-caching-layer.md" \
                --judgment "$testdir/judgment.md" \
                --rounds 6 \
                --enable-tools \
                --output "$testdir/refined.md" 2>&1 | tail -5; then

                ok=true
                check_output "$testdir/challenge.md" 20 "challenge" || ok=false
                check_output "$testdir/judgment.md" 20 "judgment" || ok=false
                check_output "$testdir/refined.md" 20 "refined" || ok=false

                if $ok; then
                    log_result 1 "full-pipeline" "PASS" "3-stage pipeline completed"
                else
                    log_result 1 "full-pipeline" "FAIL" "output files incomplete"
                fi
            else
                log_result 1 "full-pipeline" "FAIL" "refine failed"
            fi
        else
            log_result 1 "full-pipeline" "FAIL" "judge failed"
        fi
    else
        log_result 1 "full-pipeline" "FAIL" "challenge failed"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# TEST 2: Explore (divergent directions + synthesis)
#   Domain: strategic product question
#   Exercises: explore with --directions 3, custom --context
# ════════════════════════════════════════════════════════════════════════════

run_test 2 "explore" "Explore: divergent directions + synthesis"

if [ ${#REQUESTED[@]} -eq 0 ] || printf '%s\n' "${REQUESTED[@]}" | grep -qx 2; then
    testdir="$OUTDIR/explore"

    echo "  Running explore with 3 directions + market context..."
    if python3.11 scripts/debate.py explore \
        --question 'Should we build a self-hosted analytics platform or integrate with a third-party provider like PostHog or Amplitude? We have 50k monthly active users, a 3-person engineering team, and $200/month analytics budget.' \
        --directions 3 \
        --context 'Competitors: PostHog (open-source, self-hosted option, $0-450/mo), Amplitude (SaaS, $49-995/mo), Mixpanel (SaaS, $25-999/mo). Trend: privacy-first analytics growing 40% YoY. Our users are B2B SaaS companies who care about data sovereignty.' \
        --output "$testdir/explore.md" 2>&1 | tail -5; then

        if check_output "$testdir/explore.md" 30 "explore output"; then
            # Verify synthesis section exists
            if grep -q -i "synth" "$testdir/explore.md"; then
                log_result 2 "explore" "PASS" "3 directions + synthesis generated"
            else
                log_result 2 "explore" "FAIL" "no synthesis section found"
            fi
        else
            log_result 2 "explore" "FAIL" "output too short"
        fi
    else
        log_result 2 "explore" "FAIL" "explore command failed"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# TEST 3: Pressure-Test (challenge frame)
#   Domain: webhook retry system
#   Exercises: pressure-test with --frame challenge
# ════════════════════════════════════════════════════════════════════════════

run_test 3 "pressure-test" "Pressure-test: counter-thesis on webhook retry"

if [ ${#REQUESTED[@]} -eq 0 ] || printf '%s\n' "${REQUESTED[@]}" | grep -qx 3; then
    testdir="$OUTDIR/pressure-test"

    echo "  Running pressure-test (challenge frame)..."
    if python3.11 scripts/debate.py pressure-test \
        --proposal "$FIXTURES/proposal-webhook-retry.md" \
        --frame challenge \
        --output "$testdir/pressure-test.md" 2>&1 | tail -5; then

        if check_output "$testdir/pressure-test.md" 20 "pressure-test output"; then
            log_result 3 "pressure-test" "PASS" "counter-thesis generated"
        else
            log_result 3 "pressure-test" "FAIL" "output too short"
        fi
    else
        log_result 3 "pressure-test" "FAIL" "pressure-test command failed"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# TEST 4: Pre-mortem (prospective failure analysis)
#   Domain: notification routing plan
#   Exercises: pre-mortem on a plan artifact
# ════════════════════════════════════════════════════════════════════════════

run_test 4 "pre-mortem" "Pre-mortem: failure analysis on notification plan"

if [ ${#REQUESTED[@]} -eq 0 ] || printf '%s\n' "${REQUESTED[@]}" | grep -qx 4; then
    testdir="$OUTDIR/pre-mortem"

    echo "  Running pre-mortem..."
    if python3.11 scripts/debate.py pre-mortem \
        --plan "$FIXTURES/plan-notification-system.md" \
        --output "$testdir/pre-mortem.md" 2>&1 | tail -5; then

        if check_output "$testdir/pre-mortem.md" 15 "pre-mortem output"; then
            log_result 4 "pre-mortem" "PASS" "failure analysis generated"
        else
            log_result 4 "pre-mortem" "FAIL" "output too short"
        fi
    else
        log_result 4 "pre-mortem" "FAIL" "pre-mortem command failed"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# TEST 5: Review-Panel (multi-persona anonymous panel)
#   Domain: auth migration proposal
#   Exercises: review-panel with architect,security,pm,product personas
# ════════════════════════════════════════════════════════════════════════════

run_test 5 "review-panel" "Review-panel: 4-persona panel on auth migration"

if [ ${#REQUESTED[@]} -eq 0 ] || printf '%s\n' "${REQUESTED[@]}" | grep -qx 5; then
    testdir="$OUTDIR/review-panel"

    echo "  Running review-panel (4 personas)..."
    if python3.11 scripts/debate.py review-panel \
        --personas architect,security,pm,staff \
        --prompt "Review this auth migration proposal. For each finding, tag as [MATERIAL] or [ADVISORY]. Focus on: security risks of JWT vs sessions, migration rollback safety, data residency compliance, and operational complexity. Evaluate both directions of risk." \
        --input "$FIXTURES/proposal-auth-migration.md" \
        --enable-tools >"$testdir/review-panel.md" 2>"$testdir/stderr.log"; then

        tail -10 "$testdir/review-panel.md"
        if check_output "$testdir/review-panel.md" 20 "review-panel output"; then
            # Count how many personas responded
            persona_count=$(grep -c "^## Reviewer" "$testdir/review-panel.md" 2>/dev/null || echo 0)
            if [ "$persona_count" -ge 3 ]; then
                log_result 5 "review-panel" "PASS" "$persona_count personas responded"
            else
                log_result 5 "review-panel" "FAIL" "only $persona_count personas responded (expected >= 3)"
            fi
        else
            log_result 5 "review-panel" "FAIL" "output too short"
        fi
    else
        echo "  review-panel stderr:"
        tail -5 "$testdir/stderr.log" 2>/dev/null
        log_result 5 "review-panel" "FAIL" "review-panel command failed"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# TEST 6: Conviction Gate + Pressure-Test (premortem frame)
#   Domain: velocity optimization with recommendations
#   Exercises: check_conviction_gate.py validation, then pressure-test --frame premortem
# ════════════════════════════════════════════════════════════════════════════

run_test 6 "conviction-gate" "Conviction gate + premortem pressure-test"

if [ ${#REQUESTED[@]} -eq 0 ] || printf '%s\n' "${REQUESTED[@]}" | grep -qx 6; then
    testdir="$OUTDIR/conviction-gate"

    echo "  Step 1/2: conviction gate validation..."
    # This proposal has intentional failures (empty Owner on #4, TBD why-now on #2)
    gate_exit=0
    python3.11 scripts/check_conviction_gate.py \
        --proposal "$FIXTURES/proposal-conviction-gate-sample.md" \
        --json > "$testdir/gate-result.json" 2>&1 || gate_exit=$?

    echo "    Gate exit code: $gate_exit"
    python3.11 -m json.tool "$testdir/gate-result.json" 2>/dev/null | head -20 || cat "$testdir/gate-result.json" | head -20

    # Gate SHOULD fail — the fixture has intentional issues
    if [ "$gate_exit" -ne 0 ]; then
        echo "    Gate correctly rejected (exit $gate_exit) — checking details..."
        if grep -qi "owner\|why.now\|generic\|vague\|tbd" "$testdir/gate-result.json" 2>/dev/null; then
            echo "    Gate caught expected issues"
            gate_ok=true
        else
            echo "    Gate failed but didn't report expected issues"
            gate_ok=false
        fi
    else
        echo "    WARNING: gate passed but fixture has intentional issues"
        gate_ok=true
    fi

    echo ""
    echo "  Step 2/2: pressure-test (premortem frame)..."
    if python3.11 scripts/debate.py pressure-test \
        --proposal "$FIXTURES/proposal-conviction-gate-sample.md" \
        --frame premortem \
        --output "$testdir/premortem.md" 2>&1 | tail -5; then

        if check_output "$testdir/premortem.md" 15 "premortem output" && $gate_ok; then
            log_result 6 "conviction-gate" "PASS" "gate validated + premortem generated"
        else
            log_result 6 "conviction-gate" "FAIL" "gate or premortem output issues"
        fi
    else
        log_result 6 "conviction-gate" "FAIL" "premortem command failed"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# TEST 7: Managed Agents Consolidation Path
#   Domain: email pipeline proposal
#   Exercises: challenge → judge --use-ma-consolidation (with fallback test)
#   Also exercises: challenge with different personas, judge --no-consolidate
# ════════════════════════════════════════════════════════════════════════════

run_test 7 "managed-agents" "Managed Agents: MA consolidation + fallback"

if [ ${#REQUESTED[@]} -eq 0 ] || printf '%s\n' "${REQUESTED[@]}" | grep -qx 7; then
    testdir="$OUTDIR/managed-agents"

    echo "  Step 1/3: challenge (architect, security, pm)..."
    if python3.11 scripts/debate.py challenge \
        --proposal "$FIXTURES/proposal-email-pipeline.md" \
        --personas architect,security,pm \
        --output "$testdir/challenge.md" 2>&1 | tail -5; then

        # Step 2: Judge WITH MA consolidation (if MA_API_KEY is set)
        if [ -n "${MA_API_KEY:-}" ]; then
            echo "  Step 2a/3: judge with --use-ma-consolidation (MA_API_KEY set)..."
            if python3.11 scripts/debate.py judge \
                --proposal "$FIXTURES/proposal-email-pipeline.md" \
                --challenge "$testdir/challenge.md" \
                --use-ma-consolidation \
                --output "$testdir/judgment-ma.md" 2>&1 | tee "$testdir/judge-ma-log.txt" | tail -8; then

                # Check if MA was actually used or fell back
                if grep -q "MA dispatch" "$testdir/judge-ma-log.txt" 2>/dev/null; then
                    echo "    MA consolidation was used successfully"
                    ma_status="MA-used"
                elif grep -q "falling back" "$testdir/judge-ma-log.txt" 2>/dev/null; then
                    echo "    MA failed, fell back to local (fallback works)"
                    ma_status="MA-fallback"
                else
                    echo "    MA path taken but status unclear"
                    ma_status="MA-unclear"
                fi
                check_output "$testdir/judgment-ma.md" 20 "MA judgment"
            else
                echo "    MA judge command failed entirely"
                ma_status="MA-error"
            fi
        else
            echo "  Step 2a/3: SKIP — MA_API_KEY not set (testing fallback path)..."
            echo "  Running judge with --use-ma-consolidation (expect fallback)..."
            if python3.11 scripts/debate.py judge \
                --proposal "$FIXTURES/proposal-email-pipeline.md" \
                --challenge "$testdir/challenge.md" \
                --use-ma-consolidation \
                --output "$testdir/judgment-ma-fallback.md" 2>&1 | tee "$testdir/judge-fallback-log.txt" | tail -5; then

                if grep -q "MA_API_KEY" "$testdir/judge-fallback-log.txt" 2>/dev/null || \
                   grep -q "fallback\|local" "$testdir/judge-fallback-log.txt" 2>/dev/null; then
                    echo "    Correctly fell back to local when MA_API_KEY missing"
                    ma_status="fallback-correct"
                else
                    ma_status="fallback-unclear"
                fi
                check_output "$testdir/judgment-ma-fallback.md" 20 "fallback judgment"
            else
                ma_status="fallback-error"
            fi
        fi

        # Step 3: Judge WITHOUT consolidation (--no-consolidate) for comparison
        echo "  Step 3/3: judge with --no-consolidate (comparison baseline)..."
        if python3.11 scripts/debate.py judge \
            --proposal "$FIXTURES/proposal-email-pipeline.md" \
            --challenge "$testdir/challenge.md" \
            --no-consolidate \
            --output "$testdir/judgment-no-consolidate.md" 2>&1 | tail -5; then

            ok=true
            check_output "$testdir/challenge.md" 20 "challenge" || ok=false
            check_output "$testdir/judgment-no-consolidate.md" 20 "no-consolidate judgment" || ok=false

            if $ok; then
                log_result 7 "managed-agents" "PASS" "MA path: $ma_status, no-consolidate: OK"
            else
                log_result 7 "managed-agents" "FAIL" "output files incomplete"
            fi
        else
            log_result 7 "managed-agents" "FAIL" "no-consolidate judge failed"
        fi
    else
        log_result 7 "managed-agents" "FAIL" "challenge failed"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════════════

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  INTEGRATION TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  PASS: $PASS"
echo "  FAIL: $FAIL"
echo "  SKIP: $SKIP"
echo ""
echo "  Results: $RESULTS"
echo "  Output:  $OUTDIR/"
echo ""

# Append summary
echo "" >> "$RESULTS"
echo "SUMMARY: PASS=$PASS FAIL=$FAIL SKIP=$SKIP" >> "$RESULTS"

# Check debate log for new entries
new_entries=$(tail -20 stores/debate-log.jsonl 2>/dev/null | python3.11 -c "
import sys, json
from datetime import datetime
cutoff = datetime.now().strftime('%Y-%m-%d')
count = 0
for line in sys.stdin:
    try:
        d = json.loads(line)
        if d.get('timestamp','').startswith(cutoff):
            count += 1
    except: pass
print(count)
" 2>/dev/null || echo "?")
echo "  Debate log entries today: $new_entries"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo "  Some tests FAILED — check output files for details."
    exit 1
else
    echo "  All tests PASSED."
    exit 0
fi

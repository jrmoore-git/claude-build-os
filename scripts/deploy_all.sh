#!/bin/bash
# deploy_all.sh — Full deploy: skills + services + frontend + tests.
#
# Sequential. Stops on first failure. No auto-detection.
# The developer (human or Claude) decides which to run based on what changed.
# This script runs everything.
#
# Usage: bash scripts/deploy_all.sh
# TEMPLATE: This script is a starting point for your project's deploy pipeline.
# Customize the TODO sections below for your infrastructure (systemctl, launchctl,
# docker compose, etc.). Step 5 (contract tests) works out of the box.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

STEP=0
STEPS_COMPLETED=""

fail() {
    echo ""
    echo "FAILED at step $STEP."
    [ -n "$STEPS_COMPLETED" ] && echo "  Completed: $STEPS_COMPLETED"
    echo "  Fix the error above, then re-run: bash scripts/deploy_all.sh"
    exit 1
}
trap fail ERR

echo "=== Full Deploy ==="
echo "$(date): Starting full deploy sequence"

# Step 1: Deploy skills (service restart)
STEP=1
echo ""
echo "──── Step 1/5: Deploy skills (service restart) ────"
bash "$SCRIPT_DIR/deploy_skills.sh"
STEPS_COMPLETED="gateway"

# Step 2: Restart API server (picks up new code)
STEP=2
echo ""
echo "──── Step 2/5: Restart API server ────"
# Replace with your service restart command, e.g.:
#   systemctl restart my-api-server
#   launchctl stop/start com.myapp.api-server
#   docker compose restart api-server
echo "TODO: Add your API server restart command here"
sleep 3

# Verify health endpoint
if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
    echo "API server healthy post-restart"
else
    echo "FAIL: API server failed to restart"
    exit 1
fi
STEPS_COMPLETED="gateway, api-server"

# Step 3: Deploy frontend (build + restart + smoke test)
STEP=3
echo ""
echo "──── Step 3/5: Deploy frontend ────"
# Replace with your frontend deploy script:
#   bash "$SCRIPT_DIR/deploy_frontend.sh"
echo "TODO: Add your frontend deploy command here"
STEPS_COMPLETED="gateway, api-server, frontend"

# Step 4: Full test suite
STEP=4
echo ""
echo "──── Step 4/5: Full test suite ────"
# Replace with your app test runner:
#   bash "$PROJECT_DIR/app/tests/run_all.sh"
echo "TODO: Add your test suite command here"
STEPS_COMPLETED="gateway, api-server, frontend, app-tests"

# Step 5: Contract tests (behavioral invariants — self-contained, no running services needed)
STEP=5
echo ""
echo "──── Step 5/5: Contract tests ────"
bash "$PROJECT_DIR/tests/run_all.sh"

echo ""
echo "=== All deploys verified ==="
echo "$(date): Deploy complete — all tests passed"

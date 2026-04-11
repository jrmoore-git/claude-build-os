#!/bin/bash
# deploy_skills.sh — Restart gateway to apply skill/config changes
#
# Many AI frameworks cache skill definitions in memory at startup.
# File changes on disk are NOT live until the service restarts.
# Run this after any skill edit before verifying the fix.
#
# Usage: bash scripts/deploy_skills.sh [--verify <job-id>]
# TEMPLATE: Customize the SERVICE_NAME, stop/start commands, and health check
# for your gateway/agent service. The structure (stop → wait → start → health check)
# is the recommended pattern.

set -euo pipefail

# --- Configuration: adapt these to your setup ---
# SERVICE_NAME: the name of your gateway/agent service
# SERVICE_PORT: the port your gateway listens on
# SERVICE_STOP_CMD / SERVICE_START_CMD: how to stop/start the service
#   Examples:
#     launchctl stop/start com.myapp.gateway
#     systemctl stop/start myapp-gateway
#     docker compose stop/start gateway
SERVICE_NAME="gateway"
SERVICE_PORT=18789

echo "Restarting $SERVICE_NAME to apply skill changes..."

# Stop the service (replace with your stop command)
# launchctl stop com.myapp.gateway 2>/dev/null || true
echo "TODO: Add your service stop command here"

# Wait for process to actually exit (max 10s)
for i in $(seq 1 10); do
    if ! pgrep -f "$SERVICE_NAME" > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Start the service (replace with your start command)
# launchctl start com.myapp.gateway
echo "TODO: Add your service start command here"
echo "$SERVICE_NAME starting..."
sleep 5

# Health check
GW_OK=false
for i in $(seq 1 5); do
    if curl -sf --max-time 3 "http://127.0.0.1:$SERVICE_PORT/" > /dev/null 2>&1; then
        GW_OK=true
        break
    fi
    sleep 2
done
if $GW_OK; then
    echo "$SERVICE_NAME healthy post-restart"
else
    echo "FAIL: $SERVICE_NAME did not start — check service logs"
    exit 1
fi

echo "Skill changes are now live."

# Optional: verify a specific cron/scheduled job's output
if [ "${1:-}" = "--verify" ] && [ -n "${2:-}" ]; then
    JOB_ID="$2"
    echo ""
    echo "Triggering job $JOB_ID..."
    # Replace with your job trigger command:
    #   your-cli cron run "$JOB_ID"
    echo "TODO: Add your job trigger command here"
    sleep 10
    echo "Check your job logs for output verification."
fi

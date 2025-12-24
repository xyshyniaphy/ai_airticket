#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[INFO] Starting AI Air Ticket Search (Development Mode)..."
echo "------------------------------------------------------------"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "------------------------------------------------------------"

if [ ! -f ".env" ]; then
    echo "[ERROR] Environment file '.env' not found."
    exit 1
fi
echo "[SUCCESS] Found '.env' file."

mkdir -p logs

echo "[INFO] Running with docker-compose.dev.yml..."
echo "------------------------------------------------------------"

docker compose -f docker-compose.dev.yml run --rm ai-air-ticket-dev

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "[SUCCESS] Dev run completed!"
else
    echo "[ERROR] Dev run failed with exit code $EXIT_CODE."
    exit 1
fi

echo "------------------------------------------------------------"
echo "End Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"

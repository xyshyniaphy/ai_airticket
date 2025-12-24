#!/bin/bash

# ====================================================================
# AI Air Ticket Search - Daily Batch Runner
# ====================================================================
# This script runs the air ticket scraper once using Docker Compose.
# It's designed to be executed daily via crontab.
#
# CRONTAB SETUP:
# Add this script to your crontab to run daily at a specific time.
# Example: Run every day at 9:00 AM
#   0 9 * * * /home/lmr/ws/ai_airticket/run_batch.sh >> /home/lmr/ws/ai_airticket/logs/batch.log 2>&1
#
# Example: Run every day at 6:00 PM and 11:00 PM
#   0 18,23 * * * /home/lmr/ws/ai_airticket/run_batch.sh >> /home/lmr/ws/ai_airticket/logs/batch.log 2>&1
#
# Example: Run every 6 hours
#   0 */6 * * * /home/lmr/ws/ai_airticket/run_batch.sh >> /home/lmr/ws/ai_airticket/logs/batch.log 2>&1
#
# TO EDIT CRONTAB:
#   crontab -e
#
# TO LIST CRONTAB:
#   crontab -l
# ====================================================================

set -e
set -o pipefail

# --- Script Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Helper Functions for Colored Output ---
print_info() {
    echo -e "\n\e[34m[INFO]\e[0m $1"
}

print_success() {
    echo -e "\e[32m[SUCCESS]\e[0m $1"
}

print_error() {
    echo -e "\n\e[31m[ERROR]\e[0m $1" >&2
    exit 1
}

# --- Main Script Logic ---
print_info "Starting AI Air Ticket Search batch job..."
echo "------------------------------------------------------------"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "------------------------------------------------------------"

# 1. Pre-run Check: Verify the environment file exists
print_info "Checking for environment file..."
if [ ! -f ".env" ]; then
    print_error "Environment file '.env' not found. Please create it before running."
fi
print_success "Found '.env' file."

# 2. Ensure logs directory exists
mkdir -p logs

# 3. Build (if needed) and run the container
print_info "Building and running Docker Compose..."
echo "------------------------------------------------------------"

# Run with --rm to automatically remove the container after completion
docker compose run --rm ai-air-ticket

# 4. Check exit status
if [ $? -eq 0 ]; then
    echo "------------------------------------------------------------"
    print_success "Batch job completed successfully!"
else
    echo "------------------------------------------------------------"
    print_error "Batch job failed with exit code $?. Check logs for details."
fi

echo "------------------------------------------------------------"
echo "End Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "------------------------------------------------------------"

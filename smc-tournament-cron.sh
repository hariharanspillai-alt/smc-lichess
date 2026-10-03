#!/bin/bash
# SMC Lichess Tournament Creator - Cron Job
# Runs every Friday at 8:00 PM IST (14:30 UTC)
# Creates tournaments for the upcoming weekend

# Set working directory
cd "$(dirname "$0")"

# Set PATH to include Python
export PATH="/Users/hariharans/Library/Python/3.9/bin:/usr/local/bin:$HOME/Library/Python/3.9/bin:$PATH"

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

LOG_FILE="$(dirname "$0")/cron.log"

echo "========================================" >> "$LOG_FILE"
echo "$(date): Starting tournament creation" >> "$LOG_FILE"

# Create all tournaments for the week
echo "$(date): Creating week's tournaments..." >> "$LOG_FILE"
python3 smc_tournaments.py week >> "$LOG_FILE" 2>&1

echo "$(date): Tournament creation complete" >> "$LOG_FILE"
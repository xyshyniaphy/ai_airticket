#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Print commands and their arguments as they are executed.
# set -x

# Run the main Python application
echo "Starting AI Air Ticket Agent..."
python /app/main.py

# Keep container running if needed (e.g., for a cron job setup later)
# echo "Script finished. Container will exit."

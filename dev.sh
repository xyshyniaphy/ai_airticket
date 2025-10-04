#!/bin/sh
set -e

# Activate virtual environment
. .venv/bin/activate

# Run the scraper
exec python scraper.py
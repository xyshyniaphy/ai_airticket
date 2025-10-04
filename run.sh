#!/bin/bash
set -e

# Define image name
IMAGE_NAME="ai_airticket_scraper"

# Run the Docker container
echo "Running Docker container..."
docker run --rm --env-file .env $IMAGE_NAME

echo "Docker container stopped."

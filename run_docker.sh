#!/bin/bash
set -e

# Define image name
IMAGE_NAME="ai_airticket_scraper"

# Build the Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# Run the Docker container
echo "Running Docker container..."
docker run --rm --env-file .env $IMAGE_NAME

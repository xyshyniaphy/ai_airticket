#!/bin/bash
set -e

# Define image name
IMAGE_NAME="ai_airticket_scraper"

# Build the Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

echo "Docker image built: ${IMAGE_NAME}"

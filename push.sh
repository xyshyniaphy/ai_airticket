#!/bin/bash
set -e

# Define image name
DOCKER_HUB_USERNAME="xyshyniaphy"
IMAGE_NAME="ai_airticket_scraper"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}"

# 1. Build the Docker image
echo "Building Docker image..."
docker build -t $FULL_IMAGE_NAME .

# 2. Push the image to Docker Hub
echo "Pushing image to Docker Hub..."
docker push $FULL_IMAGE_NAME

echo "Image pushed successfully: ${FULL_IMAGE_NAME}"
#!/bin/bash

# --- Script Configuration ---
# 'set -e' will make the script exit immediately if any command fails.
# 'set -o pipefail' will cause a pipeline to fail if any of its commands fail.
set -e
set -o pipefail

# --- Variables ---
# Define variables at the top for easy configuration.
IMAGE_NAME="ai_airticket_scraper"
CONTAINER_NAME="airticket_scraper_instance" # Giving the container a name makes it easier to manage.
ENV_FILE=".env"

# --- Helper Functions for Colored Output ---
# Makes the script's output easier to read.
print_info() {
    echo -e "\n\e[34m[INFO]\e[0m $1"
}

print_success() {
    echo -e "\e[32m[SUCCESS]\e[0m $1"
}

print_error() {
    echo -e "\e[31m[ERROR]\e[0m $1" >&2
    exit 1
}

# --- Main Script Logic ---
print_info "Starting the Air Ticket Scraper container script..."

# 1. Pre-run Check: Verify the environment file exists.
print_info "Checking for environment file at '${ENV_FILE}'..."
if [ ! -f "$ENV_FILE" ]; then
    print_error "Environment file '${ENV_FILE}' not found. Please create it before running the container."
fi
print_success "Found '${ENV_FILE}'."

# 2. Pre-run Check: Verify the Docker image exists locally.
print_info "Checking if Docker image '${IMAGE_NAME}' exists..."
# 'docker image inspect' will have a non-zero exit code if the image is not found.
# The output is redirected to /dev/null to keep the console clean.
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    print_error "Docker image '${IMAGE_NAME}' not found locally. Did you build it first? Try running: docker build -t ${IMAGE_NAME} ."
fi
print_success "Docker image '${IMAGE_NAME}' is available."

# 3. Run the Docker Container
print_info "Attempting to run the Docker container..."
echo "------------------------------------------------------------"
echo "Container Name: ${CONTAINER_NAME}"
echo "Image Name:     ${IMAGE_NAME}"
echo "Env File:       ${ENV_FILE}"
echo "------------------------------------------------------------"

# The command is built as a string to be printed before execution.
# -it: Attaches your terminal to the container for interactive I/O. THIS IS KEY for seeing detailed output.
# --rm: Automatically removes the container when it exits, keeping your system clean.
# --name: Assigns a predictable name to the running container.
# --env-file: Loads environment variables from the specified file.
DOCKER_COMMAND="docker run -it --shm-size=2g  --rm --name ${CONTAINER_NAME} --env-file ${ENV_FILE} ${IMAGE_NAME}"

print_info "Executing command:"
echo "$DOCKER_COMMAND"
echo "--- Container Output Starts Below ---"

# Execute the command. The application's output will now stream to your console.
$DOCKER_COMMAND

# The script will pause here until the container stops.

echo "--- Container Output Ended ---"
print_success "Docker container exited successfully. Script finished."

# --- For Debugging ---
# If you need to debug by getting a shell INSIDE the container instead of running the entrypoint,
# you can comment out the execution line above and uncomment the one below.
# This is extremely useful for checking file paths, environment variables, and network connectivity.
#
# print_info "DEBUG MODE: Starting a shell inside the container..."
# docker run -it --rm --name ${CONTAINER_NAME}_debug --env-file ${ENV_FILE} --entrypoint /bin/bash ${IMAGE_NAME}
#
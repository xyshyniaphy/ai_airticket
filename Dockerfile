# ---- Build Stage ----
# This stage uses Alpine Linux to build our Python dependencies.
# The build might be slower here as some packages need to be compiled,
# but it allows us to create a very small final image.
FROM python:3.11-alpine AS builder

# Set the working directory
WORKDIR /app

# Install build-time OS dependencies for Alpine.
# 'build-base' is the equivalent of 'build-essential' on Debian.
# We need these to compile packages like lxml from source.
# '--no-cache' flag updates, installs, and cleans in one step.
RUN apk add --no-cache \
    build-base \
    libxml2-dev \
    libxslt-dev

# Set up a virtual environment. This keeps dependencies isolated.
ENV VIRTUAL_ENV=/app/.venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy the requirements file and install dependencies using pip.
# This step will be slower on Alpine because it compiles C extensions.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ---- Final Stage ----
# This stage creates the lean final image for running the application.
FROM python:3.11-alpine

# Set the working directory
WORKDIR /app

# Install only the RUNTIME OS dependencies for Alpine.
# We don't need '-dev' headers or build tools in the final image.
RUN apk add --no-cache \
    libxml2 \
    libxslt \
    chromium \
    chromium-driver

# Create a non-root user for security.
# 'adduser -D' is the standard, secure way to add a system user on Alpine.
RUN adduser -D appuser

# Copy the virtual environment from the builder stage.
COPY --from=builder --chown=appuser:appuser /app/.venv .venv

# Copy the application code and set ownership.
COPY --chown=appuser:appuser . .

# Switch to the non-root user.
USER appuser

# Add the virtual environment's executables to the PATH.
ENV PATH="/app/.venv/bin:$PATH"

# Make the entrypoint script executable.
RUN chmod +x entrypoint.sh

# Set the entrypoint for the container.
ENTRYPOINT ["./entrypoint.sh"]
# ---- Build Stage ----
# This stage installs build tools and Python packages into a virtual environment.
FROM python:3.11-slim AS builder

# Set the working directory
WORKDIR /app

# Install build-time OS dependencies required for compiling Python packages like lxml.
# Using build-essential is a good practice as it bundles gcc, make, etc.
# We clean up the apt cache in the same layer to reduce image size.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up a virtual environment to keep dependencies isolated.
# Using ENV variables makes it easy to reference the venv path.
ENV VIRTUAL_ENV=/app/.venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy the requirements file and install dependencies using pip.
# --no-cache-dir prevents pip from storing wheels, reducing layer size.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ---- Final Stage ----
# This stage creates the lean final image for running the application.
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install only the RUNTIME OS dependencies.
# We don't need the '-dev' headers or build tools in the final image.
# We clean up the apt cache in the same layer.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    chromium \
    chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security purposes.
RUN useradd --create-home --shell /bin/bash appuser

# Copy the virtual environment from the builder stage.
# This brings in all the Python packages without the build tools.
# --chown ensures the new user owns these files.
COPY --from=builder --chown=appuser:appuser /app/.venv .venv

# Copy the application code and set ownership.
# It's recommended to have a .dockerignore file to avoid copying unnecessary files.
COPY --chown=appuser:appuser . .

# Switch to the non-root user.
USER appuser

# Add the virtual environment's executables to the PATH.
# This ensures that commands run in the container use the packages from our venv.
ENV PATH="/app/.venv/bin:$PATH"

# Make the entrypoint script executable.
# This is done by the new user, who owns the file.
RUN chmod +x entrypoint.sh

# Set the entrypoint for the container.
ENTRYPOINT ["./entrypoint.sh"]
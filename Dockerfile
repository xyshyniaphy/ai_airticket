# ---- Build Stage ----
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Create virtual environment using uv
RUN uv venv .venv

# Activate virtual environment and install dependencies
COPY requirements.txt .
RUN . .venv/bin/activate && uv pip install --no-cache-dir -r requirements.txt

# ---- Final Stage ----
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies for lxml and selenium, plus Chinese and emoji fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    chromium \
    chromium-driver \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-wqy-microhei \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv .venv

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["./entrypoint.sh"]
# ---- Build Stage ----
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Create virtual environment
RUN python -m venv .venv

# Activate virtual environment and install dependencies
COPY requirements.txt .
RUN . .venv/bin/activate && uv pip install --no-cache-dir -r requirements.txt

# ---- Final Stage ----
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv .venv

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["./entrypoint.sh"]

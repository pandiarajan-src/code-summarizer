# API-only Dockerfile for multi-container deployment
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install uv for faster Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock LICENSE README.md ./

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ ./app/
COPY config.yaml prompts.yaml ./
COPY .env ./.env

# Create home directory and set permissions
RUN mkdir -p /home/appuser/.cache && \
    chown -R appuser:appuser /app /home/appuser

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check - use environment variable or default
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD sh -c 'curl -f http://localhost:${PORT:-8000}/api/health || exit 1'

# Create startup script
RUN echo '#!/bin/sh\n\
HOST=${HOST:-0.0.0.0}\n\
PORT=${PORT:-8000}\n\
exec /app/.venv/bin/uvicorn app.api_main:app --host "$HOST" --port "$PORT"' > /usr/local/bin/start-api.sh && \
    chmod +x /usr/local/bin/start-api.sh

# Start the API server
CMD ["/usr/local/bin/start-api.sh"]
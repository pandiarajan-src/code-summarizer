# Code Summarizer - Single Container Dockerfile
# Runs both FastAPI backend (port 8000) and Frontend (port 80) in one container

# Multi-stage build for optimized final image
FROM python:3.12-slim AS python-base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
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

# Copy frontend files
COPY frontend/ ./frontend/

# Copy Docker configuration files
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY docker/supervisor/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/scripts/entrypoint.sh /entrypoint.sh

# Create necessary directories and set permissions
RUN mkdir -p /var/log/supervisor /var/run/supervisor \
    && mkdir -p /var/log/nginx /var/lib/nginx /var/lib/nginx/body \
    && mkdir -p /usr/share/nginx/html \
    && cp -r frontend/* /usr/share/nginx/html/ \
    && chown -R appuser:appuser /app /var/log/supervisor /var/run/supervisor \
    && chown -R appuser:appuser /usr/share/nginx/html \
    && chown -R appuser:appuser /var/lib/nginx \
    && chown -R appuser:appuser /etc/nginx \
    && chmod +x /entrypoint.sh

# Create nginx directories with proper permissions
RUN mkdir -p /var/cache/nginx/client_temp \
    && mkdir -p /var/cache/nginx/proxy_temp \
    && mkdir -p /var/cache/nginx/fastcgi_temp \
    && mkdir -p /var/cache/nginx/uwsgi_temp \
    && mkdir -p /var/cache/nginx/scgi_temp \
    && chown -R appuser:appuser /var/cache/nginx \
    && chown -R appuser:appuser /var/log/nginx

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 80 8000

# Health check - use dynamic port from environment
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD sh -c 'curl -f http://localhost/health && curl -f http://localhost:${API_PORT:-8000}/api/health || exit 1'

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
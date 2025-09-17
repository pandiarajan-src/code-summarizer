#!/bin/bash

# Entrypoint script for single-container deployment
# Handles environment setup and starts supervisor

set -e

echo "🐳 Starting Code Summarizer (Single Container Mode)"
echo "📊 Container Mode: ${CONTAINER_MODE:-single}"
echo "🔧 API Host: ${API_HOST:-127.0.0.1}"
echo "🌐 API Port: ${API_PORT:-8000}"

# Create necessary directories
mkdir -p /var/log/supervisor /var/run/supervisor
mkdir -p /var/log/nginx
mkdir -p /var/cache/nginx/client_temp

# Set up environment variables for the application
export PYTHONPATH="/app:${PYTHONPATH}"

# Update frontend configuration based on container mode
if [ "${CONTAINER_MODE}" = "single" ]; then
    echo "🔄 Configuring frontend for single container mode"

    # Inject container mode into frontend
    sed -i "s/window.CONTAINER_MODE || 'development'/window.CONTAINER_MODE || 'single'/g" \
        /usr/share/nginx/html/index.html
fi

# Wait for dependencies (if any)
echo "⏳ Checking system readiness..."

# Validate required environment variables
if [ -z "${OPENAI_API_KEY}" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set. API may not function properly."
fi

# Test if ports are available
if command -v netstat > /dev/null; then
    if netstat -tulpn | grep -q ":8000 "; then
        echo "⚠️  Port 8000 already in use"
    fi
    if netstat -tulpn | grep -q ":80 "; then
        echo "⚠️  Port 80 already in use"
    fi
fi

# Set up permissions for nginx cache and logs
chown -R appuser:appuser /var/cache/nginx 2>/dev/null || true
chown -R appuser:appuser /var/log/nginx 2>/dev/null || true

echo "✅ Initialization complete"
echo "🚀 Starting services..."

# Execute the main command
exec "$@"
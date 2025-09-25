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

# Update frontend configuration based on container mode (run only once)
if [ "${CONTAINER_MODE}" = "single" ] && [ ! -f "/tmp/.config_done" ]; then
    echo "🔄 Configuring frontend for single container mode"

    # Get API port from environment variable
    API_PORT=${API_PORT:-8000}
    API_HOST=${API_HOST:-127.0.0.1}

    # Inject container mode and API port into frontend
    if ! grep -q "window.CONTAINER_MODE || 'single'" /usr/share/nginx/html/index.html; then
        sed -i "s/window.CONTAINER_MODE || 'development'/window.CONTAINER_MODE || 'single'/g" \
            /usr/share/nginx/html/index.html
    fi

    # Set API_PORT as a global variable in the HTML (only if not already done)
    if ! grep -q "window.API_PORT" /usr/share/nginx/html/index.html; then
        sed -i "s|<head>|<head><script>window.API_PORT = '${API_PORT}';</script>|" \
            /usr/share/nginx/html/index.html
    fi

    # Update nginx configuration with dynamic API port (only if port is different from default)
    if [ "${API_PORT}" != "8000" ] || [ "${API_HOST}" != "127.0.0.1" ]; then
        echo "🔧 Updating nginx configuration: ${API_HOST}:${API_PORT}"

        # Copy nginx config to a writable location, modify it, then copy back
        cp /etc/nginx/nginx.conf /tmp/nginx.conf.tmp
        sed "s/server 127.0.0.1:8000;/server ${API_HOST}:${API_PORT};/" \
            /tmp/nginx.conf.tmp > /tmp/nginx.conf.new

        # Copy the modified config back
        if cp /tmp/nginx.conf.new /etc/nginx/nginx.conf 2>/dev/null; then
            echo "✅ Nginx configuration updated successfully"
        else
            echo "⚠️  Could not update nginx config - using default"
        fi

        # Clean up temp files
        rm -f /tmp/nginx.conf.tmp /tmp/nginx.conf.new
    else
        echo "✅ Using default nginx configuration (${API_HOST}:${API_PORT})"
    fi

    # Mark configuration as done
    touch /tmp/.config_done
    echo "✅ Frontend configuration complete"
fi

# Wait for dependencies (if any)
echo "⏳ Checking system readiness..."

# Validate required environment variables
if [ -z "${OPENAI_API_KEY}" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set. API may not function properly."
fi

# Test if ports are available
if command -v netstat > /dev/null; then
    API_PORT=${API_PORT:-8000}
    if netstat -tulpn | grep -q ":${API_PORT} "; then
        echo "⚠️  Port ${API_PORT} already in use"
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
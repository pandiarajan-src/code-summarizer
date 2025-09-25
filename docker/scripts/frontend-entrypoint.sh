#!/bin/sh

# Entrypoint script for frontend-only container
# Handles dynamic configuration injection

set -e

echo "🐳 Starting Code Summarizer Frontend (Multi Container Mode)"
echo "🌐 API Base URL: ${API_BASE_URL:-http://api:8000}"

# Update frontend configuration for multi-container mode
echo "🔄 Configuring frontend for multi-container mode"

# Get API port from environment variable
API_PORT=${API_PORT:-8000}

# Update multi-container configuration to use nginx proxy (keep original fallback)
sed -i "s|multi: \`http://\${hostname}:8000\`|multi: window.location.origin|g" \
    /usr/share/nginx/html/index.html

# Set API_PORT as a global variable in the HTML
sed -i "s|<head>|<head><script>window.API_PORT = '${API_PORT}';</script>|" \
    /usr/share/nginx/html/index.html

# Set container mode to multi
sed -i "s/window.CONTAINER_MODE || 'development'/window.CONTAINER_MODE || 'multi'/g" \
    /usr/share/nginx/html/index.html

# Skip nginx.conf modification - CSP allows api container by default

# Create necessary directories with proper permissions
mkdir -p /tmp/client_temp /tmp/proxy_temp_path /tmp/fastcgi_temp /tmp/uwsgi_temp /tmp/scgi_temp

echo "✅ Frontend configuration complete"
echo "🚀 Starting nginx..."

# Execute the main command
exec "$@"
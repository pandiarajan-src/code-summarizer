# Docker Fix Summary

## Problem
The Docker single container was failing with permission errors when trying to modify `/etc/nginx/nginx.conf`:

```
sed: couldn't open temporary file /etc/nginx/sedGIUDf0: Permission denied
```

## Root Cause
- The Dockerfile copies nginx.conf to `/etc/nginx/nginx.conf` as root
- Then switches to `appuser` (non-root)
- The entrypoint script tries to modify the nginx config as `appuser` but lacks permissions

## Solution Applied
1. **Fixed Dockerfile permissions** (line 56):
   ```dockerfile
   && chown appuser:appuser /etc/nginx/nginx.conf \
   ```

2. **Improved entrypoint script** with better error handling:
   ```bash
   if [ -w "/etc/nginx/nginx.conf" ]; then
       echo "🔧 Updating nginx configuration: ${API_HOST}:${API_PORT}"
       sed -i "s/server 127.0.0.1:8000;/server ${API_HOST}:${API_PORT};/" \
           /etc/nginx/nginx.conf
   else
       echo "⚠️  Cannot write to nginx.conf - using default configuration"
   fi
   ```

3. **Fixed health check** to use dynamic port:
   ```dockerfile
   CMD sh -c 'curl -f http://localhost/health && curl -f http://localhost:${API_PORT:-8000}/api/health || exit 1'
   ```

## Test Commands
```bash
# Clean rebuild
make docker-down
make docker-single-build

# Check logs
docker logs code-summarizer-code-summarizer-1

# Test health
curl http://localhost/health
curl http://localhost:8000/api/health
```

## Files Modified
- `Dockerfile`: Added nginx.conf ownership to appuser
- `docker/scripts/entrypoint.sh`: Added error handling for nginx config
- `Dockerfile`: Fixed hardcoded port in health check
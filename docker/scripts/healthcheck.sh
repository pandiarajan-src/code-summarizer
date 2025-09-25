#!/bin/bash

# Health check script for Code Summarizer containers

set -e

# Default values - use environment variables for port configuration
API_PORT="${API_PORT:-8000}"
API_HOST="${API_HOST:-localhost}"
API_URL="${API_URL:-http://${API_HOST}:${API_PORT}}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost}"
TIMEOUT="${TIMEOUT:-10}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check URL health
check_url() {
    local url="$1"
    local name="$2"
    local timeout="$3"

    if curl -f -s --max-time "${timeout}" "${url}" > /dev/null; then
        echo -e "${GREEN}✓${NC} ${name} is healthy (${url})"
        return 0
    else
        echo -e "${RED}✗${NC} ${name} is unhealthy (${url})"
        return 1
    fi
}

# Function to check API endpoints
check_api() {
    echo "🔍 Checking API health..."

    local base_url="$1"
    local healthy=true

    # Check health endpoint
    if ! check_url "${base_url}/api/health" "API Health" "${TIMEOUT}"; then
        healthy=false
    fi

    # Check supported types endpoint
    if ! check_url "${base_url}/api/analyze/supported-types" "API Supported Types" "${TIMEOUT}"; then
        healthy=false
    fi

    if [ "$healthy" = true ]; then
        echo -e "${GREEN}✅ API is fully healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ API has health issues${NC}"
        return 1
    fi
}

# Function to check frontend
check_frontend() {
    echo "🌐 Checking Frontend health..."

    if check_url "${FRONTEND_URL}/health" "Frontend" "${TIMEOUT}"; then
        echo -e "${GREEN}✅ Frontend is healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ Frontend is unhealthy${NC}"
        return 1
    fi
}

# Main health check logic
main() {
    echo "🏥 Code Summarizer Health Check"
    echo "================================"

    local check_type="${1:-all}"
    local exit_code=0

    case "$check_type" in
        "api")
            if ! check_api "$API_URL"; then
                exit_code=1
            fi
            ;;
        "frontend")
            if ! check_frontend; then
                exit_code=1
            fi
            ;;
        "all"|*)
            if ! check_api "$API_URL"; then
                exit_code=1
            fi
            if ! check_frontend; then
                exit_code=1
            fi
            ;;
    esac

    echo "================================"

    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}🎉 All checks passed!${NC}"
    else
        echo -e "${RED}💥 Health check failed!${NC}"
    fi

    exit $exit_code
}

# Script arguments handling
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [api|frontend|all] [options]"
    echo ""
    echo "Options:"
    echo "  --api-url URL      API base URL (default: http://\$API_HOST:\$API_PORT or http://localhost:8000)"
    echo "  --frontend-url URL Frontend URL (default: http://localhost)"
    echo "  --timeout SECONDS  Request timeout (default: 10)"
    echo ""
    echo "Examples:"
    echo "  $0                           # Check both API and frontend"
    echo "  $0 api                       # Check only API"
    echo "  $0 frontend                  # Check only frontend"
    echo "  $0 --api-url http://api:8000 # Use custom API URL"
    exit 0
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --api-url)
            API_URL="$2"
            shift 2
            ;;
        --frontend-url)
            FRONTEND_URL="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        api|frontend|all)
            CHECK_TYPE="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run the main function
main "${CHECK_TYPE:-all}"
#!/bin/bash

# Code Summarizer - Local Development Server Script
# Starts both API and Frontend for local development

set -e

# Colors for output
BLUE="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

# Default values with environment variable support
API_PORT=${API_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-8080}
API_HOST=${API_HOST:-127.0.0.1}
FRONTEND_HOST=${FRONTEND_HOST:-127.0.0.1}

echo -e "${YELLOW}Finding available ports...${RESET}"

# Function to find next available port
find_available_port() {
    local port=$1
    while lsof -i :$port >/dev/null 2>&1; do
        port=$((port + 1))
    done
    echo $port
}

# Check and adjust ports if needed
ORIGINAL_API_PORT=$API_PORT
API_PORT=$(find_available_port $API_PORT)
if [ $API_PORT -ne $ORIGINAL_API_PORT ]; then
    echo -e "${YELLOW}API port $ORIGINAL_API_PORT was in use, using $API_PORT instead${RESET}"
fi

ORIGINAL_FRONTEND_PORT=$FRONTEND_PORT
FRONTEND_PORT=$(find_available_port $FRONTEND_PORT)
if [ $FRONTEND_PORT -ne $ORIGINAL_FRONTEND_PORT ]; then
    echo -e "${YELLOW}Frontend port $ORIGINAL_FRONTEND_PORT was in use, using $FRONTEND_PORT instead${RESET}"
fi

echo -e "${GREEN}Configuration:${RESET}"
echo "  - API: http://$API_HOST:$API_PORT"
echo "  - Frontend: http://$FRONTEND_HOST:$FRONTEND_PORT"
echo ""

# Export environment variables for the applications
export API_PORT
export FRONTEND_PORT
export API_HOST
export FRONTEND_HOST

echo -e "${BLUE}Starting API server...${RESET}"

# Start API in background
PYTHONPATH=app uv run uvicorn app.api_main:app --host $API_HOST --port $API_PORT --reload &
API_PID=$!

# Wait a moment for API to start
sleep 2

echo -e "${GREEN}API started successfully (PID: $API_PID)${RESET}"
echo -e "${BLUE}Starting Frontend server...${RESET}"

# Open browser after a short delay
(sleep 3 && (open http://$FRONTEND_HOST:$FRONTEND_PORT 2>/dev/null || xdg-open http://$FRONTEND_HOST:$FRONTEND_PORT 2>/dev/null || echo -e "${YELLOW}Please open http://$FRONTEND_HOST:$FRONTEND_PORT in your browser${RESET}")) &

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${RESET}"
    kill $API_PID 2>/dev/null || true
    echo -e "${GREEN}Local development session ended${RESET}"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM EXIT

# Move to frontend directory and prepare
cd frontend
echo -e "${BLUE}Preparing frontend for local development...${RESET}"
echo -e "${GREEN}Frontend will use API at http://$API_HOST:$API_PORT${RESET}"

echo -e "${GREEN}Frontend server starting on port $FRONTEND_PORT${RESET}"
echo -e "${YELLOW}Press Ctrl+C to stop both servers${RESET}"
echo ""

if command -v python3 >/dev/null 2>&1; then
    python3 -m http.server $FRONTEND_PORT --bind $FRONTEND_HOST
elif command -v python >/dev/null 2>&1; then
    python -m http.server $FRONTEND_PORT --bind $FRONTEND_HOST
else
    echo -e "${RED}Error: Python not found. Please install Python to run the frontend server.${RESET}"
    exit 1
fi
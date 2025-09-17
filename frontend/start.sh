#!/bin/bash

# Code Summarizer Frontend Startup Script

set -e

echo "🚀 Starting Code Summarizer Frontend..."

# Check if we're in the right directory
if [ ! -f "index.html" ]; then
    echo "❌ Error: index.html not found. Please run this script from the frontend directory."
    exit 1
fi

# Default port
PORT=${1:-8080}

echo "📁 Frontend directory: $(pwd)"
echo "🌐 Starting web server on port $PORT..."

# Try different methods to serve the frontend
if command -v python3 &> /dev/null; then
    echo "🐍 Using Python 3 HTTP server..."
    python3 -m http.server $PORT
elif command -v python &> /dev/null; then
    echo "🐍 Using Python HTTP server..."
    python -m http.server $PORT
elif command -v npx &> /dev/null; then
    echo "📦 Using npx serve..."
    npx serve . -p $PORT
elif command -v php &> /dev/null; then
    echo "🐘 Using PHP built-in server..."
    php -S localhost:$PORT
else
    echo "❌ No suitable web server found!"
    echo "Please install Python, Node.js, or PHP to serve the frontend."
    echo ""
    echo "Alternatives:"
    echo "1. Open index.html directly in your browser"
    echo "2. Use any other web server to serve this directory"
    echo ""
    echo "Note: Direct file:// access may have CORS limitations with the API."
    exit 1
fi
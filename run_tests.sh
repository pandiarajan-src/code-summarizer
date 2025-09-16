#!/bin/bash

# Test runner script for Code Summarizer
# Usage: ./run_tests.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
COVERAGE=false
VERBOSE=false
FAST=false
FAILED_ONLY=false

# Function to display help
show_help() {
    echo -e "${BLUE}Code Summarizer Test Runner${NC}"
    echo "================================"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help              Show this help message"
    echo "  -u, --unit              Run unit tests only"
    echo "  -i, --integration       Run integration tests only"
    echo "  -c, --coverage          Run tests with coverage report"
    echo "  -v, --verbose           Run tests with verbose output"
    echo "  -f, --fast              Run tests in fast mode (minimal output)"
    echo "  --failed                Run only failed tests from last run"
    echo "  --specific TEST_PATH    Run specific test file or pattern"
    echo ""
    echo "Examples:"
    echo "  $0                      # Run all tests"
    echo "  $0 -u -c               # Run unit tests with coverage"
    echo "  $0 -i -v               # Run integration tests verbosely"
    echo "  $0 --specific tests/unit/core/test_config.py"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -u|--unit)
            TEST_TYPE="unit"
            shift
            ;;
        -i|--integration)
            TEST_TYPE="integration"
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--fast)
            FAST=true
            shift
            ;;
        --failed)
            FAILED_ONLY=true
            shift
            ;;
        --specific)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv is not installed. Please install it first.${NC}"
    echo "Visit: https://github.com/astral-sh/uv"
    exit 1
fi

# Set up test environment
echo -e "${BLUE}Setting up test environment...${NC}"
export PYTHONPATH=app

# Build pytest command
PYTEST_CMD="uv run pytest"

# Determine test path
if [[ -n "$SPECIFIC_TEST" ]]; then
    TEST_PATH="$SPECIFIC_TEST"
    echo -e "${BLUE}Running specific test: $SPECIFIC_TEST${NC}"
elif [[ "$TEST_TYPE" == "unit" ]]; then
    TEST_PATH="tests/unit/"
    echo -e "${BLUE}Running unit tests...${NC}"
elif [[ "$TEST_TYPE" == "integration" ]]; then
    TEST_PATH="tests/integration/"
    echo -e "${BLUE}Running integration tests...${NC}"
else
    TEST_PATH="tests/"
    echo -e "${BLUE}Running all tests...${NC}"
fi

# Add test path
PYTEST_CMD="$PYTEST_CMD $TEST_PATH"

# Add coverage options
if [[ "$COVERAGE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=term-missing --cov-report=html"
    echo -e "${YELLOW}Coverage reporting enabled${NC}"
fi

# Add verbose option
if [[ "$VERBOSE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add fast option
if [[ "$FAST" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -q"
fi

# Add failed only option
if [[ "$FAILED_ONLY" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD --lf"
    echo -e "${YELLOW}Running only failed tests from last run${NC}"
fi

echo ""
echo -e "${YELLOW}Command: $PYTEST_CMD${NC}"
echo ""

# Run tests
if eval $PYTEST_CMD; then
    echo ""
    echo -e "${GREEN}✅ Tests completed successfully!${NC}"

    if [[ "$COVERAGE" == true ]]; then
        echo -e "${GREEN}📊 Coverage report generated in htmlcov/index.html${NC}"
    fi

    exit 0
else
    echo ""
    echo -e "${RED}❌ Tests failed!${NC}"
    exit 1
fi
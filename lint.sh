#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
FIX=false
CHECK_ONLY=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --fix)
      FIX=true
      shift
      ;;
    --check)
      CHECK_ONLY=true
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --fix      Fix issues automatically where possible"
      echo "  --check    Only check, don't fix anything"
      echo "  --verbose  Show verbose output"
      echo "  -h, --help Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

# Function to run command with proper error handling
run_linter() {
    local tool="$1"
    local cmd="$2"
    local fix_cmd="$3"
    
    echo -e "${BLUE}Running $tool...${NC}"
    
    if [ "$VERBOSE" = true ]; then
        echo "Command: $cmd"
    fi
    
    if [ "$CHECK_ONLY" = true ]; then
        if eval "$cmd"; then
            echo -e "${GREEN}✓ $tool passed${NC}"
            return 0
        else
            echo -e "${RED}✗ $tool failed${NC}"
            return 1
        fi
    elif [ "$FIX" = true ] && [ -n "$fix_cmd" ]; then
        if [ "$VERBOSE" = true ]; then
            echo "Fix command: $fix_cmd"
        fi
        if eval "$fix_cmd"; then
            echo -e "${GREEN}✓ $tool fixed issues${NC}"
            return 0
        else
            echo -e "${RED}✗ $tool could not fix all issues${NC}"
            return 1
        fi
    else
        if eval "$cmd"; then
            echo -e "${GREEN}✓ $tool passed${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ $tool found issues (use --fix to auto-fix)${NC}"
            return 1
        fi
    fi
}

# Function to check if uv is available
check_uv() {
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}Error: uv is not installed. Please install it first.${NC}"
        echo "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}🔍 Code Quality Check${NC}"
    echo "==================="
    
    check_uv
    
    # Ensure we have the lint dependencies
    if [ "$VERBOSE" = true ]; then
        echo "Installing/updating lint dependencies..."
    fi
    uv sync --extra lint --quiet
    
    local overall_status=0
    
    # 1. Black - Code formatting
    if ! run_linter "Black (formatting)" \
        "uv run black --check --diff src/" \
        "uv run black src/"; then
        overall_status=1
    fi
    
    # 2. Ruff - Linting and import sorting
    if ! run_linter "Ruff (linting)" \
        "uv run ruff check src/" \
        "uv run ruff check --fix src/"; then
        overall_status=1
    fi
    
    # 3. Ruff - Formatting check
    if ! run_linter "Ruff (formatting)" \
        "uv run ruff format --check src/" \
        "uv run ruff format src/"; then
        overall_status=1
    fi
    
    # 4. MyPy - Type checking
    if ! run_linter "MyPy (type checking)" \
        "uv run mypy src/" \
        ""; then
        overall_status=1
    fi
    
    echo "==================="
    
    if [ $overall_status -eq 0 ]; then
        echo -e "${GREEN}🎉 All checks passed!${NC}"
    else
        echo -e "${RED}❌ Some checks failed.${NC}"
        if [ "$FIX" = false ] && [ "$CHECK_ONLY" = false ]; then
            echo -e "${YELLOW}💡 Run with --fix to automatically fix issues where possible.${NC}"
        fi
    fi
    
    return $overall_status
}

# Run main function
main "$@"
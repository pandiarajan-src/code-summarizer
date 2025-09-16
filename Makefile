# Code Summarizer Makefile
# Requires: uv (https://github.com/astral-sh/uv)

.DEFAULT_GOAL := help
.PHONY: help install install-dev clean lint lint-fix format format-check type-check test test-cov run analyze build publish pre-commit

# Colors
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Variables
PYTHON_VERSION := 3.12
SRC_DIR := app
TEST_DIR := tests

## Help
help: ## Show this help message
	@echo "$(BLUE)Code Summarizer - Development Commands$(RESET)"
	@echo "======================================"
	@echo ""
	@echo "$(GREEN)Setup Commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(install|clean)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Development Commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(lint|format|type)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Testing Commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "test" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Application Commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(run|analyze|build|publish)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Examples:$(RESET)"
	@echo "  make install-dev                    # Set up development environment"
	@echo "  make lint-fix                      # Fix linting issues automatically"
	@echo "  make test-unit                     # Run unit tests only"
	@echo "  make test-integration              # Run integration tests only"
	@echo "  make test-cov                      # Run all tests with coverage"
	@echo "  make test-specific TEST=tests/unit/test_config.py  # Run specific test"
	@echo "  make test-api                      # Test all API endpoints"
	@echo "  make test-api-detailed             # Test API endpoints with detailed results"
	@echo "  make run-api                       # Start API server"
	@echo "  make analyze FILE=main.py          # Analyze a specific file"

## Setup Commands
install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(RESET)"
	uv sync --no-dev

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(RESET)"
	uv sync --dev
	@echo "$(GREEN)Development environment ready!$(RESET)"

clean: ## Clean build artifacts and caches
	@echo "$(BLUE)Cleaning build artifacts...$(RESET)"
	rm -rf build/
	rm -rf dist/
	rm -rf app/*.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf api_test_results_*.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*_summary.md" -delete
	@echo "$(GREEN)Cleanup complete!$(RESET)"

## Linting and Formatting Commands
lint: ## Run all linters (check only)
	@echo "$(BLUE)Running linters...$(RESET)"
	./lint.sh --check

lint-fix: ## Run all linters and fix issues automatically
	@echo "$(BLUE)Running linters with auto-fix...$(RESET)"
	./lint.sh --fix

format: ## Format code with black and ruff
	@echo "$(BLUE)Formatting code...$(RESET)"
	uv run black $(SRC_DIR)/
	uv run ruff format $(SRC_DIR)/
	uv run ruff check --fix $(SRC_DIR)/
	uv run black *.py
	uv run ruff format *.py
	uv run ruff check --fix *.py
	@echo "$(GREEN)Code formatted!$(RESET)"

format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(RESET)"
	uv run black --check --diff $(SRC_DIR)/
	uv run ruff format --check $(SRC_DIR)/
	uv run black --check --diff *.py
	uv run ruff format --check *.py

type-check: ## Run mypy type checker
	@echo "$(BLUE)Running type checker...$(RESET)"
	uv run mypy $(SRC_DIR)/

## Testing Commands
test: ## Run all tests (unit and integration)
	@echo "$(BLUE)Running all tests...$(RESET)"
	PYTHONPATH=app uv run pytest tests/

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(RESET)"
	PYTHONPATH=app uv run pytest tests/unit/

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(RESET)"
	PYTHONPATH=app uv run pytest tests/integration/

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	PYTHONPATH=app uv run pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)Coverage report generated in htmlcov/$(RESET)"

test-cov-unit: ## Run unit tests with coverage report
	@echo "$(BLUE)Running unit tests with coverage...$(RESET)"
	PYTHONPATH=app uv run pytest tests/unit/ --cov=app --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)Coverage report generated in htmlcov/$(RESET)"

test-cov-integration: ## Run integration tests with coverage report
	@echo "$(BLUE)Running integration tests with coverage...$(RESET)"
	PYTHONPATH=app uv run pytest tests/integration/ --cov=app --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)Coverage report generated in htmlcov/$(RESET)"

test-watch: ## Run tests in watch mode (requires pytest-xvs)
	@echo "$(BLUE)Running tests in watch mode...$(RESET)"
	PYTHONPATH=app uv run pytest -f tests/

test-verbose: ## Run tests with verbose output
	@echo "$(BLUE)Running tests with verbose output...$(RESET)"
	PYTHONPATH=app uv run pytest tests/ -v

test-fast: ## Run tests with minimal output (fast mode)
	@echo "$(BLUE)Running tests in fast mode...$(RESET)"
	PYTHONPATH=app uv run pytest tests/ -q

test-failed: ## Run only failed tests from last run
	@echo "$(BLUE)Running only failed tests...$(RESET)"
	PYTHONPATH=app uv run pytest tests/ --lf

test-specific: ## Run specific test file (use TEST=path/to/test)
ifdef TEST
	@echo "$(BLUE)Running test: $(TEST)$(RESET)"
	PYTHONPATH=app uv run pytest $(TEST) -v
else
	@echo "$(RED)Error: TEST parameter required$(RESET)"
	@echo "Usage: make test-specific TEST=tests/unit/test_example.py"
	@exit 1
endif

## Application Commands
run-api: ## Start the API server
	@echo "$(BLUE)Starting Code Summarizer API...$(RESET)"
	PYTHONPATH=app uv run uvicorn app.api_main:app --host 127.0.0.1 --port 8000 --reload

analyze: ## Analyze a file (use FILE=path/to/file)
ifndef FILE
	@echo "$(RED)Error: FILE parameter required$(RESET)"
	@echo "Usage: make analyze FILE=path/to/your/file.py"
	@exit 1
endif
	@echo "$(BLUE)Analyzing $(FILE)...$(RESET)"
	PYTHONPATH=app uv run python -m app.main analyze $(FILE) $(if $(OUTPUT),--output $(OUTPUT),) $(if $(VERBOSE),--verbose,)

version: ## Show version information
	PYTHONPATH=app uv run python -m app.main version

test-api: ## Test all API endpoints
	@echo "$(BLUE)Testing API endpoints...$(RESET)"
	uv run python test_api.py

test-api-detailed: ## Test API endpoints with detailed results
	@echo "$(BLUE)Testing API endpoints with detailed results...$(RESET)"
	uv run python test_api.py --save-results

## Build and Distribution Commands
build: ## Build the package
	@echo "$(BLUE)Building package...$(RESET)"
	uv build
	@echo "$(GREEN)Package built in dist/$(RESET)"

publish-test: ## Publish to test PyPI
	@echo "$(BLUE)Publishing to test PyPI...$(RESET)"
	uv publish --repository testpypi dist/*

publish: ## Publish to PyPI
	@echo "$(BLUE)Publishing to PyPI...$(RESET)"
	uv publish dist/*

## Quality Assurance
pre-commit: install-dev lint test ## Run all quality checks
	@echo "$(GREEN)All quality checks passed!$(RESET)"

ci: pre-commit ## Run all CI checks
	@echo "$(GREEN)CI checks completed successfully!$(RESET)"

## Development Shortcuts
dev-setup: install-dev ## Complete development setup
	@echo "$(BLUE)Setting up development environment...$(RESET)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(YELLOW)Created .env file - please add your API keys$(RESET)"; \
	fi
	@echo "$(GREEN)Development setup complete!$(RESET)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(RESET)"
	@echo "1. Edit .env and add your OpenAI API key"
	@echo "2. Try: make analyze FILE=src/code_summarizer/main.py"

quick-check: format-check lint type-check ## Quick quality check without tests

all-checks: clean install-dev lint test build ## Run comprehensive checks

# Advanced commands
check-deps: ## Check for dependency updates
	@echo "$(BLUE)Checking for dependency updates...$(RESET)"
	uv tree --outdated

upgrade-deps: ## Upgrade dependencies
	@echo "$(BLUE)Upgrading dependencies...$(RESET)"
	uv sync --upgrade

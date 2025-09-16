# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a **Code Summarizer** - an AI-powered tool that analyzes source code files and projects to generate comprehensive markdown summaries. The project supports both CLI and API interfaces.

### Core Components

- **CLI Application** (`app/main.py`): Click-based CLI for analyzing files/directories
- **FastAPI Application** (`app/api_main.py`): REST API service for web integration
- **Dual Architecture**: Both interfaces use the same core services and utilities

### Key Services

- **FileProcessor** (`app/utils/file_processor.py`): Handles file extraction, validation, and preprocessing
- **LLMClient** (`app/services/llm_client.py`): OpenAI API integration with context management
- **ContextManager** (`app/core/context_manager.py`): Token counting and batch optimization
- **MarkdownFormatter** (`app/utils/markdown_formatter.py`): Structured report generation
- **AnalysisService** (`app/services/analysis_service.py`): Core business logic for API

### Configuration System

The project uses a hybrid configuration approach:
- **Legacy YAML** (`config.yaml`, `prompts.yaml`): For CLI and existing components
- **Pydantic Settings** (`app/core/config.py`): For FastAPI with environment variable support
- **Environment Variables**: `.env` file for sensitive data (API keys)

## Development Commands

### Setup
```bash
# Install with development dependencies
uv sync --dev

# Complete development setup (includes .env creation)
make dev-setup
```

### Code Quality
```bash
# Run all linters (check only)
make lint
./lint.sh

# Fix issues automatically
make lint-fix
./lint.sh --fix

# Individual tools
uv run black app/                    # Format code
uv run ruff check app/ --fix         # Lint and fix
uv run mypy app/                     # Type checking
```

### Testing
```bash
# Run all tests (unit + integration)
make test
PYTHONPATH=app uv run pytest

# Run specific test types
make test-unit                     # Unit tests only
make test-integration              # Integration tests only

# Run with coverage
make test-cov                      # All tests with coverage
make test-cov-unit                 # Unit tests with coverage
make test-cov-integration          # Integration tests with coverage

# Additional testing options
make test-verbose                  # Verbose output
make test-fast                     # Fast mode (minimal output)
make test-failed                   # Only failed tests from last run
make test-specific TEST=path/to/test  # Run specific test file

# API testing
make test-api                      # Test all API endpoints
make test-api-detailed             # Test API with detailed results
```

### Running Applications

#### CLI Usage
```bash
# Using uv run (recommended)
uv run code-summarizer analyze myfile.py
uv run code-summarizer analyze project.zip --verbose

# Using make
make analyze FILE=myfile.py
make run-cli ARGS="analyze myfile.py --verbose"

# Direct execution
PYTHONPATH=app uv run python -m app.main analyze myfile.py
```

#### API Server
```bash
# Start API server
make run-api
PYTHONPATH=app uv run uvicorn app.api_main:app --host 127.0.0.1 --port 8000 --reload

# Test API endpoints
make test-api                      # Basic API testing
make test-api-detailed             # Detailed API testing with saved results
uv run python test_api.py          # Direct API testing script
```

## Project Structure

```
app/
├── main.py                      # CLI entry point
├── api_main.py                  # FastAPI application
├── core/                        # Core infrastructure
│   ├── config.py               # Pydantic settings
│   ├── context_manager.py      # Token management
│   └── exceptions.py           # Custom exceptions
├── services/                    # Business logic
│   ├── llm_client.py          # OpenAI integration
│   └── analysis_service.py    # API business logic
├── utils/                       # Utilities
│   ├── file_processor.py      # File handling
│   ├── markdown_formatter.py  # Report generation
│   └── prompt_loader.py       # Prompt management
├── models/                      # Pydantic models
│   ├── requests.py            # API request models
│   └── responses.py           # API response models
└── api/                         # FastAPI routes
    └── routes/
        ├── analyze.py         # Analysis endpoints
        └── health.py          # Health checks
```

## Key Technical Details

### Token Management
The application uses intelligent batching to handle large codebases within LLM context limits:
- Files are batched based on token count using `tiktoken`
- Context windows are managed per model (default: 128K tokens for GPT-4o)
- Large files are truncated while preserving structure

### File Processing
Supports 20+ programming languages with configurable extension filtering:
- Extracts from zip archives automatically
- Excludes common build/cache directories
- Validates file types before processing

### LLM Integration
- OpenAI-compatible API support (configurable base URL)
- Structured prompts loaded from `prompts.yaml`
- Temperature and token limits configurable per environment
- Robust error handling with retries

### Environment Configuration
```bash
# Required environment variables
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional
MODEL_NAME=gpt-4o                          # Optional
```

## Testing Infrastructure

### Test Structure
```
tests/
├── unit/                    # Unit tests for individual components
│   ├── core/               # Core modules (config, context_manager, exceptions)
│   ├── services/           # Service classes (llm_client, analysis_service)
│   ├── utils/              # Utility functions (file_processor, markdown_formatter, prompt_loader)
│   ├── models/             # Pydantic models (requests, responses)
│   └── api/                # API route testing
├── integration/            # End-to-end integration tests
│   ├── test_cli.py        # CLI interface testing
│   └── test_api.py        # API interface testing
└── data/                   # Test data and fixtures
    └── sample.py          # Sample files for testing
```

### Test Categories
- **Unit Tests**: Mock external dependencies, test individual functions/classes
- **Integration Tests**: Test complete workflows, real components interaction
- **API Tests**: Validate FastAPI endpoints, request/response models
- **CLI Tests**: Test command-line interface functionality

### Test Execution Strategy
```bash
# Development cycle testing
make test-unit              # Fast feedback during development
make test-integration       # Full workflow validation
make test-api              # API endpoint validation
make test-cov              # Coverage analysis

# Quality assurance
make pre-commit            # All quality checks including tests
make ci                    # Complete CI pipeline simulation
```

## Development Workflow

### Standard Development Cycle
1. **Code Changes**: Make changes in `app/` directory
2. **Quick Check**: Run `make quick-check` (format + lint + type check)
3. **Unit Test**: Run `make test-unit` for fast feedback
4. **Integration Test**: Run `make test-integration` for full validation
5. **API Test**: Run `make test-api` if API changes were made
6. **Final Validation**: Run `make pre-commit` for complete quality check

### Quality Gates
```bash
# Quick development loop
make lint-fix              # Auto-fix formatting and linting issues
make test-unit             # Fast unit test feedback

# Pre-commit validation
make quick-check           # Format + lint + type check (no tests)
make test                  # All tests (unit + integration)
make test-cov              # Coverage validation

# Complete quality assurance
make pre-commit            # All checks including tests
make ci                    # Full CI pipeline
```

### Python Version
- **Required**: Python 3.12+
- Uses `uv` as the package manager (faster than pip)
- Dependencies locked in `uv.lock`

### Important Notes
- The CLI uses legacy YAML configuration while API uses Pydantic settings
- Both share the same core services through dependency injection
- API responses are structured as Pydantic models for OpenAPI documentation
- File uploads in API are handled with multipart/form-data

## Recent Updates & Features

### Enhanced Testing Framework (Latest)
Comprehensive test suite covering all components:
- **Unit Tests**: `tests/unit/` - Core modules, services, utilities, models, and API routes
- **Integration Tests**: `tests/integration/` - End-to-end CLI and API testing
- **Coverage Reports**: HTML and terminal coverage reporting
- **Test Organization**: Structured by component type with clear separation
- **API Testing Script**: `test_api.py` with detailed endpoint validation

### Improved MarkdownFormatter
Enhanced report generation with:
- **Detailed Function Descriptions**: Comprehensive function analysis including parameters
- **Global Variables**: Detection and documentation of module-level variables
- **Enhanced Structure**: Better organization of code analysis reports
- **Rich Metadata**: Improved file and project metadata extraction

### Comprehensive Documentation
- **README.md**: Complete usage guide with all make commands
- **Makefile**: Full help system with categorized commands and examples
- **Test Documentation**: Detailed testing procedures and examples
- **API Documentation**: OpenAPI/Swagger integration for FastAPI endpoints

### Development Quality Improvements
- **Type Hints**: Strict MyPy configuration with comprehensive type coverage
- **Code Formatting**: Black and Ruff integration with auto-fix capabilities
- **Linting**: Multi-tool linting setup with `./lint.sh` script
- **CI/CD Ready**: Pre-commit hooks and quality gates

### Configuration Enhancements
- **Environment Validation**: Robust .env handling with examples
- **Hybrid Config**: Seamless integration between YAML and Pydantic settings
- **Debug Settings**: Configurable debug modes for development
- **Port Configuration**: Flexible API server configuration

### Key Testing Commands Reference
```bash
# Essential testing commands (always use these)
make test                  # All tests (unit + integration)
make test-cov              # Coverage report generation
make test-api              # API endpoint validation
make test-api-detailed     # Detailed API testing with saved results

# Development testing (use during active development)
make test-unit             # Fast unit tests only
make test-integration      # Integration tests only
make test-specific TEST=tests/unit/core/test_config.py  # Specific test file
make test-failed           # Re-run only failed tests

# Quality assurance (use before commits/PRs)
make pre-commit            # Complete quality check pipeline
make lint-fix              # Auto-fix all linting issues
make quick-check           # Fast quality check (no tests)
```

### File Organization Notes
- **App Structure**: All application code in `app/` directory
- **Test Structure**: Mirror app structure in `tests/unit/` and `tests/integration/`
- **Configuration**: YAML files for CLI, Pydantic settings for API
- **Documentation**: README.md, CLAUDE.md, and inline code documentation
- **Scripts**: Helper scripts (`lint.sh`, `test_api.py`) for development workflow
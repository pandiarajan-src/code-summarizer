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
# Run tests
make test
PYTHONPATH=app uv run pytest

# Run with coverage
make test-cov
PYTHONPATH=app uv run pytest --cov --cov-report=html
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
make test-api
uv run python test_api.py
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

## Development Workflow

1. **Code Changes**: Make changes in `app/` directory
2. **Format**: Run `make lint-fix` or `./lint.sh --fix`
3. **Test**: Run `make test` to ensure functionality
4. **Type Check**: MyPy is configured for strict type checking
5. **Integration**: Test both CLI and API interfaces

### Python Version
- **Required**: Python 3.12+
- Uses `uv` as the package manager (faster than pip)
- Dependencies locked in `uv.lock`

### Important Notes
- The CLI uses legacy YAML configuration while API uses Pydantic settings
- Both share the same core services through dependency injection
- API responses are structured as Pydantic models for OpenAPI documentation
- File uploads in API are handled with multipart/form-data
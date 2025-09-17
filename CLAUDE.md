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

### Backend (API & CLI)
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
│   └── analysis_service.py    # API business logic (CRITICAL: see fix notes)
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

### Frontend (Web Application)
```
frontend/
├── index.html              # Main single-page application
├── css/
│   └── styles.css         # Intel-inspired sky blue theme
├── js/
│   └── app.js            # Application logic and API integration
├── config.js              # Frontend configuration
├── README.md              # Frontend documentation
├── DEPLOYMENT.md          # Deployment guide
├── Dockerfile             # Container configuration
├── nginx.conf            # Production web server config
├── start.sh              # Development server script
├── test_frontend.html    # API testing interface
└── sample_test.py        # Test file for uploads
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

### API Endpoints (Important for Frontend)
All API endpoints are prefixed with `/api`:
- **Health Check**: `GET /api/health`
- **File Upload Analysis**: `POST /api/analyze/upload`
- **Batch Analysis**: `POST /api/analyze/batch/upload`
- **Supported Types**: `GET /api/analyze/supported-types`
- **Validate Files**: `POST /api/analyze/validate`

### Frontend Integration
- **API Base URL**: Default `http://127.0.0.1:8000`
- **CORS**: Enabled for all origins in development
- **File Upload**: Multipart form-data with fields:
  - `files`: File(s) to analyze
  - `output_format`: "markdown", "json", or "both"
  - `verbose`: Boolean flag
  - `extract_archives`: Boolean flag for ZIP extraction

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

## Docker Infrastructure & Deployment

### Docker Architecture

The project provides two Docker deployment strategies:

#### Single Container (`Dockerfile`)
- **Purpose**: Development and simple deployments
- **Components**: FastAPI backend + nginx frontend in one container
- **Ports**: 80 (frontend), 8000 (direct API access)
- **Configuration**: Uses supervisord to manage both services
- **Access**: Frontend serves at root, API proxied at `/api/*`

#### Multi-Container (`docker-compose.multi.yml`)
- **Purpose**: Production and scalable deployments
- **Components**: Separate API and frontend containers
- **API Container**: `docker/api/Dockerfile` - FastAPI only
- **Frontend Container**: `docker/frontend/Dockerfile` - nginx only
- **Networking**: Internal Docker networking with service discovery

### Docker Files Structure
```
docker/
├── api/
│   └── Dockerfile              # API-only container
├── frontend/
│   ├── Dockerfile              # Frontend-only container
│   └── nginx.conf              # Multi-container nginx config
├── nginx/
│   └── nginx.conf              # Single-container nginx config
├── supervisor/
│   └── supervisord.conf        # Single-container process management
└── scripts/
    ├── entrypoint.sh           # Single-container startup
    ├── frontend-entrypoint.sh  # Multi-container frontend startup
    └── healthcheck.sh          # Health check scripts
```

### Docker Environment Configuration

Required environment variables (set in `.env`):
```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional
MODEL_NAME=gpt-4o                          # Optional
DEBUG=false                                # Optional
API_TITLE=Code Summarizer API              # Optional
```

### Docker Compose Files
- **`docker-compose.single.yml`**: Single container deployment
- **`docker-compose.multi.yml`**: Multi-container deployment with API/frontend separation

## Recent Updates & Features

### Docker Infrastructure Overhaul (2025-09-17)
Major improvements to Docker deployment with complete fix for both single and multi-container modes:

#### Fixed Docker Build Issues
**Problem**: `make docker-single-build` and `make docker-multi-build` were failing with multiple errors
**Solutions Implemented**:
1. **Missing Build Dependencies**: Added `LICENSE` and `README.md` to all Dockerfiles (required by pyproject.toml)
2. **`.env.example` Exclusion**: Removed `.env.example` from `.dockerignore` as it's needed for container builds
3. **Dockerfile Case Sensitivity**: Fixed `FROM python:3.12-slim as python-base` to use `AS` (uppercase)
4. **Supervisord Path Issues**: Updated supervisord.conf to use `/app/.venv/bin/uvicorn` instead of `uv run`
5. **Nginx Permission Issues**:
   - Changed nginx PID file location from `/var/run/nginx.pid` to `/var/log/nginx/nginx.pid`
   - Added proper ownership for `/var/lib/nginx` directory
   - Updated supervisord to run nginx as `appuser` instead of `root`

#### Multi-Container Frontend API Connection Fix
**Problem**: Frontend showed "Failed to connect to API" in multi-container mode
**Root Cause**: Frontend was trying to connect to `http://${hostname}:8000` instead of using nginx proxy
**Solutions Implemented**:
1. **Added API Proxy to Frontend nginx**: Updated `docker/frontend/nginx.conf` with `/api/` location block
2. **Fixed Frontend Configuration**: Modified entrypoint script to update multi-container API URL from `http://${hostname}:8000` to `window.location.origin`
3. **Updated CSP Headers**: Removed placeholder from Content-Security-Policy header
4. **Alpine Linux Compatibility**: Changed entrypoint script shebang from `#!/bin/bash` to `#!/bin/sh`

#### Docker Permission and Cache Fixes
**API Container Issues**:
- **uv Cache Permissions**: Created `/home/appuser/.cache` directory with proper ownership
- **Direct Binary Execution**: Changed CMD from `uv run uvicorn` to `/app/.venv/bin/uvicorn` to avoid cache issues

#### Docker Networking and Service Discovery
**Multi-Container Setup**:
- **Internal Networking**: API accessible as `http://api:8000` from frontend container
- **Health Checks**: Both containers have proper health checks with curl commands
- **Dependency Management**: Frontend waits for API health before starting
- **Log Management**: Separate log volumes for each service

#### Current Docker Status
✅ **Single Container**: `make docker-single-build` - Fully functional
- Frontend: `http://localhost`
- API: `http://localhost/api` (proxied) or `http://localhost:8000` (direct - with connection issues)

✅ **Multi-Container**: `make docker-multi-build` - Fully functional
- Frontend: `http://localhost`
- API: `http://localhost:8000` (direct) or `http://localhost/api` (proxied)
- Both containers healthy with proper networking

### Frontend Web Application (Latest - 2025-09-17)
Complete single-page web application for the Code Summarizer API:
- **Location**: `frontend/` directory (isolated from backend)
- **Technology**: Pure HTML/CSS/JavaScript (no framework dependencies)
- **Features**: File upload, progress tracking, markdown preview, download reports
- **Theme**: Intel-inspired sky blue professional design
- **Deployment**: Docker-ready with nginx configuration
- **Testing**: Includes test files and API validation scripts

### Critical API Fix for Markdown Output (2025-09-17)
**Issue**: API was returning incomplete markdown output (only metadata, no function details)
**Root Cause**: `app/services/analysis_service.py` line 159 was only passing `batch_summary` to MarkdownFormatter
**Solution**: Modified to reconstruct full analysis results including file details:
```python
# Fixed code in analysis_service.py
legacy_analysis_results = []
for i, br in enumerate(batch_results):
    batch = batches[i]
    full_result = self.llm_client.analyze_batch(batch)
    legacy_analysis_results.append(full_result)
```
**Impact**: Frontend now receives complete analysis with function descriptions, parameters, and all details

### Enhanced Testing Framework
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
- **Frontend Documentation**: `frontend/README.md` and `frontend/DEPLOYMENT.md`

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
- **Frontend Structure**: Isolated in `frontend/` directory for independent deployment
- **Test Structure**: Mirror app structure in `tests/unit/` and `tests/integration/`
- **Configuration**: YAML files for CLI, Pydantic settings for API
- **Documentation**: README.md, CLAUDE.md, frontend/README.md, frontend/DEPLOYMENT.md
- **Scripts**: Helper scripts (`lint.sh`, `test_api.py`, `frontend/start.sh`) for development workflow

## Troubleshooting Guide

### Common Issues and Solutions

#### API Returns Incomplete Markdown
**Symptom**: API returns only metadata without function details
**Solution**: Check `app/services/analysis_service.py` lines 154-169. Ensure the fix is applied that reconstructs full analysis results:
```python
# The fix reconstructs full results for markdown formatter
for i, br in enumerate(batch_results):
    batch = batches[i]
    full_result = self.llm_client.analyze_batch(batch)
    legacy_analysis_results.append(full_result)
```

#### Frontend Not Connecting to API
**Symptom**: "API Offline" or connection errors
**Solution**:
1. Verify API is running: `make run-api` or `curl http://127.0.0.1:8000/api/health`
2. Check CORS settings in `app/api_main.py`
3. Update API URL in `frontend/index.html` configuration section
4. Ensure all endpoints use `/api` prefix

#### File Upload Fails
**Symptom**: Upload errors or no response
**Solution**:
1. Check file size (default limit: 50MB)
2. Verify file extension is supported (`.py`, `.js`, `.ts`, etc.)
3. Check API logs for detailed error messages
4. Ensure multipart/form-data is used for uploads

#### Markdown Preview Shows Raw Text
**Symptom**: Markdown not rendering properly
**Solution**: Ensure CDN libraries (marked.js, DOMPurify) are loading correctly

#### Empty or Truncated Analysis Results
**Symptom**: Analysis completes but results are minimal
**Solution**:
1. Check OpenAI API key is set correctly
2. Verify LLM client is receiving responses
3. Check token limits in configuration
4. Review `app/services/llm_client.py` for response parsing

### Docker-Specific Issues and Solutions

#### Docker Build Failures
**Symptom**: `make docker-single-build` or `make docker-multi-build` fails during build
**Common Causes and Solutions**:

1. **Missing LICENSE/README.md files**:
   ```bash
   # Error: "License file does not exist: LICENSE"
   # Solution: Ensure LICENSE and README.md exist in project root
   ls -la LICENSE README.md
   ```

2. **`.env.example` not found**:
   ```bash
   # Error: ".env.example: not found"
   # Solution: Check .dockerignore doesn't exclude .env.example
   grep -v "^.env.example$" .dockerignore
   ```

3. **Permission denied errors**:
   ```bash
   # Error: "mkdir() failed (13: Permission denied)"
   # Solution: Check Dockerfile creates directories with proper ownership
   # Ensure appuser has permissions for /var/lib/nginx, /var/log/nginx
   ```

#### Container Startup Issues
**Symptom**: Containers build successfully but fail to start or are unhealthy

1. **API Container Issues**:
   ```bash
   # Check API container logs
   docker logs code-summarizer-api-1

   # Common issues:
   # - uv cache permission denied: Fixed by creating /home/appuser/.cache
   # - Command not found: Use /app/.venv/bin/uvicorn instead of uv run
   ```

2. **Frontend Container Issues**:
   ```bash
   # Check frontend container logs
   docker logs code-summarizer-frontend-1

   # Common issues:
   # - /bin/bash not found: Use #!/bin/sh for Alpine Linux
   # - nginx permission denied: Check nginx runs as appuser with proper directories
   ```

#### Frontend API Connection Issues
**Symptom**: Frontend loads but shows "Failed to connect to API"
**Multi-Container Specific**:
1. **Check API is accessible from frontend container**:
   ```bash
   docker exec code-summarizer-frontend-1 wget -O - http://api:8000/api/health
   ```

2. **Verify nginx proxy configuration**:
   ```bash
   # Should have /api/ location block pointing to api:8000
   docker exec code-summarizer-frontend-1 cat /etc/nginx/nginx.conf | grep -A5 "location /api"
   ```

3. **Check frontend configuration was updated**:
   ```bash
   # Should show "multi: window.location.origin" not "multi: `http://${hostname}:8000`"
   docker exec code-summarizer-frontend-1 grep -A3 -B3 "multi:" /usr/share/nginx/html/index.html
   ```

#### Docker Networking Issues
**Symptom**: Containers can't communicate with each other
**Solutions**:
1. **Verify containers are on same network**:
   ```bash
   docker network ls
   docker network inspect code-summarizer_code-summarizer-net
   ```

2. **Test service discovery**:
   ```bash
   docker exec code-summarizer-frontend-1 nslookup api
   docker exec code-summarizer-api-1 nslookup frontend
   ```

#### Docker Performance Issues
**Symptom**: Containers start slowly or consume excessive resources
**Solutions**:
1. **Check container resource usage**:
   ```bash
   docker stats
   ```

2. **Review health check intervals**:
   ```yaml
   # In docker-compose files, reduce frequency if needed
   healthcheck:
     interval: 30s    # Increase if too frequent
     timeout: 10s
     retries: 3
   ```

#### Docker Cleanup and Reset
**When all else fails**:
```bash
# Complete cleanup and rebuild
make docker-clean
docker system prune -a
docker volume prune
make docker-multi-build  # or docker-single-build
```

## Quick Start Guide

### Running the Complete System

1. **Setup Environment**:
   ```bash
   # Create .env file with API key
   echo "OPENAI_API_KEY=your-key-here" > .env
   ```

2. **Start the API Server**:
   ```bash
   make run-api
   # OR
   PYTHONPATH=app uv run uvicorn app.api_main:app --host 127.0.0.1 --port 8000 --reload
   ```

3. **Start the Frontend**:
   ```bash
   cd frontend
   ./start.sh
   # OR
   python3 -m http.server 8080
   ```

4. **Access the Application**:
   - Frontend: `http://localhost:8080`
   - API Docs: `http://localhost:8000/docs`
   - API Health: `http://localhost:8000/api/health`

### Docker Deployment

The project supports two Docker deployment modes:

#### Single Container (Development/Simple Deployment)
```bash
# Build and start single container (API + Frontend)
make docker-single-build

# Access at:
# - Frontend: http://localhost
# - API: http://localhost/api
```

#### Multi-Container (Production/Scalable Deployment)
```bash
# Build and start multi-container setup (separate API and Frontend)
make docker-multi-build

# Access at:
# - Frontend: http://localhost
# - API: http://localhost:8000 (direct) or http://localhost/api (proxied)
```

#### Docker Management Commands
```bash
# Start existing containers
make docker-single          # Single container mode
make docker-multi            # Multi-container mode

# Stop all containers
make docker-down

# Check container health
make docker-health

# View container logs
make docker-logs

# Clean up Docker resources
make docker-clean
```

### Testing the System

```bash
# Test API endpoints
make test-api

# Test with sample file
curl -X POST -F "files=@tests/data/sample.py" \
     -F "output_format=markdown" \
     http://127.0.0.1:8000/api/analyze/upload
```
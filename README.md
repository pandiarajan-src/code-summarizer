# Code Summarizer

An AI-powered CLI tool that analyzes source code files and projects to generate comprehensive markdown summaries with language detection, dependency analysis, and detailed function/class documentation.

## Features

- **🚀 Single File Analysis**: Analyze individual source code files (`.py`, `.js`, `.cpp`, `.swift`, `.cs`, etc.)
- **📦 Zip Archive Support**: Extract and analyze entire projects from zip files
- **🤖 LLM-Powered**: Uses GPT-4o or compatible models for intelligent code understanding
- **🔍 Smart Batching**: Automatically handles large projects by batching files within token limits
- **📊 Multi-Language Support**: Supports 20+ programming languages
- **📝 Markdown Output**: Generates structured, readable analysis reports
- **🔗 Dependency Tracking**: Identifies relationships between files and external dependencies
- **⚡ Context Management**: Intelligent token counting and content optimization
- **🌐 Web Interface**: Complete frontend web application with file upload and analysis
- **🌙 Dark Mode**: Toggle between light and dark themes with persistent user preferences
- **🐳 Docker Support**: Single and multi-container deployment options

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

## Installation

### Option 1: Using uv (Recommended)

1. **Install uv** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clone and setup the project:**
```bash
git clone <repository-url>
cd code-summarizer
```

3. **Install dependencies and create virtual environment:**
```bash
uv sync
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Option 2: Development Installation

```bash
# Install in development mode
uv sync --dev

# This installs additional development tools:
# - pytest (testing)
# - black (code formatting)
# - ruff (linting)
# - mypy (type checking)
```

## Configuration

### Environment Variables

Create a `.env` file with your API configuration:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o
```

### Configuration File

Modify `config.yaml` to customize analysis settings:

```yaml
llm:
  model: "gpt-4o"
  max_tokens: 4000
  temperature: 0.1
  max_context_tokens: 128000

file_processing:
  supported_extensions:
    - .py
    - .js
    - .ts
    - .cpp
    - .java
    # ... more extensions
```

## Usage

### Using the CLI

#### Option 1: Using uv run (Recommended)

```bash
# Analyze a single file
uv run code-summarizer analyze myfile.py
# Output: myfile_summary.md

# Analyze with custom output
uv run code-summarizer analyze myfile.py --output analysis_report.md

# Analyze a zip archive
uv run code-summarizer analyze project.zip --verbose
# Output: project_summary.md

# Custom configuration
uv run code-summarizer analyze myfile.py --config custom_config.yaml

# Directory analysis
uv run code-summarizer analyze /path/to/project/
```

#### Option 2: Activate virtual environment

```bash
# Activate the virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Run commands directly
code-summarizer analyze myfile.py
code-summarizer analyze project.zip --verbose
```

### Development Commands

#### Using Make (Recommended)

```bash
# Complete development setup
make dev-setup

# Code quality and linting
make lint                    # Check code quality
make lint-fix               # Fix issues automatically
make format                 # Format code with black and ruff
make type-check            # Run mypy type checking

# Testing
make test                  # Run all tests (unit + integration)
make test-unit             # Run unit tests only
make test-integration      # Run integration tests only
make test-cov              # Run tests with coverage report
make test-cov-unit         # Run unit tests with coverage
make test-cov-integration  # Run integration tests with coverage
make test-verbose          # Run tests with verbose output
make test-fast             # Run tests in fast mode (minimal output)
make test-failed           # Run only failed tests from last run
make test-specific TEST=path/to/test  # Run specific test file

# API Testing
make test-api              # Test all API endpoints
make test-api-detailed     # Test API endpoints with detailed results

# Quick checks
make quick-check          # Format + lint + type check (no tests)
make pre-commit           # All quality checks including tests

# Application
make analyze FILE=myfile.py     # Analyze specific file
make run ARGS="--help"         # Run CLI with arguments
make version                   # Show version

# Build and publish
make build                     # Build package
make clean                     # Clean artifacts
```

#### Using Shell Script

```bash
# Comprehensive linting with colored output
./lint.sh                 # Check all linting issues
./lint.sh --fix           # Fix issues automatically
./lint.sh --check         # Check only mode
./lint.sh --verbose       # Verbose output
```

#### Direct UV Commands

```bash
# Individual tools
uv run black src/                    # Format with black
uv run ruff check src/ --fix         # Lint and fix with ruff
uv run mypy src/                     # Type checking
uv run pytest                       # Run tests
```

## Testing

The project includes comprehensive unit and integration tests to ensure code quality and functionality.

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── core/               # Tests for core modules
│   │   ├── test_config.py
│   │   ├── test_context_manager.py
│   │   └── test_exceptions.py
│   ├── services/           # Tests for service classes
│   │   ├── test_llm_client.py
│   │   └── test_analysis_service.py
│   ├── utils/              # Tests for utility functions
│   │   ├── test_file_processor.py
│   │   ├── test_markdown_formatter.py
│   │   └── test_prompt_loader.py
│   ├── models/             # Tests for Pydantic models
│   │   ├── test_requests.py
│   │   └── test_responses.py
│   └── api/                # Tests for API routes
│       └── routes/
│           ├── test_analyze.py
│           └── test_health.py
└── integration/            # Integration tests
    ├── test_cli.py         # CLI integration tests
    └── test_api.py         # API integration tests
```

### Running Tests

#### Basic Test Commands

```bash
# Run all tests
make test

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration

# Run tests with coverage report
make test-cov

# Run specific test file
make test-specific TEST=tests/unit/core/test_config.py

# Run tests in verbose mode
make test-verbose

# Run only failed tests from last run
make test-failed

# API testing
make test-api              # Test all API endpoints
make test-api-detailed     # Test API endpoints with detailed results
```

#### Using the Test Runner Script

```bash
# Run all tests with colored output
./run_tests.sh

# Run unit tests only
./run_tests.sh --unit

# Run integration tests only
./run_tests.sh --integration

# Run tests with coverage
./run_tests.sh --coverage

# Run tests verbosely
./run_tests.sh --verbose

# Run specific test file
./run_tests.sh --specific tests/unit/core/test_config.py

# Run only failed tests from last run
./run_tests.sh --failed

# Combine options
./run_tests.sh --unit --coverage --verbose
```

#### Direct pytest Commands

```bash
# Run all tests
PYTHONPATH=app uv run pytest tests/

# Run with coverage
PYTHONPATH=app uv run pytest tests/ --cov=app --cov-report=html

# Run specific test patterns
PYTHONPATH=app uv run pytest tests/ -k "test_config"

# Run with markers (if defined)
PYTHONPATH=app uv run pytest tests/ -m "unit"
```

### Test Coverage

Generate and view test coverage reports:

```bash
# Generate coverage report
make test-cov

# View HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Writing Tests

#### Unit Test Example

```python
import pytest
from app.core.config import Settings

class TestSettings:
    def test_default_values(self):
        """Test default configuration values."""
        settings = Settings()
        assert settings.api_title == "Code Summarizer API"
        assert settings.debug is False
```

#### Integration Test Example

```python
import pytest
from fastapi.testclient import TestClient
from app.api_main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Test Configuration

Tests use the following conventions:
- Unit tests should mock external dependencies
- Integration tests can use real components but should be isolated
- Use pytest fixtures for common test setup
- Mock API calls in tests to avoid external dependencies

### Environment Variables for Testing

Set these environment variables when running tests:

```bash
# For tests that require API simulation
export OPENAI_API_KEY=test-key

# Run tests
make test
```

## Supported File Types

| Language | Extensions |
|----------|------------|
| Python | `.py` |
| JavaScript/TypeScript | `.js`, `.ts`, `.jsx`, `.tsx` |
| Java | `.java` |
| C/C++ | `.c`, `.cpp`, `.h`, `.hpp` |
| C# | `.cs` |
| Swift | `.swift` |
| Go | `.go` |
| Rust | `.rs` |
| PHP | `.php` |
| Ruby | `.rb` |
| And many more... | |

## Example Output

The tool generates structured markdown reports with the following sections:

```markdown
# Code Analysis: MyProject

## 📊 Overview
- **Languages**: Python, JavaScript
- **Total Files**: 15
- **Total Lines**: 2,847
- **Analysis Date**: 2024-01-15

## 🎯 Project Summary
**Purpose**: Web application backend with API endpoints

## 📁 File Analysis

### `main.py`
**Language**: Python
**Purpose**: Application entry point and server setup
**Complexity**: Moderate

**Functions/Methods/Classes**:
- **`main()`** (function): Starts the Flask server
- **`setup_routes()`** (function): Configures API endpoints
- **`DatabaseManager`** (class): Handles database operations

## 🔗 Dependencies & Relationships
- **`main.py`** imports **`database.py`**: Database connection management
- **`api.py`** imports **`models.py`**: Data model definitions

## 🔧 Technical Details
### Design Patterns
- MVC architecture
- Repository pattern for database access
```

## OpenAI Compatible APIs

This tool works with any OpenAI-compatible API by setting the `OPENAI_BASE_URL` environment variable:

### Local LLMs (via text-generation-webui, LM Studio, etc.)
```env
OPENAI_BASE_URL=http://localhost:5000/v1
OPENAI_API_KEY=not-needed
```

### Other Providers
```env
# Anthropic Claude (via proxy)
OPENAI_BASE_URL=https://api.anthropic.com/v1
OPENAI_API_KEY=your_anthropic_key

# Azure OpenAI
OPENAI_BASE_URL=https://your-resource.openai.azure.com/
OPENAI_API_KEY=your_azure_key
```

## How It Works

### CLI Mode
1. **File Processing**: Extracts code files from input (single file, directory, or zip)
2. **Context Management**: Calculates token usage and creates optimal batches
3. **Language Detection**: Identifies programming languages from extensions and content
4. **LLM Analysis**: Sends batches to LLM for intelligent code analysis
5. **Markdown Generation**: Formats results into structured, readable reports

### Web Interface Mode
1. **File Upload**: Drag-and-drop or browse to select files/archives
2. **Real-time Processing**: Live progress updates during analysis
3. **Interactive Results**: View analysis in-browser with markdown rendering
4. **Download Reports**: Save analysis results as markdown files
5. **Theme Preferences**: Light/dark mode with persistent settings

## Token Management

The tool automatically handles token limits by:
- **Smart Batching**: Groups files that fit within context windows
- **Content Truncation**: Safely truncates large files while preserving structure  
- **Batch Optimization**: Prioritizes important files and maintains relationships

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

### Frontend (Web Application)
```
frontend/
├── index.html              # Main single-page application
├── css/
│   └── styles.css         # Intel-inspired theme with dark mode
├── js/
│   └── app.js            # Application logic and API integration
├── config.js              # Frontend configuration
├── README.md              # Frontend documentation
├── DEPLOYMENT.md          # Deployment guide
├── Dockerfile             # Container configuration
├── nginx.conf            # Production web server config
├── start.sh              # Development server script
└── test_frontend.html    # API testing interface
```

### Configuration & Docker
```
code-summarizer/
├── config.yaml                 # CLI configuration
├── prompts.yaml               # LLM prompts
├── pyproject.toml             # Project metadata & dependencies
├── uv.lock                    # Locked dependencies
├── .env.example               # Environment template
├── Makefile                   # Development commands
├── docker-compose.single.yml  # Single container deployment
├── docker-compose.multi.yml   # Multi-container deployment
├── Dockerfile                 # Single container config
└── docker/                    # Docker infrastructure
    ├── api/Dockerfile         # API-only container
    ├── frontend/Dockerfile    # Frontend-only container
    ├── nginx/nginx.conf       # Single container nginx
    ├── supervisor/supervisord.conf  # Process management
    └── scripts/               # Container scripts
```

## Web Interface

The project includes a complete frontend web application for easy code analysis:

### Features
- **File Upload**: Drag-and-drop interface for files and zip archives
- **Real-time Analysis**: Live progress tracking with detailed status updates
- **Markdown Preview**: In-browser rendering of analysis results
- **Download Reports**: Save analysis as markdown files
- **Dark Mode**: Toggle between light and dark themes
- **Responsive Design**: Works on desktop and mobile devices

### Starting the Web Interface

#### Option 1: Separate API and Frontend
```bash
# Terminal 1: Start API server
make run-api

# Terminal 2: Start frontend (navigate to frontend/ directory)
cd frontend
./start.sh
# OR
python3 -m http.server 8080
```

#### Option 2: Docker Deployment
```bash
# Single container (API + Frontend)
make docker-single-build

# Multi-container (separate API and Frontend)
make docker-multi-build
```

### Access Points
- **Frontend**: `http://localhost:8080` (development) or `http://localhost` (Docker)
- **API Documentation**: `http://localhost:8000/docs`
- **API Health**: `http://localhost:8000/api/health`

## Docker Deployment

The project supports two Docker deployment strategies:

### Single Container (Development/Simple)
```bash
# Build and start single container (API + Frontend)
make docker-single-build

# Access at:
# Frontend: http://localhost
# API: http://localhost/api (proxied) or http://localhost:8000 (direct)
```

### Multi-Container (Production/Scalable)
```bash
# Build and start separate API and Frontend containers
make docker-multi-build

# Access at:
# Frontend: http://localhost
# API: http://localhost:8000 (direct) or http://localhost/api (proxied)
```

### Docker Management
```bash
# Show Docker help
make docker-help

# Stop all containers
make docker-down

# View container logs
make docker-logs

# Check container health
make docker-health

# Clean up Docker resources
make docker-clean
```

## Troubleshooting

### Common Issues

**API Key Errors**:
```bash
Error: OPENAI_API_KEY environment variable is required
```
- Ensure your `.env` file contains a valid API key

**No Supported Files Found**:
```bash
No supported code files found in input
```
- Check that your input contains files with supported extensions
- Verify the zip file extracts properly

**Token Limit Exceeded**:
- The tool automatically handles this by batching files
- Consider increasing `max_context_tokens` in config for larger models

**JSON Parsing Errors**:
- Usually indicates LLM response formatting issues
- Try reducing `temperature` in config for more consistent output

**Frontend Connection Issues**:
- Verify API server is running: `curl http://127.0.0.1:8000/api/health`
- Check CORS settings if accessing from different ports
- For Docker: ensure containers are healthy with `make docker-health`

### Debug Mode

Enable verbose output to see detailed processing information:
```bash
# CLI
uv run code-summarizer analyze myfile.py --verbose

# API
# Use verbose=true in web interface or API requests
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `uv sync --dev`
4. Make your changes
5. Run quality checks: `make test && make lint && make type-check`
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Version History

- **v1.0.0**: Initial release with full LLM-powered analysis
  - Single file and zip archive support
  - 20+ programming languages
  - Smart token management
  - Markdown report generation
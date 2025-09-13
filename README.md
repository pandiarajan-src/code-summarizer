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
make test                  # Run tests
make test-cov             # Run tests with coverage

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

1. **File Processing**: Extracts code files from input (single file, directory, or zip)
2. **Context Management**: Calculates token usage and creates optimal batches
3. **Language Detection**: Identifies programming languages from extensions and content
4. **LLM Analysis**: Sends batches to LLM for intelligent code analysis
5. **Markdown Generation**: Formats results into structured, readable reports

## Token Management

The tool automatically handles token limits by:
- **Smart Batching**: Groups files that fit within context windows
- **Content Truncation**: Safely truncates large files while preserving structure  
- **Batch Optimization**: Prioritizes important files and maintains relationships

## Project Structure

```
code-summarizer/
├── src/code_summarizer/         # Main package
│   ├── __init__.py
│   ├── main.py                  # CLI entry point
│   ├── file_processor.py        # File/zip handling
│   ├── llm_client.py           # OpenAI API integration
│   ├── context_manager.py      # Token management
│   ├── prompts.py              # LLM prompts
│   └── markdown_formatter.py   # Report generation
├── config.yaml                 # Configuration
├── pyproject.toml             # Project metadata & dependencies
├── uv.lock                    # Locked dependencies
├── .env.example               # Environment template
├── .python-version            # Python version
└── README.md                  # Documentation
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

### Debug Mode

Enable verbose output to see detailed processing information:
```bash
uv run code-summarizer analyze myfile.py --verbose
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `uv sync --dev`
4. Make your changes
5. Run quality checks: `uv run pytest && uv run ruff check && uv run black --check src/`
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Version History

- **v1.0.0**: Initial release with full LLM-powered analysis
  - Single file and zip archive support
  - 20+ programming languages
  - Smart token management
  - Markdown report generation
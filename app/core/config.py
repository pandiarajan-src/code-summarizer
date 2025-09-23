"""Core configuration management for FastAPI application."""

import logging
import os
import re
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic import ValidationInfo
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

logger = logging.getLogger(__name__)


def find_env_file() -> str | None:
    """Find .env file in current directory or parent directories."""
    current_dir = Path.cwd()

    # Check current directory and up to 3 parent directories
    for _ in range(4):
        env_file = current_dir / ".env"
        if env_file.exists():
            logger.debug(f"Found .env file at: {env_file}")
            return str(env_file)
        current_dir = current_dir.parent

    # Also check if we're in the app directory, look in parent
    if Path.cwd().name == "app":
        parent_env = Path.cwd().parent / ".env"
        if parent_env.exists():
            logger.debug(f"Found .env file at: {parent_env}")
            return str(parent_env)

    logger.warning(".env file not found")
    return None


class SecuritySettings(BaseSettings):
    """Security-related configuration settings."""

    # CORS Configuration
    cors_origins: str = Field(
        default="http://localhost,http://127.0.0.1,http://localhost:8080,http://localhost:3000",
        description="Comma-separated list of allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: str = Field(default="GET,POST,PUT,DELETE,OPTIONS")
    cors_allow_headers: str = Field(default="*")

    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=60)
    rate_limit_burst: int = Field(default=10)
    upload_rate_limit_requests_per_minute: int = Field(default=10)
    upload_rate_limit_burst: int = Field(default=5)

    # Security Headers
    security_headers_enabled: bool = Field(default=True)
    content_security_policy: str = Field(
        default="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self';"
    )

    # JWT Configuration (for future use)
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key for token signing",
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=30)

    # API Key Security
    api_key_header_name: str = Field(default="X-API-Key")
    require_api_key: bool = Field(default=False)

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        """Validate CORS origins format."""
        if v:
            origins = [origin.strip() for origin in v.split(",")]
            for origin in origins:
                if origin != "*" and not (
                    origin.startswith("http://") or origin.startswith("https://")
                ):
                    raise ValueError(f"Invalid CORS origin format: {origin}")
        return v

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret key strength."""
        if len(v) < 32:
            logger.warning("JWT secret key should be at least 32 characters long")
        if v == "your-secret-key-change-in-production":
            logger.warning(
                "JWT secret key is using default value - change for production!"
            )
        return v


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields to avoid validation errors
        # Explicit environment variable mapping
        env_prefix="",  # No prefix, use exact names
    )

    # API Configuration
    api_title: str = "Code Summarizer API"
    api_version: str = "1.0.0"
    debug: bool = Field(default=False)

    # Server Configuration - Environment-aware host binding
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    reload: bool = Field(default=False)
    container_mode: bool = Field(
        default=False, description="Whether running in container"
    )

    # File Upload Configuration
    max_file_size_mb: int = Field(default=50)
    max_files_per_request: int = Field(default=100)
    allowed_file_types: list[str] = Field(
        default=[
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".cs",
            ".swift",
            ".go",
            ".rs",
            ".php",
            ".rb",
            ".scala",
            ".kt",
            ".dart",
            ".r",
            ".m",
            ".mm",
            ".sh",
            ".sql",
            ".yaml",
            ".yml",
            ".json",
            ".xml",
            ".html",
            ".css",
            ".scss",
            ".less",
            ".vue",
            ".svelte",
        ],
    )

    # LLM Configuration
    openai_api_key: str = Field(
        ...,  # Required field
        alias="OPENAI_API_KEY",
        description="OpenAI API key for LLM access",
    )
    openai_base_url: str | None = Field(
        default=None,
        alias="OPENAI_BASE_URL",
        description="Optional custom OpenAI base URL",
    )
    llm_model: str = Field(
        default="gpt-4o", alias="MODEL_NAME", description="LLM model to use"
    )
    llm_max_tokens: int = Field(default=4000)
    llm_temperature: float = Field(default=0.1)
    llm_max_context_tokens: int = Field(default=128000)

    # Configuration File Paths (for compatibility with existing modules)
    config_file_path: str = Field(default="config.yaml")
    prompts_file_path: str = Field(default="prompts.yaml")

    # File Processing Configuration
    exclude_patterns: list[str] = Field(
        default=[
            "__pycache__",
            ".git",
            ".svn",
            ".hg",
            "node_modules",
            ".DS_Store",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".Python",
            "build",
            "develop-eggs",
            "dist",
            "downloads",
            "eggs",
            ".eggs",
            "lib",
            "lib64",
            "parts",
            "sdist",
            "var",
            "wheels",
            "*.egg-info",
            ".installed.cfg",
            "*.egg",
            ".env",
            ".venv",
            "env",
            "venv",
            "ENV",
            "env.bak",
            "venv.bak",
        ],
    )

    # Analysis Configuration
    enable_batch_processing: bool = Field(default=True)
    max_batch_size: int = Field(default=10)
    enable_markdown_output: bool = Field(default=True)

    # Prompts Configuration
    prompts: dict[str, dict[str, str]] = Field(
        default={
            "language_detection": {
                "prompt": """Analyze the following code files and identify the programming languages used.

Files:
{files_content}

Please respond with a JSON object containing:
- "languages": array of detected programming languages
- "confidence": confidence level (1-10)
- "details": brief explanation of detection

Format your response as valid JSON only."""
            },
            "single_file_analysis": {
                "prompt": """Analyze the following source code file and provide a comprehensive summary.

File: {filename}
Language: {language}
Content:
```{language_lower}
{content}
```

Please provide a detailed analysis in the following JSON format:
{{
    "language": "detected programming language",
    "purpose": "brief description of what this file does",
    "complexity": "simple|moderate|complex",
    "functions": [
        {{
            "name": "function_name",
            "type": "function|method|class",
            "purpose": "what this function does",
            "description": "detailed description",
            "parameters": ["param1", "param2"],
            "line_number": 123
        }}
    ],
    "imports": ["import1", "import2"],
    "dependencies": ["external dependencies identified"],
    "global_variables": ["global_var1", "global_var2"],
    "key_features": ["notable features or patterns"],
    "potential_issues": ["any code issues or concerns"]
}}

Provide detailed analysis focusing on:
1. Function/method/class definitions and their purposes
2. Import statements and dependencies
3. Code structure and patterns
4. Potential issues or improvements"""
            },
            "batch_analysis": {
                "prompt": """Analyze this batch of source code files from a software project.

Files in this batch:
{files_info}

For each file, provide analysis following this structure, then provide an overall summary.

Respond with JSON in this format:
{{
    "batch_summary": {{
        "main_purpose": "overall purpose of this batch of files",
        "patterns": ["common patterns across files"],
        "architecture": "brief description of code architecture"
    }},
    "files": [
        {{
            "filename": "file1.py",
            "language": "Python",
            "purpose": "what this file does",
            "complexity": "simple|moderate|complex",
            "functions": [
                {{
                    "name": "function_name",
                    "type": "function|method|class",
                    "purpose": "what this does",
                    "description": "detailed description",
                    "parameters": ["param1", "param2"],
                    "line_number": 123
                }}
            ],
            "imports": ["dependencies"],
            "dependencies": ["external dependencies"],
            "global_variables": ["global_var1", "global_var2"],
            "key_features": ["notable aspects"],
            "potential_issues": ["any code issues or concerns"]
        }}
    ],
    "relationships": [
        {{
            "from": "file1.py",
            "to": "file2.py",
            "type": "imports|calls|extends",
            "description": "nature of relationship"
        }}
    ]
}}

Focus on:
1. Individual file analysis with functions/classes/methods
2. Cross-file relationships and dependencies
3. Overall architecture and patterns
4. Code organization and structure"""
            },
            "project_summary": {
                "prompt": """Based on the analysis of all files in this project, provide a comprehensive project summary.

Project Information:
- Total Files: {total_files}
- Languages: {languages}
- Analysis Results: {analysis_summary}

Provide a JSON response with:
{{
    "project_summary": {{
        "type": "web application|library|cli tool|mobile app|etc",
        "main_purpose": "what this project does",
        "architecture": "overall architecture description",
        "key_components": ["main components/modules"],
        "technologies": ["frameworks and libraries used"],
        "complexity_assessment": "simple|moderate|complex"
    }},
    "technical_details": {{
        "patterns": ["design patterns used"],
        "dependencies": ["major external dependencies"],
        "entry_points": ["main files or entry points"],
        "data_flow": "how data flows through the system"
    }},
    "code_quality": {{
        "strengths": ["positive aspects"],
        "areas_for_improvement": ["suggestions for improvement"],
        "maintainability": "high|medium|low"
    }}
}}

Provide insights into the overall project structure, purpose, and quality."""
            },
        }
    )

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_api_key(cls, v: str) -> str:
        """Validate OpenAI API key format and presence."""
        if not v:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )

        v = v.strip()

        # Check for placeholder values
        placeholder_values = [
            "your_api_key_here",
            "your-api-key",
            "placeholder",
            "sk-",
            "test",
            "demo",
            "example",
        ]
        if v.lower() in placeholder_values:
            raise ValueError(
                "OPENAI_API_KEY appears to be a placeholder value. "
                "Please set your actual API key."
            )

        # Validate minimum length
        if len(v) < 5:
            raise ValueError(
                "OPENAI_API_KEY appears to be too short. Please check your API key."
            )

        # Validate format for different API providers
        valid_patterns = [
            r"^sk-[a-zA-Z0-9]{48,}$",  # OpenAI format
            r"^[a-zA-Z0-9]{32,}$",  # Azure/Generic format
            r"^gsk_[a-zA-Z0-9]{52}$",  # Groq format
            r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",  # UUID format
        ]

        is_valid_format = any(re.match(pattern, v) for pattern in valid_patterns)

        if not is_valid_format:
            logger.warning(
                f"API key format doesn't match common patterns. "
                f"Length: {len(v)}, Starts with: {v[:10]}..."
            )
            # Don't raise error for custom formats, just warn

        return v

    @field_validator("max_file_size_mb")
    @classmethod
    def validate_max_file_size(cls, v: int) -> int:
        """Validate max file size is reasonable."""
        if v <= 0 or v > 500:
            raise ValueError("max_file_size_mb must be between 1 and 500")
        return v

    @field_validator("llm_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate LLM temperature is in valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("llm_temperature must be between 0.0 and 2.0")
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError("port must be between 1 and 65535")
        return v

    @field_validator("container_mode", mode="before")
    @classmethod
    def validate_container_mode(cls, v) -> bool:
        """Validate and convert container_mode to boolean."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            # Handle string values from environment variables
            return v.lower() in ("true", "1", "yes", "on", "single", "multi")
        return bool(v)

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str, _info: ValidationInfo) -> str:
        """Validate and auto-configure host based on environment."""
        # Check if running in container
        in_container = (
            os.environ.get("CONTAINER_MODE") in ("true", "single", "multi")
            or os.environ.get("DOCKER_CONTAINER") == "true"
            or Path("/.dockerenv").exists()
        )

        if in_container and v == "127.0.0.1":
            logger.info("Container detected: changing host from 127.0.0.1 to 0.0.0.0")
            return "0.0.0.0"
        if not in_container and v == "0.0.0.0":
            logger.info(
                "Local environment detected: changing host from 0.0.0.0 to 127.0.0.1"
            )
            return "127.0.0.1"

        return v

    # Security Settings Integration
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.security.cors_origins.split(",")]

    def to_legacy_config(self) -> dict[str, Any]:
        """Convert to legacy configuration format for existing modules."""
        return {
            "llm": {
                "api_key": self.openai_api_key,
                "base_url": self.openai_base_url,
                "model": self.llm_model,
                "max_tokens": self.llm_max_tokens,
                "temperature": self.llm_temperature,
                "max_context_tokens": self.llm_max_context_tokens,
            },
            "file_processing": {
                "supported_extensions": self.allowed_file_types,
                "exclude_patterns": self.exclude_patterns,
            },
            "analysis": {
                "enable_batch_processing": self.enable_batch_processing,
                "max_batch_size": self.max_batch_size,
                "enable_markdown_output": self.enable_markdown_output,
            },
        }

    def debug_info(self) -> dict[str, Any]:
        """Get debug information about configuration loading."""
        env_file_path = find_env_file()

        debug_data = {
            "current_working_directory": str(Path.cwd()),
            "env_file_found": env_file_path,
            "env_file_exists": Path(env_file_path).exists() if env_file_path else False,
            "environment_variables": {
                "OPENAI_API_KEY": (
                    "***SET***" if os.getenv("OPENAI_API_KEY") else "NOT_SET"
                ),
                "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", "NOT_SET"),
                "MODEL_NAME": os.getenv("MODEL_NAME", "NOT_SET"),
                "PYTHONPATH": os.getenv("PYTHONPATH", "NOT_SET"),
            },
            "configuration_values": {
                "api_key_configured": "***SET***" if self.openai_api_key else "NOT_SET",
                "base_url_configured": self.openai_base_url or "NOT_SET",
                "model_configured": self.llm_model,
                "debug_mode": self.debug,
            },
        }

        if env_file_path:
            try:
                with open(env_file_path) as f:
                    content = f.read()
                    debug_data["env_file_has_api_key"] = "OPENAI_API_KEY=" in content
                    debug_data["env_file_size"] = str(len(content))
            except Exception as e:
                debug_data["env_file_error"] = str(e)

        return debug_data


# Global settings instance
def create_settings() -> Settings:
    """Create settings instance with proper error handling."""
    try:
        logger.debug("Loading application settings...")
        settings_instance = Settings(OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""))
        logger.info("Settings loaded successfully")
        return settings_instance
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")

        # Log debug info if settings failed to load
        env_file_path = find_env_file()
        debug_info = {
            "current_working_directory": str(Path.cwd()),
            "env_file_found": env_file_path,
            "env_file_exists": Path(env_file_path).exists() if env_file_path else False,
            "environment_variables": {
                "OPENAI_API_KEY": (
                    "***SET***" if os.getenv("OPENAI_API_KEY") else "NOT_SET"
                ),
                "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", "NOT_SET"),
                "MODEL_NAME": os.getenv("MODEL_NAME", "NOT_SET"),
                "PYTHONPATH": os.getenv("PYTHONPATH", "NOT_SET"),
            },
        }

        if env_file_path:
            try:
                with open(env_file_path) as f:
                    content = f.read()
                    debug_info["env_file_has_api_key"] = "OPENAI_API_KEY=" in content
            except Exception as file_err:
                debug_info["env_file_error"] = str(file_err)

        import json

        logger.debug(f"Debug info: {json.dumps(debug_info, indent=2)}")

        logger.error("Common solutions:")
        logger.error("1. Ensure .env file exists in project root")
        logger.error("2. Check OPENAI_API_KEY is set in .env file")
        logger.error("3. Restart API server after changing .env")
        logger.error("4. Set PYTHONPATH=app before starting server")

        raise


settings = create_settings()

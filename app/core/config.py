"""Core configuration management for FastAPI application."""

from typing import Any

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields to avoid validation errors
    )

    # API Configuration
    api_title: str = "Code Summarizer API"
    api_version: str = "1.0.0"
    debug: bool = Field(default=False)

    # Server Configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    reload: bool = Field(default=False)

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
    openai_api_key: str | None = Field(default=None)
    openai_base_url: str | None = Field(default=None)
    llm_model: str = Field(default="gpt-4o")
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

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

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


# Global settings instance
settings = Settings()

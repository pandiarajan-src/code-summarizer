"""Core configuration management for FastAPI application."""

from typing import Any

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # API Configuration
    api_title: str = "Code Summarizer API"
    api_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")  # type: ignore[call-overload]

    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")  # type: ignore[call-overload]
    port: int = Field(default=8000, env="PORT")  # type: ignore[call-overload]
    reload: bool = Field(default=False, env="RELOAD")  # type: ignore[call-overload]

    # File Upload Configuration
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")  # type: ignore[call-overload]
    max_files_per_request: int = Field(default=100, env="MAX_FILES_PER_REQUEST")  # type: ignore[call-overload]
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
        env="ALLOWED_FILE_TYPES",  # type: ignore[call-overload]
    )

    # LLM Configuration
    openai_api_key: str | None = Field(default=None, env="OPENAI_API_KEY")  # type: ignore[call-overload]
    openai_base_url: str | None = Field(default=None, env="OPENAI_BASE_URL")  # type: ignore[call-overload]
    llm_model: str = Field(default="gpt-4o", env="LLM_MODEL")  # type: ignore[call-overload]
    llm_max_tokens: int = Field(default=4000, env="LLM_MAX_TOKENS")  # type: ignore[call-overload]
    llm_temperature: float = Field(default=0.1, env="LLM_TEMPERATURE")  # type: ignore[call-overload]
    llm_max_context_tokens: int = Field(default=128000, env="LLM_MAX_CONTEXT_TOKENS")  # type: ignore[call-overload]

    # Configuration File Paths (for compatibility with existing modules)
    config_file_path: str = Field(default="config.yaml", env="CONFIG_FILE_PATH")  # type: ignore[call-overload]
    prompts_file_path: str = Field(default="prompts.yaml", env="PROMPTS_FILE_PATH")  # type: ignore[call-overload]

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
        env="EXCLUDE_PATTERNS",  # type: ignore[call-overload]
    )

    # Analysis Configuration
    enable_batch_processing: bool = Field(default=True, env="ENABLE_BATCH_PROCESSING")  # type: ignore[call-overload]
    max_batch_size: int = Field(default=10, env="MAX_BATCH_SIZE")  # type: ignore[call-overload]
    enable_markdown_output: bool = Field(default=True, env="ENABLE_MARKDOWN_OUTPUT")  # type: ignore[call-overload]

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

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields to avoid validation errors


# Global settings instance
settings = Settings()

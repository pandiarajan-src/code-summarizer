"""Pydantic models for API requests."""

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator


class ConfigOverrides(BaseModel):
    """Configuration overrides for analysis requests."""

    # LLM Configuration
    llm_model: str | None = Field(None, description="LLM model to use")
    llm_max_tokens: int | None = Field(
        None, ge=1, le=8000, description="Maximum tokens for LLM response"
    )
    llm_temperature: float | None = Field(
        None, ge=0.0, le=2.0, description="LLM temperature"
    )

    # Analysis Configuration
    enable_batch_processing: bool | None = Field(
        None, description="Enable batch processing"
    )
    max_batch_size: int | None = Field(
        None, ge=1, le=100, description="Maximum batch size"
    )
    enable_markdown_output: bool | None = Field(
        None, description="Enable markdown output in response"
    )

    # File Processing Configuration
    exclude_patterns: list[str] | None = Field(
        None, description="Patterns to exclude from processing"
    )

    @validator("exclude_patterns")
    def validate_exclude_patterns(cls, v):
        """Validate exclude patterns."""
        if v is not None and len(v) > 50:
            raise ValueError("Too many exclude patterns (max 50)")
        return v


class FileContent(BaseModel):
    """File content for analysis."""

    filename: str = Field(..., description="Name of the file")
    content: str = Field(..., description="Content of the file")
    file_type: str | None = Field(None, description="File type/extension")

    @validator("filename")
    def validate_filename(cls, v):
        """Validate filename."""
        if not v or len(v) > 255:
            raise ValueError("Filename must be 1-255 characters")
        return v

    @validator("content")
    def validate_content(cls, v):
        """Validate file content."""
        if len(v) > 1_000_000:  # 1MB limit for text content
            raise ValueError("File content too large (max 1MB)")
        return v


class AnalysisRequest(BaseModel):
    """Request model for single file analysis."""

    files: list[FileContent] = Field(
        ..., min_items=1, max_items=100, description="Files to analyze"
    )
    config_overrides: ConfigOverrides | None = Field(
        None, description="Configuration overrides"
    )
    output_format: str = Field(
        default="json", pattern="^(json|markdown|both)$", description="Output format"
    )
    verbose: bool = Field(default=False, description="Enable verbose output")

    @validator("files")
    def validate_files(cls, v):
        """Validate files list."""
        if len(v) == 0:
            raise ValueError("At least one file is required")

        # Check for duplicate filenames
        filenames = [f.filename for f in v]
        if len(filenames) != len(set(filenames)):
            raise ValueError("Duplicate filenames not allowed")

        return v


class BatchAnalysisRequest(BaseModel):
    """Request model for batch file analysis."""

    files: list[FileContent] = Field(
        ..., min_items=1, max_items=500, description="Files to analyze in batches"
    )
    config_overrides: ConfigOverrides | None = Field(
        None, description="Configuration overrides"
    )
    output_format: str = Field(
        default="json", pattern="^(json|markdown|both)$", description="Output format"
    )
    verbose: bool = Field(default=False, description="Enable verbose output")
    force_batch: bool = Field(
        default=False, description="Force batch processing even for single files"
    )

    @validator("files")
    def validate_files(cls, v):
        """Validate files list."""
        if len(v) == 0:
            raise ValueError("At least one file is required")

        # Check for duplicate filenames
        filenames = [f.filename for f in v]
        if len(filenames) != len(set(filenames)):
            raise ValueError("Duplicate filenames not allowed")

        return v


class AnalysisFromPathRequest(BaseModel):
    """Request model for analyzing files from server paths."""

    paths: list[str] = Field(
        ..., min_items=1, max_items=10, description="File or directory paths to analyze"
    )
    config_overrides: ConfigOverrides | None = Field(
        None, description="Configuration overrides"
    )
    output_format: str = Field(
        default="json", pattern="^(json|markdown|both)$", description="Output format"
    )
    verbose: bool = Field(default=False, description="Enable verbose output")
    recursive: bool = Field(default=True, description="Recursively process directories")

    @validator("paths")
    def validate_paths(cls, v):
        """Validate paths list."""
        if len(v) == 0:
            raise ValueError("At least one path is required")
        return v


class HealthCheckRequest(BaseModel):
    """Request model for health check (usually no body needed)."""

    detailed: bool = Field(
        default=False, description="Include detailed health information"
    )


class ConfigRequest(BaseModel):
    """Request model for configuration retrieval."""

    include_sensitive: bool = Field(
        default=False, description="Include sensitive configuration values"
    )

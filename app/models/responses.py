"""Pydantic models for API responses."""

from datetime import datetime
from typing import Any
from typing import Union

from pydantic import BaseModel
from pydantic import Field


class ErrorDetail(BaseModel):
    """Error detail model."""

    type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional error details"
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: ErrorDetail = Field(..., description="Error information")
    request_id: str | None = Field(None, description="Request ID for tracing")
    path: str = Field(..., description="Request path")
    method: str = Field(..., description="HTTP method")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )


class FileAnalysisResult(BaseModel):
    """Analysis result for a single file."""

    filename: str = Field(..., description="Name of the analyzed file")
    file_type: str = Field(..., description="Detected file type")
    language: str = Field(..., description="Detected programming language")
    analysis: dict[str, Any] = Field(..., description="Analysis results")
    tokens_used: int = Field(..., description="Number of tokens used for analysis")
    processing_time_seconds: float = Field(
        ..., description="Processing time in seconds"
    )


class BatchAnalysisResult(BaseModel):
    """Analysis result for a batch of files."""

    batch_id: str = Field(..., description="Batch identifier")
    files_count: int = Field(..., description="Number of files in batch")
    batch_summary: dict[str, Any] = Field(..., description="Batch analysis summary")
    individual_analyses: list[FileAnalysisResult] = Field(
        default_factory=list, description="Individual file analyses"
    )
    total_tokens_used: int = Field(..., description="Total tokens used for batch")
    processing_time_seconds: float = Field(
        ..., description="Total processing time in seconds"
    )


class ProjectSummary(BaseModel):
    """Project-level summary."""

    total_files: int = Field(..., description="Total number of files analyzed")
    languages_detected: list[str] = Field(
        ..., description="Programming languages detected"
    )
    project_structure: dict[str, Any] = Field(
        ..., description="Project structure analysis"
    )
    key_insights: list[str] = Field(..., description="Key insights about the project")
    recommendations: list[str] = Field(
        ..., description="Recommendations for improvement"
    )
    technical_debt: dict[str, Any] = Field(
        default_factory=dict, description="Technical debt analysis"
    )
    dependencies: dict[str, list[str]] = Field(
        default_factory=dict, description="Dependencies by language"
    )


class AnalysisResponse(BaseModel):
    """Response model for analysis requests."""

    success: bool = Field(..., description="Whether the analysis was successful")
    analysis_id: str = Field(..., description="Unique identifier for this analysis")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Analysis timestamp"
    )

    # File-level results
    files_analyzed: int = Field(..., description="Number of files analyzed")
    file_results: list[FileAnalysisResult] = Field(
        default_factory=list, description="Individual file analysis results"
    )

    # Batch-level results (if applicable)
    batch_results: list[BatchAnalysisResult] = Field(
        default_factory=list, description="Batch analysis results"
    )

    # Project-level results
    project_summary: ProjectSummary | None = Field(
        None, description="Project-level summary"
    )

    # Metadata
    total_tokens_used: int = Field(..., description="Total tokens used")
    total_processing_time_seconds: float = Field(
        ..., description="Total processing time"
    )
    config_used: dict[str, Any] = Field(
        ..., description="Configuration used for analysis"
    )

    # Optional outputs
    markdown_output: str | None = Field(None, description="Markdown formatted output")


class BatchAnalysisResponse(BaseModel):
    """Response model for batch analysis requests."""

    success: bool = Field(..., description="Whether the batch analysis was successful")
    batch_analysis_id: str = Field(
        ..., description="Unique identifier for this batch analysis"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Analysis timestamp"
    )

    # Batch results
    total_batches: int = Field(..., description="Total number of batches processed")
    batch_results: list[BatchAnalysisResult] = Field(
        ..., description="Results for each batch"
    )

    # Project-level summary
    project_summary: ProjectSummary | None = Field(
        None, description="Project-level summary"
    )

    # Metadata
    total_files_analyzed: int = Field(
        ..., description="Total files analyzed across all batches"
    )
    total_tokens_used: int = Field(
        ..., description="Total tokens used across all batches"
    )
    total_processing_time_seconds: float = Field(
        ..., description="Total processing time"
    )
    config_used: dict[str, Any] = Field(
        ..., description="Configuration used for analysis"
    )

    # Optional outputs
    markdown_output: str | None = Field(None, description="Markdown formatted output")


class HealthResponse(BaseModel):
    """Response model for health checks."""

    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Health check timestamp"
    )
    version: str = Field(..., description="API version")
    uptime_seconds: float | None = Field(None, description="API uptime in seconds")

    # Detailed health info (optional)
    services: dict[str, str] | None = Field(
        None, description="Status of dependent services"
    )
    system_info: dict[str, Any] | None = Field(None, description="System information")


class VersionResponse(BaseModel):
    """Response model for version information."""

    api_version: str = Field(..., description="API version")
    app_version: str = Field(..., description="Application version")
    python_version: str = Field(..., description="Python version")
    build_date: str | None = Field(None, description="Build date")
    commit_hash: str | None = Field(None, description="Git commit hash")


class ConfigResponse(BaseModel):
    """Response model for configuration information."""

    config: dict[str, Any] = Field(..., description="Current configuration")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Configuration timestamp"
    )
    config_sources: list[str] = Field(
        ..., description="Configuration sources (file, env, defaults)"
    )


class FileUploadResponse(BaseModel):
    """Response model for file upload operations."""

    success: bool = Field(..., description="Whether the upload was successful")
    files_uploaded: int = Field(
        ..., description="Number of files successfully uploaded"
    )
    file_details: list[dict[str, Any]] = Field(
        ..., description="Details about uploaded files"
    )
    upload_id: str = Field(..., description="Unique identifier for this upload session")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Upload timestamp"
    )


class ValidationResponse(BaseModel):
    """Response model for validation operations."""

    valid: bool = Field(..., description="Whether the input is valid")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    suggestions: list[str] = Field(
        default_factory=list, description="Suggestions for improvement"
    )


# Union types for flexible responses
AnalysisResponseUnion = Union[AnalysisResponse, BatchAnalysisResponse]
APIResponse = Union[
    AnalysisResponse,
    BatchAnalysisResponse,
    HealthResponse,
    VersionResponse,
    ConfigResponse,
    ErrorResponse,
]

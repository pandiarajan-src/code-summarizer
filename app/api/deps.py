"""Dependency injection for FastAPI routes."""

from functools import lru_cache

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from ..core.config import Settings
from ..core.config import settings
from ..core.exceptions import ConfigurationError
from ..services.analysis_service import AnalysisService
from ..utils.file_handler import FileHandler

# Optional security (can be disabled for now since no auth is required)
security = HTTPBearer(auto_error=False)


@lru_cache
def get_settings() -> Settings:
    """Get application settings (cached)."""
    return settings


async def get_analysis_service(
    current_settings: Settings = Depends(get_settings),
) -> AnalysisService:
    """Get analysis service instance."""
    try:
        return AnalysisService(current_settings)
    except Exception as e:
        raise ConfigurationError(f"Failed to initialize analysis service: {str(e)}")


async def get_file_handler(
    current_settings: Settings = Depends(get_settings),
) -> FileHandler:
    """Get file handler instance."""
    try:
        return FileHandler(current_settings)
    except Exception as e:
        raise ConfigurationError(f"Failed to initialize file handler: {str(e)}")


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    current_settings: Settings = Depends(get_settings),
) -> str | None:
    """Verify API key if authentication is enabled."""
    # For now, return None since authentication is disabled
    # This can be implemented later when authentication is needed
    # Explicitly acknowledge unused parameters
    _ = credentials
    _ = current_settings
    return None


async def validate_llm_configuration(
    current_settings: Settings = Depends(get_settings),
) -> Settings:
    """Validate that LLM configuration is properly set."""
    if not current_settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "LLM service not configured",
                "message": "OpenAI API key is not configured. Please set OPENAI_API_KEY environment variable.",
            },
        )

    return current_settings


async def check_service_health(
    current_settings: Settings = Depends(get_settings),
) -> bool:
    """Check if all services are healthy and configured."""
    try:
        # Basic configuration checks
        return bool(current_settings.openai_api_key)

    except Exception:
        return False


# Composite dependencies for common use cases


async def get_configured_analysis_service(
    current_settings: Settings = Depends(validate_llm_configuration),
) -> AnalysisService:
    """Get analysis service with validated LLM configuration."""
    return AnalysisService(current_settings)


async def get_analysis_dependencies(
    analysis_service: AnalysisService = Depends(get_configured_analysis_service),
    file_handler: FileHandler = Depends(get_file_handler),
) -> tuple[AnalysisService, FileHandler]:
    """Get all dependencies needed for analysis endpoints."""
    return analysis_service, file_handler


# Request validation dependencies


async def validate_request_size(
    current_settings: Settings = Depends(get_settings),
) -> Settings:
    """Validate request size limits."""
    # This could be implemented as middleware instead
    # For now, just return settings for endpoint validation
    return current_settings


# Error handling dependencies


async def get_error_context(
    current_settings: Settings = Depends(get_settings),
) -> dict[str, str | int]:
    """Get context information for error responses."""
    return {
        "api_version": current_settings.api_version,
        "environment": "development" if current_settings.debug else "production",
        "max_file_size_mb": current_settings.max_file_size_mb,
        "max_files_per_request": current_settings.max_files_per_request,
    }

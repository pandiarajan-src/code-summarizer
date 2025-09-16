"""Health and version endpoints for the FastAPI application."""

import sys
import time
from datetime import UTC
from datetime import datetime
from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from ...core.config import Settings
from ...core.config import settings
from ...models.responses import ConfigResponse
from ...models.responses import HealthResponse
from ...models.responses import VersionResponse

router = APIRouter(tags=["Health & Info"])

# Store startup time for uptime calculation
startup_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    detailed: bool = Query(False, description="Include detailed health information"),
    current_settings: Settings = Depends(lambda: settings),
) -> HealthResponse:
    """Get API health status."""
    # Basic health response
    response_data = {
        "status": "healthy",
        "version": current_settings.api_version,
        "uptime_seconds": time.time() - startup_time,
    }

    # Add detailed information if requested
    if detailed:
        try:
            # Check if OpenAI API key is configured
            llm_status = (
                "configured" if current_settings.openai_api_key else "not_configured"
            )

            response_data["services"] = {
                "llm_service": llm_status,
                "file_processing": "available",
                "configuration": "loaded",
            }

            response_data["system_info"] = {
                "python_version": sys.version,
                "platform": sys.platform,
                "settings_loaded": True,
                "config_file": current_settings.config_file_path,
                "prompts_file": current_settings.prompts_file_path,
            }

        except Exception as e:
            response_data["status"] = "degraded"
            response_data["services"] = {"error": str(e)}

    return HealthResponse(
        status=str(response_data["status"]),
        version=str(response_data["version"]),
        uptime_seconds=response_data.get("uptime_seconds"),  # type: ignore[arg-type]
        services=response_data.get("services"),  # type: ignore[arg-type]
        system_info=response_data.get("system_info"),  # type: ignore[arg-type]
    )


@router.get("/version", response_model=VersionResponse)
async def get_version(
    current_settings: Settings = Depends(lambda: settings),
) -> VersionResponse:
    """Get API version information."""
    return VersionResponse(
        api_version=current_settings.api_version,
        app_version="1.0.0",  # This could be read from __init__.py or environment
        python_version=sys.version,
        build_date=None,  # Could be set during build process
        commit_hash=None,  # Could be set during build process
    )


@router.get("/config", response_model=ConfigResponse)
async def get_config(
    include_sensitive: bool = Query(
        False, description="Include sensitive configuration values"
    ),
    current_settings: Settings = Depends(lambda: settings),
) -> ConfigResponse:
    """Get current API configuration."""
    # Convert settings to dict
    config_dict = current_settings.model_dump()

    # Remove sensitive values if not requested
    if not include_sensitive:
        sensitive_keys = [
            "openai_api_key",
        ]
        for key in sensitive_keys:
            if key in config_dict:
                config_dict[key] = "***" if config_dict[key] else None

    # Add some metadata about configuration sources
    config_sources = ["defaults"]
    if current_settings.config_file_path:
        config_sources.append("config_file")
    config_sources.append("environment")

    return ConfigResponse(config=config_dict, config_sources=config_sources)


@router.get("/info")
async def get_info(
    current_settings: Settings = Depends(lambda: settings),
) -> dict[str, Any]:
    """Get general API information."""
    return {
        "name": current_settings.api_title,
        "version": current_settings.api_version,
        "description": "AI-powered code analysis and summarization tool",
        "endpoints": {
            "health": "/api/v1/health",
            "version": "/api/v1/version",
            "config": "/api/v1/config",
            "analyze": "/api/v1/analyze",
            "batch_analyze": "/api/v1/analyze/batch",
        },
        "documentation": "/docs",
        "openapi": "/openapi.json",
    }


@router.get("/ping")
async def ping() -> dict[str, str]:
    """Simple ping endpoint for basic connectivity testing."""
    return {"message": "pong", "timestamp": datetime.now(UTC).isoformat()}

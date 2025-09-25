"""Analysis endpoints for the FastAPI application."""

import logging
from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import Request
from fastapi import UploadFile
from fastapi import status
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...core.exceptions import AnalysisError
from ...core.exceptions import FileProcessingError
from ...core.exceptions import FileTooLargeError
from ...core.exceptions import TooManyFilesError
from ...core.exceptions import UnsupportedFileTypeError
from ...models.requests import AnalysisFromPathRequest
from ...models.requests import AnalysisRequest
from ...models.requests import BatchAnalysisRequest
from ...models.requests import ConfigOverrides
from ...models.responses import AnalysisResponse
from ...models.responses import BatchAnalysisResponse
from ...services.analysis_service import AnalysisService
from ...utils.file_handler import FileHandler
from ..deps import get_analysis_dependencies

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analysis"])


# Get limiter from app state
def get_limiter(request: Request) -> Limiter:
    """Get the rate limiter from FastAPI app state."""
    return request.app.state.limiter  # type: ignore[no-any-return]


# Create limiter instance for decorator use
limiter = Limiter(key_func=get_remote_address)


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_files(
    request: AnalysisRequest,
    dependencies: tuple[AnalysisService, FileHandler] = Depends(
        get_analysis_dependencies
    ),
) -> AnalysisResponse:
    """Analyze files provided in the request body."""
    analysis_service, _ = dependencies

    try:
        result = await analysis_service.analyze_files(
            files=request.files,
            config_overrides=request.config_overrides,
            custom_prompts=request.custom_prompts,
            output_format=request.output_format,
            verbose=request.verbose,
        )

        return result

    except (AnalysisError, FileProcessingError) as e:
        raise e
    except Exception as e:
        raise AnalysisError(f"Analysis failed: {str(e)}")


@router.post("/analyze/upload", response_model=AnalysisResponse)
@limiter.limit("10/minute")
async def analyze_uploaded_files(
    request: Request,  # noqa: ARG001
    files: list[UploadFile] = File(..., description="Files to analyze"),
    config_overrides: str | None = Form(
        None, description="JSON string of config overrides"
    ),
    custom_prompts: str | None = Form(
        None, description="JSON string of custom prompts"
    ),
    output_format: str = Form(
        "json", description="Output format: json, markdown, or both"
    ),
    verbose: bool = Form(False, description="Enable verbose output"),
    extract_archives: bool = Form(True, description="Extract ZIP archives"),
    dependencies: tuple[AnalysisService, FileHandler] = Depends(
        get_analysis_dependencies
    ),
) -> AnalysisResponse:
    """Analyze uploaded files."""
    analysis_service, file_handler = dependencies

    try:
        # Log request details at debug level
        logger.debug(
            f"Upload analysis request - Files: {len(files)}, "
            f"Output format: {output_format}, Verbose: {verbose}, "
            f"Extract archives: {extract_archives}"
        )
        # Process uploaded files
        file_contents = await file_handler.process_uploaded_files(
            files=files, extract_archives=extract_archives
        )

        # Parse config overrides if provided
        parsed_config_overrides = None
        if config_overrides and config_overrides.strip():
            import json

            try:
                parsed_config_overrides = ConfigOverrides(
                    **json.loads(config_overrides)
                )
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid config overrides JSON: {str(e)}",
                )

        # Parse custom prompts if provided
        parsed_custom_prompts = None
        if custom_prompts and custom_prompts.strip():
            import json

            try:
                parsed_custom_prompts = json.loads(custom_prompts)
                if not isinstance(parsed_custom_prompts, dict):
                    raise ValueError("Custom prompts must be a dictionary")
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid custom prompts JSON: {str(e)}",
                )

        # Analyze files
        result = await analysis_service.analyze_files(
            files=file_contents,
            config_overrides=parsed_config_overrides,
            custom_prompts=parsed_custom_prompts,
            output_format=output_format,
            verbose=verbose,
        )

        return result

    except (FileTooLargeError, UnsupportedFileTypeError, TooManyFilesError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except HTTPException:
        raise  # Re-raise HTTPException without modification
    except (AnalysisError, FileProcessingError) as e:
        raise e
    except Exception as e:
        raise AnalysisError(f"File upload analysis failed: {str(e)}")


@router.post("/analyze/paths", response_model=AnalysisResponse)
async def analyze_from_paths(
    request: AnalysisFromPathRequest,
    dependencies: tuple[AnalysisService, FileHandler] = Depends(
        get_analysis_dependencies
    ),
) -> AnalysisResponse:
    """Analyze files from server file paths."""
    analysis_service, _ = dependencies

    try:
        result = await analysis_service.analyze_from_paths(
            paths=request.paths,
            config_overrides=request.config_overrides,
            custom_prompts=request.custom_prompts,
            output_format=request.output_format,
            verbose=request.verbose,
            recursive=request.recursive,
        )

        return result

    except (AnalysisError, FileProcessingError) as e:
        raise e
    except (FileNotFoundError, OSError, PermissionError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Path error: {str(e)}"
        )
    except Exception as e:
        raise AnalysisError(f"Path analysis failed: {str(e)}")


@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(
    request: BatchAnalysisRequest,
    dependencies: tuple[AnalysisService, FileHandler] = Depends(
        get_analysis_dependencies
    ),
) -> BatchAnalysisResponse:
    """Analyze files in batch mode with enhanced batching strategy."""
    analysis_service, _ = dependencies

    try:
        # For batch analysis, we use the same analyze_files method
        # but the service will handle batching internally
        result = await analysis_service.analyze_files(
            files=request.files,
            config_overrides=request.config_overrides,
            custom_prompts=request.custom_prompts,
            output_format=request.output_format,
            verbose=request.verbose,
        )

        # Convert AnalysisResponse to BatchAnalysisResponse
        # This is a simplified conversion - in a real implementation,
        # you might want more sophisticated batch result handling

        batch_response = BatchAnalysisResponse(
            success=result.success,
            batch_analysis_id=result.analysis_id,
            timestamp=result.timestamp,
            total_batches=len(result.batch_results),
            batch_results=result.batch_results,
            project_summary=result.project_summary,
            total_files_analyzed=result.files_analyzed,
            total_tokens_used=result.total_tokens_used,
            total_processing_time_seconds=result.total_processing_time_seconds,
            config_used=result.config_used,
            markdown_output=result.markdown_output,
        )

        return batch_response

    except (AnalysisError, FileProcessingError) as e:
        raise e
    except Exception as e:
        raise AnalysisError(f"Batch analysis failed: {str(e)}")


@router.post("/analyze/batch/upload", response_model=BatchAnalysisResponse)
@limiter.limit("5/minute")
async def analyze_batch_uploaded_files(
    request: Request,  # noqa: ARG001
    files: list[UploadFile] = File(..., description="Files to analyze in batch"),
    config_overrides: str | None = Form(
        None, description="JSON string of config overrides"
    ),
    custom_prompts: str | None = Form(
        None, description="JSON string of custom prompts"
    ),
    output_format: str = Form(
        "json", description="Output format: json, markdown, or both"
    ),
    verbose: bool = Form(False, description="Enable verbose output"),
    extract_archives: bool = Form(True, description="Extract ZIP archives"),
    force_batch: bool = Form(
        False, description="Force batch processing even for single files"
    ),
    dependencies: tuple[AnalysisService, FileHandler] = Depends(
        get_analysis_dependencies
    ),
) -> BatchAnalysisResponse:
    """Analyze uploaded files in batch mode."""
    analysis_service, file_handler = dependencies

    try:
        # Process uploaded files
        file_contents = await file_handler.process_uploaded_files(
            files=files, extract_archives=extract_archives
        )

        # Parse config overrides if provided
        parsed_config_overrides = None
        if config_overrides and config_overrides.strip():
            import json

            try:
                parsed_config_overrides = ConfigOverrides(
                    **json.loads(config_overrides)
                )
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid config overrides JSON: {str(e)}",
                )

        # Parse custom prompts if provided
        parsed_custom_prompts = None
        if custom_prompts and custom_prompts.strip():
            import json

            try:
                parsed_custom_prompts = json.loads(custom_prompts)
                if not isinstance(parsed_custom_prompts, dict):
                    raise ValueError("Custom prompts must be a dictionary")
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid custom prompts JSON: {str(e)}",
                )

        # Create batch request and analyze
        batch_request = BatchAnalysisRequest(
            files=file_contents,
            config_overrides=parsed_config_overrides,
            custom_prompts=parsed_custom_prompts,
            output_format=output_format,
            verbose=verbose,
            force_batch=force_batch,
        )

        return await analyze_batch(batch_request, dependencies)

    except (FileTooLargeError, UnsupportedFileTypeError, TooManyFilesError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except (AnalysisError, FileProcessingError) as e:
        raise e
    except Exception as e:
        raise AnalysisError(f"Batch file upload analysis failed: {str(e)}")


@router.get("/analyze/supported-types")
async def get_supported_file_types(
    analysis_service: AnalysisService = Depends(
        lambda deps=Depends(get_analysis_dependencies): deps[0]
    ),
) -> dict[str, Any]:
    """Get list of supported file types for analysis."""
    return {
        "supported_extensions": analysis_service.get_supported_file_types(),
        "description": "List of file extensions supported for code analysis",
        "note": "ZIP archives are also supported and will be automatically extracted",
    }


@router.get("/analyze/config")
async def get_analysis_config(
    analysis_service: AnalysisService = Depends(
        lambda deps=Depends(get_analysis_dependencies): deps[0]
    ),
) -> dict[str, Any]:
    """Get current analysis configuration."""
    config = analysis_service.get_current_config()

    # Remove sensitive information
    if "llm" in config and "api_key" in config["llm"]:
        config["llm"]["api_key"] = "***" if config["llm"]["api_key"] else None

    return {"config": config, "description": "Current analysis service configuration"}


@router.get("/prompts")
async def get_default_prompts() -> dict[str, Any]:
    """Get all default prompts from prompts.yaml."""
    try:
        from ...utils.prompt_loader import PromptLoader

        # Load prompts from prompts.yaml
        prompt_loader = PromptLoader("prompts.yaml")

        # Get all prompts
        all_prompts = {
            "language_detection": prompt_loader.get_prompt("language_detection"),
            "single_file_analysis": prompt_loader.get_prompt("single_file_analysis"),
            "batch_analysis": prompt_loader.get_prompt("batch_analysis"),
            "project_summary": prompt_loader.get_prompt("project_summary"),
        }

        return {
            "success": True,
            "prompts": all_prompts,
            "description": "Default prompts loaded from prompts.yaml",
            "prompt_count": len(all_prompts),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load prompts: {str(e)}",
        )


@router.post("/analyze/validate")
async def validate_files(
    files: list[UploadFile] = File(..., description="Files to validate"),
    dependencies: tuple[AnalysisService, FileHandler] = Depends(
        get_analysis_dependencies
    ),
) -> dict[str, Any]:
    """Validate uploaded files without performing analysis."""
    _, file_handler = dependencies

    try:
        # Process and validate files
        file_contents = await file_handler.process_uploaded_files(
            files=files, extract_archives=True
        )

        validation_results = []
        all_valid = True

        for file_content in file_contents:
            is_valid, messages = file_handler.validate_file_content(file_content)
            validation_results.append(
                {
                    "filename": file_content.filename,
                    "valid": is_valid,
                    "messages": messages,
                    "file_size": len(file_content.content),
                    "file_type": file_content.file_type,
                }
            )
            if not is_valid:
                all_valid = False

        return {
            "all_valid": all_valid,
            "total_files": len(file_contents),
            "validation_results": validation_results,
        }

    except (FileTooLargeError, UnsupportedFileTypeError, TooManyFilesError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File validation failed: {str(e)}",
        )

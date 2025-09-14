"""Analysis endpoints for the FastAPI application."""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import status

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
from ..deps import get_analysis_dependencies

router = APIRouter(tags=["Analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_files(
    request: AnalysisRequest, dependencies: tuple = Depends(get_analysis_dependencies)
) -> AnalysisResponse:
    """Analyze files provided in the request body."""
    analysis_service, _ = dependencies

    try:
        result = await analysis_service.analyze_files(
            files=request.files,
            config_overrides=request.config_overrides,
            output_format=request.output_format,
            verbose=request.verbose,
        )

        return result

    except (AnalysisError, FileProcessingError) as e:
        raise e
    except Exception as e:
        raise AnalysisError(f"Analysis failed: {str(e)}")


@router.post("/analyze/upload", response_model=AnalysisResponse)
async def analyze_uploaded_files(
    files: list[UploadFile] = File(..., description="Files to analyze"),
    config_overrides: str | None = Form(
        None, description="JSON string of config overrides"
    ),
    output_format: str = Form(
        "json", description="Output format: json, markdown, or both"
    ),
    verbose: bool = Form(False, description="Enable verbose output"),
    extract_archives: bool = Form(True, description="Extract ZIP archives"),
    dependencies: tuple = Depends(get_analysis_dependencies),
) -> AnalysisResponse:
    """Analyze uploaded files."""
    analysis_service, file_handler = dependencies

    try:
        # Process uploaded files
        file_contents = await file_handler.process_uploaded_files(
            files=files, extract_archives=extract_archives
        )

        # Parse config overrides if provided
        parsed_config_overrides = None
        if config_overrides:
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

        # Analyze files
        result = await analysis_service.analyze_files(
            files=file_contents,
            config_overrides=parsed_config_overrides,
            output_format=output_format,
            verbose=verbose,
        )

        return result

    except (FileTooLargeError, UnsupportedFileTypeError, TooManyFilesError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except (AnalysisError, FileProcessingError) as e:
        raise e
    except Exception as e:
        raise AnalysisError(f"File upload analysis failed: {str(e)}")


@router.post("/analyze/paths", response_model=AnalysisResponse)
async def analyze_from_paths(
    request: AnalysisFromPathRequest,
    dependencies: tuple = Depends(get_analysis_dependencies),
) -> AnalysisResponse:
    """Analyze files from server file paths."""
    analysis_service, _ = dependencies

    try:
        result = await analysis_service.analyze_from_paths(
            paths=request.paths,
            config_overrides=request.config_overrides,
            output_format=request.output_format,
            verbose=request.verbose,
            recursive=request.recursive,
        )

        return result

    except (AnalysisError, FileProcessingError) as e:
        raise e
    except Exception as e:
        raise AnalysisError(f"Path analysis failed: {str(e)}")


@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(
    request: BatchAnalysisRequest,
    dependencies: tuple = Depends(get_analysis_dependencies),
) -> BatchAnalysisResponse:
    """Analyze files in batch mode with enhanced batching strategy."""
    analysis_service, _ = dependencies

    try:
        # For batch analysis, we use the same analyze_files method
        # but the service will handle batching internally
        result = await analysis_service.analyze_files(
            files=request.files,
            config_overrides=request.config_overrides,
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
async def analyze_batch_uploaded_files(
    files: list[UploadFile] = File(..., description="Files to analyze in batch"),
    config_overrides: str | None = Form(
        None, description="JSON string of config overrides"
    ),
    output_format: str = Form(
        "json", description="Output format: json, markdown, or both"
    ),
    verbose: bool = Form(False, description="Enable verbose output"),
    extract_archives: bool = Form(True, description="Extract ZIP archives"),
    force_batch: bool = Form(
        False, description="Force batch processing even for single files"
    ),
    dependencies: tuple = Depends(get_analysis_dependencies),
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
        if config_overrides:
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

        # Create batch request and analyze
        batch_request = BatchAnalysisRequest(
            files=file_contents,
            config_overrides=parsed_config_overrides,
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
) -> dict:
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
) -> dict:
    """Get current analysis configuration."""
    config = analysis_service.get_current_config()

    # Remove sensitive information
    if "llm" in config and "api_key" in config["llm"]:
        config["llm"]["api_key"] = "***" if config["llm"]["api_key"] else None

    return {"config": config, "description": "Current analysis service configuration"}


@router.post("/analyze/validate")
async def validate_files(
    files: list[UploadFile] = File(..., description="Files to validate"),
    dependencies: tuple = Depends(get_analysis_dependencies),
) -> dict:
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

"""Custom exceptions and exception handlers for the FastAPI application."""

import traceback
from typing import Any

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class CodeSummarizerException(Exception):
    """Base exception for Code Summarizer API."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AnalysisError(CodeSummarizerException):
    """Exception raised when analysis processing fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class FileProcessingError(CodeSummarizerException):
    """Exception raised when file processing fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details
        )


class ConfigurationError(CodeSummarizerException):
    """Exception raised when configuration is invalid."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class LLMServiceError(CodeSummarizerException):
    """Exception raised when LLM service fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


class FileTooLargeError(FileProcessingError):
    """Exception raised when uploaded file is too large."""

    def __init__(self, file_size: int, max_size: int):
        message = (
            f"File size {file_size} bytes exceeds maximum allowed size {max_size} bytes"
        )
        details = {"file_size": file_size, "max_size": max_size}
        super().__init__(message=message, details=details)


class UnsupportedFileTypeError(FileProcessingError):
    """Exception raised when file type is not supported."""

    def __init__(self, file_type: str, supported_types: list[str]):
        message = f"File type '{file_type}' is not supported"
        details = {"file_type": file_type, "supported_types": supported_types}
        super().__init__(message=message, details=details)


class TooManyFilesError(FileProcessingError):
    """Exception raised when too many files are uploaded."""

    def __init__(self, file_count: int, max_files: int):
        message = f"Number of files {file_count} exceeds maximum allowed {max_files}"
        details = {"file_count": file_count, "max_files": max_files}
        super().__init__(message=message, details=details)


async def code_summarizer_exception_handler(
    request: Request, exc: CodeSummarizerException
) -> JSONResponse:
    """Handle Code Summarizer exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details,
            },
            "request_id": getattr(request.state, "request_id", None),
            "path": str(request.url.path),
            "method": request.method,
        },
    )


async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "details": {"errors": exc.errors(), "body": getattr(exc, "body", None)},
            },
            "request_id": getattr(request.state, "request_id", None),
            "path": str(request.url.path),
            "method": request.method,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {"type": "HTTPException", "message": exc.detail, "details": {}},
            "request_id": getattr(request.state, "request_id", None),
            "path": str(request.url.path),
            "method": request.method,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    # Log the full traceback for debugging
    tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    print(f"Unhandled exception: {tb_str}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An internal server error occurred",
                "details": {
                    "exception_type": exc.__class__.__name__,
                    "exception_message": str(exc),
                },
            },
            "request_id": getattr(request.state, "request_id", None),
            "path": str(request.url.path),
            "method": request.method,
        },
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup exception handlers for the FastAPI application."""
    app.add_exception_handler(
        CodeSummarizerException,
        code_summarizer_exception_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(ValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, general_exception_handler)

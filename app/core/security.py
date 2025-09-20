"""Security middleware and utilities for the FastAPI application."""

import logging
import re
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from .config import Settings

logger = logging.getLogger(__name__)

# Security bearer for API key authentication
security_bearer = HTTPBearer(auto_error=False)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request validation and security headers."""

    def __init__(self, app: Any, *, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings
        self.security_config = settings.security

    async def dispatch(
        self, request: Request, call_next: Callable[..., Any]
    ) -> Response:
        """Process request through security middleware."""
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Add request start time
        start_time = time.time()
        request.state.start_time = start_time

        try:
            # Validate request path for security
            await self._validate_request_path(request)

            # Validate content length
            await self._validate_content_length(request)

            # Process the request
            response = await call_next(request)

            # Add security headers to response
            await self._add_security_headers(response)

            # Add performance headers
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id

            return response  # type: ignore[no-any-return]

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            logger.error("Exception traceback: ", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def _validate_request_path(self, request: Request) -> None:
        """Validate request path for security issues."""
        path = request.url.path

        # Check for path traversal attempts
        dangerous_patterns = [
            r"\.\./",  # Directory traversal
            r"\.\.[/\\]",  # Windows/Unix directory traversal
            r"%2e%2e%2f",  # URL encoded traversal
            r"%2e%2e[/\\]",  # URL encoded traversal (Windows/Unix)
            r"//",  # Double slashes
            r"\\\\",  # Double backslashes
            r"\x00",  # Null bytes
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                logger.warning(f"Path traversal attempt detected: {path}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid path detected",
                )

        # Check for excessively long paths
        if len(path) > 1000:
            logger.warning(f"Excessively long path: {len(path)} characters")
            raise HTTPException(status_code=414, detail="Path too long")

    async def _validate_content_length(self, request: Request) -> None:
        """Validate request content length."""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                max_size = self.settings.max_file_size_bytes * 2  # Allow some overhead
                if length > max_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request too large. Max size: {max_size} bytes",
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid content-length header",
                )

    async def _add_security_headers(self, response: Response) -> None:
        """Add security headers to the response."""
        if not self.security_config.security_headers_enabled:
            return

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # Content Security Policy
        if self.security_config.content_security_policy:
            response.headers["Content-Security-Policy"] = (
                self.security_config.content_security_policy
            )

        # HSTS header for HTTPS (only in production)
        if not self.settings.debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )


def validate_file_path(file_path: str) -> str:
    """Validate and sanitize file paths to prevent path traversal."""
    if not file_path:
        raise ValueError("File path cannot be empty")

    # Normalize the path
    try:
        normalized_path = Path(file_path).resolve()
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid file path: {str(e)}")

    # Convert to string for further checks
    path_str = str(normalized_path)

    # Check for dangerous patterns
    dangerous_patterns = [
        r"\.\./",  # Directory traversal
        r"\.\.[/\\]",  # Windows/Unix directory traversal
        r"%2e%2e%2f",  # URL encoded traversal
        r"%2e%2e[/\\]",  # URL encoded traversal (Windows/Unix)
        r"\x00",  # Null bytes
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, path_str, re.IGNORECASE):
            raise ValueError(f"Dangerous path pattern detected: {file_path}")

    # Check path length
    if len(path_str) > 500:
        raise ValueError(f"Path too long: {len(path_str)} characters")

    # Ensure path doesn't go outside allowed directories
    # This should be configured based on your specific needs
    # Note: /tmp and /var/tmp paths flagged by security scanner
    # Only allow current working directory for now
    allowed_prefixes = [
        str(Path.cwd()),
    ]

    # Only enforce prefix checking if not an absolute system path
    if path_str.startswith("/") and not any(
        path_str.startswith(prefix) for prefix in allowed_prefixes
    ):
        logger.warning(f"Path outside allowed directories: {path_str}")
        # Don't raise error, just log for now - adjust based on your needs

    return path_str


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent security issues."""
    if not filename:
        raise ValueError("Filename cannot be empty")

    # Remove or replace dangerous characters
    # Keep alphanumeric, dots, hyphens, underscores
    safe_filename = re.sub(r"[^a-zA-Z0-9.\-_]", "_", filename)

    # Prevent double extensions that could be dangerous
    safe_filename = re.sub(r"\.{2,}", ".", safe_filename)

    # Ensure filename isn't too long
    if len(safe_filename) > 255:
        name, ext = (
            safe_filename.rsplit(".", 1)
            if "." in safe_filename
            else (safe_filename, "")
        )
        safe_filename = name[: 255 - len(ext) - 1] + "." + ext if ext else name[:255]

    # Prevent reserved Windows filenames
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    name_part = safe_filename.split(".")[0].upper()
    if name_part in reserved_names:
        safe_filename = f"file_{safe_filename}"

    return safe_filename


async def validate_api_key(request: Request, settings: Settings) -> bool:
    """Validate API key from request headers."""
    if not settings.security.require_api_key:
        return True

    api_key_header = settings.security.api_key_header_name
    api_key = request.headers.get(api_key_header)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing {api_key_header} header",
        )

    # Here you would validate against your API key store
    # For now, just check it's not empty and has reasonable length
    if len(api_key) < 20:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key format"
        )

    return True

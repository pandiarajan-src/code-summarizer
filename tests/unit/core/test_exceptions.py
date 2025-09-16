import pytest
from fastapi import HTTPException, status
from pydantic import ValidationError
from unittest.mock import MagicMock
from app.core.exceptions import (
    CodeSummarizerException,
    AnalysisError,
    FileProcessingError,
    ConfigurationError,
    LLMServiceError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    TooManyFilesError,
    code_summarizer_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
)


class TestCustomExceptions:
    def test_code_summarizer_exception(self):
        """Test base CodeSummarizerException."""
        exc = CodeSummarizerException("Test error", status.HTTP_400_BAD_REQUEST, {"key": "value"})

        assert exc.message == "Test error"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.details == {"key": "value"}
        assert str(exc) == "Test error"

    def test_code_summarizer_exception_defaults(self):
        """Test CodeSummarizerException with defaults."""
        exc = CodeSummarizerException("Test error")

        assert exc.message == "Test error"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.details == {}

    def test_analysis_error(self):
        """Test AnalysisError exception."""
        exc = AnalysisError("Analysis failed", {"reason": "invalid input"})

        assert exc.message == "Analysis failed"
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert exc.details == {"reason": "invalid input"}

    def test_file_processing_error(self):
        """Test FileProcessingError exception."""
        exc = FileProcessingError("File processing failed")

        assert exc.message == "File processing failed"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_configuration_error(self):
        """Test ConfigurationError exception."""
        exc = ConfigurationError("Config invalid")

        assert exc.message == "Config invalid"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_llm_service_error(self):
        """Test LLMServiceError exception."""
        exc = LLMServiceError("LLM service unavailable")

        assert exc.message == "LLM service unavailable"
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_file_too_large_error(self):
        """Test FileTooLargeError exception."""
        exc = FileTooLargeError(1000000, 500000)

        assert "1000000 bytes exceeds maximum allowed size 500000 bytes" in exc.message
        assert exc.details["file_size"] == 1000000
        assert exc.details["max_size"] == 500000

    def test_unsupported_file_type_error(self):
        """Test UnsupportedFileTypeError exception."""
        exc = UnsupportedFileTypeError(".txt", [".py", ".js"])

        assert "File type '.txt' is not supported" in exc.message
        assert exc.details["file_type"] == ".txt"
        assert exc.details["supported_types"] == [".py", ".js"]

    def test_too_many_files_error(self):
        """Test TooManyFilesError exception."""
        exc = TooManyFilesError(150, 100)

        assert "Number of files 150 exceeds maximum allowed 100" in exc.message
        assert exc.details["file_count"] == 150
        assert exc.details["max_files"] == 100


class TestExceptionHandlers:
    @pytest.mark.asyncio
    async def test_code_summarizer_exception_handler(self):
        """Test CodeSummarizerException handler."""
        request = MagicMock()
        request.url.path = "/test"
        request.method = "GET"
        request.state.request_id = "test-123"

        exc = CodeSummarizerException("Test error", status.HTTP_400_BAD_REQUEST, {"key": "value"})

        response = await code_summarizer_exception_handler(request, exc)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        content = response.body.decode()
        assert "Test error" in content
        assert "CodeSummarizerException" in content

    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        """Test ValidationError handler."""
        request = MagicMock()
        request.url.path = "/test"
        request.method = "POST"
        request.state.request_id = "test-123"

        # Create a mock ValidationError
        exc = MagicMock(spec=ValidationError)
        exc.errors.return_value = [{"field": "test", "message": "required"}]

        response = await validation_exception_handler(request, exc)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        content = response.body.decode()
        assert "ValidationError" in content

    @pytest.mark.asyncio
    async def test_http_exception_handler(self):
        """Test HTTPException handler."""
        request = MagicMock()
        request.url.path = "/test"
        request.method = "GET"
        request.state.request_id = "test-456"

        exc = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

        response = await http_exception_handler(request, exc)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        content = response.body.decode()
        assert "Not found" in content

    @pytest.mark.asyncio
    async def test_general_exception_handler(self, capsys):
        """Test general exception handler."""
        request = MagicMock()
        request.url.path = "/test"
        request.method = "GET"
        request.state.request_id = "test-789"

        exc = ValueError("Something went wrong")

        response = await general_exception_handler(request, exc)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        content = response.body.decode()
        assert "InternalServerError" in content

        # Check that traceback was printed
        captured = capsys.readouterr()
        assert "Unhandled exception:" in captured.out
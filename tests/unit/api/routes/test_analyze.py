import json
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from starlette.requests import Request

# Mock the rate limiter before importing the routes
with patch("slowapi.Limiter") as mock_limiter_class:
    mock_limiter = MagicMock()
    mock_limiter.limit.return_value = lambda func: func
    mock_limiter_class.return_value = mock_limiter

    from app.api.routes.analyze import analyze_batch
    from app.api.routes.analyze import analyze_batch_uploaded_files
    from app.api.routes.analyze import analyze_files
    from app.api.routes.analyze import analyze_from_paths
    from app.api.routes.analyze import analyze_uploaded_files
    from app.api.routes.analyze import get_analysis_config
    from app.api.routes.analyze import get_supported_file_types
    from app.api.routes.analyze import validate_files

from app.models.requests import AnalysisFromPathRequest
from app.models.requests import AnalysisRequest
from app.models.requests import BatchAnalysisRequest
from app.models.requests import FileContent
from app.models.responses import AnalysisResponse
from app.models.responses import BatchAnalysisResponse
from app.models.responses import ProjectSummary


class TestAnalyzeFiles:
    """Test analyze files endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_files_success(self):
        """Test successful file analysis."""
        # Mock dependencies
        mock_analysis_service = AsyncMock()
        mock_file_handler = AsyncMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        # Create mock request
        request = AnalysisRequest(
            files=[{"filename": "test.py", "content": "print('hello')"}],
            output_format="json",
        )

        # Mock response
        mock_response = AnalysisResponse(
            success=True,
            analysis_id="test-123",
            files_analyzed=1,
            total_tokens_used=100,
            total_processing_time_seconds=2.0,
            config_used={},
        )
        mock_analysis_service.analyze_files.return_value = mock_response

        result = await analyze_files(request, dependencies)

        assert result == mock_response
        mock_analysis_service.analyze_files.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_files_with_config_overrides(self):
        """Test file analysis with config overrides."""
        mock_analysis_service = AsyncMock()
        mock_file_handler = AsyncMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        request = AnalysisRequest(
            files=[{"filename": "test.py", "content": "print('hello')"}],
            config_overrides={"max_tokens": 1000},
            verbose=True,
        )

        mock_response = AnalysisResponse(
            success=True,
            analysis_id="test-123",
            files_analyzed=1,
            total_tokens_used=50,
            total_processing_time_seconds=1.0,
            config_used={"max_tokens": 1000},
        )
        mock_analysis_service.analyze_files.return_value = mock_response

        result = await analyze_files(request, dependencies)

        assert result == mock_response

    @pytest.mark.asyncio
    async def test_analyze_files_analysis_error(self):
        """Test file analysis with AnalysisError."""
        from app.core.exceptions import AnalysisError

        mock_analysis_service = AsyncMock()
        mock_file_handler = AsyncMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        request = AnalysisRequest(
            files=[{"filename": "test.py", "content": "print('hello')"}]
        )

        mock_analysis_service.analyze_files.side_effect = AnalysisError(
            "Analysis failed"
        )

        with pytest.raises(AnalysisError):
            await analyze_files(request, dependencies)


class TestAnalyzeUploadedFiles:
    """Test analyze uploaded files endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_uploaded_files_success(self):
        """Test successful uploaded file analysis."""
        # Mock dependencies
        mock_analysis_service = AsyncMock()
        mock_file_handler = AsyncMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        # Mock file handler response
        file_contents = [FileContent(filename="test.py", content="print('hello')")]
        mock_file_handler.process_uploaded_files = AsyncMock(return_value=file_contents)

        # Mock analysis response
        mock_response = AnalysisResponse(
            success=True,
            analysis_id="test-123",
            files_analyzed=1,
            total_tokens_used=100,
            total_processing_time_seconds=2.0,
            config_used={},
        )
        mock_analysis_service.analyze_files.return_value = mock_response

        # Mock uploaded files
        mock_files = [MagicMock()]

        # Create a mock request
        mock_request = MagicMock(spec=Request)

        result = await analyze_uploaded_files(
            request=mock_request,  # Add request parameter
            files=mock_files,
            config_overrides=None,
            custom_prompts=None,
            output_format="json",
            verbose=False,
            extract_archives=True,
            dependencies=dependencies,
        )

        assert result == mock_response
        mock_file_handler.process_uploaded_files.assert_called_once_with(
            files=mock_files, extract_archives=True
        )

    @pytest.mark.asyncio
    async def test_analyze_uploaded_files_with_config_overrides(self):
        """Test uploaded file analysis with config overrides."""
        mock_analysis_service = AsyncMock()
        mock_file_handler = AsyncMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        file_contents = [FileContent(filename="test.py", content="print('hello')")]
        mock_file_handler.process_uploaded_files = AsyncMock(return_value=file_contents)

        mock_response = AnalysisResponse(
            success=True,
            analysis_id="test-123",
            files_analyzed=1,
            total_tokens_used=100,
            total_processing_time_seconds=2.0,
            config_used={},
        )
        mock_analysis_service.analyze_files.return_value = mock_response

        mock_files = [MagicMock()]
        config_json = json.dumps(
            {"llm_max_tokens": 1000}
        )  # Use valid ConfigOverrides field

        # Create a mock request
        mock_request = MagicMock(spec=Request)

        result = await analyze_uploaded_files(
            request=mock_request,  # Add request parameter
            files=mock_files,
            config_overrides=config_json,
            custom_prompts=None,
            output_format="json",
            verbose=False,
            extract_archives=True,
            dependencies=dependencies,
        )

        assert result == mock_response
        # Verify config was parsed correctly
        call_args = mock_analysis_service.analyze_files.call_args
        # Check that config_overrides was parsed (the exact validation would depend on the model structure)
        assert call_args.kwargs["config_overrides"] is not None

    @pytest.mark.asyncio
    async def test_analyze_uploaded_files_invalid_config_json(self):
        """Test uploaded file analysis with invalid config JSON."""
        mock_analysis_service = AsyncMock()
        mock_file_handler = AsyncMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        file_contents = [FileContent(filename="test.py", content="print('hello')")]
        mock_file_handler.process_uploaded_files = AsyncMock(return_value=file_contents)

        mock_files = [MagicMock()]
        invalid_config_json = "not valid json"

        # Create a mock request
        mock_request = MagicMock(spec=Request)

        with pytest.raises(HTTPException) as exc_info:
            await analyze_uploaded_files(
                request=mock_request,  # Add request parameter
                files=mock_files,
                config_overrides=invalid_config_json,
                custom_prompts=None,
                output_format="json",
                verbose=False,
                extract_archives=True,
                dependencies=dependencies,
            )

        assert exc_info.value.status_code == 400
        assert "Invalid config overrides JSON" in exc_info.value.detail


class TestAnalyzeFromPaths:
    """Test analyze from paths endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_from_paths_success(self):
        """Test successful path-based analysis."""
        mock_analysis_service = AsyncMock()
        mock_file_handler = AsyncMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        request = AnalysisFromPathRequest(paths=["/path/to/file.py"], recursive=False)

        mock_response = AnalysisResponse(
            success=True,
            analysis_id="test-123",
            files_analyzed=1,
            total_tokens_used=100,
            total_processing_time_seconds=2.0,
            config_used={},
        )
        mock_analysis_service.analyze_from_paths.return_value = mock_response

        result = await analyze_from_paths(request, dependencies)

        assert result == mock_response
        mock_analysis_service.analyze_from_paths.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_from_paths_file_not_found(self):
        """Test path-based analysis with FileNotFoundError."""
        mock_analysis_service = AsyncMock()
        mock_file_handler = AsyncMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        request = AnalysisFromPathRequest(paths=["/nonexistent/file.py"])

        mock_analysis_service.analyze_from_paths.side_effect = FileNotFoundError(
            "File not found"
        )

        with pytest.raises(HTTPException) as exc_info:
            await analyze_from_paths(request, dependencies)

        assert exc_info.value.status_code == 400
        assert "Path error" in exc_info.value.detail


class TestAnalyzeBatch:
    """Test analyze batch endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_batch_success(self):
        """Test successful batch analysis."""
        mock_analysis_service = AsyncMock()
        mock_file_handler = AsyncMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        request = BatchAnalysisRequest(
            files=[
                {"filename": "test1.py", "content": "print('hello')"},
                {"filename": "test2.py", "content": "print('world')"},
            ]
        )

        mock_project_summary = ProjectSummary(
            total_files=2,
            languages_detected=["python"],
            project_structure={"type": "batch"},
            key_insights=["Test project"],
            recommendations=["Keep testing"],
        )
        mock_response = AnalysisResponse(
            success=True,
            analysis_id="batch-123",
            files_analyzed=2,
            batch_results=[],
            project_summary=mock_project_summary,
            total_tokens_used=200,
            total_processing_time_seconds=3.0,
            config_used={},
        )
        mock_analysis_service.analyze_files.return_value = mock_response

        result = await analyze_batch(request, dependencies)

        assert isinstance(result, BatchAnalysisResponse)
        assert result.success
        assert result.total_files_analyzed == 2


class TestAnalyzeBatchUploadedFiles:
    """Test analyze batch uploaded files endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_batch_uploaded_files_success(self):
        """Test successful batch uploaded file analysis."""
        mock_analysis_service = AsyncMock()
        mock_file_handler = AsyncMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        file_contents = [
            FileContent(filename="test1.py", content="print('hello')"),
            FileContent(filename="test2.py", content="print('world')"),
        ]
        mock_file_handler.process_uploaded_files = AsyncMock(return_value=file_contents)

        mock_project_summary = ProjectSummary(
            total_files=2,
            languages_detected=["python"],
            project_structure={"type": "batch"},
            key_insights=["Test project"],
            recommendations=["Keep testing"],
        )
        mock_response = AnalysisResponse(
            success=True,
            analysis_id="batch-123",
            files_analyzed=2,
            batch_results=[],
            project_summary=mock_project_summary,
            total_tokens_used=200,
            total_processing_time_seconds=3.0,
            config_used={},
        )
        mock_analysis_service.analyze_files.return_value = mock_response

        mock_files = [MagicMock(), MagicMock()]

        # Create a mock request
        mock_request = MagicMock(spec=Request)

        result = await analyze_batch_uploaded_files(
            request=mock_request,  # Add request parameter
            files=mock_files,
            config_overrides=None,
            custom_prompts=None,
            output_format="json",
            verbose=False,
            extract_archives=True,
            force_batch=False,
            dependencies=dependencies,
        )

        assert isinstance(result, BatchAnalysisResponse)
        assert result.total_files_analyzed == 2


class TestGetSupportedFileTypes:
    """Test get supported file types endpoint."""

    @pytest.mark.asyncio
    async def test_get_supported_file_types(self):
        """Test getting supported file types."""
        mock_analysis_service = AsyncMock()
        # Mock as a regular method, not async
        mock_analysis_service.get_supported_file_types = MagicMock(
            return_value=[".py", ".js", ".ts"]
        )

        result = await get_supported_file_types(mock_analysis_service)

        assert "supported_extensions" in result
        assert result["supported_extensions"] == [".py", ".js", ".ts"]
        assert "description" in result


class TestGetAnalysisConfig:
    """Test get analysis config endpoint."""

    @pytest.mark.asyncio
    async def test_get_analysis_config(self):
        """Test getting analysis configuration."""
        mock_analysis_service = AsyncMock()
        # Mock as a regular method, not async
        mock_analysis_service.get_current_config = MagicMock(
            return_value={
                "llm": {"model": "gpt-4", "api_key": "test-key"},
                "other": "config",
            }
        )

        result = await get_analysis_config(mock_analysis_service)

        assert "config" in result
        # API key should be masked
        assert result["config"]["llm"]["api_key"] == "***"
        assert result["config"]["other"] == "config"


class TestValidateFiles:
    """Test validate files endpoint."""

    @pytest.mark.asyncio
    async def test_validate_files_success(self):
        """Test successful file validation."""
        mock_analysis_service = AsyncMock()
        mock_file_handler = AsyncMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        file_contents = [FileContent(filename="test.py", content="print('hello')")]
        mock_file_handler.process_uploaded_files = AsyncMock(return_value=file_contents)
        # Mock as a regular function, not async
        mock_file_handler.validate_file_content = MagicMock(
            return_value=(True, ["File is valid"])
        )

        mock_files = [MagicMock()]

        result = await validate_files(files=mock_files, dependencies=dependencies)

        assert result["all_valid"]
        assert result["total_files"] == 1
        assert len(result["validation_results"]) == 1

    @pytest.mark.asyncio
    async def test_validate_files_invalid(self):
        """Test file validation with invalid files."""
        mock_analysis_service = AsyncMock()
        mock_file_handler = AsyncMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        file_contents = [FileContent(filename="test.exe", content="binary")]
        mock_file_handler.process_uploaded_files = AsyncMock(return_value=file_contents)
        # Mock as a regular function, not async
        mock_file_handler.validate_file_content = MagicMock(
            return_value=(False, ["Invalid file type"])
        )

        mock_files = [MagicMock()]

        result = await validate_files(files=mock_files, dependencies=dependencies)

        assert not result["all_valid"]
        assert not result["validation_results"][0]["valid"]

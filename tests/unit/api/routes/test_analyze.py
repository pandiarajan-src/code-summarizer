import json
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException
from app.api.routes.analyze import (
    analyze_files,
    analyze_uploaded_files,
    analyze_from_paths,
    analyze_batch,
    analyze_batch_uploaded_files,
    get_supported_file_types,
    get_analysis_config,
    validate_files
)
from app.models.requests import (
    AnalysisRequest,
    AnalysisFromPathRequest,
    BatchAnalysisRequest,
    FileContent,
    ConfigOverrides
)
from app.models.responses import AnalysisResponse, BatchAnalysisResponse


class TestAnalyzeFiles:
    @pytest.mark.asyncio
    async def test_analyze_files_success(self):
        """Test successful file analysis."""
        # Mock dependencies
        mock_analysis_service = AsyncMock()
        mock_file_handler = MagicMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        # Mock response
        mock_response = AnalysisResponse(
            success=True,
            analysis_id="test-123",
            files_analyzed=1,
            total_tokens_used=100,
            total_processing_time_seconds=2.0,
            config_used={}
        )
        mock_analysis_service.analyze_files.return_value = mock_response

        # Create request
        request = AnalysisRequest(
            files=[FileContent(filename="test.py", content="print('hello')")]
        )

        # Call endpoint
        result = await analyze_files(request, dependencies)

        # Assertions
        assert result == mock_response
        mock_analysis_service.analyze_files.assert_called_once_with(
            files=request.files,
            config_overrides=request.config_overrides,
            output_format=request.output_format,
            verbose=request.verbose
        )

    @pytest.mark.asyncio
    async def test_analyze_files_analysis_error(self):
        """Test analysis error handling."""
        from app.core.exceptions import AnalysisError

        mock_analysis_service = AsyncMock()
        mock_file_handler = MagicMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        # Mock to raise AnalysisError
        mock_analysis_service.analyze_files.side_effect = AnalysisError("Analysis failed")

        request = AnalysisRequest(
            files=[FileContent(filename="test.py", content="print('hello')")]
        )

        # Should re-raise AnalysisError
        with pytest.raises(AnalysisError, match="Analysis failed"):
            await analyze_files(request, dependencies)

    @pytest.mark.asyncio
    async def test_analyze_files_generic_error(self):
        """Test generic error handling."""
        from app.core.exceptions import AnalysisError

        mock_analysis_service = AsyncMock()
        mock_file_handler = MagicMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        # Mock to raise generic error
        mock_analysis_service.analyze_files.side_effect = ValueError("Generic error")

        request = AnalysisRequest(
            files=[FileContent(filename="test.py", content="print('hello')")]
        )

        # Should wrap in AnalysisError
        with pytest.raises(AnalysisError, match="Analysis failed: Generic error"):
            await analyze_files(request, dependencies)


class TestAnalyzeUploadedFiles:
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
            config_used={}
        )
        mock_analysis_service.analyze_files.return_value = mock_response

        # Mock uploaded files
        mock_files = [MagicMock()]

        result = await analyze_uploaded_files(
            files=mock_files,
            config_overrides=None,
            output_format="json",
            verbose=False,
            extract_archives=True,
            dependencies=dependencies
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
            config_used={}
        )
        mock_analysis_service.analyze_files.return_value = mock_response

        # Valid config overrides JSON
        config_json = '{"llm_temperature": 0.5}'
        mock_files = [MagicMock()]

        result = await analyze_uploaded_files(
            files=mock_files,
            config_overrides=config_json,
            output_format="json",
            verbose=False,
            extract_archives=True,
            dependencies=dependencies
        )

        # Should parse and use config overrides
        mock_analysis_service.analyze_files.assert_called_once()
        call_args = mock_analysis_service.analyze_files.call_args
        assert call_args[1]["config_overrides"].llm_temperature == 0.5

    @pytest.mark.asyncio
    async def test_analyze_uploaded_files_invalid_config_json(self):
        """Test uploaded file analysis with invalid config JSON."""
        mock_analysis_service = AsyncMock()
        mock_file_handler = AsyncMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        file_contents = [FileContent(filename="test.py", content="print('hello')")]
        mock_file_handler.process_uploaded_files = AsyncMock(return_value=file_contents)

        # Invalid JSON
        config_json = '{"invalid": json}'
        mock_files = [MagicMock()]

        with pytest.raises(HTTPException) as exc_info:
            await analyze_uploaded_files(
                files=mock_files,
                config_overrides=config_json,
                output_format="json",
                verbose=False,
                extract_archives=True,
                dependencies=dependencies
            )

        assert exc_info.value.status_code == 400
        assert "Invalid config overrides JSON" in str(exc_info.value.detail)


class TestAnalyzeFromPaths:
    @pytest.mark.asyncio
    async def test_analyze_from_paths_success(self):
        """Test successful path analysis."""
        mock_analysis_service = AsyncMock()
        mock_file_handler = MagicMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        mock_response = AnalysisResponse(
            success=True,
            analysis_id="test-123",
            files_analyzed=1,
            total_tokens_used=100,
            total_processing_time_seconds=2.0,
            config_used={}
        )
        mock_analysis_service.analyze_from_paths.return_value = mock_response

        request = AnalysisFromPathRequest(paths=["/path/to/code"])

        result = await analyze_from_paths(request, dependencies)

        assert result == mock_response
        mock_analysis_service.analyze_from_paths.assert_called_once_with(
            paths=request.paths,
            config_overrides=request.config_overrides,
            output_format=request.output_format,
            verbose=request.verbose,
            recursive=request.recursive
        )

    @pytest.mark.asyncio
    async def test_analyze_from_paths_file_not_found(self):
        """Test path analysis with file not found error."""
        mock_analysis_service = AsyncMock()
        mock_file_handler = MagicMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        mock_analysis_service.analyze_from_paths.side_effect = FileNotFoundError("File not found")

        request = AnalysisFromPathRequest(paths=["/nonexistent/path"])

        with pytest.raises(HTTPException) as exc_info:
            await analyze_from_paths(request, dependencies)

        assert exc_info.value.status_code == 400
        assert "Path error: File not found" in str(exc_info.value.detail)


class TestAnalyzeBatch:
    @pytest.mark.asyncio
    async def test_analyze_batch_success(self):
        """Test successful batch analysis."""
        mock_analysis_service = AsyncMock()
        mock_file_handler = MagicMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        # Mock analysis response
        mock_analysis_response = AnalysisResponse(
            success=True,
            analysis_id="test-123",
            files_analyzed=2,
            batch_results=[],
            total_tokens_used=200,
            total_processing_time_seconds=5.0,
            config_used={}
        )
        mock_analysis_service.analyze_files.return_value = mock_analysis_response

        request = BatchAnalysisRequest(
            files=[
                FileContent(filename="test1.py", content="print('hello')"),
                FileContent(filename="test2.py", content="print('world')")
            ]
        )

        result = await analyze_batch(request, dependencies)

        # Should return BatchAnalysisResponse
        assert isinstance(result, BatchAnalysisResponse)
        assert result.success is True
        assert result.total_files_analyzed == 2
        assert result.total_tokens_used == 200


class TestGetSupportedFileTypes:
    @pytest.mark.asyncio
    async def test_get_supported_file_types(self):
        """Test getting supported file types."""
        mock_analysis_service = MagicMock()
        mock_analysis_service.get_supported_file_types.return_value = [".py", ".js", ".ts"]

        result = await get_supported_file_types(mock_analysis_service)

        assert "supported_extensions" in result
        assert result["supported_extensions"] == [".py", ".js", ".ts"]
        assert "description" in result
        assert "note" in result


class TestGetAnalysisConfig:
    @pytest.mark.asyncio
    async def test_get_analysis_config(self):
        """Test getting analysis configuration."""
        mock_analysis_service = MagicMock()
        mock_config = {
            "llm": {
                "api_key": "secret-key",
                "model": "gpt-4"
            },
            "other": "value"
        }
        mock_analysis_service.get_current_config.return_value = mock_config

        result = await get_analysis_config(mock_analysis_service)

        assert "config" in result
        assert result["config"]["llm"]["api_key"] == "***"  # Should be masked
        assert result["config"]["llm"]["model"] == "gpt-4"
        assert result["config"]["other"] == "value"

    @pytest.mark.asyncio
    async def test_get_analysis_config_no_api_key(self):
        """Test getting analysis configuration without API key."""
        mock_analysis_service = MagicMock()
        mock_config = {
            "llm": {
                "api_key": None,
                "model": "gpt-4"
            }
        }
        mock_analysis_service.get_current_config.return_value = mock_config

        result = await get_analysis_config(mock_analysis_service)

        assert result["config"]["llm"]["api_key"] is None


class TestValidateFiles:
    @pytest.mark.asyncio
    async def test_validate_files_success(self):
        """Test successful file validation."""
        mock_analysis_service = MagicMock()
        mock_file_handler = AsyncMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        # Mock file processing
        file_contents = [
            FileContent(filename="test.py", content="print('hello')", file_type=".py")
        ]
        mock_file_handler.process_uploaded_files = AsyncMock(return_value=file_contents)

        # Mock validation
        mock_file_handler.validate_file_content = MagicMock(return_value=(True, []))

        mock_files = [MagicMock()]

        result = await validate_files(mock_files, dependencies)

        assert result["all_valid"] is True
        assert result["total_files"] == 1
        assert len(result["validation_results"]) == 1
        assert result["validation_results"][0]["filename"] == "test.py"
        assert result["validation_results"][0]["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_files_with_invalid_file(self):
        """Test file validation with invalid file."""
        mock_analysis_service = MagicMock()
        mock_file_handler = AsyncMock()
        dependencies = (mock_analysis_service, mock_file_handler)

        file_contents = [
            FileContent(filename="test.py", content="print('hello')", file_type=".py")
        ]
        mock_file_handler.process_uploaded_files = AsyncMock(return_value=file_contents)

        # Mock validation to return invalid
        mock_file_handler.validate_file_content = MagicMock(return_value=(False, ["File too large"]))

        mock_files = [MagicMock()]

        result = await validate_files(mock_files, dependencies)

        assert result["all_valid"] is False
        assert result["validation_results"][0]["valid"] is False
        assert result["validation_results"][0]["messages"] == ["File too large"]
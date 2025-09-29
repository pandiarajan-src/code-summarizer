from datetime import datetime

from app.models.responses import AnalysisResponse
from app.models.responses import BatchAnalysisResponse
from app.models.responses import BatchAnalysisResult
from app.models.responses import ConfigResponse
from app.models.responses import ErrorDetail
from app.models.responses import ErrorResponse
from app.models.responses import FileAnalysisResult
from app.models.responses import FileUploadResponse
from app.models.responses import HealthResponse
from app.models.responses import ProjectSummary
from app.models.responses import ValidationResponse
from app.models.responses import VersionResponse


class TestErrorDetail:
    """Test error detail model."""

    def test_valid_error_detail(self):
        """Test valid error detail creation."""
        error = ErrorDetail(
            type="ValidationError",
            message="Invalid input data",
            details={"field": "filename", "issue": "too long"},
        )

        assert error.type == "ValidationError"
        assert error.message == "Invalid input data"
        assert error.details == {"field": "filename", "issue": "too long"}

    def test_error_detail_default_details(self):
        """Test error detail with default empty details."""
        error = ErrorDetail(type="ValidationError", message="Invalid input data")

        assert error.details == {}


class TestErrorResponse:
    """Test error response model."""

    def test_valid_error_response(self):
        """Test valid error response creation."""
        error_detail = ErrorDetail(type="ValidationError", message="Invalid input data")

        response = ErrorResponse(
            error=error_detail, request_id="req-123", path="/api/analyze", method="POST"
        )

        assert response.error == error_detail
        assert response.request_id == "req-123"
        assert response.path == "/api/analyze"
        assert response.method == "POST"
        assert isinstance(response.timestamp, datetime)

    def test_error_response_without_request_id(self):
        """Test error response without request ID."""
        error_detail = ErrorDetail(type="ValidationError", message="Invalid input data")

        response = ErrorResponse(error=error_detail, path="/api/analyze", method="POST")

        assert response.request_id is None


class TestFileAnalysisResult:
    """Test file analysis result model."""

    def test_valid_file_analysis_result(self):
        """Test valid file analysis result creation."""
        result = FileAnalysisResult(
            filename="test.py",
            file_type="python",
            language="Python",
            analysis={"purpose": "Test script", "complexity": "low"},
            tokens_used=150,
            processing_time_seconds=2.5,
        )

        assert result.filename == "test.py"
        assert result.file_type == "python"
        assert result.language == "Python"
        assert result.analysis == {"purpose": "Test script", "complexity": "low"}
        assert result.tokens_used == 150
        assert result.processing_time_seconds == 2.5


class TestBatchAnalysisResult:
    """Test batch analysis result model."""

    def test_valid_batch_analysis_result(self):
        """Test valid batch analysis result creation."""
        file_result = FileAnalysisResult(
            filename="test.py",
            file_type="python",
            language="Python",
            analysis={"purpose": "Test script"},
            tokens_used=100,
            processing_time_seconds=1.0,
        )

        batch_result = BatchAnalysisResult(
            batch_id="batch-1",
            files_count=1,
            batch_summary={"main_purpose": "Testing"},
            individual_analyses=[file_result],
            total_tokens_used=150,
            processing_time_seconds=3.0,
        )

        assert batch_result.batch_id == "batch-1"
        assert batch_result.files_count == 1
        assert batch_result.batch_summary == {"main_purpose": "Testing"}
        assert len(batch_result.individual_analyses) == 1
        assert batch_result.total_tokens_used == 150
        assert batch_result.processing_time_seconds == 3.0

    def test_batch_analysis_result_empty_analyses(self):
        """Test batch analysis result with empty individual analyses."""
        batch_result = BatchAnalysisResult(
            batch_id="batch-1",
            files_count=0,
            batch_summary={},
            total_tokens_used=0,
            processing_time_seconds=0.0,
        )

        assert batch_result.individual_analyses == []


class TestProjectSummary:
    """Test project summary model."""

    def test_valid_project_summary(self):
        """Test valid project summary creation."""
        summary = ProjectSummary(
            total_files=10,
            languages_detected=["Python", "JavaScript"],
            project_structure={
                "type": "web_app",
                "components": ["backend", "frontend"],
            },
            key_insights=["Well structured", "Good test coverage"],
            recommendations=["Add documentation", "Improve error handling"],
            technical_debt={"complexity": "medium", "issues": 5},
            dependencies={
                "Python": ["flask", "requests"],
                "JavaScript": ["react", "axios"],
            },
        )

        assert summary.total_files == 10
        assert summary.languages_detected == ["Python", "JavaScript"]
        assert summary.project_structure["type"] == "web_app"
        assert len(summary.key_insights) == 2
        assert len(summary.recommendations) == 2
        assert summary.technical_debt["complexity"] == "medium"
        assert summary.dependencies["Python"] == ["flask", "requests"]

    def test_project_summary_default_fields(self):
        """Test project summary with default fields."""
        summary = ProjectSummary(
            total_files=5,
            languages_detected=["Python"],
            project_structure={},
            key_insights=[],
            recommendations=[],
        )

        assert summary.technical_debt == {}
        assert summary.dependencies == {}


class TestAnalysisResponse:
    """Test analysis response model."""

    def test_valid_analysis_response(self):
        """Test valid analysis response creation."""
        file_result = FileAnalysisResult(
            filename="test.py",
            file_type="python",
            language="Python",
            analysis={"purpose": "Test"},
            tokens_used=100,
            processing_time_seconds=1.0,
        )

        batch_result = BatchAnalysisResult(
            batch_id="batch-1",
            files_count=1,
            batch_summary={},
            total_tokens_used=100,
            processing_time_seconds=1.0,
        )

        project_summary = ProjectSummary(
            total_files=1,
            languages_detected=["Python"],
            project_structure={},
            key_insights=[],
            recommendations=[],
        )

        response = AnalysisResponse(
            success=True,
            analysis_id="analysis-123",
            files_analyzed=1,
            file_results=[file_result],
            batch_results=[batch_result],
            project_summary=project_summary,
            total_tokens_used=100,
            total_processing_time_seconds=2.0,
            config_used={"model": "gpt-4"},
            markdown_output="# Analysis Results\n\nTest analysis",
        )

        assert response.success is True
        assert response.analysis_id == "analysis-123"
        assert response.files_analyzed == 1
        assert len(response.file_results) == 1
        assert len(response.batch_results) == 1
        assert response.project_summary == project_summary
        assert response.total_tokens_used == 100
        assert response.total_processing_time_seconds == 2.0
        assert response.config_used == {"model": "gpt-4"}
        assert response.markdown_output.startswith("# Analysis Results")
        assert isinstance(response.timestamp, datetime)

    def test_analysis_response_defaults(self):
        """Test analysis response with default values."""
        response = AnalysisResponse(
            success=True,
            analysis_id="analysis-123",
            files_analyzed=0,
            total_tokens_used=0,
            total_processing_time_seconds=0.0,
            config_used={},
        )

        assert response.file_results == []
        assert response.batch_results == []
        assert response.project_summary is None
        assert response.markdown_output is None


class TestBatchAnalysisResponse:
    """Test batch analysis response model."""

    def test_valid_batch_analysis_response(self):
        """Test valid batch analysis response creation."""
        batch_result = BatchAnalysisResult(
            batch_id="batch-1",
            files_count=2,
            batch_summary={},
            total_tokens_used=200,
            processing_time_seconds=3.0,
        )

        project_summary = ProjectSummary(
            total_files=2,
            languages_detected=["Python"],
            project_structure={},
            key_insights=[],
            recommendations=[],
        )

        response = BatchAnalysisResponse(
            success=True,
            batch_analysis_id="batch-analysis-123",
            total_batches=1,
            batch_results=[batch_result],
            project_summary=project_summary,
            total_files_analyzed=2,
            total_tokens_used=200,
            total_processing_time_seconds=4.0,
            config_used={"model": "gpt-4"},
        )

        assert response.success is True
        assert response.batch_analysis_id == "batch-analysis-123"
        assert response.total_batches == 1
        assert len(response.batch_results) == 1
        assert response.project_summary == project_summary
        assert response.total_files_analyzed == 2
        assert response.total_tokens_used == 200


class TestHealthResponse:
    """Test health response model."""

    def test_valid_health_response(self):
        """Test valid health response creation."""
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            uptime_seconds=3600.0,
            services={"llm": "connected", "storage": "connected"},
            system_info={"cpu_usage": "50%", "memory_usage": "60%"},
        )

        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.uptime_seconds == 3600.0
        assert response.services == {"llm": "connected", "storage": "connected"}
        assert response.system_info["cpu_usage"] == "50%"
        assert isinstance(response.timestamp, datetime)

    def test_health_response_minimal(self):
        """Test health response with minimal fields."""
        response = HealthResponse(status="healthy", version="1.0.0")

        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.uptime_seconds is None
        assert response.services is None
        assert response.system_info is None


class TestVersionResponse:
    """Test version response model."""

    def test_valid_version_response(self):
        """Test valid version response creation."""
        response = VersionResponse(
            api_version="1.0.0",
            app_version="2.0.0",
            python_version="3.12.0",
            build_date="2023-12-01",
            commit_hash="abc123",
        )

        assert response.api_version == "1.0.0"
        assert response.app_version == "2.0.0"
        assert response.python_version == "3.12.0"
        assert response.build_date == "2023-12-01"
        assert response.commit_hash == "abc123"

    def test_version_response_minimal(self):
        """Test version response with minimal fields."""
        response = VersionResponse(
            api_version="1.0.0", app_version="2.0.0", python_version="3.12.0"
        )

        assert response.build_date is None
        assert response.commit_hash is None


class TestConfigResponse:
    """Test config response model."""

    def test_valid_config_response(self):
        """Test valid config response creation."""
        response = ConfigResponse(
            config={"model": "gpt-4", "temperature": 0.1},
            config_sources=["config.yaml", "environment", "defaults"],
        )

        assert response.config == {"model": "gpt-4", "temperature": 0.1}
        assert response.config_sources == ["config.yaml", "environment", "defaults"]
        assert isinstance(response.timestamp, datetime)


class TestFileUploadResponse:
    """Test file upload response model."""

    def test_valid_file_upload_response(self):
        """Test valid file upload response creation."""
        response = FileUploadResponse(
            success=True,
            files_uploaded=3,
            file_details=[
                {"filename": "test1.py", "size": 100},
                {"filename": "test2.js", "size": 200},
            ],
            upload_id="upload-123",
        )

        assert response.success is True
        assert response.files_uploaded == 3
        assert len(response.file_details) == 2
        assert response.upload_id == "upload-123"
        assert isinstance(response.timestamp, datetime)


class TestValidationResponse:
    """Test validation response model."""

    def test_valid_validation_response(self):
        """Test valid validation response creation."""
        response = ValidationResponse(
            valid=False,
            errors=["Missing required field", "Invalid format"],
            warnings=["File size is large"],
            suggestions=["Use shorter filenames", "Compress files"],
        )

        assert response.valid is False
        assert response.errors == ["Missing required field", "Invalid format"]
        assert response.warnings == ["File size is large"]
        assert response.suggestions == ["Use shorter filenames", "Compress files"]

    def test_validation_response_defaults(self):
        """Test validation response with default values."""
        response = ValidationResponse(valid=True)

        assert response.valid is True
        assert response.errors == []
        assert response.warnings == []
        assert response.suggestions == []

import pytest
from unittest.mock import patch, MagicMock
from app.core.config import Settings
from app.services.analysis_service import AnalysisService
from app.models.requests import FileContent, ConfigOverrides
from app.core.exceptions import AnalysisError, FileProcessingError, ConfigurationError


class TestAnalysisService:
    @patch("app.services.analysis_service.FileProcessor")
    @patch("app.services.analysis_service.LLMClient")
    @patch("app.services.analysis_service.ContextManager")
    @patch("app.services.analysis_service.MarkdownFormatter")
    def test_init_success(self, mock_markdown, mock_context, mock_llm, mock_file_processor):
        """Test successful initialization."""
        settings = Settings()
        service = AnalysisService(settings)

        assert service.settings == settings
        assert service.file_processor is not None
        assert service.llm_client is not None
        assert service.context_manager is not None
        assert service.markdown_formatter is not None

    @patch("app.services.analysis_service.FileProcessor", side_effect=Exception("Init failed"))
    def test_init_failure(self, mock_file_processor):
        """Test initialization failure."""
        settings = Settings()

        with pytest.raises(ConfigurationError, match="Failed to initialize analysis components"):
            AnalysisService(settings)

    @pytest.mark.asyncio
    @patch("app.services.analysis_service.FileProcessor")
    @patch("app.services.analysis_service.LLMClient")
    @patch("app.services.analysis_service.ContextManager")
    @patch("app.services.analysis_service.MarkdownFormatter")
    async def test_analyze_files_success(self, mock_markdown, mock_context, mock_llm, mock_file_processor):
        """Test successful file analysis."""
        settings = Settings()
        service = AnalysisService(settings)

        # Mock context manager
        mock_context_instance = MagicMock()
        mock_context_instance.create_batches.return_value = [[{
            "path": "test.py",
            "name": "test.py",
            "content": "print('hello')",
            "extension": ".py",
            "size": 100,
            "lines": 1,
            "language": "python"
        }]]
        service.context_manager = mock_context_instance

        # Mock LLM client
        mock_llm_instance = MagicMock()
        mock_llm_instance.analyze_batch.return_value = {
            "batch_summary": {"main_purpose": "Simple script"},
            "individual_analyses": [{
                "filename": "test.py",
                "file_type": "python",
                "language": "python",
                "analysis": {"purpose": "Print hello"},
                "tokens_used": 50
            }],
            "tokens_used": 100
        }
        service.llm_client = mock_llm_instance

        files = [FileContent(filename="test.py", content="print('hello')", file_type=".py")]

        result = await service.analyze_files(files)

        assert result.success is True
        assert result.files_analyzed == 1
        assert len(result.file_results) == 1
        assert result.file_results[0].filename == "test.py"
        assert result.total_tokens_used == 100

    @pytest.mark.asyncio
    @patch("app.services.analysis_service.FileProcessor")
    @patch("app.services.analysis_service.LLMClient")
    @patch("app.services.analysis_service.ContextManager")
    @patch("app.services.analysis_service.MarkdownFormatter")
    async def test_analyze_files_empty_input(self, mock_markdown, mock_context, mock_llm, mock_file_processor):
        """Test analysis with empty file list."""
        settings = Settings()
        service = AnalysisService(settings)

        files = []

        with pytest.raises(FileProcessingError, match="No valid files to analyze"):
            await service.analyze_files(files)

    @pytest.mark.asyncio
    @patch("app.services.analysis_service.FileProcessor")
    @patch("app.services.analysis_service.LLMClient")
    @patch("app.services.analysis_service.ContextManager")
    @patch("app.services.analysis_service.MarkdownFormatter")
    async def test_analyze_files_with_project_summary(self, mock_markdown, mock_context, mock_llm, mock_file_processor):
        """Test analysis with project summary generation."""
        settings = Settings()
        service = AnalysisService(settings)

        # Mock context manager for multiple files
        mock_context_instance = MagicMock()
        mock_context_instance.create_batches.return_value = [
            [{
                "path": "test1.py", "name": "test1.py", "content": "print('hello')",
                "extension": ".py", "size": 100, "lines": 1, "language": "python"
            }],
            [{
                "path": "test2.py", "name": "test2.py", "content": "print('world')",
                "extension": ".py", "size": 100, "lines": 1, "language": "python"
            }]
        ]
        service.context_manager = mock_context_instance

        # Mock LLM client
        mock_llm_instance = MagicMock()
        mock_llm_instance.analyze_batch.return_value = {
            "batch_summary": {"main_purpose": "Simple script"},
            "individual_analyses": [],
            "tokens_used": 50
        }
        mock_llm_instance.generate_project_summary.return_value = {
            "languages_detected": ["Python"],
            "project_structure": {"type": "scripts"},
            "key_insights": ["Simple Python scripts"],
            "recommendations": ["Add documentation"],
            "technical_debt": {},
            "dependencies": {}
        }
        service.llm_client = mock_llm_instance

        files = [
            FileContent(filename="test1.py", content="print('hello')", file_type=".py"),
            FileContent(filename="test2.py", content="print('world')", file_type=".py")
        ]

        result = await service.analyze_files(files)

        assert result.success is True
        assert result.files_analyzed == 2
        assert result.project_summary is not None
        assert result.project_summary.languages_detected == ["Python"]

    @pytest.mark.asyncio
    @patch("app.services.analysis_service.FileProcessor")
    @patch("app.services.analysis_service.LLMClient")
    @patch("app.services.analysis_service.ContextManager")
    @patch("app.services.analysis_service.MarkdownFormatter")
    async def test_analyze_files_with_markdown_output(self, mock_markdown, mock_context, mock_llm, mock_file_processor):
        """Test analysis with markdown output generation."""
        settings = Settings()
        service = AnalysisService(settings)

        # Mock context manager
        mock_context_instance = MagicMock()
        mock_context_instance.create_batches.return_value = [[{
            "path": "test.py", "name": "test.py", "content": "print('hello')",
            "extension": ".py", "size": 100, "lines": 1, "language": "python"
        }]]
        service.context_manager = mock_context_instance

        # Mock LLM client
        mock_llm_instance = MagicMock()
        mock_llm_instance.analyze_batch.return_value = {
            "batch_summary": {"main_purpose": "Simple script"},
            "individual_analyses": [],
            "tokens_used": 50
        }
        service.llm_client = mock_llm_instance

        # Mock markdown formatter
        mock_markdown_instance = MagicMock()
        mock_markdown_instance.format_results.return_value = "# Analysis Results\n\nSimple script analysis."
        service.markdown_formatter = mock_markdown_instance

        files = [FileContent(filename="test.py", content="print('hello')", file_type=".py")]

        result = await service.analyze_files(files, output_format="markdown")

        assert result.success is True
        assert result.markdown_output == "# Analysis Results\n\nSimple script analysis."

    @pytest.mark.asyncio
    @patch("app.services.analysis_service.FileProcessor")
    @patch("app.services.analysis_service.LLMClient")
    @patch("app.services.analysis_service.ContextManager")
    @patch("app.services.analysis_service.MarkdownFormatter")
    async def test_analyze_files_llm_failure(self, mock_markdown, mock_context, mock_llm, mock_file_processor):
        """Test analysis with LLM failure."""
        settings = Settings()
        service = AnalysisService(settings)

        # Mock context manager
        mock_context_instance = MagicMock()
        mock_context_instance.create_batches.return_value = [[{
            "path": "test.py", "name": "test.py", "content": "print('hello')",
            "extension": ".py", "size": 100, "lines": 1, "language": "python"
        }]]
        service.context_manager = mock_context_instance

        # Mock LLM client to fail
        mock_llm_instance = MagicMock()
        mock_llm_instance.analyze_batch.side_effect = Exception("LLM API failed")
        service.llm_client = mock_llm_instance

        files = [FileContent(filename="test.py", content="print('hello')", file_type=".py")]

        with pytest.raises(Exception):  # Will be wrapped in LLMServiceError
            await service.analyze_files(files)

    @pytest.mark.asyncio
    @patch("app.services.analysis_service.FileProcessor")
    @patch("app.services.analysis_service.LLMClient")
    @patch("app.services.analysis_service.ContextManager")
    @patch("app.services.analysis_service.MarkdownFormatter")
    @patch("pathlib.Path.exists", return_value=True)
    async def test_analyze_from_paths_success(self, mock_exists, mock_markdown, mock_context, mock_llm, mock_file_processor):
        """Test successful analysis from file paths."""
        settings = Settings()
        service = AnalysisService(settings)

        # Mock file processor
        mock_file_processor_instance = MagicMock()
        mock_file_processor_instance.process_input.return_value = [{
            "path": "/path/to/test.py",
            "name": "test.py",
            "content": "print('hello')",
            "extension": ".py",
            "size": 100,
            "lines": 1
        }]
        service.file_processor = mock_file_processor_instance

        # Mock context manager
        mock_context_instance = MagicMock()
        mock_context_instance.create_batches.return_value = [[{
            "path": "/path/to/test.py", "name": "test.py", "content": "print('hello')",
            "extension": ".py", "size": 100, "lines": 1, "language": "python"
        }]]
        service.context_manager = mock_context_instance

        # Mock LLM client
        mock_llm_instance = MagicMock()
        mock_llm_instance.analyze_batch.return_value = {
            "batch_summary": {"main_purpose": "Simple script"},
            "individual_analyses": [],
            "tokens_used": 50
        }
        service.llm_client = mock_llm_instance

        result = await service.analyze_from_paths(["/path/to/test.py"])

        assert result.success is True
        assert result.files_analyzed == 1

    @pytest.mark.asyncio
    @patch("app.services.analysis_service.FileProcessor")
    @patch("app.services.analysis_service.LLMClient")
    @patch("app.services.analysis_service.ContextManager")
    @patch("app.services.analysis_service.MarkdownFormatter")
    @patch("pathlib.Path.exists", return_value=False)
    async def test_analyze_from_paths_nonexistent(self, mock_exists, mock_markdown, mock_context, mock_llm, mock_file_processor):
        """Test analysis from nonexistent paths."""
        settings = Settings()
        service = AnalysisService(settings)

        with pytest.raises(FileProcessingError, match="Path does not exist"):
            await service.analyze_from_paths(["/nonexistent/path"])

    @pytest.mark.asyncio
    async def test_convert_file_content_to_legacy_format(self):
        """Test conversion of FileContent to legacy format."""
        service = AnalysisService.__new__(AnalysisService)  # Create without init

        files = [
            FileContent(filename="/path/to/test.py", content="print('hello')", file_type=".py"),
            FileContent(filename="script.js", content="console.log('hello')", file_type=".js")
        ]

        result = await service._convert_file_content_to_legacy_format(files)

        assert len(result) == 2
        assert result[0]["name"] == "test.py"
        assert result[0]["extension"] == ".py"
        assert result[0]["language"] == "python"
        assert result[1]["name"] == "script.js"
        assert result[1]["extension"] == ".js"
        assert result[1]["language"] == "javascript"

    def test_guess_language_from_extension(self):
        """Test language guessing from extension."""
        service = AnalysisService.__new__(AnalysisService)

        assert service._guess_language_from_extension(".py") == "python"
        assert service._guess_language_from_extension(".js") == "javascript"
        assert service._guess_language_from_extension(".ts") == "typescript"
        assert service._guess_language_from_extension(".unknown") == "unknown"

    @patch("app.services.analysis_service.FileProcessor")
    @patch("app.services.analysis_service.LLMClient")
    @patch("app.services.analysis_service.ContextManager")
    @patch("app.services.analysis_service.MarkdownFormatter")
    def test_get_supported_file_types(self, mock_markdown, mock_context, mock_llm, mock_file_processor):
        """Test getting supported file types."""
        settings = Settings()
        service = AnalysisService(settings)

        file_types = service.get_supported_file_types()
        assert isinstance(file_types, list)
        assert ".py" in file_types
        assert ".js" in file_types

    @patch("app.services.analysis_service.FileProcessor")
    @patch("app.services.analysis_service.LLMClient")
    @patch("app.services.analysis_service.ContextManager")
    @patch("app.services.analysis_service.MarkdownFormatter")
    def test_get_current_config(self, mock_markdown, mock_context, mock_llm, mock_file_processor):
        """Test getting current configuration."""
        settings = Settings()
        service = AnalysisService(settings)

        config = service.get_current_config()
        assert isinstance(config, dict)
        assert "llm" in config
        assert "file_processing" in config
import pytest
from app.models.requests import AnalysisFromPathRequest
from app.models.requests import AnalysisRequest
from app.models.requests import BatchAnalysisRequest
from app.models.requests import ConfigOverrides
from app.models.requests import ConfigRequest
from app.models.requests import FileContent
from app.models.requests import HealthCheckRequest
from pydantic import ValidationError


class TestConfigOverrides:
    """Test configuration overrides model."""

    def test_valid_config_overrides(self):
        """Test valid configuration overrides."""
        config = ConfigOverrides(
            llm_model="gpt-4",
            llm_max_tokens=2000,
            llm_temperature=0.5,
            enable_batch_processing=True,
            max_batch_size=10,
            enable_markdown_output=True,
            exclude_patterns=["*.pyc", "__pycache__"],
        )

        assert config.llm_model == "gpt-4"
        assert config.llm_max_tokens == 2000
        assert config.llm_temperature == 0.5
        assert config.enable_batch_processing is True
        assert config.max_batch_size == 10
        assert config.enable_markdown_output is True
        assert config.exclude_patterns == ["*.pyc", "__pycache__"]

    def test_default_config_overrides(self):
        """Test default values for configuration overrides."""
        config = ConfigOverrides()

        assert config.llm_model is None
        assert config.llm_max_tokens is None
        assert config.llm_temperature is None
        assert config.enable_batch_processing is None
        assert config.max_batch_size is None
        assert config.enable_markdown_output is None
        assert config.exclude_patterns is None

    def test_invalid_llm_max_tokens(self):
        """Test validation of LLM max tokens."""
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 1"
        ):
            ConfigOverrides(llm_max_tokens=0)

        with pytest.raises(
            ValidationError, match="Input should be less than or equal to 8000"
        ):
            ConfigOverrides(llm_max_tokens=9000)

    def test_invalid_llm_temperature(self):
        """Test validation of LLM temperature."""
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 0"
        ):
            ConfigOverrides(llm_temperature=-0.1)

        with pytest.raises(
            ValidationError, match="Input should be less than or equal to 2"
        ):
            ConfigOverrides(llm_temperature=2.1)

    def test_invalid_max_batch_size(self):
        """Test validation of max batch size."""
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 1"
        ):
            ConfigOverrides(max_batch_size=0)

        with pytest.raises(
            ValidationError, match="Input should be less than or equal to 100"
        ):
            ConfigOverrides(max_batch_size=101)

    def test_too_many_exclude_patterns(self):
        """Test validation of exclude patterns count."""
        patterns = [f"pattern_{i}" for i in range(51)]  # 51 patterns

        with pytest.raises(
            ValidationError, match="Too many exclude patterns \\(max 50\\)"
        ):
            ConfigOverrides(exclude_patterns=patterns)


class TestFileContent:
    """Test file content model."""

    def test_valid_file_content(self):
        """Test valid file content."""
        file_content = FileContent(
            filename="test.py", content="print('hello world')", file_type=".py"
        )

        assert file_content.filename == "test.py"
        assert file_content.content == "print('hello world')"
        assert file_content.file_type == ".py"

    def test_file_content_without_file_type(self):
        """Test file content without file type."""
        file_content = FileContent(filename="test.py", content="print('hello world')")

        assert file_content.filename == "test.py"
        assert file_content.content == "print('hello world')"
        assert file_content.file_type is None

    def test_invalid_filename_empty(self):
        """Test validation of empty filename."""
        with pytest.raises(ValidationError, match="Filename must be 1-255 characters"):
            FileContent(filename="", content="test")

    def test_invalid_filename_too_long(self):
        """Test validation of too long filename."""
        long_filename = "a" * 256

        with pytest.raises(ValidationError, match="Filename must be 1-255 characters"):
            FileContent(filename=long_filename, content="test")

    def test_invalid_content_too_large(self):
        """Test validation of too large content."""
        large_content = "a" * 1_000_001  # > 1MB

        with pytest.raises(
            ValidationError, match="File content too large \\(max 1MB\\)"
        ):
            FileContent(filename="test.py", content=large_content)


class TestAnalysisRequest:
    """Test analysis request model."""

    def test_valid_analysis_request(self):
        """Test valid analysis request."""
        files = [
            FileContent(filename="test1.py", content="print('hello')"),
            FileContent(filename="test2.js", content="console.log('hello')"),
        ]

        request = AnalysisRequest(
            files=files,
            config_overrides=ConfigOverrides(llm_temperature=0.5),
            output_format="json",
            verbose=True,
        )

        assert len(request.files) == 2
        assert request.config_overrides.llm_temperature == 0.5
        assert request.output_format == "json"
        assert request.verbose is True

    def test_analysis_request_defaults(self):
        """Test analysis request with default values."""
        files = [FileContent(filename="test.py", content="print('hello')")]

        request = AnalysisRequest(files=files)

        assert len(request.files) == 1
        assert request.config_overrides is None
        assert request.output_format == "json"
        assert request.verbose is False

    def test_invalid_output_format(self):
        """Test validation of output format."""
        files = [FileContent(filename="test.py", content="print('hello')")]

        with pytest.raises(ValidationError, match="String should match pattern"):
            AnalysisRequest(files=files, output_format="invalid")

    def test_valid_output_formats(self):
        """Test all valid output formats."""
        files = [FileContent(filename="test.py", content="print('hello')")]

        for format_type in ["json", "markdown", "both"]:
            request = AnalysisRequest(files=files, output_format=format_type)
            assert request.output_format == format_type

    def test_empty_files_list(self):
        """Test validation of empty files list."""
        with pytest.raises(ValidationError, match="List should have at least 1 item"):
            AnalysisRequest(files=[])

    def test_too_many_files(self):
        """Test validation of too many files."""
        files = [
            FileContent(filename=f"test{i}.py", content="print('hello')")
            for i in range(101)
        ]

        with pytest.raises(ValidationError, match="List should have at most 100 items"):
            AnalysisRequest(files=files)

    def test_duplicate_filenames(self):
        """Test validation of duplicate filenames."""
        files = [
            FileContent(filename="test.py", content="print('hello')"),
            FileContent(
                filename="test.py", content="print('world')"
            ),  # Duplicate filename
        ]

        with pytest.raises(ValidationError, match="Duplicate filenames not allowed"):
            AnalysisRequest(files=files)


class TestBatchAnalysisRequest:
    """Test batch analysis request model."""

    def test_valid_batch_analysis_request(self):
        """Test valid batch analysis request."""
        files = [
            FileContent(filename="test1.py", content="print('hello')"),
            FileContent(filename="test2.py", content="print('world')"),
        ]

        request = BatchAnalysisRequest(files=files, force_batch=True, verbose=True)

        assert len(request.files) == 2
        assert request.force_batch is True
        assert request.verbose is True

    def test_batch_analysis_request_defaults(self):
        """Test batch analysis request with defaults."""
        files = [FileContent(filename="test.py", content="print('hello')")]

        request = BatchAnalysisRequest(files=files)

        assert request.force_batch is False
        assert request.verbose is False
        assert request.output_format == "json"

    def test_batch_analysis_max_files(self):
        """Test batch analysis with maximum files allowed."""
        files = [
            FileContent(filename=f"test{i}.py", content="print('hello')")
            for i in range(500)
        ]

        request = BatchAnalysisRequest(files=files)
        assert len(request.files) == 500

    def test_batch_analysis_too_many_files(self):
        """Test batch analysis with too many files."""
        files = [
            FileContent(filename=f"test{i}.py", content="print('hello')")
            for i in range(501)
        ]

        with pytest.raises(ValidationError, match="List should have at most 500 items"):
            BatchAnalysisRequest(files=files)


class TestAnalysisFromPathRequest:
    """Test analysis from path request model."""

    def test_valid_path_analysis_request(self):
        """Test valid path analysis request."""
        request = AnalysisFromPathRequest(
            paths=["/path/to/code", "/path/to/other"], recursive=False, verbose=True
        )

        assert request.paths == ["/path/to/code", "/path/to/other"]
        assert request.recursive is False
        assert request.verbose is True

    def test_path_analysis_request_defaults(self):
        """Test path analysis request with defaults."""
        request = AnalysisFromPathRequest(paths=["/path/to/code"])

        assert request.recursive is True
        assert request.verbose is False
        assert request.output_format == "json"

    def test_empty_paths_list(self):
        """Test validation of empty paths list."""
        with pytest.raises(ValidationError, match="List should have at least 1 item"):
            AnalysisFromPathRequest(paths=[])

    def test_too_many_paths(self):
        """Test validation of too many paths."""
        paths = [f"/path/{i}" for i in range(11)]

        with pytest.raises(ValidationError, match="List should have at most 10 items"):
            AnalysisFromPathRequest(paths=paths)


class TestHealthCheckRequest:
    """Test health check request model."""

    def test_valid_health_check_request(self):
        """Test valid health check request."""
        request = HealthCheckRequest(detailed=True)
        assert request.detailed is True

    def test_health_check_request_default(self):
        """Test health check request with default values."""
        request = HealthCheckRequest()
        assert request.detailed is False


class TestConfigRequest:
    """Test config request model."""

    def test_valid_config_request(self):
        """Test valid config request."""
        request = ConfigRequest(include_sensitive=True)
        assert request.include_sensitive is True

    def test_config_request_default(self):
        """Test config request with default values."""
        request = ConfigRequest()
        assert request.include_sensitive is False

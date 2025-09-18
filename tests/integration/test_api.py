import os
import tempfile
import zipfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open, MagicMock, AsyncMock


@pytest.fixture
def client():
    """Create test client."""
    # Import here to avoid circular imports
    from app.api_main import app
    return TestClient(app)


@pytest.fixture
def sample_python_file():
    """Create a sample Python file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("print('Hello, world!')\ndef main():\n    pass\n")
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def sample_zip_file():
    """Create a sample ZIP file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as zip_f:
        zip_file_path = zip_f.name

    # Create the zip file separately to ensure it's properly closed
    with zipfile.ZipFile(zip_file_path, 'w') as zf:
        zf.writestr('test.py', "print('hello from zip')")
        zf.writestr('utils.py', "def helper(): return True")

    yield zip_file_path
    os.unlink(zip_file_path)


class TestHealthEndpoints:
    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data

    def test_health_check_detailed(self, client):
        """Test detailed health check."""
        response = client.get("/api/health?detailed=true")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "services" in data
        assert "system_info" in data

    def test_version_endpoint(self, client):
        """Test version endpoint."""
        response = client.get("/api/version")
        assert response.status_code == 200
        data = response.json()
        assert "api_version" in data
        assert "app_version" in data
        assert "python_version" in data

    def test_config_endpoint(self, client):
        """Test config endpoint."""
        response = client.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert "config_sources" in data

    def test_config_endpoint_with_sensitive(self, client):
        """Test config endpoint with sensitive data."""
        response = client.get("/api/config?include_sensitive=true")
        assert response.status_code == 200
        data = response.json()
        assert "config" in data

    def test_info_endpoint(self, client):
        """Test info endpoint."""
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data

    def test_ping_endpoint(self, client):
        """Test ping endpoint."""
        response = client.get("/api/ping")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "pong"
        assert "timestamp" in data


class TestAnalysisEndpoints:
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.llm_client.OpenAI")
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_analyze_files_endpoint(self, mock_prompt_loader, mock_openai, client):
        """Test file analysis endpoint."""
        # Mock LLM response
        mock_client = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"purpose": "Test script", "complexity": "low"}'
        mock_client.chat.completions.create.return_value = mock_response

        # Mock prompt loader
        mock_prompt_loader.return_value.single_file_analysis_prompt = "Analyze: {content}"

        payload = {
            "files": [
                {
                    "filename": "test.py",
                    "content": "print('hello')",
                    "file_type": ".py"
                }
            ],
            "output_format": "json",
            "verbose": False
        }

        response = client.post("/api/analyze", json=payload)

        # Debug output
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "analysis_id" in data
        assert data["files_analyzed"] >= 1

    def test_analyze_files_invalid_payload(self, client):
        """Test file analysis with invalid payload."""
        payload = {
            "files": [],  # Empty files list
        }

        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 422  # Validation error

    def test_analyze_files_duplicate_filenames(self, client):
        """Test file analysis with duplicate filenames."""
        payload = {
            "files": [
                {"filename": "test.py", "content": "print('hello')"},
                {"filename": "test.py", "content": "print('world')"}  # Duplicate
            ]
        }

        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 422

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.llm_client.OpenAI")
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_analyze_upload_endpoint(self, mock_prompt_loader, mock_openai, client, sample_python_file):
        """Test file upload analysis endpoint."""
        # Mock LLM response
        mock_client = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"purpose": "Test script"}'
        mock_client.chat.completions.create.return_value = mock_response

        # Mock prompt loader
        mock_prompt_loader.return_value.single_file_analysis_prompt = "Analyze: {content}"

        # Mock config files
        with patch("builtins.open", mock_open(read_data="llm:\n  model: gpt-4")):
            with open(sample_python_file, 'rb') as f:
                files = {"files": ("test.py", f, "text/plain")}
                response = client.post("/api/analyze/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_analyze_upload_too_large_file(self, client):
        """Test file upload with too large file."""
        # Create a large file content
        large_content = "a" * (51 * 1024 * 1024)  # 51MB

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(large_content)
            f.flush()
            temp_file = f.name

        try:
            with open(temp_file, 'rb') as f:
                files = {"files": ("large.py", f, "text/plain")}
                response = client.post("/api/analyze/upload", files=files)

            # Should return error for file too large
            assert response.status_code in [400, 413, 422]

        finally:
            os.unlink(temp_file)

    def test_analyze_upload_unsupported_file_type(self, client):
        """Test file upload with unsupported file type."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a text file")
            f.flush()
            temp_file = f.name

        try:
            with open(temp_file, 'rb') as f:
                files = {"files": ("test.txt", f, "text/plain")}
                response = client.post("/api/analyze/upload", files=files)

            # Should return error for unsupported file type
            assert response.status_code in [400, 422]

        finally:
            os.unlink(temp_file)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.llm_client.OpenAI")
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_analyze_upload_with_config_overrides(self, mock_prompt_loader, mock_openai, client, sample_python_file):
        """Test file upload analysis with config overrides."""
        # Mock LLM response
        mock_client = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"purpose": "Test script"}'
        mock_client.chat.completions.create.return_value = mock_response

        # Mock prompt loader
        mock_prompt_loader.return_value.single_file_analysis_prompt = "Analyze: {content}"

        # Mock config files
        with patch("builtins.open", mock_open(read_data="llm:\n  model: gpt-4")):
            with open(sample_python_file, 'rb') as f:
                files = {"files": ("test.py", f, "text/plain")}
                data = {
                    "config_overrides": '{"llm_temperature": 0.5}',
                    "output_format": "markdown",
                    "verbose": "true"
                }
                response = client.post("/api/analyze/upload", files=files, data=data)

        assert response.status_code == 200

    def test_analyze_upload_invalid_config_json(self, client, sample_python_file):
        """Test file upload analysis with invalid config JSON."""
        with open(sample_python_file, 'rb') as f:
            files = {"files": ("test.py", f, "text/plain")}
            data = {"config_overrides": '{"invalid": json}'}
            response = client.post("/api/analyze/upload", files=files, data=data)

        assert response.status_code == 400

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.llm_client.OpenAI")
    @patch("app.utils.prompt_loader.PromptLoader")
    @patch("tiktoken.encoding_for_model")
    @patch("zipfile.ZipFile")
    def test_analyze_zip_upload(self, mock_zipfile, mock_tiktoken, mock_prompt_loader, mock_openai, client, sample_zip_file):
        """Test ZIP file upload analysis."""
        # Mock LLM response
        mock_client = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"batch_summary": {"main_purpose": "Test scripts"}}'
        mock_client.chat.completions.create.return_value = mock_response

        # Mock prompt loader
        mock_prompt_loader.return_value.batch_analysis_prompt = "Analyze: {files_info}"

        # Mock tiktoken tokenizer
        mock_encoder = MagicMock()
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5]  # Mock token list
        mock_tiktoken.return_value = mock_encoder

        # Mock zipfile to return some file entries
        mock_zip_instance = MagicMock()
        mock_zip_instance.namelist.return_value = ['test.py', 'utils.py']

        # Mock file info for size checks
        mock_file_info = MagicMock()
        mock_file_info.file_size = 100  # Small file size
        mock_zip_instance.getinfo.return_value = mock_file_info

        # Mock the file extraction mechanism
        def mock_open_file(file_path):
            mock_file_obj = MagicMock()
            content_map = {
                'test.py': "print('hello from zip')".encode('utf-8'),
                'utils.py': "def helper(): return True".encode('utf-8')
            }
            mock_file_obj.read.return_value = content_map[file_path]
            # Make it work as a context manager
            mock_file_obj.__enter__.return_value = mock_file_obj
            mock_file_obj.__exit__.return_value = None
            return mock_file_obj

        mock_zip_instance.open.side_effect = mock_open_file
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        # Mock config files with proper file processing config
        config_data = """
llm:
  model: gpt-4
file_processing:
  supported_extensions:
    - .py
    - .js
    - .ts
  exclude_patterns:
    - __pycache__
    - .git
"""
        with patch("builtins.open", mock_open(read_data=config_data)):
            with open(sample_zip_file, 'rb') as f:
                files = {"files": ("test.zip", f, "application/zip")}
                response = client.post("/api/analyze/upload", files=files)

        # Debug output
        if response.status_code != 200:
            print(f"Zip upload response status: {response.status_code}")
            print(f"Zip upload response body: {response.text}")

        assert response.status_code == 200

    def test_analyze_paths_endpoint_invalid_path(self, client):
        """Test path analysis with invalid path."""
        payload = {
            "paths": ["/nonexistent/path"],
            "recursive": True
        }

        response = client.post("/api/analyze/paths", json=payload)
        assert response.status_code == 400

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.llm_client.OpenAI")
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_batch_analysis_endpoint(self, mock_prompt_loader, mock_openai, client):
        """Test batch analysis endpoint."""
        # Mock LLM response
        mock_client = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"batch_summary": {"main_purpose": "Test scripts"}}'
        mock_client.chat.completions.create.return_value = mock_response

        # Mock prompt loader
        mock_prompt_loader.return_value.batch_analysis_prompt = "Analyze: {files_info}"

        # Mock config files
        with patch("builtins.open", mock_open(read_data="llm:\n  model: gpt-4")):
            payload = {
                "files": [
                    {"filename": "test1.py", "content": "print('hello')"},
                    {"filename": "test2.py", "content": "print('world')"}
                ],
                "force_batch": True
            }

            response = client.post("/api/analyze/batch", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "batch_analysis_id" in data

    def test_supported_types_endpoint(self, client):
        """Test supported file types endpoint."""
        response = client.get("/api/analyze/supported-types")
        assert response.status_code == 200
        data = response.json()
        assert "supported_extensions" in data
        assert isinstance(data["supported_extensions"], list)

    def test_analysis_config_endpoint(self, client):
        """Test analysis config endpoint."""
        response = client.get("/api/analyze/config")
        assert response.status_code == 200
        data = response.json()
        assert "config" in data

    def test_validate_files_endpoint(self, client, sample_python_file):
        """Test file validation endpoint."""
        with open(sample_python_file, 'rb') as f:
            files = {"files": ("test.py", f, "text/plain")}
            response = client.post("/api/analyze/validate", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "all_valid" in data
        assert "total_files" in data
        assert "validation_results" in data


class TestErrorHandling:
    def test_404_endpoint(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    def test_invalid_json_payload(self, client):
        """Test invalid JSON payload handling."""
        response = client.post(
            "/api/analyze",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test missing required fields handling."""
        payload = {}  # Missing required 'files' field

        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 422

    @patch.dict(os.environ, {}, clear=True)  # Remove API key
    def test_missing_api_key(self, client):
        """Test handling when API key is missing."""
        payload = {
            "files": [
                {"filename": "test.py", "content": "print('hello')"}
            ]
        }

        response = client.post("/api/analyze", json=payload)
        # Should handle missing API key gracefully
        assert response.status_code in [400, 500, 503]


class TestCORS:
    def test_cors_options_request(self, client):
        """Test CORS preflight request."""
        response = client.options("/api/analyze")
        # CORS handling depends on app configuration
        assert response.status_code in [200, 405]


class TestRateLimiting:
    def test_multiple_requests(self, client):
        """Test multiple requests don't cause issues."""
        # Make multiple health check requests
        for _ in range(5):
            response = client.get("/api/health")
            assert response.status_code == 200
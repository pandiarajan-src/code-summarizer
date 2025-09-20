import os
import pytest
from unittest.mock import patch
from app.core.config import Settings


class TestSettings:
    def test_default_values(self):
        """Test default configuration values."""
        # Mock environment to ensure clean test
        with patch.dict(os.environ, {}, clear=True), \
             patch('app.core.config.find_env_file', return_value=None):
            settings = Settings(OPENAI_API_KEY="test-key")

            assert settings.api_title == "Code Summarizer API"
            assert settings.api_version == "1.0.0"
            assert settings.debug is False
            assert settings.host == "127.0.0.1"  # Default host in local environment
            assert settings.port == 8000
            assert settings.llm_model == "gpt-4o"
            assert settings.llm_temperature == 0.1
            assert settings.max_file_size_mb == 50
            assert settings.max_files_per_request == 100

    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "DEBUG": "true",
            "PORT": "9000",
            "MODEL_NAME": "gpt-3.5-turbo",  # Use MODEL_NAME instead of LLM_MODEL
            "LLM_TEMPERATURE": "0.5",
            "MAX_FILE_SIZE_MB": "100"
        }, clear=True), \
             patch('app.core.config.find_env_file', return_value=None):
            settings = Settings()

            assert settings.debug is True
            assert settings.port == 9000
            assert settings.llm_model == "gpt-3.5-turbo"
            assert settings.llm_temperature == 0.5
            assert settings.max_file_size_mb == 100

    def test_max_file_size_validation(self):
        """Test max file size validation."""
        with pytest.raises(ValueError, match="max_file_size_mb must be between 1 and 500"):
            Settings(OPENAI_API_KEY="test-key", max_file_size_mb=0)

        with pytest.raises(ValueError, match="max_file_size_mb must be between 1 and 500"):
            Settings(OPENAI_API_KEY="test-key", max_file_size_mb=501)

    def test_temperature_validation(self):
        """Test temperature validation."""
        with pytest.raises(ValueError, match="llm_temperature must be between 0.0 and 2.0"):
            Settings(OPENAI_API_KEY="test-key", llm_temperature=-0.1)

        with pytest.raises(ValueError, match="llm_temperature must be between 0.0 and 2.0"):
            Settings(OPENAI_API_KEY="test-key", llm_temperature=2.1)

    def test_port_validation(self):
        """Test port validation."""
        with pytest.raises(ValueError, match="port must be between 1 and 65535"):
            Settings(OPENAI_API_KEY="test-key", port=0)

        with pytest.raises(ValueError, match="port must be between 1 and 65535"):
            Settings(OPENAI_API_KEY="test-key", port=65536)

    def test_max_file_size_bytes_property(self):
        """Test max_file_size_bytes property calculation."""
        settings = Settings(OPENAI_API_KEY="test-key", max_file_size_mb=10)
        assert settings.max_file_size_bytes == 10 * 1024 * 1024

    def test_to_legacy_config(self):
        """Test conversion to legacy config format."""
        # Mock environment to avoid loading .env file
        with patch.dict(os.environ, {}, clear=True), \
             patch('app.core.config.find_env_file', return_value=None):
            settings = Settings(
                OPENAI_API_KEY="test-key",
                llm_temperature=0.2,
                enable_batch_processing=True
            )
            # Override the model after creation to test the exact value
            settings.llm_model = "gpt-4"

            legacy_config = settings.to_legacy_config()

            assert legacy_config["llm"]["api_key"] == "test-key"
            assert legacy_config["llm"]["model"] == "gpt-4"
            assert legacy_config["llm"]["temperature"] == 0.2
            assert legacy_config["analysis"]["enable_batch_processing"] is True
            assert isinstance(legacy_config["file_processing"]["supported_extensions"], list)
            assert isinstance(legacy_config["file_processing"]["exclude_patterns"], list)

    def test_allowed_file_types(self):
        """Test that allowed file types contain expected extensions."""
        settings = Settings(OPENAI_API_KEY="test-key")

        expected_types = [".py", ".js", ".ts", ".java", ".cpp", ".go", ".rs"]
        for file_type in expected_types:
            assert file_type in settings.allowed_file_types

    def test_exclude_patterns(self):
        """Test that exclude patterns contain expected patterns."""
        settings = Settings(OPENAI_API_KEY="test-key")

        expected_patterns = ["__pycache__", ".git", "node_modules", "*.pyc", ".env"]
        for pattern in expected_patterns:
            assert pattern in settings.exclude_patterns
import pytest
import sys
from unittest.mock import MagicMock, patch, PropertyMock
from app.api.routes.health import health_check, get_version, get_config, get_info, ping
from app.core.config import Settings
from app.models.responses import HealthResponse, VersionResponse, ConfigResponse


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_basic(self):
        """Test basic health check."""
        with patch('app.core.config.find_env_file', return_value=None):
            mock_settings = Settings(OPENAI_API_KEY="test-key")
            mock_settings.api_version = "1.0.0"

        with patch('app.api.routes.health.startup_time', 100.0), \
             patch('time.time', return_value=200.0):

            result = await health_check(detailed=False, current_settings=mock_settings)

        assert isinstance(result, HealthResponse)
        assert result.status == "healthy"
        assert result.version == "1.0.0"
        assert result.uptime_seconds == 100.0
        assert result.services is None
        assert result.system_info is None

    @pytest.mark.asyncio
    async def test_health_check_detailed(self):
        """Test detailed health check."""
        with patch('app.core.config.find_env_file', return_value=None):
            mock_settings = Settings(OPENAI_API_KEY="test-key")
            mock_settings.api_version = "1.0.0"
            mock_settings.config_file_path = "config.yaml"
            mock_settings.prompts_file_path = "prompts.yaml"

        with patch('app.api.routes.health.startup_time', 100.0), \
             patch('time.time', return_value=200.0):

            result = await health_check(detailed=True, current_settings=mock_settings)

        assert result.status == "healthy"
        assert result.services["llm_service"] == "configured"
        assert result.services["file_processing"] == "available"
        assert result.services["configuration"] == "loaded"
        assert result.system_info["python_version"] == sys.version

    @pytest.mark.asyncio
    async def test_health_check_detailed_no_api_key(self):
        """Test detailed health check without API key."""
        with patch('app.core.config.find_env_file', return_value=None):
            # Create settings with API key first, then mock it to appear empty
            mock_settings = Settings(OPENAI_API_KEY="test-key")
            mock_settings.api_version = "1.0.0"
            # Mock the openai_api_key property to return None
            with patch.object(mock_settings, 'openai_api_key', None):

                with patch('app.api.routes.health.startup_time', 100.0), \
                     patch('time.time', return_value=200.0):

                    result = await health_check(detailed=True, current_settings=mock_settings)

                assert result.status == "healthy"
                assert result.services["llm_service"] == "not_configured"


class TestGetVersion:
    @pytest.mark.asyncio
    async def test_get_version(self):
        """Test version endpoint."""
        with patch('app.core.config.find_env_file', return_value=None):
            mock_settings = Settings(OPENAI_API_KEY="test-key")
            mock_settings.api_version = "1.0.0"

        result = await get_version(current_settings=mock_settings)

        assert isinstance(result, VersionResponse)
        assert result.app_version == "1.0.0"
        assert result.python_version == sys.version
        assert result.build_date is None
        assert result.commit_hash is None


class TestGetConfig:
    @pytest.mark.asyncio
    async def test_get_config_without_sensitive(self):
        """Test getting config without sensitive information."""
        with patch('app.core.config.find_env_file', return_value=None):
            mock_settings = Settings(OPENAI_API_KEY="secret-key", config_file_path="config.yaml")

        result = await get_config(include_sensitive=False, current_settings=mock_settings)

        assert isinstance(result, ConfigResponse)
        assert result.config["openai_api_key"] == "***"
        assert result.config["api_version"] == "1.0.0"
        assert "config_file" in result.config_sources

    @pytest.mark.asyncio
    async def test_get_config_with_sensitive(self):
        """Test getting config with sensitive information."""
        with patch('app.core.config.find_env_file', return_value=None):
            mock_settings = Settings(OPENAI_API_KEY="secret-key", config_file_path="")

        result = await get_config(include_sensitive=True, current_settings=mock_settings)

        assert isinstance(result, ConfigResponse)
        assert result.config["openai_api_key"] == "secret-key"
        assert result.config["api_version"] == "1.0.0"
        assert "config_file" not in result.config_sources

    @pytest.mark.asyncio
    async def test_get_config_no_api_key(self):
        """Test getting config with masked API key."""
        with patch('app.core.config.find_env_file', return_value=None):
            mock_settings = Settings(OPENAI_API_KEY="secret-key", config_file_path="config.yaml")

        result = await get_config(include_sensitive=False, current_settings=mock_settings)

        assert isinstance(result, ConfigResponse)
        # When sensitive=False, API key should be masked
        assert result.config["openai_api_key"] == "***"

    @pytest.mark.asyncio
    async def test_get_config_sources(self):
        """Test config sources detection."""
        with patch('app.core.config.find_env_file', return_value=None):
            mock_settings = Settings(OPENAI_API_KEY="test-key", config_file_path="")

        result = await get_config(include_sensitive=False, current_settings=mock_settings)

        assert "defaults" in result.config_sources
        assert "config_file" not in result.config_sources
        assert "environment" in result.config_sources


class TestGetInfo:
    @pytest.mark.asyncio
    async def test_get_info(self):
        """Test info endpoint."""
        with patch('app.core.config.find_env_file', return_value=None):
            mock_settings = Settings(OPENAI_API_KEY="test-key")
            mock_settings.api_title = "Code Summarizer API"
            mock_settings.api_version = "1.0.0"

        result = await get_info(current_settings=mock_settings)

        assert isinstance(result, dict)
        assert result["name"] == "Code Summarizer API"
        assert result["version"] == "1.0.0"
        assert "description" in result
        assert "endpoints" in result


class TestPing:
    @pytest.mark.asyncio
    async def test_ping(self):
        """Test ping endpoint."""
        result = await ping()

        assert result["message"] == "pong"
        assert "timestamp" in result
"""Unit tests for LLMClient class."""

from unittest.mock import MagicMock, mock_open, patch

import pytest

from app.services.llm_client import LLMClient


class TestLLMClient:
    """Test suite for LLM client functionality."""
    @patch("pathlib.Path.open", mock_open(read_data="llm:\n  model: gpt-4\n  max_tokens: 2000"))
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_init_with_config(self, mock_prompt_loader_class):
        """Test initialization with configuration file."""
        # Create a mock instance
        mock_prompt_loader = MagicMock()
        mock_prompt_loader.single_file_analysis_prompt = "Analyze: {content}"
        mock_prompt_loader.batch_analysis_prompt = "Analyze batch: {files_info}"
        mock_prompt_loader_class.return_value = mock_prompt_loader

        client = LLMClient("test_config.yaml", "test_prompts.yaml")

        assert client.model == "gpt-4"
        assert client.max_tokens == 2000
        assert client.temperature == 0.1

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_init_without_config(self, mock_file):
        """Test initialization without configuration file."""
        with patch("app.utils.prompt_loader.PromptLoader"):
            client = LLMClient("nonexistent.yaml")

            assert client.model == "gpt-4o"
            assert client.max_tokens == 4000

    def test_init_without_api_key(self):
        """Test initialization fails without API key."""
        from unittest.mock import MagicMock

        # Create mock settings with no API key
        mock_settings = MagicMock()
        mock_settings.openai_api_key = None
        mock_settings.openai_base_url = "https://api.openai.com/v1"

        with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
            LLMClient(settings=mock_settings)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_make_api_call_success(self, mock_prompt_loader):
        """Test successful API call."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"result": "success"}'

        with patch("app.services.llm_client.OpenAIClientPool.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            client = LLMClient()
            result = client._make_api_call("test prompt")

            assert result == '{"result": "success"}'
            mock_client.chat.completions.create.assert_called_once()

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_make_api_call_empty_response(self, mock_prompt_loader):
        """Test API call with empty response."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = None

        with patch("app.services.llm_client.OpenAIClientPool.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            client = LLMClient()

            with pytest.raises(Exception, match="LLM returned empty response"):
                client._make_api_call("test prompt")

    def test_parse_json_response_valid_json(self):
        """Test parsing valid JSON response."""
        client = LLMClient.__new__(LLMClient)  # Create instance without calling __init__

        response = '{"key": "value", "number": 42}'
        result = client._parse_json_response(response)

        assert result == {"key": "value", "number": 42}

    def test_parse_json_response_markdown_json(self):
        """Test parsing JSON in markdown code blocks."""
        client = LLMClient.__new__(LLMClient)

        response = 'Here is the analysis:\n```json\n{"key": "value"}\n```\nEnd of response'
        result = client._parse_json_response(response)

        assert result == {"key": "value"}

    def test_parse_json_response_embedded_json(self):
        """Test parsing JSON embedded in text."""
        client = LLMClient.__new__(LLMClient)

        response = 'Some text before {"key": "value", "nested": {"inner": true}} some text after'
        result = client._parse_json_response(response)

        assert result == {"key": "value", "nested": {"inner": True}}

    def test_parse_json_response_invalid(self):
        """Test parsing invalid JSON response."""
        client = LLMClient.__new__(LLMClient)

        response = 'This is not JSON at all'

        with pytest.raises(Exception, match="Could not parse JSON from LLM response"):
            client._parse_json_response(response)

    def test_guess_language_from_extension(self):
        """Test language guessing from file extension."""
        client = LLMClient.__new__(LLMClient)

        assert client._guess_language_from_extension(".py") == "Python"
        assert client._guess_language_from_extension(".js") == "JavaScript"
        assert client._guess_language_from_extension(".ts") == "TypeScript"
        assert client._guess_language_from_extension(".java") == "Java"
        assert client._guess_language_from_extension(".unknown") == "Unknown"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_detect_languages(self, mock_prompt_loader):
        """Test language detection functionality."""
        mock_prompt_loader.return_value.language_detection_prompt = (
            "Detect languages: {files_content}"
        )

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"languages": ["Python", "JavaScript"]}'

        with patch("app.services.llm_client.OpenAIClientPool.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            client = LLMClient()

            files_data = [
                {"name": "test.py", "content": "print('hello')"},
                {"name": "test.js", "content": "console.log('hello')"}
            ]

            result = client.detect_languages(files_data)
            assert result == {"languages": ["Python", "JavaScript"]}

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_analyze_single_file(self, mock_prompt_loader):
        """Test single file analysis."""
        mock_prompt_loader.return_value.single_file_analysis_prompt = (
            "Analyze: {filename} {language} {content}"
        )

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"purpose": "Test file", "complexity": "low"}'

        with patch("app.services.llm_client.OpenAIClientPool.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            client = LLMClient()

            file_data = {
                "name": "test.py",
                "path": "/path/to/test.py",
                "content": "print('hello')",
                "extension": ".py",
                "size": 100,
                "lines": 1
            }

            result = client.analyze_single_file(file_data)

            assert result["purpose"] == "Test file"
            assert result["complexity"] == "low"
            assert result["filename"] == "test.py"
            assert result["filepath"] == "/path/to/test.py"
            assert result["file_size"] == 100
            assert result["line_count"] == 1

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_analyze_batch_single_file(self, mock_prompt_loader):
        """Test batch analysis with single file."""
        mock_prompt_loader.return_value.single_file_analysis_prompt = (
            "Analyze: {filename} {language} {content}"
        )

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"purpose": "Test file"}'

        with patch("app.services.llm_client.OpenAIClientPool.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            client = LLMClient()

            file_data = {
                "name": "test.py",
                "path": "/path/to/test.py",
                "content": "print('hello')",
                "extension": ".py",
                "size": 100,
                "lines": 1
            }

            result = client.analyze_batch([file_data])

            assert result["batch_summary"]["main_purpose"] == "Single file analysis"
            assert len(result["files"]) == 1

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_analyze_batch_multiple_files(self, mock_prompt_loader):
        """Test batch analysis with multiple files."""
        mock_prompt_loader.return_value.batch_analysis_prompt = "Analyze batch: {files_info}"

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"batch_summary": {"main_purpose": "Web application"}}'

        with patch("app.services.llm_client.OpenAIClientPool.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            client = LLMClient()

            files_data = [
                {
                    "name": "test1.py",
                    "path": "/path/to/test1.py",
                    "content": "print('hello')",
                    "extension": ".py",
                    "lines": 1
                },
                {
                    "name": "test2.js",
                    "path": "/path/to/test2.js",
                    "content": "console.log('hello')",
                    "extension": ".js",
                    "lines": 1
                }
            ]

            result = client.analyze_batch(files_data)
            assert result["batch_summary"]["main_purpose"] == "Web application"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_generate_project_summary(self, mock_prompt_loader):
        """Test project summary generation."""
        mock_prompt_loader.return_value.project_summary_prompt = (
            "Summarize project: {total_files} {languages} {analysis_summary}"
        )

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"project_type": "Web application", "main_language": "Python"}'

        with patch("app.services.llm_client.OpenAIClientPool.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            client = LLMClient()

            files_data = [
                {"name": "test.py", "extension": ".py"},
                {"name": "test.js", "extension": ".js"}
            ]

            analysis_results = [
                {"batch_summary": {"main_purpose": "Backend API"}},
                {"batch_summary": {"main_purpose": "Frontend UI"}}
            ]

            result = client.generate_project_summary(files_data, analysis_results)

            assert result["project_type"] == "Web application"
            assert result["main_language"] == "Python"

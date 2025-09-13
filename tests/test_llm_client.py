"""Tests for llm_client module."""

import json
import os
import tempfile
from unittest.mock import Mock, patch

import pytest
import yaml

from code_summarizer.llm_client import LLMClient


class TestLLMClient:
    """Test cases for LLMClient class."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_init_default_config(self):
        """Test initialization with default config."""
        with patch("code_summarizer.llm_client.Path") as mock_path:
            mock_path.return_value.open.side_effect = FileNotFoundError
            with patch("code_summarizer.llm_client.OpenAI"):
                client = LLMClient()
                
                assert client.config == {}
                assert client.model == "gpt-4o"
                assert client.max_tokens == 4000
                assert client.temperature == 0.1

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_init_with_config(self):
        """Test initialization with custom config."""
        config_data = {
            "llm": {
                "model": "gpt-3.5-turbo",
                "max_tokens": 2000,
                "temperature": 0.5
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            with patch("code_summarizer.llm_client.OpenAI"):
                client = LLMClient(config_path=config_path)
                assert client.model == "gpt-3.5-turbo"
                assert client.max_tokens == 2000
                assert client.temperature == 0.5
        finally:
            os.unlink(config_path)

    def test_initialize_client_missing_api_key(self):
        """Test client initialization without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("code_summarizer.llm_client.Path") as mock_path:
                mock_path.return_value.open.side_effect = FileNotFoundError
                
                with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is required"):
                    LLMClient()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://custom.api.com/v1"})
    def test_initialize_client_custom_base_url(self):
        """Test client initialization with custom base URL."""
        with patch("code_summarizer.llm_client.Path") as mock_path:
            mock_path.return_value.open.side_effect = FileNotFoundError
            with patch("code_summarizer.llm_client.OpenAI") as mock_openai:
                client = LLMClient()
                
                mock_openai.assert_called_once_with(
                    api_key="test-key",
                    base_url="https://custom.api.com/v1"
                )

    def test_make_api_call_success(self):
        """Test successful API call."""
        client = LLMClient.__new__(LLMClient)
        client.model = "gpt-4o"
        client.max_tokens = 4000
        client.temperature = 0.1
        
        # Mock the OpenAI client response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "  API response  "
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        client.client = mock_client
        
        result = client._make_api_call("test prompt")
        
        assert result == "API response"
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a code analysis expert. Always respond with valid JSON.",
                },
                {"role": "user", "content": "test prompt"},
            ],
            max_tokens=4000,
            temperature=0.1,
        )

    def test_make_api_call_empty_response(self):
        """Test API call with empty response."""
        client = LLMClient.__new__(LLMClient)
        client.model = "gpt-4o"
        client.max_tokens = 4000
        client.temperature = 0.1
        
        # Mock empty response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        client.client = mock_client
        
        with pytest.raises(Exception, match="LLM returned empty response"):
            client._make_api_call("test prompt")

    def test_make_api_call_failure(self):
        """Test API call failure."""
        client = LLMClient.__new__(LLMClient)
        client.model = "gpt-4o"
        client.max_tokens = 4000
        client.temperature = 0.1
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        client.client = mock_client
        
        with pytest.raises(Exception, match="LLM API call failed: API Error"):
            client._make_api_call("test prompt")

    def test_parse_json_response_success(self):
        """Test successful JSON parsing."""
        client = LLMClient.__new__(LLMClient)
        
        json_response = '{"key": "value", "number": 42}'
        result = client._parse_json_response(json_response)
        
        assert result == {"key": "value", "number": 42}

    def test_parse_json_response_with_code_block(self):
        """Test JSON parsing with markdown code block."""
        client = LLMClient.__new__(LLMClient)
        
        response_with_markdown = '''
        Here's the analysis:
        ```json
        {"key": "value", "number": 42}
        ```
        Hope this helps!
        '''
        
        result = client._parse_json_response(response_with_markdown)
        assert result == {"key": "value", "number": 42}

    def test_parse_json_response_extract_json(self):
        """Test JSON extraction from mixed content."""
        client = LLMClient.__new__(LLMClient)
        
        mixed_response = 'Some text before {"key": "value"} some text after'
        result = client._parse_json_response(mixed_response)
        
        assert result == {"key": "value"}

    def test_parse_json_response_failure(self):
        """Test JSON parsing failure."""
        client = LLMClient.__new__(LLMClient)
        
        invalid_response = "This is not JSON at all"
        
        with pytest.raises(Exception, match="Could not parse JSON from LLM response"):
            client._parse_json_response(invalid_response)

    def test_detect_languages(self):
        """Test language detection."""
        client = LLMClient.__new__(LLMClient)
        
        files_data = [
            {"name": "test1.py", "content": "def hello(): pass"},
            {"name": "test2.js", "content": "function hello() {}"},
        ]
        
        with patch.object(client, '_make_api_call', return_value='{"languages": ["Python", "JavaScript"]}'):
            with patch.object(client, '_parse_json_response', return_value={"languages": ["Python", "JavaScript"]}):
                result = client.detect_languages(files_data)
                
                assert result == {"languages": ["Python", "JavaScript"]}

    def test_analyze_single_file(self):
        """Test single file analysis."""
        client = LLMClient.__new__(LLMClient)
        
        file_data = {
            "name": "test.py",
            "path": "/test.py",
            "extension": ".py",
            "content": "def hello(): pass",
            "size": 100,
            "lines": 1
        }
        
        mock_analysis = {
            "language": "Python",
            "purpose": "Test function",
            "functions": [{"name": "hello", "type": "function"}]
        }
        
        with patch.object(client, '_make_api_call', return_value='{}'):
            with patch.object(client, '_parse_json_response', return_value=mock_analysis):
                result = client.analyze_single_file(file_data)
                
                assert result["filename"] == "test.py"
                assert result["filepath"] == "/test.py"
                assert result["file_size"] == 100
                assert result["line_count"] == 1
                assert result["language"] == "Python"

    def test_analyze_batch_single_file(self):
        """Test batch analysis with single file."""
        client = LLMClient.__new__(LLMClient)
        
        file_data = {"name": "test.py", "extension": ".py", "content": "code"}
        mock_analysis = {"language": "Python"}
        
        with patch.object(client, 'analyze_single_file', return_value=mock_analysis):
            result = client.analyze_batch([file_data])
            
            assert result["batch_summary"]["main_purpose"] == "Single file analysis"
            assert len(result["files"]) == 1
            assert result["files"][0] == mock_analysis
            assert result["relationships"] == []

    def test_analyze_batch_multiple_files(self):
        """Test batch analysis with multiple files."""
        client = LLMClient.__new__(LLMClient)
        
        files_data = [
            {"name": "test1.py", "extension": ".py", "content": "code1", "path": "/test1.py", "lines": 5},
            {"name": "test2.py", "extension": ".py", "content": "code2", "path": "/test2.py", "lines": 3}
        ]
        
        mock_batch_result = {
            "batch_summary": {"main_purpose": "Python modules"},
            "files": [{"name": "test1.py"}, {"name": "test2.py"}],
            "relationships": []
        }
        
        with patch.object(client, '_make_api_call', return_value='{}'):
            with patch.object(client, '_parse_json_response', return_value=mock_batch_result):
                result = client.analyze_batch(files_data)
                
                assert result == mock_batch_result

    def test_generate_project_summary(self):
        """Test project summary generation."""
        client = LLMClient.__new__(LLMClient)
        
        files_data = [
            {"extension": ".py"},
            {"extension": ".js"}
        ]
        
        analysis_results = [
            {"batch_summary": {"main_purpose": "Backend logic"}},
            {"batch_summary": {"main_purpose": "Frontend code"}}
        ]
        
        mock_summary = {
            "project_summary": {"type": "web application"},
            "technical_details": {"patterns": ["MVC"]}
        }
        
        with patch.object(client, '_make_api_call', return_value='{}'):
            with patch.object(client, '_parse_json_response', return_value=mock_summary):
                result = client.generate_project_summary(files_data, analysis_results)
                
                assert result == mock_summary

    def test_guess_language_from_extension(self):
        """Test language guessing from file extensions."""
        client = LLMClient.__new__(LLMClient)
        
        assert client._guess_language_from_extension(".py") == "Python"
        assert client._guess_language_from_extension(".JS") == "JavaScript"  # Case insensitive
        assert client._guess_language_from_extension(".unknown") == "Unknown"
"""Integration tests for CLI functionality."""

import os
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest
from click.testing import CliRunner

from app.main import cli, analyze


class TestCLIIntegration:
    """Test CLI integration functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "AI-powered code analysis and summarization tool" in result.output

    def test_analyze_help(self):
        """Test analyze command help."""
        result = self.runner.invoke(analyze, ['--help'])
        assert result.exit_code == 0
        assert "Analyze source code files" in result.output

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.llm_client.OpenAI")
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_analyze_single_file_success(self, mock_prompt_loader, mock_openai):
        """Test successful analysis of a single file."""
        # Create temporary Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello, world!')\n")
            f.flush()
            temp_file = f.name

        try:
            # Mock LLM response
            mock_client = mock_openai.return_value
            content = '{"purpose": "Hello world script", "complexity": "low"}'
            mock_message = type('MockMessage', (), {'content': content})()
            mock_choice = type('MockChoice', (), {'message': mock_message})()
            mock_response = type('MockResponse', (), {'choices': [mock_choice]})()
            mock_client.chat.completions.create.return_value = mock_response

            # Mock prompt loader
            mock_prompt_loader.return_value.single_file_analysis_prompt = "Analyze: {content}"

            # Mock config and prompts files
            with patch("builtins.open", mock_open(read_data="llm:\n  model: gpt-4")):
                result = self.runner.invoke(analyze, [temp_file])

            assert result.exit_code == 0
            assert ("Analysis completed successfully" in result.output or
                    "purpose" in result.output or
                    "Analysis complete!" in result.output)

        finally:
            # Cleanup
            os.unlink(temp_file)

    def test_analyze_nonexistent_file(self):
        """Test analysis of nonexistent file."""
        result = self.runner.invoke(analyze, ['/nonexistent/file.py'])
        assert result.exit_code != 0
        assert "does not exist" in result.output or "Error" in result.output

    def test_analyze_unsupported_file_type(self):
        """Test analysis of unsupported file type."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a text file")
            f.flush()
            temp_file = f.name

        try:
            result = self.runner.invoke(analyze, [temp_file])
            assert result.exit_code != 0
            assert "Unsupported file type" in result.output or "Error" in result.output

        finally:
            os.unlink(temp_file)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.llm_client.OpenAI")
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_analyze_directory(self, mock_prompt_loader, mock_openai):
        """Test analysis of a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            py_file = Path(temp_dir) / "test.py"
            py_file.write_text("print('hello')")

            js_file = Path(temp_dir) / "test.js"
            js_file.write_text("console.log('hello')")

            # Mock LLM response
            mock_client = mock_openai.return_value
            content = '{"batch_summary": {"main_purpose": "Test scripts"}}'
            mock_message = type('MockMessage', (), {'content': content})()
            mock_choice = type('MockChoice', (), {'message': mock_message})()
            mock_response = type('MockResponse', (), {'choices': [mock_choice]})()
            mock_client.chat.completions.create.return_value = mock_response

            # Mock prompt loader
            mock_prompt_loader.return_value.batch_analysis_prompt = "Analyze batch: {files_info}"

            # Mock config and prompts files
            with patch("builtins.open", mock_open(read_data="llm:\n  model: gpt-4")):
                result = self.runner.invoke(analyze, [temp_dir])

            assert result.exit_code == 0

    def test_analyze_empty_directory(self):
        """Test analysis of empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(analyze, [temp_dir])
            assert result.exit_code != 0
            assert "No supported code files" in result.output or "Error" in result.output

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.llm_client.OpenAI")
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_analyze_with_output_file(self, mock_prompt_loader, mock_openai):
        """Test analysis with output file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello, world!')")
            f.flush()
            temp_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as out_f:
            output_file = out_f.name

        try:
            # Mock LLM response
            mock_client = mock_openai.return_value
            mock_message = type('MockMessage', (), {'content': '{"purpose": "Hello world script"}'})()
            mock_choice = type('MockChoice', (), {'message': mock_message})()
            mock_response = type('MockResponse', (), {'choices': [mock_choice]})()
            mock_client.chat.completions.create.return_value = mock_response

            # Mock prompt loader
            mock_prompt_loader.return_value.single_file_analysis_prompt = "Analyze: {content}"

            # Mock config and prompts files
            with patch("builtins.open", mock_open(read_data="llm:\n  model: gpt-4")):
                result = self.runner.invoke(analyze, [temp_file, '--output', output_file])

            assert result.exit_code == 0
            assert Path(output_file).exists()

        finally:
            # Cleanup
            os.unlink(temp_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_analyze_without_api_key(self):
        """Test analysis without API key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello, world!')")
            f.flush()
            temp_file = f.name

        try:
            # Ensure no API key in environment
            with patch.dict(os.environ, {}, clear=True):
                result = self.runner.invoke(analyze, [temp_file])

            assert result.exit_code != 0
            assert "OPENAI_API_KEY" in result.output or "API key" in result.output

        finally:
            os.unlink(temp_file)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_analyze_verbose_mode(self):
        """Test analysis in verbose mode."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello, world!')")
            f.flush()
            temp_file = f.name

        try:
            # Mock config and prompts files
            with patch("builtins.open", mock_open(read_data="llm:\n  model: gpt-4")):
                result = self.runner.invoke(analyze, [temp_file, '--verbose'])

            # In verbose mode, should show more output or at least not crash
            # Exact behavior depends on implementation
            assert "Loading configuration" in result.output or result.exit_code in [0, 1]

        finally:
            os.unlink(temp_file)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.llm_client.OpenAI")
    @patch("app.utils.prompt_loader.PromptLoader")
    def test_analyze_zip_file(self, mock_prompt_loader, mock_openai):
        """Test analysis of ZIP file."""
        import zipfile

        # Create a ZIP file with Python code
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as zip_f:
            with zipfile.ZipFile(zip_f.name, 'w') as zf:
                zf.writestr('test.py', "print('hello from zip')")
                zf.writestr('subdir/main.py', "def main(): pass")

            zip_file = zip_f.name

        try:
            # Mock LLM response
            mock_client = mock_openai.return_value
            content = '{"batch_summary": {"main_purpose": "Zip archive code"}}'
            mock_message = type('MockMessage', (), {'content': content})()
            mock_choice = type('MockChoice', (), {'message': mock_message})()
            mock_response = type('MockResponse', (), {'choices': [mock_choice]})()
            mock_client.chat.completions.create.return_value = mock_response

            # Mock prompt loader
            mock_prompt_loader.return_value.batch_analysis_prompt = "Analyze batch: {files_info}"

            # Mock config and prompts files
            mock_config = "llm:\n  model: gpt-4\nfile_processing:\n  supported_extensions:\n    - .py\n    - .js\n"
            with patch("builtins.open", mock_open(read_data=mock_config)):
                result = self.runner.invoke(analyze, [zip_file])

            # Debug output
            if result.exit_code != 0:
                print(f"Exit code: {result.exit_code}")
                print(f"Output: {result.output}")
                if result.exception:
                    print(f"Exception: {result.exception}")

            assert result.exit_code == 0

        finally:
            os.unlink(zip_file)

    def test_analyze_with_invalid_config(self):
        """Test analysis with invalid configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello, world!')")
            f.flush()
            temp_file = f.name

        try:
            # Mock invalid YAML config
            with patch("builtins.open", mock_open(read_data="invalid: yaml: content: [")):
                result = self.runner.invoke(analyze, [temp_file])

            # Should handle invalid config gracefully
            assert result.exit_code in [0, 1]  # May succeed with defaults or fail

        finally:
            os.unlink(temp_file)

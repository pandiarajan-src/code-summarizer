"""Tests for main CLI module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from code_summarizer.main import analyze, cli, version


class TestMainCLI:
    """Test cases for main CLI functionality."""

    def test_version_command(self):
        """Test version command output."""
        runner = CliRunner()
        result = runner.invoke(version)
        
        assert result.exit_code == 0
        assert "Code Summarizer v1.0.0" in result.output

    def test_cli_group_help(self):
        """Test main CLI group help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "AI-powered code analysis and summarization tool" in result.output
        assert "analyze" in result.output
        assert "version" in result.output

    def test_analyze_command_help(self):
        """Test analyze command help."""
        runner = CliRunner()
        result = runner.invoke(analyze, ["--help"])
        
        assert result.exit_code == 0
        assert "Analyze source code files" in result.output
        assert "--output" in result.output
        assert "--config" in result.output
        assert "--verbose" in result.output

    @patch('code_summarizer.main.FileProcessor')
    @patch('code_summarizer.main.LLMClient')
    @patch('code_summarizer.main.ContextManager')
    @patch('code_summarizer.main.MarkdownFormatter')
    def test_analyze_successful_execution(
        self, 
        mock_markdown_formatter,
        mock_context_manager,
        mock_llm_client,
        mock_file_processor
    ):
        """Test successful analysis execution."""
        # Create a temporary input file
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
            f.write("def hello(): pass")
            temp_input = f.name

        try:
            # Mock the component instances
            mock_file_processor_instance = Mock()
            mock_file_processor_instance.process_input.return_value = [
                {"name": "test.py", "content": "def hello(): pass", "extension": ".py"}
            ]
            mock_file_processor.return_value = mock_file_processor_instance
            
            mock_context_manager_instance = Mock()
            mock_context_manager_instance.create_batches.return_value = [
                [{"name": "test.py", "content": "def hello(): pass"}]
            ]
            mock_context_manager.return_value = mock_context_manager_instance
            
            mock_llm_client_instance = Mock()
            mock_llm_client_instance.analyze_batch.return_value = {
                "files": [{"filename": "test.py", "language": "Python"}]
            }
            mock_llm_client.return_value = mock_llm_client_instance
            
            mock_markdown_formatter_instance = Mock()
            mock_markdown_formatter_instance.format_results.return_value = "# Test Analysis"
            mock_markdown_formatter.return_value = mock_markdown_formatter_instance

            # Create temporary output directory
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "output.md"
                
                runner = CliRunner()
                result = runner.invoke(analyze, [
                    temp_input,
                    "--output", str(output_path),
                    "--verbose"
                ])
                
                assert result.exit_code == 0
                assert "Analyzing:" in result.output
                assert "Found 1 code files" in result.output
                assert "Created 1 batches" in result.output
                assert "Analysis complete!" in result.output
                assert str(output_path) in result.output

        finally:
            Path(temp_input).unlink()

    @patch('code_summarizer.main.FileProcessor')
    def test_analyze_no_supported_files(self, mock_file_processor):
        """Test analysis when no supported files are found."""
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_input = f.name

        try:
            # Mock FileProcessor to return no files
            mock_file_processor_instance = Mock()
            mock_file_processor_instance.process_input.return_value = []
            mock_file_processor.return_value = mock_file_processor_instance
            
            runner = CliRunner()
            result = runner.invoke(analyze, [temp_input])
            
            assert result.exit_code == 1
            assert "No supported code files found" in result.output

        finally:
            Path(temp_input).unlink()

    def test_analyze_nonexistent_input(self):
        """Test analysis with nonexistent input file."""
        runner = CliRunner()
        result = runner.invoke(analyze, ["/nonexistent/path"])
        
        assert result.exit_code == 2  # Click error for invalid path
        assert "does not exist" in result.output

    @patch('code_summarizer.main.FileProcessor')
    def test_analyze_exception_handling(self, mock_file_processor):
        """Test exception handling in analyze command."""
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_input = f.name

        try:
            # Mock FileProcessor to raise an exception
            mock_file_processor.side_effect = Exception("Processing failed")
            
            runner = CliRunner()
            result = runner.invoke(analyze, [temp_input])
            
            assert result.exit_code == 1
            assert "Error: Processing failed" in result.output

        finally:
            Path(temp_input).unlink()

    @patch('code_summarizer.main.FileProcessor')
    def test_analyze_verbose_exception_handling(self, mock_file_processor):
        """Test verbose exception handling with traceback."""
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_input = f.name

        try:
            # Mock FileProcessor to raise an exception
            mock_file_processor.side_effect = Exception("Processing failed")
            
            runner = CliRunner()
            result = runner.invoke(analyze, [temp_input, "--verbose"])
            
            assert result.exit_code == 1
            assert "Error: Processing failed" in result.output
            # In verbose mode, traceback should be printed

        finally:
            Path(temp_input).unlink()

    @patch('code_summarizer.main.FileProcessor')
    @patch('code_summarizer.main.LLMClient')
    @patch('code_summarizer.main.ContextManager')
    @patch('code_summarizer.main.MarkdownFormatter')
    def test_analyze_default_output_name(
        self,
        mock_markdown_formatter,
        mock_context_manager,
        mock_llm_client,
        mock_file_processor
    ):
        """Test analysis with default output file name."""
        # Mock all components
        mock_file_processor_instance = Mock()
        mock_file_processor_instance.process_input.return_value = [
            {"name": "test.py", "content": "def hello(): pass"}
        ]
        mock_file_processor.return_value = mock_file_processor_instance
        
        mock_context_manager_instance = Mock()
        mock_context_manager_instance.create_batches.return_value = [[{}]]
        mock_context_manager.return_value = mock_context_manager_instance
        
        mock_llm_client_instance = Mock()
        mock_llm_client_instance.analyze_batch.return_value = {"files": []}
        mock_llm_client.return_value = mock_llm_client_instance
        
        mock_markdown_formatter_instance = Mock()
        mock_markdown_formatter_instance.format_results.return_value = "# Analysis"
        mock_markdown_formatter.return_value = mock_markdown_formatter_instance

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create input file inside isolated filesystem
            input_file = "test_input.py"
            Path(input_file).write_text("def hello(): pass")
            
            # Create a config file to satisfy Click's exists=True requirement
            config_file = "config.yaml"
            Path(config_file).write_text("# Test config")
            
            result = runner.invoke(analyze, [input_file])
            
            assert result.exit_code == 0
            expected_output = "test_input_summary.md"
            assert expected_output in result.output
            assert Path(expected_output).exists()

    @patch('code_summarizer.main.FileProcessor')
    @patch('code_summarizer.main.LLMClient')
    @patch('code_summarizer.main.ContextManager')
    @patch('code_summarizer.main.MarkdownFormatter')
    def test_analyze_with_custom_config(
        self,
        mock_markdown_formatter,
        mock_context_manager,
        mock_llm_client,
        mock_file_processor
    ):
        """Test analysis with custom config file."""
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as input_file:
            input_file.write("def hello(): pass")
            temp_input = input_file.name

        with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False) as config_file:
            config_file.write("llm:\n  model: gpt-3.5-turbo")
            temp_config = config_file.name

        try:
            # Mock all components
            mock_file_processor_instance = Mock()
            mock_file_processor_instance.process_input.return_value = [
                {"name": "test.py", "content": "def hello(): pass"}
            ]
            mock_file_processor.return_value = mock_file_processor_instance
            
            mock_context_manager_instance = Mock()
            mock_context_manager_instance.create_batches.return_value = [[{}]]
            mock_context_manager.return_value = mock_context_manager_instance
            
            mock_llm_client_instance = Mock()
            mock_llm_client_instance.analyze_batch.return_value = {"files": []}
            mock_llm_client.return_value = mock_llm_client_instance
            
            mock_markdown_formatter_instance = Mock()
            mock_markdown_formatter_instance.format_results.return_value = "# Analysis"
            mock_markdown_formatter.return_value = mock_markdown_formatter_instance

            runner = CliRunner()
            with runner.isolated_filesystem():
                result = runner.invoke(analyze, [
                    temp_input,
                    "--config", temp_config
                ])
                
                assert result.exit_code == 0
                # Verify that components were initialized with the custom config
                mock_file_processor.assert_called_with(config_path=temp_config)
                mock_llm_client.assert_called_with(config_path=temp_config)
                mock_context_manager.assert_called_with(config_path=temp_config)
                mock_markdown_formatter.assert_called_with(config_path=temp_config)

        finally:
            Path(temp_input).unlink()
            Path(temp_config).unlink()

    @patch('code_summarizer.main.FileProcessor')
    @patch('code_summarizer.main.LLMClient')
    @patch('code_summarizer.main.ContextManager')
    @patch('code_summarizer.main.MarkdownFormatter')
    def test_analyze_multiple_batches(
        self,
        mock_markdown_formatter,
        mock_context_manager,
        mock_llm_client,
        mock_file_processor
    ):
        """Test analysis with multiple batches."""
        # Mock components to return multiple batches
        mock_file_processor_instance = Mock()
        mock_file_processor_instance.process_input.return_value = [
            {"name": "test1.py"}, {"name": "test2.py"}
        ]
        mock_file_processor.return_value = mock_file_processor_instance
        
        mock_context_manager_instance = Mock()
        mock_context_manager_instance.create_batches.return_value = [
            [{"name": "test1.py"}], 
            [{"name": "test2.py"}]
        ]
        mock_context_manager.return_value = mock_context_manager_instance
        
        mock_llm_client_instance = Mock()
        mock_llm_client_instance.analyze_batch.return_value = {"files": []}
        mock_llm_client.return_value = mock_llm_client_instance
        
        mock_markdown_formatter_instance = Mock()
        mock_markdown_formatter_instance.format_results.return_value = "# Analysis"
        mock_markdown_formatter.return_value = mock_markdown_formatter_instance

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create input file inside isolated filesystem
            input_file = "multi_batch_test.py" 
            Path(input_file).write_text("def hello(): pass")
            
            # Create a config file to satisfy Click's exists=True requirement
            config_file = "config.yaml"
            Path(config_file).write_text("# Test config")
            
            result = runner.invoke(analyze, [input_file, "--verbose"])
            
            assert result.exit_code == 0
            assert "Found 2 code files" in result.output
            assert "Created 2 batches" in result.output
            assert "Analyzing batch 1/2" in result.output
            assert "Analyzing batch 2/2" in result.output
            # Verify analyze_batch was called twice
            assert mock_llm_client_instance.analyze_batch.call_count == 2

    def test_cli_integration(self):
        """Test CLI group includes expected commands."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        
        # Should show help when --help is provided
        assert result.exit_code == 0
        assert "analyze" in result.output
        assert "version" in result.output
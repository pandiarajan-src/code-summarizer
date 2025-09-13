"""Tests for context_manager module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from code_summarizer.context_manager import ContextManager


class TestContextManager:
    """Test cases for ContextManager class."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        with patch("code_summarizer.context_manager.Path") as mock_path:
            mock_path.return_value.open.side_effect = FileNotFoundError
            cm = ContextManager()
            
            assert cm.config == {}
            assert cm.model_name == "gpt-4o"
            assert cm.max_context_tokens == 128000

    def test_init_with_config_file(self):
        """Test initialization with custom config file."""
        config_data = {
            "llm": {
                "model": "gpt-3.5-turbo",
                "max_context_tokens": 4096,
                "max_tokens": 1000
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            cm = ContextManager(config_path=config_path)
            assert cm.model_name == "gpt-3.5-turbo"
            assert cm.max_context_tokens == 4096
            assert cm.response_tokens == 1000
        finally:
            Path(config_path).unlink()

    def test_count_tokens_success(self):
        """Test token counting with successful encoding."""
        cm = ContextManager()
        
        # Mock the tokenizer
        mock_tokenizer = Mock()
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        cm.tokenizer = mock_tokenizer
        
        result = cm.count_tokens("test text")
        assert result == 5
        mock_tokenizer.encode.assert_called_once_with("test text")

    def test_count_tokens_fallback(self):
        """Test token counting with fallback estimation."""
        cm = ContextManager()
        
        # Mock the tokenizer to raise an exception
        mock_tokenizer = Mock()
        mock_tokenizer.encode.side_effect = Exception("Encoding failed")
        cm.tokenizer = mock_tokenizer
        
        test_text = "test text that is 20 chars"
        result = cm.count_tokens(test_text)
        expected_tokens = len(test_text) // 4  # Fallback estimation: chars / 4
        assert result == expected_tokens

    def test_estimate_file_tokens(self):
        """Test file token estimation."""
        cm = ContextManager()
        
        with patch.object(cm, 'count_tokens') as mock_count:
            mock_count.side_effect = [100, 50]  # content tokens, metadata tokens
            
            file_data = {
                "name": "test.py",
                "path": "/path/to/test.py",
                "lines": 10,
                "content": "def test(): pass"
            }
            
            result = cm.estimate_file_tokens(file_data)
            assert result == 150
            assert mock_count.call_count == 2

    def test_create_batches_empty_input(self):
        """Test batching with empty file list."""
        cm = ContextManager()
        result = cm.create_batches([])
        assert result == []

    def test_create_batches_single_file(self):
        """Test batching with single file that fits."""
        cm = ContextManager()
        cm.available_tokens = 1000
        
        file_data = {
            "name": "test.py",
            "path": "/test.py",
            "content": "print('hello')",
            "lines": 1
        }
        
        with patch.object(cm, 'estimate_file_tokens', return_value=500):
            result = cm.create_batches([file_data])
            
            assert len(result) == 1
            assert len(result[0]) == 1
            assert result[0][0] == file_data

    def test_create_batches_multiple_files(self):
        """Test batching with multiple files."""
        cm = ContextManager()
        cm.available_tokens = 1000
        
        files = [
            {"name": "file1.py", "content": "code1", "lines": 5},
            {"name": "file2.py", "content": "code2", "lines": 3},
            {"name": "file3.py", "content": "code3", "lines": 7}
        ]
        
        # Mock token estimation: file1=600, file2=300, file3=500
        token_estimates = [600, 300, 500]
        with patch.object(cm, 'estimate_file_tokens', side_effect=token_estimates):
            result = cm.create_batches(files)
            
            # Should create 2 batches: [file1], [file2, file3]
            assert len(result) == 2
            assert len(result[0]) == 1  # file1 alone
            assert len(result[1]) == 2  # file2 + file3

    def test_create_batches_oversized_file(self):
        """Test batching with file that exceeds token limit."""
        cm = ContextManager()
        cm.available_tokens = 1000
        
        file_data = {
            "name": "large.py",
            "path": "/large.py",
            "content": "x" * 2000,
            "lines": 100,
            "size": 2000
        }
        
        with patch.object(cm, 'estimate_file_tokens', return_value=1500):
            with patch.object(cm, '_truncate_file_content') as mock_truncate:
                mock_truncate.return_value = {"name": "large.py", "truncated": True}
                
                result = cm.create_batches([file_data])
                
                assert len(result) == 1
                assert len(result[0]) == 1
                mock_truncate.assert_called_once_with(file_data, 1000)

    def test_truncate_file_content(self):
        """Test file content truncation."""
        cm = ContextManager()
        
        file_data = {
            "name": "test.py",
            "content": "line1\nline2\nline3\nline4\nline5",
            "lines": 5
        }
        
        # Mock token counting to simulate truncation
        def mock_count_tokens(text):
            if "truncated" in text:
                return 50
            return len(text.split('\n')) * 10
        
        with patch.object(cm, 'count_tokens', side_effect=mock_count_tokens):
            result = cm._truncate_file_content(file_data, 300)
            
            assert result["truncated"] is True
            assert result["original_lines"] == 5
            assert "truncated due to size limits" in result["content"]

    def test_get_batch_info(self):
        """Test batch information extraction."""
        cm = ContextManager()
        
        batch = [
            {"name": "test1.py", "extension": ".py", "lines": 10, "size": 100},
            {"name": "test2.js", "extension": ".js", "lines": 5, "size": 50}
        ]
        
        with patch.object(cm, 'estimate_file_tokens', side_effect=[200, 100]):
            result = cm.get_batch_info(batch)
            
            assert result["total_files"] == 2
            assert result["total_tokens"] == 300
            assert result["total_lines"] == 15
            assert "Python" in result["languages"]
            assert "JavaScript" in result["languages"]

    def test_extension_to_language(self):
        """Test file extension to language mapping."""
        cm = ContextManager()
        
        assert cm._extension_to_language(".py") == "Python"
        assert cm._extension_to_language(".js") == "JavaScript"
        assert cm._extension_to_language(".unknown") == "Unknown"

    def test_optimize_batching_strategy(self):
        """Test batching strategy optimization."""
        cm = ContextManager()
        cm.available_tokens = 1000
        
        # Test single_batch strategy
        small_files = [{"size": 100} for _ in range(3)]
        with patch.object(cm, 'estimate_file_tokens', return_value=200):
            result = cm.optimize_batching_strategy(small_files)
            assert result == "single_batch"
        
        # Test file_by_file strategy
        medium_files = [{"size": 100} for _ in range(5)]
        with patch.object(cm, 'estimate_file_tokens', return_value=300):
            result = cm.optimize_batching_strategy(medium_files)
            assert result == "file_by_file"
        
        # Test smart_batching strategy
        large_files = [{"size": 100} for _ in range(15)]
        with patch.object(cm, 'estimate_file_tokens', return_value=200):
            result = cm.optimize_batching_strategy(large_files)
            assert result == "smart_batching"
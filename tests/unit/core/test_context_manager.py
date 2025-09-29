from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest
from app.core.context_manager import ContextManager


class TestContextManager:
    """Test context manager functionality."""

    @pytest.fixture(autouse=True)
    def setup_mock_tiktoken(self):
        """Setup mock tiktoken for all tests."""
        mock_tokenizer = MagicMock()

        def mock_encode(text):
            # Return empty list for empty string, otherwise return some tokens
            return [] if not text else [1, 2, 3, 4]

        mock_tokenizer.encode.side_effect = mock_encode
        with patch("tiktoken.encoding_for_model", return_value=mock_tokenizer):
            yield

    @patch(
        "pathlib.Path.open",
        mock_open(read_data="llm:\n  model: gpt-4\n  max_context_tokens: 8000"),
    )
    def test_init_with_config(self):
        """Test initialization with configuration file."""
        cm = ContextManager("test_config.yaml")

        assert cm.model_name == "gpt-4"
        assert cm.max_context_tokens == 8000

    @patch("pathlib.Path.open", side_effect=FileNotFoundError)
    def test_init_without_config(self, mock_open):
        """Test initialization without configuration file."""
        cm = ContextManager("nonexistent.yaml")

        assert cm.model_name == "gpt-4o"
        assert cm.max_context_tokens == 128000

    def test_count_tokens(self):
        """Test token counting functionality."""
        cm = ContextManager()

        # Test with simple text
        tokens = cm.count_tokens("Hello world")
        assert isinstance(tokens, int)
        assert tokens == 4  # Based on our mock

        # Test with empty text
        tokens = cm.count_tokens("")
        assert tokens == 0

    def test_estimate_file_tokens(self):
        """Test file token estimation."""
        cm = ContextManager()

        file_data = {
            "name": "test.py",
            "path": "/path/to/test.py",
            "content": "print('Hello, world!')",
            "lines": 1,
        }

        tokens = cm.estimate_file_tokens(file_data)
        assert isinstance(tokens, int)
        assert tokens > 0

    def test_create_batches_empty_input(self):
        """Test batch creation with empty input."""
        cm = ContextManager()
        batches = cm.create_batches([])
        assert batches == []

    def test_create_batches_single_file(self):
        """Test batch creation with single file."""
        cm = ContextManager()

        file_data = {
            "name": "test.py",
            "path": "/path/to/test.py",
            "content": "print('Hello, world!')",
            "lines": 1,
            "size": 100,
            "extension": ".py",
        }

        batches = cm.create_batches([file_data])
        assert len(batches) == 1
        assert len(batches[0]) == 1
        assert batches[0][0] == file_data

    def test_create_batches_multiple_files(self):
        """Test batch creation with multiple files."""
        cm = ContextManager()

        files_data = [
            {
                "name": f"test{i}.py",
                "path": f"/path/to/test{i}.py",
                "content": f"print('Hello, world {i}!')",
                "lines": 1,
                "size": 100,
                "extension": ".py",
            }
            for i in range(5)
        ]

        batches = cm.create_batches(files_data)
        assert len(batches) >= 1
        assert sum(len(batch) for batch in batches) == 5

    def test_truncate_file_content(self):
        """Test file content truncation."""
        cm = ContextManager()

        large_content = "\n".join([f"Line {i}" for i in range(1000)])
        file_data = {
            "name": "large_file.py",
            "path": "/path/to/large_file.py",
            "content": large_content,
            "lines": 1000,
            "size": len(large_content),
            "extension": ".py",
        }

        truncated = cm._truncate_file_content(file_data, 1000)

        assert truncated["truncated"] is True
        assert truncated["original_lines"] == 1000
        assert truncated["truncated_lines"] < 1000
        assert "[... Content truncated due to size limits ...]" in truncated["content"]

    def test_get_batch_info(self):
        """Test batch information retrieval."""
        cm = ContextManager()

        batch = [
            {
                "name": "test1.py",
                "path": "/path/to/test1.py",
                "content": "print('Hello')",
                "lines": 1,
                "size": 100,
                "extension": ".py",
            },
            {
                "name": "test2.js",
                "path": "/path/to/test2.js",
                "content": "console.log('Hello')",
                "lines": 1,
                "size": 120,
                "extension": ".js",
            },
        ]

        info = cm.get_batch_info(batch)

        assert info["total_files"] == 2
        assert info["total_lines"] == 2
        assert info["total_tokens"] > 0
        assert "Python" in info["languages"]
        assert "JavaScript" in info["languages"]
        assert len(info["files"]) == 2

    def test_extension_to_language(self):
        """Test extension to language mapping."""
        cm = ContextManager()

        assert cm._extension_to_language(".py") == "Python"
        assert cm._extension_to_language(".js") == "JavaScript"
        assert cm._extension_to_language(".ts") == "TypeScript"
        assert cm._extension_to_language(".java") == "Java"
        assert cm._extension_to_language(".unknown") == "Unknown"

    def test_optimize_batching_strategy(self):
        """Test batching strategy optimization."""
        cm = ContextManager()

        # Small dataset
        small_files = [
            {
                "name": "test.py",
                "path": "/path/to/test.py",
                "content": "print('Hello')",
                "lines": 1,
                "size": 100,
                "extension": ".py",
            }
        ]

        strategy = cm.optimize_batching_strategy(small_files)
        assert strategy in ["single_batch", "file_by_file", "smart_batching"]

        # Large dataset
        large_files = [
            {
                "name": f"test{i}.py",
                "path": f"/path/to/test{i}.py",
                "content": f"print('Hello {i}')",
                "lines": 1,
                "size": 100,
                "extension": ".py",
            }
            for i in range(20)
        ]

        strategy = cm.optimize_batching_strategy(large_files)
        assert strategy in ["single_batch", "file_by_file", "smart_batching"]

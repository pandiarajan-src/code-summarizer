"""Tests for file_processor module."""

import os
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
import yaml

from code_summarizer.file_processor import FileProcessor


class TestFileProcessor:
    """Test cases for FileProcessor class."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        with patch("code_summarizer.file_processor.Path") as mock_path:
            mock_path.return_value.open.side_effect = FileNotFoundError
            fp = FileProcessor()
            
            assert fp.config == {}
            assert fp.supported_extensions == []
            assert fp.exclude_patterns == []

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config_data = {
            "file_processing": {
                "supported_extensions": [".py", ".js"],
                "exclude_patterns": ["*/node_modules/*", "*/__pycache__/*"]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            fp = FileProcessor(config_path=config_path)
            assert fp.supported_extensions == [".py", ".js"]
            assert fp.exclude_patterns == ["*/node_modules/*", "*/__pycache__/*"]
        finally:
            Path(config_path).unlink()

    def test_is_supported_file(self):
        """Test file extension support checking."""
        fp = FileProcessor()
        fp.supported_extensions = [".py", ".js", ".ts"]
        
        assert fp._is_supported_file("test.py") is True
        assert fp._is_supported_file("test.JS") is True  # Case insensitive
        assert fp._is_supported_file("test.txt") is False

    def test_should_exclude(self):
        """Test file exclusion pattern matching."""
        fp = FileProcessor()
        fp.exclude_patterns = ["*/node_modules/*", "*/__pycache__/*"]
        
        assert fp._should_exclude("/path/node_modules/file.js") is True
        assert fp._should_exclude("/path/__pycache__/file.pyc") is True
        assert fp._should_exclude("/path/src/file.py") is False

    def test_read_file_content_success(self):
        """Test successful file content reading."""
        fp = FileProcessor()
        content = "def hello():\n    print('world')"
        
        with patch("code_summarizer.file_processor.Path") as mock_path:
            mock_file = mock_open(read_data=content)
            mock_path.return_value.open = mock_file
            
            result = fp._read_file_content("test.py")
            assert result == content

    def test_read_file_content_encoding_fallback(self):
        """Test file reading with encoding fallback."""
        fp = FileProcessor()
        
        with patch("code_summarizer.file_processor.Path") as mock_path:
            # First encoding fails, second succeeds
            mock_file = mock_open(read_data="content")
            mock_file.side_effect = [UnicodeDecodeError("utf-8", b"", 0, 1, "error"), mock_file.return_value]
            mock_path.return_value.open = mock_file
            
            result = fp._read_file_content("test.py")
            assert result == "content"

    def test_read_file_content_binary_fallback(self):
        """Test file reading with binary fallback."""
        fp = FileProcessor()
        binary_content = b"binary content"
        
        with patch("code_summarizer.file_processor.Path") as mock_path:
            # Create context managers that raise UnicodeDecodeError
            def create_text_error_cm():
                cm = Mock()
                cm.__enter__ = Mock(side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "error"))
                cm.__exit__ = Mock(return_value=False)
                return cm
            
            # Binary mock that succeeds
            binary_mock = mock_open(read_data=binary_content)
            
            mock_path.return_value.open.side_effect = [
                create_text_error_cm(),  # UTF-8 failure
                create_text_error_cm(),  # Latin-1 failure  
                create_text_error_cm(),  # CP1252 failure
                binary_mock.return_value  # Binary success
            ]
            
            result = fp._read_file_content("test.py")
            assert result == "binary content"

    def test_extract_zip_success(self):
        """Test successful zip file extraction."""
        fp = FileProcessor()
        
        # Create a temporary zip file
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "test.zip")
            with zipfile.ZipFile(zip_path, 'w') as zip_file:
                zip_file.writestr("test.py", "print('hello')")
            
            result_dir = fp._extract_zip(zip_path)
            
            try:
                assert os.path.isdir(result_dir)
                assert os.path.exists(os.path.join(result_dir, "test.py"))
            finally:
                # Cleanup
                import shutil
                shutil.rmtree(result_dir, ignore_errors=True)

    def test_extract_zip_failure(self):
        """Test zip extraction failure."""
        fp = FileProcessor()
        
        with pytest.raises(Exception, match="Failed to extract zip file"):
            fp._extract_zip("nonexistent.zip")

    def test_scan_directory(self):
        """Test directory scanning for code files."""
        fp = FileProcessor()
        fp.supported_extensions = [".py", ".js"]
        fp.exclude_patterns = ["*/__pycache__/*"]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            py_file = os.path.join(temp_dir, "test.py")
            js_file = os.path.join(temp_dir, "script.js")
            txt_file = os.path.join(temp_dir, "readme.txt")
            
            # Create excluded directory
            pycache_dir = os.path.join(temp_dir, "__pycache__")
            os.makedirs(pycache_dir)
            pyc_file = os.path.join(pycache_dir, "test.pyc")
            
            for file_path in [py_file, js_file, txt_file, pyc_file]:
                Path(file_path).write_text("content")
            
            result = fp._scan_directory(temp_dir)
            
            # Should find .py and .js files, but not .txt or files in __pycache__
            result_names = [os.path.basename(f) for f in result]
            assert "test.py" in result_names
            assert "script.js" in result_names
            assert "readme.txt" not in result_names
            assert "test.pyc" not in result_names

    def test_create_file_data(self):
        """Test file data structure creation."""
        fp = FileProcessor()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test.py")
            content = "def hello():\n    return 'world'"
            Path(test_file).write_text(content)
            
            result = fp._create_file_data([test_file], temp_dir)
            
            assert len(result) == 1
            file_data = result[0]
            assert file_data["name"] == "test.py"
            assert file_data["path"] == "test.py"  # Relative to base_dir
            assert file_data["extension"] == ".py"
            assert file_data["content"] == content
            assert file_data["size"] == len(content)
            assert file_data["lines"] == 2

    def test_create_file_data_read_error(self):
        """Test file data creation with read error."""
        fp = FileProcessor()
        
        with patch.object(fp, '_read_file_content', side_effect=Exception("Read error")):
            with patch('builtins.print'):  # Suppress warning print
                result = fp._create_file_data(["/nonexistent/file.py"])
                assert result == []

    def test_process_input_single_file(self):
        """Test processing single code file."""
        fp = FileProcessor()
        fp.supported_extensions = [".py"]
        
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
            f.write("print('hello')")
            file_path = f.name
        
        try:
            with patch.object(fp, '_create_file_data', return_value=[{"name": "test.py"}]):
                result = fp.process_input(file_path)
                assert result == [{"name": "test.py"}]
        finally:
            os.unlink(file_path)

    def test_process_input_zip_file(self):
        """Test processing zip file."""
        fp = FileProcessor()
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            zip_path = f.name
        
        try:
            with patch.object(fp, '_process_zip_file', return_value=[{"name": "from_zip.py"}]):
                result = fp.process_input(zip_path)
                assert result == [{"name": "from_zip.py"}]
        finally:
            os.unlink(zip_path)

    def test_process_input_directory(self):
        """Test processing directory."""
        fp = FileProcessor()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(fp, '_scan_directory', return_value=["/path/file.py"]):
                with patch.object(fp, '_create_file_data', return_value=[{"name": "file.py"}]):
                    result = fp.process_input(temp_dir)
                    assert result == [{"name": "file.py"}]

    def test_process_input_unsupported_file(self):
        """Test processing unsupported file type."""
        fp = FileProcessor()
        fp.supported_extensions = [".py"]
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            file_path = f.name
        
        try:
            with pytest.raises(Exception, match="Unsupported file type"):
                fp.process_input(file_path)
        finally:
            os.unlink(file_path)

    def test_process_input_nonexistent(self):
        """Test processing nonexistent path."""
        fp = FileProcessor()
        
        with pytest.raises(Exception, match="Input path does not exist"):
            fp.process_input("/nonexistent/path")

    def test_get_project_info(self):
        """Test project information extraction."""
        fp = FileProcessor()
        
        files_data = [
            {"extension": ".py", "lines": 10, "size": 100},
            {"extension": ".js", "lines": 5, "size": 50},
            {"extension": ".py", "lines": 8, "size": 80}
        ]
        
        result = fp.get_project_info(files_data)
        
        assert result["total_files"] == 3
        assert result["total_lines"] == 23
        assert result["total_size"] == 230
        assert "Python" in result["languages"]
        assert "JavaScript" in result["languages"]
        assert result["file_types"]["Python"] == 2
        assert result["file_types"]["JavaScript"] == 1

    def test_get_project_info_empty(self):
        """Test project info with empty file list."""
        fp = FileProcessor()
        result = fp.get_project_info([])
        assert result == {}

    def test_extension_to_language(self):
        """Test file extension to language mapping."""
        fp = FileProcessor()
        
        assert fp._extension_to_language(".py") == "Python"
        assert fp._extension_to_language(".JS") == "JavaScript"  # Case insensitive
        assert fp._extension_to_language(".unknown") == "Unknown"
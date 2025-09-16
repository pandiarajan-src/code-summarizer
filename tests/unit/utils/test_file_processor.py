import os
import pytest
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch, mock_open
from app.utils.file_processor import FileProcessor


class TestFileProcessor:
    @patch("pathlib.Path.open", mock_open(read_data="file_processing:\n  supported_extensions: ['.py', '.js']\n  exclude_patterns: ['__pycache__']"))
    def test_init_with_config(self):
        """Test initialization with configuration file."""
        processor = FileProcessor("test_config.yaml")

        assert processor.supported_extensions == ['.py', '.js']
        assert processor.exclude_patterns == ['__pycache__']

    @patch("pathlib.Path.open", side_effect=FileNotFoundError)
    def test_init_without_config(self, mock_open):
        """Test initialization without configuration file."""
        processor = FileProcessor("nonexistent.yaml")

        assert processor.supported_extensions == []
        assert processor.exclude_patterns == []

    def test_is_supported_file(self):
        """Test supported file detection."""
        processor = FileProcessor.__new__(FileProcessor)
        processor.supported_extensions = ['.py', '.js', '.ts']

        assert processor._is_supported_file("test.py") is True
        assert processor._is_supported_file("test.JS") is True  # Case insensitive
        assert processor._is_supported_file("test.txt") is False

    def test_should_exclude(self):
        """Test exclude pattern matching."""
        processor = FileProcessor.__new__(FileProcessor)
        processor.exclude_patterns = ['__pycache__', '*.pyc', 'node_modules']

        assert processor._should_exclude("/path/__pycache__/file.py") is True
        assert processor._should_exclude("/path/file.pyc") is True
        assert processor._should_exclude("/path/node_modules/lib.js") is True
        assert processor._should_exclude("/path/src/main.py") is False

    @patch("pathlib.Path.open", mock_open(read_data="print('hello world')"))
    def test_read_file_content_utf8(self):
        """Test reading file content with UTF-8 encoding."""
        processor = FileProcessor.__new__(FileProcessor)

        content = processor._read_file_content("test.py")
        assert content == "print('hello world')"

    @patch("pathlib.Path.open")
    def test_read_file_content_encoding_fallback(self, mock_open_path):
        """Test reading file content with encoding fallback."""
        processor = FileProcessor.__new__(FileProcessor)

        # Mock first encoding to fail, second to succeed
        mock_open_path.side_effect = [
            UnicodeDecodeError("utf-8", b"", 0, 1, "invalid"),
            mock_open(read_data="content with special chars")()
        ]

        content = processor._read_file_content("test.py")
        assert content == "content with special chars"

    def test_extract_zip_success(self):
        """Test successful zip extraction."""
        # Create a temporary zip file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w') as zf:
                zf.writestr('test.py', 'print("hello")')

        processor = FileProcessor.__new__(FileProcessor)

        try:
            temp_dir = processor._extract_zip(temp_zip.name)
            assert os.path.exists(temp_dir)
            assert os.path.exists(os.path.join(temp_dir, 'test.py'))

            # Read extracted file
            with open(os.path.join(temp_dir, 'test.py')) as f:
                content = f.read()
            assert content == 'print("hello")'

        finally:
            # Cleanup
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            os.unlink(temp_zip.name)

    def test_extract_zip_failure(self):
        """Test zip extraction failure."""
        processor = FileProcessor.__new__(FileProcessor)

        with pytest.raises(Exception, match="Failed to extract zip file"):
            processor._extract_zip("nonexistent.zip")

    def test_scan_directory(self):
        """Test directory scanning for code files."""
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some files
            py_file = os.path.join(temp_dir, "test.py")
            js_file = os.path.join(temp_dir, "script.js")
            txt_file = os.path.join(temp_dir, "readme.txt")

            # Create subdirectory with files
            sub_dir = os.path.join(temp_dir, "src")
            os.makedirs(sub_dir)
            sub_py_file = os.path.join(sub_dir, "main.py")

            # Create excluded directory
            cache_dir = os.path.join(temp_dir, "__pycache__")
            os.makedirs(cache_dir)
            cache_file = os.path.join(cache_dir, "test.pyc")

            # Write files
            for file_path in [py_file, js_file, txt_file, sub_py_file, cache_file]:
                with open(file_path, 'w') as f:
                    f.write("test content")

            processor = FileProcessor.__new__(FileProcessor)
            processor.supported_extensions = ['.py', '.js']
            processor.exclude_patterns = ['__pycache__', '*.pyc']

            files = processor._scan_directory(temp_dir)

            # Should find .py and .js files but not .txt or files in __pycache__
            assert py_file in files
            assert js_file in files
            assert sub_py_file in files
            assert txt_file not in files
            assert cache_file not in files

    def test_create_file_data(self):
        """Test file data creation."""
        # Create temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            py_file = os.path.join(temp_dir, "test.py")
            content = "print('hello')\nprint('world')\n"

            with open(py_file, 'w') as f:
                f.write(content)

            processor = FileProcessor.__new__(FileProcessor)
            files_data = processor._create_file_data([py_file], temp_dir)

            assert len(files_data) == 1
            file_data = files_data[0]

            assert file_data["name"] == "test.py"
            assert file_data["extension"] == ".py"
            assert file_data["content"] == content
            assert file_data["size"] == len(content)
            assert file_data["lines"] == 2  # Two print lines
            assert file_data["path"] == "test.py"  # Relative path
            assert file_data["absolute_path"] == py_file

    def test_process_input_single_file(self):
        """Test processing single file input."""
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
            temp_file.write(b"print('hello')")
            temp_file.flush()

            processor = FileProcessor.__new__(FileProcessor)
            processor.supported_extensions = ['.py']
            processor.exclude_patterns = []

            try:
                files_data = processor.process_input(temp_file.name)

                assert len(files_data) == 1
                assert files_data[0]["name"] == os.path.basename(temp_file.name)
                assert files_data[0]["extension"] == ".py"
            finally:
                os.unlink(temp_file.name)

    def test_process_input_unsupported_file(self):
        """Test processing unsupported file type."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            processor = FileProcessor.__new__(FileProcessor)
            processor.supported_extensions = ['.py']

            try:
                with pytest.raises(Exception, match="Unsupported file type"):
                    processor.process_input(temp_file.name)
            finally:
                os.unlink(temp_file.name)

    def test_process_input_directory(self):
        """Test processing directory input."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Python file
            py_file = os.path.join(temp_dir, "test.py")
            with open(py_file, 'w') as f:
                f.write("print('hello')")

            processor = FileProcessor.__new__(FileProcessor)
            processor.supported_extensions = ['.py']
            processor.exclude_patterns = []

            files_data = processor.process_input(temp_dir)

            assert len(files_data) == 1
            assert files_data[0]["name"] == "test.py"

    def test_process_input_empty_directory(self):
        """Test processing empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            processor = FileProcessor.__new__(FileProcessor)
            processor.supported_extensions = ['.py']

            with pytest.raises(Exception, match="No supported code files found in directory"):
                processor.process_input(temp_dir)

    def test_process_input_nonexistent_path(self):
        """Test processing nonexistent path."""
        processor = FileProcessor.__new__(FileProcessor)

        with pytest.raises(Exception, match="Input path does not exist"):
            processor.process_input("/nonexistent/path")

    def test_process_zip_file(self):
        """Test processing zip file."""
        # Create temporary zip with Python file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w') as zf:
                zf.writestr('src/main.py', 'print("hello from zip")')
                zf.writestr('README.txt', 'This is a readme')

        processor = FileProcessor.__new__(FileProcessor)
        processor.supported_extensions = ['.py']
        processor.exclude_patterns = []

        try:
            files_data = processor._process_zip_file(temp_zip.name)

            assert len(files_data) == 1
            assert files_data[0]["name"] == "main.py"
            assert files_data[0]["content"] == 'print("hello from zip")'
            assert "src/main.py" in files_data[0]["path"]
        finally:
            os.unlink(temp_zip.name)

    def test_get_project_info(self):
        """Test project information extraction."""
        processor = FileProcessor.__new__(FileProcessor)

        files_data = [
            {
                "name": "main.py",
                "extension": ".py",
                "lines": 50,
                "size": 1000
            },
            {
                "name": "script.js",
                "extension": ".js",
                "lines": 30,
                "size": 800
            },
            {
                "name": "utils.py",
                "extension": ".py",
                "lines": 20,
                "size": 500
            }
        ]

        project_info = processor.get_project_info(files_data)

        assert project_info["total_files"] == 3
        assert project_info["total_lines"] == 100
        assert project_info["total_size"] == 2300
        assert "Python" in project_info["languages"]
        assert "JavaScript" in project_info["languages"]
        assert project_info["file_types"]["Python"] == 2
        assert project_info["file_types"]["JavaScript"] == 1

    def test_get_project_info_empty(self):
        """Test project info with empty files list."""
        processor = FileProcessor.__new__(FileProcessor)

        project_info = processor.get_project_info([])
        assert project_info == {}

    def test_extension_to_language(self):
        """Test extension to language mapping."""
        processor = FileProcessor.__new__(FileProcessor)

        assert processor._extension_to_language(".py") == "Python"
        assert processor._extension_to_language(".js") == "JavaScript"
        assert processor._extension_to_language(".ts") == "TypeScript"
        assert processor._extension_to_language(".java") == "Java"
        assert processor._extension_to_language(".unknown") == "Unknown"
        assert processor._extension_to_language(".PY") == "Python"  # Case insensitive
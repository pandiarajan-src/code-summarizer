"""File processing module for handling single files and zip archives."""

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import yaml


class FileProcessor:
    """Processes source code files and zip archives for analysis."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize file processor with configuration.

        Args:
            config_path: Path to configuration YAML file.
        """
        self.config = self._load_config(config_path)
        self.supported_extensions = self.config.get("file_processing", {}).get(
            "supported_extensions", []
        )
        self.exclude_patterns = self.config.get("file_processing", {}).get(
            "exclude_patterns", []
        )

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with Path(config_path).open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}

    def _is_supported_file(self, file_path: str) -> bool:
        """Check if file has supported extension."""
        return any(file_path.lower().endswith(ext) for ext in self.supported_extensions)

    def _should_exclude(self, file_path: str) -> bool:
        """Check if file matches exclude patterns."""
        for pattern in self.exclude_patterns:
            if pattern.replace("*", "") in file_path:
                return True
        return False

    def _read_file_content(self, file_path: str) -> str:
        """Read file content with encoding detection."""
        encodings = ["utf-8", "latin-1", "cp1252"]

        for encoding in encodings:
            try:
                with Path(file_path).open(encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        # If all encodings fail, read as binary and decode with errors='ignore'
        with Path(file_path).open("rb") as f:
            return f.read().decode("utf-8", errors="ignore")

    def _extract_zip(self, zip_path: str) -> str:
        """Extract zip file to temporary directory."""
        temp_dir = tempfile.mkdtemp(prefix="code_summarizer_")

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
            return temp_dir
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception(f"Failed to extract zip file: {str(e)}")

    def _scan_directory(self, directory: str) -> list[str]:
        """Recursively scan directory for supported code files."""
        code_files = []

        for root, dirs, files in os.walk(directory):
            # Skip excluded directories
            dirs[:] = [
                d
                for d in dirs
                if not any(
                    pattern.replace("*", "") in os.path.join(root, d)
                    for pattern in self.exclude_patterns
                )
            ]

            for file in files:
                file_path = os.path.join(root, file)

                if self._is_supported_file(file) and not self._should_exclude(
                    file_path
                ):
                    code_files.append(file_path)

        return code_files

    def _create_file_data(
        self, file_paths: list[str], base_dir: str | None = None
    ) -> list[dict[str, Any]]:
        """Create file data structures with content and metadata."""
        files_data = []

        for file_path in file_paths:
            try:
                content = self._read_file_content(file_path)

                # Calculate relative path if base_dir provided
                relative_path = file_path
                if base_dir:
                    relative_path = os.path.relpath(file_path, base_dir)

                file_info = {
                    "path": relative_path,
                    "absolute_path": file_path,
                    "name": os.path.basename(file_path),
                    "extension": Path(file_path).suffix,
                    "content": content,
                    "size": len(content),
                    "lines": len(content.splitlines()),
                }

                files_data.append(file_info)

            except Exception as e:
                print(f"Warning: Could not read file {file_path}: {str(e)}")
                continue

        return files_data

    def process_input(self, input_path: str) -> list[dict[str, Any]]:
        """Process input (single file or zip) and return file data.

        Returns:
            List of file data dictionaries.
        """
        input_path = os.path.abspath(input_path)

        # Handle single file
        if os.path.isfile(input_path):
            if input_path.lower().endswith(".zip"):
                return self._process_zip_file(input_path)
            if self._is_supported_file(input_path):
                return self._create_file_data([input_path])
            raise Exception(f"Unsupported file type: {Path(input_path).suffix}")

        # Handle directory
        if os.path.isdir(input_path):
            code_files = self._scan_directory(input_path)
            if not code_files:
                raise Exception("No supported code files found in directory")
            return self._create_file_data(code_files, input_path)

        raise Exception(f"Input path does not exist: {input_path}")

    def _process_zip_file(self, zip_path: str) -> list[dict[str, Any]]:
        """Process zip file and return file data."""
        temp_dir = None

        try:
            # Extract zip
            temp_dir = self._extract_zip(zip_path)

            # Find code files
            code_files = self._scan_directory(temp_dir)

            if not code_files:
                raise Exception("No supported code files found in zip archive")

            # Create file data
            files_data = self._create_file_data(code_files, temp_dir)

            return files_data

        finally:
            # Cleanup temporary directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def get_project_info(self, files_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract project-level information from file data."""
        if not files_data:
            return {}

        # Detect languages
        languages = set()
        for file_data in files_data:
            ext = file_data["extension"].lower()
            lang = self._extension_to_language(ext)
            if lang:
                languages.add(lang)

        # Calculate totals
        total_files = len(files_data)
        total_lines = sum(file_data["lines"] for file_data in files_data)
        total_size = sum(file_data["size"] for file_data in files_data)

        return {
            "languages": sorted(list(languages)),
            "total_files": total_files,
            "total_lines": total_lines,
            "total_size": total_size,
            "file_types": {
                lang: len(
                    [
                        f
                        for f in files_data
                        if self._extension_to_language(f["extension"]) == lang
                    ]
                )
                for lang in languages
            },
        }

    def _extension_to_language(self, extension: str) -> str:
        """Map file extension to programming language."""
        ext_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "JavaScript (React)",
            ".tsx": "TypeScript (React)",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
            ".h": "C/C++",
            ".hpp": "C++",
            ".cs": "C#",
            ".swift": "Swift",
            ".go": "Go",
            ".rs": "Rust",
            ".php": "PHP",
            ".rb": "Ruby",
            ".scala": "Scala",
            ".kt": "Kotlin",
            ".dart": "Dart",
            ".r": "R",
            ".m": "Objective-C",
            ".mm": "Objective-C++",
            ".sh": "Shell",
            ".sql": "SQL",
        }

        return ext_map.get(extension.lower(), "Unknown")

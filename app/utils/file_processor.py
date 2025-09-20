"""File processing module for handling single files and zip archives."""

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

import aiofiles

if TYPE_CHECKING:
    from app.core.config import Settings


class FileProcessor:
    """Processes source code files and zip archives for analysis."""

    def __init__(
        self, config_path: str | None = None, *, settings: "Settings | None" = None
    ) -> None:
        """Initialize file processor with configuration.

        Args:
            config_path: Legacy config path for backward compatibility
                (positional for backward compat)
            settings: Pydantic Settings object (preferred, keyword-only)
        """
        if settings:
            self.supported_extensions = settings.allowed_file_types
            self.exclude_patterns = settings.exclude_patterns
        elif config_path:
            # Legacy support
            self.config = self._load_legacy_config(config_path)
            self.supported_extensions = self.config.get("file_processing", {}).get(
                "supported_extensions", []
            )
            self.exclude_patterns = self.config.get("file_processing", {}).get(
                "exclude_patterns", []
            )
        else:
            # Use defaults from Settings if no config provided
            from app.core.config import settings as default_settings

            self.supported_extensions = default_settings.allowed_file_types
            self.exclude_patterns = default_settings.exclude_patterns

    def _load_legacy_config(self, config_path: str) -> dict[str, Any]:
        """Load configuration from YAML file (legacy support)."""
        try:
            import yaml

            with Path(config_path).open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}

    def _is_supported_file(self, file_path: str) -> bool:
        """Check if file has supported extension."""
        return any(file_path.lower().endswith(ext) for ext in self.supported_extensions)

    def _should_exclude(self, file_path: str, base_dir: str | None = None) -> bool:
        """Check if file matches exclude patterns.

        Args:
            file_path: Path to check
            base_dir: Base directory for relative path calculation (optional)
        """
        path_obj = Path(file_path)

        # If we have a base directory, work with relative path for exclusion checks
        if base_dir:
            try:
                rel_path = path_obj.relative_to(Path(base_dir))
                check_path = str(rel_path)
                check_parts = rel_path.parts
            except ValueError:
                # If file is not relative to base_dir, use absolute path
                check_path = str(path_obj)
                check_parts = path_obj.parts
        else:
            check_path = str(path_obj)
            check_parts = path_obj.parts

        for pattern in self.exclude_patterns:
            # Handle wildcard patterns (like *.pyc)
            if pattern.startswith("*"):
                if path_obj.name.endswith(pattern[1:]):
                    return True
            # Handle directory patterns
            else:
                # Check if pattern matches filename exactly
                if pattern == path_obj.name:
                    return True

                # Check if pattern matches any directory in the (relative) path
                if pattern in check_parts:
                    return True

        return False

    def _read_file_content(self, file_path: str) -> str:
        """Read file content with encoding detection (sync version for backward compatibility)."""
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

    async def _read_file_content_async(self, file_path: str) -> str:
        """Read file content with encoding detection using async I/O."""
        encodings = ["utf-8", "latin-1", "cp1252"]

        for encoding in encodings:
            try:
                async with aiofiles.open(file_path, encoding=encoding) as f:
                    return await f.read()
            except UnicodeDecodeError:
                continue

        # If all encodings fail, read as binary and decode with errors='ignore'
        async with aiofiles.open(file_path, "rb") as f:
            content = await f.read()
            return content.decode("utf-8", errors="ignore")

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
            root_path = Path(root)

            # Skip excluded directories
            dirs[:] = [
                d
                for d in dirs
                if not self._should_exclude(str(root_path / d), directory)
            ]

            for file in files:
                file_path = root_path / file

                if self._is_supported_file(file) and not self._should_exclude(
                    str(file_path), directory
                ):
                    code_files.append(str(file_path))

        return code_files

    def _create_file_data(
        self, file_paths: list[str], base_dir: str | None = None
    ) -> list[dict[str, Any]]:
        """Create file data structures with content and metadata (sync version for backward compatibility)."""
        files_data = []

        for file_path in file_paths:
            try:
                content = self._read_file_content(file_path)
                path_obj = Path(file_path)

                # Calculate relative path if base_dir provided
                relative_path = file_path
                if base_dir:
                    base_path = Path(base_dir)
                    relative_path = str(path_obj.relative_to(base_path))

                file_info = {
                    "path": relative_path,
                    "absolute_path": file_path,
                    "name": path_obj.name,
                    "extension": path_obj.suffix,
                    "content": content,
                    "size": len(content),
                    "lines": len(content.splitlines()),
                }

                files_data.append(file_info)

            except Exception as e:
                print(f"Warning: Failed to process file {file_path}: {str(e)}")
                continue

        return files_data

    async def _create_file_data_async(
        self, file_paths: list[str], base_dir: str | None = None
    ) -> list[dict[str, Any]]:
        """Create file data structures with content and metadata using async I/O."""
        files_data = []

        for file_path in file_paths:
            try:
                content = await self._read_file_content_async(file_path)
                path_obj = Path(file_path)

                # Calculate relative path if base_dir provided
                relative_path = file_path
                if base_dir:
                    base_path = Path(base_dir)
                    relative_path = str(path_obj.relative_to(base_path))

                file_info = {
                    "path": relative_path,
                    "absolute_path": file_path,
                    "name": path_obj.name,
                    "extension": path_obj.suffix,
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
        """Process input (single file or zip) and return file data (sync version for backward compatibility).

        Returns:
            List of file data dictionaries.
        """
        path_obj = Path(input_path).resolve()

        # Handle single file
        if path_obj.is_file():
            if str(path_obj).lower().endswith(".zip"):
                return self._process_zip_file(str(path_obj))
            if self._is_supported_file(str(path_obj)):
                return self._create_file_data([str(path_obj)])
            raise Exception(f"Unsupported file type: {path_obj.suffix}")

        # Handle directory
        if path_obj.is_dir():
            code_files = self._scan_directory(str(path_obj))
            if not code_files:
                raise Exception("No supported code files found in directory")
            return self._create_file_data(code_files, str(path_obj))

        raise Exception(f"Input path does not exist: {input_path}")

    async def process_input_async(self, input_path: str) -> list[dict[str, Any]]:
        """Process input (single file or zip) and return file data using async I/O.

        Returns:
            List of file data dictionaries.
        """
        path_obj = Path(input_path).resolve()

        # Handle single file
        if path_obj.is_file():
            if str(path_obj).lower().endswith(".zip"):
                return await self._process_zip_file_async(str(path_obj))
            if self._is_supported_file(str(path_obj)):
                return await self._create_file_data_async([str(path_obj)])
            raise Exception(f"Unsupported file type: {path_obj.suffix}")

        # Handle directory
        if path_obj.is_dir():
            code_files = self._scan_directory(str(path_obj))
            if not code_files:
                raise Exception("No supported code files found in directory")
            return await self._create_file_data_async(code_files, str(path_obj))

        raise Exception(f"Input path does not exist: {input_path}")

    def _process_zip_file(self, zip_path: str) -> list[dict[str, Any]]:
        """Process zip file and return file data (sync version for backward compatibility)."""
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
            if temp_dir and Path(temp_dir).exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    async def _process_zip_file_async(self, zip_path: str) -> list[dict[str, Any]]:
        """Process zip file and return file data using async I/O."""
        temp_dir = None

        try:
            # Extract zip
            temp_dir = self._extract_zip(zip_path)

            # Find code files
            code_files = self._scan_directory(temp_dir)

            if not code_files:
                raise Exception("No supported code files found in zip archive")

            # Create file data
            files_data = await self._create_file_data_async(code_files, temp_dir)

            return files_data

        finally:
            # Cleanup temporary directory
            if temp_dir and Path(temp_dir).exists():
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

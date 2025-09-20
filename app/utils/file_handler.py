"""File handling utilities for FastAPI file uploads and processing."""

import logging
import tempfile
import zipfile
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from ..core.config import Settings
from ..core.exceptions import FileProcessingError
from ..core.exceptions import FileTooLargeError
from ..core.exceptions import TooManyFilesError
from ..core.exceptions import UnsupportedFileTypeError
from ..core.security import sanitize_filename
from ..core.security import validate_file_path
from ..models.requests import FileContent

logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file upload, validation, and processing operations."""

    def __init__(self, settings: Settings):
        """Initialize file handler with settings."""
        self.settings = settings
        self.max_file_size = settings.max_file_size_bytes
        self.max_files = settings.max_files_per_request
        self.allowed_extensions = set(settings.allowed_file_types)

    async def process_uploaded_files(
        self, files: list[UploadFile], extract_archives: bool = True
    ) -> list[FileContent]:
        """Process uploaded files and return FileContent objects."""
        if len(files) > self.max_files:
            raise TooManyFilesError(len(files), self.max_files)

        all_file_contents = []

        for upload_file in files:
            try:
                # Basic validation
                await self._validate_uploaded_file(upload_file)

                # Read file content
                content = await self._read_uploaded_file(upload_file)

                # Check if it's a zip file and should be extracted
                if (
                    extract_archives
                    and upload_file.filename
                    and upload_file.filename.lower().endswith(".zip")
                ):
                    extracted_files = await self._extract_zip_content(
                        upload_file.filename, content
                    )
                    all_file_contents.extend(extracted_files)
                else:
                    # Process as single file
                    file_content = await self._create_file_content(
                        upload_file.filename or "unknown", content
                    )
                    all_file_contents.append(file_content)

            except Exception as e:
                if isinstance(
                    e,
                    (FileTooLargeError, UnsupportedFileTypeError, FileProcessingError),
                ):
                    raise
                raise FileProcessingError(
                    f"Failed to process file {upload_file.filename}: {str(e)}"
                )

        # Final validation
        if len(all_file_contents) > self.max_files:
            raise TooManyFilesError(len(all_file_contents), self.max_files)

        return all_file_contents

    async def _validate_uploaded_file(self, upload_file: UploadFile) -> None:
        """Validate uploaded file against size and type constraints."""
        # Check file size
        if upload_file.size and upload_file.size > self.max_file_size:
            raise FileTooLargeError(upload_file.size, self.max_file_size)

        # Check file extension
        if upload_file.filename:
            file_ext = Path(upload_file.filename).suffix.lower()

            # Allow zip files for extraction, or check against allowed extensions
            if file_ext != ".zip" and file_ext not in self.allowed_extensions:
                raise UnsupportedFileTypeError(file_ext, list(self.allowed_extensions))

    async def _read_uploaded_file(self, upload_file: UploadFile) -> bytes:
        """Read the content of an uploaded file."""
        # Reset file position
        await upload_file.seek(0)

        # Read content
        content = await upload_file.read()

        # Validate size after reading
        if len(content) > self.max_file_size:
            raise FileTooLargeError(len(content), self.max_file_size)

        return content

    async def _create_file_content(self, filename: str, content: bytes) -> FileContent:
        """Create FileContent object from filename and content."""
        # Sanitize and validate filename for security
        try:
            safe_filename = sanitize_filename(filename)
            validated_filename = validate_file_path(safe_filename)
        except ValueError as e:
            logger.warning(f"Unsafe filename detected: {filename} - {str(e)}")
            raise FileProcessingError(f"Invalid filename: {str(e)}")

        # Decode content to string
        try:
            # Try UTF-8 first
            text_content = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                # Try latin-1 as fallback
                text_content = content.decode("latin-1")
            except UnicodeDecodeError:
                # If still fails, treat as binary and create a placeholder
                raise FileProcessingError(
                    f"Unable to decode file {safe_filename} as text. "
                    "Only text files are supported for analysis."
                )

        # Get file extension
        file_ext = Path(safe_filename).suffix.lower()

        return FileContent(
            filename=safe_filename, content=text_content, file_type=file_ext
        )

    async def _extract_zip_content(
        self, zip_filename: str, zip_content: bytes
    ) -> list[FileContent]:
        """Extract files from zip archive and return FileContent objects."""
        file_contents = []

        try:
            # Write zip content to temporary file
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
                temp_zip.write(zip_content)
                temp_zip_path = temp_zip.name

            # Extract and process files
            with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
                file_list = zip_ref.namelist()

                # Filter files by supported extensions and exclude directories
                valid_files = []
                for file_path in file_list:
                    if not file_path.endswith("/") and self._is_supported_file_in_zip(
                        file_path
                    ):
                        # Validate path for security (prevent zip bombs and path traversal)
                        try:
                            # Check for dangerous paths
                            safe_path = sanitize_filename(Path(file_path).name)
                            validate_file_path(safe_path)
                            valid_files.append(file_path)
                        except ValueError as e:
                            logger.warning(
                                f"Skipping unsafe file in zip: {file_path} - {str(e)}"
                            )
                            continue

                # Check if too many files
                if len(valid_files) > self.max_files:
                    raise TooManyFilesError(len(valid_files), self.max_files)

                # Extract and process each valid file
                for file_path in valid_files:
                    try:
                        # Check file size before extraction
                        file_info = zip_ref.getinfo(file_path)
                        if file_info.file_size > self.max_file_size:
                            continue  # Skip oversized files

                        # Extract file content
                        with zip_ref.open(file_path) as extracted_file:
                            file_content_bytes = extracted_file.read()

                        # Create FileContent object
                        file_content = await self._create_file_content(
                            file_path, file_content_bytes
                        )
                        file_contents.append(file_content)

                    except Exception as e:
                        # Log error and continue with other files
                        print(f"Warning: Failed to extract {file_path}: {str(e)}")
                        continue

            # Clean up temporary file
            Path(temp_zip_path).unlink()

            if not file_contents:
                raise FileProcessingError(
                    f"No supported files found in archive {zip_filename}"
                )

            return file_contents

        except zipfile.BadZipFile:
            raise FileProcessingError(f"Invalid zip file: {zip_filename}")
        except Exception as e:
            raise FileProcessingError(
                f"Failed to extract zip file {zip_filename}: {str(e)}"
            )

    def _is_supported_file_in_zip(self, file_path: str) -> bool:
        """Check if file in zip archive has supported extension."""
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.allowed_extensions

    def get_file_type_from_content(self, content: str, filename: str) -> str:
        """Guess file type from content and filename."""
        # Try extension first
        file_ext = Path(filename).suffix.lower()
        if file_ext:
            return file_ext

        # Try to guess from content (basic heuristics)
        content_lower = content.lower().strip()

        if content_lower.startswith("<!doctype html") or "<html" in content_lower:
            return ".html"
        if content_lower.startswith("<?xml") or content_lower.startswith("<"):
            return ".xml"
        if '"use strict"' in content_lower or "function(" in content_lower:
            return ".js"
        if "def " in content_lower or "import " in content_lower:
            return ".py"
        if "class " in content_lower and "{" in content_lower:
            return ".java"  # Could also be C++, C#, etc.

        return ".txt"  # Default fallback

    def validate_file_content(
        self, file_content: FileContent
    ) -> tuple[bool, list[str]]:
        """Validate file content and return validation results."""
        errors = []
        warnings = []

        # Check file size
        content_size = len(file_content.content.encode("utf-8"))
        if content_size > self.max_file_size:
            errors.append(
                f"File {file_content.filename} is too large ({content_size} bytes)"
            )

        # Check if content is empty
        if not file_content.content.strip():
            warnings.append(f"File {file_content.filename} appears to be empty")

        # Check if content looks like binary
        if len(file_content.content) > 100:
            # Simple heuristic: if more than 10% of characters are non-printable, might be binary
            non_printable_count = sum(
                1
                for c in file_content.content[:1000]
                if ord(c) < 32 and c not in "\t\n\r"
            )
            if non_printable_count > len(file_content.content[:1000]) * 0.1:
                warnings.append(
                    f"File {file_content.filename} might contain binary content"
                )

        return len(errors) == 0, errors + warnings

    async def save_files_to_temp_directory(
        self, files: list[FileContent], base_dir: str | None = None
    ) -> str:
        """Save files to temporary directory and return directory path."""
        if base_dir:
            temp_dir = Path(base_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
        else:
            temp_dir = Path(tempfile.mkdtemp(prefix="code_summarizer_"))

        for file_content in files:
            file_path = temp_dir / file_content.filename

            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file content
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(file_content.content)

        return str(temp_dir)

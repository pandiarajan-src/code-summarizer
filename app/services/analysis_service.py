"""Analysis service wrapper for integrating existing core modules with FastAPI."""

# Import existing core modules
import os
import time
import uuid
from pathlib import Path
from typing import Any

from ..core.config import Settings

# Import from app directory (organized structure)
from ..core.context_manager import ContextManager
from ..core.exceptions import AnalysisError
from ..core.exceptions import ConfigurationError
from ..core.exceptions import FileProcessingError
from ..core.exceptions import LLMServiceError
from ..models.requests import ConfigOverrides
from ..models.requests import FileContent
from ..models.responses import AnalysisResponse
from ..models.responses import BatchAnalysisResult
from ..models.responses import FileAnalysisResult
from ..models.responses import ProjectSummary
from ..utils.file_processor import FileProcessor
from ..utils.markdown_formatter import MarkdownFormatter
from .llm_client import LLMClient


class AnalysisService:
    """Service class for handling code analysis operations."""

    def __init__(self, settings: Settings):
        """Initialize the analysis service with settings."""
        self.settings = settings
        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize the core analysis components."""
        try:
            # Set environment variables from Pydantic settings for legacy modules
            self._set_environment_variables()

            # Create a legacy config dict for existing modules
            legacy_config = self.settings.to_legacy_config()

            # Initialize components with config
            self.file_processor = FileProcessor(
                config_path=self.settings.config_file_path
            )
            self.llm_client = LLMClient(
                config_path=self.settings.config_file_path,
                prompts_file=self.settings.prompts_file_path,
            )
            self.context_manager = ContextManager(
                config_path=self.settings.config_file_path
            )
            self.markdown_formatter = MarkdownFormatter(
                config_path=self.settings.config_file_path
            )

            print(f"✅ Analysis components initialized successfully")
            print(f"   API key configured: {'***SET***' if self.settings.openai_api_key else 'NOT_SET'}")
            print(f"   Model: {self.settings.llm_model}")

        except Exception as e:
            print(f"❌ Failed to initialize analysis components: {str(e)}")
            raise ConfigurationError(
                f"Failed to initialize analysis components: {str(e)}",
                details={"component_error": str(e)},
            )

    def _set_environment_variables(self) -> None:
        """Set environment variables from Pydantic settings for legacy modules."""
        print("🔧 Setting environment variables for legacy modules...")

        # Set OpenAI API key
        if self.settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = self.settings.openai_api_key
            print("   ✅ OPENAI_API_KEY set from Pydantic settings")
        else:
            print("   ❌ OPENAI_API_KEY not available in Pydantic settings")

        # Set OpenAI base URL if provided
        if self.settings.openai_base_url:
            os.environ["OPENAI_BASE_URL"] = self.settings.openai_base_url
            print(f"   ✅ OPENAI_BASE_URL set to: {self.settings.openai_base_url}")

        # Set model name
        if self.settings.llm_model:
            os.environ["MODEL_NAME"] = self.settings.llm_model
            print(f"   ✅ MODEL_NAME set to: {self.settings.llm_model}")

        print("   Environment variables configured for legacy modules")

    async def analyze_files(
        self,
        files: list[FileContent],
        config_overrides: ConfigOverrides | None = None,
        output_format: str = "json",
        verbose: bool = False,
    ) -> AnalysisResponse:
        """Analyze a list of files and return results."""
        start_time = time.time()
        analysis_id = str(uuid.uuid4())

        try:
            # Convert FileContent objects to the format expected by existing modules
            files_data = await self._convert_file_content_to_legacy_format(files)

            if not files_data:
                raise FileProcessingError("No valid files to analyze")

            # Apply configuration overrides if provided
            if config_overrides:
                await self._apply_config_overrides(config_overrides)

            # Create batches and analyze them
            batches = self.context_manager.create_batches(files_data)
            batch_results, total_tokens = await self._analyze_batches(
                batches, analysis_id, verbose
            )

            # Generate project summary and markdown output
            project_summary = await self._generate_project_summary(
                files_data, batch_results, verbose
            )
            markdown_output = await self._generate_markdown_output(
                output_format, files_data, batches, batch_results, verbose
            )

            # Build and return response
            processing_time = time.time() - start_time
            file_results = []
            for batch_result in batch_results:
                file_results.extend(batch_result.individual_analyses)

            return AnalysisResponse(
                success=True,
                analysis_id=analysis_id,
                files_analyzed=len(files_data),
                file_results=file_results,
                batch_results=batch_results,
                project_summary=project_summary,
                total_tokens_used=total_tokens,
                total_processing_time_seconds=processing_time,
                config_used=self.settings.to_legacy_config(),
                markdown_output=markdown_output,
            )

        except Exception as e:
            if isinstance(
                e,
                (
                    AnalysisError,
                    FileProcessingError,
                    LLMServiceError,
                    ConfigurationError,
                ),
            ):
                raise
            raise AnalysisError(f"Analysis failed: {str(e)}", details={"error": str(e)})

    async def analyze_from_paths(
        self,
        paths: list[str],
        config_overrides: ConfigOverrides | None = None,
        output_format: str = "json",
        verbose: bool = False,
        recursive: bool = True,
    ) -> AnalysisResponse:
        """Analyze files from server paths."""
        try:
            # Process paths using existing file processor
            all_files_data = []

            for path in paths:
                if not Path(path).exists():
                    raise FileProcessingError(f"Path does not exist: {path}")

                files_data = self.file_processor.process_input(path)
                all_files_data.extend(files_data)

            if not all_files_data:
                raise FileProcessingError("No supported files found in provided paths")

            # Convert to FileContent format and analyze
            file_contents = []
            for file_data in all_files_data:
                file_contents.append(
                    FileContent(
                        filename=file_data["path"],
                        content=file_data["content"],
                        file_type=file_data.get("extension", "unknown"),
                    )
                )

            return await self.analyze_files(
                files=file_contents,
                config_overrides=config_overrides,
                output_format=output_format,
                verbose=verbose,
            )

        except Exception as e:
            if isinstance(
                e,
                (
                    AnalysisError,
                    FileProcessingError,
                    LLMServiceError,
                    ConfigurationError,
                ),
            ):
                raise
            raise AnalysisError(f"Path analysis failed: {str(e)}")

    async def _convert_file_content_to_legacy_format(
        self, files: list[FileContent]
    ) -> list[dict[str, Any]]:
        """Convert FileContent objects to legacy format expected by existing modules."""
        files_data = []
        for file_content in files:
            # Determine file extension
            file_path = Path(file_content.filename)
            extension = file_path.suffix or file_content.file_type or ""

            # Create legacy format matching the expected structure
            file_data = {
                "path": file_content.filename,
                "absolute_path": file_content.filename,
                "name": file_path.name,
                "extension": extension,
                "content": file_content.content,
                "size": len(file_content.content),
                "lines": len(file_content.content.splitlines()),
                "language": self._guess_language_from_extension(extension),
            }

            files_data.append(file_data)

        return files_data

    def _guess_language_from_extension(self, extension: str) -> str:
        """Guess programming language from file extension."""
        # This mirrors the logic from existing modules
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".swift": "swift",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".scala": "scala",
            ".kt": "kotlin",
            ".dart": "dart",
            ".r": "r",
            ".m": "objective-c",
            ".mm": "objective-c",
        }

        return language_map.get(extension.lower(), "unknown")

    async def _apply_config_overrides(self, overrides: ConfigOverrides) -> None:
        """Apply configuration overrides to the service."""
        # Note: This is a simplified implementation
        # In a production system, you might want to create new component instances
        # with the overridden configuration rather than modifying existing ones

        if overrides.llm_model:
            # Would need to reinitialize LLM client with new model
            pass

        if overrides.llm_max_tokens:
            # Would need to update LLM client configuration
            pass

        # Add other override handling as needed

    def get_supported_file_types(self) -> list[str]:
        """Get list of supported file types."""
        return self.settings.allowed_file_types

    async def _analyze_batches(
        self, batches: list[Any], analysis_id: str, verbose: bool
    ) -> tuple[list[BatchAnalysisResult], int]:
        """Analyze batches and return results with total tokens."""
        if verbose:
            print(f"Created {len(batches)} batches for analysis")

        batch_results = []
        total_tokens = 0

        for i, batch in enumerate(batches):
            if verbose:
                print(f"Analyzing batch {i + 1}/{len(batches)}...")

            batch_start_time = time.time()
            try:
                result = self.llm_client.analyze_batch(batch)
                batch_processing_time = time.time() - batch_start_time

                # Create batch result
                batch_result = BatchAnalysisResult(
                    batch_id=f"{analysis_id}_batch_{i}",
                    files_count=len(batch),
                    batch_summary=result.get("batch_summary", {}),
                    individual_analyses=[],
                    total_tokens_used=result.get("tokens_used", 0),
                    processing_time_seconds=batch_processing_time,
                )

                # Add individual file analyses if available
                if "individual_analyses" in result:
                    for file_analysis in result["individual_analyses"]:
                        batch_result.individual_analyses.append(
                            FileAnalysisResult(
                                filename=file_analysis.get("filename", "unknown"),
                                file_type=file_analysis.get("file_type", "unknown"),
                                language=file_analysis.get("language", "unknown"),
                                analysis=file_analysis.get("analysis", {}),
                                tokens_used=file_analysis.get("tokens_used", 0),
                                processing_time_seconds=0,  # Individual timing not available
                            )
                        )

                batch_results.append(batch_result)
                total_tokens += result.get("tokens_used", 0)

            except Exception as e:
                raise LLMServiceError(f"Batch analysis failed: {str(e)}")

        return batch_results, total_tokens

    async def _generate_project_summary(
        self,
        files_data: list[Any],
        batch_results: list[BatchAnalysisResult],
        verbose: bool,
    ) -> ProjectSummary | None:
        """Generate project summary if multiple files."""
        if len(files_data) <= 1:
            return None

        try:
            summary_result = self.llm_client.generate_project_summary(
                files_data, [br.batch_summary for br in batch_results]
            )
            return ProjectSummary(
                total_files=len(files_data),
                languages_detected=summary_result.get("languages_detected", []),
                project_structure=summary_result.get("project_structure", {}),
                key_insights=summary_result.get("key_insights", []),
                recommendations=summary_result.get("recommendations", []),
                technical_debt=summary_result.get("technical_debt", {}),
                dependencies=summary_result.get("dependencies", {}),
            )
        except Exception as e:
            if verbose:
                print(f"Project summary generation failed: {str(e)}")
            return None

    async def _generate_markdown_output(
        self,
        output_format: str,
        files_data: list[Any],
        batches: list[Any],
        batch_results: list[BatchAnalysisResult],
        verbose: bool,
    ) -> str | None:
        """Generate markdown output if requested."""
        if output_format not in ["markdown", "both"]:
            return None

        try:
            # Convert batch results back to legacy format for markdown formatter
            # Need to reconstruct the full analysis results including file details
            legacy_analysis_results = []
            for i, _br in enumerate(batch_results):
                # Get the original batch analysis result from LLM client
                batch = batches[i]
                full_result = self.llm_client.analyze_batch(batch)
                legacy_analysis_results.append(full_result)

            return self.markdown_formatter.format_results(
                files_data, legacy_analysis_results
            )
        except Exception as e:
            if verbose:
                print(f"Markdown generation failed: {str(e)}")
            return None

    def get_current_config(self) -> dict[str, Any]:
        """Get current service configuration."""
        return self.settings.to_legacy_config()

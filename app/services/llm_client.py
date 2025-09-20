"""LLM client for interacting with OpenAI-compatible APIs."""

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import cast

import httpx
from openai import OpenAI

if TYPE_CHECKING:
    from app.core.config import Settings


class OpenAIClientPool:
    """Connection pool manager for OpenAI clients."""

    _instance = None
    _clients: dict[str, OpenAI] = {}
    _http_client: httpx.Client | None = None

    def __new__(cls) -> "OpenAIClientPool":
        """Create singleton instance of OpenAI client pool."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_client(
        cls, api_key: str, base_url: str = "https://api.openai.com/v1"
    ) -> OpenAI:
        """Get or create an OpenAI client with connection pooling."""
        client_key = f"{api_key[:10]}...{base_url}"

        if client_key not in cls._clients:
            # Create shared HTTP client with connection pooling
            if cls._http_client is None:
                cls._http_client = httpx.Client(
                    limits=httpx.Limits(
                        max_keepalive_connections=10,
                        max_connections=20,
                        keepalive_expiry=30.0,
                    ),
                    timeout=httpx.Timeout(60.0),
                )

            cls._clients[client_key] = OpenAI(
                api_key=api_key, base_url=base_url, http_client=cls._http_client
            )

        return cls._clients[client_key]

    @classmethod
    def close_all(cls) -> None:
        """Close all pooled connections."""
        if cls._http_client:
            cls._http_client.close()
            cls._http_client = None
        cls._clients.clear()


class LLMClient:
    """Client for interacting with Large Language Models via OpenAI-compatible APIs."""

    def __init__(
        self,
        config_path: str | None = None,
        prompts_file: str | None = None,
        *,
        settings: "Settings | None" = None,
    ) -> None:
        """Initialize LLM client with configuration.

        Args:
            config_path: Legacy config path for backward compatibility
                (positional for backward compat)
            prompts_file: Legacy prompts file path for backward compatibility
                (positional for backward compat)
            settings: Pydantic Settings object (preferred, keyword-only)
        """
        if settings:
            self.settings = settings
            self.client = self._initialize_client_from_settings(settings)
            self.prompts = settings.prompts
            self.model = settings.llm_model
            self.max_tokens = settings.llm_max_tokens
            self.temperature = settings.llm_temperature
        elif config_path:
            # Legacy support
            self.config = self._load_legacy_config(config_path)
            self.client = self._initialize_client()

            # Load prompts from file if provided
            if prompts_file:
                from ..utils.prompt_loader import PromptLoader

                self.prompt_loader = PromptLoader(prompts_file)
                self.prompts = {}
            else:
                self.prompts = {}

            # LLM settings
            llm_config = self.config.get("llm", {})
            self.model = llm_config.get("model", "gpt-4o")
            self.max_tokens = llm_config.get("max_tokens", 4000)
            self.temperature = llm_config.get("temperature", 0.1)
        else:
            # Use defaults from Settings if no config provided
            from app.core.config import settings as default_settings

            self.settings = default_settings
            self.client = self._initialize_client_from_settings(default_settings)
            self.prompts = default_settings.prompts
            self.model = default_settings.llm_model
            self.max_tokens = default_settings.llm_max_tokens
            self.temperature = default_settings.llm_temperature

    def _load_legacy_config(self, config_path: str) -> dict[str, Any]:
        """Load configuration from YAML file (legacy support)."""
        try:
            import yaml

            with Path(config_path).open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}

    def _initialize_client_from_settings(self, settings: "Settings") -> OpenAI:
        """Initialize OpenAI client from Pydantic settings with connection pooling."""
        api_key = settings.openai_api_key
        base_url = settings.openai_base_url or "https://api.openai.com/v1"

        print("🔧 Initializing LLM client with connection pooling...")
        print(f"   API key available: {'***SET***' if api_key else 'NOT_SET'}")
        print(f"   Base URL: {base_url}")

        if not api_key:
            error_msg = (
                "OPENAI_API_KEY is required. "
                "Please set it in your .env file or environment."
            )
            print(f"   ❌ {error_msg}")
            raise ValueError(error_msg)

        print("   ✅ LLM client initialized successfully with connection pooling")
        return OpenAIClientPool.get_client(api_key=api_key, base_url=base_url)

    def _initialize_client(self) -> OpenAI:
        """Initialize OpenAI client with API key and base URL using connection pooling."""
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

        print("🔧 Initializing LLM client with connection pooling...")
        print(f"   API key available: {'***SET***' if api_key else 'NOT_SET'}")
        print(f"   Base URL: {base_url}")

        if not api_key:
            error_msg = (
                "OPENAI_API_KEY environment variable is required. "
                "This should be set by the AnalysisService from Pydantic settings."
            )
            print(f"   ❌ {error_msg}")
            raise ValueError(error_msg)

        try:
            client = OpenAIClientPool.get_client(api_key=api_key, base_url=base_url)
            print(
                "   ✅ OpenAI client initialized successfully with connection pooling"
            )
            return client
        except Exception as e:
            error_msg = f"Failed to initialize OpenAI client: {str(e)}"
            print(f"   ❌ {error_msg}")
            raise ValueError(error_msg)

    def _get_prompt(self, prompt_name: str) -> str:
        """Get prompt by name from either new settings or legacy prompt loader."""
        if hasattr(self, "prompts") and self.prompts:
            # New way: from Pydantic settings
            prompt_config = self.prompts.get(prompt_name, {})
            prompt_text = prompt_config.get("prompt", "")
            if not isinstance(prompt_text, str):
                raise ValueError(f"Prompt '{prompt_name}' must be a string")
            return prompt_text
        if hasattr(self, "prompt_loader"):
            # Legacy way: from prompt loader
            prompt_text = getattr(self.prompt_loader, f"{prompt_name}_prompt", "")
            if not isinstance(prompt_text, str):
                raise ValueError(f"Prompt '{prompt_name}' must be a string")
            return prompt_text
        raise ValueError(f"Prompt '{prompt_name}' not found in configuration")

    def _make_api_call(self, prompt: str) -> str:
        """Make API call to LLM and return response."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a code analysis expert. "
                            "Always respond with valid JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            content = response.choices[0].message.content
            if content is None:
                raise Exception("LLM returned empty response")
            return content.strip()

        except Exception as e:
            raise Exception(f"LLM API call failed: {str(e)}")

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Parse JSON response from LLM, handling common formatting issues."""
        try:
            # Try direct parsing first
            result = json.loads(response)
            if isinstance(result, dict):
                return result
            raise ValueError("Response is not a JSON object")
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                if json_end != -1:
                    json_str = response[json_start:json_end].strip()
                    result = json.loads(json_str)
                    if isinstance(result, dict):
                        return result

            # Try to find JSON-like content
            start_idx = response.find("{")
            end_idx = response.rfind("}")
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx : end_idx + 1]
                result = json.loads(json_str)
                if isinstance(result, dict):
                    return result

            raise Exception(
                f"Could not parse JSON from LLM response: {response[:200]}..."
            )

    def detect_languages(self, files_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Detect programming languages in files."""
        # Create summary of files for language detection
        files_summary = []
        for file_data in files_data[:5]:  # Limit to first 5 files for detection
            files_summary.append(
                f"File: {file_data['name']}\n{file_data['content'][:500]}...\n"
            )

        files_content = "\n".join(files_summary)
        prompt = self._get_prompt("language_detection").format(
            files_content=files_content
        )

        response = self._make_api_call(prompt)
        return self._parse_json_response(response)

    def analyze_single_file(self, file_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze a single source code file."""
        # Determine language from extension or content
        language = self._guess_language_from_extension(file_data["extension"])

        prompt = self._get_prompt("single_file_analysis").format(
            filename=file_data["name"],
            language=language,
            language_lower=language.lower(),
            content=file_data["content"],
        )

        response = self._make_api_call(prompt)
        result = self._parse_json_response(response)

        # Add file metadata
        result["filename"] = file_data["name"]
        result["filepath"] = file_data["path"]
        result["file_size"] = file_data["size"]
        result["line_count"] = file_data["lines"]

        return result

    def analyze_batch(self, batch_files: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze a batch of files together."""
        if len(batch_files) == 1:
            # Single file analysis
            return {
                "batch_summary": {
                    "main_purpose": "Single file analysis",
                    "patterns": [],
                    "architecture": "N/A",
                },
                "files": [self.analyze_single_file(batch_files[0])],
                "relationships": [],
            }

        # Prepare files info for batch analysis
        files_info = []
        for file_data in batch_files:
            info = f"""
File: {file_data["name"]} ({file_data["extension"]})
Path: {file_data["path"]}
Lines: {file_data["lines"]}
Content:
```
{file_data["content"][:2000]}{"..." if len(file_data["content"]) > 2000 else ""}
```
"""
            files_info.append(info)

        prompt = self._get_prompt("batch_analysis").format(
            files_info="\n".join(files_info)
        )

        response = self._make_api_call(prompt)
        return self._parse_json_response(response)

    def generate_project_summary(
        self, files_data: list[dict[str, Any]], analysis_results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate overall project summary."""
        # Extract languages and totals
        languages = set()
        for file_data in files_data:
            lang = self._guess_language_from_extension(file_data["extension"])
            languages.add(lang)

        # Create analysis summary
        analysis_summary = {
            "total_batches": len(analysis_results),
            "total_files_analyzed": sum(
                len(result.get("files", [])) for result in analysis_results
            ),
            "key_findings": [],
        }

        # Extract key findings from batch results
        key_findings = cast(list[str], analysis_summary["key_findings"])
        for result in analysis_results:
            if "batch_summary" in result:
                main_purpose = result["batch_summary"].get("main_purpose", "")
                if main_purpose:
                    key_findings.append(main_purpose)

        prompt = self._get_prompt("project_summary").format(
            total_files=len(files_data),
            languages=", ".join(languages),
            analysis_summary=json.dumps(analysis_summary, indent=2),
        )

        response = self._make_api_call(prompt)
        return self._parse_json_response(response)

    def _guess_language_from_extension(self, extension: str) -> str:
        """Simple language detection from file extension."""
        ext_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "JavaScript",
            ".tsx": "TypeScript",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
            ".h": "C",
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
            ".sh": "Shell",
            ".sql": "SQL",
        }

        return ext_map.get(extension.lower(), "Unknown")

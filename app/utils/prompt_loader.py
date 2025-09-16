"""Dynamic prompt loader for reading prompts from configuration files."""

from pathlib import Path
from typing import Any

import yaml


class PromptLoader:
    """Loads prompts from external configuration files at runtime."""

    def __init__(self, prompts_file: str = "prompts.yaml") -> None:
        """Initialize the prompt loader with a prompts file path.

        Args:
            prompts_file: Path to the prompts configuration file.
        """
        self.prompts_file = Path(prompts_file)
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> dict[str, Any]:
        """Load prompts from the configuration file.

        Returns:
            Dictionary containing all prompts.

        Raises:
            FileNotFoundError: If the prompts file doesn't exist.
            ValueError: If the prompts file is invalid.
        """
        if not self.prompts_file.exists():
            raise FileNotFoundError(
                f"Prompts file not found: {self.prompts_file}. "
                "Please ensure prompts.yaml exists in the project root."
            )

        try:
            with self.prompts_file.open(encoding="utf-8") as f:
                prompts_data = yaml.safe_load(f)

            if not prompts_data:
                raise ValueError("Prompts file is empty")

            if not isinstance(prompts_data, dict):
                raise ValueError("Prompts file must contain a dictionary")

            return prompts_data

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in prompts file: {e}")

    def get_prompt(self, prompt_name: str) -> str:
        """Get a specific prompt by name.

        Args:
            prompt_name: Name of the prompt to retrieve.

        Returns:
            The prompt template string.

        Raises:
            KeyError: If the prompt name doesn't exist.
        """
        if prompt_name not in self.prompts:
            available = ", ".join(self.prompts.keys())
            raise KeyError(
                f"Prompt '{prompt_name}' not found. Available prompts: {available}"
            )

        prompt_data = self.prompts[prompt_name]

        # Support both direct string and nested structure with 'prompt' key
        if isinstance(prompt_data, dict):
            if "prompt" not in prompt_data:
                raise ValueError(f"Prompt '{prompt_name}' is missing 'prompt' field")
            prompt_value = prompt_data["prompt"]
            if not isinstance(prompt_value, str):
                raise ValueError(f"Prompt '{prompt_name}' value must be a string")
            return prompt_value
        if isinstance(prompt_data, str):
            return prompt_data
        raise ValueError(
            f"Invalid prompt format for '{prompt_name}'. "
            "Expected string or dict with 'prompt' field."
        )

    def reload(self) -> None:
        """Reload prompts from the configuration file.

        Useful for hot-reloading prompts during development.
        """
        self.prompts = self._load_prompts()

    @property
    def language_detection_prompt(self) -> str:
        """Get the language detection prompt."""
        return self.get_prompt("language_detection")

    @property
    def single_file_analysis_prompt(self) -> str:
        """Get the single file analysis prompt."""
        return self.get_prompt("single_file_analysis")

    @property
    def batch_analysis_prompt(self) -> str:
        """Get the batch analysis prompt."""
        return self.get_prompt("batch_analysis")

    @property
    def project_summary_prompt(self) -> str:
        """Get the project summary prompt."""
        return self.get_prompt("project_summary")

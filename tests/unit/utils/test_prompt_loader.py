import tempfile
from pathlib import Path

import pytest
from app.utils.prompt_loader import PromptLoader


class TestPromptLoader:
    """Test prompt loader functionality."""

    def test_init_with_valid_prompts_file(self):
        """Test initialization with valid prompts file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
language_detection: "Detect the programming language in the following code: {files_content}"
single_file_analysis:
  prompt: "Analyze this {language} file: {content}"
batch_analysis: "Analyze this batch of files: {files_info}"
project_summary: "Create project summary for {total_files} files"
"""
            )
            f.flush()

            try:
                loader = PromptLoader(f.name)

                assert "language_detection" in loader.prompts
                assert "single_file_analysis" in loader.prompts
                assert "batch_analysis" in loader.prompts
                assert "project_summary" in loader.prompts
            finally:
                Path(f.name).unlink()

    def test_init_with_nonexistent_file(self):
        """Test initialization with nonexistent prompts file."""
        with pytest.raises(FileNotFoundError, match="Prompts file not found"):
            PromptLoader("nonexistent.yaml")

    def test_init_with_empty_file(self):
        """Test initialization with empty prompts file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()

            try:
                with pytest.raises(ValueError, match="Prompts file is empty"):
                    PromptLoader(f.name)
            finally:
                Path(f.name).unlink()

    def test_init_with_invalid_yaml(self):
        """Test initialization with invalid YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()

            try:
                with pytest.raises(ValueError, match="Invalid YAML in prompts file"):
                    PromptLoader(f.name)
            finally:
                Path(f.name).unlink()

    def test_init_with_non_dict_content(self):
        """Test initialization with non-dictionary content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("- this\n- is\n- a\n- list")
            f.flush()

            try:
                with pytest.raises(
                    ValueError, match="Prompts file must contain a dictionary"
                ):
                    PromptLoader(f.name)
            finally:
                Path(f.name).unlink()

    def test_get_prompt_string_format(self):
        """Test getting prompt in string format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write('simple_prompt: "This is a simple prompt"')
            f.flush()

            try:
                loader = PromptLoader(f.name)
                prompt = loader.get_prompt("simple_prompt")
                assert prompt == "This is a simple prompt"
            finally:
                Path(f.name).unlink()

    def test_get_prompt_dict_format(self):
        """Test getting prompt in dictionary format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
complex_prompt:
  prompt: "This is a complex prompt with {variable}"
  description: "A complex prompt example"
"""
            )
            f.flush()

            try:
                loader = PromptLoader(f.name)
                prompt = loader.get_prompt("complex_prompt")
                assert prompt == "This is a complex prompt with {variable}"
            finally:
                Path(f.name).unlink()

    def test_get_prompt_nonexistent(self):
        """Test getting nonexistent prompt."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write('existing_prompt: "This exists"')
            f.flush()

            try:
                loader = PromptLoader(f.name)

                with pytest.raises(KeyError, match="Prompt 'nonexistent' not found"):
                    loader.get_prompt("nonexistent")
            finally:
                Path(f.name).unlink()

    def test_get_prompt_dict_missing_prompt_key(self):
        """Test getting prompt from dict missing 'prompt' key."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
invalid_prompt:
  description: "Missing prompt key"
"""
            )
            f.flush()

            try:
                loader = PromptLoader(f.name)

                with pytest.raises(
                    ValueError,
                    match="Prompt 'invalid_prompt' is missing 'prompt' field",
                ):
                    loader.get_prompt("invalid_prompt")
            finally:
                Path(f.name).unlink()

    def test_get_prompt_dict_non_string_prompt(self):
        """Test getting prompt with non-string prompt value."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
invalid_prompt:
  prompt: 123
"""
            )
            f.flush()

            try:
                loader = PromptLoader(f.name)

                with pytest.raises(
                    ValueError, match="Prompt 'invalid_prompt' value must be a string"
                ):
                    loader.get_prompt("invalid_prompt")
            finally:
                Path(f.name).unlink()

    def test_get_prompt_invalid_format(self):
        """Test getting prompt with invalid format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid_prompt: 123")
            f.flush()

            try:
                loader = PromptLoader(f.name)

                with pytest.raises(ValueError, match="Invalid prompt format"):
                    loader.get_prompt("invalid_prompt")
            finally:
                Path(f.name).unlink()

    def test_reload(self):
        """Test reloading prompts from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write('test_prompt: "Original prompt"')
            f.flush()

            try:
                loader = PromptLoader(f.name)
                original_prompt = loader.get_prompt("test_prompt")
                assert original_prompt == "Original prompt"

                # Modify file
                with open(f.name, "w") as updated_f:
                    updated_f.write('test_prompt: "Updated prompt"')

                # Reload
                loader.reload()
                updated_prompt = loader.get_prompt("test_prompt")
                assert updated_prompt == "Updated prompt"
            finally:
                Path(f.name).unlink()

    def test_property_methods(self):
        """Test property methods for common prompts."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
language_detection: "Detect language: {files_content}"
single_file_analysis: "Analyze file: {content}"
batch_analysis: "Analyze batch: {files_info}"
project_summary: "Summarize project: {total_files}"
"""
            )
            f.flush()

            try:
                loader = PromptLoader(f.name)

                assert (
                    loader.language_detection_prompt
                    == "Detect language: {files_content}"
                )
                assert loader.single_file_analysis_prompt == "Analyze file: {content}"
                assert loader.batch_analysis_prompt == "Analyze batch: {files_info}"
                assert (
                    loader.project_summary_prompt == "Summarize project: {total_files}"
                )
            finally:
                Path(f.name).unlink()

    def test_property_methods_missing_prompts(self):
        """Test property methods when prompts are missing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write('some_other_prompt: "Not the one we need"')
            f.flush()

            try:
                loader = PromptLoader(f.name)

                with pytest.raises(
                    KeyError, match="Prompt 'language_detection' not found"
                ):
                    _ = loader.language_detection_prompt

                with pytest.raises(
                    KeyError, match="Prompt 'single_file_analysis' not found"
                ):
                    _ = loader.single_file_analysis_prompt

                with pytest.raises(KeyError, match="Prompt 'batch_analysis' not found"):
                    _ = loader.batch_analysis_prompt

                with pytest.raises(
                    KeyError, match="Prompt 'project_summary' not found"
                ):
                    _ = loader.project_summary_prompt
            finally:
                Path(f.name).unlink()

    def test_prompts_file_path_handling(self):
        """Test that prompts file path is properly handled as Path object."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write('test: "value"')
            f.flush()

            try:
                loader = PromptLoader(f.name)
                assert isinstance(loader.prompts_file, Path)
                assert str(loader.prompts_file) == f.name
            finally:
                Path(f.name).unlink()

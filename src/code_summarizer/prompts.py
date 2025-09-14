"""Prompt templates for LLM-based code analysis.

DEPRECATED: This module is kept for backward compatibility.
Use PromptLoader class from prompt_loader module instead.
"""

from .prompt_loader import PromptLoader

# Create a default prompt loader for backward compatibility
_default_loader = PromptLoader()

# Export the prompts as constants for backward compatibility
LANGUAGE_DETECTION_PROMPT = _default_loader.language_detection_prompt
SINGLE_FILE_ANALYSIS_PROMPT = _default_loader.single_file_analysis_prompt
BATCH_ANALYSIS_PROMPT = _default_loader.batch_analysis_prompt
PROJECT_SUMMARY_PROMPT = _default_loader.project_summary_prompt

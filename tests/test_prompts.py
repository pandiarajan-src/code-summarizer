"""Tests for prompts module."""

import pytest

from code_summarizer.prompts import (
    BATCH_ANALYSIS_PROMPT,
    LANGUAGE_DETECTION_PROMPT,
    PROJECT_SUMMARY_PROMPT,
    SINGLE_FILE_ANALYSIS_PROMPT,
)


class TestPrompts:
    """Test cases for prompt templates."""

    def test_language_detection_prompt_structure(self):
        """Test language detection prompt has required placeholders."""
        assert "{files_content}" in LANGUAGE_DETECTION_PROMPT
        assert "JSON" in LANGUAGE_DETECTION_PROMPT
        assert "languages" in LANGUAGE_DETECTION_PROMPT
        assert "confidence" in LANGUAGE_DETECTION_PROMPT

    def test_language_detection_prompt_formatting(self):
        """Test language detection prompt can be formatted correctly."""
        files_content = "def hello(): pass"
        formatted = LANGUAGE_DETECTION_PROMPT.format(files_content=files_content)
        
        assert files_content in formatted
        assert "JSON" in formatted
        assert "{files_content}" not in formatted

    def test_single_file_analysis_prompt_structure(self):
        """Test single file analysis prompt has required placeholders."""
        assert "{filename}" in SINGLE_FILE_ANALYSIS_PROMPT
        assert "{language}" in SINGLE_FILE_ANALYSIS_PROMPT
        assert "{language_lower}" in SINGLE_FILE_ANALYSIS_PROMPT
        assert "{content}" in SINGLE_FILE_ANALYSIS_PROMPT
        assert "JSON" in SINGLE_FILE_ANALYSIS_PROMPT
        assert "functions" in SINGLE_FILE_ANALYSIS_PROMPT
        assert "imports" in SINGLE_FILE_ANALYSIS_PROMPT

    def test_single_file_analysis_prompt_formatting(self):
        """Test single file analysis prompt can be formatted correctly."""
        test_data = {
            "filename": "test.py",
            "language": "Python",
            "language_lower": "python",
            "content": "def hello(): pass"
        }
        
        formatted = SINGLE_FILE_ANALYSIS_PROMPT.format(**test_data)
        
        assert "test.py" in formatted
        assert "Python" in formatted
        assert "python" in formatted
        assert "def hello(): pass" in formatted
        assert "{filename}" not in formatted

    def test_single_file_analysis_prompt_json_structure(self):
        """Test single file analysis prompt defines proper JSON structure."""
        # Check that the prompt contains the expected JSON fields
        expected_fields = [
            '"language"',
            '"purpose"',
            '"complexity"',
            '"functions"',
            '"imports"',
            '"dependencies"',
            '"key_features"',
            '"potential_issues"'
        ]
        
        for field in expected_fields:
            assert field in SINGLE_FILE_ANALYSIS_PROMPT

    def test_batch_analysis_prompt_structure(self):
        """Test batch analysis prompt has required placeholders."""
        assert "{files_info}" in BATCH_ANALYSIS_PROMPT
        assert "JSON" in BATCH_ANALYSIS_PROMPT
        assert "batch_summary" in BATCH_ANALYSIS_PROMPT
        assert "files" in BATCH_ANALYSIS_PROMPT
        assert "relationships" in BATCH_ANALYSIS_PROMPT

    def test_batch_analysis_prompt_formatting(self):
        """Test batch analysis prompt can be formatted correctly."""
        files_info = "file1.py: Python module\nfile2.js: JavaScript file"
        formatted = BATCH_ANALYSIS_PROMPT.format(files_info=files_info)
        
        assert files_info in formatted
        assert "{files_info}" not in formatted
        assert "JSON" in formatted

    def test_batch_analysis_prompt_json_structure(self):
        """Test batch analysis prompt defines proper JSON structure."""
        expected_sections = [
            '"batch_summary"',
            '"main_purpose"',
            '"patterns"',
            '"architecture"',
            '"files"',
            '"relationships"',
            '"from"',
            '"to"',
            '"type"'
        ]
        
        for section in expected_sections:
            assert section in BATCH_ANALYSIS_PROMPT

    def test_project_summary_prompt_structure(self):
        """Test project summary prompt has required placeholders."""
        assert "{total_files}" in PROJECT_SUMMARY_PROMPT
        assert "{languages}" in PROJECT_SUMMARY_PROMPT
        assert "{analysis_summary}" in PROJECT_SUMMARY_PROMPT
        assert "JSON" in PROJECT_SUMMARY_PROMPT

    def test_project_summary_prompt_formatting(self):
        """Test project summary prompt can be formatted correctly."""
        test_data = {
            "total_files": 5,
            "languages": "Python, JavaScript",
            "analysis_summary": "Web application with API endpoints"
        }
        
        formatted = PROJECT_SUMMARY_PROMPT.format(**test_data)
        
        assert "5" in formatted
        assert "Python, JavaScript" in formatted
        assert "Web application with API endpoints" in formatted
        assert "{total_files}" not in formatted

    def test_project_summary_prompt_json_structure(self):
        """Test project summary prompt defines proper JSON structure."""
        expected_sections = [
            '"project_summary"',
            '"type"',
            '"main_purpose"',
            '"architecture"',
            '"key_components"',
            '"technologies"',
            '"complexity_assessment"',
            '"technical_details"',
            '"patterns"',
            '"dependencies"',
            '"entry_points"',
            '"data_flow"',
            '"code_quality"',
            '"strengths"',
            '"areas_for_improvement"',
            '"maintainability"'
        ]
        
        for section in expected_sections:
            assert section in PROJECT_SUMMARY_PROMPT

    def test_prompts_are_non_empty_strings(self):
        """Test all prompts are non-empty strings."""
        prompts = [
            LANGUAGE_DETECTION_PROMPT,
            SINGLE_FILE_ANALYSIS_PROMPT,
            BATCH_ANALYSIS_PROMPT,
            PROJECT_SUMMARY_PROMPT
        ]
        
        for prompt in prompts:
            assert isinstance(prompt, str)
            assert len(prompt.strip()) > 0

    def test_prompts_contain_analysis_instructions(self):
        """Test prompts contain proper analysis instructions."""
        # Language detection should mention programming languages
        assert "programming languages" in LANGUAGE_DETECTION_PROMPT.lower()
        
        # Single file analysis should mention comprehensive analysis
        assert "comprehensive" in SINGLE_FILE_ANALYSIS_PROMPT.lower()
        assert "function" in SINGLE_FILE_ANALYSIS_PROMPT.lower()
        
        # Batch analysis should mention relationships
        assert "relationship" in BATCH_ANALYSIS_PROMPT.lower()
        assert "architecture" in BATCH_ANALYSIS_PROMPT.lower()
        
        # Project summary should mention overall project
        assert "project" in PROJECT_SUMMARY_PROMPT.lower()
        assert "overall" in PROJECT_SUMMARY_PROMPT.lower()

    def test_prompts_specify_json_output(self):
        """Test all prompts explicitly request JSON output."""
        prompts = [
            LANGUAGE_DETECTION_PROMPT,
            SINGLE_FILE_ANALYSIS_PROMPT,
            BATCH_ANALYSIS_PROMPT,
            PROJECT_SUMMARY_PROMPT
        ]
        
        for prompt in prompts:
            assert "JSON" in prompt or "json" in prompt

    def test_single_file_prompt_covers_code_analysis_aspects(self):
        """Test single file prompt covers key code analysis aspects."""
        analysis_aspects = [
            "function",
            "import",
            "dependencies",
            "pattern",
            "issue"
        ]
        
        prompt_lower = SINGLE_FILE_ANALYSIS_PROMPT.lower()
        for aspect in analysis_aspects:
            assert aspect in prompt_lower

    def test_batch_prompt_covers_project_structure(self):
        """Test batch analysis prompt covers project structure analysis."""
        structure_aspects = [
            "architecture",
            "pattern",
            "relationship",
            "dependencies",
            "organization"
        ]
        
        prompt_lower = BATCH_ANALYSIS_PROMPT.lower()
        for aspect in structure_aspects:
            assert aspect in prompt_lower

    def test_project_summary_covers_high_level_analysis(self):
        """Test project summary prompt covers high-level analysis."""
        high_level_aspects = [
            "architecture",
            "component",
            "technologies",  # Fixed: plural form matches the prompt
            "quality",
            "maintainability"
        ]
        
        prompt_lower = PROJECT_SUMMARY_PROMPT.lower()
        for aspect in high_level_aspects:
            assert aspect in prompt_lower
"""Tests for markdown_formatter module."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from code_summarizer.markdown_formatter import MarkdownFormatter


class TestMarkdownFormatter:
    """Test cases for MarkdownFormatter class."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        with patch("code_summarizer.markdown_formatter.Path") as mock_path:
            mock_path.return_value.open.side_effect = FileNotFoundError
            formatter = MarkdownFormatter()
            
            assert formatter.config == {}

    def test_init_with_config_file(self):
        """Test initialization with custom config file."""
        config_data = {
            "markdown": {
                "include_timestamps": True,
                "include_file_sizes": False
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            formatter = MarkdownFormatter(config_path=config_path)
            assert formatter.config == config_data
        finally:
            Path(config_path).unlink()

    def test_extract_project_info(self):
        """Test project information extraction."""
        formatter = MarkdownFormatter()
        
        files_data = [
            {"extension": ".py", "lines": 10, "size": 100, "name": "test.py", "path": "src/test.py"},
            {"extension": ".js", "lines": 5, "size": 50, "name": "script.js", "path": "src/script.js"}
        ]
        
        result = formatter._extract_project_info(files_data)
        
        assert result["name"] == "src"
        assert result["total_files"] == 2
        assert result["total_lines"] == 15
        assert result["total_size"] == 150
        assert "Python" in result["languages"]
        assert "JavaScript" in result["languages"]

    def test_extract_project_info_single_file(self):
        """Test project info extraction with single file."""
        formatter = MarkdownFormatter()
        
        files_data = [
            {"extension": ".py", "lines": 10, "size": 100, "name": "test.py", "path": "test.py"}
        ]
        
        result = formatter._extract_project_info(files_data)
        
        assert result["name"] == "test"
        assert result["total_files"] == 1
        assert result["languages"] == ["Python"]

    def test_extract_project_info_empty(self):
        """Test project info with empty file list."""
        formatter = MarkdownFormatter()
        result = formatter._extract_project_info([])
        assert result["name"] == "Code Analysis"
        assert result["total_files"] == 0

    def test_format_header(self):
        """Test markdown header formatting."""
        formatter = MarkdownFormatter()
        project_info = {"name": "TestProject"}
        
        with patch("code_summarizer.markdown_formatter.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30, 0)
            result = formatter._format_header(project_info)
            
            assert "# Code Analysis: TestProject" in result
            assert "2024-01-15 14:30:00" in result

    def test_format_overview(self):
        """Test overview section formatting."""
        formatter = MarkdownFormatter()
        project_info = {
            "languages": ["Python", "JavaScript"],
            "total_files": 5,
            "total_lines": 250,
            "total_size": 1024
        }
        analysis_results = []
        
        result = formatter._format_overview(project_info, analysis_results)
        
        assert "## 📊 Overview" in result
        assert "Python, JavaScript" in result
        assert "5" in result
        assert "250" in result
        assert "1.0 KB" in result

    def test_format_project_summary_with_detailed_summary(self):
        """Test project summary formatting with detailed LLM results."""
        formatter = MarkdownFormatter()
        analysis_results = [
            {
                "project_summary": {
                    "main_purpose": "Web application for task management",
                    "type": "web application",
                    "architecture": "MVC pattern",
                    "key_components": ["User Authentication", "Task Management", "API Layer"]
                }
            }
        ]
        
        result = formatter._format_project_summary(analysis_results)
        
        assert "## 🎯 Project Summary" in result
        assert "Web application for task management" in result
        assert "web application" in result
        assert "MVC pattern" in result
        assert "User Authentication" in result

    def test_format_project_summary_from_batch_summaries(self):
        """Test project summary from batch summaries when no detailed summary."""
        formatter = MarkdownFormatter()
        analysis_results = [
            {
                "batch_summary": {
                    "main_purpose": "Backend API logic",
                    "patterns": ["REST API", "Database integration"]
                }
            },
            {
                "batch_summary": {
                    "main_purpose": "Frontend components",
                    "patterns": ["React components", "State management"]
                }
            }
        ]
        
        result = formatter._format_project_summary(analysis_results)
        
        assert "## 🎯 Project Summary" in result
        # Check both purposes are present (order may vary due to set operations)
        assert "Backend API logic" in result
        assert "Frontend components" in result
        # Check all patterns are present (order may vary due to set operations)
        assert "REST API" in result
        assert "Database integration" in result
        assert "React components" in result
        assert "State management" in result

    def test_format_file_analysis(self):
        """Test file analysis section formatting."""
        formatter = MarkdownFormatter()
        analysis_results = [
            {
                "files": [
                    {
                        "filename": "test.py",
                        "language": "Python",
                        "purpose": "Test utilities",
                        "complexity": "simple",
                        "line_count": 25,
                        "functions": [
                            {
                                "name": "test_function",
                                "type": "function",
                                "purpose": "Performs unit tests",
                                "line_number": 10
                            }
                        ],
                        "imports": ["unittest", "mock"],
                        "key_features": ["Comprehensive test coverage"]
                    }
                ]
            }
        ]
        
        result = formatter._format_file_analysis(analysis_results)
        
        assert "## 📁 File Analysis" in result
        assert "`test.py`" in result
        assert "Python" in result
        assert "Test utilities" in result
        assert "Simple" in result
        assert "25" in result
        assert "test_function" in result
        assert "line 10" in result
        assert "unittest, mock" in result

    def test_format_single_file_minimal(self):
        """Test single file formatting with minimal data."""
        formatter = MarkdownFormatter()
        file_analysis = {
            "filename": "simple.py",
            "language": "Python",
            "purpose": "Simple script"
        }
        
        result = formatter._format_single_file(file_analysis)
        
        assert "`simple.py`" in result
        assert "Python" in result
        assert "Simple script" in result
        assert "Unknown" in result  # complexity fallback

    def test_format_single_file_with_issues(self):
        """Test single file formatting with potential issues."""
        formatter = MarkdownFormatter()
        file_analysis = {
            "filename": "complex.py",
            "language": "Python",
            "purpose": "Complex module",
            "complexity": "complex",
            "potential_issues": ["Long function", "Missing error handling"]
        }
        
        result = formatter._format_single_file(file_analysis)
        
        assert "⚠️ **Potential Issues**:" in result
        assert "Long function" in result
        assert "Missing error handling" in result

    def test_format_dependencies(self):
        """Test dependencies and relationships formatting."""
        formatter = MarkdownFormatter()
        analysis_results = [
            {
                "relationships": [
                    {
                        "from": "main.py",
                        "to": "utils.py",
                        "type": "imports",
                        "description": "Uses utility functions"
                    },
                    {
                        "from": "app.py", 
                        "to": "models.py",
                        "type": "calls",
                        "description": "Database operations"
                    }
                ]
            }
        ]
        
        result = formatter._format_dependencies(analysis_results)
        
        assert "## 🔗 Dependencies & Relationships" in result
        assert "`main.py`" in result
        assert "`utils.py`" in result
        assert "imports" in result
        assert "Uses utility functions" in result

    def test_format_dependencies_empty(self):
        """Test dependencies formatting when no relationships found."""
        formatter = MarkdownFormatter()
        analysis_results = [{"relationships": []}]
        
        result = formatter._format_dependencies(analysis_results)
        
        assert "No explicit inter-file relationships detected" in result

    def test_format_technical_details(self):
        """Test technical details section formatting."""
        formatter = MarkdownFormatter()
        analysis_results = [
            {
                "technical_details": {
                    "patterns": ["Factory Pattern", "Observer Pattern"],
                    "dependencies": ["requests", "numpy"]
                },
                "project_summary": {
                    "technologies": ["Flask", "SQLite"]
                },
                "batch_summary": {
                    "patterns": ["MVC Pattern"]
                }
            }
        ]
        
        result = formatter._format_technical_details(analysis_results)
        
        assert "## 🔧 Technical Details" in result
        assert "### Design Patterns" in result
        assert "Factory Pattern" in result
        assert "### Technologies & Frameworks" in result
        assert "Flask" in result
        assert "### External Dependencies" in result
        assert "requests" in result

    def test_format_technical_details_empty(self):
        """Test technical details when no data available."""
        formatter = MarkdownFormatter()
        analysis_results = [{}]
        
        result = formatter._format_technical_details(analysis_results)
        
        assert result == ""

    def test_extension_to_language(self):
        """Test file extension to language mapping."""
        formatter = MarkdownFormatter()
        
        assert formatter._extension_to_language(".py") == "Python"
        assert formatter._extension_to_language(".JS") == "JavaScript"
        assert formatter._extension_to_language(".cpp") == "C++"
        assert formatter._extension_to_language(".unknown") == "Unknown"

    def test_format_bytes(self):
        """Test byte formatting utility."""
        formatter = MarkdownFormatter()
        
        assert formatter._format_bytes(512) == "512.0 B"
        assert formatter._format_bytes(1536) == "1.5 KB"
        assert formatter._format_bytes(1048576) == "1.0 MB"
        assert formatter._format_bytes(1073741824) == "1.0 GB"

    def test_format_results_integration(self):
        """Test complete markdown formatting integration."""
        formatter = MarkdownFormatter()
        
        files_data = [
            {
                "extension": ".py", 
                "lines": 10, 
                "size": 100, 
                "name": "test.py", 
                "path": "test.py"
            }
        ]
        
        analysis_results = [
            {
                "files": [
                    {
                        "filename": "test.py",
                        "language": "Python", 
                        "purpose": "Test file",
                        "complexity": "simple"
                    }
                ],
                "batch_summary": {
                    "main_purpose": "Testing framework",
                    "patterns": ["Unit testing"]
                },
                "relationships": []
            }
        ]
        
        with patch("code_summarizer.markdown_formatter.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30, 0)
            result = formatter.format_results(files_data, analysis_results)
            
            # Check that all main sections are present
            assert "# Code Analysis" in result
            assert "## 📊 Overview" in result
            assert "## 📁 File Analysis" in result
            assert "## 🔧 Technical Details" in result
            assert "`test.py`" in result
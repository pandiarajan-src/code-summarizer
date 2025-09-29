from unittest.mock import mock_open
from unittest.mock import patch

from app.utils.markdown_formatter import MarkdownFormatter


class TestMarkdownFormatter:
    """Test markdown formatter functionality."""

    @patch("pathlib.Path.open", mock_open(read_data="config:\n  key: value"))
    def test_init_with_config(self):
        """Test initialization with configuration file."""
        formatter = MarkdownFormatter("test_config.yaml")
        assert formatter.config == {"config": {"key": "value"}}

    @patch("pathlib.Path.open", side_effect=FileNotFoundError)
    def test_init_without_config(self, mock_file):
        """Test initialization without configuration file."""
        formatter = MarkdownFormatter("nonexistent.yaml")
        assert formatter.config == {}

    def test_extract_project_info(self):
        """Test project information extraction."""
        formatter = MarkdownFormatter.__new__(MarkdownFormatter)

        files_data = [
            {
                "path": "src/main.py",
                "name": "main.py",
                "extension": ".py",
                "lines": 50,
                "size": 1000,
            },
            {
                "path": "frontend/app.js",
                "name": "app.js",
                "extension": ".js",
                "lines": 30,
                "size": 800,
            },
        ]

        project_info = formatter._extract_project_info(files_data)

        assert project_info["name"] == "src"
        assert "Python" in project_info["languages"]
        assert "JavaScript" in project_info["languages"]
        assert project_info["total_files"] == 2
        assert project_info["total_lines"] == 80
        assert project_info["total_size"] == 1800

    def test_extract_project_info_empty(self):
        """Test project info extraction with empty files."""
        formatter = MarkdownFormatter.__new__(MarkdownFormatter)

        project_info = formatter._extract_project_info([])

        assert project_info["name"] == "Code Analysis"
        assert project_info["languages"] == []
        assert project_info["total_files"] == 0

    def test_format_header(self):
        """Test header formatting."""
        formatter = MarkdownFormatter.__new__(MarkdownFormatter)

        project_info = {"name": "My Project"}

        with patch("app.utils.markdown_formatter.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2023-12-01 10:30:00"
            header = formatter._format_header(project_info)

        assert "# Code Analysis: My Project" in header
        assert "*Generated on 2023-12-01 10:30:00*" in header

    def test_format_overview(self):
        """Test overview section formatting."""
        formatter = MarkdownFormatter.__new__(MarkdownFormatter)

        project_info = {
            "languages": ["Python", "JavaScript"],
            "total_files": 5,
            "total_lines": 500,
            "total_size": 10240,
        }

        with patch("app.utils.markdown_formatter.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2023-12-01"
            overview = formatter._format_overview(project_info, [])

        assert "## 📊 Overview" in overview
        assert "**Languages**: Python, JavaScript" in overview
        assert "**Total Files**: 5" in overview
        assert "**Total Lines**: 500" in overview
        assert "10.0 KB" in overview  # Size formatting

    def test_format_project_summary_from_batch(self):
        """Test project summary formatting from batch results."""
        formatter = MarkdownFormatter.__new__(MarkdownFormatter)

        analysis_results = [
            {
                "batch_summary": {
                    "main_purpose": "Web backend API",
                    "patterns": ["MVC", "REST API"],
                }
            },
            {
                "batch_summary": {
                    "main_purpose": "Frontend UI components",
                    "patterns": ["Component-based"],
                }
            },
        ]

        summary = formatter._format_project_summary(analysis_results)

        assert "## 🎯 Project Summary" in summary
        assert (
            "Web backend API; Frontend UI components" in summary
            or "Frontend UI components; Web backend API" in summary
        )
        # Check that all patterns are present (order may vary)
        assert "MVC" in summary
        assert "REST API" in summary
        assert "Component-based" in summary

    def test_format_project_summary_detailed(self):
        """Test detailed project summary formatting."""
        formatter = MarkdownFormatter.__new__(MarkdownFormatter)

        analysis_results = [
            {
                "project_summary": {
                    "main_purpose": "E-commerce platform",
                    "type": "Web application",
                    "architecture": "Microservices",
                    "key_components": [
                        "User service",
                        "Product catalog",
                        "Payment gateway",
                    ],
                }
            }
        ]

        summary = formatter._format_project_summary(analysis_results)

        assert "## 🎯 Project Summary" in summary
        assert "**Purpose**: E-commerce platform" in summary
        assert "**Type**: Web application" in summary
        assert "**Architecture**: Microservices" in summary
        assert "- User service" in summary
        assert "- Product catalog" in summary

    def test_format_single_file(self):
        """Test single file analysis formatting."""
        formatter = MarkdownFormatter.__new__(MarkdownFormatter)

        file_analysis = {
            "filename": "main.py",
            "language": "Python",
            "purpose": "Main application entry point",
            "complexity": "medium",
            "line_count": 100,
            "functions": [
                {
                    "name": "main",
                    "type": "function",
                    "purpose": "Application entry point",
                    "line_number": 50,
                },
                {
                    "name": "setup_logging",
                    "type": "function",
                    "purpose": "Configure application logging",
                },
            ],
            "imports": ["os", "sys", "logging"],
            "key_features": ["Command line interface", "Logging configuration"],
            "potential_issues": ["Hard-coded configuration", "No error handling"],
        }

        md = formatter._format_single_file(file_analysis)

        assert "### `main.py`" in md
        assert "**Language**: Python" in md
        assert "**Purpose**: Main application entry point" in md
        assert "**Complexity**: Medium" in md
        assert "**Lines**: 100" in md
        assert "**`main`** (function) (line 50): Application entry point" in md
        assert "**`setup_logging`** (function): Configure application logging" in md
        assert "**Imports**: os, sys, logging" in md
        assert "- Command line interface" in md
        assert "⚠️ **Potential Issues**:" in md
        assert "- Hard-coded configuration" in md

    def test_format_file_analysis(self):
        """Test file analysis section formatting."""
        formatter = MarkdownFormatter.__new__(MarkdownFormatter)

        analysis_results = [
            {
                "files": [
                    {
                        "filename": "main.py",
                        "language": "Python",
                        "purpose": "Main module",
                        "complexity": "low",
                    }
                ]
            }
        ]

        md = formatter._format_file_analysis(analysis_results)

        assert "## 📁 File Analysis" in md
        assert "### `main.py`" in md

    def test_format_dependencies(self):
        """Test dependencies section formatting."""
        formatter = MarkdownFormatter.__new__(MarkdownFormatter)

        analysis_results = [
            {
                "relationships": [
                    {
                        "from": "main.py",
                        "to": "utils.py",
                        "type": "imports",
                        "description": "Uses utility functions",
                    },
                    {"from": "app.py", "to": "config.py", "type": "imports"},
                ]
            }
        ]

        md = formatter._format_dependencies(analysis_results)

        assert "## 🔗 Dependencies & Relationships" in md
        assert "### Inter-file Relationships" in md
        assert "**`main.py`** imports **`utils.py`**: Uses utility functions" in md
        assert "**`app.py`** imports **`config.py`**" in md

    def test_format_dependencies_empty(self):
        """Test dependencies section with no relationships."""
        formatter = MarkdownFormatter.__new__(MarkdownFormatter)

        analysis_results = [{"relationships": []}]

        md = formatter._format_dependencies(analysis_results)

        assert "## 🔗 Dependencies & Relationships" in md
        assert "No explicit inter-file relationships detected." in md

    def test_format_technical_details(self):
        """Test technical details section formatting."""
        formatter = MarkdownFormatter.__new__(MarkdownFormatter)

        analysis_results = [
            {
                "technical_details": {
                    "patterns": ["Factory Pattern", "Singleton"],
                    "dependencies": ["requests", "flask"],
                },
                "project_summary": {"technologies": ["Python", "Flask", "SQLAlchemy"]},
                "batch_summary": {"patterns": ["MVC"]},
            }
        ]

        md = formatter._format_technical_details(analysis_results)

        assert "## 🔧 Technical Details" in md
        assert "### Design Patterns" in md
        assert "- Factory Pattern" in md
        assert "- Singleton" in md
        assert "- MVC" in md
        assert "### Technologies & Frameworks" in md
        assert "- Python" in md
        assert "### External Dependencies" in md
        assert "- requests" in md

    def test_format_technical_details_empty(self):
        """Test technical details section with no data."""
        formatter = MarkdownFormatter.__new__(MarkdownFormatter)

        analysis_results = [{}]

        md = formatter._format_technical_details(analysis_results)

        assert md == ""

    def test_format_results_complete(self):
        """Test complete markdown formatting."""
        formatter = MarkdownFormatter.__new__(MarkdownFormatter)

        files_data = [
            {
                "path": "main.py",
                "name": "main.py",
                "extension": ".py",
                "lines": 50,
                "size": 1000,
            }
        ]

        analysis_results = [
            {
                "batch_summary": {"main_purpose": "Simple script"},
                "files": [
                    {
                        "filename": "main.py",
                        "language": "Python",
                        "purpose": "Script entry point",
                        "complexity": "low",
                    }
                ],
            }
        ]

        with patch("app.utils.markdown_formatter.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.side_effect = [
                "2023-12-01 10:30:00",
                "2023-12-01",
            ]
            md = formatter.format_results(files_data, analysis_results)

        assert "# Code Analysis: main" in md
        assert "## 📊 Overview" in md
        assert (
            "## 🎯 Project Summary" not in md
        )  # Single file doesn't get project summary
        assert "## 📁 File Analysis" in md
        assert "### `main.py`" in md

    def test_extension_to_language(self):
        """Test extension to language mapping."""
        formatter = MarkdownFormatter.__new__(MarkdownFormatter)

        assert formatter._extension_to_language(".py") == "Python"
        assert formatter._extension_to_language(".js") == "JavaScript"
        assert formatter._extension_to_language(".ts") == "TypeScript"
        assert formatter._extension_to_language(".unknown") == "Unknown"

    def test_format_bytes(self):
        """Test byte formatting."""
        formatter = MarkdownFormatter.__new__(MarkdownFormatter)

        assert formatter._format_bytes(500) == "500.0 B"
        assert formatter._format_bytes(1536) == "1.5 KB"
        assert formatter._format_bytes(1048576) == "1.0 MB"
        assert formatter._format_bytes(1073741824) == "1.0 GB"

"""Markdown formatter for generating structured code analysis reports."""

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class MarkdownFormatter:
    """Generates structured markdown reports from code analysis results."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize markdown formatter with configuration.

        Args:
            config_path: Path to configuration YAML file.
        """
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with Path(config_path).open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}

    def format_results(
        self, files_data: list[dict[str, Any]], analysis_results: list[dict[str, Any]]
    ) -> str:
        """Format analysis results into markdown report

        Args:
            files_data: Original file data
            analysis_results: LLM analysis results for each batch

        Returns:
            Formatted markdown string
        """
        # Extract project information
        project_info = self._extract_project_info(files_data)

        # Build markdown content
        sections = []

        # Header
        sections.append(self._format_header(project_info))

        # Overview
        sections.append(self._format_overview(project_info, analysis_results))

        # Project Summary (if multiple files)
        if len(files_data) > 1:
            sections.append(self._format_project_summary(analysis_results))

        # File Analysis
        sections.append(self._format_file_analysis(analysis_results))

        # Dependencies & Relationships
        if len(files_data) > 1:
            sections.append(self._format_dependencies(analysis_results))

        # Technical Details
        sections.append(self._format_technical_details(analysis_results))

        return "\n\n".join(sections)

    def _extract_project_info(self, files_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract high-level project information"""
        languages = set()
        total_lines = 0
        total_size = 0

        for file_data in files_data:
            # Map extension to language
            ext = file_data["extension"].lower()
            lang = self._extension_to_language(ext)
            if lang != "Unknown":
                languages.add(lang)

            total_lines += file_data["lines"]
            total_size += file_data["size"]

        # Determine project name (from first file or directory)
        if files_data:
            first_file = files_data[0]
            file_path = Path(first_file["path"])
            if len(file_path.parts) > 1:
                project_name = file_path.parts[0]
            else:
                project_name = file_path.stem
        else:
            project_name = "Code Analysis"

        return {
            "name": project_name,
            "languages": sorted(list(languages)),
            "total_files": len(files_data),
            "total_lines": total_lines,
            "total_size": total_size,
        }

    def _format_header(self, project_info: dict[str, Any]) -> str:
        """Format markdown header"""
        return f"""# Code Analysis: {project_info["name"]}

*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*"""

    def _format_overview(
        self, project_info: dict[str, Any], analysis_results: list[dict[str, Any]]
    ) -> str:
        """Format overview section"""
        languages_str = (
            ", ".join(project_info["languages"])
            if project_info["languages"]
            else "Unknown"
        )

        return f"""## 📊 Overview

- **Languages**: {languages_str}
- **Total Files**: {project_info["total_files"]}
- **Total Lines**: {project_info["total_lines"]:,}
- **Total Size**: {self._format_bytes(project_info["total_size"])}
- **Analysis Date**: {datetime.now().strftime("%Y-%m-%d")}"""

    def _format_project_summary(self, analysis_results: list[dict[str, Any]]) -> str:
        """Format project summary section"""
        # Try to get project summary from LLM results
        project_summary = None
        for result in analysis_results:
            if isinstance(result, dict) and "project_summary" in result:
                project_summary = result["project_summary"]
                break

        if not project_summary:
            # Extract from batch summaries
            purposes = []
            patterns = []

            for result in analysis_results:
                if isinstance(result, dict) and "batch_summary" in result:
                    batch_summary = result["batch_summary"]
                    if "main_purpose" in batch_summary:
                        purposes.append(batch_summary["main_purpose"])
                    if "patterns" in batch_summary:
                        patterns.extend(batch_summary["patterns"])

            return f"""## 🎯 Project Summary

**Main Purpose**: {"; ".join(set(purposes)) if purposes else "Code analysis and documentation"}

**Key Patterns**: {", ".join(set(patterns)) if patterns else "Standard code organization"}"""

        # Format detailed project summary
        summary_md = "## 🎯 Project Summary\n\n"

        if "main_purpose" in project_summary:
            summary_md += f"**Purpose**: {project_summary['main_purpose']}\n\n"

        if "type" in project_summary:
            summary_md += f"**Type**: {project_summary['type']}\n\n"

        if "architecture" in project_summary:
            summary_md += f"**Architecture**: {project_summary['architecture']}\n\n"

        if "key_components" in project_summary:
            components = project_summary["key_components"]
            if components:
                summary_md += "**Key Components**:\n"
                for comp in components:
                    summary_md += f"- {comp}\n"
                summary_md += "\n"

        return summary_md.rstrip()

    def _format_file_analysis(self, analysis_results: list[dict[str, Any]]) -> str:
        """Format detailed file analysis section"""
        md = "## 📁 File Analysis\n\n"

        for result in analysis_results:
            if not isinstance(result, dict) or "files" not in result:
                continue

            for file_analysis in result["files"]:
                md += self._format_single_file(file_analysis)
                md += "\n"

        return md.rstrip()

    def _format_single_file(self, file_analysis: dict[str, Any]) -> str:
        """Format analysis for a single file."""
        filename = file_analysis.get("filename", "Unknown")
        language = file_analysis.get("language", "Unknown")
        purpose = file_analysis.get("purpose", "No description available")
        complexity = file_analysis.get("complexity", "unknown")

        md = f"### `{filename}`\n\n"
        md += f"**Language**: {language}  \n"
        md += f"**Purpose**: {purpose}  \n"
        md += f"**Complexity**: {complexity.title()}  \n"

        # Add file metadata if available
        if "line_count" in file_analysis:
            md += f"**Lines**: {file_analysis['line_count']}  \n"

        # Add functions/methods/classes
        functions = file_analysis.get("functions", [])
        if functions:
            md += "\n**Functions/Methods/Classes**:\n\n"
            for func in functions:
                func_name = func.get("name", "unnamed")
                func_type = func.get("type", "function")
                func_purpose = func.get("purpose", "No description")
                func_description = func.get("description", "")
                func_parameters = func.get("parameters", [])
                line_num = func.get("line_number", "")

                line_info = f" (line {line_num})" if line_num else ""
                md += f"- **`{func_name}`** ({func_type}){line_info}: {func_purpose}\n"

                # Add detailed description if available
                if func_description and func_description != func_purpose:
                    md += f"  - *Description*: {func_description}\n"

                # Add parameters if available
                if func_parameters:
                    params_str = ", ".join(func_parameters)
                    md += f"  - *Parameters*: `{params_str}`\n"

        # Add global variables
        global_vars = file_analysis.get("global_variables", [])
        if global_vars:
            md += f"\n**Global Variables**: {', '.join(global_vars)}\n"

        # Add imports
        imports = file_analysis.get("imports", [])
        if imports:
            md += f"\n**Imports**: {', '.join(imports)}\n"

        # Add external dependencies
        dependencies = file_analysis.get("dependencies", [])
        if dependencies:
            md += f"\n**External Dependencies**: {', '.join(dependencies)}\n"

        # Add key features
        features = file_analysis.get("key_features", [])
        if features:
            md += "\n**Key Features**:\n"
            for feature in features:
                md += f"- {feature}\n"

        # Add potential issues
        issues = file_analysis.get("potential_issues", [])
        if issues:
            md += "\n⚠️ **Potential Issues**:\n"
            for issue in issues:
                md += f"- {issue}\n"

        return md

    def _format_dependencies(self, analysis_results: list[dict[str, Any]]) -> str:
        """Format dependencies and relationships section."""
        md = "## 🔗 Dependencies & Relationships\n\n"

        # Collect all relationships
        relationships = []
        for result in analysis_results:
            if isinstance(result, dict) and "relationships" in result:
                relationships.extend(result["relationships"])

        if relationships:
            md += "### Inter-file Relationships\n\n"
            for rel in relationships:
                from_file = rel.get("from", "unknown")
                to_file = rel.get("to", "unknown")
                rel_type = rel.get("type", "unknown")
                description = rel.get("description", "")

                md += f"- **`{from_file}`** {rel_type} **`{to_file}`**"
                if description:
                    md += f": {description}"
                md += "\n"
        else:
            md += "No explicit inter-file relationships detected.\n"

        return md

    def _format_technical_details(self, analysis_results: list[dict[str, Any]]) -> str:
        """Format technical details section."""
        md = "## 🔧 Technical Details\n\n"

        # Collect technical information
        all_patterns = []
        all_technologies = []
        all_dependencies = []

        for result in analysis_results:
            if isinstance(result, dict):
                # From project summary
                if "technical_details" in result:
                    tech_details = result["technical_details"]
                    all_patterns.extend(tech_details.get("patterns", []))
                    all_dependencies.extend(tech_details.get("dependencies", []))

                if "project_summary" in result:
                    proj_summary = result["project_summary"]
                    all_technologies.extend(proj_summary.get("technologies", []))

                # From batch summaries
                if "batch_summary" in result:
                    batch_summary = result["batch_summary"]
                    all_patterns.extend(batch_summary.get("patterns", []))

        # Remove duplicates and format
        unique_patterns = list(set(all_patterns))
        unique_technologies = list(set(all_technologies))
        unique_dependencies = list(set(all_dependencies))

        if unique_patterns:
            md += "### Design Patterns\n"
            for pattern in unique_patterns:
                md += f"- {pattern}\n"
            md += "\n"

        if unique_technologies:
            md += "### Technologies & Frameworks\n"
            for tech in unique_technologies:
                md += f"- {tech}\n"
            md += "\n"

        if unique_dependencies:
            md += "### External Dependencies\n"
            for dep in unique_dependencies:
                md += f"- {dep}\n"
            md += "\n"

        return md.rstrip() if md != "## 🔧 Technical Details\n\n" else ""

    def _extension_to_language(self, extension: str) -> str:
        """Map file extension to programming language name."""
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

    def _format_bytes(self, byte_count: int) -> str:
        """Format byte count as human-readable string."""
        count = float(byte_count)
        for unit in ["B", "KB", "MB", "GB"]:
            if count < 1024:
                return f"{count:.1f} {unit}"
            count /= 1024
        return f"{count:.1f} TB"

"""
Prompt templates for LLM-based code analysis
"""

LANGUAGE_DETECTION_PROMPT = """
Analyze the following code files and identify the programming languages used.

Files:
{files_content}

Please respond with a JSON object containing:
- "languages": array of detected programming languages
- "confidence": confidence level (1-10)
- "details": brief explanation of detection

Format your response as valid JSON only.
"""

SINGLE_FILE_ANALYSIS_PROMPT = """
Analyze the following source code file and provide a comprehensive summary.

File: {filename}
Language: {language}
Content:
```{language_lower}
{content}
```

Please provide a detailed analysis in the following JSON format:
{{
    "language": "detected programming language",
    "purpose": "brief description of what this file does",
    "complexity": "simple|moderate|complex",
    "functions": [
        {{
            "name": "function_name",
            "type": "function|method|class",
            "purpose": "what this function does",
            "parameters": ["param1", "param2"],
            "line_number": 123
        }}
    ],
    "imports": ["import1", "import2"],
    "dependencies": ["external dependencies identified"],
    "key_features": ["notable features or patterns"],
    "potential_issues": ["any code issues or concerns"]
}}

Provide detailed analysis focusing on:
1. Function/method/class definitions and their purposes
2. Import statements and dependencies
3. Code structure and patterns
4. Potential issues or improvements
"""

BATCH_ANALYSIS_PROMPT = """
Analyze this batch of source code files from a software project. 

Files in this batch:
{files_info}

For each file, provide analysis following this structure, then provide an overall summary.

Respond with JSON in this format:
{{
    "batch_summary": {{
        "main_purpose": "overall purpose of this batch of files",
        "patterns": ["common patterns across files"],
        "architecture": "brief description of code architecture"
    }},
    "files": [
        {{
            "filename": "file1.py",
            "language": "Python", 
            "purpose": "what this file does",
            "complexity": "simple|moderate|complex",
            "functions": [
                {{
                    "name": "function_name",
                    "type": "function|method|class",
                    "purpose": "what this does",
                    "line_number": 123
                }}
            ],
            "imports": ["dependencies"],
            "key_features": ["notable aspects"]
        }}
    ],
    "relationships": [
        {{
            "from": "file1.py",
            "to": "file2.py", 
            "type": "imports|calls|extends",
            "description": "nature of relationship"
        }}
    ]
}}

Focus on:
1. Individual file analysis with functions/classes/methods
2. Cross-file relationships and dependencies
3. Overall architecture and patterns
4. Code organization and structure
"""

PROJECT_SUMMARY_PROMPT = """
Based on the analysis of all files in this project, provide a comprehensive project summary.

Project Information:
- Total Files: {total_files}
- Languages: {languages}
- Analysis Results: {analysis_summary}

Provide a JSON response with:
{{
    "project_summary": {{
        "type": "web application|library|cli tool|mobile app|etc",
        "main_purpose": "what this project does",
        "architecture": "overall architecture description", 
        "key_components": ["main components/modules"],
        "technologies": ["frameworks and libraries used"],
        "complexity_assessment": "simple|moderate|complex"
    }},
    "technical_details": {{
        "patterns": ["design patterns used"],
        "dependencies": ["major external dependencies"],
        "entry_points": ["main files or entry points"],
        "data_flow": "how data flows through the system"
    }},
    "code_quality": {{
        "strengths": ["positive aspects"],
        "areas_for_improvement": ["suggestions for improvement"],
        "maintainability": "high|medium|low"
    }}
}}

Provide insights into the overall project structure, purpose, and quality.
"""
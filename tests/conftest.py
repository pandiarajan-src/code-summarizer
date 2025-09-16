"""Global pytest configuration and fixtures."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(scope="session")
def test_data_dir():
    """Return path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def temp_dir():
    """Create and clean up temporary directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_python_code():
    """Return sample Python code for testing."""
    return '''
def hello_world():
    """Print hello world message."""
    print("Hello, world!")
    return "Hello, world!"

class Calculator:
    """Simple calculator class."""

    def add(self, a, b):
        """Add two numbers."""
        return a + b

    def multiply(self, a, b):
        """Multiply two numbers."""
        return a * b

if __name__ == "__main__":
    hello_world()
    calc = Calculator()
    result = calc.add(2, 3)
    print(f"2 + 3 = {result}")
'''


@pytest.fixture
def sample_javascript_code():
    """Return sample JavaScript code for testing."""
    return '''
function greet(name) {
    return `Hello, ${name}!`;
}

class Person {
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }

    introduce() {
        return `Hi, I'm ${this.name} and I'm ${this.age} years old.`;
    }
}

// Usage
const person = new Person("Alice", 30);
console.log(person.introduce());
console.log(greet("World"));
'''


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "purpose": "Test script for demonstration",
        "complexity": "low",
        "language": "Python",
        "functions": [
            {
                "name": "hello_world",
                "type": "function",
                "purpose": "Prints hello world message",
                "line_number": 2
            }
        ],
        "classes": [
            {
                "name": "Calculator",
                "type": "class",
                "purpose": "Simple calculator for basic operations",
                "line_number": 7
            }
        ],
        "imports": [],
        "key_features": ["Command line output", "Object-oriented design"],
        "potential_issues": []
    }


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        "OPENAI_API_KEY": "test-api-key",
        "OPENAI_BASE_URL": "https://api.openai.com/v1",
        "MODEL_NAME": "gpt-4o"
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def sample_config():
    """Return sample configuration dictionary."""
    return {
        "llm": {
            "model": "gpt-4o",
            "max_tokens": 4000,
            "temperature": 0.1,
            "max_context_tokens": 128000
        },
        "file_processing": {
            "supported_extensions": [".py", ".js", ".ts", ".java", ".cpp"],
            "exclude_patterns": ["__pycache__", "*.pyc", "node_modules"]
        },
        "analysis": {
            "enable_batch_processing": True,
            "max_batch_size": 10,
            "enable_markdown_output": True
        }
    }


# Set up test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "api: API-related tests")
    config.addinivalue_line("markers", "cli: CLI-related tests")


# Skip tests that require API key if not provided
def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle API key requirements."""
    skip_api = pytest.mark.skip(reason="OPENAI_API_KEY not set")

    for item in items:
        if "integration" in item.keywords and not os.getenv("OPENAI_API_KEY"):
            # Only skip integration tests if they specifically test API functionality
            if "api" in item.keywords or "llm" in item.keywords:
                item.add_marker(skip_api)
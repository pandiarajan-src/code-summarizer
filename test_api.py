#!/usr/bin/env python3
"""Test script for the Code Summarizer API."""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_simple_analysis():
    """Test simple file analysis."""

    # Simple Python code
    sample_code = """def hello():
    print("Hello World!")
    return "Hello World!"

if __name__ == "__main__":
    hello()"""

    payload = {
        "files": [
            {
                "filename": "hello.py",
                "content": sample_code,
                "file_type": ".py"
            }
        ],
        "output_format": "json",
        "verbose": True
    }

    print("Testing simple analysis...")
    response = requests.post(f"{BASE_URL}/analyze", json=payload)

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ Analysis successful!")
        print(f"Files analyzed: {result.get('files_analyzed', 0)}")
        print(f"Total tokens: {result.get('total_tokens_used', 0)}")
    else:
        print("❌ Analysis failed!")
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_simple_analysis()
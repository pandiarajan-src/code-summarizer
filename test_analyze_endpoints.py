#!/usr/bin/env python
"""
Test script for analyze endpoints
Tests the fixed configuration bridge between Pydantic settings and legacy modules
"""

import requests
import json
import sys
from pathlib import Path

def test_analyze_endpoints():
    """Test all analyze endpoints"""
    base_url = "http://127.0.0.1:8000"

    print("🧪 Testing Code Summarizer Analyze Endpoints")
    print("=" * 60)

    # Test 1: Validate endpoint (simplest)
    print("\n1. Testing /api/analyze/validate endpoint...")
    try:
        # Create a simple test file
        test_content = '''# Simple Python test
def hello():
    return "Hello, World!"
'''

        test_file = Path("temp_validate_test.py")
        test_file.write_text(test_content)

        with open(test_file, 'rb') as f:
            files = {'files': f}
            response = requests.post(
                f"{base_url}/api/analyze/validate",
                files=files,
                timeout=15
            )

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print("   ✅ Validate endpoint working!")
            result = response.json()
            print(f"   Files validated: {result.get('total_files', 0)}")
            print(f"   All valid: {result.get('all_valid', False)}")
        else:
            print("   ❌ Validate endpoint failed")
            print(f"   Error: {response.text}")

        # Clean up
        test_file.unlink()

    except Exception as e:
        print(f"   ❌ Validate test error: {e}")

    # Test 2: Upload endpoint (actual analysis)
    print("\n2. Testing /api/analyze/upload endpoint...")
    try:
        # Create a simple test file
        test_content = '''# Simple Python test for analysis
def calculate_sum(a, b):
    """Calculate the sum of two numbers."""
    return a + b

def main():
    """Main function."""
    result = calculate_sum(5, 3)
    print(f"Sum: {result}")

if __name__ == "__main__":
    main()
'''

        test_file = Path("temp_analysis_test.py")
        test_file.write_text(test_content)

        with open(test_file, 'rb') as f:
            files = {'files': f}
            data = {
                'output_format': 'json',
                'verbose': 'false'
            }

            response = requests.post(
                f"{base_url}/api/analyze/upload",
                files=files,
                data=data,
                timeout=60  # Longer timeout for analysis
            )

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print("   ✅ Upload analysis endpoint working!")
            result = response.json()
            print(f"   Analysis ID: {result.get('analysis_id', 'N/A')}")
            print(f"   Files analyzed: {result.get('files_analyzed', 0)}")
            print(f"   Success: {result.get('success', False)}")

            # Check if we have batch results
            batch_results = result.get('batch_results', [])
            if batch_results:
                print(f"   Batch results count: {len(batch_results)}")
                if batch_results[0].get('analysis_results'):
                    print("   ✅ Got analysis results from LLM!")
                else:
                    print("   ⚠️  No analysis results in batch")
            else:
                print("   ⚠️  No batch results")

        else:
            print("   ❌ Upload analysis endpoint failed")
            try:
                error_details = response.json()
                print(f"   Error type: {error_details.get('type', 'Unknown')}")
                print(f"   Error message: {error_details.get('message', 'No message')}")
                if 'details' in error_details:
                    print(f"   Details: {error_details['details']}")
            except:
                print(f"   Raw error: {response.text}")

        # Clean up
        test_file.unlink()

    except Exception as e:
        print(f"   ❌ Upload test error: {e}")

    # Test 3: Get supported types
    print("\n3. Testing /api/analyze/supported-types endpoint...")
    try:
        response = requests.get(f"{base_url}/api/analyze/supported-types", timeout=10)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print("   ✅ Supported types endpoint working!")
            result = response.json()
            extensions = result.get('supported_extensions', [])
            print(f"   Supported extensions: {len(extensions)} types")
            print(f"   Examples: {extensions[:5]}...")
        else:
            print("   ❌ Supported types endpoint failed")

    except Exception as e:
        print(f"   ❌ Supported types test error: {e}")

    # Test 4: Get config
    print("\n4. Testing /api/analyze/config endpoint...")
    try:
        response = requests.get(f"{base_url}/api/analyze/config", timeout=10)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print("   ✅ Config endpoint working!")
            result = response.json()
            config = result.get('config', {})
            print(f"   Config sections: {list(config.keys())}")

            # Check LLM config
            llm_config = config.get('llm', {})
            if llm_config:
                print(f"   LLM model: {llm_config.get('model', 'N/A')}")
                print(f"   API key configured: {'***' if llm_config.get('api_key') else 'NOT_SET'}")
                print(f"   Base URL: {llm_config.get('base_url', 'Default')}")
        else:
            print("   ❌ Config endpoint failed")

    except Exception as e:
        print(f"   ❌ Config test error: {e}")

    return True

def main():
    """Main test function"""
    print("🧪 Code Summarizer Analyze Endpoints Test")
    print("=" * 70)

    # First check if API is running
    try:
        response = requests.get("http://127.0.0.1:8000/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ API health check failed!")
            print("Make sure the API server is running")
            return False
    except Exception:
        print("❌ Cannot connect to API server!")
        print("Make sure the API server is running on port 8000")
        return False

    print("✅ API server is running")

    success = test_analyze_endpoints()

    print("\n" + "=" * 70)
    if success:
        print("🎉 Analyze endpoints test completed!")
        print("\nIf any endpoints failed, check the API server logs for detailed error messages.")
    else:
        print("❌ Some tests failed!")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
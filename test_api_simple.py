#!/usr/bin/env python
"""
Simple API Test Script
Quick test to validate API functionality and identify issues
"""

import requests
import json
import sys
from pathlib import Path

def test_api():
    """Test the API with simple requests"""
    base_url = "http://127.0.0.1:8000"

    print("🧪 Testing Code Summarizer API")
    print("=" * 40)

    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print("   ❌ Health check failed")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot connect to API: {e}")
        print("   Make sure the API server is running on port 8000")
        return False

    # Test 2: Get supported types
    print("\n2. Testing supported types endpoint...")
    try:
        response = requests.get(f"{base_url}/api/analyze/supported-types", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Supported types endpoint working")
            types = response.json()
            print(f"   Supported extensions: {types.get('supported_extensions', [])[:5]}...")
        else:
            print("   ❌ Supported types endpoint failed")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: File upload with simple Python file
    print("\n3. Testing file upload...")
    try:
        # Create a simple test file
        test_content = '''# Simple test file
def hello():
    """Say hello"""
    return "Hello, World!"

if __name__ == "__main__":
    print(hello())
'''

        test_file = Path("temp_test.py")
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
                timeout=30
            )

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print("   ✅ File upload test passed")
            result = response.json()
            print(f"   Analysis completed successfully")
            print(f"   Response keys: {list(result.keys())}")
        else:
            print("   ❌ File upload test failed")
            print(f"   Error: {response.text}")
            if response.status_code == 500:
                print("\n   🔍 This is a 500 Internal Server Error!")
                print("   Common causes:")
                print("   - Missing or invalid OpenAI API key")
                print("   - Missing dependencies")
                print("   - Configuration file issues")
                print("   - PYTHONPATH not set correctly")

        # Clean up
        test_file.unlink()

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    return True

if __name__ == "__main__":
    success = test_api()
    if not success:
        print("\n" + "=" * 40)
        print("❌ API tests failed!")
        print("\nNext steps:")
        print("1. Run 'python debug_api.py' for detailed diagnostics")
        print("2. Check the API server window for error messages")
        print("3. Verify your .env file has correct OPENAI_API_KEY")
        sys.exit(1)
    else:
        print("\n" + "=" * 40)
        print("✅ All API tests passed!")
        print("The API is working correctly.")
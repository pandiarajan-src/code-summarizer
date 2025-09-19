#!/usr/bin/env python
"""
Test config overrides issue specifically
"""

import requests
from pathlib import Path

def test_config_overrides_issue():
    """Test the specific config overrides JSON parsing issue"""
    base_url = "http://127.0.0.1:8000"

    print("🧪 Testing Config Overrides Issue")
    print("=" * 50)

    # Create a simple test file
    test_content = '''def hello():
    return "Hello!"
'''

    test_file = Path("temp_config_test.py")
    test_file.write_text(test_content)

    try:
        # Test 1: No config_overrides parameter at all
        print("\n1. Testing without config_overrides parameter...")
        with open(test_file, 'rb') as f:
            files = {'files': f}
            data = {
                'output_format': 'json',
                'verbose': 'false'
            }
            # Note: NOT sending config_overrides at all

            response = requests.post(
                f"{base_url}/api/analyze/upload",
                files=files,
                data=data,
                timeout=30
            )

        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Works without config_overrides")
        else:
            print("   ❌ Failed without config_overrides")
            try:
                error = response.json()
                print(f"   Error: {error.get('detail', response.text)}")
            except:
                print(f"   Error: {response.text}")

        # Test 2: Empty string config_overrides
        print("\n2. Testing with empty string config_overrides...")
        with open(test_file, 'rb') as f:
            files = {'files': f}
            data = {
                'output_format': 'json',
                'verbose': 'false',
                'config_overrides': ''  # Empty string
            }

            response = requests.post(
                f"{base_url}/api/analyze/upload",
                files=files,
                data=data,
                timeout=30
            )

        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Works with empty string config_overrides")
        else:
            print("   ❌ Failed with empty string config_overrides")
            try:
                error = response.json()
                print(f"   Error: {error.get('detail', response.text)}")
            except:
                print(f"   Error: {response.text}")

        # Test 3: Valid JSON config_overrides
        print("\n3. Testing with valid JSON config_overrides...")
        with open(test_file, 'rb') as f:
            files = {'files': f}
            data = {
                'output_format': 'json',
                'verbose': 'false',
                'config_overrides': '{"temperature": 0.1}'  # Valid JSON
            }

            response = requests.post(
                f"{base_url}/api/analyze/upload",
                files=files,
                data=data,
                timeout=30
            )

        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Works with valid JSON config_overrides")
        else:
            print("   ❌ Failed with valid JSON config_overrides")
            try:
                error = response.json()
                print(f"   Error: {error.get('detail', response.text)}")
            except:
                print(f"   Error: {response.text}")

    finally:
        # Clean up
        test_file.unlink()

if __name__ == "__main__":
    test_config_overrides_issue()
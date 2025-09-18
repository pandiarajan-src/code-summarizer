#!/usr/bin/env python
"""
Configuration Test Script
Test the fixed Pydantic settings configuration
"""

import sys
import os
from pathlib import Path

# Add app directory to Python path
if 'app' not in sys.path:
    sys.path.insert(0, 'app')

def test_config():
    """Test configuration loading"""
    print("🔧 Testing Configuration Loading")
    print("=" * 50)

    # Show current environment
    print(f"📁 Current directory: {Path.cwd()}")
    print(f"🐍 Python path: {sys.path[:3]}...")

    # Check for .env file
    env_file = Path('.env')
    if env_file.exists():
        print(f"✅ .env file found at: {env_file.absolute()}")
        with open(env_file, 'r') as f:
            content = f.read()
            if 'OPENAI_API_KEY=' in content:
                print("✅ OPENAI_API_KEY found in .env file")
            else:
                print("❌ OPENAI_API_KEY not found in .env file")
    else:
        print("❌ .env file not found")

    # Check environment variables
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print(f"✅ OPENAI_API_KEY environment variable set (length: {len(api_key)})")
    else:
        print("❌ OPENAI_API_KEY environment variable not set")

    print("\n🔄 Attempting to load configuration...")

    try:
        # Import the configuration
        from app.core.config import settings

        print("✅ Configuration loaded successfully!")
        print(f"📊 API Key configured: {'***SET***' if settings.openai_api_key else 'NOT_SET'}")
        print(f"🔧 Debug mode: {settings.debug}")
        print(f"🌐 API title: {settings.api_title}")
        print(f"🤖 LLM model: {settings.llm_model}")

        # Test debug info method
        print("\n🔍 Configuration Debug Info:")
        debug_info = settings.debug_info()
        for key, value in debug_info.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")

        return True

    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        print(f"   Error type: {type(e).__name__}")

        # The create_settings function should already print debug info
        return False

def main():
    """Main test function"""
    print("🧪 Code Summarizer Configuration Test")
    print("=" * 60)

    success = test_config()

    print("\n" + "=" * 60)
    if success:
        print("✅ Configuration test PASSED!")
        print("The API should now work correctly.")
    else:
        print("❌ Configuration test FAILED!")
        print("\nNext steps:")
        print("1. Check the debug information above")
        print("2. Ensure .env file exists with OPENAI_API_KEY")
        print("3. Restart the API server")
        print("4. Try running: python debug_api.py")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
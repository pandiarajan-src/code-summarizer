#!/usr/bin/env python
"""
API Debug Script for Windows
Helps identify and diagnose 500 internal server errors
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path
import platform

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.RESET):
    """Print colored message"""
    print(f"{color}{message}{Colors.RESET}")

def check_environment():
    """Check environment variables and configuration"""
    print_colored("\n🔍 Environment Check", Colors.BLUE + Colors.BOLD)
    print_colored("=" * 50, Colors.BLUE)

    issues = []

    # Check .env file
    env_path = Path('.env')
    if not env_path.exists():
        issues.append("❌ .env file not found")
        print_colored("❌ .env file not found", Colors.RED)
    else:
        print_colored("✅ .env file exists", Colors.GREEN)

        # Check API key
        with open(env_path, 'r') as f:
            content = f.read()
            if 'OPENAI_API_KEY=' not in content:
                issues.append("❌ OPENAI_API_KEY not set in .env")
                print_colored("❌ OPENAI_API_KEY not set in .env", Colors.RED)
            elif 'your_api_key_here' in content:
                issues.append("❌ OPENAI_API_KEY still has placeholder value")
                print_colored("❌ OPENAI_API_KEY still has placeholder value", Colors.RED)
            else:
                print_colored("✅ OPENAI_API_KEY appears to be set", Colors.GREEN)

    # Check PYTHONPATH
    pythonpath = os.environ.get('PYTHONPATH', '')
    if 'app' not in pythonpath:
        issues.append("⚠️  PYTHONPATH may not include 'app' directory")
        print_colored("⚠️  PYTHONPATH may not include 'app' directory", Colors.YELLOW)
        print_colored(f"   Current PYTHONPATH: {pythonpath}", Colors.YELLOW)
    else:
        print_colored("✅ PYTHONPATH includes app directory", Colors.GREEN)

    # Check required files
    required_files = [
        'app/main.py',
        'app/api_main.py',
        'config.yaml',
        'prompts.yaml'
    ]

    for file in required_files:
        if Path(file).exists():
            print_colored(f"✅ {file} exists", Colors.GREEN)
        else:
            issues.append(f"❌ {file} missing")
            print_colored(f"❌ {file} missing", Colors.RED)

    return issues

def test_direct_import():
    """Test importing the main application modules"""
    print_colored("\n🐍 Python Import Test", Colors.BLUE + Colors.BOLD)
    print_colored("=" * 50, Colors.BLUE)

    # Set PYTHONPATH for this test
    if 'app' not in sys.path:
        sys.path.insert(0, 'app')

    issues = []

    try:
        print_colored("Testing core imports...", Colors.YELLOW)

        # Test basic imports
        import app.core.config
        print_colored("✅ app.core.config imported successfully", Colors.GREEN)

        import app.api_main
        print_colored("✅ app.api_main imported successfully", Colors.GREEN)

        # Test configuration loading
        try:
            from app.core.config import settings
            print_colored("✅ Settings loaded successfully", Colors.GREEN)
            print_colored(f"   Debug mode: {settings.debug}", Colors.BLUE)
            print_colored(f"   API title: {settings.api_title}", Colors.BLUE)
        except Exception as e:
            issues.append(f"❌ Settings loading failed: {e}")
            print_colored(f"❌ Settings loading failed: {e}", Colors.RED)

    except ImportError as e:
        issues.append(f"❌ Import failed: {e}")
        print_colored(f"❌ Import failed: {e}", Colors.RED)
        print_colored("   This usually means missing dependencies", Colors.YELLOW)
    except Exception as e:
        issues.append(f"❌ Unexpected error: {e}")
        print_colored(f"❌ Unexpected error: {e}", Colors.RED)

    return issues

def test_api_endpoints():
    """Test API endpoints to identify specific errors"""
    print_colored("\n🌐 API Endpoint Test", Colors.BLUE + Colors.BOLD)
    print_colored("=" * 50, Colors.BLUE)

    base_url = "http://127.0.0.1:8000"
    issues = []

    # Test endpoints in order of complexity
    endpoints = [
        ("Health Check", "/api/health", "GET"),
        ("Root", "/", "GET"),
        ("API Docs", "/docs", "GET"),
        ("Supported Types", "/api/analyze/supported-types", "GET"),
    ]

    for name, endpoint, method in endpoints:
        try:
            print_colored(f"Testing {name} ({method} {endpoint})...", Colors.YELLOW)

            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=10)

            print_colored(f"   Status Code: {response.status_code}", Colors.BLUE)

            if response.status_code == 200:
                print_colored(f"✅ {name} working", Colors.GREEN)
                if 'application/json' in response.headers.get('content-type', ''):
                    try:
                        data = response.json()
                        print_colored(f"   Response: {json.dumps(data, indent=2)[:200]}...", Colors.BLUE)
                    except:
                        pass
            elif response.status_code == 500:
                print_colored(f"❌ {name} returning 500 Internal Server Error", Colors.RED)
                issues.append(f"500 error on {endpoint}")

                # Try to get error details
                try:
                    error_text = response.text
                    print_colored(f"   Error details: {error_text[:500]}...", Colors.RED)
                except:
                    pass
            else:
                print_colored(f"⚠️  {name} returned status {response.status_code}", Colors.YELLOW)

        except requests.exceptions.ConnectionError:
            issues.append(f"❌ Cannot connect to API server on {base_url}")
            print_colored(f"❌ Cannot connect to API server on {base_url}", Colors.RED)
            print_colored("   Make sure the API server is running", Colors.YELLOW)
            break
        except Exception as e:
            issues.append(f"❌ Error testing {name}: {e}")
            print_colored(f"❌ Error testing {name}: {e}", Colors.RED)

    return issues

def check_api_logs():
    """Help user find and check API server logs"""
    print_colored("\n📋 API Server Logs", Colors.BLUE + Colors.BOLD)
    print_colored("=" * 50, Colors.BLUE)

    print_colored("To see detailed API server logs:", Colors.YELLOW)
    print_colored("1. Look at the command window where you started the API", Colors.BLUE)
    print_colored("2. Or start the API manually to see errors:", Colors.BLUE)
    print()
    print_colored("   cd /path/to/code-summarizer", Colors.GREEN)
    print_colored("   set PYTHONPATH=app", Colors.GREEN)
    print_colored("   python -m uvicorn app.api_main:app --host 127.0.0.1 --port 8000 --reload --log-level debug", Colors.GREEN)
    print()
    print_colored("Look for error messages like:", Colors.YELLOW)
    print_colored("   - ImportError: No module named '...'", Colors.RED)
    print_colored("   - AttributeError: module has no attribute '...'", Colors.RED)
    print_colored("   - FileNotFoundError: config.yaml not found", Colors.RED)
    print_colored("   - ValidationError: Invalid configuration", Colors.RED)

def run_manual_test():
    """Run a manual API test"""
    print_colored("\n🧪 Manual API Test", Colors.BLUE + Colors.BOLD)
    print_colored("=" * 50, Colors.BLUE)

    try:
        # Test with a simple file upload
        test_file_content = """# Sample Python file
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
"""

        print_colored("Creating test file...", Colors.YELLOW)
        test_file_path = Path("test_sample.py")
        with open(test_file_path, 'w') as f:
            f.write(test_file_content)

        print_colored("Testing file upload API...", Colors.YELLOW)

        with open(test_file_path, 'rb') as f:
            files = {'files': f}
            data = {
                'output_format': 'json',
                'verbose': 'true'
            }

            response = requests.post(
                'http://127.0.0.1:8000/api/analyze/upload',
                files=files,
                data=data,
                timeout=30
            )

        print_colored(f"Status Code: {response.status_code}", Colors.BLUE)

        if response.status_code == 200:
            print_colored("✅ File upload test successful!", Colors.GREEN)
            try:
                result = response.json()
                print_colored(f"Response keys: {list(result.keys())}", Colors.BLUE)
            except:
                print_colored("Response received but not valid JSON", Colors.YELLOW)
        else:
            print_colored(f"❌ File upload test failed", Colors.RED)
            print_colored(f"Response: {response.text[:500]}...", Colors.RED)

        # Clean up
        test_file_path.unlink()

    except Exception as e:
        print_colored(f"❌ Manual test failed: {e}", Colors.RED)

def show_common_solutions():
    """Show common solutions for 500 errors"""
    print_colored("\n💡 Common Solutions for 500 Errors", Colors.BLUE + Colors.BOLD)
    print_colored("=" * 70, Colors.BLUE)

    solutions = [
        ("Missing Dependencies", [
            "pip install fastapi uvicorn openai tiktoken pydantic pydantic-settings",
            "OR: uv sync --frozen --no-dev"
        ]),
        ("Wrong PYTHONPATH", [
            "set PYTHONPATH=app",
            "Restart the API server after setting this"
        ]),
        ("Missing Config Files", [
            "Ensure config.yaml and prompts.yaml exist in project root",
            "Check .env file has correct OPENAI_API_KEY"
        ]),
        ("OpenAI API Issues", [
            "Verify your OpenAI API key is valid",
            "Check you have credits in your OpenAI account",
            "Test with: curl -H 'Authorization: Bearer your-key' https://api.openai.com/v1/models"
        ]),
        ("File Permissions", [
            "Ensure the app directory is readable",
            "Check Windows file permissions if on restricted system"
        ])
    ]

    for issue, steps in solutions:
        print_colored(f"\n{issue}:", Colors.YELLOW + Colors.BOLD)
        for step in steps:
            print_colored(f"  • {step}", Colors.GREEN)

def main():
    """Main debug function"""
    print_colored("\n" + "="*60, Colors.BOLD)
    print_colored("🐛 Code Summarizer API Debug Tool", Colors.BOLD + Colors.BLUE)
    print_colored("="*60 + "\n", Colors.BOLD)

    all_issues = []

    # Run all checks
    all_issues.extend(check_environment())
    all_issues.extend(test_direct_import())
    all_issues.extend(test_api_endpoints())

    # Run manual test if basic endpoints work
    if not any("Cannot connect" in issue for issue in all_issues):
        run_manual_test()

    # Show log instructions
    check_api_logs()

    # Summary
    print_colored("\n📊 Debug Summary", Colors.BLUE + Colors.BOLD)
    print_colored("=" * 50, Colors.BLUE)

    if all_issues:
        print_colored(f"Found {len(all_issues)} potential issues:", Colors.RED)
        for issue in all_issues:
            print_colored(f"  • {issue}", Colors.RED)
    else:
        print_colored("✅ No obvious configuration issues found", Colors.GREEN)
        print_colored("The 500 error may be a runtime issue. Check the API logs.", Colors.YELLOW)

    # Show solutions
    show_common_solutions()

    print_colored("\n" + "="*60, Colors.BOLD)
    print_colored("Next Steps:", Colors.YELLOW + Colors.BOLD)
    print_colored("1. Check the API server command window for detailed error messages", Colors.BLUE)
    print_colored("2. Try starting the API manually with debug logging", Colors.BLUE)
    print_colored("3. Fix any issues found above", Colors.BLUE)
    print_colored("4. If issues persist, share the API error logs", Colors.BLUE)
    print_colored("="*60 + "\n", Colors.BOLD)

if __name__ == "__main__":
    # Enable colors on Windows
    if platform.system() == "Windows":
        os.system("color")

    main()
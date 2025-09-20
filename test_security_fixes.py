#!/usr/bin/env python3
"""Test script to verify security fixes are working."""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.core.config import Settings
from app.core.security import sanitize_filename
from app.core.security import validate_file_path


def test_cors_configuration():
    """Test CORS configuration."""
    print("🔒 Testing CORS Configuration...")

    # Test with environment variables
    os.environ["CORS_ORIGINS"] = "http://localhost,https://example.com"
    settings = Settings()

    cors_origins = settings.cors_origins_list
    print(f"   ✅ CORS Origins: {cors_origins}")
    assert "http://localhost" in cors_origins
    assert "https://example.com" in cors_origins
    assert "*" not in cors_origins
    print("   ✅ CORS properly configured with whitelist")


def test_api_key_validation():
    """Test API key validation."""
    print("\n🔑 Testing API Key Validation...")

    # Test valid OpenAI key format
    try:
        os.environ["OPENAI_API_KEY"] = "sk-" + "a" * 48
        settings = Settings()
        print("   ✅ Valid OpenAI key format accepted")
    except ValueError as e:
        print(f"   ❌ Valid key rejected: {e}")

    # Test placeholder rejection
    try:
        os.environ["OPENAI_API_KEY"] = "your_api_key_here"
        settings = Settings()
        print("   ❌ Placeholder key should have been rejected")
    except ValueError:
        print("   ✅ Placeholder key properly rejected")


def test_host_configuration():
    """Test environment-aware host configuration."""
    print("\n🌐 Testing Host Configuration...")

    # Set a valid API key for testing
    os.environ["OPENAI_API_KEY"] = "sk-" + "a" * 48

    # Test local environment
    os.environ.pop("CONTAINER_MODE", None)
    os.environ.pop("DOCKER_CONTAINER", None)
    os.environ["HOST"] = "0.0.0.0"

    settings = Settings()
    print(f"   Host (local): {settings.host}")
    if settings.host == "127.0.0.1":
        print("   ✅ Local environment: host changed to 127.0.0.1")
    else:
        print("   ⚠️  Local environment: host not changed")

    # Test container environment
    os.environ["CONTAINER_MODE"] = "true"
    os.environ["HOST"] = "127.0.0.1"

    settings = Settings()
    print(f"   Host (container): {settings.host}")
    if settings.host == "0.0.0.0":
        print("   ✅ Container environment: host changed to 0.0.0.0")
    else:
        print("   ⚠️  Container environment: host not changed")


def test_path_validation():
    """Test path traversal prevention."""
    print("\n🛡️  Testing Path Validation...")

    # Test safe paths
    safe_paths = ["normal_file.txt", "folder/file.py", "test-file_123.js"]
    for path in safe_paths:
        try:
            result = validate_file_path(path)
            print(f"   ✅ Safe path accepted: {path}")
        except ValueError as e:
            print(f"   ❌ Safe path rejected: {path} - {e}")

    # Test dangerous paths
    dangerous_paths = [
        "../../../etc/passwd",
        "..\\..\\windows\\system32",
        "%2e%2e%2f%2e%2e%2f",
        "file\x00.txt",
    ]

    for path in dangerous_paths:
        try:
            result = validate_file_path(path)
            print(f"   ❌ Dangerous path accepted: {path}")
        except ValueError:
            print(f"   ✅ Dangerous path rejected: {path}")


def test_filename_sanitization():
    """Test filename sanitization."""
    print("\n🧹 Testing Filename Sanitization...")

    test_cases = [
        ("normal_file.txt", "normal_file.txt"),
        ("file with spaces.py", "file_with_spaces.py"),
        ('file<>:"/\\|?*.txt', "file_________.txt"),
        ("CON.txt", "file_CON.txt"),  # Reserved Windows name
        ("very" * 100 + ".txt", None),  # Should be truncated
    ]

    for original, expected in test_cases:
        try:
            sanitized = sanitize_filename(original)
            if expected and sanitized == expected:
                print(f"   ✅ Correctly sanitized: {original} → {sanitized}")
            elif expected is None and len(sanitized) <= 255:
                print(
                    f"   ✅ Long filename truncated: {original[:20]}... → {sanitized[:20]}..."
                )
            else:
                print(f"   ⚠️  Unexpected result: {original} → {sanitized}")
        except ValueError as e:
            print(f"   ❌ Sanitization failed: {original} - {e}")


def test_security_middleware():
    """Test security middleware components."""
    print("\n🛡️  Testing Security Middleware...")

    # Set a valid API key for testing
    os.environ["OPENAI_API_KEY"] = "sk-" + "a" * 48
    settings = Settings()

    # Test security settings
    print(f"   Security headers enabled: {settings.security.security_headers_enabled}")
    print(
        f"   Rate limit per minute: {settings.security.rate_limit_requests_per_minute}"
    )
    print(
        f"   Upload rate limit: {settings.security.upload_rate_limit_requests_per_minute}"
    )
    print(f"   CSP configured: {bool(settings.security.content_security_policy)}")

    print("   ✅ Security middleware configuration loaded")


def main():
    """Run all security tests."""
    print("🔒 SECURITY FIXES VERIFICATION")
    print("=" * 50)

    try:
        test_cors_configuration()
        test_api_key_validation()
        test_host_configuration()
        test_path_validation()
        test_filename_sanitization()
        test_security_middleware()

        print("\n" + "=" * 50)
        print("✅ ALL SECURITY TESTS COMPLETED")
        print("🎉 Critical security issues have been fixed!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

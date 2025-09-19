#!/usr/bin/env python
"""
Test script for external access to Code Summarizer
Tests CORS and external connectivity
"""

import socket
import subprocess
import requests
import sys
import platform
from pathlib import Path

def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        # Connect to a remote server to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Unable to determine"

def check_port_open(host, port):
    """Check if a port is open and accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def test_local_access():
    """Test local access (127.0.0.1)"""
    print("\n🔍 Testing Local Access (127.0.0.1)")
    print("-" * 50)

    # Test API health
    try:
        response = requests.get("http://127.0.0.1:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Local API access: WORKING")
        else:
            print(f"❌ Local API access: Failed (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Local API access: Failed ({e})")
        return False

    # Test Frontend
    try:
        response = requests.get("http://127.0.0.1:8080", timeout=5)
        if response.status_code == 200:
            print("✅ Local Frontend access: WORKING")
        else:
            print(f"❌ Local Frontend access: Failed (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Local Frontend access: Failed ({e})")
        return False

    return True

def test_external_access(local_ip):
    """Test external access using local IP"""
    print(f"\n🌐 Testing External Access ({local_ip})")
    print("-" * 50)

    # Test port accessibility
    api_port_open = check_port_open(local_ip, 8000)
    frontend_port_open = check_port_open(local_ip, 8080)

    print(f"Port 8000 (API) accessible: {'✅ YES' if api_port_open else '❌ NO'}")
    print(f"Port 8080 (Frontend) accessible: {'✅ YES' if frontend_port_open else '❌ NO'}")

    if not api_port_open:
        print("\n⚠️  Port 8000 is not accessible externally")
        print("This could be due to:")
        print("  1. API server bound to 127.0.0.1 instead of 0.0.0.0")
        print("  2. Windows Firewall blocking the port")
        print("  3. Router/network firewall blocking the port")
        return False

    if not frontend_port_open:
        print("\n⚠️  Port 8080 is not accessible externally")
        print("This could be due to:")
        print("  1. Frontend server bound to localhost instead of 0.0.0.0")
        print("  2. Windows Firewall blocking the port")
        return False

    # Test API HTTP request
    try:
        response = requests.get(f"http://{local_ip}:8000/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ External API HTTP request: WORKING")
        else:
            print(f"❌ External API HTTP request: Failed (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ External API HTTP request: Failed ({e})")
        return False

    # Test Frontend HTTP request
    try:
        response = requests.get(f"http://{local_ip}:8080", timeout=10)
        if response.status_code == 200:
            print("✅ External Frontend HTTP request: WORKING")
        else:
            print(f"❌ External Frontend HTTP request: Failed (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ External Frontend HTTP request: Failed ({e})")
        return False

    return True

def test_cors():
    """Test CORS configuration"""
    print("\n🔐 Testing CORS Configuration")
    print("-" * 50)

    local_ip = get_local_ip()

    try:
        # Simulate a cross-origin request
        headers = {
            'Origin': f'http://{local_ip}:8080',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }

        # Test preflight request
        response = requests.options("http://127.0.0.1:8000/api/health", headers=headers, timeout=5)

        cors_headers = response.headers
        print(f"CORS Headers received:")
        for header, value in cors_headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")

        if 'Access-Control-Allow-Origin' in cors_headers:
            allow_origin = cors_headers['Access-Control-Allow-Origin']
            if allow_origin == '*' or local_ip in allow_origin:
                print("✅ CORS configuration: WORKING")
                return True
            else:
                print(f"❌ CORS configuration: Origin not allowed ({allow_origin})")
                return False
        else:
            print("❌ CORS configuration: No Access-Control-Allow-Origin header")
            return False

    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False

def check_firewall_rules():
    """Check Windows firewall rules"""
    print("\n🔥 Checking Windows Firewall Rules")
    print("-" * 50)

    if platform.system() != "Windows":
        print("ℹ️  Not Windows - skipping firewall check")
        return True

    try:
        # Check for existing firewall rules
        result = subprocess.run(
            'netsh advfirewall firewall show rule name="Code Summarizer API"',
            shell=True,
            capture_output=True,
            text=True
        )

        if "Code Summarizer API" in result.stdout:
            print("✅ API firewall rule exists")
        else:
            print("❌ API firewall rule missing")
            print("Run setup_firewall.bat as Administrator to add firewall rules")

        result = subprocess.run(
            'netsh advfirewall firewall show rule name="Code Summarizer Frontend"',
            shell=True,
            capture_output=True,
            text=True
        )

        if "Code Summarizer Frontend" in result.stdout:
            print("✅ Frontend firewall rule exists")
            return True
        else:
            print("❌ Frontend firewall rule missing")
            print("Run setup_firewall.bat as Administrator to add firewall rules")
            return False

    except Exception as e:
        print(f"⚠️  Could not check firewall rules: {e}")
        return True  # Don't fail the test for this

def main():
    """Main test function"""
    print("🧪 Code Summarizer External Access Test")
    print("=" * 60)

    local_ip = get_local_ip()
    print(f"📍 Local IP Address: {local_ip}")

    # Test 1: Local access
    local_ok = test_local_access()

    # Test 2: External access
    external_ok = False
    if local_ok:
        external_ok = test_external_access(local_ip)

    # Test 3: CORS
    cors_ok = test_cors()

    # Test 4: Firewall rules
    firewall_ok = check_firewall_rules()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Local Access:     {'✅ PASS' if local_ok else '❌ FAIL'}")
    print(f"External Access:  {'✅ PASS' if external_ok else '❌ FAIL'}")
    print(f"CORS Config:      {'✅ PASS' if cors_ok else '❌ FAIL'}")
    print(f"Firewall Rules:   {'✅ PASS' if firewall_ok else '❌ FAIL'}")

    if all([local_ok, external_ok, cors_ok]):
        print("\n🎉 All tests passed! External access should work.")
        print(f"\nAccess from other machines:")
        print(f"  Frontend: http://{local_ip}:8080")
        print(f"  API:      http://{local_ip}:8000")
        print(f"  API Docs: http://{local_ip}:8000/docs")
    else:
        print("\n❌ Some tests failed. Check the issues above.")

        if not local_ok:
            print("\n🔧 Fix local access first:")
            print("  1. Ensure both API and Frontend servers are running")
            print("  2. Check for any error messages in the server windows")

        if not external_ok and local_ok:
            print("\n🔧 To fix external access:")
            print("  1. Restart API server with --host 0.0.0.0")
            print("  2. Run setup_firewall.bat as Administrator")
            print("  3. Check your router/network firewall settings")

        if not cors_ok:
            print("\n🔧 To fix CORS:")
            print("  1. Check FastAPI CORS middleware configuration")
            print("  2. Ensure allow_origins includes '*' or your IP")

    return all([local_ok, external_ok, cors_ok])

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
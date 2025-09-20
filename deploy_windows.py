#!/usr/bin/env python
"""Simple Windows Deployment Script for Code Summarizer
Runs API and Frontend servers without Docker
"""

import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# Colors for terminal output (Windows compatible)
if platform.system() == "Windows":
    os.system("color")


class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_colored(message, color=Colors.RESET):
    """Print colored message"""
    print(f"{color}{message}{Colors.RESET}")


def check_port(port):
    """Check if a port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("127.0.0.1", port))
    sock.close()
    return result != 0


def kill_process_on_port(port):
    """Kill process running on specified port"""
    if platform.system() == "Windows":
        # Windows command to find and kill process
        try:
            # Find the PID using the port
            result = subprocess.run(
                f"netstat -aon | findstr :{port}",
                check=False,
                shell=True,
                capture_output=True,
                text=True,
            )

            if result.stdout:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        if pid and pid.isdigit():
                            print(f"Killing process {pid} on port {port}...")
                            subprocess.run(
                                f"taskkill /F /PID {pid}",
                                check=False,
                                shell=True,
                                capture_output=True,
                            )
        except Exception as e:
            print(f"Could not kill process on port {port}: {e}")
    else:
        # Unix/Linux/Mac command
        try:
            subprocess.run(
                f"lsof -ti:{port} | xargs kill -9",
                check=False,
                shell=True,
                capture_output=True,
            )
        except:
            pass


def check_python():
    """Check if Python is installed"""
    try:
        result = subprocess.run(
            [sys.executable, "--version"], check=False, capture_output=True, text=True
        )
        version = result.stdout.strip()
        print_colored(f"✓ Python found: {version}", Colors.GREEN)
        return True
    except Exception as e:
        print_colored("✗ Python not found!", Colors.RED)
        return False


def setup_env_file():
    """Setup .env file if it doesn't exist"""
    env_path = Path(".env")
    env_example_path = Path(".env.example")

    if not env_path.exists():
        print_colored("Setting up environment file...", Colors.YELLOW)

        if env_example_path.exists():
            shutil.copy(env_example_path, env_path)
            print_colored("Created .env from .env.example", Colors.GREEN)
        else:
            # Create a basic .env file
            with open(env_path, "w") as f:
                f.write("OPENAI_API_KEY=your_api_key_here\n")
                f.write("OPENAI_BASE_URL=https://api.openai.com/v1\n")
                f.write("MODEL_NAME=gpt-4o\n")
            print_colored("Created basic .env file", Colors.GREEN)

        print_colored(
            "\n⚠️  IMPORTANT: Edit .env and add your OPENAI_API_KEY", Colors.YELLOW
        )

        # Try to open in default editor
        if platform.system() == "Windows":
            os.system("notepad .env")

        input("Press Enter after updating .env file...")
        return True

    # Check if API key is set
    with open(env_path) as f:
        content = f.read()
        if "your_api_key_here" in content or "OPENAI_API_KEY=" not in content:
            print_colored(
                "⚠️  WARNING: OPENAI_API_KEY may not be set properly", Colors.YELLOW
            )
            if platform.system() == "Windows":
                response = input("Would you like to edit .env now? (y/n): ")
                if response.lower() == "y":
                    os.system("notepad .env")
                    input("Press Enter after updating .env file...")

    return True


def install_dependencies():
    """Install Python dependencies"""
    print_colored("\nInstalling dependencies...", Colors.BLUE)

    # Try with uv first
    if shutil.which("uv"):
        print("Using uv package manager...")
        result = subprocess.run("uv sync --frozen --no-dev", check=False, shell=True)
        if result.returncode == 0:
            print_colored("✓ Dependencies installed with uv", Colors.GREEN)
            return True

    # Fall back to pip with requirements.txt
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        # Generate requirements.txt from pyproject.toml if needed
        print("Generating requirements.txt...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "toml"],
                check=False,
                capture_output=True,
            )
            try:
                import toml

                with open("pyproject.toml") as f:
                    data = toml.load(f)
                    deps = data.get("project", {}).get("dependencies", [])
                    with open("requirements.txt", "w") as req:
                        req.write("\n".join(deps))
            except ImportError:
                print_colored("Could not import toml module", Colors.YELLOW)
        except Exception as e:
            print_colored(f"Could not generate requirements.txt: {e}", Colors.YELLOW)

    if requirements_path.exists():
        print("Using pip to install dependencies...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=False,
        )
        if result.returncode == 0:
            print_colored("✓ Dependencies installed with pip", Colors.GREEN)
            return True

    # Try installing core dependencies directly
    print("Installing core dependencies...")
    core_deps = [
        "fastapi",
        "uvicorn[standard]",
        "pydantic",
        "pydantic-settings",
        "openai",
        "tiktoken",
        "click",
        "python-multipart",
        "pyyaml",
    ]

    for dep in core_deps:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", dep],
            check=False,
            capture_output=True,
        )

    print_colored("✓ Core dependencies installed", Colors.GREEN)
    return True


def start_api_server():
    """Start the API server"""
    print_colored("\nStarting API server...", Colors.BLUE)

    # Kill existing process on port 8000
    if not check_port(8000):
        print("Port 8000 is in use, cleaning up...")
        kill_process_on_port(8000)
        time.sleep(2)

    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = "app"

    # Start API server (bind to 0.0.0.0 to allow external access)
    if platform.system() == "Windows":
        api_process = subprocess.Popen(
            'start "Code Summarizer API" cmd /k "set PYTHONPATH=app&& python -m uvicorn app.api_main:app --host 0.0.0.0 --port 8000 --reload"',
            shell=True,
            env=env,
        )
    else:
        api_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.api_main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--reload",
            ],
            env=env,
        )

    # Wait for API to start
    print("Waiting for API to start...")
    for _ in range(10):
        time.sleep(1)
        if not check_port(8000):
            # Try to check health endpoint
            try:
                import urllib.request

                response = urllib.request.urlopen("http://127.0.0.1:8000/api/health")
                if response.status == 200:
                    print_colored(
                        "✓ API server is running on http://localhost:8000", Colors.GREEN
                    )
                    return api_process
            except Exception:
                pass

    print_colored(
        "⚠️  API may not have started properly. Check for errors.", Colors.YELLOW
    )
    return api_process


def start_frontend_server():
    """Start the frontend server"""
    print_colored("\nStarting Frontend server...", Colors.BLUE)

    # Kill existing process on port 8080
    if not check_port(8080):
        print("Port 8080 is in use, cleaning up...")
        kill_process_on_port(8080)
        time.sleep(2)

    # Change to frontend directory
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print_colored("✗ Frontend directory not found!", Colors.RED)
        return None

    # Start frontend server
    if platform.system() == "Windows":
        frontend_process = subprocess.Popen(
            'start "Code Summarizer Frontend" cmd /k "cd frontend && python -m http.server 8080"',
            shell=True,
        )
    else:
        frontend_process = subprocess.Popen(
            [sys.executable, "-m", "http.server", "8080"], cwd="frontend"
        )

    time.sleep(2)
    print_colored("✓ Frontend server is running on http://localhost:8080", Colors.GREEN)
    return frontend_process


def main():
    """Main deployment function"""
    print_colored("\n" + "=" * 50, Colors.BOLD)
    print_colored("Code Summarizer Windows Deployment", Colors.BOLD)
    print_colored("=" * 50 + "\n", Colors.BOLD)

    # Check Python
    if not check_python():
        print_colored(
            "Please install Python 3.12+ from https://www.python.org/", Colors.RED
        )
        sys.exit(1)

    # Setup environment
    if not setup_env_file():
        print_colored("Failed to setup environment file", Colors.RED)
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        print_colored("Failed to install dependencies", Colors.RED)
        sys.exit(1)

    # Start servers
    start_api_server()
    start_frontend_server()

    # Print success message
    print_colored("\n" + "=" * 50, Colors.GREEN)
    print_colored("🚀 Deployment Complete!", Colors.GREEN + Colors.BOLD)
    print_colored("=" * 50, Colors.GREEN)

    print_colored("\n📍 Access Points:", Colors.BLUE)
    print(f"   • Frontend: {Colors.BOLD}http://localhost:8080{Colors.RESET}")
    print(f"   • API: {Colors.BOLD}http://localhost:8000{Colors.RESET}")
    print(f"   • API Docs: {Colors.BOLD}http://localhost:8000/docs{Colors.RESET}")

    print_colored("\n📝 Instructions:", Colors.YELLOW)
    print("   • The frontend will open in your browser automatically")
    print("   • Upload code files or zip archives to analyze")
    print("   • View the generated markdown summaries")

    print_colored("\n⚠️  To stop servers:", Colors.YELLOW)
    print("   • Press Ctrl+C in this window")
    print("   • Or close the server command windows")

    # Open browser
    time.sleep(2)
    print_colored("\nOpening browser...", Colors.BLUE)
    webbrowser.open("http://localhost:8080")

    # Keep running
    try:
        print_colored("\nPress Ctrl+C to stop all servers...\n", Colors.YELLOW)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_colored("\n\nShutting down servers...", Colors.YELLOW)

        # Kill processes on ports
        kill_process_on_port(8000)
        kill_process_on_port(8080)

        print_colored("✓ Servers stopped", Colors.GREEN)
        sys.exit(0)


if __name__ == "__main__":
    main()

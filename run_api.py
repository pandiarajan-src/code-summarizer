#!/usr/bin/env python3
"""Startup script for Code Summarizer API."""

import os
import sys
import socket
import signal
import subprocess
import time

def is_port_in_use(host, port):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True

def find_process_using_port(port):
    """Find the PID of the process using the specified port."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip().split('\n')[0])
    except (subprocess.SubprocessError, ValueError):
        pass
    return None

def kill_process_on_port(port):
    """Kill the process using the specified port."""
    pid = find_process_using_port(port)
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"Killed process {pid} using port {port}")
            time.sleep(1)  # Give the process time to terminate

            # If process still exists, force kill
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass  # Process already terminated

            return True
        except ProcessLookupError:
            print(f"Process {pid} already terminated")
            return True
        except PermissionError:
            print(f"Permission denied to kill process {pid}")
            return False
    return False

if __name__ == "__main__":
    # Add app directory to path (simplified structure)
    app_path = os.path.join(os.path.dirname(__file__), "app")
    sys.path.insert(0, app_path)

    # Also add root directory to path so app can be imported as a module
    root_path = os.path.dirname(__file__)
    sys.path.insert(0, root_path)

    # Set PYTHONPATH environment variable to include both paths
    os.environ["PYTHONPATH"] = f"{root_path}:{app_path}"

    # Configuration
    HOST = "0.0.0.0"
    PORT = 8000

    # Check if port is in use and handle it
    if is_port_in_use(HOST, PORT):
        print(f"Port {PORT} is already in use on {HOST}")
        print("Attempting to stop the existing process...")

        if kill_process_on_port(PORT):
            print(f"Successfully freed port {PORT}")
            time.sleep(1)  # Wait a moment before starting new server
        else:
            print(f"Failed to free port {PORT}. You may need to manually stop the process.")
            sys.exit(1)

    import uvicorn

    # Run the API server
    print(f"Starting API server on {HOST}:{PORT}")
    uvicorn.run(
        "app.api_main:app",
        host=HOST,
        port=PORT,
        reload=False,  # Disable reload to avoid subprocess issues
        log_level="info"
    )

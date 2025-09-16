#!/usr/bin/env python3
"""Startup script for Code Summarizer API."""

import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path


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
        # Validate port strictly
        if not isinstance(port, int) or not (1 <= port <= 65535):
            print("Port must be an integer between 1 and 65535")
            return None

        # Locate the full path to the lsof binary
        lsof_path = shutil.which("lsof")
        if not lsof_path:
            # lsof not available on this system
            return None

        result = subprocess.run(
            [lsof_path, "-ti", f":{port}"],
            capture_output=True,
            text=True,
            check=False,
        )  # nosec S603

        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip().split("\n")[0])
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
            with suppress(ProcessLookupError):
                os.kill(pid, signal.SIGKILL)
                print(f"Force killed process {pid} using port {port}")

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
    app_path = Path(__file__).parent / "app"
    sys.path.insert(0, str(app_path))

    # Also add root directory to path so app can be imported as a module
    root_path = Path(__file__).parent
    sys.path.insert(0, str(root_path))

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
            print(
                f"Failed to free port {PORT}. You may need to manually stop the process."
            )
            sys.exit(1)

    import uvicorn

    # Run the API server
    print(f"Starting API server on {HOST}:{PORT}")
    uvicorn.run(
        "app.api_main:app",
        host=HOST,
        port=PORT,
        reload=False,  # Disable reload to avoid subprocess issues
        log_level="info",
    )

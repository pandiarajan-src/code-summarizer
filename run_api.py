#!/usr/bin/env python3
"""Startup script for Code Summarizer API."""

import os
import sys

if __name__ == "__main__":
    # Add src to path
    src_path = os.path.join(os.path.dirname(__file__), "src")
    sys.path.insert(0, src_path)

    # Set PYTHONPATH environment variable
    os.environ["PYTHONPATH"] = src_path

    import uvicorn

    # Run the API server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
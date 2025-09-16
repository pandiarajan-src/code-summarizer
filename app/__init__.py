"""Code Summarizer - AI-powered code analysis and summarization tool."""

__version__ = "1.0.0"
__author__ = "Code Analysis Team"
__description__ = "AI-powered code analysis and summarization tool"


# Only import CLI when explicitly requested to avoid dependency issues
def get_cli() -> object:
    """Lazy import CLI to avoid loading heavy dependencies."""
    from .main import cli

    return cli


__all__ = ["get_cli"]

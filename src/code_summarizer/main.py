#!/usr/bin/env python3
"""Code Summarizer CLI - AI-powered code analysis tool."""

import sys
from pathlib import Path

import click
from dotenv import load_dotenv

from .context_manager import ContextManager
from .file_processor import FileProcessor
from .llm_client import LLMClient
from .markdown_formatter import MarkdownFormatter

load_dotenv()


@click.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=str, help="Output markdown file path")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    default="config.yaml",
    help="Configuration file path",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def analyze(input_path: str, output: str, config: str, verbose: bool) -> None:
    """Analyze source code files or projects and generate markdown summaries.

    INPUT_PATH can be a single source file or a zip archive containing a project.
    """
    try:
        if verbose:
            click.echo(f"Analyzing: {input_path}")

        # Initialize components
        file_processor = FileProcessor(config_path=config)
        llm_client = LLMClient(config_path=config)
        context_manager = ContextManager(config_path=config)
        markdown_formatter = MarkdownFormatter(config_path=config)

        # Process input
        files_data = file_processor.process_input(input_path)

        if not files_data:
            click.echo("No supported code files found in input.", err=True)
            sys.exit(1)

        if verbose:
            click.echo(f"Found {len(files_data)} code files")

        # Batch files based on context limits
        batches = context_manager.create_batches(files_data)

        if verbose:
            click.echo(f"Created {len(batches)} batches for analysis")

        # Analyze each batch
        analysis_results = []
        for i, batch in enumerate(batches):
            if verbose:
                click.echo(f"Analyzing batch {i + 1}/{len(batches)}...")
            result = llm_client.analyze_batch(batch)
            analysis_results.append(result)

        # Generate markdown output
        markdown_content = markdown_formatter.format_results(
            files_data, analysis_results
        )

        # Determine output path
        if not output:
            input_name = Path(input_path).stem
            output = f"{input_name}_summary.md"

        # Write output
        with open(output, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        click.echo(f"Analysis complete! Summary saved to: {output}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@click.command()
def version() -> None:
    """Show version information."""
    click.echo("Code Summarizer v1.0.0")


@click.group()
def cli() -> None:
    """AI-powered code analysis and summarization tool."""
    pass


cli.add_command(analyze)
cli.add_command(version)

if __name__ == "__main__":
    cli()

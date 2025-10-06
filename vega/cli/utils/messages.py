"""CLI message formatting utilities"""
from pathlib import Path
from typing import Sequence

import click


class CLIMessages:
    """Centralized CLI message formatting with consistent styling"""

    # Color and style constants
    SUCCESS_STYLE = {'fg': 'green', 'bold': True}
    ERROR_STYLE = {'fg': 'red'}
    WARNING_STYLE = {'fg': 'yellow'}
    INFO_STYLE = {'fg': 'blue'}
    HIGHLIGHT_STYLE = {'fg': 'green'}

    @staticmethod
    def success(message: str) -> str:
        """Format success message"""
        prefix = click.style('SUCCESS:', **CLIMessages.SUCCESS_STYLE)
        return f"{prefix} {message}"

    @staticmethod
    def error(message: str) -> str:
        """Format error message"""
        return click.style(f"ERROR: {message}", **CLIMessages.ERROR_STYLE)

    @staticmethod
    def warning(message: str) -> str:
        """Format warning message"""
        return click.style(f"WARNING: {message}", **CLIMessages.WARNING_STYLE)

    @staticmethod
    def info(message: str) -> str:
        """Format info message"""
        return f"[*] {message}"

    @staticmethod
    def file_created(path: Path, project_root: Path | None = None) -> str:
        """Format file creation message"""
        if project_root:
            try:
                path = path.relative_to(project_root)
            except ValueError:
                pass  # Path not relative to project_root, use as-is

        path_str = click.style(str(path), **CLIMessages.HIGHLIGHT_STYLE)
        return f"  + Created {path_str}"

    @staticmethod
    def next_steps(steps: Sequence[str], title: str = "Next steps") -> str:
        """Format next steps message"""
        lines = [f"\n{title}:"]
        for step in steps:
            lines.append(f"  {step}")
        return '\n'.join(lines)

    @staticmethod
    def tip(message: str) -> str:
        """Format tip message"""
        return f"\n[TIP] {message}"

    @staticmethod
    def section_header(title: str) -> str:
        """Format section header"""
        return f"\n[*] {title}"

    @staticmethod
    def component_usage(component_name: str, example: str) -> str:
        """Format component usage example"""
        return CLIMessages.tip(f"Usage:\n   {example}")

    @staticmethod
    def docs_link(url: str = "https://vega-framework.readthedocs.io/") -> str:
        """Format documentation link"""
        return f"\n[Docs] {url}"

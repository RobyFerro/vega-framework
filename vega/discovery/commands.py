"""Click CLI commands auto-discovery utilities"""
import importlib
import inspect
import logging
from pathlib import Path
from typing import List

try:
    import click
except ImportError:
    click = None

logger = logging.getLogger(__name__)


def discover_commands(
    base_package: str,
    commands_subpackage: str = "presentation.cli.commands"
) -> List["click.Command"]:
    """
    Auto-discover Click commands from a package.

    This function scans a package directory for Python modules containing
    Click Command instances and returns them as a list.

    Args:
        base_package: Base package name (use __package__ from calling module)
        commands_subpackage: Subpackage path containing commands (default: "presentation.cli.commands")

    Returns:
        List[click.Command]: List of discovered Click commands

    Example:
        # In your project's presentation/cli/commands/__init__.py
        from vega.discovery import discover_commands

        def get_commands():
            return discover_commands(__package__)

        # Or with custom configuration
        def get_commands():
            return discover_commands(
                __package__,
                commands_subpackage="cli.custom_commands"
            )

    Note:
        Each command module can export multiple Click Command instances.
        All public (non-underscore prefixed) Command instances will be discovered.
    """
    if click is None:
        raise ImportError(
            "Click is not installed. Install it with: pip install click"
        )

    commands = []

    # Resolve the commands package path
    try:
        # Determine the package to scan
        if base_package.endswith(commands_subpackage):
            commands_package = base_package
        else:
            # Extract base from fully qualified package name
            parts = base_package.split('.')
            # Find the root package (usually the project name)
            root_package = parts[0]
            commands_package = f"{root_package}.{commands_subpackage}"

        # Import the commands package to get its path
        commands_module = importlib.import_module(commands_package)
        commands_dir = Path(commands_module.__file__).parent

        logger.debug(f"Discovering commands in: {commands_dir}")

        # Scan for command modules
        discovered_count = 0
        for file in commands_dir.glob("*.py"):
            if file.stem == "__init__":
                continue

            module_name = f"{commands_package}.{file.stem}"

            try:
                module = importlib.import_module(module_name)

                # Find all Click Command instances
                for name, obj in inspect.getmembers(module):
                    if isinstance(obj, click.Command) and not name.startswith("_"):
                        commands.append(obj)
                        discovered_count += 1
                        logger.info(f"Registered command: {name} from {module_name}")

            except Exception as e:
                logger.warning(f"Failed to import {module_name}: {e}")
                continue

        logger.info(f"Auto-discovery complete: {discovered_count} command(s) registered")

    except ImportError as e:
        logger.error(f"Failed to import commands package '{commands_package}': {e}")
        raise

    return commands

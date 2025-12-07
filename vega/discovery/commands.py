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


def discover_commands_ddd(
    base_package: str
) -> List["click.Command"]:
    """
    Auto-discover Click commands from all bounded contexts (DDD structure).

    This function scans all bounded contexts in lib/ and discovers commands from each context's
    presentation.cli.commands package.

    Args:
        base_package: Base package name (usually the project name)

    Returns:
        List[click.Command]: List of all discovered Click commands from all contexts

    Example:
        # In your project's main.py
        from vega.discovery import discover_commands_ddd

        commands = discover_commands_ddd("my_project")
        for cmd in commands:
            cli.add_command(cmd)

    Note:
        - This function expects a DDD structure with lib/{context}/presentation/cli/commands/
        - Falls back to legacy structure if lib/ doesn't exist
        - Each command module can export multiple Click Command instances
    """
    if click is None:
        raise ImportError(
            "Click is not installed. Install it with: pip install click"
        )

    all_commands = []

    try:
        # Try to import lib package to check if DDD structure exists
        lib_module = importlib.import_module(f"{base_package}.lib")
        lib_path = Path(lib_module.__file__).parent

        logger.info(f"Detected DDD structure in: {lib_path}")

        # Get all bounded contexts (directories in lib/ except __pycache__ and shared)
        contexts = [
            d.name for d in lib_path.iterdir()
            if d.is_dir() and not d.name.startswith('_') and d.name != 'shared'
        ]

        logger.info(f"Found {len(contexts)} bounded context(s): {contexts}")

        total_discovered = 0

        # Discover commands in each context
        for context in contexts:
            commands_package = f"{base_package}.lib.{context}.presentation.cli.commands"

            try:
                commands_module = importlib.import_module(commands_package)
                commands_dir = Path(commands_module.__file__).parent

                logger.debug(f"Discovering commands in context '{context}': {commands_dir}")

                # Scan for command modules in this context
                for file in commands_dir.glob("*.py"):
                    if file.stem == "__init__":
                        continue

                    module_name = f"{commands_package}.{file.stem}"

                    try:
                        module = importlib.import_module(module_name)

                        # Find all Click Command instances
                        for name, obj in inspect.getmembers(module):
                            if isinstance(obj, click.Command) and not name.startswith("_"):
                                all_commands.append(obj)
                                total_discovered += 1
                                logger.info(f"Registered command: {name} from {module_name} (context: {context})")

                    except Exception as e:
                        logger.warning(f"Failed to import {module_name}: {e}")
                        continue

            except ImportError:
                logger.debug(f"No CLI commands found in context '{context}'")
                continue

        logger.info(f"Auto-discovery complete: {total_discovered} command(s) from {len(contexts)} context(s)")

    except ImportError:
        # Fallback to legacy structure
        logger.info("DDD structure not found, falling back to legacy structure")
        return discover_commands(base_package)

    return all_commands

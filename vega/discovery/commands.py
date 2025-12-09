"""Click CLI commands auto-discovery utilities"""
import importlib
import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from typing import List, Optional

try:
    import click
except ImportError:
    click = None

logger = logging.getLogger(__name__)


def _find_package_dir_from_filesystem(base_package: str, subpackage: str = "") -> Optional[Path]:
    """
    Find package directory from filesystem without requiring __init__.py.

    This function supports PEP 420 namespace packages by searching for
    package directories in sys.path and the current working directory.

    Args:
        base_package: Base package name (e.g., "myapp")
        subpackage: Subpackage path (e.g., "domain.repositories")

    Returns:
        Path to the package directory if found, None otherwise
    """
    # Construct the relative path parts
    base_parts = base_package.split('.')
    subpackage_parts = subpackage.split('.') if subpackage else []

    # Search locations: current directory first, then sys.path
    search_paths = [Path.cwd()] + [Path(p) for p in sys.path if p]

    for search_root in search_paths:
        # Strategy 1: Try full path (base_package + subpackage)
        potential_dir = search_root
        for part in base_parts + subpackage_parts:
            potential_dir = potential_dir / part

        if potential_dir.exists() and potential_dir.is_dir():
            if list(potential_dir.glob("*.py")) or list(potential_dir.glob("**/*.py")):
                logger.debug(f"Found package directory via filesystem (full path): {potential_dir}")
                return potential_dir

        # Strategy 2: If we're already inside base_package directory, look for subpackage only
        if subpackage_parts:
            potential_dir = search_root
            for part in subpackage_parts:
                potential_dir = potential_dir / part

            if potential_dir.exists() and potential_dir.is_dir():
                if list(potential_dir.glob("*.py")) or list(potential_dir.glob("**/*.py")):
                    logger.debug(f"Found package directory via filesystem (subpackage only): {potential_dir}")
                    return potential_dir

    return None


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

        # Handle namespace packages (PEP 420) where __file__ can be None
        if hasattr(commands_module, '__file__') and commands_module.__file__ is not None:
            commands_dir = Path(commands_module.__file__).parent
        else:
            # For namespace packages, use importlib.util.find_spec
            spec = importlib.util.find_spec(commands_package)
            if spec is None:
                # Fallback: search filesystem
                parts = commands_package.split('.')
                commands_dir = _find_package_dir_from_filesystem(parts[0], '.'.join(parts[1:]) if len(parts) > 1 else "")
                if commands_dir is None:
                    raise ImportError(f"Cannot locate commands package '{commands_package}' (namespace package without __file__)")
            elif spec.origin is not None:
                commands_dir = Path(spec.origin).parent
            elif spec.submodule_search_locations:
                # Namespace package: use first location from submodule_search_locations
                commands_dir = Path(spec.submodule_search_locations[0])
            else:
                # Fallback: search filesystem
                parts = commands_package.split('.')
                commands_dir = _find_package_dir_from_filesystem(parts[0], '.'.join(parts[1:]) if len(parts) > 1 else "")
                if commands_dir is None:
                    raise ImportError(f"Cannot locate commands package '{commands_package}' (namespace package without __file__)")

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
        # First try the package itself (new structure), then lib/ (legacy)
        package_module = None
        package_path_str = None

        try:
            # New structure: contexts directly in base package
            package_module = importlib.import_module(base_package)
            if hasattr(package_module, '__file__') and package_module.__file__ is not None:
                lib_path = Path(package_module.__file__).parent
                package_path_str = base_package
            else:
                # Namespace package: use find_spec or filesystem search
                lib_path = _find_package_dir_from_filesystem(base_package)
                if lib_path is None:
                    raise ImportError(f"Cannot locate package '{base_package}' (namespace package without __file__)")
                package_path_str = base_package
        except (ImportError, AttributeError):
            # Legacy structure: contexts in base_package.lib
            try:
                lib_module = importlib.import_module(f"{base_package}.lib")
                if hasattr(lib_module, '__file__') and lib_module.__file__ is not None:
                    lib_path = Path(lib_module.__file__).parent
                    package_path_str = f"{base_package}.lib"
                else:
                    # Namespace package: use find_spec or filesystem search
                    lib_path = _find_package_dir_from_filesystem(base_package, "lib")
                    if lib_path is None:
                        raise ImportError(f"Cannot locate package '{base_package}.lib' (namespace package without __file__)")
                    package_path_str = f"{base_package}.lib"
            except ImportError:
                raise

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
            commands_package = f"{package_path_str}.{context}.presentation.cli.commands"

            try:
                commands_module = importlib.import_module(commands_package)

                # Handle namespace packages (PEP 420) where __file__ can be None
                if hasattr(commands_module, '__file__') and commands_module.__file__ is not None:
                    commands_dir = Path(commands_module.__file__).parent
                else:
                    # For namespace packages, use importlib.util.find_spec
                    spec = importlib.util.find_spec(commands_package)
                    if spec is None:
                        # Fallback: search filesystem
                        parts = commands_package.split('.')
                        commands_dir = _find_package_dir_from_filesystem(parts[0], '.'.join(parts[1:]) if len(parts) > 1 else "")
                        if commands_dir is None:
                            logger.debug(f"Cannot locate commands package '{commands_package}', skipping context '{context}'")
                            continue
                    elif spec.origin is not None:
                        commands_dir = Path(spec.origin).parent
                    elif spec.submodule_search_locations:
                        # Namespace package: use first location from submodule_search_locations
                        commands_dir = Path(spec.submodule_search_locations[0])
                    else:
                        # Fallback: search filesystem
                        parts = commands_package.split('.')
                        commands_dir = _find_package_dir_from_filesystem(parts[0], '.'.join(parts[1:]) if len(parts) > 1 else "")
                        if commands_dir is None:
                            logger.debug(f"Cannot locate commands package '{commands_package}', skipping context '{context}'")
                            continue

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

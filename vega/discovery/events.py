"""Event handlers auto-discovery utilities"""
import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Optional

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


def discover_event_handlers(
    base_package: str,
    events_subpackage: str = "events"
) -> None:
    """
    Auto-discover and register event handlers from a package.

    This function scans a package directory for Python modules containing
    event handlers decorated with @subscribe() and automatically imports them
    to trigger registration with the global event bus.

    Args:
        base_package: Base package name (use __package__ from calling module)
        events_subpackage: Subpackage path containing events (default: "events")

    Example:
        # In your project's events/__init__.py
        from vega.discovery import discover_event_handlers

        def register_all_handlers():
            discover_event_handlers(__package__)

        # Or with custom configuration
        def register_all_handlers():
            discover_event_handlers(
                __package__,
                events_subpackage="application.events"
            )

    Note:
        Event handlers are registered automatically when modules are imported.
        This function simply imports all modules in the events directory to
        trigger the @subscribe() decorator registration.

        The function doesn't return anything - handlers register themselves
        with the global event bus via the @subscribe() decorator.
    """
    # Resolve the events package path
    try:
        # Determine the package to scan
        if base_package.endswith(events_subpackage):
            events_package = base_package
        else:
            # Extract base from fully qualified package name
            parts = base_package.split('.')
            # Find the root package (usually the project name)
            root_package = parts[0]
            events_package = f"{root_package}.{events_subpackage}"

        # Import the events package to get its path
        events_module = importlib.import_module(events_package)

        # Handle namespace packages (PEP 420) where __file__ can be None
        if hasattr(events_module, '__file__') and events_module.__file__ is not None:
            events_dir = Path(events_module.__file__).parent
        else:
            # For namespace packages, use importlib.util.find_spec
            spec = importlib.util.find_spec(events_package)
            if spec is None:
                # Fallback: search filesystem
                parts = events_package.split('.')
                events_dir = _find_package_dir_from_filesystem(parts[0], '.'.join(parts[1:]) if len(parts) > 1 else "")
                if events_dir is None:
                    raise ImportError(f"Cannot locate events package '{events_package}' (namespace package without __file__)")
            elif spec.origin is not None:
                events_dir = Path(spec.origin).parent
            elif spec.submodule_search_locations:
                # Namespace package: use first location from submodule_search_locations
                events_dir = Path(spec.submodule_search_locations[0])
            else:
                # Fallback: search filesystem
                parts = events_package.split('.')
                events_dir = _find_package_dir_from_filesystem(parts[0], '.'.join(parts[1:]) if len(parts) > 1 else "")
                if events_dir is None:
                    raise ImportError(f"Cannot locate events package '{events_package}' (namespace package without __file__)")

        logger.debug(f"Discovering event handlers in: {events_dir}")

        # Scan for event handler modules
        discovered_count = 0
        for file in events_dir.glob("*.py"):
            if file.stem == "__init__":
                continue

            module_name = f"{events_package}.{file.stem}"

            try:
                # Import the module to trigger @subscribe() decorator registration
                importlib.import_module(module_name)
                discovered_count += 1
                logger.info(f"Loaded event handlers from: {module_name}")

            except Exception as e:
                logger.warning(f"Failed to import {module_name}: {e}")
                continue

        logger.info(f"Auto-discovery complete: {discovered_count} event module(s) loaded")

    except ImportError as e:
        logger.error(f"Failed to import events package '{events_package}': {e}")
        raise

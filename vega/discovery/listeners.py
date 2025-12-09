"""Job listeners auto-discovery utilities"""
import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import List, Optional, Type

from vega.listeners.listener import JobListener
from vega.listeners.registry import get_listener_registry

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


def discover_listeners(
    base_package: str,
    listeners_subpackage: str = "infrastructure.listeners"
) -> List[Type[JobListener]]:
    """
    Auto-discover job listeners from a package.

    Similar to discover_event_handlers - imports modules to trigger
    @job_listener decorator registration.

    The function scans a package directory for Python modules containing
    listeners decorated with @job_listener and automatically imports them
    to trigger registration with the global listener registry.

    Args:
        base_package: Base package name (use __package__ from calling module)
        listeners_subpackage: Subpackage path containing listeners
                             (default: "infrastructure.listeners")

    Returns:
        List of discovered listener classes

    Example:
        # In your project's infrastructure/listeners/__init__.py
        from vega.discovery import discover_listeners

        def register_all_listeners():
            return discover_listeners(__package__)

        # Or from config.py
        from vega.discovery import discover_listeners

        # Discover all listeners on startup
        listeners = discover_listeners(
            "infrastructure",
            listeners_subpackage="listeners"
        )

    Usage in CLI:
        This function is called automatically by `vega listener run`:

        $ vega listener run
        ✓ Discovered 3 listener(s)
          - SendEmailListener (queue: emails, workers: 3)
          - ProcessOrderListener (queue: orders, workers: 5)
          - GenerateReportListener (queue: reports, workers: 1)

    Note:
        Listeners are registered automatically when modules are imported.
        This function simply imports all modules in the listeners directory to
        trigger the @job_listener() decorator registration.

        The discovered listeners are returned from the global registry.
    """
    discovered_classes = []

    try:
        # Determine the package to scan
        if base_package.endswith(listeners_subpackage):
            listeners_package = base_package
        else:
            # Extract root from fully qualified package name
            parts = base_package.split('.')
            root_package = parts[0]
            listeners_package = f"{root_package}.{listeners_subpackage}"

        # Import the listeners package to get its path
        try:
            listeners_module = importlib.import_module(listeners_package)
        except ImportError:
            logger.warning(
                f"Listeners package '{listeners_package}' not found. "
                f"Create it with: mkdir -p {listeners_subpackage.replace('.', '/')}"
            )
            return []

        # Handle namespace packages (PEP 420) where __file__ can be None
        if hasattr(listeners_module, '__file__') and listeners_module.__file__ is not None:
            listeners_dir = Path(listeners_module.__file__).parent
        else:
            # For namespace packages, use importlib.util.find_spec
            spec = importlib.util.find_spec(listeners_package)
            if spec is None:
                # Fallback: search filesystem
                parts = listeners_package.split('.')
                listeners_dir = _find_package_dir_from_filesystem(parts[0], '.'.join(parts[1:]) if len(parts) > 1 else "")
                if listeners_dir is None:
                    logger.warning(
                        f"Listeners package '{listeners_package}' not found (namespace package without __file__). "
                        f"Create it with: mkdir -p {listeners_subpackage.replace('.', '/')}"
                    )
                    return []
            elif spec.origin is not None:
                listeners_dir = Path(spec.origin).parent
            elif spec.submodule_search_locations:
                # Namespace package: use first location from submodule_search_locations
                listeners_dir = Path(spec.submodule_search_locations[0])
            else:
                # Fallback: search filesystem
                parts = listeners_package.split('.')
                listeners_dir = _find_package_dir_from_filesystem(parts[0], '.'.join(parts[1:]) if len(parts) > 1 else "")
                if listeners_dir is None:
                    logger.warning(
                        f"Listeners package '{listeners_package}' not found (namespace package without __file__). "
                        f"Create it with: mkdir -p {listeners_subpackage.replace('.', '/')}"
                    )
                    return []

        logger.debug(f"Discovering listeners in: {listeners_dir}")

        # Get initial registry count
        registry = get_listener_registry()
        initial_count = len(registry)

        # Scan for listener modules
        discovered_count = 0
        for file in listeners_dir.glob("*.py"):
            if file.stem == "__init__":
                continue

            module_name = f"{listeners_package}.{file.stem}"

            try:
                # Import module (triggers @job_listener registration)
                importlib.import_module(module_name)
                discovered_count += 1
                logger.info(f"Loaded listeners from: {module_name}")

            except Exception as e:
                logger.warning(
                    f"Failed to import {module_name}: {e}",
                    exc_info=True
                )
                continue

        # Get newly registered listeners
        registry = get_listener_registry()
        final_count = len(registry)
        new_listeners = final_count - initial_count

        logger.info(
            f"Auto-discovery complete: {new_listeners} listener(s) registered "
            f"from {discovered_count} module(s)"
        )

        return list(registry)

    except Exception as e:
        logger.error(f"Failed to discover listeners: {e}", exc_info=True)
        raise

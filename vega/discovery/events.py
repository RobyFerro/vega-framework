"""Event handlers auto-discovery utilities"""
import importlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


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
        events_dir = Path(events_module.__file__).parent

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

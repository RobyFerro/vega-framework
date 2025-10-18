"""DI Container beans auto-discovery utilities"""
import importlib
import inspect
import logging
from pathlib import Path
from typing import Optional, List

from vega.di import get_container, is_bean

logger = logging.getLogger(__name__)


def discover_beans(
    base_package: str,
    subpackages: Optional[List[str]] = None,
    recursive: bool = True
) -> int:
    """
    Auto-discover and register @bean decorated classes from packages.

    This function scans package directories for Python modules containing
    classes decorated with @bean and ensures they are registered in the
    DI container by importing them.

    Args:
        base_package: Base package name to scan (e.g., "myapp")
        subpackages: List of subpackage paths to scan (default: ["domain", "application", "infrastructure"])
        recursive: Recursively scan subdirectories (default: True)

    Returns:
        int: Number of beans discovered and registered

    Example:
        # Auto-discover beans in default locations
        from vega.discovery import discover_beans

        # Discover in domain, application, infrastructure
        count = discover_beans("myapp")
        print(f"Discovered {count} beans")

        # Custom subpackages
        count = discover_beans(
            "myapp",
            subpackages=["repositories", "services"]
        )

        # Scan specific package recursively
        count = discover_beans("myapp.domain", subpackages=None)

    Note:
        - Classes must be decorated with @bean to be registered
        - The import itself triggers registration (decorator side-effect)
        - Circular imports should be avoided in bean definitions
        - Default subpackages follow Clean Architecture structure
    """

    if subpackages is None:
        # Default Clean Architecture structure
        subpackages = ["domain", "application", "infrastructure"]

    discovered_count = 0
    container = get_container()

    # Track initial services count
    initial_count = len(container._services)

    # If no subpackages specified, scan the base package directly
    if not subpackages:
        subpackages = [""]

    for subpackage in subpackages:
        # Construct full package name
        if subpackage:
            full_package = f"{base_package}.{subpackage}"
        else:
            full_package = base_package

        try:
            # Import the package to get its path
            try:
                package_module = importlib.import_module(full_package)
            except ImportError as e:
                logger.debug(f"Skipping package '{full_package}': {e}")
                continue

            if not hasattr(package_module, '__file__') or package_module.__file__ is None:
                logger.debug(f"Skipping namespace package '{full_package}'")
                continue

            package_dir = Path(package_module.__file__).parent
            logger.debug(f"Discovering beans in: {package_dir}")

            # Scan for Python modules
            if recursive:
                pattern = "**/*.py"
            else:
                pattern = "*.py"

            for file in package_dir.glob(pattern):
                if file.stem.startswith("__"):
                    continue

                # Convert file path to module name
                relative_path = file.relative_to(package_dir.parent)
                module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]
                module_name = ".".join(module_parts)

                try:
                    # Import the module (this triggers @bean decorator)
                    module = importlib.import_module(module_name)

                    # Count beans in this module
                    module_beans = 0
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and is_bean(obj):
                            module_beans += 1

                    if module_beans > 0:
                        logger.info(f"Found {module_beans} bean(s) in {module_name}")
                        discovered_count += module_beans

                except Exception as e:
                    logger.warning(f"Failed to import {module_name}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scanning package '{full_package}': {e}")
            continue

    # Verify beans were registered
    final_count = len(container._services)
    registered_count = final_count - initial_count

    logger.info(
        f"Bean discovery complete: {discovered_count} bean(s) found, "
        f"{registered_count} registered in container"
    )

    return discovered_count


def discover_beans_in_module(module_name: str) -> int:
    """
    Discover @bean decorated classes in a specific module.

    Args:
        module_name: Fully qualified module name (e.g., "myapp.domain.repositories")

    Returns:
        int: Number of beans discovered

    Example:
        from vega.discovery import discover_beans_in_module

        count = discover_beans_in_module("myapp.domain.repositories")
    """
    try:
        module = importlib.import_module(module_name)

        # Count beans in this module
        bean_count = 0
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and is_bean(obj):
                bean_count += 1
                logger.debug(f"Found bean: {obj.__name__} in {module_name}")

        if bean_count > 0:
            logger.info(f"Discovered {bean_count} bean(s) in {module_name}")

        return bean_count

    except ImportError as e:
        logger.error(f"Failed to import module '{module_name}': {e}")
        return 0


def list_registered_beans() -> dict:
    """
    List all currently registered beans in the container.

    Returns:
        dict: Dictionary mapping interface -> implementation

    Example:
        from vega.discovery import list_registered_beans

        beans = list_registered_beans()
        for interface, implementation in beans.items():
            print(f"{interface.__name__} -> {implementation.__name__}")
    """
    container = get_container()
    return dict(container._services)

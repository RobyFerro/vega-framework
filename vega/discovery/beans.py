"""DI Container beans auto-discovery utilities"""
import importlib
import inspect
import logging
import sys
from pathlib import Path
from typing import Optional, List

from vega.di import get_container, is_bean

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

    Example:
        # For base_package="bdc", subpackage="infrastructure.repositories"
        # Returns: /path/to/bdc/infrastructure/repositories
    """
    # Construct the relative path parts
    base_parts = base_package.split('.')
    subpackage_parts = subpackage.split('.') if subpackage else []

    # Search locations: current directory first, then sys.path
    search_paths = [Path.cwd()] + [Path(p) for p in sys.path if p]

    for search_root in search_paths:
        # Strategy 1: Try full path (base_package + subpackage)
        # E.g., looking for "bdc/infrastructure/repositories" from parent dir
        potential_dir = search_root
        for part in base_parts + subpackage_parts:
            potential_dir = potential_dir / part

        if potential_dir.exists() and potential_dir.is_dir():
            if list(potential_dir.glob("*.py")) or list(potential_dir.glob("**/*.py")):
                logger.debug(f"Found package directory via filesystem (full path): {potential_dir}")
                return potential_dir

        # Strategy 2: If we're already inside base_package directory, look for subpackage only
        # E.g., CWD is "/path/to/bdc", looking for "infrastructure/repositories"
        if subpackage_parts:
            potential_dir = search_root
            for part in subpackage_parts:
                potential_dir = potential_dir / part

            if potential_dir.exists() and potential_dir.is_dir():
                if list(potential_dir.glob("*.py")) or list(potential_dir.glob("**/*.py")):
                    logger.debug(f"Found package directory via filesystem (subpackage only): {potential_dir}")
                    return potential_dir

    return None


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
            # Try to get package directory using two approaches:
            # 1. Traditional import (fast, works with regular packages)
            # 2. Filesystem scan (works with PEP 420 namespace packages without __init__.py)
            package_dir = None
            found_via_import = False

            try:
                package_module = importlib.import_module(full_package)
                if hasattr(package_module, '__file__') and package_module.__file__ is not None:
                    package_dir = Path(package_module.__file__).parent
                    found_via_import = True
                    logger.debug(f"Found package via import: {package_dir}")
            except ImportError as e:
                logger.debug(f"Cannot import '{full_package}': {e}, trying filesystem scan...")

            # Fallback: Search filesystem for namespace packages (PEP 420)
            if package_dir is None:
                package_dir = _find_package_dir_from_filesystem(base_package, subpackage)
                if package_dir is None:
                    logger.debug(f"Skipping package '{full_package}': not found")
                    continue

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
                # Handle both cases: regular packages and namespace packages
                try:
                    # Calculate relative path from package_dir
                    relative_path = file.relative_to(package_dir)
                    module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]

                    if found_via_import:
                        # Package was imported successfully - use full_package as prefix
                        if module_parts and module_parts != [file.stem]:
                            # File is in a subdirectory
                            module_name = f"{full_package}.{'.'.join(module_parts)}"
                        else:
                            # File is directly in package_dir
                            module_name = f"{full_package}.{file.stem}"
                    else:
                        # Package found via filesystem - use subpackage only (no base_package)
                        # This handles cases where base_package is not importable
                        if subpackage:
                            if module_parts and module_parts != [file.stem]:
                                module_name = f"{subpackage}.{'.'.join(module_parts)}"
                            else:
                                module_name = f"{subpackage}.{file.stem}"
                        else:
                            # No subpackage, just use module parts
                            module_name = ".".join(module_parts) if module_parts != [file.stem] else file.stem
                except ValueError:
                    # Fallback: use old logic if relative_to fails
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

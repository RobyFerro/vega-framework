"""DI Container beans auto-discovery utilities"""
import importlib
import importlib.util
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
        # Check if this is DDD structure with lib/ or legacy structure
        lib_path = Path.cwd() / "lib"
        if lib_path.exists() and lib_path.is_dir():
            # New DDD structure - scan all bounded contexts
            logger.info("Detected DDD structure with bounded contexts (lib/)")
            contexts = [d.name for d in lib_path.iterdir()
                       if d.is_dir() and not d.name.startswith('_')]
            # Scan all contexts and shared kernel
            subpackages = []
            for context in contexts:
                subpackages.extend([
                    f"lib.{context}.domain",
                    f"lib.{context}.application",
                    f"lib.{context}.infrastructure",
                ])
            # Also scan shared kernel
            if (lib_path / "shared").exists():
                subpackages.append("lib.shared")
        else:
            # Check if this is bounded context structure without lib/ (e.g., myapp/blog/domain, myapp/shared/domain)
            # Try to find the base package directory
            base_parts = base_package.split('.')
            search_paths = [Path.cwd()] + [Path(p) for p in sys.path if p]

            bounded_contexts_detected = False
            for search_root in search_paths:
                potential_base = search_root
                for part in base_parts:
                    potential_base = potential_base / part

                if potential_base.exists() and potential_base.is_dir():
                    # Check if there are subdirectories with domain/application/infrastructure
                    contexts = []
                    for subdir in potential_base.iterdir():
                        if subdir.is_dir() and not subdir.name.startswith('_') and not subdir.name.startswith('.'):
                            # Check if this looks like a bounded context (has domain/ or infrastructure/ subdirectories)
                            has_domain = (subdir / "domain").exists()
                            has_infrastructure = (subdir / "infrastructure").exists()
                            has_application = (subdir / "application").exists()

                            if has_domain or has_infrastructure or has_application:
                                contexts.append(subdir.name)

                    if contexts:
                        # Bounded context structure detected
                        logger.info(f"Detected bounded context structure (without lib/): {contexts}")
                        bounded_contexts_detected = True
                        subpackages = []
                        for context in contexts:
                            # Note: we don't include base_package here as it will be added later
                            # when constructing full_package in the scanning loop
                            subpackages.extend([
                                f"{context}.domain",
                                f"{context}.application",
                                f"{context}.infrastructure",
                            ])
                        break

            if not bounded_contexts_detected:
                # Legacy Clean Architecture structure
                logger.info("Detected legacy Clean Architecture structure")
                subpackages = ["domain", "application", "infrastructure"]

    discovered_count = 0
    container = get_container()

    # Track initial services count
    initial_count = len(container.get_bindings())

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
                else:
                    # Namespace package (PEP 420): use importlib.util.find_spec
                    spec = importlib.util.find_spec(full_package)
                    if spec is not None and spec.submodule_search_locations:
                        # Use first location from namespace package
                        package_dir = Path(spec.submodule_search_locations[0])
                        found_via_import = True
                        logger.debug(f"Found namespace package via find_spec: {package_dir}")
                    else:
                        raise ImportError(f"Package '{full_package}' has no __file__ and no submodule_search_locations")
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

                    # Always use full_package as the prefix
                    # This ensures correct module names whether found via import or filesystem
                    if module_parts and module_parts != [file.stem]:
                        # File is in a subdirectory
                        module_name = f"{full_package}.{'.'.join(module_parts)}"
                    else:
                        # File is directly in package_dir
                        module_name = f"{full_package}.{file.stem}"
                except ValueError:
                    # Fallback: use old logic if relative_to fails
                    relative_path = file.relative_to(package_dir.parent)
                    module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]
                    module_name = ".".join(module_parts)

                try:
                    # Import the module (this triggers @bean decorator)
                    # Try standard import first (works with regular packages)
                    try:
                        module = importlib.import_module(module_name)
                    except (ImportError, ModuleNotFoundError) as import_err:
                        # If standard import fails (e.g., namespace package issue),
                        # use spec_from_file_location to load directly from file
                        # This bypasses the need for package __init__.py files
                        spec = importlib.util.spec_from_file_location(module_name, file)
                        if spec is None or spec.loader is None:
                            raise ImportError(f"Could not create spec for {module_name} from {file}") from import_err
                        
                        module = importlib.util.module_from_spec(spec)
                        # Add parent packages to sys.modules to avoid import errors
                        # when the module imports from parent packages
                        parent_parts = module_name.split('.')[:-1]
                        for i in range(len(parent_parts)):
                            parent_name = '.'.join(parent_parts[:i+1])
                            if parent_name not in sys.modules:
                                # Create a minimal namespace package module
                                parent_module = importlib.util.module_from_spec(
                                    importlib.util.spec_from_loader(parent_name, loader=None)
                                )
                                sys.modules[parent_name] = parent_module
                        
                        # Execute the module (this triggers @bean decorator)
                        spec.loader.exec_module(module)
                        # Store in sys.modules so it can be imported by name later
                        sys.modules[module_name] = module

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
                    import traceback
                    logger.debug(traceback.format_exc())
                    continue

        except Exception as e:
            logger.error(f"Error scanning package '{full_package}': {e}")
            continue

    # Verify beans were registered
    final_count = len(container.get_bindings())
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
    return dict(container.get_bindings())

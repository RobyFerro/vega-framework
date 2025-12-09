"""Vega Web router auto-discovery utilities"""
import importlib
import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from typing import Optional

try:
    from vega.web import Router
except ImportError:
    Router = None

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


def discover_routers(
    base_package: str,
    routes_subpackage: str = "presentation.web.routes",
    api_prefix: str = "/api",
    auto_tags: bool = True,
    auto_prefix: bool = True,
    include_builtin: bool = False,
) -> "Router":
    """
    Auto-discover and register Vega Web routers from a package.

    This function scans a package directory for Python modules containing
    Router instances named 'router' and automatically registers them
    with the main router.

    Args:
        base_package: Base package name (use __package__ from calling module)
        routes_subpackage: Subpackage path containing routes (default: "presentation.web.routes")
        api_prefix: Prefix for the main API router (default: "/api")
        auto_tags: Automatically generate tags from module name (default: True)
        auto_prefix: Automatically generate prefix from module name (default: True)
        include_builtin: (deprecated) include old framework-level builtin routers (default: False)

    Returns:
        Router: Main router with all discovered routers included

    Example:
        # In your project's presentation/web/routes/__init__.py
        from vega.discovery import discover_routers

        router = discover_routers(__package__)

        # Or with custom configuration
        router = discover_routers(
            __package__,
            routes_subpackage="api.routes",
            api_prefix="/v1"
        )

    Note:
        Each route module should export a Router instance named 'router'.
        The module filename will be used for tags and prefix generation if enabled.
    """
    if Router is None:
        raise ImportError(
            "Vega Web is not installed. This should not happen if you're using vega-framework."
        )

    main_router = Router(prefix=api_prefix)

    # Resolve the routes package path
    try:
        # Determine the package to scan
        if base_package.endswith(routes_subpackage):
            routes_package = base_package
        else:
            # Extract base from fully qualified package name
            parts = base_package.split('.')
            # Find the root package (usually the project name)
            root_package = parts[0]
            routes_package = f"{root_package}.{routes_subpackage}"

        # Import the routes package to get its path
        routes_module = importlib.import_module(routes_package)

        # Handle namespace packages (PEP 420) where __file__ can be None
        if hasattr(routes_module, '__file__') and routes_module.__file__ is not None:
            routes_dir = Path(routes_module.__file__).parent
        else:
            # For namespace packages, use importlib.util.find_spec
            spec = importlib.util.find_spec(routes_package)
            if spec is None:
                # Fallback: search filesystem
                parts = routes_package.split('.')
                routes_dir = _find_package_dir_from_filesystem(parts[0], '.'.join(parts[1:]) if len(parts) > 1 else "")
                if routes_dir is None:
                    raise ImportError(f"Cannot locate routes package '{routes_package}' (namespace package without __file__)")
            elif spec.origin is not None:
                routes_dir = Path(spec.origin).parent
            elif spec.submodule_search_locations:
                # Namespace package: use first location from submodule_search_locations
                routes_dir = Path(spec.submodule_search_locations[0])
            else:
                # Fallback: search filesystem
                parts = routes_package.split('.')
                routes_dir = _find_package_dir_from_filesystem(parts[0], '.'.join(parts[1:]) if len(parts) > 1 else "")
                if routes_dir is None:
                    raise ImportError(f"Cannot locate routes package '{routes_package}' (namespace package without __file__)")

        logger.debug(f"Discovering routers in: {routes_dir}")

        # Scan for router modules
        discovered_count = 0
        for file in routes_dir.glob("*.py"):
            if file.stem == "__init__":
                continue

            module_name = f"{routes_package}.{file.stem}"

            try:
                module = importlib.import_module(module_name)

                # Find Router instance named 'router'
                router = getattr(module, 'router', None)

                if isinstance(router, Router):
                    # Generate tags and prefix from module name
                    if auto_tags:
                        tag = file.stem.replace("_", " ").title()
                        tags = [tag]
                    else:
                        tags = None

                    if auto_prefix:
                        prefix = f"/{file.stem.replace('_', '-')}"
                    else:
                        prefix = None

                    main_router.include_router(
                        router,
                        tags=tags,
                        prefix=prefix
                    )
                    discovered_count += 1
                    logger.info(f"Registered router: {module_name} (tags={tags}, prefix={prefix})")
                else:
                    logger.debug(f"No 'router' found in {module_name}")

            except Exception as e:
                logger.warning(f"Failed to import {module_name}: {e}")
                continue

        logger.info(f"Auto-discovery complete: {discovered_count} router(s) registered")

    except ImportError as e:
        logger.error(f"Failed to import routes package '{routes_package}': {e}")
        raise

    return main_router


def discover_routers_ddd(
    base_package: str,
    api_prefix: str = "/api",
    auto_tags: bool = True,
    auto_prefix: bool = True,
    include_builtin: bool = False,
) -> "Router":
    """
    Auto-discover and register Vega Web routers from all bounded contexts (DDD structure).

    This function scans all bounded contexts in lib/ and discovers routers from each context's
    presentation.web.routes package.

    Args:
        base_package: Base package name (usually the project name)
        api_prefix: Prefix for the main API router (default: "/api")
        auto_tags: Automatically generate tags from module name (default: True)
        auto_prefix: Automatically generate prefix from module name (default: True)
        include_builtin: (deprecated) include old framework-level builtin routers (default: False)

    Returns:
        Router: Main router with all discovered routers from all contexts

    Example:
        # In your project's main web entry point
        from vega.discovery import discover_routers_ddd

        app = VegaApp()
        router = discover_routers_ddd("my_project")
        app.include_router(router)

    Note:
        - This function expects a DDD structure with lib/{context}/presentation/web/routes/
        - Falls back to legacy structure if lib/ doesn't exist
        - Each route module should export a Router instance named 'router'
    """
    if Router is None:
        raise ImportError(
            "Vega Web is not installed. This should not happen if you're using vega-framework."
        )

    main_router = Router(prefix=api_prefix)

    try:
        # Try to import base package to check if DDD structure exists
        # First try the package itself (new structure), then lib/ (legacy)
        package_module = None
        package_path_str = None

        try:
            # New structure: contexts directly in base package
            package_module = importlib.import_module(base_package)
            if hasattr(package_module, '__file__') and package_module.__file__ is not None:
                package_path = Path(package_module.__file__).parent
                package_path_str = base_package
            else:
                # Namespace package: use find_spec or filesystem search
                package_path = _find_package_dir_from_filesystem(base_package)
                if package_path is None:
                    raise ImportError(f"Cannot locate package '{base_package}' (namespace package without __file__)")
                package_path_str = base_package
        except (ImportError, AttributeError):
            # Legacy structure: contexts in base_package.lib
            try:
                package_module = importlib.import_module(f"{base_package}.lib")
                if hasattr(package_module, '__file__') and package_module.__file__ is not None:
                    package_path = Path(package_module.__file__).parent
                    package_path_str = f"{base_package}.lib"
                else:
                    # Namespace package: use find_spec or filesystem search
                    package_path = _find_package_dir_from_filesystem(base_package, "lib")
                    if package_path is None:
                        raise ImportError(f"Cannot locate package '{base_package}.lib' (namespace package without __file__)")
                    package_path_str = f"{base_package}.lib"
            except ImportError:
                raise

        logger.info(f"Detected DDD structure in: {package_path}")

        # Get all bounded contexts (directories except __pycache__)
        contexts = [
            d.name for d in package_path.iterdir()
            if d.is_dir() and not d.name.startswith('_')
        ]

        logger.info(f"Found {len(contexts)} bounded context(s): {contexts}")

        total_discovered = 0

        # Discover routers in each context
        for context in contexts:
            routes_package = f"{package_path_str}.{context}.presentation.web.routes"

            try:
                routes_module = importlib.import_module(routes_package)

                # Handle namespace packages (PEP 420) where __file__ can be None
                if hasattr(routes_module, '__file__') and routes_module.__file__ is not None:
                    routes_dir = Path(routes_module.__file__).parent
                else:
                    # For namespace packages, use importlib.util.find_spec
                    spec = importlib.util.find_spec(routes_package)
                    if spec is None:
                        # Fallback: search filesystem
                        parts = routes_package.split('.')
                        routes_dir = _find_package_dir_from_filesystem(parts[0], '.'.join(parts[1:]) if len(parts) > 1 else "")
                        if routes_dir is None:
                            logger.debug(f"Cannot locate routes package '{routes_package}', skipping context '{context}'")
                            continue
                    elif spec.origin is not None:
                        routes_dir = Path(spec.origin).parent
                    elif spec.submodule_search_locations:
                        # Namespace package: use first location from submodule_search_locations
                        routes_dir = Path(spec.submodule_search_locations[0])
                    else:
                        # Fallback: search filesystem
                        parts = routes_package.split('.')
                        routes_dir = _find_package_dir_from_filesystem(parts[0], '.'.join(parts[1:]) if len(parts) > 1 else "")
                        if routes_dir is None:
                            logger.debug(f"Cannot locate routes package '{routes_package}', skipping context '{context}'")
                            continue

                logger.debug(f"Discovering routers in context '{context}': {routes_dir}")

                # Scan for router modules in this context
                for file in routes_dir.glob("*.py"):
                    if file.stem == "__init__":
                        continue

                    module_name = f"{routes_package}.{file.stem}"

                    try:
                        module = importlib.import_module(module_name)
                        router = getattr(module, 'router', None)

                        if isinstance(router, Router):
                            # Special handling: shared/default router hosts framework health at root
                            if context == "shared" and file.stem == "default":
                                tags = ["Health"] if auto_tags else None
                                prefix = ""
                            else:
                                if auto_tags:
                                    tag = f"{context.title()} - {file.stem.replace('_', ' ').title()}"
                                    tags = [tag]
                                else:
                                    tags = None

                                if auto_prefix:
                                    # Use only the bounded context as include prefix;
                                    # route-level prefix is owned by the child router itself.
                                    prefix = f"/{context}"
                                else:
                                    prefix = None

                            main_router.include_router(
                                router,
                                tags=tags,
                                prefix=prefix
                            )
                            total_discovered += 1
                            logger.info(f"Registered router: {module_name} (tags={tags}, prefix={prefix})")

                    except Exception as e:
                        logger.warning(f"Failed to import {module_name}: {e}")
                        continue

            except ImportError:
                logger.debug(f"No web routes found in context '{context}'")
                continue

        logger.info(f"Auto-discovery complete: {total_discovered} router(s) from {len(contexts)} context(s)")

    except ImportError:
        # Fallback to legacy structure
        logger.info("DDD structure not found, falling back to legacy structure")
        return discover_routers(base_package)

    return main_router

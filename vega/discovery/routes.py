"""Vega Web router auto-discovery utilities"""
import importlib
import inspect
import logging
from pathlib import Path
from typing import Optional

try:
    from vega.web import Router
except ImportError:
    Router = None

logger = logging.getLogger(__name__)


def discover_routers(
    base_package: str,
    routes_subpackage: str = "presentation.web.routes",
    api_prefix: str = "/api",
    auto_tags: bool = True,
    auto_prefix: bool = True
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
        routes_dir = Path(routes_module.__file__).parent

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
    auto_prefix: bool = True
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

        # Discover routers in each context
        for context in contexts:
            routes_package = f"{base_package}.lib.{context}.presentation.web.routes"

            try:
                routes_module = importlib.import_module(routes_package)
                routes_dir = Path(routes_module.__file__).parent

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
                            # Generate tags with context name
                            if auto_tags:
                                tag = f"{context.title()} - {file.stem.replace('_', ' ').title()}"
                                tags = [tag]
                            else:
                                tags = None

                            # Generate prefix with context
                            if auto_prefix:
                                prefix = f"/{context}/{file.stem.replace('_', '-')}"
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

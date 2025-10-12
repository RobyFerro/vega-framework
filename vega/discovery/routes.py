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

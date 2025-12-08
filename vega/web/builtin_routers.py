"""Built-in routers for Vega Web Framework"""
from datetime import datetime

from .router import Router


def create_health_router() -> Router:
    """
    Create framework-level health check router.

    This router provides a basic health check endpoint that is automatically
    included in all Vega Web applications. It's intended as a simple liveness probe
    for container orchestration systems (Kubernetes, Docker Compose, etc.).

    Returns:
        Router: Health check router with /health endpoint

    Example:
        The health router is automatically included when using discovery:

        >>> from vega.discovery import discover_routers_ddd
        >>> router = discover_routers_ddd("my_project")  # includes health router
        >>> app.include_router(router)

        Or manually:

        >>> from vega.web.builtin_routers import create_health_router
        >>> health_router = create_health_router()
        >>> app.include_router(health_router)
    """
    router = Router()

    @router.get("/health", summary="Application health check", tags=["Framework"])
    async def health_check():
        """
        Global health check endpoint for the entire application.

        Returns basic health status and current timestamp. This endpoint is intended
        for use as a liveness probe in container orchestration platforms.

        Returns:
            dict: Health status information
                - status (str): "healthy" if the application is running
                - timestamp (str): Current UTC timestamp in ISO format
        """
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }

    return router


__all__ = ["create_health_router"]

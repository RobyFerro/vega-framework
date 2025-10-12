"""Main application class for Vega Web Framework"""

from typing import Any, Callable, Dict, List, Optional, Sequence

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount, Route as StarletteRoute
from starlette.types import ASGIApp
from starlette.responses import JSONResponse as StarletteJSONResponse

from .router import Router
from .exceptions import HTTPException
from .response import JSONResponse
from .openapi import get_openapi_schema
from .docs import get_swagger_ui_html, get_redoc_html


class VegaApp:
    """
    Main application class for Vega Web Framework.

    This is the core ASGI application that handles all HTTP requests.
    It's built on Starlette but provides a FastAPI-like API for familiarity.

    Args:
        title: Application title
        description: Application description
        version: Application version
        debug: Enable debug mode
        middleware: List of middleware to apply
        on_startup: Functions to run on startup
        on_shutdown: Functions to run on shutdown

    Example:
        app = VegaApp(
            title="My API",
            version="1.0.0",
            debug=True
        )

        @app.get("/")
        async def root():
            return {"message": "Hello World"}

        # Or with routers
        router = Router(prefix="/api")
        @router.get("/users")
        async def get_users():
            return {"users": []}

        app.include_router(router)
    """

    def __init__(
        self,
        *,
        title: str = "Vega API",
        description: str = "",
        version: str = "0.1.0",
        debug: bool = False,
        middleware: Optional[Sequence[Middleware]] = None,
        on_startup: Optional[Sequence[Callable]] = None,
        on_shutdown: Optional[Sequence[Callable]] = None,
        docs_url: Optional[str] = "/docs",
        redoc_url: Optional[str] = "/redoc",
        openapi_url: Optional[str] = "/openapi.json",
    ):
        self.title = title
        self.description = description
        self.version = version
        self.debug = debug

        # Documentation URLs (None to disable)
        self.docs_url = docs_url
        self.redoc_url = redoc_url
        self.openapi_url = openapi_url

        # Internal router for top-level routes
        self._router = Router()

        # Middleware stack
        self._middleware = list(middleware) if middleware else []

        # Lifecycle handlers
        self._on_startup = list(on_startup) if on_startup else []
        self._on_shutdown = list(on_shutdown) if on_shutdown else []

        # Starlette app (created lazily)
        self._starlette_app: Optional[Starlette] = None

        # OpenAPI schema (cached)
        self._openapi_schema: Optional[Dict[str, Any]] = None

    def add_middleware(
        self,
        middleware_class: type,
        **options: Any,
    ) -> None:
        """
        Add middleware to the application.

        Args:
            middleware_class: Middleware class
            **options: Middleware configuration options

        Example:
            from starlette.middleware.cors import CORSMiddleware

            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
            )
        """
        self._middleware.append(Middleware(middleware_class, **options))
        # Invalidate cached Starlette app
        self._starlette_app = None

    def on_event(self, event_type: str) -> Callable:
        """
        Register lifecycle event handler.

        Args:
            event_type: Either "startup" or "shutdown"

        Example:
            @app.on_event("startup")
            async def startup():
                print("Starting up!")

            @app.on_event("shutdown")
            async def shutdown():
                print("Shutting down!")
        """

        def decorator(func: Callable) -> Callable:
            if event_type == "startup":
                self._on_startup.append(func)
            elif event_type == "shutdown":
                self._on_shutdown.append(func)
            else:
                raise ValueError(f"Invalid event type: {event_type}")
            # Invalidate cached Starlette app
            self._starlette_app = None
            return func

        return decorator

    def include_router(
        self,
        router: Router,
        prefix: str = "",
        tags: Optional[List[str]] = None,
    ) -> None:
        """
        Include a router in the application.

        Args:
            router: Router to include
            prefix: URL prefix for all routes
            tags: Tags to add to all routes

        Example:
            users_router = Router()
            @users_router.get("/{user_id}")
            async def get_user(user_id: str):
                return {"id": user_id}

            app.include_router(users_router, prefix="/users", tags=["users"])
        """
        self._router.include_router(router, prefix=prefix, tags=tags)
        # Invalidate cached Starlette app
        self._starlette_app = None

    def get(self, path: str, **kwargs: Any) -> Callable:
        """
        Decorator for GET requests.

        Example:
            @app.get("/items/{item_id}")
            async def get_item(item_id: str):
                return {"id": item_id}
        """
        return self._router.get(path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Callable:
        """Decorator for POST requests."""
        return self._router.post(path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Callable:
        """Decorator for PUT requests."""
        return self._router.put(path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> Callable:
        """Decorator for PATCH requests."""
        return self._router.patch(path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Callable:
        """Decorator for DELETE requests."""
        return self._router.delete(path, **kwargs)

    def route(self, path: str, methods: List[str], **kwargs: Any) -> Callable:
        """
        Decorator for custom methods.

        Example:
            @app.route("/items", methods=["GET", "POST"])
            async def items():
                return {"items": []}
        """
        return self._router.route(path, methods, **kwargs)

    def openapi(self) -> Dict[str, Any]:
        """
        Generate and return the OpenAPI schema.

        Returns:
            OpenAPI schema dictionary
        """
        if self._openapi_schema is None:
            self._openapi_schema = get_openapi_schema(
                title=self.title,
                version=self.version,
                description=self.description,
                routes=self._router.get_routes(),
            )
        return self._openapi_schema

    def _build_starlette_app(self) -> Starlette:
        """Build the Starlette application from routes and middleware."""
        # Convert Vega routes to Starlette routes
        starlette_routes = [
            route.to_starlette_route() for route in self._router.get_routes()
        ]

        # Add OpenAPI endpoint
        if self.openapi_url:
            async def openapi_endpoint(request):
                return StarletteJSONResponse(self.openapi())

            starlette_routes.append(
                StarletteRoute(self.openapi_url, endpoint=openapi_endpoint, methods=["GET"])
            )

        # Add Swagger UI endpoint
        if self.docs_url:
            async def swagger_ui_endpoint(request):
                return get_swagger_ui_html(
                    openapi_url=self.openapi_url or "/openapi.json",
                    title=f"{self.title} - Swagger UI"
                )

            starlette_routes.append(
                StarletteRoute(self.docs_url, endpoint=swagger_ui_endpoint, methods=["GET"])
            )

        # Add ReDoc endpoint
        if self.redoc_url:
            async def redoc_endpoint(request):
                return get_redoc_html(
                    openapi_url=self.openapi_url or "/openapi.json",
                    title=f"{self.title} - ReDoc"
                )

            starlette_routes.append(
                StarletteRoute(self.redoc_url, endpoint=redoc_endpoint, methods=["GET"])
            )

        # Create Starlette app
        app = Starlette(
            debug=self.debug,
            routes=starlette_routes,
            middleware=self._middleware,
            on_startup=self._on_startup,
            on_shutdown=self._on_shutdown,
        )

        return app

    def _get_app(self) -> Starlette:
        """Get or create the Starlette app."""
        if self._starlette_app is None:
            self._starlette_app = self._build_starlette_app()
        return self._starlette_app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """
        ASGI application callable.

        This makes VegaApp a valid ASGI application.
        """
        app = self._get_app()
        await app(scope, receive, send)


__all__ = ["VegaApp"]

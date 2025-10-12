"""
Vega Web Framework

A lightweight web framework built on Starlette, providing a FastAPI-like
developer experience while being deeply integrated with Vega's architecture.

Example:
    from vega.web import Router, VegaApp, HTTPException, status

    router = Router()

    @router.get("/users/{user_id}")
    async def get_user(user_id: str):
        if user_id == "invalid":
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user_id, "name": "John"}

    app = VegaApp(title="My API", version="1.0.0")
    app.include_router(router, prefix="/api")

    # Run with: uvicorn main:app --reload
"""

__version__ = "0.1.0"

# Core application
from .application import VegaApp

# Routing
from .router import Router

# Request/Response
from .request import Request
from .response import (
    Response,
    JSONResponse,
    HTMLResponse,
    PlainTextResponse,
    RedirectResponse,
    StreamingResponse,
    FileResponse,
)

# Exceptions
from .exceptions import (
    HTTPException,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    BadRequestError,
    status,
)

# Middleware (optional, can be imported explicitly)
from .middleware import (
    VegaMiddleware,
    CORSMiddleware,
    RequestLoggingMiddleware,
)

# Route middleware
from .route_middleware import (
    RouteMiddleware,
    MiddlewarePhase,
    middleware,
)

# OpenAPI / Documentation
from .openapi import get_openapi_schema
from .docs import get_swagger_ui_html, get_redoc_html

__all__ = [
    # Version
    "__version__",
    # Core
    "VegaApp",
    "Router",
    # Request/Response
    "Request",
    "Response",
    "JSONResponse",
    "HTMLResponse",
    "PlainTextResponse",
    "RedirectResponse",
    "StreamingResponse",
    "FileResponse",
    # Exceptions
    "HTTPException",
    "ValidationError",
    "NotFoundError",
    "UnauthorizedError",
    "ForbiddenError",
    "BadRequestError",
    "status",
    # Middleware
    "VegaMiddleware",
    "CORSMiddleware",
    "RequestLoggingMiddleware",
    # Route Middleware
    "RouteMiddleware",
    "MiddlewarePhase",
    "middleware",
    # OpenAPI / Docs
    "get_openapi_schema",
    "get_swagger_ui_html",
    "get_redoc_html",
]

"""Routing utilities and decorators for Vega Web Framework"""

import inspect
from typing import Any, Callable, Dict, List, Optional, Type, get_type_hints
from functools import wraps

from starlette.routing import Route as StarletteRoute, Mount
from starlette.requests import Request as StarletteRequest

from .exceptions import HTTPException
from .request import Request
from .response import JSONResponse, Response, create_response
from .route_middleware import MiddlewareChain


class Route:
    """
    Represents a single route in the application.

    Args:
        path: URL path pattern (e.g., "/users/{user_id}")
        endpoint: Handler function
        methods: HTTP methods (e.g., ["GET", "POST"])
        name: Optional route name
        include_in_schema: Whether to include in OpenAPI schema
        tags: Tags for documentation
        summary: Short description
        description: Longer description
        response_model: Expected response model type
        status_code: Default status code
    """

    def __init__(
        self,
        path: str,
        endpoint: Callable,
        methods: List[str],
        name: Optional[str] = None,
        include_in_schema: bool = True,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_model: Optional[Type] = None,
        status_code: int = 200,
    ):
        self.path = path
        self.endpoint = endpoint
        self.methods = methods
        self.name = name or endpoint.__name__
        self.include_in_schema = include_in_schema
        self.tags = tags or []
        self.summary = summary
        self.description = description or inspect.getdoc(endpoint)
        self.response_model = response_model
        self.status_code = status_code

        # Extract middleware from endpoint if decorated with @middleware
        self.middlewares = getattr(endpoint, '_route_middlewares', [])

    async def __call__(self, request: StarletteRequest) -> Response:
        """Execute the route handler"""
        return await self.endpoint(request)

    def to_starlette_route(self) -> StarletteRoute:
        """Convert to Starlette Route object"""
        async def wrapped_endpoint(request: StarletteRequest) -> Response:
            """Wrapper that handles request/response conversion and exceptions"""
            try:
                # Use request directly - Request is already a subclass of StarletteRequest
                vega_request = request

                # Get function signature to determine how to call it
                sig = inspect.signature(self.endpoint)
                params = sig.parameters

                # Prepare kwargs for function call
                kwargs = {}

                # Extract path parameters
                path_params = request.path_params

                # Check if function expects Request object
                has_request_param = any(
                    param.annotation == Request or param.name == "request"
                    for param in params.values()
                )

                if has_request_param:
                    kwargs["request"] = vega_request

                # Add path parameters
                for param_name, param_value in path_params.items():
                    if param_name in params:
                        kwargs[param_name] = param_value

                # Execute middleware chain if present
                if self.middlewares:
                    middleware_chain = MiddlewareChain(self.middlewares)
                    # Remove request from kwargs since it's passed separately to middleware
                    handler_kwargs = {k: v for k, v in kwargs.items() if k != "request"}
                    return await middleware_chain.execute(
                        vega_request,
                        self.endpoint,
                        **handler_kwargs
                    )

                # No middleware, call endpoint directly
                if inspect.iscoroutinefunction(self.endpoint):
                    result = await self.endpoint(**kwargs)
                else:
                    result = self.endpoint(**kwargs)

                # Handle different return types
                if isinstance(result, (Response, JSONResponse)):
                    return result
                elif isinstance(result, dict):
                    return JSONResponse(content=result, status_code=self.status_code)
                elif isinstance(result, (list, tuple)):
                    return JSONResponse(content=result, status_code=self.status_code)
                elif isinstance(result, str):
                    return Response(content=result, status_code=self.status_code)
                elif result is None:
                    return Response(content=b"", status_code=self.status_code)
                else:
                    # Try to serialize as JSON
                    return JSONResponse(content=result, status_code=self.status_code)

            except HTTPException as exc:
                # Handle HTTP exceptions
                return JSONResponse(
                    content={"detail": exc.detail},
                    status_code=exc.status_code,
                    headers=exc.headers,
                )
            except Exception as exc:
                # Handle unexpected exceptions
                return JSONResponse(
                    content={"detail": str(exc)},
                    status_code=500,
                )

        return StarletteRoute(
            path=self.path,
            endpoint=wrapped_endpoint,
            methods=self.methods,
            name=self.name,
        )


def route(
    path: str,
    methods: List[str],
    *,
    name: Optional[str] = None,
    include_in_schema: bool = True,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    response_model: Optional[Type] = None,
    status_code: int = 200,
) -> Callable:
    """
    Generic route decorator.

    Args:
        path: URL path pattern
        methods: List of HTTP methods
        name: Optional route name
        include_in_schema: Whether to include in API docs
        tags: Tags for documentation
        summary: Short description
        description: Longer description
        response_model: Expected response type
        status_code: Default HTTP status code

    Example:
        @route("/users", methods=["GET", "POST"])
        async def users_handler():
            return {"users": []}
    """

    def decorator(func: Callable) -> Callable:
        func._route_info = {
            "path": path,
            "methods": methods,
            "name": name,
            "include_in_schema": include_in_schema,
            "tags": tags,
            "summary": summary,
            "description": description,
            "response_model": response_model,
            "status_code": status_code,
        }
        return func

    return decorator


def get(
    path: str,
    *,
    name: Optional[str] = None,
    include_in_schema: bool = True,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    response_model: Optional[Type] = None,
    status_code: int = 200,
) -> Callable:
    """
    GET request decorator.

    Example:
        @get("/users/{user_id}")
        async def get_user(user_id: str):
            return {"id": user_id}
    """
    return route(
        path,
        methods=["GET"],
        name=name,
        include_in_schema=include_in_schema,
        tags=tags,
        summary=summary,
        description=description,
        response_model=response_model,
        status_code=status_code,
    )


def post(
    path: str,
    *,
    name: Optional[str] = None,
    include_in_schema: bool = True,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    response_model: Optional[Type] = None,
    status_code: int = 201,
) -> Callable:
    """
    POST request decorator.

    Example:
        @post("/users")
        async def create_user(request: Request):
            data = await request.json()
            return {"id": "new_user", **data}
    """
    return route(
        path,
        methods=["POST"],
        name=name,
        include_in_schema=include_in_schema,
        tags=tags,
        summary=summary,
        description=description,
        response_model=response_model,
        status_code=status_code,
    )


def put(
    path: str,
    *,
    name: Optional[str] = None,
    include_in_schema: bool = True,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    response_model: Optional[Type] = None,
    status_code: int = 200,
) -> Callable:
    """PUT request decorator."""
    return route(
        path,
        methods=["PUT"],
        name=name,
        include_in_schema=include_in_schema,
        tags=tags,
        summary=summary,
        description=description,
        response_model=response_model,
        status_code=status_code,
    )


def patch(
    path: str,
    *,
    name: Optional[str] = None,
    include_in_schema: bool = True,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    response_model: Optional[Type] = None,
    status_code: int = 200,
) -> Callable:
    """PATCH request decorator."""
    return route(
        path,
        methods=["PATCH"],
        name=name,
        include_in_schema=include_in_schema,
        tags=tags,
        summary=summary,
        description=description,
        response_model=response_model,
        status_code=status_code,
    )


def delete(
    path: str,
    *,
    name: Optional[str] = None,
    include_in_schema: bool = True,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    response_model: Optional[Type] = None,
    status_code: int = 204,
) -> Callable:
    """DELETE request decorator."""
    return route(
        path,
        methods=["DELETE"],
        name=name,
        include_in_schema=include_in_schema,
        tags=tags,
        summary=summary,
        description=description,
        response_model=response_model,
        status_code=status_code,
    )


__all__ = [
    "Route",
    "route",
    "get",
    "post",
    "put",
    "patch",
    "delete",
]

"""Routing utilities and decorators for Vega Web Framework"""

import inspect
from typing import Any, Callable, Dict, List, Optional, Type, get_type_hints, get_origin, get_args, Union
from functools import wraps

from starlette.routing import Route as StarletteRoute, Mount
from starlette.requests import Request as StarletteRequest
from pydantic import BaseModel, ValidationError

from .exceptions import HTTPException
from .request import Request
from .response import JSONResponse, Response, create_response
from .route_middleware import MiddlewareChain
from .params import Query


def _is_pydantic_model(type_hint: Any) -> bool:
    """Check if a type hint is a Pydantic BaseModel"""
    try:
        return inspect.isclass(type_hint) and issubclass(type_hint, BaseModel)
    except (TypeError, AttributeError):
        return False


def _convert_query_param(value: str, target_type: Any) -> Any:
    """
    Convert a query parameter string to the target type.

    This function attempts to convert string values from query parameters to their
    target types. It handles Optional types, special cases like bool and date/datetime,
    and falls back to direct type conversion for any callable type.

    Args:
        value: The string value from the query parameter
        target_type: The target type to convert to

    Returns:
        Converted value

    Raises:
        ValueError: If conversion fails
    """
    from datetime import date, datetime

    # Handle Optional types (e.g., Optional[int] or int | None)
    origin = get_origin(target_type)
    if origin is Union:
        # Get non-None types from Union
        args = get_args(target_type)
        non_none_types = [arg for arg in args if arg is not type(None)]
        if non_none_types:
            target_type = non_none_types[0]
        else:
            return value
    # Handle Python 3.10+ union types (e.g., int | None)
    elif hasattr(target_type, '__class__') and target_type.__class__.__name__ == 'UnionType':
        # For Python 3.10+ union syntax (int | None)
        args = get_args(target_type)
        non_none_types = [arg for arg in args if arg is not type(None)]
        if non_none_types:
            target_type = non_none_types[0]
        else:
            return value

    # Special case: bool requires custom parsing
    # (can't just call bool(value) because bool("false") == True)
    if target_type is bool or target_type == bool:
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        elif value.lower() in ('false', '0', 'no', 'off', ''):
            return False
        else:
            raise ValueError(f"Cannot convert '{value}' to boolean. Expected: true/false, 1/0, yes/no, on/off")

    # Special case: date supports multiple common formats
    if target_type is date or target_type == date:
        for date_format in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue
        raise ValueError(f"Cannot convert '{value}' to date. Expected formats: YYYY-MM-DD, DD/MM/YYYY, or MM/DD/YYYY")

    # Special case: datetime supports ISO format and tries to be lenient
    if target_type is datetime or target_type == datetime:
        try:
            # Try ISO format with timezone
            return datetime.fromisoformat(value)
        except ValueError:
            try:
                # Try common datetime formats
                for dt_format in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%d/%m/%Y %H:%M:%S'):
                    try:
                        return datetime.strptime(value, dt_format)
                    except ValueError:
                        continue
                raise ValueError("No format matched")
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to datetime. Expected ISO format or YYYY-MM-DD HH:MM:SS")

    # General case: try to call the type as a constructor
    # This works for int, float, str, Decimal, UUID, Path, and most simple types
    if callable(target_type):
        try:
            return target_type(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert '{value}' to {target_type.__name__}: {str(e)}")

    # If not callable, just return the string value
    return value


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

                # Get type hints for the function
                try:
                    type_hints = get_type_hints(self.endpoint)
                except Exception:
                    type_hints = {}

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

                # Process query parameters
                query_params = request.query_params
                for param_name, param in params.items():
                    # Skip if already processed (request or path param)
                    if param_name in kwargs or param_name == "request":
                        continue

                    # Get type hint and default value
                    param_type = type_hints.get(param_name, param.annotation)
                    param_default = param.default

                    # Check if this is a Query parameter
                    if isinstance(param_default, Query):
                        query_def = param_default
                        query_key = query_def.alias or param_name

                        # Check if param_type is a list type
                        origin = get_origin(param_type)
                        is_list = origin is list or (hasattr(origin, '__name__') and 'list' in origin.__name__.lower())

                        try:
                            if is_list:
                                # Get all values for list parameters
                                query_values = query_params.getlist(query_key)
                                if query_values:
                                    # Get the element type from list[T]
                                    args = get_args(param_type)
                                    element_type = args[0] if args else str
                                    # Convert each value to the target type
                                    converted_values = [_convert_query_param(val, element_type) for val in query_values]
                                    kwargs[param_name] = converted_values
                                else:
                                    # Use default value or empty list
                                    kwargs[param_name] = query_def.default if query_def.default is not None else []
                            else:
                                # Get single value from query string
                                query_value = query_params.get(query_key)
                                if query_value is not None:
                                    # Convert string to target type
                                    converted_value = _convert_query_param(query_value, param_type)
                                    # Validate using Query rules
                                    validated_value = query_def.validate(converted_value, param_name)
                                    kwargs[param_name] = validated_value
                                else:
                                    # Use default value
                                    kwargs[param_name] = query_def.default
                        except (ValueError, TypeError) as e:
                            return JSONResponse(
                                content={"detail": f"Invalid query parameter '{param_name}': {str(e)}"},
                                status_code=422,
                            )
                    # Handle regular query parameters with type hints (without Query())
                    elif param_name not in kwargs and param_type != inspect.Parameter.empty:
                        # Check if parameter type suggests it might be a query param
                        # (not a Pydantic model, not Request)
                        if not _is_pydantic_model(param_type) and param_type != Request:
                            # Check if param_type is a list type
                            origin = get_origin(param_type)
                            is_list = origin is list or (hasattr(origin, '__name__') and 'list' in origin.__name__.lower())

                            if is_list:
                                # Get all values for list parameters
                                query_values = query_params.getlist(param_name)
                                if query_values:
                                    try:
                                        # Get the element type from list[T]
                                        args = get_args(param_type)
                                        element_type = args[0] if args else str
                                        # Convert each value to the target type
                                        converted_values = [_convert_query_param(val, element_type) for val in query_values]
                                        kwargs[param_name] = converted_values
                                    except (ValueError, TypeError) as e:
                                        return JSONResponse(
                                            content={"detail": f"Invalid query parameter '{param_name}': {str(e)}"},
                                            status_code=422,
                                        )
                                elif param_default != inspect.Parameter.empty:
                                    # Use default value if provided
                                    kwargs[param_name] = param_default
                                else:
                                    # No values provided and no default, use empty list
                                    kwargs[param_name] = []
                            else:
                                # Handle single value
                                query_value = query_params.get(param_name)

                                if query_value is not None:
                                    try:
                                        converted_value = _convert_query_param(query_value, param_type)
                                        kwargs[param_name] = converted_value
                                    except (ValueError, TypeError) as e:
                                        return JSONResponse(
                                            content={"detail": f"Invalid query parameter '{param_name}': {str(e)}"},
                                            status_code=422,
                                        )
                                elif param_default != inspect.Parameter.empty:
                                    # Use default value if provided
                                    kwargs[param_name] = param_default
                                else:
                                    # Check if parameter is optional (Union with None)
                                    origin = get_origin(param_type)
                                    is_optional = False
                                    if origin is Union and type(None) in get_args(param_type):
                                        is_optional = True
                                    # Handle Python 3.10+ union types
                                    elif hasattr(param_type, '__class__') and param_type.__class__.__name__ == 'UnionType':
                                        args = get_args(param_type)
                                        if type(None) in args:
                                            is_optional = True

                                    if is_optional:
                                        kwargs[param_name] = None

                # Check for Pydantic model parameters (body parsing)
                # Only parse the first Pydantic model found
                body_parsed = False
                for param_name, param in params.items():
                    # Skip if already processed (request or path param)
                    if param_name in kwargs or param_name == "request":
                        continue

                    # Get type hint for this parameter
                    param_type = type_hints.get(param_name, param.annotation)

                    # If it's a Pydantic model, parse the request body (only once)
                    if _is_pydantic_model(param_type) and not body_parsed:
                        try:
                            body_data = await request.json()
                            # Validate and parse using Pydantic
                            kwargs[param_name] = param_type(**body_data)
                            body_parsed = True
                        except ValidationError as e:
                            # Return validation errors in a user-friendly format
                            return JSONResponse(
                                content={"detail": e.errors()},
                                status_code=422,
                            )
                        except Exception as e:
                            # Handle JSON parsing errors
                            return JSONResponse(
                                content={"detail": f"Invalid JSON body: {str(e)}"},
                                status_code=400,
                            )

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
                elif isinstance(result, BaseModel):
                    # Serialize Pydantic models using model_dump()
                    return JSONResponse(content=result.model_dump(), status_code=self.status_code)
                elif isinstance(result, dict):
                    return JSONResponse(content=result, status_code=self.status_code)
                elif isinstance(result, (list, tuple)):
                    # Check if list contains Pydantic models
                    if result and isinstance(result[0], BaseModel):
                        # Serialize list of Pydantic models
                        serialized = [item.model_dump() for item in result]
                        return JSONResponse(content=serialized, status_code=self.status_code)
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

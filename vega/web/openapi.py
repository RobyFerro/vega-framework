"""OpenAPI schema generation for Vega Web Framework"""

from typing import Any, Dict, List, Optional, Type, get_type_hints
from inspect import signature, Parameter
import json

try:
    from pydantic import BaseModel
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = None  # type: ignore


def get_openapi_schema(
    *,
    title: str,
    version: str,
    description: str = "",
    routes: List[Any],
    openapi_version: str = "3.0.2",
) -> Dict[str, Any]:
    """
    Generate OpenAPI 3.0 schema from routes.

    Args:
        title: API title
        version: API version
        description: API description
        routes: List of Route objects
        openapi_version: OpenAPI specification version

    Returns:
        OpenAPI schema dictionary
    """
    schema: Dict[str, Any] = {
        "openapi": openapi_version,
        "info": {
            "title": title,
            "version": version,
        },
        "paths": {},
    }

    if description:
        schema["info"]["description"] = description

    # Components for reusable schemas
    components: Dict[str, Any] = {
        "schemas": {}
    }

    # Process each route
    for route in routes:
        path = route.path

        # Convert path parameters from {param} to OpenAPI format
        openapi_path = path

        if openapi_path not in schema["paths"]:
            schema["paths"][openapi_path] = {}

        for method in route.methods:
            method_lower = method.lower()

            operation: Dict[str, Any] = {
                "responses": {
                    "200": {
                        "description": "Successful Response"
                    }
                }
            }

            # Add summary and description
            if route.summary:
                operation["summary"] = route.summary

            if route.description:
                operation["description"] = route.description
            elif route.endpoint.__doc__:
                operation["description"] = route.endpoint.__doc__.strip()

            # Add tags
            if route.tags:
                operation["tags"] = route.tags

            # Add operation ID
            operation["operationId"] = f"{method_lower}_{route.name or route.endpoint.__name__}"

            # Analyze endpoint parameters
            params = _get_parameters(route)
            if params:
                operation["parameters"] = params

            # Analyze request body
            request_body = _get_request_body(route, components)
            if request_body:
                operation["requestBody"] = request_body

            # Analyze response model
            if route.response_model:
                response_schema = _get_response_schema(route.response_model, components)
                if response_schema:
                    operation["responses"]["200"] = {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": response_schema
                            }
                        }
                    }

            # Add status code if specified
            if route.status_code and route.status_code != 200:
                operation["responses"][str(route.status_code)] = operation["responses"].pop("200")

            # Add error responses
            operation["responses"]["422"] = {
                "description": "Validation Error"
            }

            schema["paths"][openapi_path][method_lower] = operation

    # Add components if we have any schemas
    if components["schemas"]:
        schema["components"] = components

    return schema


def _get_parameters(route: Any) -> List[Dict[str, Any]]:
    """Extract path and query parameters from route."""
    parameters = []

    # Get function signature
    sig = signature(route.endpoint)
    type_hints = get_type_hints(route.endpoint)

    # Find which parameters are Pydantic models (request body)
    request_body_params = set()
    if PYDANTIC_AVAILABLE:
        for param_name, param in sig.parameters.items():
            param_type = type_hints.get(param_name)
            if param_type and isinstance(param_type, type) and issubclass(param_type, BaseModel):
                request_body_params.add(param_name)

    for param_name, param in sig.parameters.items():
        # Skip special parameters
        if param_name in ("request", "self", "cls"):
            continue

        # Skip parameters that are Pydantic models (they're in request body)
        if param_name in request_body_params:
            continue

        # Check if it's a path parameter
        if f"{{{param_name}}}" in route.path:
            param_schema = {
                "name": param_name,
                "in": "path",
                "required": True,
                "schema": _get_type_schema(type_hints.get(param_name, str))
            }
            parameters.append(param_schema)
        elif param.default == Parameter.empty:
            # Required query parameter
            param_schema = {
                "name": param_name,
                "in": "query",
                "required": True,
                "schema": _get_type_schema(type_hints.get(param_name, str))
            }
            parameters.append(param_schema)
        else:
            # Optional query parameter
            param_schema = {
                "name": param_name,
                "in": "query",
                "required": False,
                "schema": _get_type_schema(type_hints.get(param_name, str))
            }
            if param.default is not None and param.default != Parameter.empty:
                param_schema["schema"]["default"] = param.default
            parameters.append(param_schema)

    return parameters


def _get_request_body(route: Any, components: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract request body schema from route."""
    if not PYDANTIC_AVAILABLE:
        return None

    # Get function signature
    sig = signature(route.endpoint)
    type_hints = get_type_hints(route.endpoint)

    for param_name, param in sig.parameters.items():
        # Skip special parameters and path parameters
        if param_name in ("request", "self", "cls"):
            continue
        if f"{{{param_name}}}" in route.path:
            continue

        param_type = type_hints.get(param_name)

        # Check if it's a Pydantic model
        if param_type and isinstance(param_type, type) and issubclass(param_type, BaseModel):
            model_name = param_type.__name__

            # Add model schema to components
            if model_name not in components["schemas"]:
                components["schemas"][model_name] = param_type.model_json_schema()

            return {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": f"#/components/schemas/{model_name}"
                        }
                    }
                }
            }

    return None


def _get_response_schema(response_model: Type, components: Dict[str, Any]) -> Dict[str, Any]:
    """Get response schema from response model."""
    if not PYDANTIC_AVAILABLE:
        return {}

    # Handle Pydantic models
    if isinstance(response_model, type) and issubclass(response_model, BaseModel):
        model_name = response_model.__name__

        # Add model schema to components
        if model_name not in components["schemas"]:
            components["schemas"][model_name] = response_model.model_json_schema()

        return {
            "$ref": f"#/components/schemas/{model_name}"
        }

    # Handle List types
    if hasattr(response_model, "__origin__"):
        if response_model.__origin__ is list:
            item_type = response_model.__args__[0]
            if isinstance(item_type, type) and issubclass(item_type, BaseModel):
                model_name = item_type.__name__

                # Add model schema to components
                if model_name not in components["schemas"]:
                    components["schemas"][model_name] = item_type.model_json_schema()

                return {
                    "type": "array",
                    "items": {
                        "$ref": f"#/components/schemas/{model_name}"
                    }
                }

    # Handle dict
    if response_model is dict:
        return {"type": "object"}

    return {}


def _get_type_schema(param_type: Any) -> Dict[str, Any]:
    """Convert Python type to OpenAPI schema."""
    if param_type is str or param_type == "str":
        return {"type": "string"}
    elif param_type is int or param_type == "int":
        return {"type": "integer"}
    elif param_type is float or param_type == "float":
        return {"type": "number"}
    elif param_type is bool or param_type == "bool":
        return {"type": "boolean"}
    elif param_type is list or (hasattr(param_type, "__origin__") and param_type.__origin__ is list):
        return {"type": "array", "items": {}}
    elif param_type is dict:
        return {"type": "object"}
    else:
        return {"type": "string"}


__all__ = ["get_openapi_schema"]

"""Route-level middleware system for Vega Web Framework"""

from typing import Callable, List, Optional, Union, Any
from enum import Enum
from functools import wraps
import inspect

from pydantic import BaseModel

from .request import Request
from .response import Response, JSONResponse


class MiddlewarePhase(str, Enum):
    """When the middleware should execute"""
    BEFORE = "before"  # Execute before the handler
    AFTER = "after"    # Execute after the handler
    BOTH = "both"      # Execute both before and after


class RouteMiddleware:
    """
    Base class for route-level middleware.

    Route middleware can execute before or after the handler function,
    allowing for request preprocessing, response postprocessing, or both.

    Attributes:
        phase: When to execute (BEFORE, AFTER, or BOTH)

    Example:
        class AuthMiddleware(RouteMiddleware):
            def __init__(self):
                super().__init__(phase=MiddlewarePhase.BEFORE)

            async def before(self, request: Request) -> Optional[Response]:
                token = request.headers.get("Authorization")
                if not token:
                    return JSONResponse(
                        {"detail": "Missing authorization"},
                        status_code=401
                    )
                # Continue to handler
                return None

        @router.get("/protected")
        @middleware(AuthMiddleware())
        async def protected_route():
            return {"message": "Protected data"}
    """

    def __init__(self, phase: MiddlewarePhase = MiddlewarePhase.BEFORE):
        self.phase = phase

    async def before(self, request: Request) -> Optional[Response]:
        """
        Execute before the handler.

        Args:
            request: The incoming request

        Returns:
            Optional[Response]: Return a Response to short-circuit,
                              or None to continue to the handler
        """
        return None

    async def after(
        self,
        request: Request,
        response: Response
    ) -> Response:
        """
        Execute after the handler.

        Args:
            request: The incoming request
            response: The response from the handler

        Returns:
            Response: Modified or original response
        """
        return response

    async def process(
        self,
        request: Request,
        handler: Callable,
        **kwargs
    ) -> Response:
        """
        Process the middleware chain.

        Args:
            request: The incoming request
            handler: The route handler function
            **kwargs: Handler keyword arguments

        Returns:
            Response object
        """
        # Execute before phase
        if self.phase in (MiddlewarePhase.BEFORE, MiddlewarePhase.BOTH):
            before_response = await self.before(request)
            if before_response is not None:
                # Short-circuit: return response without calling handler
                return before_response

        # Call the handler
        if inspect.iscoroutinefunction(handler):
            result = await handler(**kwargs)
        else:
            result = handler(**kwargs)

        # Convert result to Response if needed
        if isinstance(result, (Response, JSONResponse)):
            response = result
        elif isinstance(result, BaseModel):
            # Serialize Pydantic models using model_dump()
            response = JSONResponse(content=result.model_dump())
        elif isinstance(result, dict):
            response = JSONResponse(content=result)
        elif isinstance(result, (list, tuple)):
            response = JSONResponse(content=result)
        elif isinstance(result, str):
            response = Response(content=result)
        elif result is None:
            response = Response(content=b"")
        else:
            response = JSONResponse(content=result)

        # Execute after phase
        if self.phase in (MiddlewarePhase.AFTER, MiddlewarePhase.BOTH):
            response = await self.after(request, response)

        return response


class MiddlewareChain:
    """
    Manages a chain of middleware for a route.

    Example:
        chain = MiddlewareChain([AuthMiddleware(), LoggingMiddleware()])
        response = await chain.execute(request, handler, user_id="123")
    """

    def __init__(self, middlewares: List[RouteMiddleware]):
        self.middlewares = middlewares

    async def execute(
        self,
        request: Request,
        handler: Callable,
        **kwargs
    ) -> Response:
        """
        Execute the middleware chain.

        Args:
            request: The incoming request
            handler: The route handler
            **kwargs: Handler arguments

        Returns:
            Response object
        """
        if not self.middlewares:
            # No middleware, call handler directly
            if inspect.iscoroutinefunction(handler):
                result = await handler(**kwargs)
            else:
                result = handler(**kwargs)

            # Convert to response
            if isinstance(result, (Response, JSONResponse)):
                return result
            elif isinstance(result, BaseModel):
                # Serialize Pydantic models using model_dump()
                return JSONResponse(content=result.model_dump())
            elif isinstance(result, dict):
                return JSONResponse(content=result)
            elif isinstance(result, (list, tuple)):
                return JSONResponse(content=result)
            elif isinstance(result, str):
                return Response(content=result)
            elif result is None:
                return Response(content=b"")
            else:
                return JSONResponse(content=result)

        # Execute BEFORE middleware
        for mw in self.middlewares:
            if mw.phase in (MiddlewarePhase.BEFORE, MiddlewarePhase.BOTH):
                before_response = await mw.before(request)
                if before_response is not None:
                    # Short-circuit
                    return before_response

        # Call handler - check if it needs request parameter
        sig = inspect.signature(handler)
        handler_params = sig.parameters

        # Add request to kwargs if handler expects it
        if "request" in handler_params or any(
            p.annotation.__name__ == "Request" if hasattr(p.annotation, "__name__") else False
            for p in handler_params.values()
        ):
            kwargs["request"] = request

        if inspect.iscoroutinefunction(handler):
            result = await handler(**kwargs)
        else:
            result = handler(**kwargs)

        # Convert to response
        if isinstance(result, (Response, JSONResponse)):
            response = result
        elif isinstance(result, BaseModel):
            # Serialize Pydantic models using model_dump()
            response = JSONResponse(content=result.model_dump())
        elif isinstance(result, dict):
            response = JSONResponse(content=result)
        elif isinstance(result, (list, tuple)):
            response = JSONResponse(content=result)
        elif isinstance(result, str):
            response = Response(content=result)
        elif result is None:
            response = Response(content=b"")
        else:
            response = JSONResponse(content=result)

        # Execute AFTER middleware (in reverse order)
        for mw in reversed(self.middlewares):
            if mw.phase in (MiddlewarePhase.AFTER, MiddlewarePhase.BOTH):
                response = await mw.after(request, response)

        return response


def middleware(*middlewares: RouteMiddleware) -> Callable:
    """
    Decorator to attach middleware to a route handler.

    Args:
        *middlewares: One or more RouteMiddleware instances

    Example:
        @router.get("/users/{user_id}")
        @middleware(AuthMiddleware(), LoggingMiddleware())
        async def get_user(user_id: str):
            return {"id": user_id}

        # Or single middleware
        @router.post("/admin/action")
        @middleware(AdminOnlyMiddleware())
        async def admin_action():
            return {"status": "done"}
    """
    middleware_list = list(middlewares)

    def decorator(func: Callable) -> Callable:
        # Store middleware list on the function
        if not hasattr(func, '_route_middlewares'):
            func._route_middlewares = []
        func._route_middlewares.extend(middleware_list)
        return func

    return decorator


__all__ = [
    "RouteMiddleware",
    "MiddlewarePhase",
    "MiddlewareChain",
    "middleware",
]

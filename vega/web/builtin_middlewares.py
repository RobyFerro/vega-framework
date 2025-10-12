"""Built-in route middleware implementations for Vega Web Framework"""

import time
import logging
from typing import Optional

from .route_middleware import RouteMiddleware, MiddlewarePhase
from .request import Request
from .response import Response, JSONResponse
from .exceptions import HTTPException, status


class AuthMiddleware(RouteMiddleware):
    """
    Authentication middleware - validates Authorization header.

    Executes BEFORE the handler.

    Args:
        header_name: Name of the header to check (default: "Authorization")
        scheme: Expected auth scheme (default: "Bearer")

    Example:
        @router.get("/protected")
        @middleware(AuthMiddleware())
        async def protected_route():
            return {"data": "secret"}
    """

    def __init__(self, header_name: str = "Authorization", scheme: str = "Bearer"):
        super().__init__(phase=MiddlewarePhase.BEFORE)
        self.header_name = header_name
        self.scheme = scheme

    async def before(self, request: Request) -> Optional[Response]:
        """Check for valid authentication token"""
        auth_header = request.headers.get(self.header_name.lower())

        if not auth_header:
            return JSONResponse(
                content={"detail": "Missing authentication credentials"},
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": f"{self.scheme}"},
            )

        # Parse scheme and token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != self.scheme.lower():
            return JSONResponse(
                content={"detail": f"Invalid authentication scheme. Expected: {self.scheme}"},
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": f"{self.scheme}"},
            )

        token = parts[1]

        # TODO: Validate token here (this is a simple example)
        if token == "invalid":
            return JSONResponse(
                content={"detail": "Invalid or expired token"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        # Store user info in request state for handler to use
        request.state.user_id = "user_from_token"
        request.state.token = token

        return None  # Continue to handler


class TimingMiddleware(RouteMiddleware):
    """
    Request timing middleware - measures execution time.

    Executes BOTH before and after the handler.

    Example:
        @router.get("/slow-operation")
        @middleware(TimingMiddleware())
        async def slow_operation():
            await asyncio.sleep(1)
            return {"status": "done"}
    """

    def __init__(self):
        super().__init__(phase=MiddlewarePhase.BOTH)
        self.logger = logging.getLogger("vega.web.timing")

    async def before(self, request: Request) -> Optional[Response]:
        """Record start time"""
        request.state.start_time = time.time()
        return None

    async def after(self, request: Request, response: Response) -> Response:
        """Calculate and log execution time"""
        if hasattr(request.state, "start_time"):
            duration = time.time() - request.state.start_time
            self.logger.info(
                f"{request.method} {request.url.path} completed in {duration:.3f}s"
            )

            # Add timing header to response
            if hasattr(response, "headers"):
                response.headers["X-Process-Time"] = f"{duration:.3f}"

        return response


class CacheControlMiddleware(RouteMiddleware):
    """
    Cache control middleware - adds cache headers to response.

    Executes AFTER the handler.

    Args:
        max_age: Cache max age in seconds
        public: Whether cache is public (default: True)

    Example:
        @router.get("/static-data")
        @middleware(CacheControlMiddleware(max_age=3600))
        async def get_static_data():
            return {"data": "rarely changes"}
    """

    def __init__(self, max_age: int = 300, public: bool = True):
        super().__init__(phase=MiddlewarePhase.AFTER)
        self.max_age = max_age
        self.public = public

    async def after(self, request: Request, response: Response) -> Response:
        """Add cache control headers"""
        cache_type = "public" if self.public else "private"
        cache_value = f"{cache_type}, max-age={self.max_age}"

        if hasattr(response, "headers"):
            response.headers["Cache-Control"] = cache_value

        return response


class CORSMiddleware(RouteMiddleware):
    """
    CORS middleware for specific routes.

    Executes AFTER the handler to add CORS headers.

    Args:
        allow_origins: List of allowed origins or "*"
        allow_methods: List of allowed methods
        allow_headers: List of allowed headers

    Example:
        @router.get("/public-api/data")
        @middleware(CORSMiddleware(allow_origins=["*"]))
        async def public_data():
            return {"data": "public"}
    """

    def __init__(
        self,
        allow_origins: list = None,
        allow_methods: list = None,
        allow_headers: list = None,
    ):
        super().__init__(phase=MiddlewarePhase.AFTER)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]

    async def after(self, request: Request, response: Response) -> Response:
        """Add CORS headers to response"""
        if hasattr(response, "headers"):
            origin = request.headers.get("origin", "*")

            if "*" in self.allow_origins or origin in self.allow_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = ", ".join(
                    self.allow_methods
                )
                response.headers["Access-Control-Allow-Headers"] = ", ".join(
                    self.allow_headers
                )

        return response


class RateLimitMiddleware(RouteMiddleware):
    """
    Simple rate limiting middleware.

    Executes BEFORE the handler.

    Args:
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds

    Example:
        @router.post("/expensive-operation")
        @middleware(RateLimitMiddleware(max_requests=10, window_seconds=60))
        async def expensive_op():
            return {"status": "processing"}
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(phase=MiddlewarePhase.BEFORE)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # IP -> [timestamps]

    async def before(self, request: Request) -> Optional[Response]:
        """Check rate limit"""
        from datetime import datetime, timedelta

        client_ip = request.client.host if request.client else "unknown"
        now = datetime.now()

        # Clean old entries
        if client_ip in self.requests:
            cutoff = now - timedelta(seconds=self.window_seconds)
            self.requests[client_ip] = [
                ts for ts in self.requests[client_ip] if ts > cutoff
            ]

        # Check limit
        if client_ip in self.requests:
            if len(self.requests[client_ip]) >= self.max_requests:
                return JSONResponse(
                    content={
                        "detail": f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s"
                    },
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={
                        "Retry-After": str(self.window_seconds),
                        "X-RateLimit-Limit": str(self.max_requests),
                        "X-RateLimit-Remaining": "0",
                    },
                )

        # Record request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(now)

        return None


class LoggingMiddleware(RouteMiddleware):
    """
    Request/Response logging middleware.

    Executes BOTH before and after.

    Example:
        @router.post("/important-action")
        @middleware(LoggingMiddleware())
        async def important_action():
            return {"status": "done"}
    """

    def __init__(self, logger_name: str = "vega.web.routes"):
        super().__init__(phase=MiddlewarePhase.BOTH)
        self.logger = logging.getLogger(logger_name)

    async def before(self, request: Request) -> Optional[Response]:
        """Log incoming request"""
        self.logger.info(
            f"→ {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        return None

    async def after(self, request: Request, response: Response) -> Response:
        """Log response"""
        self.logger.info(
            f"← {request.method} {request.url.path} [{response.status_code}]"
        )
        return response


__all__ = [
    "AuthMiddleware",
    "TimingMiddleware",
    "CacheControlMiddleware",
    "CORSMiddleware",
    "RateLimitMiddleware",
    "LoggingMiddleware",
]

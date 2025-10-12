"""Middleware utilities for Vega Web Framework"""

from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class VegaMiddleware(BaseHTTPMiddleware):
    """
    Base middleware class for Vega applications.

    Extend this class to create custom middleware.

    Example:
        class LoggingMiddleware(VegaMiddleware):
            async def dispatch(self, request: Request, call_next: Callable) -> Response:
                print(f"Request: {request.method} {request.url.path}")
                response = await call_next(request)
                print(f"Response: {response.status_code}")
                return response

        app.add_middleware(LoggingMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request.

        Args:
            request: Incoming request
            call_next: Function to call next middleware or endpoint

        Returns:
            Response object
        """
        return await call_next(request)


class CORSMiddleware:
    """
    CORS (Cross-Origin Resource Sharing) middleware.

    This is a re-export of Starlette's CORSMiddleware for convenience.

    Example:
        from vega.web import VegaApp
        from vega.web.middleware import CORSMiddleware

        app = VegaApp()
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    """

    # This will be imported from Starlette
    from starlette.middleware.cors import CORSMiddleware as _CORSMiddleware

    def __new__(cls, *args, **kwargs):
        return cls._CORSMiddleware(*args, **kwargs)


class TrustedHostMiddleware:
    """
    Middleware to validate the Host header.

    This is a re-export of Starlette's TrustedHostMiddleware.

    Example:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["example.com", "*.example.com"]
        )
    """

    from starlette.middleware.trustedhost import TrustedHostMiddleware as _TrustedHostMiddleware

    def __new__(cls, *args, **kwargs):
        return cls._TrustedHostMiddleware(*args, **kwargs)


class GZipMiddleware:
    """
    Middleware to compress responses using GZip.

    This is a re-export of Starlette's GZipMiddleware.

    Example:
        app.add_middleware(GZipMiddleware, minimum_size=1000)
    """

    from starlette.middleware.gzip import GZipMiddleware as _GZipMiddleware

    def __new__(cls, *args, **kwargs):
        return cls._GZipMiddleware(*args, **kwargs)


class RateLimitMiddleware(VegaMiddleware):
    """
    Simple rate limiting middleware (example implementation).

    Args:
        requests_per_minute: Maximum requests per minute per IP

    Example:
        app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict = {}  # IP -> [timestamps]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit before processing request"""
        from datetime import datetime, timedelta

        client_ip = request.client.host if request.client else "unknown"
        now = datetime.now()

        # Clean old entries
        if client_ip in self.requests:
            cutoff = now - timedelta(minutes=1)
            self.requests[client_ip] = [
                ts for ts in self.requests[client_ip] if ts > cutoff
            ]

        # Check rate limit
        if client_ip in self.requests:
            if len(self.requests[client_ip]) >= self.requests_per_minute:
                from ..response import JSONResponse
                return JSONResponse(
                    content={"detail": "Rate limit exceeded"},
                    status_code=429,
                )

        # Record request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(now)

        return await call_next(request)


class RequestLoggingMiddleware(VegaMiddleware):
    """
    Middleware to log all requests.

    Example:
        app.add_middleware(RequestLoggingMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response"""
        import logging
        import time

        logger = logging.getLogger("vega.web")

        start_time = time.time()
        logger.info(f"→ {request.method} {request.url.path}")

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            f"← {request.method} {request.url.path} "
            f"[{response.status_code}] {process_time:.3f}s"
        )

        return response


__all__ = [
    "VegaMiddleware",
    "CORSMiddleware",
    "TrustedHostMiddleware",
    "GZipMiddleware",
    "RateLimitMiddleware",
    "RequestLoggingMiddleware",
]

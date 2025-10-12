"""Test Vega Web route middleware system"""

import asyncio
from vega.web import (
    VegaApp,
    Router,
    Request,
    RouteMiddleware,
    MiddlewarePhase,
    middleware,
    status,
)
from vega.web.builtin_middlewares import (
    AuthMiddleware,
    TimingMiddleware,
    CacheControlMiddleware,
    LoggingMiddleware,
)


# Create app
app = VegaApp(title="Middleware Test", version="1.0.0", debug=True)
router = Router(prefix="/api")


# Example 1: Auth middleware (BEFORE)
@router.get("/protected")
@middleware(AuthMiddleware())
async def protected_route():
    """Protected endpoint requiring authentication"""
    return {"message": "You are authenticated!", "data": "secret"}


# Example 2: Multiple middleware (timing + logging)
@router.get("/timed")
@middleware(TimingMiddleware(), LoggingMiddleware())
async def timed_route():
    """Route with timing and logging"""
    await asyncio.sleep(0.1)  # Simulate work
    return {"message": "Operation completed"}


# Example 3: Cache control (AFTER)
@router.get("/cached")
@middleware(CacheControlMiddleware(max_age=3600))
async def cached_route():
    """Route with cache control headers"""
    return {"data": "This response is cacheable", "timestamp": "2024-01-01"}


# Example 4: Custom middleware
class CustomHeaderMiddleware(RouteMiddleware):
    """Add custom header to response"""

    def __init__(self, header_name: str, header_value: str):
        super().__init__(phase=MiddlewarePhase.AFTER)
        self.header_name = header_name
        self.header_value = header_value

    async def after(self, request: Request, response):
        """Add custom header"""
        if hasattr(response, "headers"):
            response.headers[self.header_name] = self.header_value
        return response


@router.get("/custom")
@middleware(CustomHeaderMiddleware("X-Custom-Header", "CustomValue"))
async def custom_middleware_route():
    """Route with custom middleware"""
    return {"message": "Check the headers!"}


# Example 5: Before and After middleware
class RequestValidationMiddleware(RouteMiddleware):
    """Validate request and modify response"""

    def __init__(self):
        super().__init__(phase=MiddlewarePhase.BOTH)

    async def before(self, request: Request):
        """Validate request has required header"""
        if not request.headers.get("x-api-version"):
            from vega.web import JSONResponse
            return JSONResponse(
                {"detail": "Missing X-API-Version header"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return None

    async def after(self, request: Request, response):
        """Add version to response"""
        if hasattr(response, "headers"):
            api_version = request.headers.get("x-api-version", "unknown")
            response.headers["X-API-Version-Echo"] = api_version
        return response


@router.post("/validated")
@middleware(RequestValidationMiddleware())
async def validated_route(request: Request):
    """Route with validation middleware"""
    data = await request.json()
    return {"message": "Data validated and processed", "received": data}


# Example 6: Chaining multiple middleware
@router.get("/chained")
@middleware(
    LoggingMiddleware(),
    TimingMiddleware(),
    CacheControlMiddleware(max_age=60)
)
async def chained_middleware_route():
    """Route with multiple chained middleware"""
    return {"message": "Multiple middleware executed in order"}


# Include router
app.include_router(router)


# Simple routes without middleware for comparison
@app.get("/")
async def root():
    """Root endpoint without middleware"""
    return {"message": "No middleware here", "tip": "Try /api/protected"}


if __name__ == "__main__":
    print("=== Vega Web Middleware Test Server ===")
    print("\nAvailable endpoints:")
    print("  GET  /                    - No middleware")
    print("  GET  /api/protected       - Auth middleware (requires Bearer token)")
    print("  GET  /api/timed           - Timing + Logging middleware")
    print("  GET  /api/cached          - Cache control middleware")
    print("  GET  /api/custom          - Custom header middleware")
    print("  POST /api/validated       - Request validation middleware")
    print("  GET  /api/chained         - Multiple chained middleware")
    print("\nTest commands:")
    print("  # No auth (should fail)")
    print("  curl http://localhost:8000/api/protected")
    print()
    print("  # With auth (should succeed)")
    print("  curl -H 'Authorization: Bearer mytoken' http://localhost:8000/api/protected")
    print()
    print("  # Check timing header")
    print("  curl -i http://localhost:8000/api/timed")
    print()
    print("  # Check cache headers")
    print("  curl -i http://localhost:8000/api/cached")
    print()
    print("  # Validation (should fail)")
    print("  curl -X POST http://localhost:8000/api/validated -d '{}'")
    print()
    print("  # Validation (should succeed)")
    print("  curl -X POST -H 'X-API-Version: 1.0' http://localhost:8000/api/validated -d '{\"test\": \"data\"}'")
    print()

    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

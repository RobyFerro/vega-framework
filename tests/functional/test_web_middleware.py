"""Functional tests for Vega Web middleware system"""

import asyncio
import pytest
from starlette.testclient import TestClient
from vega.web import (
    VegaApp,
    Router,
    Request,
    RouteMiddleware,
    MiddlewarePhase,
    middleware,
    status,
    JSONResponse,
)
from vega.web.builtin_middlewares import (
    AuthMiddleware,
    TimingMiddleware,
    CacheControlMiddleware,
    LoggingMiddleware,
)


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


class RequestValidationMiddleware(RouteMiddleware):
    """Validate request and modify response"""

    def __init__(self):
        super().__init__(phase=MiddlewarePhase.BOTH)

    async def before(self, request: Request):
        """Validate request has required header"""
        if not request.headers.get("x-api-version"):
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


@pytest.fixture
def app():
    """Create test application with middleware"""
    app = VegaApp(title="Middleware Test", version="1.0.0", debug=True)
    router = Router(prefix="/api")

    @app.get("/")
    async def root():
        """Root endpoint without middleware"""
        return {"message": "No middleware here"}

    @router.get("/protected")
    @middleware(AuthMiddleware())
    async def protected_route():
        """Protected endpoint requiring authentication"""
        return {"message": "You are authenticated!", "data": "secret"}

    @router.get("/timed")
    @middleware(TimingMiddleware(), LoggingMiddleware())
    async def timed_route():
        """Route with timing and logging"""
        await asyncio.sleep(0.1)  # Simulate work
        return {"message": "Operation completed"}

    @router.get("/cached")
    @middleware(CacheControlMiddleware(max_age=3600))
    async def cached_route():
        """Route with cache control headers"""
        return {"data": "This response is cacheable"}

    @router.get("/custom")
    @middleware(CustomHeaderMiddleware("X-Custom-Header", "CustomValue"))
    async def custom_middleware_route():
        """Route with custom middleware"""
        return {"message": "Check the headers!"}

    @router.post("/validated")
    @middleware(RequestValidationMiddleware())
    async def validated_route(request: Request):
        """Route with validation middleware"""
        data = await request.json()
        return {"message": "Data validated and processed", "received": data}

    @router.get("/chained")
    @middleware(
        LoggingMiddleware(),
        TimingMiddleware(),
        CacheControlMiddleware(max_age=60)
    )
    async def chained_middleware_route():
        """Route with multiple chained middleware"""
        return {"message": "Multiple middleware executed in order"}

    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


class TestNoMiddleware:
    """Test routes without middleware"""

    def test_root_no_middleware(self, client):
        """Test route without middleware works correctly"""
        response = client.get("/")
        assert response.status_code == 200
        assert "No middleware" in response.json()["message"]


class TestAuthMiddleware:
    """Test authentication middleware"""

    def test_missing_token(self, client):
        """Test auth middleware rejects requests without token"""
        response = client.get("/api/protected")
        assert response.status_code == 401
        assert "Missing authentication" in response.json()["detail"]
        assert "WWW-Authenticate" in response.headers

    def test_invalid_token(self, client):
        """Test auth middleware rejects invalid tokens"""
        response = client.get(
            "/api/protected",
            headers={"Authorization": "Bearer invalid"}
        )
        assert response.status_code == 401
        assert "Invalid or expired" in response.json()["detail"]

    def test_valid_token(self, client):
        """Test auth middleware accepts valid tokens"""
        response = client.get(
            "/api/protected",
            headers={"Authorization": "Bearer mytoken"}
        )
        assert response.status_code == 200
        assert "authenticated" in response.json()["message"]


class TestTimingMiddleware:
    """Test timing middleware"""

    def test_timing_header_present(self, client):
        """Test timing middleware adds process time header"""
        response = client.get("/api/timed")
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers

    def test_timing_accuracy(self, client):
        """Test timing middleware measures time accurately"""
        response = client.get("/api/timed")
        process_time = float(response.headers["X-Process-Time"])
        # Should take at least 0.1s due to sleep
        assert process_time >= 0.1


class TestCacheControlMiddleware:
    """Test cache control middleware"""

    def test_cache_headers(self, client):
        """Test cache control middleware adds correct headers"""
        response = client.get("/api/cached")
        assert response.status_code == 200
        assert "Cache-Control" in response.headers
        assert "max-age=3600" in response.headers["Cache-Control"]


class TestCustomMiddleware:
    """Test custom middleware"""

    def test_custom_header(self, client):
        """Test custom middleware adds custom headers"""
        response = client.get("/api/custom")
        assert response.status_code == 200
        assert "X-Custom-Header" in response.headers
        assert response.headers["X-Custom-Header"] == "CustomValue"


class TestValidationMiddleware:
    """Test validation middleware"""

    def test_missing_required_header(self, client):
        """Test validation middleware rejects missing headers"""
        response = client.post("/api/validated", json={"test": "data"})
        assert response.status_code == 400
        assert "Missing X-API-Version" in response.json()["detail"]

    def test_with_required_header(self, client):
        """Test validation middleware accepts valid requests"""
        response = client.post(
            "/api/validated",
            json={"test": "data"},
            headers={"X-API-Version": "1.0"}
        )
        assert response.status_code == 200
        assert "validated" in response.json()["message"]
        assert "X-API-Version-Echo" in response.headers
        assert response.headers["X-API-Version-Echo"] == "1.0"


class TestChainedMiddleware:
    """Test multiple chained middleware"""

    def test_multiple_middleware(self, client):
        """Test multiple middleware execute in correct order"""
        response = client.get("/api/chained")
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        assert "Cache-Control" in response.headers
        assert "max-age=60" in response.headers["Cache-Control"]

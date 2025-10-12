"""Functional tests for Vega Web endpoints"""

import pytest
from starlette.testclient import TestClient
from vega.web import (
    VegaApp,
    Router,
    HTTPException,
    status,
    Request,
    middleware,
)
from vega.web.builtin_middlewares import (
    AuthMiddleware,
    TimingMiddleware,
    LoggingMiddleware,
)


@pytest.fixture
def app():
    """Create test application"""
    app = VegaApp(
        title="Vega Web Demo API",
        version="1.0.0",
        debug=True
    )

    router = Router(prefix="/api")

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {"message": "Hello from Vega Web!"}

    @app.get("/health")
    def health_check():
        """Health check (sync handler)"""
        return {"status": "ok"}

    @router.get("/users/{user_id}")
    @middleware(TimingMiddleware())
    async def get_user(user_id: str):
        """Get user by ID with timing"""
        if user_id == "invalid":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return {"id": user_id, "name": "John Doe"}

    @router.post("/users")
    @middleware(LoggingMiddleware())
    async def create_user(request: Request):
        """Create a new user with logging"""
        try:
            data = await request.json()
            return {
                "id": "new_user_123",
                "name": data.get("name", "Unknown"),
                "email": data.get("email", "unknown@example.com")
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request body: {str(e)}"
            )

    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


class TestBasicEndpoints:
    """Test basic endpoints without middleware"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns correct response"""
        response = client.get('/')
        assert response.status_code == 200
        assert response.json() == {"message": "Hello from Vega Web!"}

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestUserEndpoints:
    """Test user-related endpoints"""

    def test_get_user_success(self, client):
        """Test successful user retrieval"""
        response = client.get('/api/users/123')
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "123"
        assert data["name"] == "John Doe"

    def test_get_user_not_found(self, client):
        """Test user not found returns 404"""
        response = client.get('/api/users/invalid')
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_user_success(self, client):
        """Test successful user creation"""
        user_data = {'name': 'Alice', 'email': 'alice@example.com'}
        response = client.post('/api/users', json=user_data)

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["name"] == "Alice"
        assert data["email"] == "alice@example.com"
        assert "id" in data

    def test_create_user_with_defaults(self, client):
        """Test user creation with default values"""
        response = client.post('/api/users', json={})
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["name"] == "Unknown"
        assert data["email"] == "unknown@example.com"

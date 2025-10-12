"""Unit tests for Web Router"""

import pytest
from vega.web import Router, HTTPException, status


class TestRouterBasics:
    """Test basic router functionality"""

    def test_router_initialization(self):
        """Test router can be initialized"""
        router = Router()
        assert router is not None

    def test_router_with_prefix(self):
        """Test router initialization with prefix"""
        router = Router(prefix="/api")
        assert router.prefix == "/api"

    def test_router_with_tags(self):
        """Test router initialization with tags"""
        router = Router(tags=["users", "api"])
        assert "users" in router.tags
        assert "api" in router.tags


class TestRouteRegistration:
    """Test route registration"""

    def test_get_route_decorator(self):
        """Test @router.get() decorator"""
        router = Router()

        @router.get("/users")
        async def get_users():
            return {"users": []}

        assert len(router.routes) > 0

    def test_post_route_decorator(self):
        """Test @router.post() decorator"""
        router = Router()

        @router.post("/users")
        async def create_user():
            return {"id": "123"}

        assert len(router.routes) > 0

    def test_put_route_decorator(self):
        """Test @router.put() decorator"""
        router = Router()

        @router.put("/users/{user_id}")
        async def update_user(user_id: str):
            return {"id": user_id}

        assert len(router.routes) > 0

    def test_delete_route_decorator(self):
        """Test @router.delete() decorator"""
        router = Router()

        @router.delete("/users/{user_id}")
        async def delete_user(user_id: str):
            return {"deleted": user_id}

        assert len(router.routes) > 0


class TestRouteParameters:
    """Test route parameters"""

    def test_path_parameters(self):
        """Test path parameters in routes"""
        router = Router()

        @router.get("/users/{user_id}")
        async def get_user(user_id: str):
            return {"id": user_id}

        # Path should contain parameter
        route = router.routes[0]
        assert "{user_id}" in str(route.path)

    def test_multiple_path_parameters(self):
        """Test multiple path parameters"""
        router = Router()

        @router.get("/users/{user_id}/posts/{post_id}")
        async def get_post(user_id: str, post_id: str):
            return {"user_id": user_id, "post_id": post_id}

        route = router.routes[0]
        assert "{user_id}" in str(route.path)
        assert "{post_id}" in str(route.path)


class TestRouteMetadata:
    """Test route metadata"""

    def test_route_with_name(self):
        """Test route with custom name"""
        router = Router()

        @router.get("/users", name="list_users")
        async def get_users():
            return []

        route = router.routes[0]
        assert route.name == "list_users"

    def test_route_with_tags(self):
        """Test route with tags"""
        router = Router()

        @router.get("/users", tags=["users"])
        async def get_users():
            return []

        route = router.routes[0]
        if hasattr(route, 'tags'):
            assert "users" in route.tags


class TestHTTPException:
    """Test HTTP exceptions"""

    def test_http_exception_creation(self):
        """Test creating HTTP exception"""
        exc = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
        assert exc.status_code == 404
        assert exc.detail == "Not found"

    def test_http_exception_with_headers(self):
        """Test HTTP exception with custom headers"""
        exc = HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"}
        )
        assert exc.status_code == 401
        assert exc.headers["WWW-Authenticate"] == "Bearer"

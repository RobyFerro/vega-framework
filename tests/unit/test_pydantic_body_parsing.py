"""Tests for automatic Pydantic body parsing in routes"""

import pytest
from pydantic import BaseModel, Field
from vega.web import Router, VegaApp
from starlette.testclient import TestClient


class CreateUserRequest(BaseModel):
    """Request model for creating a user"""
    name: str = Field(..., min_length=1)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: int = Field(..., ge=0, le=150)


class UserResponse(BaseModel):
    """Response model for user"""
    id: str
    name: str
    email: str
    age: int


class TestPydanticBodyParsing:
    """Test automatic Pydantic model body parsing"""

    def test_automatic_body_parsing(self):
        """Test that Pydantic models are automatically parsed from request body"""
        router = Router()

        @router.post("/users", response_model=UserResponse)
        async def create_user(user_data: CreateUserRequest) -> UserResponse:
            """Create a new user"""
            return UserResponse(
                id="test-123",
                name=user_data.name,
                email=user_data.email,
                age=user_data.age
            )

        app = VegaApp()
        app.include_router(router)

        client = TestClient(app)

        # Test valid request
        response = client.post(
            "/users",
            json={"name": "John Doe", "email": "john@example.com", "age": 30}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "test-123"
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert data["age"] == 30

    def test_validation_error_returns_422(self):
        """Test that validation errors return 422 status code"""
        router = Router()

        @router.post("/users")
        async def create_user(user_data: CreateUserRequest) -> dict:
            return {"success": True}

        app = VegaApp()
        app.include_router(router)

        client = TestClient(app)

        # Test invalid email
        response = client.post(
            "/users",
            json={"name": "John", "email": "invalid-email", "age": 30}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_missing_field_returns_422(self):
        """Test that missing required fields return 422"""
        router = Router()

        @router.post("/users")
        async def create_user(user_data: CreateUserRequest) -> dict:
            return {"success": True}

        app = VegaApp()
        app.include_router(router)

        client = TestClient(app)

        # Missing age field
        response = client.post(
            "/users",
            json={"name": "John", "email": "john@example.com"}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_invalid_json_returns_400(self):
        """Test that invalid JSON returns 400 status code"""
        router = Router()

        @router.post("/users")
        async def create_user(user_data: CreateUserRequest) -> dict:
            return {"success": True}

        app = VegaApp()
        app.include_router(router)

        client = TestClient(app)

        # Send invalid JSON
        response = client.post(
            "/users",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_body_parsing_with_path_params(self):
        """Test that body parsing works alongside path parameters"""
        router = Router()

        class UpdateUserRequest(BaseModel):
            name: str
            email: str

        @router.put("/users/{user_id}")
        async def update_user(user_id: str, user_data: UpdateUserRequest) -> dict:
            return {
                "id": user_id,
                "name": user_data.name,
                "email": user_data.email
            }

        app = VegaApp()
        app.include_router(router)

        client = TestClient(app)

        response = client.put(
            "/users/123",
            json={"name": "Jane Doe", "email": "jane@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "123"
        assert data["name"] == "Jane Doe"

    def test_pydantic_model_with_nested_models(self):
        """Test Pydantic models with nested structures"""
        router = Router()

        class Address(BaseModel):
            street: str
            city: str

        class UserWithAddress(BaseModel):
            name: str
            email: str
            address: Address

        @router.post("/users-with-address")
        async def create_user_with_address(user_data: UserWithAddress) -> dict:
            return {
                "name": user_data.name,
                "email": user_data.email,
                "city": user_data.address.city
            }

        app = VegaApp()
        app.include_router(router)

        client = TestClient(app)

        response = client.post(
            "/users-with-address",
            json={
                "name": "Jane Doe",
                "email": "jane@example.com",
                "address": {
                    "street": "123 Main St",
                    "city": "New York"
                }
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Jane Doe"
        assert data["city"] == "New York"

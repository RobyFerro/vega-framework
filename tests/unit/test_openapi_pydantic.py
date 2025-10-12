"""Tests for OpenAPI schema generation with Pydantic models"""

import pytest
from pydantic import BaseModel, Field
from vega.web import Router, VegaApp
from vega.web.openapi import get_openapi_schema


class CreateUserRequest(BaseModel):
    """Request model for creating a user"""
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: int = Field(..., ge=0, le=150)


class UserResponse(BaseModel):
    """Response model for user"""
    id: str
    name: str
    email: str
    age: int


class TestOpenAPIPydantic:
    """Test OpenAPI schema generation with Pydantic models"""

    def test_request_body_schema_in_components(self):
        """Test that request body Pydantic models are added to components"""
        router = Router()

        @router.post("/users", response_model=UserResponse)
        async def create_user(user_data: CreateUserRequest) -> UserResponse:
            return UserResponse(id="1", name="John", email="john@example.com", age=30)

        routes = router.get_routes()
        schema = get_openapi_schema(
            title="Test API",
            version="1.0.0",
            routes=routes
        )

        # Check that components exist
        assert "components" in schema
        assert "schemas" in schema["components"]

        # Check that CreateUserRequest is in components
        assert "CreateUserRequest" in schema["components"]["schemas"]

        # Check that the schema has the expected fields
        request_schema = schema["components"]["schemas"]["CreateUserRequest"]
        assert "properties" in request_schema
        assert "name" in request_schema["properties"]
        assert "email" in request_schema["properties"]
        assert "age" in request_schema["properties"]

    def test_response_model_schema_in_components(self):
        """Test that response Pydantic models are added to components"""
        router = Router()

        @router.post("/users", response_model=UserResponse)
        async def create_user(user_data: CreateUserRequest) -> UserResponse:
            return UserResponse(id="1", name="John", email="john@example.com", age=30)

        routes = router.get_routes()
        schema = get_openapi_schema(
            title="Test API",
            version="1.0.0",
            routes=routes
        )

        # Check that UserResponse is in components
        assert "UserResponse" in schema["components"]["schemas"]

        # Check that the schema has the expected fields
        response_schema = schema["components"]["schemas"]["UserResponse"]
        assert "properties" in response_schema
        assert "id" in response_schema["properties"]
        assert "name" in response_schema["properties"]
        assert "email" in response_schema["properties"]
        assert "age" in response_schema["properties"]

    def test_request_body_reference(self):
        """Test that request body has correct $ref to component"""
        router = Router()

        @router.post("/users", response_model=UserResponse)
        async def create_user(user_data: CreateUserRequest) -> UserResponse:
            return UserResponse(id="1", name="John", email="john@example.com", age=30)

        routes = router.get_routes()
        schema = get_openapi_schema(
            title="Test API",
            version="1.0.0",
            routes=routes
        )

        # Check request body reference
        post_operation = schema["paths"]["/users"]["post"]
        assert "requestBody" in post_operation
        assert "content" in post_operation["requestBody"]
        assert "application/json" in post_operation["requestBody"]["content"]

        request_schema = post_operation["requestBody"]["content"]["application/json"]["schema"]
        assert "$ref" in request_schema
        assert request_schema["$ref"] == "#/components/schemas/CreateUserRequest"

    def test_response_reference(self):
        """Test that response has correct $ref to component"""
        router = Router()

        @router.post("/users", response_model=UserResponse)
        async def create_user(user_data: CreateUserRequest) -> UserResponse:
            return UserResponse(id="1", name="John", email="john@example.com", age=30)

        routes = router.get_routes()
        schema = get_openapi_schema(
            title="Test API",
            version="1.0.0",
            routes=routes
        )

        # Check response reference
        post_operation = schema["paths"]["/users"]["post"]
        assert "201" in post_operation["responses"]
        assert "content" in post_operation["responses"]["201"]
        assert "application/json" in post_operation["responses"]["201"]["content"]

        response_schema = post_operation["responses"]["201"]["content"]["application/json"]["schema"]
        assert "$ref" in response_schema
        assert response_schema["$ref"] == "#/components/schemas/UserResponse"

    def test_both_models_in_same_endpoint(self):
        """Test that both request and response models are in components"""
        router = Router()

        @router.post("/users", response_model=UserResponse)
        async def create_user(user_data: CreateUserRequest) -> UserResponse:
            return UserResponse(id="1", name="John", email="john@example.com", age=30)

        routes = router.get_routes()
        schema = get_openapi_schema(
            title="Test API",
            version="1.0.0",
            routes=routes
        )

        # Both models should be in components
        assert "CreateUserRequest" in schema["components"]["schemas"]
        assert "UserResponse" in schema["components"]["schemas"]

    def test_vega_app_openapi_endpoint(self):
        """Test that VegaApp generates correct OpenAPI schema"""
        router = Router(prefix="/api/users")

        @router.post("", response_model=UserResponse)
        async def create_user(user_data: CreateUserRequest) -> UserResponse:
            return UserResponse(id="1", name="John", email="john@example.com", age=30)

        app = VegaApp(title="User API", version="1.0.0")
        app.include_router(router)

        # Get the OpenAPI schema
        from starlette.testclient import TestClient
        client = TestClient(app)

        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()

        # Check that components exist
        assert "components" in schema
        assert "schemas" in schema["components"]
        assert "CreateUserRequest" in schema["components"]["schemas"]
        assert "UserResponse" in schema["components"]["schemas"]

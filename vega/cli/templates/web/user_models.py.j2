"""User-related Pydantic models for API validation"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class CreateUserRequest(BaseModel):
    """Request model for creating a user"""
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    age: Optional[int] = Field(None, ge=0, le=150, description="User's age")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "age": 30
            }
        }


class UserResponse(BaseModel):
    """Response model for user data"""
    id: str = Field(..., description="User's unique identifier")
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    age: Optional[int] = Field(None, description="User's age")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "age": 30
            }
        }

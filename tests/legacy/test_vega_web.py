"""Test Vega Web Framework with Middleware Support"""

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


# Create app
app = VegaApp(
    title="Vega Web Demo API",
    version="1.0.0",
    debug=True
)

# Create router
router = Router(prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Hello from Vega Web!", "features": ["routing", "middleware", "async"]}


@app.get("/health")
def health_check():
    """Health check (sync handler)"""
    return {"status": "ok"}


# Example: Route with timing middleware
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


# Example: Protected route with auth middleware
@router.get("/users/{user_id}/profile")
@middleware(AuthMiddleware(), TimingMiddleware())
async def get_user_profile(user_id: str):
    """Protected endpoint requiring authentication"""
    return {
        "id": user_id,
        "name": "John Doe",
        "email": "john@example.com",
        "role": "user"
    }


# Example: Create user with logging
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


# Include router
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("VEGA WEB FRAMEWORK - Demo Server")
    print("=" * 60)
    print("\nFeatures demonstrated:")
    print("  - FastAPI-like routing API")
    print("  - Built on Starlette")
    print("  - Route-level middleware with @middleware decorator")
    print("  - BEFORE/AFTER execution phases")
    print("  - Built-in middleware (Auth, Timing, Logging, etc.)")
    print("\nEndpoints:")
    print("  GET  /                       - Basic endpoint")
    print("  GET  /health                 - Health check")
    print("  GET  /api/users/{user_id}    - User endpoint (with timing)")
    print("  GET  /api/users/{user_id}/profile - Protected (requires auth)")
    print("  POST /api/users              - Create user (with logging)")
    print("\nTest commands:")
    print("  # Basic request")
    print("  curl http://localhost:8000/")
    print("\n  # With timing middleware")
    print("  curl -i http://localhost:8000/api/users/123")
    print("\n  # Protected route (will fail)")
    print("  curl http://localhost:8000/api/users/123/profile")
    print("\n  # Protected route (with auth)")
    print("  curl -H 'Authorization: Bearer mytoken' http://localhost:8000/api/users/123/profile")
    print("\n" + "=" * 60)
    print()
    uvicorn.run(app, host="127.0.0.1", port=8000)

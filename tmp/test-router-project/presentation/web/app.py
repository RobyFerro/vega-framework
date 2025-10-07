"""FastAPI application factory for test-router-project"""
from fastapi import FastAPI

from .routes import get_api_router


APP_TITLE = "Test Router Project"
APP_VERSION = "0.1.0"


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(title=APP_TITLE, version=APP_VERSION)
    app.include_router(get_api_router())
    return app

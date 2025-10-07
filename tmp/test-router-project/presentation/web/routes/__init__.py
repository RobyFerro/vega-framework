"""API routers aggregation"""
from fastapi import APIRouter

from . import health, order, product, users


API_PREFIX = "/api"


def get_api_router() -> APIRouter:
    """Return application API router"""
    router = APIRouter(prefix=API_PREFIX)
    router.include_router(health.router, tags=["health"], prefix="/health")
    router.include_router(users.router, tags=["users"], prefix="/users")
    router.include_router(product.router, tags=["Products"], prefix="/products")
    router.include_router(order.router, tags=["Orders"], prefix="/orders")
    return router

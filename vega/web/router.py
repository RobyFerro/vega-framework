"""Router class for Vega Web Framework"""

from typing import Any, Callable, List, Optional, Sequence, Type

from starlette.routing import Mount

from .routing import Route, route as create_route


class Router:
    """
    HTTP Router for organizing endpoints.

    Similar to FastAPI's APIRouter, this class allows you to group related
    endpoints together with common configuration like prefix, tags, etc.

    Args:
        prefix: URL prefix for all routes (e.g., "/api/v1")
        tags: Default tags for all routes
        dependencies: Shared dependencies (future feature)
        responses: Common response models (future feature)

    Example:
        router = Router(prefix="/users", tags=["users"])

        @router.get("/{user_id}")
        async def get_user(user_id: str):
            return {"id": user_id, "name": "John"}

        @router.post("")
        async def create_user(request: Request):
            data = await request.json()
            return {"id": "new_id", **data}
    """

    def __init__(
        self,
        prefix: str = "",
        tags: Optional[List[str]] = None,
        dependencies: Optional[Sequence[Any]] = None,
        responses: Optional[dict] = None,
    ):
        self.prefix = prefix
        self.tags = tags or []
        self.dependencies = dependencies or []
        self.responses = responses or {}
        self.routes: List[Route] = []
        self.child_routers: List[tuple[Router, str, Optional[List[str]]]] = []

    def add_route(
        self,
        path: str,
        endpoint: Callable,
        methods: List[str],
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_model: Optional[Type] = None,
        status_code: int = 200,
    ) -> None:
        """
        Add a route to the router.

        Args:
            path: URL path pattern
            endpoint: Handler function
            methods: HTTP methods
            name: Optional route name
            include_in_schema: Include in API docs
            tags: Route tags
            summary: Short description
            description: Longer description
            response_model: Expected response type
            status_code: Default status code
        """
        # Merge router tags with route-specific tags
        route_tags = (tags or []) + self.tags

        route_obj = Route(
            path=path,
            endpoint=endpoint,
            methods=methods,
            name=name,
            include_in_schema=include_in_schema,
            tags=route_tags,
            summary=summary,
            description=description,
            response_model=response_model,
            status_code=status_code,
        )
        self.routes.append(route_obj)

    def route(
        self,
        path: str,
        methods: List[str],
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_model: Optional[Type] = None,
        status_code: int = 200,
    ) -> Callable:
        """
        Decorator to add a route.

        Example:
            @router.route("/items", methods=["GET", "POST"])
            async def items():
                return {"items": []}
        """

        def decorator(func: Callable) -> Callable:
            self.add_route(
                path=path,
                endpoint=func,
                methods=methods,
                name=name,
                include_in_schema=include_in_schema,
                tags=tags,
                summary=summary,
                description=description,
                response_model=response_model,
                status_code=status_code,
            )
            return func

        return decorator

    def get(
        self,
        path: str,
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_model: Optional[Type] = None,
        status_code: int = 200,
    ) -> Callable:
        """
        Decorator for GET requests.

        Example:
            @router.get("/items/{item_id}")
            async def get_item(item_id: str):
                return {"id": item_id}
        """
        return self.route(
            path,
            methods=["GET"],
            name=name,
            include_in_schema=include_in_schema,
            tags=tags,
            summary=summary,
            description=description,
            response_model=response_model,
            status_code=status_code,
        )

    def post(
        self,
        path: str,
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_model: Optional[Type] = None,
        status_code: int = 201,
    ) -> Callable:
        """
        Decorator for POST requests.

        Example:
            @router.post("/items")
            async def create_item(request: Request):
                data = await request.json()
                return {"id": "new", **data}
        """
        return self.route(
            path,
            methods=["POST"],
            name=name,
            include_in_schema=include_in_schema,
            tags=tags,
            summary=summary,
            description=description,
            response_model=response_model,
            status_code=status_code,
        )

    def put(
        self,
        path: str,
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_model: Optional[Type] = None,
        status_code: int = 200,
    ) -> Callable:
        """Decorator for PUT requests."""
        return self.route(
            path,
            methods=["PUT"],
            name=name,
            include_in_schema=include_in_schema,
            tags=tags,
            summary=summary,
            description=description,
            response_model=response_model,
            status_code=status_code,
        )

    def patch(
        self,
        path: str,
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_model: Optional[Type] = None,
        status_code: int = 200,
    ) -> Callable:
        """Decorator for PATCH requests."""
        return self.route(
            path,
            methods=["PATCH"],
            name=name,
            include_in_schema=include_in_schema,
            tags=tags,
            summary=summary,
            description=description,
            response_model=response_model,
            status_code=status_code,
        )

    def delete(
        self,
        path: str,
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_model: Optional[Type] = None,
        status_code: int = 204,
    ) -> Callable:
        """Decorator for DELETE requests."""
        return self.route(
            path,
            methods=["DELETE"],
            name=name,
            include_in_schema=include_in_schema,
            tags=tags,
            summary=summary,
            description=description,
            response_model=response_model,
            status_code=status_code,
        )

    def include_router(
        self,
        router: "Router",
        prefix: str = "",
        tags: Optional[List[str]] = None,
    ) -> None:
        """
        Include another router's routes in this router.

        Args:
            router: Router to include
            prefix: Additional prefix for included routes
            tags: Additional tags for included routes

        Example:
            users_router = Router()
            @users_router.get("/{user_id}")
            async def get_user(user_id: str):
                return {"id": user_id}

            main_router = Router()
            main_router.include_router(users_router, prefix="/users", tags=["users"])
        """
        self.child_routers.append((router, prefix, tags))

    def get_routes(self) -> List[Route]:
        """
        Get all routes including child routers.

        Returns:
            List of Route objects with prefixes applied
        """
        routes = []

        # Add direct routes with prefix
        for route in self.routes:
            # Create a copy with the prefix applied
            prefixed_route = Route(
                path=self.prefix + route.path,
                endpoint=route.endpoint,
                methods=route.methods,
                name=route.name,
                include_in_schema=route.include_in_schema,
                tags=route.tags,
                summary=route.summary,
                description=route.description,
                response_model=route.response_model,
                status_code=route.status_code,
            )
            routes.append(prefixed_route)

        # Add child router routes
        for child_router, child_prefix, child_tags in self.child_routers:
            for route in child_router.get_routes():
                # Apply additional prefix and tags
                combined_prefix = self.prefix + child_prefix
                combined_tags = route.tags + (child_tags or [])

                prefixed_route = Route(
                    path=combined_prefix + route.path,
                    endpoint=route.endpoint,
                    methods=route.methods,
                    name=route.name,
                    include_in_schema=route.include_in_schema,
                    tags=combined_tags,
                    summary=route.summary,
                    description=route.description,
                    response_model=route.response_model,
                    status_code=route.status_code,
                )
                routes.append(prefixed_route)

        return routes


__all__ = ["Router"]

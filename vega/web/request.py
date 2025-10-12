"""Request wrapper for Vega Web Framework"""

from typing import Any, Dict, Optional
from starlette.requests import Request as StarletteRequest


class Request(StarletteRequest):
    """
    HTTP Request wrapper built on Starlette.

    This class extends Starlette's Request to provide a familiar interface
    for developers coming from FastAPI while maintaining full compatibility
    with Starlette's ecosystem.

    Attributes:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        headers: HTTP headers
        query_params: Query string parameters
        path_params: Path parameters from URL
        cookies: Request cookies
        client: Client address info

    Example:
        @router.get("/users/{user_id}")
        async def get_user(request: Request, user_id: str):
            # Access path parameters
            assert user_id == request.path_params["user_id"]

            # Access query parameters
            limit = request.query_params.get("limit", "10")

            # Parse JSON body
            body = await request.json()

            return {"user_id": user_id, "limit": limit}
    """

    async def json(self) -> Any:
        """
        Parse request body as JSON.

        Returns:
            Parsed JSON data

        Raises:
            ValueError: If body is not valid JSON
        """
        return await super().json()

    async def form(self) -> Dict[str, Any]:
        """
        Parse request body as form data.

        Returns:
            Form data as dictionary
        """
        form_data = await super().form()
        return dict(form_data)

    async def body(self) -> bytes:
        """
        Get raw request body as bytes.

        Returns:
            Raw body bytes
        """
        return await super().body()

    @property
    def path_params(self) -> Dict[str, Any]:
        """
        Get path parameters extracted from URL.

        Returns:
            Dictionary of path parameters
        """
        return self.scope.get("path_params", {})

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a specific header value.

        Args:
            name: Header name (case-insensitive)
            default: Default value if header is not present

        Returns:
            Header value or default
        """
        return self.headers.get(name.lower(), default)

    def get_query_param(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a specific query parameter value.

        Args:
            name: Parameter name
            default: Default value if parameter is not present

        Returns:
            Parameter value or default
        """
        return self.query_params.get(name, default)

    def get_cookie(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a specific cookie value.

        Args:
            name: Cookie name
            default: Default value if cookie is not present

        Returns:
            Cookie value or default
        """
        return self.cookies.get(name, default)


__all__ = ["Request"]

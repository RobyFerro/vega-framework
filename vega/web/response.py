"""Response classes for Vega Web Framework"""

import json
from typing import Any, Dict, Optional, Union

from starlette.responses import (
    Response as StarletteResponse,
    JSONResponse as StarletteJSONResponse,
    HTMLResponse as StarletteHTMLResponse,
    PlainTextResponse as StarlettePlainTextResponse,
    RedirectResponse as StarletteRedirectResponse,
    StreamingResponse as StarletteStreamingResponse,
    FileResponse as StarletteFileResponse,
)


class Response(StarletteResponse):
    """
    Base HTTP Response class.

    A thin wrapper around Starlette's Response for API consistency.

    Args:
        content: Response body content
        status_code: HTTP status code (default: 200)
        headers: Optional HTTP headers
        media_type: Content-Type header value

    Example:
        return Response(content="Success", status_code=200)
        return Response(content=b"binary data", media_type="application/octet-stream")
    """

    pass


class JSONResponse(StarletteJSONResponse):
    """
    JSON HTTP Response.

    Automatically serializes Python objects to JSON and sets appropriate headers.

    Args:
        content: Object to serialize as JSON
        status_code: HTTP status code (default: 200)
        headers: Optional HTTP headers

    Example:
        return JSONResponse({"status": "ok", "data": [1, 2, 3]})
        return JSONResponse({"error": "Not found"}, status_code=404)
    """

    def render(self, content: Any) -> bytes:
        """Render content as JSON bytes"""
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


class HTMLResponse(StarletteHTMLResponse):
    """
    HTML HTTP Response.

    Args:
        content: HTML content as string
        status_code: HTTP status code (default: 200)
        headers: Optional HTTP headers

    Example:
        return HTMLResponse("<h1>Hello World</h1>")
    """

    pass


class PlainTextResponse(StarlettePlainTextResponse):
    """
    Plain text HTTP Response.

    Args:
        content: Text content
        status_code: HTTP status code (default: 200)
        headers: Optional HTTP headers

    Example:
        return PlainTextResponse("Hello, World!")
    """

    pass


class RedirectResponse(StarletteRedirectResponse):
    """
    HTTP Redirect Response.

    Args:
        url: URL to redirect to
        status_code: HTTP status code (default: 307)
        headers: Optional HTTP headers

    Example:
        return RedirectResponse(url="/new-location")
        return RedirectResponse(url="/login", status_code=302)
    """

    pass


class StreamingResponse(StarletteStreamingResponse):
    """
    Streaming HTTP Response.

    Useful for large files or real-time data.

    Args:
        content: Async generator or iterator
        status_code: HTTP status code (default: 200)
        headers: Optional HTTP headers
        media_type: Content-Type header value

    Example:
        async def generate():
            for i in range(10):
                yield f"data: {i}\\n\\n"
                await asyncio.sleep(1)

        return StreamingResponse(generate(), media_type="text/event-stream")
    """

    pass


class FileResponse(StarletteFileResponse):
    """
    File HTTP Response.

    Efficiently serves files from disk.

    Args:
        path: Path to file
        status_code: HTTP status code (default: 200)
        headers: Optional HTTP headers
        media_type: Content-Type (auto-detected if not provided)
        filename: If set, includes Content-Disposition header

    Example:
        return FileResponse("report.pdf", media_type="application/pdf")
        return FileResponse("image.jpg", filename="download.jpg")
    """

    pass


def create_response(
    content: Any = None,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None,
    media_type: Optional[str] = None,
) -> Union[Response, JSONResponse]:
    """
    Create an appropriate response based on content type.

    Automatically chooses between Response and JSONResponse based on content.

    Args:
        content: Response content
        status_code: HTTP status code
        headers: Optional HTTP headers
        media_type: Content-Type header value

    Returns:
        Response object

    Example:
        return create_response({"status": "ok"})  # Returns JSONResponse
        return create_response("text content")     # Returns Response
    """
    if content is None:
        return Response(content=b"", status_code=status_code, headers=headers)

    # If it's a dict, list, or other JSON-serializable type
    if isinstance(content, (dict, list)):
        return JSONResponse(content=content, status_code=status_code, headers=headers)

    # If it's a string
    if isinstance(content, str):
        return Response(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type or "text/plain",
        )

    # If it's bytes
    if isinstance(content, bytes):
        return Response(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type or "application/octet-stream",
        )

    # Default to JSON for other types
    return JSONResponse(content=content, status_code=status_code, headers=headers)


__all__ = [
    "Response",
    "JSONResponse",
    "HTMLResponse",
    "PlainTextResponse",
    "RedirectResponse",
    "StreamingResponse",
    "FileResponse",
    "create_response",
]

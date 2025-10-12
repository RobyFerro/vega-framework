"""Documentation endpoints for Vega Web Framework"""

from typing import Callable
from starlette.responses import HTMLResponse, JSONResponse


def get_swagger_ui_html(
    *,
    openapi_url: str,
    title: str,
    swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
    swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    swagger_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
) -> HTMLResponse:
    """
    Generate Swagger UI HTML page.

    Args:
        openapi_url: URL to OpenAPI schema JSON
        title: Page title
        swagger_js_url: URL to Swagger UI JavaScript
        swagger_css_url: URL to Swagger UI CSS
        swagger_favicon_url: URL to favicon

    Returns:
        HTML response with Swagger UI
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="shortcut icon" href="{swagger_favicon_url}">
        <link rel="stylesheet" type="text/css" href="{swagger_css_url}" />
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="{swagger_js_url}"></script>
        <script>
            const ui = SwaggerUIBundle({{
                url: '{openapi_url}',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout",
                deepLinking: true,
                showExtensions: true,
                showCommonExtensions: true
            }})
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


def get_redoc_html(
    *,
    openapi_url: str,
    title: str,
    redoc_js_url: str = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    redoc_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
) -> HTMLResponse:
    """
    Generate ReDoc HTML page.

    Args:
        openapi_url: URL to OpenAPI schema JSON
        title: Page title
        redoc_js_url: URL to ReDoc JavaScript
        redoc_favicon_url: URL to favicon

    Returns:
        HTML response with ReDoc
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="shortcut icon" href="{redoc_favicon_url}">
        <style>
            body {{
                margin: 0;
                padding: 0;
            }}
        </style>
    </head>
    <body>
        <redoc spec-url="{openapi_url}"></redoc>
        <script src="{redoc_js_url}"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


__all__ = ["get_swagger_ui_html", "get_redoc_html"]

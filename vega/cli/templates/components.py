from __future__ import annotations

from textwrap import dedent


def render_entity(class_name: str) -> str:
    """Return the template for a domain entity."""
    content = f'''"""{class_name} entity"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class {class_name}:
    """{class_name} domain entity"""
    id: str
    # Add your fields here

    # Add your business logic methods here
    def is_valid(self) -> bool:
        """Validate entity"""
        return bool(self.id)
'''
    return dedent(content).rstrip() + "\n"


def render_repository_interface(
    class_name: str,
    entity_name: str,
    entity_file: str,
) -> str:
    """Return the template for a repository interface."""
    entity_lower = entity_name.lower()
    content = f'''"""{class_name} interface"""
from abc import abstractmethod
from typing import List, Optional

from vega.patterns import Repository
from ..entities.{entity_file} import {entity_name}


class {class_name}(Repository[{entity_name}]):
    """{class_name} interface"""

    @abstractmethod
    async def find_all(self) -> List[{entity_name}]:
        """Find all {entity_lower}s"""
        pass

    # Add your custom methods here
    # @abstractmethod
    # async def find_by_name(self, name: str) -> Optional[{entity_name}]:
    #     pass
'''
    return dedent(content).rstrip() + "\n"


def render_service_interface(class_name: str) -> str:
    """Return the template for a service interface."""
    content = f'''"""{class_name} interface"""
from abc import abstractmethod

from vega.patterns import Service


class {class_name}(Service):
    """{class_name} interface"""

    @abstractmethod
    async def execute(self, data: dict) -> dict:
        """Execute service operation"""
        pass

    # Add your custom methods here
'''
    return dedent(content).rstrip() + "\n"


def render_interactor(class_name: str, entity_name: str, entity_file: str) -> str:
    """Return the template for an interactor."""
    content = f'''"""{class_name} use case"""
from vega.patterns import Interactor
from vega.di import bind

# Import your dependencies
# from ..entities.{entity_file} import {entity_name}
# from ..repositories.{entity_file}_repository import {entity_name}Repository


class {class_name}(Interactor[dict]):  # Replace dict with your return type
    """{class_name} use case"""

    def __init__(self, **kwargs):
        # Store input parameters
        pass

    @bind
    async def call(self) -> dict:  # Add dependencies as parameters
        """Execute the use case"""
        # TODO: Implement use case logic
        raise NotImplementedError("Implement this use case")
'''
    return dedent(content).rstrip() + "\n"


def render_mediator(class_name: str) -> str:
    """Return the template for a mediator."""
    content = f'''"""{class_name} workflow"""
from vega.patterns import Mediator

# Import your use cases
# from ...domain.interactors.create_user import CreateUser


class {class_name}(Mediator[dict]):  # Replace dict with your return type
    """{class_name} workflow - orchestrates multiple use cases"""

    def __init__(self, **kwargs):
        # Store input parameters
        pass

    async def call(self) -> dict:
        """Execute the workflow"""
        # TODO: Orchestrate multiple use cases
        # Example:
        # user = await CreateUser(name="John")
        # await SendWelcomeEmail(user.email)
        # return user

        raise NotImplementedError("Implement this workflow")
'''
    return dedent(content).rstrip() + "\n"


def render_infrastructure_repository(
    impl_class: str,
    interface_class_name: str,
    interface_file_name: str,
    entity_name: str,
    entity_file: str,
) -> str:
    """Return the template for a repository implementation."""
    entity_lower = entity_name.lower()
    content = f'''"""{impl_class} implementation"""
from typing import List

from ...domain.entities.{entity_file} import {entity_name}
from ...domain.repositories.{interface_file_name} import {interface_class_name}


class {impl_class}({interface_class_name}):
    """{impl_class} concrete implementation."""

    async def find_all(self) -> List[{entity_name}]:
        """Find all {entity_lower}s"""
        raise NotImplementedError("Implement repository logic")
'''
    return dedent(content).rstrip() + "\n"


def render_infrastructure_service(
    impl_class: str,
    interface_class_name: str,
    interface_file_name: str,
) -> str:
    """Return the template for a service implementation."""
    content = f'''"""{impl_class} implementation"""
from ...domain.services.{interface_file_name} import {interface_class_name}


class {impl_class}({interface_class_name}):
    """{impl_class} concrete implementation."""

    async def execute(self, data: dict) -> dict:
        """Execute service operation"""
        raise NotImplementedError("Implement service logic")
'''
    return dedent(content).rstrip() + "\n"

def render_web_package_init() -> str:
    """Return the template for web/__init__.py"""
    return ""


def render_fastapi_app(project_name: str) -> str:
    """Return the template for web/app.py"""
    template = f'''"""FastAPI application factory for {project_name}"""
from fastapi import FastAPI

from .routes import get_api_router


APP_TITLE = "{project_name.replace('-', ' ').replace('_', ' ').title()}"
APP_VERSION = "0.1.0"


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(title=APP_TITLE, version=APP_VERSION)
    app.include_router(get_api_router())
    return app
'''
    return dedent(template).rstrip() + "\n"


def render_fastapi_routes_init() -> str:
    """Return the template for web/routes/__init__.py"""
    template = '''"""API routers aggregation"""
from fastapi import APIRouter

from . import health


API_PREFIX = "/api"


def get_api_router() -> APIRouter:
    """Return application API router"""
    router = APIRouter(prefix=API_PREFIX)
    router.include_router(health.router, tags=["health"], prefix="/health")
    return router
'''
    return dedent(template).rstrip() + "\n"


def render_fastapi_health_route() -> str:
    """Return the template for web/routes/health.py"""
    template = '''"""Health check endpoints"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/status", summary="Health status", response_model=dict)
def health_status() -> dict:
    """Return service health information"""
    return {"status": "ok"}
'''
    return dedent(template).rstrip() + "\n"


def render_fastapi_dependencies() -> str:
    """Return the template for web/dependencies.py"""
    template = '''"""Shared FastAPI dependency providers"""
from typing import Any


async def get_container() -> Any:
    """Resolve Vega DI container or other dependencies"""
    # from config import container
    # return container
    raise NotImplementedError("Wire your dependency container here")
'''
    return dedent(template).rstrip() + "\n"


def render_fastapi_main(project_name: str) -> str:
    """Return the template for presentation/web/main.py"""
    template = f'''"""FastAPI ASGI entrypoint for {project_name}"""
from fastapi import FastAPI

from .app import create_app

app: FastAPI = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "presentation.web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
'''
    return dedent(template).rstrip() + "\n"


def render_standard_main(project_name: str) -> str:
    """Return the template for main.py (standard project with CLI)"""
    template = f'''"""Main entry point for {project_name}"""
import asyncio
import click
import config  # noqa: F401 - Import to initialize DI container

# Import your use cases here
# from domain.interactors.create_user import CreateUser


@click.group()
def cli():
    """Vega Framework CLI Application"""
    pass


@cli.command()
def hello():
    """Example CLI command"""
    click.echo("Hello from Vega Framework!")
    click.echo("Add your CLI commands in presentation/cli/commands/")


@cli.command()
@click.option('--name', default='World', help='Name to greet')
def greet(name: str):
    """Example command with parameter"""
    click.echo(f"Hello, {{name}}!")


# Uncomment this block if you enable FastAPI support
# @cli.command()
# @click.option('--host', default='0.0.0.0', help='Host to bind')
# @click.option('--port', default=8000, help='Port to bind')
# @click.option('--reload', is_flag=True, help='Enable auto-reload')
# def web(host: str, port: int, reload: bool):
#     """Start FastAPI web server"""
#     import uvicorn
#     from presentation.web.main import app
#
#     click.echo(f"Starting web server on http://{{host}}:{{port}}")
#     uvicorn.run(
#         app,
#         host=host,
#         port=port,
#         reload=reload,
#     )


# Add more CLI commands here or import them from presentation/cli/commands/


if __name__ == "__main__":
    cli()
'''
    return dedent(template).rstrip() + "\n"


def render_fastapi_project_main(project_name: str) -> str:
    """Return the template for main.py (FastAPI project with Web and CLI)"""
    template = f'''"""Main entry point for {project_name}"""
import click
import config  # noqa: F401 - Import to initialize DI container


@click.group()
def cli():
    """Vega Framework Application - CLI and Web"""
    pass


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind')
@click.option('--port', default=8000, help='Port to bind')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def web(host: str, port: int, reload: bool):
    """Start FastAPI web server"""
    import uvicorn
    from presentation.web.main import app

    click.echo(f"Starting web server on http://{{host}}:{{port}}")
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
    )


@cli.command()
def hello():
    """Example CLI command"""
    click.echo("Hello from Vega Framework!")
    click.echo("Add your CLI commands in presentation/cli/commands/")


# Add more CLI commands here or import them from presentation/cli/commands/


if __name__ == "__main__":
    cli()
'''
    return dedent(template).rstrip() + "\n"

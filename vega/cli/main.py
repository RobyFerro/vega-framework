"""Vega Framework CLI - Main entry point"""
import click
import os
from pathlib import Path

from vega import __version__
from vega.cli.commands.init import init_project
from vega.cli.commands.generate import generate_component
from vega.cli.commands.add import add
from vega.cli.commands.update import update_vega, check_version
from vega.cli.commands.migrate import migrate


@click.group()
@click.version_option(version=__version__, prog_name="Vega Framework")
def cli():
    """
    Vega Framework - Clean Architecture for Python

    Build applications with Clean Architecture principles:
    - Automatic Dependency Injection
    - Type-safe patterns (Interactor, Mediator, Repository)
    - Testable and maintainable code

    Examples:
        vega init my-app              # Create new project
        vega generate entity User     # Generate entity
        vega generate repo User       # Generate repository
        vega generate interactor CreateUser  # Generate use case
    """
    pass


@cli.command()
@click.argument('project_name')
@click.option('--template', default='basic', help='Project template (basic, fastapi, ai-rag)')
@click.option('--path', default='.', help='Parent directory for project')
def init(project_name, template, path):
    """
    Initialize a new Vega project with Clean Architecture structure.

    Creates:
    - domain/ (entities, repositories, services, interactors)
    - application/ (mediators)
    - infrastructure/ (implementations)
    - config.py (DI container)
    - settings.py (app configuration)

    Examples:
        vega init my-app
        vega init my-api --template=fastapi
        vega init my-ai --template=ai-rag --path=./projects
    """
    init_project(project_name, template, path)


@cli.command()
@click.argument('component_type', type=click.Choice([
    'entity', 'repository', 'repo', 'service', 'interactor', 'mediator', 'router', 'middleware', 'model', 'command'
]))
@click.argument('name')
@click.option('--path', default='.', help='Project root path')
@click.option('--impl', default=None, help='Generate infrastructure implementation for repository/service (e.g., memory, sql) or command type (async, sync)')
def generate(component_type, name, path, impl):
    """
    Generate a component in your Vega project.

    Component types:
        entity      - Domain entity (dataclass)
        repository  - Repository interface (domain layer)
        repo        - Short alias for repository
        service     - Service interface (domain layer)
        interactor  - Use case (business logic)
        mediator    - Workflow (orchestrates use cases)
        router      - FastAPI router (requires web module)
        middleware  - FastAPI middleware (requires web module)
        model       - SQLAlchemy model (requires sqlalchemy module)
        command     - CLI command (async by default)

    Examples:
        vega generate entity Product
        vega generate repository ProductRepository
        vega generate repository Product --impl memory
        vega generate interactor CreateProduct
        vega generate mediator CheckoutFlow
        vega generate router Product
        vega generate middleware Logging
        vega generate model User
        vega generate command CreateUser
        vega generate command ListUsers --impl sync
    """
    # Normalize 'repo' to 'repository'
    if component_type == 'repo':
        component_type = 'repository'

    generate_component(component_type, name, path, impl)


@cli.command()
@click.option('--path', default='.', help='Project path to validate')
def doctor(path):
    """
    Validate Vega project structure and architecture.

    Checks:
    - Correct folder structure
    - DI container configuration
    - Import dependencies
    - Architecture violations

    Example:
        vega doctor
        vega doctor --path=./my-app
    """
    click.echo("🏥 Running Vega Doctor...")
    click.echo("⚠️  Feature not implemented yet. Coming soon!")


@cli.command()
@click.option('--check', is_flag=True, help='Check for updates without installing')
@click.option('--force', is_flag=True, help='Force reinstall even if up to date')
def update(check, force):
    """
    Update Vega Framework to the latest version.

    Examples:
        vega update              # Update to latest version
        vega update --check      # Check for updates only
        vega update --force      # Force reinstall
    """
    if check:
        check_version()
    else:
        update_vega(force=force)


# Register the add and migrate commands
cli.add_command(add)
cli.add_command(migrate)


if __name__ == '__main__':
    cli()

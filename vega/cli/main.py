"""Vega Framework CLI - Main entry point"""
import click
import os
from pathlib import Path

from vega.cli.commands.init import init_project
from vega.cli.commands.generate import generate_component
from vega.cli.commands.add import add


@click.group()
@click.version_option(version="0.1.5", prog_name="Vega Framework")  # Updated version
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
    'entity', 'repository', 'repo', 'service', 'interactor', 'mediator'
]))
@click.argument('name')
@click.option('--path', default='.', help='Project root path')
@click.option('--impl', default=None, help='Generate infrastructure implementation for repository/service (e.g., memory, sql)')
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

    Examples:
        vega generate entity Product
        vega generate repository ProductRepository
        vega generate repository Product --impl memory
        vega generate web fastapi
        vega generate interactor CreateProduct
        vega generate mediator CheckoutFlow
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


# Register the add command
cli.add_command(add)


if __name__ == '__main__':
    cli()

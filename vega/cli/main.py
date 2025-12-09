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
from vega.cli.commands.web import web
from vega.cli.commands.listener import listener


@click.group()
@click.version_option(version=__version__, prog_name="Vega Framework")
def cli():
    """
    Vega Framework v2.0 - Domain-Driven Design & Clean Architecture for Python

    Build applications with DDD and Clean Architecture:
    - Domain-Driven Design with Bounded Contexts
    - CQRS (Command Query Responsibility Segregation)
    - Automatic Dependency Injection
    - Type-safe patterns (Aggregate, CommandHandler, QueryHandler)
    - Testable and maintainable code

    Examples:
        vega init my-app                    # Create new DDD project
        vega generate context sales         # Create bounded context
        vega generate aggregate Order       # Generate aggregate root
        vega generate command CreateOrder   # Generate command handler
        vega generate query GetOrderById    # Generate query handler
    """
    pass


@cli.command()
@click.argument('project_name')
@click.option('--path', default='.', help='Parent directory for project')
def init(project_name, path):
    """
    Initialize a new Vega project with DDD and Clean Architecture structure.

    Creates:
    - {project_name}/shared/ (shared kernel with full structure: domain, application, infrastructure, presentation)
    - config.py (DI container)
    - settings.py (app configuration)

    Use 'vega generate context <name>' to create additional bounded contexts.

    Includes Vega Web support by default with Swagger UI and auto-discovery.

    Examples:
        vega init my-app
        vega init my-api --path=./projects
    """
    init_project(project_name, 'web', path)


@cli.command()
@click.argument('component_type', type=click.Choice([
    'context',
    'aggregate',
    'value-object',
    'entity',
    'repository',
    'repo',
    'service',
    'interactor',
    'mediator',
    'router',
    'middleware',
    'webmodel',
    'model',
    'command',
    'query',
    'cli-command',
    'event',
    'event-handler',
    'subscriber',
]))
@click.argument('name')
@click.option('--path', default='.', help='Project root path')
@click.option('--impl', default=None, help='Generate infrastructure implementation for repository/service (e.g., memory, sql) or command type (async, sync)')
@click.option('--request', is_flag=True, help='Generate request model (for webmodel)')
@click.option('--response', is_flag=True, help='Generate response model (for webmodel)')
@click.option('--demo-router', is_flag=True, help='Generate a demo router with sample CRUD endpoints (default is empty)')
def generate(component_type, name, path, impl, request, response, demo_router):
    """
    Generate a component in your Vega project.

    Component types (DDD):
        context     - Bounded context (creates lib/{context}/ structure)
        aggregate   - Aggregate root (DDD pattern)
        value-object- Value object (immutable, validated)
        entity      - Domain entity (dataclass)
        command     - Command handler (CQRS write operation)
        query       - Query handler (CQRS read operation)
        event       - Domain event (immutable dataclass + metadata)

    Component types (Clean Architecture):
        repository  - Repository interface (domain layer)
        repo        - Short alias for repository
        service     - Service interface (domain layer)
        interactor  - Use case (business logic)
        mediator    - Workflow (orchestrates use cases)
        event-handler/subscriber - Application-level event subscriber

    Component types (Infrastructure):
        router      - Vega Web router (requires web module)
        middleware  - Vega Web middleware (requires web module)
        webmodel    - Pydantic request/response models (requires web module)
        model       - SQLAlchemy model (requires sqlalchemy module)
        cli-command - CLI command (presentation layer, async by default)

    Examples (DDD):
        vega generate context sales
        vega generate aggregate Order
        vega generate value-object Money
        vega generate command CreateOrder
        vega generate query GetOrderById

    Examples (Clean Architecture):
        vega generate entity Product
        vega generate repository ProductRepository
        vega generate repository Product --impl memory
        vega generate interactor CreateProduct
        vega generate mediator CheckoutFlow
        vega generate event UserCreated
        vega generate subscriber SendWelcomeEmail

    Examples (Infrastructure):
        vega generate router Product
        vega generate middleware Logging
        vega generate webmodel CreateUserRequest --request
        vega generate model User
        vega generate cli-command create-user
        vega generate cli-command list-users --impl sync
    """
    # Normalize aliases
    if component_type == 'repo':
        component_type = 'repository'
    if component_type == 'cli-command':
        component_type = 'cli_command'

    generate_component(component_type, name, path, impl, request, response, demo_router)


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


# Register the add, migrate, web and listener commands
cli.add_command(add)
cli.add_command(migrate)
cli.add_command(web)
cli.add_command(listener)


if __name__ == '__main__':
    cli()

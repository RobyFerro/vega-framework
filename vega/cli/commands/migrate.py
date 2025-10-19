"""Database migration commands"""
import click
import subprocess
import sys


@click.group()
def migrate():
    """Database migration commands"""
    pass


@migrate.command()
@click.option('-m', '--message', required=True, help='Migration message')
def create(message: str):
    """Create a new migration"""
    click.echo(f"Creating new migration: {message}")
    result = subprocess.run(
        [sys.executable, '-m', 'alembic', 'revision', '--autogenerate', '-m', message],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        click.secho("Migration created successfully", fg='green')
        click.echo(result.stdout)
    else:
        click.secho("Failed to create migration", fg='red')
        click.echo(result.stderr)
        sys.exit(1)


@migrate.command()
@click.option('--revision', default='head', help='Target revision (default: head)')
def upgrade(revision: str):
    """Apply migrations"""
    click.echo(f"Upgrading database to: {revision}")
    result = subprocess.run(
        [sys.executable, '-m', 'alembic', 'upgrade', revision],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        click.secho("Database upgraded successfully", fg='green')
        click.echo(result.stdout)
    else:
        click.secho("Failed to upgrade database", fg='red')
        click.echo(result.stderr)
        sys.exit(1)


@migrate.command()
@click.option('--revision', default='-1', help='Target revision (default: -1)')
def downgrade(revision: str):
    """Rollback migrations"""
    click.echo(f"Downgrading database to: {revision}")
    result = subprocess.run(
        [sys.executable, '-m', 'alembic', 'downgrade', revision],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        click.secho("Database downgraded successfully", fg='green')
        click.echo(result.stdout)
    else:
        click.secho("Failed to downgrade database", fg='red')
        click.echo(result.stderr)
        sys.exit(1)


@migrate.command()
def current():
    """Show current migration revision"""
    result = subprocess.run(
        [sys.executable, '-m', 'alembic', 'current'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        click.echo(result.stdout)
    else:
        click.secho("Failed to get current revision", fg='red')
        click.echo(result.stderr)
        sys.exit(1)


@migrate.command()
def history():
    """Show migration history"""
    result = subprocess.run(
        [sys.executable, '-m', 'alembic', 'history', '--verbose'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        click.echo(result.stdout)
    else:
        click.secho("Failed to get migration history", fg='red')
        click.echo(result.stderr)
        sys.exit(1)


@migrate.command()
def init():
    """Initialize database with current schema (create tables)"""
    from pathlib import Path
    import sys
    from vega.cli.utils import async_command
    from vega.di import get_container
    from vega.discovery import discover_beans

    # Add project root to path to allow imports
    project_root = Path.cwd()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Get the base package name from project structure
    # Try to determine the base package from common file locations
    base_package = None
    for potential_name in ['app', 'src', project_root.name]:
        potential_path = project_root / potential_name
        if potential_path.exists() and potential_path.is_dir():
            if any(potential_path.glob("*.py")):
                base_package = potential_name
                break

    # If no standard structure found, use project name
    if base_package is None:
        base_package = project_root.name.replace('-', '_').replace(' ', '_')

    # Discover beans to ensure DatabaseManager is registered
    click.echo(f"Discovering beans in package '{base_package}'...")
    try:
        bean_count = discover_beans(base_package)
        if bean_count == 0:
            click.secho(
                f"Warning: No beans discovered in '{base_package}'. "
                "Make sure your DatabaseManager is decorated with @bean.",
                fg='yellow'
            )
    except Exception as e:
        click.secho(f"Warning: Failed to discover beans: {e}", fg='yellow')

    # Try to get DatabaseManager from container
    container = get_container()
    db_manager = None

    # Search for DatabaseManager in registered beans
    for interface, implementation in container._services.items():
        if 'DatabaseManager' in implementation.__name__:
            try:
                db_manager = container.resolve(interface)
                click.echo(f"Found DatabaseManager: {implementation.__name__}")
                break
            except Exception as e:
                click.secho(f"Failed to resolve {implementation.__name__}: {e}", fg='yellow')

    if db_manager is None:
        click.secho(
            "Error: Could not find DatabaseManager in DI container.\n"
            "Make sure you have:\n"
            "  1. Created a DatabaseManager class\n"
            "  2. Decorated it with @bean\n"
            "  3. Placed it in a discoverable location (domain/application/infrastructure)",
            fg='red'
        )
        sys.exit(1)

    @async_command
    async def _init():
        click.echo("Creating database tables...")
        await db_manager.create_tables()
        click.secho("Database tables created successfully", fg='green')

    try:
        _init()
    except Exception as e:
        click.secho(f"Failed to initialize database: {e}", fg='red')
        sys.exit(1)

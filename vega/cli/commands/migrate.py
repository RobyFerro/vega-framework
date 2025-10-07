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

    # Add project root to path to allow imports
    project_root = Path.cwd()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    try:
        from config import db_manager
    except ImportError:
        click.secho("Error: Could not import db_manager from config.py", fg='red')
        click.echo("Make sure you have SQLAlchemy configured in your project")
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

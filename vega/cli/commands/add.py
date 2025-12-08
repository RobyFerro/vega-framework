"""Add command - Add features to existing Vega project"""
from pathlib import Path

import click

from vega.cli.scaffolds import create_sqlalchemy_scaffold


@click.command()
@click.argument('feature', type=click.Choice(['sqlalchemy', 'db'], case_sensitive=False))
@click.option('--path', default='.', help='Path to Vega project (default: current directory)')
def add(feature: str, path: str):
    """Add features to an existing Vega project

    Features:
        sqlalchemy - Add SQLAlchemy database support (alias: db)
        db         - Alias for sqlalchemy

    Examples:
        vega add sqlalchemy
        vega add db --path ./my-project

    Note: Web support is now integrated by default in all new projects.
    Use 'vega init <name>' to create a project with web support included.
    """
    project_path = Path(path).resolve()

    # Validate it's a Vega project
    if not (project_path / "config.py").exists():
        click.echo(click.style("ERROR: Not a Vega project (config.py not found)", fg='red'))
        click.echo(f"Path checked: {project_path}")
        return

    # Get project name from directory
    project_name = project_path.name

    if feature.lower() in ['sqlalchemy', 'db']:
        add_sqlalchemy_feature(project_path, project_name)


def add_sqlalchemy_feature(project_path: Path, project_name: str):
    """Add SQLAlchemy database support to existing project"""
    click.echo(f"\n[*] Adding SQLAlchemy database support to: {click.style(project_name, fg='green', bold=True)}\n")

    # Check if database_manager.py already exists
    db_manager_path = project_path / "infrastructure" / "database_manager.py"
    if db_manager_path.exists():
        click.echo(click.style("WARNING: SQLAlchemy scaffold already exists!", fg='yellow'))
        if not click.confirm("Do you want to overwrite existing files?"):
            click.echo("Aborted.")
            return
        overwrite = True
    else:
        overwrite = False

    # Create SQLAlchemy scaffold
    create_sqlalchemy_scaffold(project_path, project_name, overwrite=overwrite)

    # Ask if user wants an example repository
    create_example = click.confirm("\nDo you want to create an example User repository with SQLAlchemy implementation?", default=True)

    if create_example:
        click.echo("\n[*] Creating example User repository...")
        _create_user_example_repository(project_path, project_name)

    click.echo(f"\n{click.style('SUCCESS: SQLAlchemy database support added!', fg='green', bold=True)}\n")
    click.echo("Next steps:")
    click.echo("  1. Add DATABASE_URL to your settings.py:")
    click.echo('     DATABASE_URL: str = "sqlite+aiosqlite:///./database.db"')
    click.echo("  2. Install dependencies:")
    click.echo("     poetry install")
    click.echo("  3. Initialize database:")
    click.echo("     vega migrate init")
    click.echo("  4. Create your first migration:")
    click.echo('     vega migrate create -m "Initial migration"')
    click.echo("  5. Apply migrations:")
    click.echo("     vega migrate upgrade")


def _create_user_example_repository(project_path: Path, project_name: str):
    """Create example User entity, repository, and SQLAlchemy implementation"""
    from vega.cli.commands.generate import _generate_entity, _generate_repository, _generate_sqlalchemy_model, _generate_infrastructure_repository
    import sys
    from io import StringIO

    # Generate User entity
    click.echo("  + Creating User entity...")
    _generate_entity(project_path, project_name, 'User', 'user')

    # Generate UserRepository interface (without next steps)
    click.echo("  + Creating UserRepository interface...")
    original_stdout = sys.stdout
    sys.stdout = StringIO()  # Suppress "Next steps" output

    try:
        _generate_repository(project_path, project_name, 'UserRepository', 'user_repository', implementation=None)
    finally:
        sys.stdout = original_stdout

    # Generate SQLAlchemy UserModel
    click.echo("  + Creating UserModel (SQLAlchemy)...")
    sys.stdout = StringIO()  # Suppress verbose output
    try:
        _generate_sqlalchemy_model(project_path, project_name, 'User', 'user')
    finally:
        sys.stdout = original_stdout

    # Generate SQLAlchemy repository implementation
    click.echo("  + Creating SQLAlchemyUserRepository implementation...")
    _generate_infrastructure_repository(
        project_path,
        'UserRepository',
        'user_repository',
        'User',
        'user',
        'sql'
    )

    click.echo(click.style("\n  [OK] Example User repository created!", fg='green'))
    click.echo("\nGenerated files:")
    click.echo("  - domain/entities/user.py")
    click.echo("  - domain/repositories/user_repository.py")
    click.echo("  - infrastructure/models/user.py")
    click.echo("  - infrastructure/repositories/sqlalchemy_user_repository.py")
    click.echo("\nNext step: Update config.py to register SQLAlchemyUserRepository in SERVICES dict")

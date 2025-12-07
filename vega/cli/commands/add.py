"""Add command - Add features to existing Vega project"""
from pathlib import Path

import click

from vega.cli.scaffolds import create_vega_web_scaffold, create_sqlalchemy_scaffold


@click.command()
@click.argument('feature', type=click.Choice(['web', 'sqlalchemy', 'db'], case_sensitive=False))
@click.option('--path', default='.', help='Path to Vega project (default: current directory)')
def add(feature: str, path: str):
    """Add features to an existing Vega project

    Features:
        web        - Add Vega Web scaffold to the project
        sqlalchemy - Add SQLAlchemy database support (alias: db)
        db         - Alias for sqlalchemy

    Examples:
        vega add web
        vega add sqlalchemy
        vega add db --path ./my-project
    """
    project_path = Path(path).resolve()

    # Validate it's a Vega project
    if not (project_path / "config.py").exists():
        click.echo(click.style("ERROR: Not a Vega project (config.py not found)", fg='red'))
        click.echo(f"Path checked: {project_path}")
        return

    # Get project name from directory
    project_name = project_path.name

    if feature.lower() == 'web':
        add_web_feature(project_path, project_name)
    elif feature.lower() in ['sqlalchemy', 'db']:
        add_sqlalchemy_feature(project_path, project_name)


def add_web_feature(project_path: Path, project_name: str):
    """Add Vega Web scaffold to existing project (supports DDD structure)"""
    click.echo(f"\n[*] Adding Vega Web scaffold to: {click.style(project_name, fg='green', bold=True)}\n")

    # Detect if this is a DDD project (lib/ structure)
    lib_path = project_path / "lib"
    is_ddd = lib_path.exists() and lib_path.is_dir()

    if is_ddd:
        # DDD structure - add web to all contexts
        click.echo(click.style("Detected DDD structure with bounded contexts", fg='cyan'))
        contexts = [d.name for d in lib_path.iterdir()
                   if d.is_dir() and not d.name.startswith('_') and d.name != 'shared']

        if len(contexts) == 0:
            click.echo(click.style("ERROR: No bounded contexts found in lib/", fg='red'))
            return

        # Ask which context(s) to add web support to
        click.echo("\nAvailable contexts:")
        for i, ctx in enumerate(contexts, 1):
            click.echo(f"  {i}. {ctx}")
        click.echo(f"  {len(contexts) + 1}. All contexts")

        choice = click.prompt("Select context", type=click.IntRange(1, len(contexts) + 1), default=1)

        if choice == len(contexts) + 1:
            target_contexts = contexts
        else:
            target_contexts = [contexts[choice - 1]]

        # Add web to selected context(s)
        for context in target_contexts:
            click.echo(f"\n[*] Adding web to context: {click.style(context, fg='green')}")
            context_path = lib_path / context
            web_dir = context_path / "presentation" / "web"

            # Check if already exists
            if web_dir.exists() and (web_dir / "main.py").exists():
                click.echo(click.style(f"  WARNING: Web scaffold already exists in '{context}'", fg='yellow'))
                if not click.confirm(f"  Overwrite in '{context}'?", default=False):
                    continue
                overwrite = True
            else:
                overwrite = False

            # Create web structure in context
            _create_web_in_context(context_path, project_name, context, overwrite)

    else:
        # Legacy structure - add to root presentation/
        click.echo(click.style("Detected legacy Clean Architecture structure", fg='cyan'))
        web_dir = project_path / "presentation" / "web"
        if web_dir.exists() and (web_dir / "main.py").exists():
            click.echo(click.style("WARNING: Web scaffold already exists!", fg='yellow'))
            if not click.confirm("Do you want to overwrite existing files?"):
                click.echo("Aborted.")
                return
            overwrite = True
        else:
            overwrite = False

        # Create presentation directory if it doesn't exist
        presentation_dir = project_path / "presentation"
        if not presentation_dir.exists():
            presentation_dir.mkdir(parents=True, exist_ok=True)
            click.echo(f"  + Created presentation/")

        # Create Vega Web scaffold
        create_vega_web_scaffold(project_path, project_name, overwrite=overwrite)

    click.echo(f"\n{click.style('SUCCESS: Vega Web scaffold added!', fg='green', bold=True)}\n")
    click.echo("Next steps:")
    click.echo("  1. Dependencies are already included in vega-framework")
    click.echo("  2. Run the server:")
    click.echo("     vega web run --reload")
    click.echo("  3. Visit http://localhost:8000/api/health/status")


def _create_web_in_context(context_path: Path, project_name: str, context_name: str, overwrite: bool = False):
    """Create web structure inside a bounded context"""
    web_path = context_path / "presentation" / "web"
    web_path.mkdir(parents=True, exist_ok=True)

    # Create routes directory
    routes_path = web_path / "routes"
    routes_path.mkdir(exist_ok=True)

    # Create __init__.py files
    (web_path / "__init__.py").write_text("")
    (routes_path / "__init__.py").write_text("")

    # Create health route as example
    from vega.cli.templates import render_vega_health_route
    health_route = routes_path / "health.py"
    if not health_route.exists() or overwrite:
        health_route.write_text(render_vega_health_route())
        click.echo(f"  + Created {context_name}/presentation/web/routes/health.py")

    # Create main.py for the context web app
    from vega.cli.templates import render_vega_main
    main_file = web_path / "main.py"
    if not main_file.exists() or overwrite:
        main_content = render_vega_main(project_name)
        main_file.write_text(main_content)
        click.echo(f"  + Created {context_name}/presentation/web/main.py")

    click.echo(f"  + Web structure created in context '{context_name}'")


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

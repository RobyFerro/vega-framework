"""Add command - Add features to existing Vega project"""
from pathlib import Path

import click

from vega.cli.scaffolds import create_fastapi_scaffold


@click.command()
@click.argument('feature', type=click.Choice(['web'], case_sensitive=False))
@click.option('--path', default='.', help='Path to Vega project (default: current directory)')
def add(feature: str, path: str):
    """Add features to an existing Vega project

    Features:
        web - Add FastAPI web scaffold to the project

    Examples:
        vega add web
        vega add web --path ./my-project
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


def add_web_feature(project_path: Path, project_name: str):
    """Add FastAPI web scaffold to existing project"""
    click.echo(f"\n[*] Adding FastAPI web scaffold to: {click.style(project_name, fg='green', bold=True)}\n")

    # Check if presentation/web already exists
    web_dir = project_path / "presentation" / "web"
    if web_dir.exists() and (web_dir / "main.py").exists():
        click.echo(click.style("WARNING: FastAPI scaffold already exists!", fg='yellow'))
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
        (presentation_dir / "__init__.py").write_text("")
        click.echo(f"  + Created presentation/")

    # Create FastAPI scaffold
    create_fastapi_scaffold(project_path, project_name, overwrite=overwrite)

    # Update main.py to use web command
    main_file = project_path / "main.py"
    if main_file.exists():
        click.echo("\n[!] Update main.py to add web command:")
        click.echo("    Add the following to your main.py CLI group:\n")
        click.echo(click.style('''
@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind')
@click.option('--port', default=8000, help='Port to bind')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def web(host: str, port: int, reload: bool):
    """Start FastAPI web server"""
    import uvicorn
    from presentation.web.main import app

    click.echo(f"Starting web server on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=reload)
''', fg='cyan'))

    click.echo(f"\n{click.style('SUCCESS: FastAPI web scaffold added!', fg='green', bold=True)}\n")
    click.echo("Next steps:")
    click.echo("  1. Add FastAPI dependencies:")
    click.echo("     poetry add fastapi uvicorn[standard]")
    click.echo("  2. Update your main.py with the web command (see above)")
    click.echo("  3. Run the server:")
    click.echo("     python main.py web --reload")
    click.echo("  4. Visit http://localhost:8000/api/health/status")

"""Web command - Manage Vega Web server"""
import sys
from pathlib import Path

import click


@click.group()
def web():
    """Manage Vega Web server

    Commands to manage the web server for your Vega project.
    The web module must be added to the project first using 'vega add web'.
    """
    pass


@web.command()
@click.option('--host', default='0.0.0.0', help='Host to bind')
@click.option('--port', default=8000, help='Port to bind')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
@click.option('--path', default='.', help='Path to Vega project (default: current directory)')
def run(host: str, port: int, reload: bool, path: str):
    """Start the Vega Web server

    Examples:
        vega web run
        vega web run --reload
        vega web run --host 127.0.0.1 --port 3000
        vega web run --path ./my-project --reload
    """
    project_path = Path(path).resolve()

    # Validate it's a Vega project
    if not (project_path / "config.py").exists():
        click.echo(click.style("ERROR: Not a Vega project (config.py not found)", fg='red'))
        click.echo(f"Path checked: {project_path}")
        click.echo("\nRun 'vega init <project-name>' to create a new Vega project.")
        sys.exit(1)

    # Check if web module exists
    web_main = project_path / "presentation" / "web" / "main.py"
    if not web_main.exists():
        click.echo(click.style("ERROR: Web module not found", fg='red'))
        click.echo("\nThe Vega Web module is not available in this project.")
        click.echo("Add it using:")
        click.echo(click.style("  vega add web", fg='cyan', bold=True))
        sys.exit(1)

    # Add project path to sys.path so we can import from it
    if str(project_path) not in sys.path:
        sys.path.insert(0, str(project_path))

    # Try to import uvicorn
    try:
        import uvicorn
    except ImportError:
        click.echo(click.style("ERROR: uvicorn not installed", fg='red'))
        click.echo("\nUvicorn is required but not installed.")
        click.echo("It should be included with vega-framework, but you can also install it with:")
        click.echo(click.style("  poetry add uvicorn[standard]", fg='cyan', bold=True))
        sys.exit(1)

    # Initialize DI container first
    try:
        import config  # noqa: F401
    except ImportError as e:
        click.echo(click.style("ERROR: Failed to load DI container", fg='red'))
        click.echo(f"\nDetails: {e}")
        click.echo("\nMake sure config.py exists in the project root")
        sys.exit(1)

    # Try to import the app
    try:
        from presentation.web.main import app
    except ImportError as e:
        click.echo(click.style("ERROR: Failed to import Vega Web app", fg='red'))
        click.echo(f"\nDetails: {e}")
        click.echo("\nMake sure:")
        click.echo("  1. You are in the project directory or use --path")
        click.echo("  2. The web module is properly configured")
        click.echo("  3. All dependencies are installed (poetry install)")
        sys.exit(1)

    click.echo(f"Starting web server on http://{host}:{port}")
    if reload:
        click.echo(click.style("Auto-reload enabled", fg='yellow'))

    # Run the server
    try:
        uvicorn.run(
            "presentation.web.main:app",
            host=host,
            port=port,
            reload=reload,
        )
    except Exception as e:
        click.echo(click.style(f"\nERROR: Failed to start server", fg='red'))
        click.echo(f"Details: {e}")
        sys.exit(1)

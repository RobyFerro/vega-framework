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
@click.option('--context', default=None, help='Bounded context to run (DDD structure)')
def run(host: str, port: int, reload: bool, path: str, context: str):
    """Start the Vega Web server

    Examples:
        vega web run
        vega web run --reload
        vega web run --host 127.0.0.1 --port 3000
        vega web run --context shared --reload  # DDD structure with shared kernel
        vega web run --path ./my-project --reload
    """
    project_path = Path(path).resolve()

    # Validate it's a Vega project
    if not (project_path / "config.py").exists():
        click.echo(click.style("ERROR: Not a Vega project (config.py not found)", fg='red'))
        click.echo(f"Path checked: {project_path}")
        click.echo("\nRun 'vega init <project-name>' to create a new Vega project.")
        sys.exit(1)

    # Detect structure (DDD vs Legacy)
    # Try to find package directory (normalized project name) or lib/ (legacy DDD)
    normalized_name = project_path.name.replace('-', '_')
    package_path = project_path / normalized_name
    lib_path = project_path / "lib"  # Legacy DDD structure

    is_ddd = package_path.exists() and package_path.is_dir()
    if not is_ddd and lib_path.exists():
        # Legacy DDD structure with lib/
        is_ddd = True
        package_path = lib_path

    web_main = None
    import_path = None

    if is_ddd:
        # DDD structure - use auto-discovery to load all routers from all contexts
        click.echo(click.style("Detected DDD structure with bounded contexts", fg='cyan'))

        contexts = [d.name for d in package_path.iterdir()
                   if d.is_dir() and not d.name.startswith('_') and d.name != 'shared']

        if len(contexts) == 0:
            click.echo(click.style(f"ERROR: No bounded contexts found in {package_path.name}/", fg='red'))
            sys.exit(1)

        # Find contexts with web module
        web_contexts = []
        for ctx in contexts:
            ctx_web_routes = package_path / ctx / "presentation" / "web" / "routes"
            if ctx_web_routes.exists():
                web_contexts.append(ctx)

        if len(web_contexts) == 0:
            click.echo(click.style("ERROR: No web routes found in any context", fg='red'))
            click.echo("\nNo bounded context has web routes.")
            click.echo("Add web support using:")
            click.echo(click.style("  vega add web", fg='cyan', bold=True))
            sys.exit(1)

        click.echo(f"Found {len(web_contexts)} context(s) with web routes: {', '.join(web_contexts)}")

        # For DDD, we'll create the app dynamically with auto-discovery
        # No need for a specific main.py - we use discover_routers_ddd()
        web_main = None  # Not used in DDD
        import_path = None  # We'll create the app inline

    else:
        # Legacy structure
        click.echo(click.style("Detected legacy Clean Architecture structure", fg='cyan'))
        web_main = project_path / "presentation" / "web" / "main.py"
        import_path = "presentation.web.main:app"

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

    # Prepare the app
    if is_ddd:
        # For DDD structure, create app with auto-discovery
        try:
            from vega.web import VegaApp
            from vega.discovery import discover_routers_ddd

            click.echo("\nAuto-discovering routers from all bounded contexts...")

            # Get project name from directory
            project_name = project_path.name.replace('-', '_')

            # Create app and discover all routers (including framework health)
            app = VegaApp(
                title=f"{project_name.title()} API",
                description=f"API for {project_name} - DDD with Bounded Contexts",
                version="1.0.0"
            )

            # Auto-discover and include all routers from all contexts (shared/default provides /health)
            router = discover_routers_ddd(project_name, include_builtin=False)
            app.include_router(router)

            click.echo(click.style("✓ Routers auto-discovered successfully (shared /health included)", fg='green'))

        except Exception as e:
            click.echo(click.style("ERROR: Failed to create Vega Web app with auto-discovery", fg='red'))
            click.echo(f"\nDetails: {e}")
            click.echo("\nMake sure:")
            click.echo("  1. All dependencies are installed (poetry install)")
            click.echo("  2. Routes are properly defined in lib/{context}/presentation/web/routes/")
            import traceback
            traceback.print_exc()
            sys.exit(1)

        # For DDD, we run the app instance directly (can't use string path with reload)
        click.echo(f"\nStarting web server on http://{host}:{port}")
        click.echo("Available endpoints:")
        click.echo(f"  - http://{host}:{port}/health (shared default health check)")
        click.echo(f"  - http://{host}:{port}/docs (API documentation)")
        click.echo(f"  - http://{host}:{port}/api/{{context}}/{{route}}")
        if reload:
            click.echo(click.style("\nWARNING: Auto-reload is not supported with DDD auto-discovery", fg='yellow'))
            click.echo(click.style("         Use legacy structure or single context main.py for reload", fg='yellow'))
        click.echo()

        try:
            uvicorn.run(
                app,
                host=host,
                port=port,
                reload=False,  # Can't use reload with app instance
            )
        except Exception as e:
            click.echo(click.style(f"\nERROR: Failed to start server", fg='red'))
            click.echo(f"Details: {e}")
            sys.exit(1)

    else:
        # Legacy structure - import from presentation.web.main
        try:
            # Dynamically import the app to verify it exists
            module_path, app_name = import_path.split(':')
            module = __import__(module_path, fromlist=[app_name])
            app = getattr(module, app_name)
        except ImportError as e:
            click.echo(click.style("ERROR: Failed to import Vega Web app", fg='red'))
            click.echo(f"\nDetails: {e}")
            click.echo("\nMake sure:")
            click.echo("  1. You are in the project directory or use --path")
            click.echo("  2. The web module is properly configured")
            click.echo("  3. All dependencies are installed (poetry install)")
            sys.exit(1)

        click.echo(f"\nStarting web server on http://{host}:{port}")
        click.echo("Available endpoints:")
        click.echo(f"  - http://{host}:{port}/health (shared default health check)")
        click.echo(f"  - http://{host}:{port}/docs (API documentation)")
        click.echo(f"  - http://{host}:{port}/api/...")
        if reload:
            click.echo(click.style("\nAuto-reload enabled", fg='yellow'))
        click.echo()

        # Run the server
        try:
            uvicorn.run(
                import_path,
                host=host,
                port=port,
                reload=reload,
            )
        except Exception as e:
            click.echo(click.style(f"\nERROR: Failed to start server", fg='red'))
            click.echo(f"Details: {e}")
            sys.exit(1)

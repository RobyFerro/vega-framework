"""Init command - Create new Vega project"""
from __future__ import annotations

from pathlib import Path

import click

from vega.cli.scaffolds import create_vega_web_scaffold
from vega.cli.templates.loader import render_template
import vega


def init_project(project_name: str, template: str, parent_path: str):
    """Initialize a new Vega project with DDD and Bounded Contexts structure"""

    template = template.lower()
    # Validate project name
    if not project_name.replace('-', '').replace('_', '').isalnum():
        click.echo(click.style("ERROR: Error: Project name must be alphanumeric (- and _ allowed)", fg='red'))
        return

    # Create project directory
    project_path = Path(parent_path) / project_name
    if project_path.exists():
        click.echo(click.style(f"ERROR: Error: Directory '{project_name}' already exists", fg='red'))
        return

    click.echo(f"\n[*] Creating Vega DDD project: {click.style(project_name, fg='green', bold=True)}")
    click.echo(f"[*] Architecture: Domain-Driven Design with Bounded Contexts")
    click.echo(f"[*] Location: {project_path.absolute()}\n")

    # Use normalized project name as package directory (replaces "lib/")
    normalized_name = project_name.replace('-', '_')

    # Create DDD structure with normalized package name and shared kernel
    directories = [
        # Shared kernel with full structure
        f"{normalized_name}/shared/domain/aggregates",
        f"{normalized_name}/shared/domain/entities",
        f"{normalized_name}/shared/domain/value_objects",
        f"{normalized_name}/shared/domain/events",
        f"{normalized_name}/shared/domain/repositories",
        f"{normalized_name}/shared/application/commands",
        f"{normalized_name}/shared/application/queries",
        f"{normalized_name}/shared/infrastructure/repositories",
        f"{normalized_name}/shared/infrastructure/services",
        f"{normalized_name}/shared/presentation/cli/commands",
        f"{normalized_name}/shared/presentation/web/routes",
        f"{normalized_name}/shared/presentation/web/models",
        # Tests for shared kernel
        f"tests/{normalized_name}/shared/domain",
        f"tests/{normalized_name}/shared/application",
        f"tests/{normalized_name}/shared/infrastructure",
        f"tests/{normalized_name}/shared/presentation",
    ]

    for directory in directories:
        dir_path = project_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)

        # Use auto-discovery template for cli/commands
        if "cli" in directory and "commands" in directory:
            from vega.cli.templates import render_cli_commands_init
            content = render_cli_commands_init()
            (dir_path / "__init__.py").write_text(content)
        # Use auto-discovery template for domain/events/
        elif directory.endswith("domain/events"):
            from vega.cli.templates import render_events_init
            content = render_events_init()
            (dir_path / "__init__.py").write_text(content)

        click.echo(f"  + Created {directory}/")

    # Initialize web files in shared kernel
    click.echo("\n[*] Initializing Vega Web in shared kernel")
    from vega.cli.scaffolds import create_vega_web_scaffold_in_context
    create_vega_web_scaffold_in_context(project_path, project_name, "shared", echo=click.echo)

    # Note: In Python 3.3+, __init__.py files are optional for namespace packages.
    # We only create them when they contain functional code (auto-discovery, imports, etc.)
    # Documentation-only __init__.py files are omitted for cleaner project structure.

    # Create config.py
    config_content = render_template(
        "config.py.j2",
        project_name=project_name,
        project_package=normalized_name,
    )
    (project_path / "config.py").write_text(config_content)
    click.echo(f"  + Created config.py")

    # Create settings.py
    settings_content = render_template("settings.py.j2", project_name=project_name)
    (project_path / "settings.py").write_text(settings_content)
    click.echo(f"  + Created settings.py")

    # Create .env.example
    env_content = render_template(".env.example", project_name=project_name)
    (project_path / ".env.example").write_text(env_content)
    click.echo(f"  + Created .env.example")

    # Create .gitignore
    gitignore_content = render_template(".gitignore")
    (project_path / ".gitignore").write_text(gitignore_content)
    click.echo(f"  + Created .gitignore")

    # Create pyproject.toml with dependencies based on template
    pyproject_content = render_template(
        "pyproject.toml.j2",
        project_name=project_name,
        template=template,
        vega_version=vega.__version__
    )
    (project_path / "pyproject.toml").write_text(pyproject_content)
    click.echo(f"  + Created pyproject.toml")

    # Create README.md
    readme_content = render_template("README.md.j2", project_name=project_name, template=template)
    (project_path / "README.md").write_text(readme_content, encoding='utf-8')
    click.echo(f"  + Created README.md")

    # Create ARCHITECTURE.md
    architecture_content = render_template("ARCHITECTURE.md.j2", project_name=project_name)
    (project_path / "ARCHITECTURE.md").write_text(architecture_content, encoding='utf-8')
    click.echo(f"  + Created ARCHITECTURE.md")

    # Create main.py for CLI commands
    main_content = render_template("main.py.j2", project_name=project_name, template="fastapi")
    (project_path / "main.py").write_text(main_content)
    click.echo(f"  + Created main.py (CLI entry point)")


    # Success message with appropriate next steps
    click.echo(f"\n{click.style('SUCCESS: Success!', fg='green', bold=True)} Project created successfully.\n")
    click.echo("Next steps:")
    click.echo(f"  cd {project_name}")
    click.echo(f"  poetry install")
    click.echo(f"  cp .env.example .env")

    click.echo(f"\nRun commands:")
    click.echo(f"  vega web run                # Start Vega Web server (http://localhost:8000)")
    click.echo(f"  vega web run --reload       # Start with auto-reload")
    click.echo(f"  python main.py hello        # Run CLI command")
    click.echo(f"  python main.py --help       # Show all commands")

    click.echo(f"\nGenerate DDD components:")
    click.echo(f"  vega generate context sales          # Create new bounded context")
    click.echo(f"  vega generate aggregate Order        # Create aggregate root")
    click.echo(f"  vega generate value-object Money     # Create value object")
    click.echo(f"  vega generate entity User            # Create domain entity")
    click.echo(f"  vega generate command CreateOrder    # Create command handler (CQRS)")
    click.echo(f"  vega generate query GetOrderById     # Create query handler (CQRS)")
    click.echo(f"  vega generate repository OrderRepository")
    click.echo(f"\n[Docs] https://vega-framework.readthedocs.io/")

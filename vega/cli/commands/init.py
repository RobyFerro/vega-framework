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

    # Create DDD structure with lib/ and bounded contexts
    directories = [
        "lib/core/domain/aggregates",
        "lib/core/domain/entities",
        "lib/core/domain/value_objects",
        "lib/core/domain/events",
        "lib/core/domain/repositories",
        "lib/core/application/commands",
        "lib/core/application/queries",
        "lib/core/infrastructure/repositories",
        "lib/core/infrastructure/services",
        "lib/core/presentation/cli/commands",
        "lib/shared",
        "tests/lib/core/domain",
        "tests/lib/core/application",
        "tests/lib/core/infrastructure",
        "tests/lib/core/presentation",
    ]

    # Add web directories if web template
    if template in ["web", "fastapi"]:
        directories.extend([
            "lib/core/presentation/web/routes",
            "lib/core/presentation/web/models",
        ])

    for directory in directories:
        dir_path = project_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)

        # Create __init__.py for Python packages
        (dir_path / "__init__.py").write_text("")

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

    # Create bounded context init files with documentation
    from vega.cli.templates import render_context_init

    # Core context __init__.py
    core_init = render_context_init("core", project_name)
    (project_path / "lib" / "core" / "__init__.py").write_text(core_init)
    click.echo(f"  + Created lib/core/__init__.py (Core bounded context)")

    # Shared kernel __init__.py
    shared_init = render_context_init("shared", project_name)
    (project_path / "lib" / "shared" / "__init__.py").write_text(shared_init)
    click.echo(f"  + Created lib/shared/__init__.py (Shared kernel)")

    # lib/__init__.py
    (project_path / "lib" / "__init__.py").write_text("")

    # Create config.py
    config_content = render_template("config.py.j2", project_name=project_name)
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

    # Create main.py based on template
    # Support both "web" and "fastapi" (backward compat)
    if template in ["web", "fastapi"]:
        click.echo("\n[*] Adding Vega Web scaffold (presentation/web/)")
        create_vega_web_scaffold(project_path, project_name)

        # Create main.py for web project
        main_content = render_template("main.py.j2", project_name=project_name, template="fastapi")
        (project_path / "main.py").write_text(main_content)
        click.echo(f"  + Created main.py (Vega Web entrypoint)")
    else:
        # Create standard main.py
        main_content = render_template("main.py.j2", project_name=project_name, template="standard")
        (project_path / "main.py").write_text(main_content)
        click.echo(f"  + Created main.py")


    # Success message with appropriate next steps
    click.echo(f"\n{click.style('SUCCESS: Success!', fg='green', bold=True)} Project created successfully.\n")
    click.echo("Next steps:")
    click.echo(f"  cd {project_name}")
    click.echo(f"  poetry install")
    click.echo(f"  cp .env.example .env")

    if template in ["web", "fastapi"]:
        click.echo(f"\nRun commands:")
        click.echo(f"  vega web run                # Start Vega Web server (http://localhost:8000)")
        click.echo(f"  vega web run --reload       # Start with auto-reload")
        click.echo(f"  python main.py hello        # Run CLI command")
        click.echo(f"  python main.py --help       # Show all commands")
    else:
        click.echo(f"\nRun commands:")
        click.echo(f"  python main.py hello        # Run example CLI command")
        click.echo(f"  python main.py greet --name John  # Run with parameters")
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

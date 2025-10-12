"""Init command - Create new Vega project"""
from __future__ import annotations

from pathlib import Path

import click

from vega.cli.scaffolds import create_vega_web_scaffold
from vega.cli.templates.loader import render_template
import vega


def init_project(project_name: str, template: str, parent_path: str):
    """Initialize a new Vega project with Clean Architecture structure"""

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

    click.echo(f"\n[*] Creating Vega project: {click.style(project_name, fg='green', bold=True)}")
    click.echo(f"[*] Location: {project_path.absolute()}\n")

    # Create directory structure
    directories = [
        "domain/entities",
        "domain/repositories",
        "domain/services",
        "domain/interactors",
        "application/mediators",
        "infrastructure/repositories",
        "infrastructure/services",
        "presentation/cli/commands",
        "events",
        "tests/domain",
        "tests/application",
        "tests/infrastructure",
        "tests/presentation",
    ]

    for directory in directories:
        dir_path = project_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)

        # Use auto-discovery template for cli/commands
        if "cli" in directory and "commands" in directory:
            from vega.cli.templates import render_cli_commands_init
            content = render_cli_commands_init()
            (dir_path / "__init__.py").write_text(content)
        # Use auto-discovery template for events/
        elif directory == "events":
            from vega.cli.templates import render_events_init
            content = render_events_init()
            (dir_path / "__init__.py").write_text(content)

        click.echo(f"  + Created {directory}/")


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

    click.echo(f"\nGenerate components:")
    click.echo(f"  vega generate entity User")
    click.echo(f"  vega generate repository UserRepository")
    click.echo(f"  vega generate interactor CreateUser")
    click.echo(f"\n[Docs] https://vega-framework.readthedocs.io/")

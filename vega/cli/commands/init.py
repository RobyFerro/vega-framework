"""Init command - Create new Vega project"""
from __future__ import annotations

from pathlib import Path
import importlib.resources

import click

from vega.cli.scaffolds import create_fastapi_scaffold
from vega.cli.templates.loader import render_template
import vega


def _load_architecture_md() -> str | None:
    """Try to load ARCHITECTURE.md content from several known locations."""

    candidate_paths: list[Path] = []

    # When the framework is installed, the file may live next to the package.
    try:
        import vega  # type: ignore

        package_file = Path(getattr(vega, "__file__", ""))
        if package_file:
            package_dir = package_file.parent
            candidate_paths.append(package_dir / "ARCHITECTURE.md")
            candidate_paths.append(package_dir.parent / "ARCHITECTURE.md")
    except Exception:
        pass

    # When running from a cloned repository, walk up from this module.
    current_file = Path(__file__)
    candidate_paths.extend(parent / "ARCHITECTURE.md" for parent in current_file.parents)
    candidate_paths.append(Path.cwd() / "ARCHITECTURE.md")

    seen: set[str] = set()
    for candidate in candidate_paths:
        try:
            resolved = candidate if candidate.is_absolute() else candidate.resolve()
        except Exception:
            resolved = candidate

        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)

        if resolved.is_file():
            try:
                return resolved.read_text(encoding="utf-8")
            except Exception:
                continue

    # Fallback to package resources in case the file is bundled differently.
    try:
        files = getattr(importlib.resources, "files", None)
        if files:
            resource = files("vega").joinpath("ARCHITECTURE.md")
            if resource.is_file():
                return resource.read_text(encoding="utf-8")
        else:  # pragma: no cover - legacy Python fallback
            return importlib.resources.read_text("vega", "ARCHITECTURE.md", encoding="utf-8")
    except Exception:
        pass

    # setuptools-style fallback
    try:  # pragma: no cover - optional dependency
        import pkg_resources  # type: ignore

        data = pkg_resources.resource_string("vega", "ARCHITECTURE.md")
        if data:
            return data.decode("utf-8")
    except Exception:
        pass

    return None

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
        "tests/domain",
        "tests/application",
        "tests/infrastructure",
        "tests/presentation",
    ]

    for directory in directories:
        dir_path = project_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        (dir_path / "__init__.py").write_text("")
        click.echo(f"  + Created {directory}/")

    # Create __init__.py files
    (project_path / "__init__.py").write_text("")
    (project_path / "domain" / "__init__.py").write_text("")
    (project_path / "application" / "__init__.py").write_text("")
    (project_path / "infrastructure" / "__init__.py").write_text("")
    (project_path / "presentation" / "__init__.py").write_text("")
    (project_path / "tests" / "__init__.py").write_text("")

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

    # Copy ARCHITECTURE.md from vega framework to project root
    architecture_content = _load_architecture_md()
    if architecture_content:
        try:
            architecture_dest = project_path / "ARCHITECTURE.md"
            architecture_dest.write_text(architecture_content, encoding="utf-8")
            click.echo("  + Created ARCHITECTURE.md")
        except Exception:
            pass

    # Create main.py based on template
    if template == "fastapi":
        click.echo("\n[*] Adding FastAPI scaffold (presentation/web/)")
        create_fastapi_scaffold(project_path, project_name)

        # Create main.py for FastAPI project
        main_content = render_template("main.py.j2", project_name=project_name, template="fastapi")
        (project_path / "main.py").write_text(main_content)
        click.echo(f"  + Created main.py (FastAPI entrypoint)")
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

    if template == "fastapi":
        click.echo(f"\nRun commands:")
        click.echo(f"  python main.py web          # Start FastAPI server (http://localhost:8000)")
        click.echo(f"  python main.py web --reload # Start with auto-reload")
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

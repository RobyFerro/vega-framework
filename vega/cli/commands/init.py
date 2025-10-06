"""Init command - Create new Vega project"""
from __future__ import annotations

from pathlib import Path
import importlib.resources

import click

from vega.cli.scaffolds import create_fastapi_scaffold
from vega.cli.templates import render_standard_main, render_fastapi_project_main


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
    config_content = f'''"""Dependency Injection configuration for {project_name}"""
from vega.di import Container, set_container

# Domain interfaces (Abstract)
# Example:
# from {project_name}.domain.repositories.user_repository import UserRepository

# Infrastructure implementations (Concrete)
# Example:
# from {project_name}.infrastructure.repositories.memory_user_repository import MemoryUserRepository

# DI Registry: Map interfaces to implementations
SERVICES = {{
    # Example:
    # UserRepository: MemoryUserRepository,
}}

# Create and set container
container = Container(SERVICES)
set_container(container)
'''
    (project_path / "config.py").write_text(config_content)
    click.echo(f"  + Created config.py")

    # Create settings.py
    settings_content = f'''"""Application settings for {project_name}"""
from vega.settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration"""

    # Application
    app_name: str = Field(default="{project_name}")
    debug: bool = Field(default=False)

    # Add your settings here
    # database_url: str = Field(...)
    # api_key: str = Field(...)


# Global settings instance
settings = Settings()
'''
    (project_path / "settings.py").write_text(settings_content)
    click.echo(f"  + Created settings.py")

    # Create .env.example
    env_content = f'''# {project_name} - Environment Variables

# Application
APP_NAME={project_name}
DEBUG=true

# Add your environment variables here
# DATABASE_URL=postgresql://user:pass@localhost/dbname
# API_KEY=your_api_key_here
'''
    (project_path / ".env.example").write_text(env_content)
    click.echo(f"  + Created .env.example")

    # Create .gitignore
    gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
dist/
*.egg-info/

# Environment
.env
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db
'''
    (project_path / ".gitignore").write_text(gitignore_content)
    click.echo(f"  + Created .gitignore")

    # Create pyproject.toml with dependencies based on template
    fastapi_deps = ""
    if template == "fastapi":
        fastapi_deps = '''fastapi = "^0.115.0"
uvicorn = {extras = ["standard"], version = "^0.32.0"}
'''

    pyproject_content = f'''[tool.poetry]
name = "{project_name}"
version = "0.1.0"
description = "Vega Framework application"
authors = ["Your Name <you@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.10"
vega-framework = "^0.1.3"
pydantic = "^2.0"
pydantic-settings = "^2.0"
click = "^8.1.0"
{fastapi_deps}
[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
pytest-asyncio = "^0.21"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
'''
    (project_path / "pyproject.toml").write_text(pyproject_content)
    click.echo(f"  + Created pyproject.toml")

    # Create README.md
    fastapi_structure = ""
    if template == "fastapi":
        fastapi_structure = '''│
├── presentation/        # Delivery mechanisms
│   ├── web/            # FastAPI web interface
│   │   ├── routes/     # HTTP endpoints
│   │   ├── app.py      # FastAPI app factory
│   │   └── main.py     # ASGI entrypoint
│   └── cli/            # CLI commands (if needed)
'''
    else:
        fastapi_structure = '''│
├── presentation/        # Delivery mechanisms
│   └── cli/            # CLI commands
'''

    readme_content = f'''# {project_name}

Vega Framework application with Clean Architecture.

## Structure

```
{project_name}/
├── domain/              # 🔵 Business logic (framework-independent)
│   ├── entities/        # Business entities
│   ├── repositories/    # Repository interfaces
│   ├── services/        # Service interfaces
│   └── interactors/     # Use cases
│
├── application/         # 🟢 Application workflows
│   └── mediators/       # Complex workflows
│
├── infrastructure/      # 🟡 Concrete implementations
│   ├── repositories/    # Repository implementations
│   └── services/        # Service implementations
{fastapi_structure}│
├── config.py            # Dependency injection setup
├── settings.py          # Application configuration
└── main.py              # Application entry point
```

## Getting Started

```bash
# Install dependencies
poetry install

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Generate components
vega generate entity User
vega generate repository UserRepository
vega generate interactor CreateUser

# Run tests
poetry run pytest
```

## Vega Framework

This project uses [Vega Framework](https://github.com/your-org/vega-framework) for Clean Architecture:

- Automatic Dependency Injection
- Clean Architecture patterns (4 layers: Domain, Application, Infrastructure, Presentation)
- Type-safe with Python type hints
- Easy to test and maintain

## Documentation

- [Vega Framework Docs](https://vega-framework.readthedocs.io/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
'''
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
        main_content = render_fastapi_project_main(project_name)
        (project_path / "main.py").write_text(main_content)
        click.echo(f"  + Created main.py (FastAPI entrypoint)")
    else:
        # Create standard main.py
        main_content = render_standard_main(project_name)
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

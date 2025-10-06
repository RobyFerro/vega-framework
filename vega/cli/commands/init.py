"""Init command - Create new Vega project"""
import os
import click
from pathlib import Path


def init_project(project_name: str, template: str, parent_path: str):
    """Initialize a new Vega project with Clean Architecture structure"""

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
        "tests/domain",
        "tests/application",
        "tests/infrastructure",
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

    # Create pyproject.toml
    pyproject_content = f'''[tool.poetry]
name = "{project_name}"
version = "0.1.0"
description = "Vega Framework application"
authors = ["Your Name <you@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.10"
vega-framework = "^0.1.0"
pydantic = "^2.0"
pydantic-settings = "^2.0"

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
    readme_content = f'''# {project_name}

Vega Framework application with Clean Architecture.

## Structure

```
{project_name}/
├── domain/              # Business logic (framework-independent)
│   ├── entities/        # Business entities
│   ├── repositories/    # Repository interfaces
│   ├── services/        # Service interfaces
│   └── interactors/     # Use cases
│
├── application/         # Application workflows
│   └── mediators/       # Complex workflows
│
├── infrastructure/      # External implementations
│   ├── repositories/    # Repository implementations
│   └── services/        # Service implementations
│
├── config.py            # Dependency injection setup
└── settings.py          # Application configuration
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
- Clean Architecture patterns
- Type-safe with Python type hints
- Easy to test and maintain

## Documentation

- [Vega Framework Docs](https://vega-framework.readthedocs.io/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
'''
    (project_path / "README.md").write_text(readme_content, encoding='utf-8')
    click.echo(f"  + Created README.md")

    # Success message
    click.echo(f"\n{click.style('SUCCESS: Success!', fg='green', bold=True)} Project created successfully.\n")
    click.echo("Next steps:")
    click.echo(f"  cd {project_name}")
    click.echo(f"  poetry install")
    click.echo(f"  cp .env.example .env")
    click.echo(f"  vega generate entity User")
    click.echo(f"\n[Docs] https://vega-framework.readthedocs.io/")

from __future__ import annotations

from pathlib import Path
from typing import Callable

import click

from vega.cli.templates import (
    render_database_manager,
    render_alembic_ini,
    render_alembic_env,
    render_alembic_script_mako,
)


def create_sqlalchemy_scaffold(
    project_root: Path,
    project_name: str,
    *,
    overwrite: bool = False,
    echo: Callable[[str], None] | None = None,
) -> list[Path]:
    """Create SQLAlchemy scaffolding under the project infrastructure/ directory."""
    if echo is None:
        echo = click.echo

    created: list[Path] = []
    infrastructure_dir = project_root / "infrastructure"
    alembic_dir = project_root / "alembic"
    alembic_versions_dir = alembic_dir / "versions"

    # Ensure directories exist
    infrastructure_dir.mkdir(parents=True, exist_ok=True)
    alembic_dir.mkdir(parents=True, exist_ok=True)
    alembic_versions_dir.mkdir(parents=True, exist_ok=True)

    files = [
        (infrastructure_dir / "database_manager.py", render_database_manager()),
        (project_root / "alembic.ini", render_alembic_ini()),
        (alembic_dir / "env.py", render_alembic_env()),
        (alembic_dir / "script.py.mako", render_alembic_script_mako()),
    ]

    # Create .gitkeep for versions directory
    gitkeep_path = alembic_versions_dir / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.write_text("", encoding="utf-8")
        created.append(gitkeep_path.relative_to(project_root))
        echo(f"+ Created {click.style(str(gitkeep_path.relative_to(project_root)), fg='green')}")

    for path, content in files:
        rel_path = path.relative_to(project_root)
        if path.exists() and not overwrite:
            echo(
                click.style(
                    f"WARNING: {rel_path} already exists. Skipping.",
                    fg="yellow",
                )
            )
            continue

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created.append(rel_path)
        echo(f"+ Created {click.style(str(rel_path), fg='green')}")

    # Update config.py to add db_manager
    if _update_config_with_db_manager(project_root):
        echo(f"+ Updated {click.style('config.py', fg='green')} with DatabaseManager")

    # Update pyproject.toml with SQLAlchemy dependencies
    if _ensure_sqlalchemy_dependencies(project_root):
        echo(f"+ Updated {click.style('pyproject.toml', fg='green')} with SQLAlchemy dependencies")

    echo("\n[TIP] SQLAlchemy scaffold ready:")
    echo("   1. Add DATABASE_URL to your settings.py:")
    echo('      DATABASE_URL = "sqlite+aiosqlite:///./database.db"')
    echo("   2. poetry install  # sync dependencies (or poetry update)")
    echo("   3. vega migrate init  # initialize database")
    echo("   4. vega migrate create -m \"Initial migration\"  # create migration")
    echo("   5. vega migrate upgrade  # apply migration")

    return created


def _update_config_with_db_manager(project_root: Path) -> bool:
    """Add db_manager initialization to config.py if not present."""
    config_path = project_root / "config.py"
    if not config_path.exists():
        return False

    content = config_path.read_text(encoding="utf-8")

    # Check if db_manager already exists
    if "db_manager" in content:
        return False

    lines = content.splitlines()

    # Find import section and add DatabaseManager import
    import_added = False
    for i, line in enumerate(lines):
        if line.startswith("from infrastructure.") or line.startswith("from domain."):
            if "DatabaseManager" not in content:
                lines.insert(i, "from infrastructure.database_manager import DatabaseManager")
                import_added = True
            break

    # If no infrastructure imports found, add after settings import
    if not import_added:
        for i, line in enumerate(lines):
            if "from settings import" in line or "import settings" in line:
                lines.insert(i + 1, "from infrastructure.database_manager import DatabaseManager")
                import_added = True
                break

    # Add db_manager initialization after settings
    db_manager_added = False
    for i, line in enumerate(lines):
        if "settings = Settings()" in line or "settings = " in line:
            # Insert db_manager after settings initialization
            lines.insert(i + 1, "")
            lines.insert(i + 2, "# Database Manager")
            lines.insert(i + 3, "db_manager = DatabaseManager(settings.DATABASE_URL)")
            db_manager_added = True
            break

    if import_added or db_manager_added:
        config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True

    return False


def _ensure_sqlalchemy_dependencies(project_root: Path) -> bool:
    """Ensure SQLAlchemy dependencies exist in pyproject.toml; return True if modified."""
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        return False

    content = pyproject_path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)

    changed = False
    changed |= _ensure_dependency_line(lines, "sqlalchemy", "^2.0")
    changed |= _ensure_dependency_line(lines, "alembic", "^1.13")
    changed |= _ensure_dependency_line(lines, "aiosqlite", "^0.19")

    if changed:
        pyproject_path.write_text("".join(lines), encoding="utf-8")

    return changed


def _ensure_dependency_line(lines: list[str], name: str, spec: str) -> bool:
    """Insert dependency assignment into [tool.poetry.dependencies] if missing."""
    header = "[tool.poetry.dependencies]"
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == header)
    except StopIteration:
        return False

    end = start + 1
    while end < len(lines) and not lines[end].startswith("["):
        end += 1

    block = lines[start + 1:end]
    if any(line.strip().startswith(f"{name} =") for line in block):
        return False

    insertion = f"{name} = \"{spec}\"\n"
    lines.insert(end, insertion)
    return True

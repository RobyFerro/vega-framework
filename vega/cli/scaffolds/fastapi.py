from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

import click

from vega.cli.templates import (
    render_fastapi_app,
    render_fastapi_health_route,
    render_fastapi_main,
    render_fastapi_routes_init_autodiscovery,
    render_fastapi_user_route,
    render_pydantic_models_init,
    render_pydantic_user_models,
    render_web_package_init,
)


def create_fastapi_scaffold(
    project_root: Path,
    project_name: str,
    *,
    overwrite: bool = False,
    echo: Callable[[str], None] | None = None,
) -> list[Path]:
    """Create FastAPI scaffolding under the project presentation/web/ directory."""
    if echo is None:
        echo = click.echo

    created: list[Path] = []
    web_dir = project_root / "presentation" / "web"
    routes_dir = web_dir / "routes"
    models_dir = web_dir / "models"

    files: Iterable[tuple[Path, str]] = (
        (web_dir / "__init__.py", render_web_package_init()),
        (web_dir / "app.py", render_fastapi_app(project_name)),
        (web_dir / "main.py", render_fastapi_main(project_name)),
        (routes_dir / "__init__.py", render_fastapi_routes_init_autodiscovery()),
        (routes_dir / "health.py", render_fastapi_health_route()),
        (routes_dir / "users.py", render_fastapi_user_route()),
        (models_dir / "__init__.py", render_pydantic_models_init()),
        (models_dir / "user_models.py", render_pydantic_user_models()),
    )

    web_dir.mkdir(parents=True, exist_ok=True)
    routes_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

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

    echo("\n[TIP] FastAPI scaffold ready:")
    echo("   1. poetry install  # sync dependencies (or poetry update)")
    echo("   2. poetry run uvicorn presentation.web.main:app --reload")

    return created

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

from pathlib import Path

import pytest

from vega.discovery import discover_routers_ddd


def _write(file: Path, content: str) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8")


def test_discover_routers_ddd_includes_shared_health(tmp_path, monkeypatch):
    """
    The shared/default router should expose /health at root when discovered.
    """
    project_root = tmp_path / "proj"
    shared_routes = project_root / "shared" / "presentation" / "web" / "routes"

    # Minimal package structure
    for pkg_dir in [
        project_root,
        project_root / "shared",
        project_root / "shared" / "presentation",
        project_root / "shared" / "presentation" / "web",
        shared_routes,
    ]:
        _write(pkg_dir / "__init__.py", "")

    _write(
        shared_routes / "default.py",
        """from vega.web import Router

router = Router()


@router.get("/health")
async def health():
    return {"status": "healthy"}
""",
    )

    monkeypatch.syspath_prepend(str(tmp_path))

    main_router = discover_routers_ddd("proj", include_builtin=False)

    shared_root_router = next(
        (child for child in main_router.child_routers if child[1] == ""), None
    )
    assert shared_root_router is not None, "Shared default router not registered at root"

    shared_router = shared_root_router[0]
    paths = {route.path for route in shared_router.routes}
    assert "/health" in paths, "Health route missing from shared default router"


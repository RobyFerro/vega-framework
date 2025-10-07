"""
CleanArch Framework

A lightweight Python framework for building applications with Clean Architecture.

Features:
- Automatic Dependency Injection
- Clean Architecture patterns (Interactor, Mediator, Repository)
- Type-safe with Python type hints
- Scoped dependency management (Singleton, Scoped, Transient)
- CLI scaffolding tools

Example:
    from vega.patterns import Interactor
    from vega.di import bind

    class CreateUser(Interactor[User]):
        def __init__(self, name: str, email: str):
            self.name = name
            self.email = email

        @bind
        async def call(self, repository: UserRepository) -> User:
            user = User(name=self.name, email=self.email)
            return await repository.save(user)
"""

import tomllib
from pathlib import Path

def _get_version() -> str:
    """Read version from pyproject.toml or use importlib.metadata as fallback"""
    try:
        # Try reading from pyproject.toml (development)
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                pyproject = tomllib.load(f)
                return pyproject["tool"]["poetry"]["version"]
    except Exception:
        pass

    try:
        # Fallback to importlib.metadata (installed package)
        from importlib.metadata import version
        return version("vega-framework")
    except Exception:
        return "0.0.0"

__version__ = _get_version()
__author__ = "Roberto Ferro"

from vega.di import bind, injectable, Scope, scope_context
from vega.patterns import Interactor, Mediator, Repository, Service

__all__ = [
    "bind",
    "injectable",
    "Scope",
    "scope_context",
    "Interactor",
    "Mediator",
    "Repository",
    "Service",
]

"""
Vega Framework v2.0

Enterprise-ready Python framework with Domain-Driven Design (DDD), CQRS,
and Clean Architecture for building maintainable and scalable applications.

Features:
- Domain-Driven Design with Bounded Contexts
- CQRS (Command Query Responsibility Segregation)
- Automatic Dependency Injection
- Clean Architecture patterns (Interactor, Mediator, Repository)
- DDD patterns (Aggregate, Value Object, Domain Events)
- Type-safe with Python type hints
- Scoped dependency management (Singleton, Scoped, Transient)
- CLI scaffolding tools for rapid development

Example:
    from vega.patterns import CommandHandler, AggregateRoot
    from vega.di import bind
    from dataclasses import dataclass

    @dataclass
    class Order(AggregateRoot[str]):
        id: str
        total: float

    class CreateOrder(CommandHandler[Order]):
        def __init__(self, customer_id: str, total: float):
            self.customer_id = customer_id
            self.total = total

        @bind
        async def call(self, repository: OrderRepository) -> Order:
            order = Order(id="...", total=self.total)
            return await repository.save(order)
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
from vega.patterns import (
    Interactor,
    Mediator,
    Repository,
    Service,
    AggregateRoot,
    CommandHandler,
    QueryHandler,
)

__all__ = [
    "bind",
    "injectable",
    "Scope",
    "scope_context",
    "Interactor",
    "Mediator",
    "Repository",
    "Service",
    "AggregateRoot",
    "CommandHandler",
    "QueryHandler",
]

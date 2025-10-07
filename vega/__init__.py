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

__version__ = "0.1.5"
__author__ = "CleanArch Contributors"

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

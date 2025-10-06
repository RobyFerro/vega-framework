"""
Dependency Injection system for CleanArch Framework

This module provides automatic dependency injection through decorators.

Features:
- Automatic dependency resolution from IOC container
- Support for Singleton, Scoped, and Transient lifetimes
- Thread-safe scoped instances for concurrent operations
- @injectable: for classes (decorates __init__)
- @bind: for methods (decorates any method, default SCOPED)

Scopes:
- SINGLETON: One instance for the entire application lifecycle
- SCOPED: One instance per operation/request (shared within operation)
- TRANSIENT: New instance every time (no caching)

Example:
    from vega.di import bind, injectable, Scope
    from vega.patterns import Interactor

    @injectable(scope=Scope.SINGLETON)
    class EmailService:
        def send(self, to: str, message: str):
            pass

    class CreateUser(Interactor[User]):
        @bind
        async def call(self, email_service: EmailService) -> User:
            # email_service is auto-injected
            await email_service.send(user.email, "Welcome!")
            return user
"""

from vega.di.scope import Scope, scope_context, clear_singletons, get_singleton_instance
from vega.di.decorators import bind, injectable
from vega.di.errors import DependencyInjectionError
from vega.di.container import Container, get_container, set_container, resolve

__all__ = [
    "Scope",
    "scope_context",
    "clear_singletons",
    "get_singleton_instance",
    "bind",
    "injectable",
    "DependencyInjectionError",
    "Container",
    "get_container",
    "set_container",
    "resolve",
]

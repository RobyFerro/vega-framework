"""
Bean decorator for automatic dependency injection registration.

This module provides the @bean decorator that automatically registers classes
in the DI container, enabling dependency injection without manual registration.
"""

import inspect
from abc import ABC
import logging
from typing import Type, TypeVar, Optional, Any, Dict
from vega.di.scope import Scope
from vega.di.container import get_container
from vega.di.errors import DependencyInjectionError
from vega.patterns import Repository, Service


T = TypeVar('T')


def bean(
    cls: Type[T] = None,
    *,
    scope: Scope = Scope.SCOPED,
    interface: Type = None,
    **constructor_params: Any
) -> Type[T]:
    """
    Register a class in the DI container automatically.

    This decorator handles automatic registration of classes in the dependency
    injection container. It supports:
    - Auto-detection of abstract interfaces (classes inheriting from ABC, Repository, or Service)
    - Registration of concrete classes
    - Constructor parameter injection
    - Configurable scope (SINGLETON, SCOPED, TRANSIENT)

    Args:
        cls: The class to decorate (when used without parameters)
        scope: The lifecycle scope (default: SCOPED)
        interface: Explicit interface to register against (optional)
        **constructor_params: Parameters to pass to the constructor

    Returns:
        The decorated class (unchanged, but registered in the container)

    Raises:
        DependencyInjectionError: If multiple interfaces found without explicit interface parameter

    Examples:
        # Basic usage with ABC interface
        @bean
        class SqlUserRepository(UserRepository):  # UserRepository inherits from ABC
            def __init__(self, db: DatabaseManager):
                self._db = db

        # Basic usage with Repository pattern
        @bean
        class PostgresUserRepository(UserRepository):  # UserRepository inherits from Repository
            def __init__(self, db: DatabaseManager):
                self._db = db

        # Basic usage with Service pattern
        @bean
        class SendgridEmailService(EmailService):  # EmailService inherits from Service
            def __init__(self, api_key: str):
                self.api_key = api_key

        # Concrete class without interface
        @bean
        class ConfigService:
            def __init__(self):
                pass

        # With constructor parameters
        @bean(url=settings.database_url, scope=Scope.SINGLETON)
        class DatabaseManager:
            def __init__(self, url: str):
                self.url = url

        # Multiple interfaces - explicit interface required
        @bean(interface=UserRepository)
        class SqlUserRepository(UserRepository, AuditableRepository):
            pass

        # Override scope
        @bean(scope=Scope.SINGLETON)
        class CacheService:
            pass
    """

    def decorator(target_cls: Type[T]) -> Type[T]:
        """Inner decorator that performs the actual registration."""

        # Determine which interface to register against
        detected_interface = _detect_interface(target_cls, interface)

        # Register in the global container
        container = get_container()

        # If constructor params are provided, register as a factory lambda
        if constructor_params:
            # Create a factory function that instantiates with the provided params
            factory = _create_factory_with_params(target_cls, constructor_params, container)
            container.register_factory(detected_interface, factory, scope=scope)
            # Also add the concrete class to _concrete_services so it can be resolved directly
            # when used as a dependency in other classes
            if target_cls not in container._concrete_services:
                container._concrete_services.append(target_cls)
        else:
            # Standard registration: interface -> concrete class
            container.register(detected_interface, target_cls)

        # Store metadata on the class for introspection (including DI-compatible flags)
        target_cls._bean_registered = True
        target_cls._bean_interface = detected_interface
        target_cls._bean_scope = scope
        # Mark class as DI-enabled for container resolution
        target_cls._di_enabled = True
        target_cls._di_scope = scope

        return target_cls

    # Support both @bean and @bean(...) syntax
    if cls is None:
        # Called with parameters: @bean(scope=..., ...)
        return decorator
    else:
        # Called without parameters: @bean
        return decorator(cls)


def _detect_interface(cls: Type, explicit_interface: Optional[Type] = None) -> Type:
    """
    Detect which interface to register the class against.

    Logic:
    1. If explicit_interface is provided, use it
    2. If class inherits from ABC, Repository, or Service classes, use the first one
    3. If multiple interface classes found, raise error
    4. Otherwise, register the class as its own interface

    Args:
        cls: The class to analyze
        explicit_interface: Explicitly provided interface (optional)

    Returns:
        The interface type to register

    Raises:
        DependencyInjectionError: If multiple interfaces found without explicit parameter
    """

    # If explicit interface provided, use it
    if explicit_interface is not None:
        return explicit_interface

    # Get all base classes (excluding object)
    bases = [base for base in cls.__bases__ if base is not object]

    # Filter only ABC-based interfaces
    abc_interfaces = [base for base in bases if _is_abc_interface(base)]

    # No ABC interfaces found - register class as its own interface
    if not abc_interfaces:
        return cls

    # Exactly one ABC interface - use it
    if len(abc_interfaces) == 1:
        return abc_interfaces[0]

    # Multiple ABC interfaces - require explicit interface parameter
    interface_names = [iface.__name__ for iface in abc_interfaces]
    raise DependencyInjectionError(
        f"Class '{cls.__name__}' implements multiple interfaces: {interface_names}. "
        f"Please specify which interface to register using @bean(interface=YourInterface)"
    )


def _is_abc_interface(cls: Type) -> bool:
    """
    Check if a class is an interface (ABC, Repository, or Service).

    A class is considered an interface if it inherits from:
    - ABC (Abstract Base Class)
    - Repository (pattern class for data persistence)
    - Service (pattern class for external integrations)

    Args:
        cls: The class to check

    Returns:
        True if the class is an ABC, Repository, or Service, False otherwise
    """
    try:
        mro = inspect.getmro(cls)
        # Check if ABC, Repository, or Service is in the method resolution order
        return ABC in mro or Repository in mro or Service in mro
    except (AttributeError, TypeError):
        return False


def _create_factory_with_params(cls: Type[T], params: Dict[str, Any], container) -> Type[T]:
    """
    Create a factory function that wraps a class with pre-configured parameters.

    This factory function allows mixing of:
    - Pre-configured parameters (passed via @bean decorator)
    - Auto-injected dependencies (resolved by the container)

    Args:
        cls: The class to instantiate
        params: Parameters to pass to the constructor
        container: DI container used to resolve remaining deps

    Returns:
        A factory class that the container can instantiate
    """

    def factory():
        """
        Factory closure that mixes configured params with DI-resolved ones.
        Uses the container public helper to remain scope-aware.
        """
        return container.build(cls, **params)

    return factory


def get_bean_metadata(cls: Type) -> Optional[Dict[str, Any]]:
    """
    Get bean registration metadata from a class.

    Args:
        cls: The class to inspect

    Returns:
        Dictionary with metadata if class is a bean, None otherwise
        Keys: 'registered', 'interface', 'scope'
    """
    if not hasattr(cls, '_bean_registered'):
        return None

    return {
        'registered': getattr(cls, '_bean_registered', False),
        'interface': getattr(cls, '_bean_interface', None),
        'scope': getattr(cls, '_bean_scope', None),
    }


def is_bean(cls: Type) -> bool:
    """
    Check if a class has been decorated with @bean.

    Args:
        cls: The class to check

    Returns:
        True if the class is decorated with @bean, False otherwise
    """
    return getattr(cls, '_bean_registered', False)

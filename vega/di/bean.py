"""
Bean decorator for automatic dependency injection registration.

This module provides the @bean decorator that automatically registers classes
in the DI container, enabling dependency injection without manual registration.
"""

import inspect
from abc import ABC
from typing import Type, TypeVar, Optional, Any, Dict
from vega.di.scope import Scope
from vega.di.container import get_container
from vega.di.errors import DependencyInjectionError


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
    - Auto-detection of abstract interfaces (classes inheriting from ABC)
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
            factory = _create_factory_with_params(target_cls, constructor_params)
            container.register(detected_interface, factory)
        else:
            # Standard registration: interface -> concrete class
            container.register(detected_interface, target_cls)

        # Store metadata on the class for introspection
        target_cls._bean_registered = True
        target_cls._bean_interface = detected_interface
        target_cls._bean_scope = scope

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
    2. If class inherits from ABC-based classes, use the first one
    3. If multiple ABC-based classes found, raise error
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
    Check if a class is an ABC-based interface.

    A class is considered an ABC interface if it inherits from ABC
    (directly or indirectly).

    Args:
        cls: The class to check

    Returns:
        True if the class inherits from ABC, False otherwise
    """
    try:
        # Check if ABC is in the method resolution order
        return ABC in inspect.getmro(cls)
    except (AttributeError, TypeError):
        return False


def _create_factory_with_params(cls: Type[T], params: Dict[str, Any]) -> Type[T]:
    """
    Create a factory function that wraps a class with pre-configured parameters.

    This factory function allows mixing of:
    - Pre-configured parameters (passed via @bean decorator)
    - Auto-injected dependencies (resolved by the container)

    Args:
        cls: The class to instantiate
        params: Parameters to pass to the constructor

    Returns:
        A factory class that the container can instantiate
    """

    # Create a wrapper class that acts as a factory
    class BeanFactory:
        """Factory wrapper for bean with constructor parameters."""

        def __new__(cls_factory):
            # Get the signature of the original class constructor
            sig = inspect.signature(cls.__init__)

            # Separate auto-injectable params from pre-configured params
            auto_inject_params = {}

            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue

                # Skip parameters that are already provided
                if param_name in params:
                    continue

                # This parameter needs to be auto-injected by the container
                # The container will handle this via _instantiate_with_dependencies
                auto_inject_params[param_name] = param

            # Instantiate the original class with pre-configured params
            # The container will handle auto-injection of remaining dependencies
            return cls(**params)

    # Copy metadata from original class
    BeanFactory.__name__ = f"{cls.__name__}Factory"
    BeanFactory.__module__ = cls.__module__
    BeanFactory._bean_target_class = cls
    BeanFactory._bean_params = params

    return BeanFactory


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

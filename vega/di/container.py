"""IOC Container for dependency resolution"""
import inspect
from typing import Type, TypeVar, get_type_hints, Dict, Any

from vega.di.scope import _scope_manager, Scope

T = TypeVar('T')


class Container:
    """
    Inversion of Control container for dependency injection.

    Maps abstract interfaces to concrete implementations.

    Example:
        from vega.di import Container

        # Define mappings
        container = Container({
            EmailService: SendgridEmailService,
            UserRepository: PostgresUserRepository,
        })

        # Resolve dependencies
        email_service = container.resolve(EmailService)
    """

    def __init__(self, services: Dict[Type, Type] = None):
        """
        Initialize container with service mappings.

        Args:
            services: Dictionary mapping abstract types to concrete implementations
        """
        self._services = services or {}
        self._concrete_services = list(self._services.values())

    def register(self, abstract: Type, concrete: Type):
        """
        Register a service mapping.

        Args:
            abstract: Abstract interface type
            concrete: Concrete implementation type
        """
        self._services[abstract] = concrete
        if concrete not in self._concrete_services:
            self._concrete_services.append(concrete)

    def _instantiate_with_dependencies(self, cls: Type[T]) -> T:
        """
        Instantiate a class by resolving its constructor dependencies recursively.

        Supports scoped caching for classes decorated with @injectable(scope=Scope.SCOPED).

        Args:
            cls: The class to instantiate

        Returns:
            Instance of the class with all dependencies resolved
        """
        # Check if class has @injectable decorator with scope
        if hasattr(cls, '_di_enabled') and cls._di_enabled:
            # Use ScopeManager to handle caching
            if hasattr(cls, '_di_scope'):
                cache_key = f"{cls.__module__}.{cls.__name__}"
                return _scope_manager.get_or_create(
                    cache_key=cache_key,
                    scope=cls._di_scope,
                    factory=lambda: cls(),
                    context_name=f"class '{cls.__name__}'"
                )
            else:
                # No scope specified, just instantiate
                return cls()

        # Get constructor signature
        try:
            sig = inspect.signature(cls.__init__)
            hints = get_type_hints(cls.__init__)
        except Exception:
            # If we can't inspect, try to instantiate without args
            return cls()

        # Resolve constructor dependencies
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # Skip parameters with defaults
            if param.default is not inspect.Parameter.empty:
                continue

            # Get type hint
            param_type = hints.get(param_name)
            if param_type is None:
                continue

            # Resolve dependency recursively
            if param_type in self._services or param_type in self._concrete_services:
                kwargs[param_name] = self.resolve(param_type)

        return cls(**kwargs)

    def resolve(self, service: Type[T]) -> T:
        """
        Resolve a service from the registry.

        Supports both abstract interface types and concrete implementations.
        Automatically resolves dependencies recursively.

        Args:
            service: Either an abstract interface or concrete class type

        Returns:
            Instance of the requested service with all dependencies resolved

        Raises:
            ValueError: If service is not registered

        Examples:
            # Interface-based (recommended)
            auth_service = container.resolve(AuthorizationService)

            # Concrete type
            repo = container.resolve(PostgresUserRepository)
        """
        if not isinstance(service, type):
            raise ValueError(f"Invalid service type: {type(service)}. Expected a class type.")

        # Check if it's an abstract interface that needs mapping
        if service in self._services:
            concrete_class = self._services[service]
            return self._instantiate_with_dependencies(concrete_class)

        # Check if it's already a concrete implementation
        if service in self._concrete_services:
            return self._instantiate_with_dependencies(service)

        raise ValueError(
            f"Service {service.__name__} not registered. "
            f"Available abstracts: {list(self._services.keys())}"
        )


# Global default container (can be overridden per application)
_default_container: Container = Container()


def get_container() -> Container:
    """Get the default global container."""
    return _default_container


def set_container(container: Container):
    """Set the default global container."""
    global _default_container
    _default_container = container


def resolve(service: Type[T]) -> T:
    """
    Resolve a service from the default global container.

    This is a convenience function that uses the default container.

    Args:
        service: Service type to resolve

    Returns:
        Instance of the service
    """
    return _default_container.resolve(service)

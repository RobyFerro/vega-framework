"""IOC Container for dependency resolution"""
import inspect
from typing import Type, TypeVar, get_type_hints, Dict, Any, Callable, Tuple, Iterable

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
        self._services: Dict[Type, Type] = services or {}
        self._concrete_services = list(self._services.values())
        # Factories are stored separately to avoid changing existing semantics.
        self._factories: Dict[Type, Tuple[Callable[[], Any], Scope]] = {}

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

    def register_factory(self, abstract: Type, factory: Callable[[], Any], *, scope: Scope = Scope.TRANSIENT):
        """
        Register a factory for an abstract type.

        This keeps backward compatibility by living alongside `register`.
        """
        self._factories[abstract] = (factory, scope)

    # --- Public inspection helpers (to reduce direct access to privates) ---
    def is_registered(self, abstract: Type) -> bool:
        """Check if an abstract type is registered (class or factory)."""
        return abstract in self._services or abstract in self._factories

    def has_concrete(self, cls: Type) -> bool:
        """Check if a concrete implementation is known to the container."""
        return cls in self._concrete_services

    def get_bindings(self) -> Dict[Type, Any]:
        """Return a copy of bindings (abstract -> concrete/factory)."""
        # Factories shadow class bindings when present.
        merged: Dict[Type, Any] = {**self._services}
        merged.update({k: v[0] for k, v in self._factories.items()})
        return dict(merged)

    def iter_concretes(self) -> Iterable[Type]:
        """Iterate over known concrete classes."""
        return tuple(self._concrete_services)

    def _resolve_constructor_kwargs(self, cls: Type[T]) -> Dict[str, Any]:
        """
        Resolve constructor dependencies for a class.

        Args:
            cls: The class to resolve dependencies for

        Returns:
            Dictionary of resolved dependencies
        """
        # Get constructor signature
        try:
            sig = inspect.signature(cls.__init__)
            hints = get_type_hints(cls.__init__)
        except Exception:
            # If we can't inspect, return empty kwargs
            return {}

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
            if self.is_registered(param_type) or self.has_concrete(param_type):
                kwargs[param_name] = self.resolve(param_type)

        return kwargs

    def _instantiate_with_dependencies(self, cls: Type[T]) -> T:
        """
        Instantiate a class by resolving its constructor dependencies recursively.

        Supports scoped caching for classes decorated with @injectable(scope=Scope.SCOPED).

        Args:
            cls: The class to instantiate

        Returns:
            Instance of the class with all dependencies resolved
        """
        # Check if class has @injectable or @bean decorator with scope
        if hasattr(cls, '_di_enabled') and cls._di_enabled:
            # Use ScopeManager to handle caching
            if hasattr(cls, '_di_scope'):
                # Use class ID for cache key to handle local classes with same name
                cache_key = f"{cls.__module__}.{cls.__name__}@{id(cls)}"

                # Create factory that resolves dependencies
                def factory():
                    kwargs = self._resolve_constructor_kwargs(cls)
                    return cls(**kwargs)

                return _scope_manager.get_or_create(
                    cache_key=cache_key,
                    scope=cls._di_scope,
                    factory=factory,
                    context_name=f"class '{cls.__name__}'"
                )
            else:
                # No scope specified, just instantiate with dependencies
                kwargs = self._resolve_constructor_kwargs(cls)
                return cls(**kwargs)

        # For classes without @bean/@injectable, resolve dependencies directly
        kwargs = self._resolve_constructor_kwargs(cls)
        return cls(**kwargs)

    def _resolve_factory(self, abstract: Type[T]) -> T:
        factory, scope = self._factories[abstract]
        cache_key = f"factory:{abstract.__module__}.{abstract.__name__}"

        def run_factory():
            return factory()

        if scope == Scope.TRANSIENT:
            return run_factory()

        return _scope_manager.get_or_create(
            cache_key=cache_key,
            scope=scope,
            factory=run_factory,
            context_name=f"factory '{abstract.__name__}'"
        )

    def build(self, cls: Type[T], **provided_kwargs: Any) -> T:
        """
        Public helper to instantiate a class with DI plus provided kwargs.
        Provided kwargs override auto-resolved ones.
        """
        kwargs = self._resolve_constructor_kwargs(cls)
        kwargs.update(provided_kwargs)
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

        # Check if there's a factory registered
        if service in self._factories:
            return self._resolve_factory(service)

        # Check if it's an abstract interface that needs mapping
        if service in self._services:
            concrete_class = self._services[service]
            return self._instantiate_with_dependencies(concrete_class)

        # Check if it's already a concrete implementation
        if service in self._concrete_services:
            return self._instantiate_with_dependencies(service)

        raise ValueError(
            f"Service {service.__name__} not registered. "
            f"Available abstracts: {list(self.get_bindings().keys())}"
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


def Summon(service: Type[T]) -> T:
    """
    Summon (resolve) a service from the DI container.

    Type-safe service locator pattern for manual dependency resolution.
    Use this when you need to resolve dependencies outside of @bind context
    or when you need dynamic resolution.

    Args:
        service: The class type to resolve (not a string, actual class)

    Returns:
        Instance of the service with all dependencies resolved

    Raises:
        ValueError: If service is not registered in the container

    Examples:
        # Resolve a repository
        user_repo = Summon(UserRepository)

        # Resolve a service
        email_service = Summon(EmailService)

        # In any class or function
        def my_function():
            repository = Summon(ProductRepository)
            return repository.find_all()

        # In event handlers
        @subscribe(UserCreated)
        async def on_user_created(event: UserCreated):
            email_service = Summon(EmailService)
            await email_service.send_welcome(event.email)
    """
    return _default_container.resolve(service)

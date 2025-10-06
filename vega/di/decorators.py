"""Dependency injection decorators"""
import inspect
import logging
from functools import wraps
from typing import Callable, Dict, Any, get_type_hints

from vega.di.scope import Scope, _scope_manager, scope_context
from vega.di.errors import DependencyInjectionError
from vega.di.container import get_container

logger = logging.getLogger(__name__)


def _resolve_dependencies_from_hints(
    method: Callable,
    provided_kwargs: Dict[str, Any],
    scope: Scope = Scope.TRANSIENT,
    context_name: str = "unknown"
) -> Dict[str, Any]:
    """
    Resolve dependencies from type hints.

    Shared between @injectable and @bind decorators.
    """
    container = get_container()

    # Get type hints
    try:
        hints = get_type_hints(method)
    except Exception as e:
        hints = method.__annotations__ if hasattr(method, '__annotations__') else {}
        logger.debug(f"{context_name}: Using __annotations__ instead of get_type_hints: {e}")

    # Get signature for parameters with defaults
    try:
        sig = inspect.signature(method)
        params_with_defaults = {
            name: param.default
            for name, param in sig.parameters.items()
            if param.default is not inspect.Parameter.empty
        }
    except Exception:
        params_with_defaults = {}

    resolved = {}

    # Auto-resolve dependencies
    for param_name, param_type in hints.items():
        if param_name == 'return':
            continue

        # Skip if already provided
        if param_name in provided_kwargs:
            resolved[param_name] = provided_kwargs[param_name]
            continue

        # Skip if has default value
        if param_name in params_with_defaults:
            continue

        # Try to resolve the dependency
        # param_type could be either abstract or concrete
        try:
            # Check if type is registered in container
            if param_type in container._services or param_type in container._concrete_services:
                # Create cache key and factory
                cache_key = f"{param_type.__module__}.{param_type.__name__}"
                factory = lambda pt=param_type: container.resolve(pt)

                # Use ScopeManager to get or create instance
                resolved[param_name] = _scope_manager.get_or_create(
                    cache_key=cache_key,
                    scope=scope,
                    factory=factory,
                    context_name=f"{context_name} -> {param_name}"
                )
        except Exception as e:
            # Dependency not found or error resolving
            logger.debug(
                f"{context_name}: Could not resolve '{param_name}' of type '{param_type}': {e}"
            )

    return resolved


def bind(method: Callable = None, *, scope: Scope = Scope.SCOPED) -> Callable:
    """
    Enable automatic dependency injection for methods.

    Default scope is SCOPED: dependencies are shared within the same operation
    but separate instances are created for different operations.

    Examples:
        class MyInteractor:
            @bind
            async def call(self, repository: ProjectRepository) -> Result:
                return await repository.get(...)

        @bind(scope=Scope.SINGLETON)
        async def get_config(config: ConfigService) -> dict:
            return config.load()
    """

    def decorator(func: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(func)
        func_name = func.__name__

        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Auto-create scope context if using SCOPED and no scope is active
                # This makes @bind transparent - the first @bind creates the scope
                with scope_context():
                    # Resolve dependencies
                    resolved_kwargs = _resolve_dependencies_from_hints(
                        method=func,
                        provided_kwargs=kwargs,
                        scope=scope,
                        context_name=func_name
                    )

                    # Call original function with resolved dependencies
                    return await func(*args, **resolved_kwargs)

            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Auto-create scope context if using SCOPED and no scope is active
                with scope_context():
                    # Resolve dependencies
                    resolved_kwargs = _resolve_dependencies_from_hints(
                        method=func,
                        provided_kwargs=kwargs,
                        scope=scope,
                        context_name=func_name
                    )

                    # Call original function with resolved dependencies
                    return func(*args, **resolved_kwargs)

            return sync_wrapper

    # Support both @bind and @bind(scope=...)
    if method is None:
        return decorator
    else:
        return decorator(method)


def injectable(cls=None, *, scope: Scope = Scope.TRANSIENT):
    """
    Enable auto-injection of dependencies from IOC container.

    Supports Singleton, Scoped, and Transient lifetimes.
    Allows manual override for testing.

    Examples:
        @injectable
        class MyService:
            def __init__(self, repository: ProjectRepository):
                self.repository = repository

        @injectable(scope=Scope.SINGLETON)
        class ConfigService:
            def __init__(self, settings: SettingsRepository):
                self.settings = settings
    """

    def decorator(target_cls):
        original_init = target_cls.__init__
        class_name = target_cls.__name__

        def new_init(self, *args, **kwargs):
            # If positional arguments provided, pass to original constructor
            if args:
                logger.warning(
                    f"{class_name}: Using positional arguments. "
                    "Consider using keyword arguments for better DI support."
                )
                original_init(self, *args, **kwargs)
                return

            # Use common logic to resolve dependencies
            resolved_kwargs = _resolve_dependencies_from_hints(
                method=original_init,
                provided_kwargs=kwargs,
                scope=scope,
                context_name=f"class '{class_name}'"
            )

            try:
                original_init(self, **resolved_kwargs)
            except TypeError as e:
                # Provide detailed error on missing parameters
                raise DependencyInjectionError(
                    f"Failed to initialize {class_name}: {str(e)}. "
                    f"Provided kwargs: {list(resolved_kwargs.keys())}"
                ) from e

        new_init.__name__ = original_init.__name__
        new_init.__doc__ = original_init.__doc__
        target_cls.__init__ = new_init

        # Add metadata for introspection
        target_cls._di_scope = scope
        target_cls._di_enabled = True

        return target_cls

    # Support both @injectable and @injectable(scope=...)
    if cls is None:
        # Called with parameters: @injectable(scope=...)
        return decorator
    else:
        # Called without parameters: @injectable
        return decorator(cls)

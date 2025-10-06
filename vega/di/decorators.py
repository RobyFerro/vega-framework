"""Dependency injection decorators"""
import inspect
import logging
from functools import wraps
from typing import Callable, Dict, Any, get_type_hints, Tuple

from vega.di.scope import Scope, _scope_manager, scope_context
from vega.di.errors import DependencyInjectionError
from vega.di.container import get_container

logger = logging.getLogger(__name__)

# Constants for method detection
_METHOD_FIRST_PARAMS = frozenset({'self', 'cls'})


def _is_instance_or_class_method(func: Callable) -> bool:
    """
    Check if a function is an instance or class method.

    Returns True if the first parameter is 'self' or 'cls'.
    """
    try:
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        return len(params) > 0 and params[0] in _METHOD_FIRST_PARAMS
    except Exception:
        return False


def _resolve_and_merge_kwargs(
    func: Callable,
    provided_kwargs: Dict[str, Any],
    scope: Scope,
    is_method: bool
) -> Dict[str, Any]:
    """
    Resolve dependencies and merge with provided kwargs.

    Args:
        func: The function to resolve dependencies for
        provided_kwargs: Already provided keyword arguments
        scope: Dependency scope
        is_method: Whether the function is an instance/class method

    Returns:
        Merged dictionary of resolved dependencies and provided kwargs
    """
    return _resolve_dependencies_from_hints(
        method=func,
        provided_kwargs=provided_kwargs,
        scope=scope,
        context_name=func.__name__,
        skip_first_param=is_method
    )


def _resolve_dependencies_from_hints(
    method: Callable,
    provided_kwargs: Dict[str, Any],
    scope: Scope = Scope.TRANSIENT,
    context_name: str = "unknown",
    skip_first_param: bool = False
) -> Dict[str, Any]:
    """
    Resolve dependencies from type hints using the DI container.

    This function inspects the type hints of a method and automatically resolves
    dependencies that are registered in the DI container. It handles:
    - Skipping parameters that are already provided
    - Skipping parameters with default values
    - Skipping the first parameter for instance/class methods (self/cls)
    - Resolving dependencies with the appropriate scope

    Args:
        method: The method/function to resolve dependencies for
        provided_kwargs: Already provided keyword arguments (will not be resolved)
        scope: Dependency scope (TRANSIENT, SCOPED, or SINGLETON)
        context_name: Context name for logging and debugging
        skip_first_param: If True, skip the first parameter (self/cls for methods)

    Returns:
        Dictionary mapping parameter names to resolved dependency instances

    Note:
        Parameters not found in the container or with resolution errors are silently
        skipped (logged at DEBUG level). This allows for flexible dependency resolution
        where not all parameters need to come from the container.
    """
    container = get_container()

    # Extract type hints from method signature
    # Fall back to __annotations__ if get_type_hints fails (e.g., forward references)
    try:
        hints = get_type_hints(method)
    except Exception as e:
        hints = method.__annotations__ if hasattr(method, '__annotations__') else {}
        logger.debug(f"{context_name}: Using __annotations__ instead of get_type_hints: {e}")

    # Identify parameters with default values - these won't be auto-injected
    # Also handle skip_first_param for instance/class methods
    try:
        sig = inspect.signature(method)
        params_with_defaults = {
            name: param.default
            for name, param in sig.parameters.items()
            if param.default is not inspect.Parameter.empty
        }

        # Exclude 'self' or 'cls' from dependency resolution for methods
        if skip_first_param:
            param_names = list(sig.parameters.keys())
            if param_names:
                first_param = param_names[0]
                hints = {k: v for k, v in hints.items() if k != first_param}
    except Exception:
        params_with_defaults = {}

    resolved = {}

    # Iterate through type hints and resolve dependencies from container
    for param_name, param_type in hints.items():
        # Skip return type annotation
        if param_name == 'return':
            continue

        # Use provided value if already given (allows manual override)
        if param_name in provided_kwargs:
            resolved[param_name] = provided_kwargs[param_name]
            continue

        # Skip parameters with default values (optional dependencies)
        if param_name in params_with_defaults:
            continue

        # Attempt to resolve dependency from container
        # Type can be either an abstract interface or concrete implementation
        try:
            if param_type in container._services or param_type in container._concrete_services:
                # Generate unique cache key for scope management
                cache_key = f"{param_type.__module__}.{param_type.__name__}"
                factory = lambda pt=param_type: container.resolve(pt)

                # Resolve with appropriate scope (TRANSIENT/SCOPED/SINGLETON)
                resolved[param_name] = _scope_manager.get_or_create(
                    cache_key=cache_key,
                    scope=scope,
                    factory=factory,
                    context_name=f"{context_name} -> {param_name}"
                )
        except Exception as e:
            # Silently skip unresolvable dependencies (not in container)
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
        is_method = _is_instance_or_class_method(func)

        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with scope_context():
                    resolved_kwargs = _resolve_and_merge_kwargs(
                        func, kwargs, scope, is_method
                    )
                    return await func(*args, **resolved_kwargs)

            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with scope_context():
                    resolved_kwargs = _resolve_and_merge_kwargs(
                        func, kwargs, scope, is_method
                    )
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

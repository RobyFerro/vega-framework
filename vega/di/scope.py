"""Scope management for dependency injection"""
import logging
import threading
from contextlib import contextmanager
from enum import Enum
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class Scope(Enum):
    """
    Dependency injection scopes.

    SINGLETON: Single shared instance across the application (lazy-loaded)
    SCOPED: Single instance per request/operation (shared within same operation)
    TRANSIENT: New instance created every time (default)
    """
    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


class _ScopeManager:
    """
    Manages dependency caching for different scopes.

    Handles:
    - Singleton: Global cache
    - Scoped: Thread-local cache per operation
    - Transient: No caching
    """

    def __init__(self):
        self._singleton_cache: Dict[str, Any] = {}
        self._scoped_storage = threading.local()

    @property
    def singleton_cache(self) -> Dict[str, Any]:
        return self._singleton_cache

    def get_scoped_cache(self) -> Dict[str, Any]:
        if not hasattr(self._scoped_storage, 'cache'):
            self._scoped_storage.cache = {}
        return self._scoped_storage.cache

    def is_scope_active(self) -> bool:
        return hasattr(self._scoped_storage, 'scope_active') and self._scoped_storage.scope_active

    def set_scope_active(self, active: bool):
        self._scoped_storage.scope_active = active

    def clear_scoped_cache(self):
        if hasattr(self._scoped_storage, 'cache'):
            self._scoped_storage.cache.clear()
            logger.debug("Scoped cache cleared for current operation")

    def clear_singleton_cache(self):
        self._singleton_cache.clear()
        logger.info("Singleton cache cleared")

    def get_or_create(
        self,
        cache_key: str,
        scope: Scope,
        factory: Callable[[], Any],
        context_name: str = "unknown"
    ) -> Any:
        """
        Get cached instance or create new one based on scope.

        Args:
            cache_key: Unique key for this dependency
            scope: Scope (SINGLETON, SCOPED, or TRANSIENT)
            factory: Function to create new instance
            context_name: Name for logging

        Returns:
            Instance from cache or newly created
        """
        if scope == Scope.SINGLETON:
            if cache_key in self._singleton_cache:
                logger.debug(f"{context_name}: Using cached SINGLETON {cache_key}")
                return self._singleton_cache[cache_key]

            instance = factory()
            self._singleton_cache[cache_key] = instance
            logger.debug(f"{context_name}: Created and cached SINGLETON {cache_key}")
            return instance

        elif scope == Scope.SCOPED:
            scoped_cache = self.get_scoped_cache()
            if cache_key in scoped_cache:
                logger.debug(f"{context_name}: Using cached SCOPED {cache_key}")
                return scoped_cache[cache_key]

            instance = factory()
            scoped_cache[cache_key] = instance
            logger.debug(f"{context_name}: Created and cached SCOPED {cache_key}")
            return instance

        else:  # TRANSIENT
            logger.debug(f"{context_name}: Creating TRANSIENT {cache_key}")
            return factory()


# Global scope manager
_scope_manager = _ScopeManager()


@contextmanager
def scope_context():
    """
    Context manager for scoped dependencies lifecycle.

    Use this to wrap operations that should share scoped dependencies.
    At the end of the context, all scoped instances are cleared.

    Example:
        with scope_context():
            # All scoped dependencies created here share the same instances
            service1 = resolve(MyService)
            service2 = resolve(AnotherService)
            # Both services share the same scoped dependencies
        # Scoped cache is cleared here
    """
    # Track if we're the outermost scope
    was_active = _scope_manager.is_scope_active()
    if not was_active:
        _scope_manager.set_scope_active(True)

    try:
        yield
    finally:
        # Only clear cache if we created the scope
        if not was_active:
            _scope_manager.set_scope_active(False)
            _scope_manager.clear_scoped_cache()


def clear_singletons():
    """Clear all singleton instances. Useful for testing."""
    _scope_manager.clear_singleton_cache()


def get_singleton_instance(service_name: str) -> Optional[Any]:
    """Get a singleton instance from cache if it exists."""
    return _scope_manager.singleton_cache.get(service_name)

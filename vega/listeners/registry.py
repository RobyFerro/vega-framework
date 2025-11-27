"""Global registry for job listeners"""
from typing import List, Type
import logging

logger = logging.getLogger(__name__)

# Global listener registry
# Listeners register themselves via @job_listener decorator
_listener_registry: List[Type['JobListener']] = []


def register_listener(listener_cls: Type['JobListener']) -> None:
    """
    Register a listener class in the global registry.

    Called automatically by @job_listener decorator.

    Args:
        listener_cls: The listener class to register
    """
    _listener_registry.append(listener_cls)
    logger.debug(f"Registered listener: {listener_cls.__name__}")


def get_listener_registry() -> List[Type['JobListener']]:
    """
    Get all registered listener classes.

    Returns:
        List of registered listener classes
    """
    return _listener_registry.copy()


def clear_listener_registry() -> None:
    """
    Clear the listener registry.

    Useful for testing to reset state between test cases.
    """
    _listener_registry.clear()
    logger.debug("Cleared listener registry")

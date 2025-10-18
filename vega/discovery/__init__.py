"""Auto-discovery utilities for Vega framework"""
from .routes import discover_routers
from .commands import discover_commands
from .events import discover_event_handlers
from .beans import discover_beans, discover_beans_in_module, list_registered_beans

__all__ = [
    "discover_routers",
    "discover_commands",
    "discover_event_handlers",
    "discover_beans",
    "discover_beans_in_module",
    "list_registered_beans",
]

"""Auto-discovery utilities for Vega framework"""
from .routes import discover_routers, discover_routers_ddd
from .commands import discover_commands, discover_commands_ddd
from .events import discover_event_handlers
from .beans import discover_beans, discover_beans_in_module, list_registered_beans
from .listeners import discover_listeners

__all__ = [
    "discover_routers",
    "discover_routers_ddd",
    "discover_commands",
    "discover_commands_ddd",
    "discover_event_handlers",
    "discover_beans",
    "discover_beans_in_module",
    "list_registered_beans",
    "discover_listeners",
]

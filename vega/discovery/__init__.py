"""Auto-discovery utilities for Vega framework"""
from .routes import discover_routers
from .commands import discover_commands
from .events import discover_event_handlers

__all__ = ["discover_routers", "discover_commands", "discover_event_handlers"]

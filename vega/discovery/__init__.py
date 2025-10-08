"""Auto-discovery utilities for Vega framework"""
from .routes import discover_routers
from .commands import discover_commands

__all__ = ["discover_routers", "discover_commands"]

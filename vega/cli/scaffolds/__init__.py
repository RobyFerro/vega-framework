"""Scaffolding helpers for Vega CLI."""

from .vega_web import create_vega_web_scaffold
from .sqlalchemy import create_sqlalchemy_scaffold

# Backward compatibility alias
create_fastapi_scaffold = create_vega_web_scaffold

__all__ = [
    "create_vega_web_scaffold",
    "create_fastapi_scaffold",  # Deprecated: use create_vega_web_scaffold
    "create_sqlalchemy_scaffold",
]

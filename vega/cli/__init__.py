"""Vega Framework CLI tools"""

# Lazy import to avoid circular dependencies when importing utilities
def __getattr__(name: str):
    if name == "cli":
        from vega.cli.main import cli
        return cli
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["cli"]

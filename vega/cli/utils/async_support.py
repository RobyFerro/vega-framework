"""Async support utilities for Click CLI commands"""
import asyncio
import functools
from typing import TypeVar, Callable, Any

import click

F = TypeVar('F', bound=Callable[..., Any])


def async_command(f: F) -> F:
    """
    Decorator to make Click commands support async functions.

    This allows you to define async Click commands that can call
    async interactors and other async operations.

    Example:
        @click.command()
        @click.option('--name', required=True)
        @async_command
        async def create_user(name: str):
            # Import config to initialize DI container
            import config  # noqa: F401
            from domain.interactors.create_user import CreateUser

            user = await CreateUser(name=name)
            click.echo(f"Created user: {user.name}")

    Usage in Click groups:
        @cli.command()
        @click.argument('user_id')
        @async_command
        async def get_user(user_id: str):
            user = await GetUser(user_id=user_id)
            click.echo(f"User: {user.name}")
    """
    @functools.wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(f(*args, **kwargs))
    return wrapper  # type: ignore


def coro(f: F) -> F:
    """
    Alias for async_command. Shorter name for convenience.

    Example:
        @click.command()
        @coro
        async def my_command():
            result = await MyInteractor()
            click.echo(result)
    """
    return async_command(f)

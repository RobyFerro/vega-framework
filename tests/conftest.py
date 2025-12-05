"""
Pytest configuration and shared fixtures for Vega Framework tests.

This file contains:
- Global pytest configuration
- Shared fixtures used across multiple test modules
- Test utilities and helpers
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from vega.di import Container
from vega.events import EventBus
from vega.web import VegaApp


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an event loop for the test session.

    This ensures all async tests run in the same event loop.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def container() -> Container:
    """
    Provide a fresh dependency injection container for each test.

    Returns:
        Container: A new DI container instance
    """
    return Container()


@pytest.fixture
def event_bus() -> EventBus:
    """
    Provide a fresh event bus for each test.

    Returns:
        EventBus: A new event bus instance
    """
    return EventBus()


@pytest.fixture
def vega_app() -> VegaApp:
    """
    Provide a basic Vega web application for testing.

    Returns:
        VegaApp: A configured Vega application instance
    """
    return VegaApp(
        title="Test Application",
        version="0.0.1",
        debug=True
    )


@pytest.fixture
async def async_container() -> AsyncGenerator[Container, None]:
    """
    Provide an async-compatible DI container.

    Yields:
        Container: A DI container with async support
    """
    container = Container()
    yield container
    # Cleanup if needed
    await asyncio.sleep(0)  # Allow pending tasks to complete


@pytest.fixture
async def async_event_bus() -> AsyncGenerator[EventBus, None]:
    """
    Provide an async-compatible event bus.

    Yields:
        EventBus: An event bus for async testing
    """
    bus = EventBus()
    yield bus
    # Cleanup if needed
    await asyncio.sleep(0)


# Test markers configuration
def pytest_configure(config):
    """
    Configure custom pytest markers.
    """
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "functional: mark test as a functional test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "web: mark test as web-related"
    )
    config.addinivalue_line(
        "markers", "di: mark test as dependency injection related"
    )
    config.addinivalue_line(
        "markers", "events: mark test as event system related"
    )
    config.addinivalue_line(
        "markers", "listeners: mark test as job listener related"
    )


# Pytest collection configuration
def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers automatically.
    """
    for item in items:
        # Auto-mark tests based on their location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "functional" in str(item.fspath):
            item.add_marker(pytest.mark.functional)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Auto-mark based on test name
        if "web" in item.nodeid.lower():
            item.add_marker(pytest.mark.web)
        if "di" in item.nodeid.lower() or "container" in item.nodeid.lower():
            item.add_marker(pytest.mark.di)
        if "event" in item.nodeid.lower():
            item.add_marker(pytest.mark.events)
        if "listener" in item.nodeid.lower():
            item.add_marker(pytest.mark.listeners)

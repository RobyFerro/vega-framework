"""Decorators for event handling"""
from typing import Type, Callable, Optional
from vega.events.event import Event
from vega.events.bus import get_event_bus


def subscribe(
    event_type: Type[Event],
    priority: int = 0,
    retry_on_error: bool = False,
    max_retries: int = 3
):
    """
    Decorator to subscribe a function to an event on the global event bus.

    This is a convenience decorator that uses the global event bus instance.

    Args:
        event_type: Type of event to subscribe to
        priority: Handler priority (higher runs first)
        retry_on_error: Whether to retry on failure
        max_retries: Maximum retry attempts

    Returns:
        Decorated function

    Example:
        from vega.events import subscribe, Event
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class UserCreated(Event):
            user_id: str
            email: str

        @subscribe(UserCreated)
        async def send_welcome_email(event: UserCreated):
            print(f"Sending welcome email to {event.email}")

        @subscribe(UserCreated, priority=10)
        async def critical_handler(event: UserCreated):
            # This runs first due to higher priority
            print("Critical handler")

        @subscribe(UserCreated, retry_on_error=True, max_retries=5)
        async def retry_handler(event: UserCreated):
            # Will retry up to 5 times on failure
            await external_api.call()
    """
    def decorator(func: Callable) -> Callable:
        bus = get_event_bus()
        bus.subscribe(
            event_type=event_type,
            handler=func,
            priority=priority,
            retry_on_error=retry_on_error,
            max_retries=max_retries
        )
        return func

    return decorator


def event_handler(
    event_type: Type[Event],
    bus: Optional['EventBus'] = None,
    priority: int = 0,
    retry_on_error: bool = False,
    max_retries: int = 3
):
    """
    Decorator to mark a method as an event handler.

    Similar to @subscribe but allows specifying a custom event bus.
    Useful for class-based handlers or testing.

    Args:
        event_type: Type of event to subscribe to
        bus: Custom event bus instance (uses global if None)
        priority: Handler priority
        retry_on_error: Whether to retry on failure
        max_retries: Maximum retry attempts

    Returns:
        Decorated function

    Example:
        from vega.events import event_handler, Event, EventBus

        class UserEventHandlers:
            def __init__(self, email_service):
                self.email_service = email_service

            @event_handler(UserCreated)
            async def handle_user_created(self, event: UserCreated):
                await self.email_service.send_welcome(event.email)

        # With custom bus
        custom_bus = EventBus()

        class CustomHandlers:
            @event_handler(UserCreated, bus=custom_bus)
            async def handle(self, event: UserCreated):
                pass
    """
    def decorator(func: Callable) -> Callable:
        event_bus = bus or get_event_bus()
        event_bus.subscribe(
            event_type=event_type,
            handler=func,
            priority=priority,
            retry_on_error=retry_on_error,
            max_retries=max_retries
        )
        # Mark function as event handler for introspection
        func._is_event_handler = True
        func._event_type = event_type
        return func

    return decorator


def trigger(event_class: Type[Event]):
    """
    Decorator for Interactor classes to automatically trigger an event after call() completes.

    The event is constructed with the return value of call() method and auto-published.
    This is perfect for domain events that should be triggered after a use case completes.

    Args:
        event_class: The event class to trigger (must accept call() result in constructor)

    Example:
        from vega.patterns import Interactor
        from vega.events import trigger
        from vega.di import bind
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class UserCreated(Event):
            user_id: str
            email: str
            name: str

            def __post_init__(self):
                super().__init__()

        @trigger(UserCreated)
        class CreateUser(Interactor[dict]):
            def __init__(self, name: str, email: str):
                self.name = name
                self.email = email

            @bind
            async def call(self, repository: UserRepository) -> dict:
                user = await repository.create(name=self.name, email=self.email)
                # Return dict that matches UserCreated constructor
                return {
                    "user_id": user.id,
                    "email": user.email,
                    "name": user.name
                }

        # Usage
        result = await CreateUser(name="John", email="john@test.com")
        # After call() completes:
        # 1. Returns result to caller
        # 2. Automatically publishes UserCreated event with result as input
        # 3. All @subscribe(UserCreated) handlers are triggered

    Note:
        - The event class constructor must accept the call() result
        - If call() returns a dict, event(**result) is called
        - If call() returns an object, event is called with the object as first arg
        - Works seamlessly with auto-publish (events publish themselves)
    """
    def decorator(cls):
        # Store the event class on the Interactor class
        cls._trigger_event = event_class
        return cls
    return decorator
